# -*- coding: utf-8 -*-
"""RBAC 权限隔离自动化测试 (tests/test_rbac.py)

对应 openspec 变更：2026-09-18-运营人员权限隔离与多租户协作规范

覆盖：
1. 开发者权限完全放行；
2. 运营人员跨项目访问抛出 403；
3. 运营人员调用成员管理 / LLM Key 写入 / 项目删除抛出 403；
4. 未登记路由对运营 fail-closed、对开发者放行；
5. 花名册并发读写不丢数据（RLock + 原子替换）；
6. 成员添加、修改、停用、删除流程正常。

重要：测试全部在本地临时文件上完成，**不依赖小毛驴上游**（NEXTDOOR_BASE_URL
默认指向 127.0.0.1:3001，本地未必起服务），也不污染真实 data/rbac_members.json。
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEV_PHONE = "13150568888"
OP_USER_ID = "1829384756102938475"
OP_PHONE = "13900000001"
ALL_PERMS = list(rbac.PERMISSION_CODES)


class RbacTestBase(unittest.TestCase):
    """把花名册指向临时文件，避免污染真实数据。"""

    def setUp(self):
        self._orig_roster_file = rbac.ROSTER_FILE
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_rbac_test_")
        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "members": [],
        })

    def tearDown(self):
        rbac.ROSTER_FILE = self._orig_roster_file
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def add_operator(self, allowed_projects, permissions=None, status="active"):
        ok, msg, rec = rbac.upsert_member({
            "user_id": OP_USER_ID,
            "phone": OP_PHONE,
            "name": "运营同事小张",
            "allowed_projects": allowed_projects,
            "permissions": permissions if permissions is not None else ALL_PERMS,
            "status": status,
        })
        self.assertTrue(ok, msg)
        return rec


class TestIdentityResolution(RbacTestBase):
    """身份解析：user_id 优先、phone 兜底，开发者白名单优先于 members"""

    def test_developer_by_phone(self):
        ident = rbac.resolve_identity(phone=DEV_PHONE)
        self.assertTrue(ident.is_developer)
        self.assertTrue(ident.matched)
        self.assertEqual(ident.role, rbac.ROLE_DEVELOPER)

    def test_operator_by_user_id(self):
        self.add_operator(["nextgeo"])
        ident = rbac.resolve_identity(user_id=OP_USER_ID)
        self.assertFalse(ident.is_developer)
        self.assertTrue(ident.matched)
        self.assertEqual(ident.allowed_projects, ["nextgeo"])

    def test_operator_by_phone_fallback(self):
        """user_id 缺失时按 phone 兜底匹配"""
        self.add_operator(["nextgeo"])
        ident = rbac.resolve_identity(phone=OP_PHONE)
        self.assertTrue(ident.matched)
        self.assertEqual(ident.user_id, OP_USER_ID)

    def test_unknown_user_not_matched(self):
        ident = rbac.resolve_identity(user_id="999", phone="13800000000")
        self.assertFalse(ident.matched)

    def test_empty_identity_rejected(self):
        ident = rbac.resolve_identity()
        self.assertFalse(ident.matched)

    def test_disabled_member_has_no_permission(self):
        self.add_operator(["nextgeo"], status="disabled")
        ident = rbac.resolve_identity(user_id=OP_USER_ID)
        self.assertTrue(ident.matched)          # 命中花名册
        self.assertEqual(ident.permissions, [])  # 但零权限
        self.assertEqual(ident.allowed_projects, [])

    def test_upstream_role_not_trusted(self):
        """上游 role 不得参与鉴权：花名册里没有的人，即便自称 admin 也不放行"""
        ident = rbac.resolve_identity(user_id="admin_from_upstream", phone="")
        self.assertFalse(ident.matched)
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/meta", "GET", ident)
        self.assertFalse(ok)
        self.assertEqual(status, 401)


class TestDeveloperFullAccess(RbacTestBase):
    """决策：开发者对所有路由放行"""

    def setUp(self):
        super().setUp()
        self.dev = rbac.resolve_identity(phone=DEV_PHONE)

    def test_developer_allowed_on_every_category(self):
        cases = [
            ("/api/projects/any/meta", "GET"),
            ("/api/projects/any/delete", "POST"),
            ("/api/llm/config", "POST"),
            ("/api/admin/members", "GET"),
            ("/api/projects", "POST"),
            ("/api/projects/any/totally-unregistered-action", "POST"),
        ]
        for path, method in cases:
            ok, status, msg = rbac.guard_route(path, method, self.dev)
            self.assertTrue(ok, f"{method} {path} 应放行，实际 {status} {msg}")


class TestOperatorIsolation(RbacTestBase):
    """运营人员隔离：跨项目 403、开发者专属 403、缺权限 403"""

    def setUp(self):
        super().setUp()
        self.add_operator(["nextgeo"])
        self.op = rbac.resolve_identity(user_id=OP_USER_ID)

    def test_cross_project_denied(self):
        ok, status, _ = rbac.guard_route("/api/projects/other_client/meta", "GET", self.op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_own_project_allowed(self):
        ok, status, msg = rbac.guard_route("/api/projects/nextgeo/meta", "GET", self.op)
        self.assertTrue(ok, msg)

    def test_developer_only_endpoints_denied(self):
        cases = [
            ("/api/admin/members", "GET"),
            ("/api/admin/members", "POST"),
            ("/api/llm/config", "POST"),
            ("/api/projects/nextgeo/delete", "POST"),
            ("/api/settings/notifications", "POST"),
            ("/api/patrol/trigger", "POST"),
        ]
        for path, method in cases:
            ok, status, _ = rbac.guard_route(path, method, self.op)
            self.assertFalse(ok, f"{method} {path} 应对运营 403")
            self.assertEqual(status, 403)

    def test_project_create_allowed_for_operator(self):
        """// [2026-09-19] [员工自主建企] POST /api/projects 对运营人员放行"""
        ok, status, msg = rbac.guard_route("/api/projects", "POST", self.op)
        self.assertTrue(ok, msg)
        self.assertEqual(status, 200)
        ok, status, msg = rbac.guard_route("/api/v1/projects", "POST", self.op)
        self.assertTrue(ok, msg)
        self.assertEqual(status, 200)

    def test_project_list_allowed_and_server_filtered(self):
        """列表接口对运营开放（内容由服务端过滤），不得被 fail-closed 拦死"""
        ok, status, msg = rbac.guard_route("/api/projects", "GET", self.op)
        self.assertTrue(ok, msg)
        ok, status, msg = rbac.guard_route("/api/groups", "GET", self.op)
        self.assertTrue(ok, msg)

    def test_bare_project_route_treated_as_read(self):
        """/api/projects/{id} 无动作后缀：GET 按只读；PUT 需要 article:edit；DELETE 仅开发者"""
        ok, status, msg = rbac.guard_route("/api/projects/nextgeo", "GET", self.op)
        self.assertTrue(ok, msg)

        reader = rbac.resolve_identity(user_id=OP_USER_ID)
        # 当前 self.op 持有全部权限，先换成只读
        self.add_operator(["nextgeo"], permissions=["report:view"])
        reader = rbac.resolve_identity(user_id=OP_USER_ID)
        ok, status, msg = rbac.guard_route("/api/projects/nextgeo", "GET", reader)
        self.assertTrue(ok, msg)
        ok, status, msg = rbac.guard_route("/api/projects/nextgeo", "PUT", reader)
        self.assertFalse(ok)
        self.assertEqual(status, 403)
        self.assertIn("article:edit", msg)
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo", "DELETE", reader)
        self.assertFalse(ok)
        self.assertEqual(status, 403)

        self.add_operator(["nextgeo"], permissions=["article:edit"])
        editor = rbac.resolve_identity(user_id=OP_USER_ID)
        ok, _, msg = rbac.guard_route("/api/projects/nextgeo", "PUT", editor)
        self.assertTrue(ok, msg)

    def test_missing_atomic_permission_denied(self):
        """只给 report:view，触发 ai:generate 动作应被拒"""
        self.add_operator(["nextgeo"], permissions=["report:view"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        ok, status, msg = rbac.guard_route("/api/projects/nextgeo/probing/run", "POST", op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)
        self.assertIn("ai:generate", msg)

    def test_disabled_account_denied(self):
        self.add_operator(["nextgeo"], status="disabled")
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/meta", "GET", op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)


class TestFailClosed(RbacTestBase):
    """决策 B：未登记路由 fail-closed，仅开发者可用"""

    def setUp(self):
        super().setUp()
        self.add_operator(["nextgeo"])
        self.op = rbac.resolve_identity(user_id=OP_USER_ID)
        self.dev = rbac.resolve_identity(phone=DEV_PHONE)

    def test_unregistered_project_route_closed_for_operator(self):
        ok, status, _ = rbac.guard_route(
            "/api/projects/nextgeo/brand-new-unregistered", "POST", self.op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_unregistered_project_route_open_for_developer(self):
        ok, _, _ = rbac.guard_route(
            "/api/projects/nextgeo/brand-new-unregistered", "POST", self.dev)
        self.assertTrue(ok)

    def test_unregistered_non_project_route_closed_for_operator(self):
        ok, status, _ = rbac.guard_route("/api/some/future/endpoint", "GET", self.op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)


class TestMethodAwareSubstrings(RbacTestBase):
    """包含式匹配必须方法感知：/output/ 与 /evidence/ 有 DELETE 路由，
    只读权限的运营不得借子串规则删产出或证据，DELETE 必须保持仅开发者可用。"""

    def setUp(self):
        super().setUp()
        self.add_operator(["t"])
        self.op = rbac.resolve_identity(user_id=OP_USER_ID)
        self.dev = rbac.resolve_identity(phone=DEV_PHONE)

    def test_operator_can_read_output_and_evidence(self):
        for path in ("/api/projects/t/output/01_x.md", "/api/projects/t/evidence/src1"):
            ok, _, msg = rbac.guard_route(path, "GET", self.op)
            self.assertTrue(ok, msg)

    def test_operator_cannot_delete_output(self):
        ok, status, _ = rbac.guard_route("/api/projects/t/output/01_x.md", "DELETE", self.op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_operator_cannot_delete_evidence(self):
        ok, status, _ = rbac.guard_route("/api/projects/t/evidence/src1", "DELETE", self.op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_developer_can_delete(self):
        for path in ("/api/projects/t/output/01_x.md", "/api/projects/t/evidence/src1"):
            ok, _, _ = rbac.guard_route(path, "DELETE", self.dev)
            self.assertTrue(ok)

    def test_run_substring_requires_ai_generate(self):
        self.add_operator(["t"], permissions=["report:view"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        ok, status, msg = rbac.guard_route("/api/projects/t/run/step2", "POST", op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)
        self.assertIn("ai:generate", msg)


class TestPublicRoutes(RbacTestBase):
    """公开白名单对未登录者也放行"""

    def test_public_login_allowed_for_anonymous(self):
        anon = rbac.resolve_identity(phone="")
        for path in ("/api/auth/login", "/api/auth/wechat-qr", "/api/llm/status"):
            ok, _, _ = rbac.guard_route(path, "POST", anon)
            self.assertTrue(ok, f"{path} 应公开")

    def test_share_prefix_allowed_for_anonymous(self):
        anon = rbac.resolve_identity(phone="")
        ok, _, _ = rbac.guard_route("/api/share/abc123/data", "GET", anon)
        self.assertTrue(ok)

    def test_private_route_401_for_anonymous(self):
        anon = rbac.resolve_identity(phone="")
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/meta", "GET", anon)
        self.assertFalse(ok)
        self.assertEqual(status, 401)


class TestRosterConcurrency(RbacTestBase):
    """花名册并发读写：RLock + 原子替换，不丢数据、不写坏文件"""

    def test_concurrent_upsert_no_data_loss(self):
        errors = []

        def worker(i):
            try:
                ok, msg, _ = rbac.upsert_member({
                    "user_id": "uid_%d" % i,
                    "phone": "139%08d" % i,
                    "name": "同事%d" % i,
                    "allowed_projects": ["nextgeo"],
                    "permissions": ["report:view"],
                })
                if not ok:
                    errors.append(msg)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], "并发写入出现异常: %s" % errors)
        final = rbac.load_roster()
        self.assertEqual(len(final["members"]), 20, "并发写入丢数据")

    def test_corrupted_file_falls_back_to_default(self):
        with open(rbac.ROSTER_FILE, "w", encoding="utf-8") as f:
            f.write("{ this is not valid json")
        roster = rbac.load_roster()  # 不得抛异常
        self.assertEqual(roster["schema_version"], rbac.SCHEMA_VERSION)
        self.assertIn(DEV_PHONE, roster["developer_phones"])
        self.assertEqual(roster["members"], [])

    def test_missing_file_falls_back_to_default(self):
        os.remove(rbac.ROSTER_FILE)
        roster = rbac.load_roster()
        self.assertIn(DEV_PHONE, roster["developer_phones"])


class TestMemberManagement(RbacTestBase):
    """成员增删改停用流程"""

    def test_add_member(self):
        ok, msg, rec = rbac.upsert_member({
            "user_id": OP_USER_ID, "phone": OP_PHONE, "name": "张三",
            "allowed_projects": ["nextgeo"], "permissions": ["article:edit"],
        })
        self.assertTrue(ok, msg)
        self.assertEqual(rec["role"], rbac.ROLE_OPERATOR)
        self.assertEqual(rec["status"], rbac.STATUS_ACTIVE)

    def test_role_always_operator_even_if_upstream_says_admin(self):
        rbac.upsert_member({"phone": OP_PHONE, "name": "张三", "role": "admin"})
        rec = rbac.get_member(OP_PHONE)
        self.assertEqual(rec["role"], rbac.ROLE_OPERATOR)

    def test_developer_phone_cannot_be_operator(self):
        ok, msg, _ = rbac.upsert_member({"phone": DEV_PHONE, "name": "冒充者"})
        self.assertFalse(ok)
        self.assertIn("开发者", msg)

    def test_invalid_permission_filtered(self):
        rbac.upsert_member({
            "phone": OP_PHONE, "name": "张三",
            "permissions": ["article:edit", "not:a:real:permission"],
        })
        rec = rbac.get_member(OP_PHONE)
        self.assertEqual(rec["permissions"], ["article:edit"])

    def test_update_member(self):
        self.add_operator(["nextgeo"])
        ok, _, rec = rbac.upsert_member(
            {"allowed_projects": ["nextgeo", "client_a"], "status": "disabled"},
            key=OP_PHONE)
        self.assertTrue(ok)
        self.assertEqual(rec["allowed_projects"], ["nextgeo", "client_a"])
        self.assertEqual(rec["status"], "disabled")
        self.assertEqual(len(rbac.list_members()), 1, "修改不应新增记录")

    def test_delete_member(self):
        self.add_operator(["nextgeo"])
        ok, msg = rbac.delete_member(OP_PHONE)
        self.assertTrue(ok, msg)
        self.assertIsNone(rbac.get_member(OP_PHONE))

    def test_delete_missing_member(self):
        ok, _ = rbac.delete_member("not-exist")
        self.assertFalse(ok)

    def test_empty_phone_and_user_id_rejected(self):
        ok, msg, _ = rbac.upsert_member({"name": "无标识"})
        self.assertFalse(ok)


class TestProjectFilter(RbacTestBase):
    """服务端项目过滤（安全边界）"""

    def test_developer_sees_all(self):
        dev = rbac.resolve_identity(phone=DEV_PHONE)
        projects = [{"client_id": "a"}, {"client_id": "b"}, {"client_id": "c"}]
        self.assertEqual(len(rbac.filter_projects(projects, dev)), 3)

    def test_operator_sees_only_allowed(self):
        self.add_operator(["b"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        projects = [{"client_id": "a"}, {"client_id": "b"}, {"client_id": "c"}]
        out = rbac.filter_projects(projects, op)
        self.assertEqual([p["client_id"] for p in out], ["b"])

    def test_groups_filtered_by_allowed_projects(self):
        self.add_operator(["b"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        groups = [
            {
                "group_id": "g1",
                "group_name": "可见组",
                "parent_project_id": "b",
                "children": [
                    {"project_id": "b", "role": "主"},
                    {"project_id": "secret", "role": "子"},
                ],
            },
            {
                "group_id": "g2",
                "group_name": "别人的组",
                "parent_project_id": "secret",
                "children": [{"project_id": "secret"}],
            },
        ]
        out = rbac.filter_groups(groups, op)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["group_id"], "g1")
        self.assertEqual([c["project_id"] for c in out[0]["children"]], ["b"])

    def test_developer_by_user_id_without_phone(self):
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "developer_user_ids": ["dev-uid-1"],
            "members": [],
        })
        ident = rbac.resolve_identity(user_id="dev-uid-1", phone="")
        self.assertTrue(ident.is_developer)
        self.assertTrue(ident.matched)

    def test_disabled_operator_sees_nothing(self):
        self.add_operator(["b"], status="disabled")
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        projects = [{"client_id": "a"}, {"client_id": "b"}]
        self.assertEqual(rbac.filter_projects(projects, op), [])



class TestReadOnlyRoutesReleased(RbacTestBase):
    """只读展示类接口对运营放行（本次变更核心）"""

    def setUp(self):
        super().setUp()
        self.add_operator(["nextgeo"])
        self.op = rbac.resolve_identity(user_id=OP_USER_ID)

    def test_ledger_get_allowed(self):
        ok, status, msg = rbac.guard_route("/api/ops/check-ledger", "GET", self.op)
        self.assertTrue(ok, msg)

    def test_partners_get_allowed(self):
        ok, status, msg = rbac.guard_route("/api/partners", "GET", self.op)
        self.assertTrue(ok, msg)

    def test_notifications_get_allowed(self):
        ok, status, msg = rbac.guard_route("/api/settings/notifications", "GET", self.op)
        self.assertTrue(ok, msg)

    def test_writes_still_developer_only(self):
        cases = [
            ("/api/partners", "POST"),                  # 创建合作方
            ("/api/partners/p_001", "POST"),            # 改档/归档
            ("/api/settings/notifications", "POST"),    # 写通知配置
            ("/api/settings/notifications", "PUT"),
            ("/api/settings/notifications/test", "POST"),
            ("/api/batch/trigger", "POST"),
            ("/api/patrol/trigger", "POST"),
            ("/api/ops/check-logs", "GET"),
            ("/api/llm/config", "POST"),
        ]
        for path, method in cases:
            ok, status, _ = rbac.guard_route(path, method, self.op)
            self.assertFalse(ok, f"{method} {path} 应对运营 403")
            self.assertEqual(status, 403)

    def test_developer_keeps_full_access(self):
        dev = rbac.resolve_identity(phone=DEV_PHONE)
        for path, method in [("/api/partners", "POST"),
                             ("/api/partners/p_001", "POST"),
                             ("/api/settings/notifications", "POST"),
                             ("/api/batch/trigger", "POST")]:
            ok, _, msg = rbac.guard_route(path, method, dev)
            self.assertTrue(ok, f"{method} {path} 应对开发者放行: {msg}")


class TestLedgerTenantFilter(RbacTestBase):
    """台账多租户裁剪：只滤 rows 不重算 summary 等于泄露他户数量"""

    def _payload(self):
        return {
            "success": True,
            "policy": {"warn_days": 7},
            "rows": [
                {"project_id": "nextgeo", "client_name": "邻里", "status": "ok"},
                {"project_id": "nextgeo", "client_name": "邻里2", "status": "warn"},
                {"project_id": "demo_corp", "client_name": "智数", "status": "overdue"},
                {"project_id": "xuzhou_xuanyuan", "client_name": "璇源", "status": "never"},
            ],
            "summary": {"never": 1, "overdue": 1, "warn": 1, "ok": 1, "total": 4},
            "generated_at": "2026-09-18T00:00:00Z",
        }

    def test_operator_sees_only_authorized_projects(self):
        self.add_operator(["nextgeo"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        out = rbac.filter_check_ledger(self._payload(), op)
        ids = {r["project_id"] for r in out["rows"]}
        self.assertEqual(ids, {"nextgeo"}, "运营看到了未授权项目")

    def test_summary_recomputed_not_leaked(self):
        self.add_operator(["nextgeo"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        out = rbac.filter_check_ledger(self._payload(), op)
        # 全站是 total=4，运营应只剩 2 条；若 summary 仍是 4 说明没重算
        self.assertEqual(out["summary"]["total"], 2)
        self.assertEqual(out["summary"]["ok"], 1)
        self.assertEqual(out["summary"]["warn"], 1)
        self.assertEqual(out["summary"]["overdue"], 0)
        self.assertEqual(out["summary"]["never"], 0)

    def test_developer_sees_full(self):
        dev = rbac.resolve_identity(phone=DEV_PHONE)
        out = rbac.filter_check_ledger(self._payload(), dev)
        self.assertEqual(len(out["rows"]), 4)
        self.assertEqual(out["summary"]["total"], 4)

    def test_disabled_operator_sees_nothing(self):
        self.add_operator(["nextgeo"], status="disabled")
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        out = rbac.filter_check_ledger(self._payload(), op)
        self.assertEqual(out["rows"], [])
        self.assertEqual(out["summary"]["total"], 0)


class TestSiteRoutesGuarded(RbacTestBase):
    """站点预览/资源/状态/下载：移入鉴权门之后，必须受守卫约束"""

    def setUp(self):
        super().setUp()
        self.add_operator(["nextgeo"])
        self.op = rbac.resolve_identity(user_id=OP_USER_ID)
        self.dev = rbac.resolve_identity(phone=DEV_PHONE)
        self.anon = rbac.resolve_identity()

    def test_anonymous_denied(self):
        for path in ("/api/projects/nextgeo/site/preview",
                     "/api/projects/nextgeo/site/status",
                     "/api/projects/nextgeo/site/index.html"):
            ok, status, _ = rbac.guard_route(path, "GET", self.anon)
            self.assertFalse(ok, f"{path} 未登录不应放行")
            self.assertEqual(status, 401)

    def test_operator_own_project_preview_allowed(self):
        ok, _, msg = rbac.guard_route("/api/projects/nextgeo/site/preview", "GET", self.op)
        self.assertTrue(ok, msg)
        ok, _, msg = rbac.guard_route("/api/projects/nextgeo/site/status", "GET", self.op)
        self.assertTrue(ok, msg)

    def test_operator_cross_project_preview_denied(self):
        ok, status, _ = rbac.guard_route("/api/projects/demo_corp/site/preview", "GET", self.op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_site_download_developer_only(self):
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/site/download", "GET", self.op)
        self.assertFalse(ok, "运营不应能下载整站源码 ZIP")
        self.assertEqual(status, 403)
        ok, _, msg = rbac.guard_route("/api/projects/nextgeo/site/download", "GET", self.dev)
        self.assertTrue(ok, msg)

    def test_developer_can_preview_any_project(self):
        ok, _, msg = rbac.guard_route("/api/projects/demo_corp/site/preview", "GET", self.dev)
        self.assertTrue(ok, msg)


class TestPortfolioRoutesForOperator(RbacTestBase):
    """仪表盘大盘接口：运营可读，且汇总只含白名单项目"""

    def setUp(self):
        super().setUp()
        self.add_operator(["nextgeo"])
        self.op = rbac.resolve_identity(user_id=OP_USER_ID)
        self.dev = rbac.resolve_identity(phone=DEV_PHONE)

    def test_portfolio_routes_allowed_for_operator(self):
        for path, method in (
            ("/api/portfolio/summary", "GET"),
            ("/api/portfolio/report", "GET"),
            ("/api/portfolio/patrol", "POST"),
        ):
            ok, status, msg = rbac.guard_route(path, method, self.op)
            self.assertTrue(ok, f"{method} {path} 应对运营放行: {msg}")

    def test_portfolio_summary_scoped_to_allowed_projects(self):
        from tools.geo.portfolio import get_portfolio_summary
        scoped = get_portfolio_summary(allowed_project_ids=["nextgeo"])
        ids = {c.get("project_id") for c in (scoped.get("project_cards") or [])}
        self.assertTrue(ids.issubset({"nextgeo"}), f"运营大盘泄露他户: {ids}")
        self.assertEqual(scoped.get("scale", {}).get("total_projects"), len(ids))
        full = get_portfolio_summary(allowed_project_ids=None)
        # 全量至少不少于白名单视角（仓库里通常有多个项目）
        self.assertGreaterEqual(
            full.get("scale", {}).get("total_projects", 0),
            scoped.get("scale", {}).get("total_projects", 0),
        )


class TestStripPartnerForOperator(RbacTestBase):
    def test_strip_partner_fields(self):
        self.add_operator(["nextgeo"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        payload = {
            "projects": [
                {"client_id": "nextgeo", "partner_id": "p1", "partner_name": "渠道张三"},
            ]
        }
        out = rbac.strip_partner_fields(payload, op)
        self.assertNotIn("partner_id", out["projects"][0])
        self.assertNotIn("partner_name", out["projects"][0])
        self.assertEqual(out["projects"][0]["client_id"], "nextgeo")

    def test_meta_post_developer_only(self):
        self.add_operator(["nextgeo"])
        op = rbac.resolve_identity(user_id=OP_USER_ID)
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/meta", "POST", op)
        self.assertFalse(ok)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
