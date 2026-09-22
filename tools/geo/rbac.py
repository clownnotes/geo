# -*- coding: utf-8 -*-
"""GEO 管理台 RBAC 权限模块 (tools/geo/rbac.py)

// [2026-09-18] [运营人员权限隔离] 建立本地花名册权威源与统一路由守卫
设计契约（对应 openspec/changes/2026-09-18-运营人员权限隔离与多租户协作规范/design.md）：
1. 本地花名册 data/rbac_members.json 是权限的唯一权威源，上游小毛驴返回的 role 一律不采信；
2. 身份主键以 user_id 为首选、phone 为兜底，两者皆空则拒绝；
3. 角色仅两档：developer（全系统唯一）与 operator（纯使用，按项目隔离）；
4. 统一路由守卫按四档判定：公开白名单 / 开发者专属 / 项目级+原子权限 / 未登记 fail-closed；
5. 花名册读写必须原子化：threading.RLock + 临时文件 os.replace，缺失或解析失败回退默认结构。
"""

import itertools
import json
import logging
import os
import re
import threading
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量与路径
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ROSTER_FILE = os.path.join(DATA_DIR, "rbac_members.json")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")

SCHEMA_VERSION = 1

ROLE_DEVELOPER = "developer"
ROLE_OPERATOR = "operator"

STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"

# 五大原子权限（与 design.md 权限点枚举一致）
PERMISSION_CODES = (
    "keyword:manage",   # 关键词词库导入、新增、修改与导出
    "ai:generate",      # 触发语料提纯、大模型文章生成与 FAQ 生成
    "article:edit",     # 编辑保存文章、更新元数据
    "preview:view",     # 查看本地项目站点预览
    "report:view",      # 查看 GEO 分析评测报告
)

# 默认花名册骨架（沿用既有本地开发者身份，消除 server.py 硬编码双真源）
DEFAULT_DEVELOPER_PHONES = ["13150568888"]

# 花名册读-改-写全程锁，杜绝多端/多线程并发写丢数据
_ROSTER_LOCK = threading.RLock()

# 临时文件自增序号（在 _ROSTER_LOCK 保护下递增，保证同进程内文件名唯一）
_TMP_SEQ = itertools.count(1)


# ---------------------------------------------------------------------------
# 花名册原子读写
# ---------------------------------------------------------------------------

def _default_roster():
    """返回一份全新的默认花名册（深拷贝，避免调用方污染模块级常量）"""
    return {
        "schema_version": SCHEMA_VERSION,
        "developer_phones": list(DEFAULT_DEVELOPER_PHONES),
        "developer_user_ids": [],
        "members": [],
    }


def load_roster():
    """加载花名册。文件缺失或 JSON 损坏时回退默认结构并打 WARNING，绝不抛异常。"""
    with _ROSTER_LOCK:
        if not os.path.exists(ROSTER_FILE):
            logger.warning("[RBAC] 花名册不存在，回退默认结构: %s", ROSTER_FILE)
            return _default_roster()
        try:
            with open(ROSTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.warning("[RBAC] 花名册解析失败(%s)，回退默认结构: %s", e, ROSTER_FILE)
            return _default_roster()

        if not isinstance(data, dict):
            logger.warning("[RBAC] 花名册结构非法(非 dict)，回退默认结构")
            return _default_roster()

        # 补齐缺失字段，容忍手工编辑导致的不完整文件
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("developer_phones", list(DEFAULT_DEVELOPER_PHONES))
        data.setdefault("developer_user_ids", [])
        data.setdefault("members", [])
        if not isinstance(data.get("developer_phones"), list):
            data["developer_phones"] = list(DEFAULT_DEVELOPER_PHONES)
        if not isinstance(data.get("developer_user_ids"), list):
            data["developer_user_ids"] = []
        if not isinstance(data.get("members"), list):
            data["members"] = []
        return data


def save_roster(data):
    """原子化写入花名册：临时文件 + os.replace，杜绝写一半崩溃导致文件损坏。

    临时文件名必须每次唯一（含进程号 + 自增序号），否则同进程内多线程并发写会
    共用同一个 tmp 文件互相覆盖，造成丢数据。
    """
    tmp_path = ""
    with _ROSTER_LOCK:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_path = "%s.tmp.%d.%d" % (ROSTER_FILE, os.getpid(), next(_TMP_SEQ))
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, ROSTER_FILE)
            return True
        except Exception as e:
            logger.error("[RBAC] 花名册写入失败: %s", e)
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            return False


# ---------------------------------------------------------------------------
# 身份对象
# ---------------------------------------------------------------------------

class Identity(object):
    """一次请求解析出的身份快照。所有鉴权判定只依赖本对象，不依赖上游 role 字段。"""

    __slots__ = (
        "user_id", "phone", "name", "role", "is_developer",
        "allowed_projects", "permissions", "status", "matched",
    )

    def __init__(self, user_id="", phone="", name="", role="", is_developer=False,
                 allowed_projects=None, permissions=None, status="", matched=False):
        self.user_id = str(user_id or "")
        self.phone = str(phone or "")
        self.name = name or ""
        self.role = role
        self.is_developer = bool(is_developer)
        self.allowed_projects = list(allowed_projects or [])
        self.permissions = list(permissions or [])
        self.status = status
        self.matched = matched  # 是否在花名册中命中（未命中应拒绝访问）

    def has_permission(self, permission_code):
        if self.is_developer:
            return True
        if not permission_code:
            return True
        return permission_code in self.permissions

    def can_access_project(self, project_id):
        if self.is_developer:
            return True
        if not project_id:
            return True
        return project_id in self.allowed_projects

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "phone": self.phone,
            "name": self.name,
            "role": self.role,
            "is_developer": self.is_developer,
            "allowed_projects": list(self.allowed_projects),
            "permissions": list(self.permissions),
        }


def _anonymous():
    """未命中花名册的匿名身份（matched=False）"""
    return Identity(role="", is_developer=False, matched=False)


def _developer_identity(phone):
    return Identity(
        user_id="", phone=str(phone or ""), name="开发者",
        role=ROLE_DEVELOPER, is_developer=True,
        allowed_projects=["*"], permissions=list(PERMISSION_CODES),
        status=STATUS_ACTIVE, matched=True,
    )


def sync_member_user_id_on_login(phone, user_id):
    """// [2026-09-20] [成员管理交付看板与企业透视改造] 首次登录回写：
    手机号命中运营成员且会话带 user_id、花名册该行 user_id 为空时，加锁写回落盘。
    """
    phone = str(phone or "").strip()
    user_id = str(user_id or "").strip()
    if not phone or not user_id:
        return False
    with _ROSTER_LOCK:
        roster = load_roster()
        members = roster.get("members", [])
        idx = _find_member_index(members, phone)
        if idx < 0:
            return False
        record = members[idx]
        if not str(record.get("user_id") or "").strip():
            record["user_id"] = user_id
            record["updated_at"] = _now_str()
            members[idx] = record
            roster["members"] = members
            return save_roster(roster)
    return False


# ---------------------------------------------------------------------------
# 身份解析
# ---------------------------------------------------------------------------

def resolve_identity(user_id="", phone=""):
    """按 user_id 优先、phone 兜底解析身份。

    返回 Identity：
      - 命中 developer_phones -> 开发者
      - 命中 members 且 status=active -> 运营人员
      - 命中 members 但 status=disabled -> matched=True 但零权限
      - 均未命中 -> matched=False（应返回 401 提示联系管理员）
    """
    user_id = str(user_id or "").strip()
    phone = str(phone or "").strip()
    if not user_id and not phone:
        return _anonymous()

    roster = load_roster()

    # 1) 开发者白名单（developer 不写入 members，只在此处判定）
    # user_id 优先：上游偶发不回 phone 时，仍能认回师弟
    for dev_uid in roster.get("developer_user_ids", []) or []:
        if user_id and str(dev_uid).strip() == user_id:
            return _developer_identity(phone)
    for dev_phone in roster.get("developer_phones", []):
        if phone and str(dev_phone).strip() == phone:
            return _developer_identity(dev_phone)

    # 2) 运营人员：先按 user_id 精确匹配
    if user_id:
        for m in roster.get("members", []):
            if str(m.get("user_id") or "").strip() == user_id:
                return _member_to_identity(m)

    # 3) 运营人员：再按 phone 兜底匹配
    if phone:
        for m in roster.get("members", []):
            if str(m.get("phone") or "").strip() == phone:
                # [2026-09-20] [成员管理交付看板与企业透视改造] 首次登录回写：
                # 若会话带 user_id 且花名册该成员 user_id 为空，写回落盘
                if user_id and not str(m.get("user_id") or "").strip():
                    sync_member_user_id_on_login(phone, user_id)
                    m["user_id"] = user_id
                return _member_to_identity(m)

    return _anonymous()


def _member_to_identity(member):
    """把花名册成员记录转为 Identity。status 非 active 一律零权限。"""
    status = member.get("status", STATUS_ACTIVE)
    active = (status == STATUS_ACTIVE)
    return Identity(
        user_id=str(member.get("user_id") or ""),
        phone=str(member.get("phone") or ""),
        name=member.get("name") or "",
        role=ROLE_OPERATOR,
        is_developer=False,
        allowed_projects=list(member.get("allowed_projects") or []) if active else [],
        permissions=list(member.get("permissions") or []) if active else [],
        status=status,
        matched=True,
    )


# ---------------------------------------------------------------------------
# 成员管理（仅开发者可调用，开发者本身不写入 members）
# ---------------------------------------------------------------------------

def list_members():
    """返回全部运营人员（不含开发者）"""
    return list(load_roster().get("members", []))


def get_member(key):
    """按 user_id 或 phone 查找单个运营人员"""
    key = str(key or "").strip()
    if not key:
        return None
    for m in load_roster().get("members", []):
        if str(m.get("user_id") or "").strip() == key:
            return m
        if str(m.get("phone") or "").strip() == key:
            return m
    return None


def _now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _find_member_index(members, key):
    """按 user_id 或 phone 定位成员下标，未找到返回 -1"""
    key = str(key or "").strip()
    if not key:
        return -1
    for i, m in enumerate(members):
        if str(m.get("user_id") or "").strip() == key:
            return i
        if str(m.get("phone") or "").strip() == key:
            return i
    return -1


def upsert_member(payload, key=None):
    """新增或修改运营人员。禁止登记开发者手机号。返回 (ok, msg, member)

    整个读-改-写过程包在 _ROSTER_LOCK 内（RLock 可重入，内部 load/save 不会死锁），
    否则多线程下会出现「同时读到旧值、后写覆盖先写」的丢数据问题。
    """
    with _ROSTER_LOCK:
        roster = load_roster()
        members = roster.get("members", [])
        key = str(key or "").strip()

        # 1) 定位既有记录：优先按 key，其次按 payload 内的 phone / user_id
        idx = _find_member_index(members, key) if key else -1
        if idx < 0:
            idx = _find_member_index(members, str(payload.get("phone") or "").strip())
        if idx < 0:
            idx = _find_member_index(members, str(payload.get("user_id") or "").strip())
        existing = members[idx] if idx >= 0 else {}

        # 2) 标识允许从既有记录继承（修改场景 payload 可以只带要改的字段）
        phone = str(payload.get("phone") or existing.get("phone") or "").strip()
        user_id = str(payload.get("user_id") or existing.get("user_id") or "").strip()
        if not phone and not user_id:
            return False, "手机号与 user_id 不能同时为空", None

        dev_phones = [str(p).strip() for p in roster.get("developer_phones", [])]
        if phone and phone in dev_phones:
            return False, "该手机号属于开发者，禁止登记为运营人员", None

        # 3) 权限处理：// [2026-09-20] [成员管理交付看板与企业透视改造] 开通默认赋予全部 PERMISSION_CODES
        if "permissions" in payload and payload["permissions"] is not None:
            raw_perms = payload["permissions"]
            if idx < 0 and not raw_perms:
                perms = list(PERMISSION_CODES)
            else:
                perms = [p for p in raw_perms if p in PERMISSION_CODES]
        elif existing:
            perms = [p for p in existing.get("permissions", []) if p in PERMISSION_CODES]
        else:
            perms = list(PERMISSION_CODES)

        now = _now_str()
        record = {
            "user_id": user_id or existing.get("user_id", ""),
            "phone": phone or existing.get("phone", ""),
            "name": payload.get("name", existing.get("name", "")),
            "role": ROLE_OPERATOR,  # 恒为 operator，不接受外部传入
            "status": payload.get("status", existing.get("status", STATUS_ACTIVE)),
            "allowed_projects": list(payload.get("allowed_projects", existing.get("allowed_projects", []) or [])),
            "permissions": perms,
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
        }
        if record["status"] not in (STATUS_ACTIVE, STATUS_DISABLED):
            record["status"] = STATUS_ACTIVE

        if idx >= 0:
            members[idx] = record
        else:
            members.append(record)

        roster["members"] = members
        if save_roster(roster):
            return True, "已保存", record
        return False, "花名册写入失败", None


def delete_member(key):
    """删除运营人员。返回 (ok, msg)。读-改-写整体加锁，避免并发丢数据。"""
    key = str(key or "").strip()
    with _ROSTER_LOCK:
        roster = load_roster()
        members = roster.get("members", [])
        remain = [m for m in members
                  if str(m.get("user_id") or "").strip() != key and str(m.get("phone") or "").strip() != key]
        if len(remain) == len(members):
            return False, "未找到该成员"
        roster["members"] = remain
        if save_roster(roster):
            return True, "已删除"
        return False, "花名册写入失败"


def assign_member_project(key, project_id):
    """// [2026-09-20] [成员管理交付看板与企业透视改造] 追加成员管辖项目，原子加锁。返回 (bool, str)"""
    key = str(key or "").strip()
    project_id = str(project_id or "").strip()
    if not key:
        return False, "成员标识不能为空"
    if not project_id:
        return False, "企业代号不能为空"

    with _ROSTER_LOCK:
        roster = load_roster()
        members = roster.get("members", [])
        idx = _find_member_index(members, key)
        if idx < 0:
            return False, "未找到该成员"
        record = members[idx]
        allowed = list(record.get("allowed_projects") or [])
        if project_id not in allowed:
            allowed.append(project_id)
            record["allowed_projects"] = allowed
            record["updated_at"] = _now_str()
            members[idx] = record
            roster["members"] = members
            if save_roster(roster):
                return True, "已成功分配企业管辖权"
            return False, "花名册写入失败"
        return True, "该企业已在管辖名单中"


def unassign_member_project(key, project_id):
    """// [2026-09-20] [成员管理交付看板与企业透视改造] 收回成员管辖项目，原子加锁。返回 (bool, str)"""
    key = str(key or "").strip()
    project_id = str(project_id or "").strip()
    if not key:
        return False, "成员标识不能为空"
    if not project_id:
        return False, "企业代号不能为空"

    with _ROSTER_LOCK:
        roster = load_roster()
        members = roster.get("members", [])
        idx = _find_member_index(members, key)
        if idx < 0:
            return False, "未找到该成员"
        record = members[idx]
        allowed = list(record.get("allowed_projects") or [])
        if project_id in allowed:
            allowed.remove(project_id)
            record["allowed_projects"] = allowed
            record["updated_at"] = _now_str()
            members[idx] = record
            roster["members"] = members
            if save_roster(roster):
                return True, "已收回企业管辖权"
            return False, "花名册写入失败"
        return True, "该企业不在管辖名单中"


def append_member_allowed_project(user_id=None, phone=None, project_id=None):
    """// [2026-09-19] [员工自主建企与代理免选专注交付] 运营建企成功后，把 project_id 追加进该成员 allowed_projects。
    // [2026-09-20] 复用 assign_member_project，双键兜底（user_id 优先、phone 兜底），保持唯一真相源 (SSOT)。
    """
    u = str(user_id or "").strip()
    p = str(phone or "").strip()
    if u:
        ok, _ = assign_member_project(u, project_id)
        if ok:
            return True
    if p:
        ok, _ = assign_member_project(p, project_id)
        return ok
    return False


# ---------------------------------------------------------------------------
# 路由四档登记表
# ---------------------------------------------------------------------------

# A 档：公开白名单（无需登录即可访问）
ROUTE_PUBLIC = frozenset({
    "/api/auth/status",
    "/api/auth/login",
    "/api/v1/xiulan/login",
    "/api/v1/sessions",
    "/api/auth/logout",
    "/api/auth/wechat-qr",
    "/api/v1/auth/wechat-qr",
    "/api/v1/community/auth/wx-login",
    "/api/llm/status",
})

# 公开前缀（分享链接靠 URL 内的 token 自证，不走登录态）
ROUTE_PUBLIC_PREFIXES = ("/api/share/",)

# 已登录即可访问、无需项目与原子权限判定的列表类接口。
# 这些接口的返回内容已在服务端按 allowed_projects 过滤，是运营人员看得见项目列表的唯一入口；
# 若落入 fail-closed 兜底，运营将连自己的项目都看不到。
ROUTE_AUTHENTICATED = frozenset({
    ("/api/projects", "GET"),
    ("/api/v1/projects", "GET"),
    # [2026-09-19] [员工自主建企与代理免选专注交付] 开放运营人员创建项目权限，建企后自动将项目追加至管辖名单
    ("/api/projects", "POST"),
    ("/api/v1/projects", "POST"),
    ("/api/groups", "GET"),
    # 只读放行：仪表盘首屏、企业管理下拉、巡检状态文案
    ("/api/ops/check-ledger", "GET"),   # 响应须按 allowed_projects 裁剪 rows 与 summary
    ("/api/partners", "GET"),           # 合作方下拉 / 筛选
    ("/api/settings/notifications", "GET"),  # loadPatrolStatus 读巡检开关与上次时间
})

# B 档：开发者专属（运营一律 403）
ROUTE_DEVELOPER = frozenset({
    "/api/llm/config",                  # 写入大模型 API Key
    "/api/settings/notifications/test", # 试发通知
    "/api/patrol/trigger",              # 全域巡检触发
    "/api/batch/trigger",               # 批量任务触发
    "/api/ops/check-logs",
    # // [2026-09-20] [商业洞察权限收敛] 商业洞察大盘、组合 ROI、服务费与行业对标收敛为开发者专属
    "/api/portfolio/summary",           # 商业洞察：组合 ROI / 服务费
    "/api/portfolio/report",            # 商业洞察：服务费大盘报告
    "/api/portfolio/patrol",            # 商业洞察：全域巡检扫描
    "/api/benchmark/industries",        # 跨租户行业聚合大盘
    # 注意：/api/ops/check-ledger、/api/partners、/api/settings/notifications 的 GET
    # 已移入 ROUTE_AUTHENTICATED（只读放行，台账响应按 allowed_projects 裁剪）；
    # 它们的写操作见 ROUTE_DEVELOPER_VERBS，切勿再整段放回本集合。
})

# 开发者专属：需区分方法的路由 -> (path, method)
ROUTE_DEVELOPER_VERBS = frozenset({
    ("/api/partners", "POST"),                  # 创建合作方
    ("/api/settings/notifications", "POST"),    # 写通知配置
    ("/api/settings/notifications", "PUT"),
})

# 开发者专属：项目级危险动作（按后缀匹配）
ROUTE_DEVELOPER_SUFFIXES = (
    "/delete",          # shutil.rmtree 直接删项目
    "/site/download",
    # [2026-09-19] [运营端去IDE化与小毛驴算力内嵌闭环] 配方口、整包下载与机房配置仅开发者专属
    "/answer-rewrite/ide-pack",
    "/answer-rewrite/pack",
    "/answer-rewrite/writeback-cmd",
    "/answer-audit/ide-clipboard",
    "/diag/deepen-prompt",
    "/diag/boss-audit-pack",
    "/export",
    "/acceptance/download-zip",
    "/site/nginx-conf",
    # [2026-09-19] [运营账号反AI抓取] 分享票自建：运营不得给自己开后门再下整包
    "/share/create",
    # // [2026-09-20] [商业洞察权限收敛] 报价物料与 ROI 设定收敛为开发者专属（B档优先，防掉入只读兜底）
    "/pitch/data",
    "/pitch/slides",
    "/pitch/print",
    "/roi/settings",
)

# C 档：项目级动作 -> 原子权限映射（顺序敏感，长后缀优先）
ROUTE_PERMISSION_SUFFIXES = (
    ("/facts/confirm-all", "article:edit"),
    ("/facts/resolve-conflict", "article:edit"),
    ("/corpus/diff-confirm-all", "article:edit"),
    ("/corpus/diff-decide", "article:edit"),
    ("/corpus/pin", "article:edit"),
    ("/corpus/dirty-blocks", "report:view"),
    ("/corpus/diff", "report:view"),
    ("/probe/apply", "article:edit"),
    ("/probe/apply-disk", "article:edit"),
    ("/probe/script", "ai:generate"),
    ("/probe/preview", "preview:view"),
    ("/probe/preview-disk", "preview:view"),
    ("/probe/guide", "preview:view"),
    ("/profile", "article:edit"),
    ("/monitor/manual-ingest", "ai:generate"),
    ("/ingest/url", "keyword:manage"),
    ("/ingest/text", "keyword:manage"),
    ("/raw_materials", "article:edit"),
    ("/evidence", "report:view"),
    ("/evolution/apply", "article:edit"),
    ("/evolution/generate", "ai:generate"),
    ("/evolution/analyze", "report:view"),
    ("/heal/apply", "article:edit"),
    ("/heal/rollback", "article:edit"),
    ("/heal/preview", "preview:view"),
    ("/heal/audit", "report:view"),
    ("/ledger/batch-add", "article:edit"),
    ("/ledger/audit", "report:view"),
    ("/ledger/summary", "report:view"),
    # /roi/settings 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/roi/calculate", "report:view"),       # 运营交付动线在用，勿动
    ("/distribution/record", "article:edit"),
    ("/distribution/verify", "report:view"),
    ("/distribution/ledger", "report:view"),
    ("/visual/generate", "ai:generate"),
    ("/visual/assets", "report:view"),
    ("/defense/generate", "ai:generate"),
    ("/intent/generate", "ai:generate"),
    ("/intent/sync-eval", "report:view"),
    ("/intent/matrix", "report:view"),
    ("/share/create", "article:edit"),
    ("/share/info", "report:view"),
    ("/playground/simulate", "preview:view"), # 运营交付动线在用，勿动
    ("/playground/batch", "preview:view"),    # 运营交付动线在用，勿动
    ("/crawler/simulate", "report:view"),
    ("/rag/diagnose", "report:view"),
    ("/compliance/inspect", "report:view"),
    ("/compliance/sanitize", "ai:generate"),
    ("/competitor/gap", "report:view"),
    ("/citation/authority", "report:view"),
    ("/guard/injection", "report:view"),
    ("/guard/repair", "ai:generate"),
    ("/guard/risks", "report:view"),
    ("/guard/simulation", "report:view"),
    ("/princeton/audit", "report:view"),
    ("/eval/run", "ai:generate"),
    ("/eval/report", "report:view"),
    ("/answer-audit", "report:view"),
    ("/probing/run", "ai:generate"),
    ("/probing/reconcile", "ai:generate"),
    ("/spider-audit/run", "ai:generate"),
    ("/rival-crack/run", "ai:generate"),
    ("/alert-bot/send", "ai:generate"),
    ("/doubao-index/boost", "ai:generate"),
    ("/sentiment/scan", "ai:generate"),
    ("/sentiment/suppress", "ai:generate"),
    ("/decay/track", "ai:generate"),
    ("/decay/heal", "ai:generate"),
    ("/mindshare/audit", "ai:generate"),
    ("/mindshare/pitch", "ai:generate"),
    ("/rerank/simulate", "ai:generate"),
    ("/rerank/reinforce", "ai:generate"),
    ("/attribution/audit", "ai:generate"),
    ("/attribution/optimize", "ai:generate"),
    ("/funnel/simulate", "ai:generate"),
    ("/funnel/defend", "ai:generate"),
    ("/robustness/test", "ai:generate"),
    ("/robustness/harden", "ai:generate"),
    ("/moat/simulate", "ai:generate"),
    ("/moat/assets", "report:view"),
    ("/toutiao/build", "ai:generate"),
    ("/wechat/build", "ai:generate"),
    ("/deepseek/build", "ai:generate"),
    ("/kimi_baidu/build", "ai:generate"),
    ("/publish/compile", "ai:generate"),
    ("/publish/pack-status", "report:view"),
    ("/graph/data", "report:view"),
    ("/graph/svg", "report:view"),
    ("/graph/query", "report:view"),
    # /pitch/data, /pitch/slides, /pitch/print 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/acceptance/data", "report:view"),
    ("/acceptance/print", "report:view"),
    # /acceptance/download-zip 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/certificate", "report:view"),
    ("/report/print", "report:view"),
    ("/benchmark", "report:view"),
    ("/history", "report:view"),
    ("/meta", "report:view"),  # 读；POST 改归属见 _is_developer_route
    # /export 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/export-audit-html", "report:view"),  # 客户单份体检报告，保留给运营
    # /diag/boss-audit-pack 与 /diag/deepen-prompt 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/diag/probe-answer-audit", "report:view"),
    # [2026-09-19] [运营端去IDE化与小毛驴算力内嵌闭环] 在线改写闭环接口
    ("/answer-rewrite/brief", "report:view"),
    ("/answer-rewrite/content", "report:view"),
    ("/answer-rewrite/ai-generate", "ai:generate"),
    ("/answer-rewrite/save-final", "article:edit"),
    ("/answer-rewrite/writeback-status", "report:view"),
    # /answer-rewrite/ide-pack, /answer-rewrite/writeback-cmd, /answer-audit/ide-clipboard 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/distribute/latest-log", "report:view"),
    ("/publish/preview", "report:view"),
    ("/monitor/metrics", "report:view"),
    ("/monitor/prompts", "report:view"),  # 真机实测试题，保留给运营
    ("/site/status", "preview:view"),
    # /site/nginx-conf 已移入 ROUTE_DEVELOPER_SUFFIXES
    ("/tasks", "ai:generate"),
    ("/reports", "report:view"),
    ("/bundles", "report:view"),
    # --- 补齐覆盖率审计发现的缺口（2026-09-18 全量 182 条路由审计） ---
    ("/acceptance", "report:view"),
    ("/archive", "report:view"),
    ("/audit-html", "report:view"),
    ("/audit-report", "report:view"),
    ("/confirm", "article:edit"),            # /facts/{key}/confirm 单条确认
    ("/deepseek/zhihu", "report:view"),
    ("/doubao-index/audit", "ai:generate"),
    ("/download", "report:view"),
    ("/download-zip", "report:view"),
    ("/file", "report:view"),
    ("/matrix", "report:view"),              # 集团矩阵短后缀，不是意图矩阵；集团分支不靠它放行
    ("/probing/trace", "report:view"),
    ("/simulate", "report:view"),            # 兜底：更具体的 /rerank/simulate 等已在上方命中
    ("/toutiao/micro", "report:view"),
    ("/wechat/video", "report:view"),
    ("/facts", "report:view"),               # 事实清单读取（仅 GET 路由）
)

# 包含式匹配：路径中间带层级参数的路由（如 /evidence/{id}、/output/{file}），
# 无法用 endswith 覆盖，在后缀匹配全部落空后才按子串判定。
# 元组为 (子串, 权限, 方法)；方法为 None 表示任意方法，否则仅在该方法下命中。
#
# 【安全约束】/output/ 与 /evidence/ 同时存在 DELETE 路由（server.py 删除产出与证据），
# 因此只登记 GET；DELETE 不登记 -> 落 fail-closed -> 仅开发者可用。
ROUTE_PERMISSION_SUBSTRINGS = (
    ("/run/", "ai:generate", None),              # /run/{step} 流水线执行
    ("/facts/", "report:view", None),            # /facts/{key} 事实条目读取
    ("/evidence/", "report:view", "GET"),        # 仅读取；DELETE 保持仅开发者
    ("/output/", "report:view", "GET"),          # 仅读取；DELETE 保持仅开发者
    ("/site/", "preview:view", None),            # /site/{path} 站点预览（/site/download 已被 B 档拦截）
    ("/distribution/rich-content/", "report:view", None),
)

# 已打过「仅靠兜底放行」警告的路径，避免每条请求刷日志
_READONLY_FALLBACK_WARNED = set()

# 只读兜底：以上未命中时按通用后缀判为只读（仅 GET 生效）
ROUTE_READONLY_SUFFIXES = (
    "/status", "/report", "/report30", "/data", "/svg", "/query",
    "/preview", "/copy", "/readme", "/llms", "/whitepaper", "/baike", "/qa",
    "/print", "/info", "/guide", "/logs", "/events",
)


# ---------------------------------------------------------------------------
# 统一路由守卫
# ---------------------------------------------------------------------------

# // [2026-09-20] [商业洞察权限收敛与集团矩阵路由] 集团级路由正则，置于项目级前
_GROUP_ROUTE_RE = re.compile(r"^/api/(?:v1/)?groups/([^/]+)(/.*)?$")

# 项目级路由：/api/projects/{id}/... 或 /api/v1/projects/{id}/...
_PROJECT_ROUTE_RE = re.compile(r"^/api/(?:v1/)?projects/([^/]+)(/.*)?$")

# // [2026-09-20] [商业洞察权限收敛与集团矩阵路由] 集团级配置缓存与可见性判定
_GROUPS_CACHE = {"mtime": 0.0, "data": {}}


def _load_groups_cached():
    """按文件 mtime 失效的进程内缓存；文件缺失或解析失败时返回空 dict，绝不抛异常。"""
    if not os.path.exists(GROUPS_FILE):
        _GROUPS_CACHE["mtime"] = 0.0
        _GROUPS_CACHE["data"] = {}
        return {}
    try:
        mtime = os.path.getmtime(GROUPS_FILE)
        if mtime > 0 and mtime == _GROUPS_CACHE["mtime"] and _GROUPS_CACHE["data"]:
            return _GROUPS_CACHE["data"]
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        groups = raw.get("groups", {}) if isinstance(raw, dict) else {}
        _GROUPS_CACHE["mtime"] = mtime
        _GROUPS_CACHE["data"] = groups
        return groups
    except Exception as e:
        logger.warning("[RBAC] 集团配置解析失败(fail-closed)，回退空结构: %s (%s)", GROUPS_FILE, e)
        _GROUPS_CACHE["mtime"] = 0.0
        _GROUPS_CACHE["data"] = {}
        return {}


def _can_access_group(group_id, identity):
    """集团可见性判定：开发者放行；identity 为空返回 False；
    否则母公司 parent_project_id 或任一 children[].project_id 命中 allowed_projects 即放行。
    判定语义必须与 filter_groups() 保持一致。
    """
    if identity is None:
        return False
    if getattr(identity, "is_developer", False):
        return True
    groups = _load_groups_cached()
    grp = groups.get(str(group_id))
    if not isinstance(grp, dict):
        return False
    allowed = set(str(x) for x in (getattr(identity, "allowed_projects", None) or []))
    parent = str(grp.get("parent_project_id") or "")
    if parent and parent in allowed:
        return True
    for c in grp.get("children") or []:
        if isinstance(c, dict) and str(c.get("project_id") or "") in allowed:
            return True
    return False


def _match_permission(path, method=None):
    """按后缀 -> 子串(方法感知) -> 通用只读后缀的顺序匹配所需原子权限。未登记返回 None。

    // [2026-09-19] [运营账号反AI抓取] 通用只读兜底只对 GET 生效。
    原实现对任意方法（含 POST/PUT/DELETE）都判给 report:view，等于给运营开了一扇
    「写操作自动放行」的后门，且与 design.md 的 fail-closed 原则冲突。
    """
    method = (method or "GET").upper()
    for suffix, perm in ROUTE_PERMISSION_SUFFIXES:
        if path.endswith(suffix):
            return perm
    for substr, perm, verb in ROUTE_PERMISSION_SUBSTRINGS:
        if substr in path and (verb is None or verb == method):
            return perm
    if method != "GET":
        # 非只读方法一律不兜底 -> 落 fail-closed，仅开发者可用
        return None
    for suffix in ROUTE_READONLY_SUFFIXES:
        if path.endswith(suffix):
            if path not in _READONLY_FALLBACK_WARNED:
                _READONLY_FALLBACK_WARNED.add(path)
                logger.warning("[RBAC] 路由仅靠只读兜底放行，开发者应显式登记: GET %s", path)
            return "report:view"
    return None


def _is_public(path):
    if path in ROUTE_PUBLIC:
        return True
    for prefix in ROUTE_PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _is_developer_route(path, method):
    if path.startswith("/api/admin"):
        return True
    if path in ROUTE_DEVELOPER:
        return True
    if (path, method) in ROUTE_DEVELOPER_VERBS:
        return True
    # 合作方改档/归档：现码为 POST /api/partners/{id}（无 PUT/DELETE），动态路径无法用集合登记
    if path.startswith("/api/partners/") and method != "GET":
        return True
    # 改挂合作方：运营不维护「客户属于谁」
    if path.startswith("/api/projects/") and path.endswith("/meta") and method != "GET":
        return True
    # 母盘素材写入：写文同事可以看，不能改。不要放进后缀表，否则 GET 也会被挡住
    if path.startswith("/api/projects/") and path.endswith("/raw_materials") and method != "GET":
        return True
    for suffix in ROUTE_DEVELOPER_SUFFIXES:
        if path.endswith(suffix):
            return True
    return False


def guard_route(path, method, identity):
    """统一路由守卫。返回 (ok: bool, http_status: int, msg: str)。

    判定顺序（前一档命中即返回）：
      A 公开白名单  -> 放行
      B 开发者专属  -> 非开发者 403
      C 项目级      -> require_project_access + require_permission
      D 兜底未登记  -> fail-closed，仅开发者可用，并打 WARNING
    """
    method = (method or "GET").upper()

    # A 档：公开
    if _is_public(path):
        return True, 200, ""

    # 未登录 / 未命中花名册
    if identity is None or not getattr(identity, "matched", False):
        return False, 401, "您尚未获得 GEO 平台操作权限，请联系管理员开通"

    # 已停用账号
    if not identity.is_developer and identity.status == STATUS_DISABLED:
        return False, 403, "账号已停用，请联系管理员"

    # B 档：开发者专属
    if _is_developer_route(path, method):
        if not identity.is_developer:
            return False, 403, "无此操作权限（开发者专属）"
        return True, 200, ""

    # 已登录即可访问的列表类接口（内容已在服务端按 allowed_projects 过滤）
    if (path, method) in ROUTE_AUTHENTICATED:
        return True, 200, ""

    # 开发者对所有路由放行
    if identity.is_developer:
        return True, 200, ""

    # // [2026-09-20] [商业洞察权限收敛与集团矩阵路由] 集团级分支（置于开发者全放行后、项目级之前）
    g = _GROUP_ROUTE_RE.match(path)
    if g:
        group_id = g.group(1)
        if not _can_access_group(group_id, identity):
            return False, 403, "无权访问该集团"
        if method == "GET" and path.endswith("/matrix"):
            if not identity.has_permission("report:view"):
                return False, 403, "缺少相应操作权限（需要 report:view）"
            return True, 200, ""
        logger.warning("[RBAC] 未登记集团级路由被拦截(fail-closed): %s %s user=%s",
                       method, path, identity.user_id or identity.phone)
        return False, 403, "该操作尚未开放给运营人员，请联系管理员开通"

    # C 档：项目级
    m = _PROJECT_ROUTE_RE.match(path)
    if m:
        project_id = m.group(1)
        if not identity.can_access_project(project_id):
            return False, 403, "无权访问该项目"
        perm = _match_permission(path, method)
        if perm is None and not (m.group(2) or "").strip("/"):
            # 形如 /api/projects/{id} 无动作后缀：必须按方法区分，禁止只读权限改配置
            if method == "GET":
                perm = "report:view"
            elif method in ("PUT", "POST"):
                perm = "article:edit"
            else:
                perm = None  # DELETE 等保持 fail-closed，仅开发者（已在上方放行）
        if perm is None:
            logger.warning("[RBAC] 未登记项目级路由被拦截(fail-closed): %s %s user=%s",
                           method, path, identity.user_id or identity.phone)
            return False, 403, "该操作尚未开放给运营人员，请联系管理员开通"
        if not identity.has_permission(perm):
            return False, 403, "缺少相应操作权限（需要 %s）" % perm
        return True, 200, ""

    # D 档：非项目级且未登记
    logger.warning("[RBAC] 未登记路由被拦截(fail-closed): %s %s user=%s",
                   method, path, identity.user_id or identity.phone)
    return False, 403, "该操作尚未开放给运营人员，请联系管理员开通"


def filter_groups(groups, identity):
    """按管辖项目裁剪集团列表。无交集的集团整组丢掉，子项目只留授权项。"""
    if identity is None:
        return []
    if identity.is_developer:
        return list(groups or [])
    allowed = set(str(x) for x in (identity.allowed_projects or []))
    out = []
    for g in groups or []:
        if not isinstance(g, dict):
            continue
        parent = str(g.get("parent_project_id") or "")
        kept = []
        for c in g.get("children") or []:
            if isinstance(c, dict) and str(c.get("project_id") or "") in allowed:
                kept.append(c)
        if parent not in allowed and not kept:
            continue
        g2 = dict(g)
        g2["children"] = kept
        if parent not in allowed:
            g2["parent_project_id"] = ""
        out.append(g2)
    return out


def redact_group_matrix(payload, identity):
    """// [2026-09-20] [商业洞察权限收敛与集团矩阵路由] 集团矩阵响应数据多租户裁剪。

    开发者原样返回；非开发者按 design.md 第 7 节裁剪：
    1. children_matrix 只留 project_id 在 allowed_projects 里的行；
    2. shared_citations 里的品牌名只留授权品牌；一条里不足 2 个授权品牌则整条删除；
    3. 若删掉了任何子品牌：禁止把原来的汇总字段原样返回，按留下来的行重数与加权平均；
       tier 与 summary 用纯文字「只统计你负责的品牌」，禁止表情符号；
    4. parent_project_id 未授权则清空；
    5. 一个子品牌都没留下：返回无权访问。
    """
    if not isinstance(payload, dict):
        return payload
    if identity is None:
        return {"success": False, "message": "无权访问该集团"}
    if getattr(identity, "is_developer", False):
        return payload

    allowed = set(str(x) for x in (getattr(identity, "allowed_projects", None) or []))

    orig_children = payload.get("children_matrix") or []
    kept_children = [
        dict(c) for c in orig_children
        if isinstance(c, dict) and str(c.get("project_id") or "") in allowed
    ]

    if not kept_children:
        return {"success": False, "message": "无权访问该集团"}

    out = dict(payload)

    # 4. parent_project_id 不在授权名单里就清空，与 filter_groups() 一致
    parent = str(payload.get("parent_project_id") or "")
    if parent not in allowed:
        out["parent_project_id"] = ""

    # 2. shared_citations 里的品牌名只留授权品牌；一条里不足 2 个授权品牌则整条删除
    allowed_brand_names = set(
        str(c.get("brand_name") or c.get("client_name") or c.get("project_id") or "")
        for c in kept_children
    )
    kept_citations = []
    for cit in payload.get("shared_citations") or []:
        if not isinstance(cit, dict):
            continue
        shared_by = [
            b for b in (cit.get("shared_by_brands") or [])
            if str(b) in allowed_brand_names
        ]
        if len(shared_by) >= 2:
            c2 = dict(cit)
            c2["shared_by_brands"] = shared_by
            kept_citations.append(c2)

    dropped_any = len(kept_children) < len(orig_children)

    if dropped_any:
        # 3. 若删掉了任何子品牌：禁止把原来的汇总字段原样返回
        total_brands = len(kept_children)
        total_prompts = sum(c.get("keywords_count", 0) for c in kept_children)

        # 重新计算贡献率与 group_sov
        total_eff = sum(c.get("effective_volume", 0.0) for c in kept_children)
        for c in kept_children:
            if total_eff > 0:
                c["contribution_pct"] = round((c.get("effective_volume", 0.0) / total_eff) * 100, 1)
            else:
                c["contribution_pct"] = round((c.get("keywords_count", 0) / max(total_prompts, 1)) * 100, 1)

        total_weights = sum(c.get("weight", 0.0) for c in kept_children if "error" not in c)
        if total_weights > 0:
            group_sov = round(sum(c.get("sov_pct", 0.0) * (c.get("weight", 0.0) / total_weights) for c in kept_children if "error" not in c), 1)
        elif total_prompts > 0:
            group_sov = round(total_eff / total_prompts, 1)
        else:
            group_sov = 0.0

        total_child_cit = sum(c.get("citation_count", 0) for c in kept_children)
        if total_child_cit > 0:
            synergy_multiplier = round(1.0 + (len(kept_citations) * 0.15) + (group_sov / 100.0 * 0.2), 2)
            synergy_index = 1.0
        else:
            synergy_multiplier = 1.0
            synergy_index = 1.0

        out["group_sov"] = group_sov
        out["synergy_index"] = synergy_index
        out["synergy_multiplier"] = synergy_multiplier
        out["tier"] = "只统计你负责的品牌"
        out["tier_color"] = "indigo"
        out["summary"] = "只统计你负责的品牌"
        out["total_brands"] = total_brands
        out["total_prompts"] = total_prompts
        out["total_unique_citation_domains"] = len(kept_citations)
        out["shared_citations_count"] = len(kept_citations)
        out["shared_citations"] = kept_citations
    else:
        # 未删子品牌，但非开发者文案必须去除 Emoji
        tier = out.get("tier", "")
        summary = out.get("summary", "")
        out["tier"] = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27ff\u2300-\u23ff\ufe0f]", "", str(tier)).strip()
        out["summary"] = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27ff\u2300-\u23ff\ufe0f]", "", str(summary)).strip()
        out["shared_citations"] = payload.get("shared_citations") or []

    out["children_matrix"] = kept_children
    return out


def filter_check_ledger(payload, identity):
    """运维检测台账多租户裁剪。

    开发者看全量；运营只看到 allowed_projects 内的项目，且 summary 必须按裁剪后的
    rows 重算——只滤 rows 却留下全站 summary，等于把别人的客户数量泄露出去。
    """
    if not isinstance(payload, dict):
        return payload
    if identity is None:
        return {"success": True, "policy": payload.get("policy", {}),
                "summary": {}, "rows": [], "generated_at": payload.get("generated_at", "")}
    if getattr(identity, "is_developer", False):
        return payload

    allowed = set(getattr(identity, "allowed_projects", None) or [])
    rows = [r for r in (payload.get("rows") or [])
            if str((r or {}).get("project_id", "")) in allowed]

    summary = {
        "never": sum(1 for r in rows if r.get("status") == "never"),
        "overdue": sum(1 for r in rows if r.get("status") == "overdue"),
        "warn": sum(1 for r in rows if r.get("status") == "warn"),
        "ok": sum(1 for r in rows if r.get("status") == "ok"),
        "sov_alert_count": sum(1 for r in rows if r.get("sov_alert")),
        "total": len(rows),
    }

    out = dict(payload)
    out["rows"] = rows
    out["summary"] = summary
    return out


def strip_partner_fields(payload, identity):
    """运营响应里去掉合作方归属，避免看见「客户是谁的」。"""
    if identity is None or getattr(identity, "is_developer", False):
        return payload
    if isinstance(payload, list):
        return [strip_partner_fields(x, identity) for x in payload]
    if not isinstance(payload, dict):
        return payload
    out = dict(payload)
    out.pop("partner_id", None)
    out.pop("partner_name", None)
    for key in ("project", "projects"):
        if key in out:
            out[key] = strip_partner_fields(out[key], identity)
    return out


def filter_projects(projects, identity, key="client_id"):
    """按 allowed_projects 过滤项目列表（服务端过滤才是安全边界）。"""
    if identity is None:
        return []
    if identity.is_developer:
        return list(projects)
    allowed = set(identity.allowed_projects or [])
    out = []
    for p in projects or []:
        pid = p.get(key) if isinstance(p, dict) else p
        if str(pid) in allowed:
            out.append(p)
    return out
