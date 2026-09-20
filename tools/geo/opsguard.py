# -*- coding: utf-8 -*-
"""GEO 运营账号反抓取护栏 (tools/geo/opsguard.py)

// [2026-09-19] [运营账号反AI抓取与核心资产防搬走纵深加固]
针对「运营把登录票贴进自己的 AI / 脚本，一夜之间把客户整库爬走」这一威胁面。

本模块只做三件事，且只对运营人员生效（开发者完全不受约束）：

1. 限流：单账号每分钟请求数、每小时产出文件读取数、每小时跨项目数；
2. 审计：运营的每一次 API 调用落盘到 data/operator_audit.jsonl，开发者可查可导出；
3. 抓取特征自动处置：短时高频读取产出、遍历大量不同文件名、跨大量客户项目、
   反复触发限流 —— 直接把该成员在花名册里置为 disabled（其会话随后被服务端吊销）。

记忆体只放在进程内存里，重启即清零；阈值改动不需要迁移数据。
"""

import json
import logging
import os
import re
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
AUDIT_FILE = os.path.join(DATA_DIR, "operator_audit.jsonl")

# --- 阈值（可按业务节奏调整；调高=更宽松，调低=更敏感） ---
REQ_PER_MINUTE = 120              # 单账号每分钟最多请求数
OUTPUT_READ_PER_HOUR = 120        # 每小时最多读取产出文件次数
DISTINCT_FILENAME_PER_HOUR = 80   # 每小时最多触碰多少个不同产出文件名（超限先 429 频控，不停用）
DISTINCT_PROJECT_PER_HOUR = 10    # 每小时最多触碰多少个不同客户项目
TOO_MANY_429_PER_HOUR = 10        # 每小时被限流多少次后直接停用
SENSITIVE_DENIALS_PER_HOUR = 10   # 每小时撞击敏感核心资产多少次后直接停用

_LOCK = threading.RLock()
_REQ_LOG = {}    # user_key -> deque([timestamp])，只保留最近 60 秒
_HOUR_BUCKET = {}  # user_key -> (hour_index, counters)

_PROJECT_ROUTE_RE = re.compile(r"^/api/(?:v1/)?projects/([^/]+)(/.*)?$")


def _user_key(identity):
    return (getattr(identity, "user_id", "") or getattr(identity, "phone", "") or "anonymous")


def _bucket(user_key):
    hour = int(time.time() // 3600)
    with _LOCK:
        cur = _HOUR_BUCKET.get(user_key)
        if not cur or cur[0] != hour:
            cur = (hour, {
                "output_reads": 0,
                "filenames": set(),
                "projects": set(),
                "denied": 0,
                "sensitive_denied": 0,
            })
            _HOUR_BUCKET[user_key] = cur
        return cur[1]


def _auto_disable(identity, reason):
    """把该运营成员在花名册里置为停用。会话吊销由 server.check_auth 随后执行。"""
    try:
        from .rbac import (load_roster, save_roster, _find_member_index,
                           _now_str, STATUS_DISABLED)
    except Exception:
        return
    with _LOCK:
        try:
            roster = load_roster()
            members = roster.get("members", [])
            idx = _find_member_index(members, getattr(identity, "user_id", ""))
            if idx < 0:
                idx = _find_member_index(members, getattr(identity, "phone", ""))
            if idx < 0:
                return
            if members[idx].get("status") == STATUS_DISABLED:
                return
            members[idx]["status"] = STATUS_DISABLED
            members[idx]["updated_at"] = _now_str()
            roster["members"] = members
            if save_roster(roster):
                logger.error("[OPSGUARD] 自动停用运营账号 user=%s 原因=%s",
                             _user_key(identity), reason)
        except Exception as e:
            logger.error("[OPSGUARD] 自动停用失败: %s", e)


def record_sensitive_denial(identity, path=""):
    """记录一次敏感/违规核心资产探测拦截。超过阈值直接停用账号并吊销会话。"""
    if identity is None or not getattr(identity, "matched", False):
        return
    if getattr(identity, "is_developer", False):
        return
    user_key = _user_key(identity)
    with _LOCK:
        counters = _bucket(user_key)
        counters["sensitive_denied"] += 1
        if counters["sensitive_denied"] > SENSITIVE_DENIALS_PER_HOUR:
            _auto_disable(identity, f"短时间内多次尝试探测敏感核心资产(命中{counters['sensitive_denied']}次)")


def check(identity, path, method="GET"):
    """运营请求准入判定。返回 (ok, http_status, msg)。

    开发者与匿名请求一律直接放行（匿名由总门与守卫负责）。
    """
    if identity is None or not getattr(identity, "matched", False):
        return True, 200, ""
    if getattr(identity, "is_developer", False):
        return True, 200, ""

    user_key = _user_key(identity)
    now = time.time()

    # 1) 每分钟请求数
    with _LOCK:
        dq = _REQ_LOG.setdefault(user_key, deque())
        while dq and now - dq[0] > 60:
            dq.popleft()
        dq.append(now)
        if len(dq) > REQ_PER_MINUTE:
            counters = _bucket(user_key)
            counters["denied"] += 1
            if counters["denied"] > TOO_MANY_429_PER_HOUR:
                _auto_disable(identity, "反复触发频率限制")
                return False, 403, "账号已被安全策略停用，请联系管理员"
            return False, 429, "操作过于频繁，请稍后再试"

    counters = _bucket(user_key)

    # 2) 跨客户项目探测
    m = _PROJECT_ROUTE_RE.match(path or "")
    if m:
        counters["projects"].add(m.group(1))
        if len(counters["projects"]) > DISTINCT_PROJECT_PER_HOUR:
            counters["denied"] += 1
            if counters["denied"] > TOO_MANY_429_PER_HOUR:
                _auto_disable(identity, "短时间内访问大量不同客户项目")
                return False, 403, "账号已被安全策略停用，请联系管理员"
            return False, 429, "跨客户项目访问过于频繁，请稍后再试"

    # 3) 产出文件批量读取
    if "/output/" in (path or ""):
        counters["output_reads"] += 1
        fname = os.path.basename((path or "").split("/output/", 1)[1])
        if fname:
            counters["filenames"].add(fname)
        if len(counters["filenames"]) > DISTINCT_FILENAME_PER_HOUR:
            counters["denied"] += 1
            if counters["denied"] > TOO_MANY_429_PER_HOUR:
                _auto_disable(identity, "短时间内遍历大量不同产出文件名")
                return False, 403, "账号已被安全策略停用，请联系管理员"
            return False, 429, "产出文件访问过于频繁，请稍后再试"
        if counters["output_reads"] > OUTPUT_READ_PER_HOUR:
            counters["denied"] += 1
            if counters["denied"] > TOO_MANY_429_PER_HOUR:
                _auto_disable(identity, "短时间内大量读取产出文件")
                return False, 403, "账号已被安全策略停用，请联系管理员"
            return False, 429, "产出文件读取过于频繁，请稍后再试"

    return True, 200, ""


def record(identity, method, path, status=200, extra=None):
    """运营操作审计。只记 /api/ 调用与运营人员，开发者与静态资源不入库。"""
    if identity is None or not getattr(identity, "matched", False):
        return
    if getattr(identity, "is_developer", False):
        return
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "user": _user_key(identity),
        "name": getattr(identity, "name", ""),
        "method": method,
        "path": path,
        "status": status,
        "ip": (extra or {}).get("ip", ""),
    }
    if extra:
        entry.update(extra)
    with _LOCK:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning("[OPSGUARD] 审计写入失败: %s", e)


def reset_for_test():
    """仅供单测清理内存态，生产代码禁止调用。"""
    with _LOCK:
        _REQ_LOG.clear()
        _HOUR_BUCKET.clear()
