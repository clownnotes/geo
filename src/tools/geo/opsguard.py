# -*- coding: utf-8 -*-
"""GEO 运营账号反抓取护栏 (tools/geo/opsguard.py)

// [2026-09-19] [运营账号反AI抓取与核心资产防搬走纵深加固]
针对「运营把登录票贴进自己的 AI / 脚本，一夜之间把客户整库爬走」这一威胁面。

本模块只做三件事，且只对运营人员生效（开发者完全不受约束）：

1. 限流：单账号每分钟请求数、每小时产出文件读取数、每小时跨项目数；
2. 审计：运营的每一次 API 调用落盘到 data/operator_audit.jsonl，开发者可查可导出；
3. 抓取特征自动处置：短时高频访问只做 429 频控保护，绝不停用账号；唯独反复恶意探测敏感核心资产时才停用账号。

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
# [2026-09-21] [阶段一帮助提示剥离与连点封禁逻辑废除] 调高阈值适配多卡片并发，彻底废除频控自动停用账号
REQ_PER_MINUTE = 300              # 单账号每分钟最多请求数 (适配单页面20+并发请求)
OUTPUT_READ_PER_HOUR = 600        # 每小时最多读取产出文件次数
DISTINCT_FILENAME_PER_HOUR = 150  # 每小时最多触碰多少个不同产出文件名（超限先 429 频控，绝不停用）
DISTINCT_PROJECT_PER_HOUR = 20    # 每小时最多触碰多少个不同客户项目
TOO_MANY_429_PER_HOUR = 999999    # [已废除自动停用] 仅作记录，不再执行封禁
SENSITIVE_DENIALS_PER_HOUR = 20   # 每小时撞击敏感核心资产多次后告警

_LOCK = threading.RLock()
_REQ_LOG = {}    # user_key -> deque([timestamp])，只保留最近 60 秒
_HOUR_BUCKET = {}  # user_key -> {"start": float, "projects": set, "filenames": set, "output_reads": int, "denied": int, "sensitive_denials": int}

_PROJECT_ROUTE_RE = re.compile(r"^/api/projects/([^/]+)/")


def _user_key(identity):
    if not identity:
        return "anonymous"
    return str(getattr(identity, "user_id", "") or getattr(identity, "phone", "") or "unknown")


def _bucket(user_key):
    now = time.time()
    b = _HOUR_BUCKET.setdefault(user_key, {
        "start": now,
        "projects": set(),
        "filenames": set(),
        "output_reads": 0,
        "denied": 0,
        "sensitive_denials": 0,
    })
    if now - b["start"] > 3600:
        b["start"] = now
        b["projects"].clear()
        b["filenames"].clear()
        b["output_reads"] = 0
        b["denied"] = 0
        b["sensitive_denials"] = 0
    return b


def _auto_disable(identity, reason):
    """[已收敛] 仅限开发者手动调用或极度恶意探测，日常频控绝对禁止触发。"""
    try:
        from .rbac import (load_roster, save_roster, _find_member_index,
                           _now_str, STATUS_DISABLED)
    except Exception as e:
        logger.error("[OPSGUARD] 导入 rbac 失败，无法停用: %s", e)
        return False
    user_id = getattr(identity, "user_id", "")
    phone = getattr(identity, "phone", "")
    if not user_id and not phone:
        return False
    roster = load_roster()
    members = roster.get("members", [])
    idx = _find_member_index(members, user_id)
    if idx < 0 and phone:
        idx = _find_member_index(members, phone)
    if idx < 0:
        return False
    m = members[idx]
    if m.get("status") == STATUS_DISABLED:
        return True
    m["status"] = STATUS_DISABLED
    m["disabled_at"] = _now_str()
    m["disabled_reason"] = f"系统反抓取策略自动停用: {reason}"
    ok = save_roster(roster)
    if ok:
        logger.critical(
            "[OPSGUARD] 自动停用运营账号 user=%s phone=%s 原因=%s",
            user_id, phone, reason
        )
    return ok


def record_sensitive_denial(identity, path):
    """当 server 拦截运营人员访问敏感文件（9因子、语料库、dist_channels 等）时调用此函数。"""
    if identity is None or not getattr(identity, "matched", False):
        return
    if getattr(identity, "is_developer", False):
        return
    user_key = _user_key(identity)
    with _LOCK:
        b = _bucket(user_key)
        b["sensitive_denials"] += 1
        cnt = b["sensitive_denials"]
        if cnt > SENSITIVE_DENIALS_PER_HOUR:
            _auto_disable(identity, f"短时间内多次尝试探测敏感核心资产(命中{cnt}次)")


def check(identity, path, method="GET"):
    """运营请求准入判定。返回 (ok, http_status, msg)。

    开发者与匿名请求一律直接放行（匿名由总门与守卫负责）。
    // [2026-09-21] [阶段一帮助提示剥离与连点封禁逻辑废除] 彻底废除频控自动改写花名册停用账号的逻辑
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
            msg = "操作稍显频繁，系统正在处理中，请稍后再试"
            logger.warning("[OPSGUARD] 频控拦截: user=%s path=%s msg=%s", user_key, path, msg)
            return False, 429, msg

    counters = _bucket(user_key)

    # 2) 跨客户项目探测
    m = _PROJECT_ROUTE_RE.match(path or "")
    if m:
        counters["projects"].add(m.group(1))
        if len(counters["projects"]) > DISTINCT_PROJECT_PER_HOUR:
            counters["denied"] += 1
            msg = "跨客户项目访问过于频繁，请稍后再试"
            logger.warning("[OPSGUARD] 频控拦截: user=%s path=%s msg=%s", user_key, path, msg)
            return False, 429, msg

    # 3) 产出文件批量读取
    if "/output/" in (path or ""):
        counters["output_reads"] += 1
        fname = os.path.basename((path or "").split("/output/", 1)[1])
        if fname:
            counters["filenames"].add(fname)
        if len(counters["filenames"]) > DISTINCT_FILENAME_PER_HOUR:
            counters["denied"] += 1
            msg = "产出文件访问过于频繁，请稍后再试"
            logger.warning("[OPSGUARD] 频控拦截: user=%s path=%s msg=%s", user_key, path, msg)
            return False, 429, msg
        if counters["output_reads"] > OUTPUT_READ_PER_HOUR:
            counters["denied"] += 1
            msg = "产出文件读取过于频繁，请稍后再试"
            logger.warning("[OPSGUARD] 频控拦截: user=%s path=%s msg=%s", user_key, path, msg)
            return False, 429, msg

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
