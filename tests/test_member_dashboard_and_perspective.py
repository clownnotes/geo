# -*- coding: utf-8 -*-
"""成员管理交付看板与企业透视改造测试 (tests/test_member_dashboard_and_perspective.py)

对应 openspec 变更：2026-09-20-成员管理交付看板与企业透视改造
覆盖：
1. 透视聚合与自建判定（只认 creator_user_id，禁止以姓名猜，老项目无该字段算分配）；
2. 进度算法（同 GET /api/projects 扫 outputs/ 01_~05_）与摸底状态枚举严格约束；
3. assign_member_project 与 unassign_member_project 原子读写与幂等性；
4. 极简开通：仅凭姓名+手机号入库，默认赋予全部 PERMISSION_CODES；
5. 首次登录回写：会话带 user_id 且花名册该成员 user_id 为空时加锁落盘；
6. DELETE 路由顺序：先收回企业管辖权，再删整人；
7. 视觉规范：0 Emoji 违规，主文案严禁出现「SOP」。
"""

import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402
from tools.geo import perspective  # noqa: E402

DEV_PHONE = "13150568888"


class MemberDashboardAndPerspectiveTest(unittest.TestCase):

    def setUp(self):
        self._orig_roster_file = rbac.ROSTER_FILE
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_member_test_")
        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "members": [],
        })
        self.projects_dir = os.path.join(self.tmp_dir, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)

    def tearDown(self):
        rbac.ROSTER_FILE = self._orig_roster_file
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _create_mock_project(self, slug, name, creator_user_id="", creator_name="",
                             probe_status="unprobed", output_files=None):
        p_dir = os.path.join(self.projects_dir, slug)
        out_dir = os.path.join(p_dir, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        yaml_content = f"""client_id: "{slug}"
client_name: "{name}"
creator_user_id: "{creator_user_id}"
creator_name: "{creator_name}"
probe_status: "{probe_status}"
"""
        with open(os.path.join(p_dir, "project.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        if output_files:
            for f in output_files:
                with open(os.path.join(out_dir, f), "w", encoding="utf-8") as out_f:
                    out_f.write("mock content")
        return p_dir

    def test_minimal_upsert_member_defaults(self):
        """1. 极简开通：仅凭姓名+手机号入库，默认赋予全部 PERMISSION_CODES，user_id 允许为空"""
        ok, msg, rec = rbac.upsert_member({
            "name": "测试运营李四",
            "phone": "13805206070",
        })
        self.assertTrue(ok, msg)
        self.assertEqual(rec["name"], "测试运营李四")
        self.assertEqual(rec["phone"], "13805206070")
        self.assertEqual(rec["user_id"], "")
        self.assertEqual(set(rec["permissions"]), set(rbac.PERMISSION_CODES))
        self.assertEqual(rec["status"], rbac.STATUS_ACTIVE)

    def test_sync_member_user_id_on_login(self):
        """2. 首次登录回写：手机号命中运营人员且会话带 user_id、花名册 user_id 为空时写回落盘"""
        ok, msg, rec = rbac.upsert_member({
            "name": "待登录运营王五",
            "phone": "13805206071",
        })
        self.assertTrue(ok, msg)
        self.assertEqual(rec["user_id"], "")

        # 模拟登录时触发 sync_member_user_id_on_login
        res = rbac.sync_member_user_id_on_login("13805206071", "user_snowflake_1001")
        self.assertTrue(res)

        # 检查花名册中是否已落盘写回
        updated_member = rbac.get_member("13805206071")
        self.assertIsNotNone(updated_member)
        self.assertEqual(updated_member["user_id"], "user_snowflake_1001")

        # 验证 resolve_identity 也能自动触发写回
        rbac.upsert_member({"name": "赵六", "phone": "13805206072"})
        m_before = rbac.get_member("13805206072")
        self.assertEqual(m_before["user_id"], "")

        ident = rbac.resolve_identity(user_id="user_snowflake_1002", phone="13805206072")
        self.assertEqual(ident.user_id, "user_snowflake_1002")
        m_after = rbac.get_member("13805206072")
        self.assertEqual(m_after["user_id"], "user_snowflake_1002")

    def test_assign_and_unassign_member_project(self):
        """3. 分配与收回企业管辖：原子性、幂等性与 SSOT 复用"""
        rbac.upsert_member({
            "name": "运营小孙",
            "phone": "13805206073",
            "allowed_projects": ["proj_initial"],
        })

        # 分配新企业
        ok, msg = rbac.assign_member_project("13805206073", "proj_added")
        self.assertTrue(ok)
        m = rbac.get_member("13805206073")
        self.assertIn("proj_added", m["allowed_projects"])
        self.assertIn("proj_initial", m["allowed_projects"])

        # 幂等追加
        ok2, msg2 = rbac.assign_member_project("13805206073", "proj_added")
        self.assertTrue(ok2)
        m2 = rbac.get_member("13805206073")
        self.assertEqual(m2["allowed_projects"].count("proj_added"), 1)

        # 收回企业
        ok_un, msg_un = rbac.unassign_member_project("13805206073", "proj_added")
        self.assertTrue(ok_un)
        m3 = rbac.get_member("13805206073")
        self.assertNotIn("proj_added", m3["allowed_projects"])
        self.assertIn("proj_initial", m3["allowed_projects"])

        # 幂接收回
        ok_un2, _ = rbac.unassign_member_project("13805206073", "proj_added")
        self.assertTrue(ok_un2)

        # 验证 append_member_allowed_project 复用
        appended = rbac.append_member_allowed_project(phone="13805206073", project_id="proj_from_creation")
        self.assertTrue(appended)
        m4 = rbac.get_member("13805206073")
        self.assertIn("proj_from_creation", m4["allowed_projects"])

    def test_perspective_enrichment_and_self_created_rule(self):
        """4. 透视聚合：自建只认 creator_user_id，禁止姓名猜，老项目无该字段算分配"""
        # 创建三个 mock 项目：
        # proj_self: creator_user_id == "op_uid_888" -> 自建
        # proj_assigned: creator_user_id == "other_uid" -> 老板分配
        # proj_legacy_same_name: creator_user_id 为空，creator_name == "运营小钱" -> 依然算老板分配！
        self._create_mock_project(
            "proj_self", "小钱自建科技有限公司",
            creator_user_id="op_uid_888", creator_name="运营小钱",
            probe_status="baseline_ready",
            output_files=["01_diag.md", "02_scaffold.html", "03_princeton.md"]
        )
        self._create_mock_project(
            "proj_assigned", "老板划拨产业有限公司",
            creator_user_id="boss_uid", creator_name="老板",
            probe_status="unprobed",
            output_files=["01_diag.md"]
        )
        self._create_mock_project(
            "proj_legacy_same_name", "同名老项目股份有限公司",
            creator_user_id="", creator_name="运营小钱",
            probe_status="awaiting_retest",
            output_files=["01_diag.md", "02_scaffold.html", "03_princeton.md", "04_distribute.md", "05_acceptance.md"]
        )

        member = {
            "name": "运营小钱",
            "phone": "13805206088",
            "user_id": "op_uid_888",
            "status": "active",
            "allowed_projects": ["proj_self", "proj_assigned", "proj_legacy_same_name"],
        }

        enriched = perspective.build_members_perspective([member], self.projects_dir)
        self.assertEqual(len(enriched), 1)
        card = enriched[0]

        # 统计核对
        self.assertEqual(card["total_count"], 3)
        self.assertEqual(card["self_created_count"], 1)
        self.assertEqual(card["assigned_count"], 2)

        proj_map = {p["client_id"]: p for p in card["projects"]}

        # 1) proj_self
        p_self = proj_map["proj_self"]
        self.assertTrue(p_self["is_self_created"])
        self.assertEqual(p_self["origin_label"], "自建")
        self.assertEqual(p_self["probe_status"], "baseline_ready")
        self.assertEqual(p_self["steps_done"], 3)
        self.assertEqual(p_self["progress_pct"], 60)
        self.assertTrue(bool(p_self["updated_at"]))

        # 2) proj_assigned
        p_ass = proj_map["proj_assigned"]
        self.assertFalse(p_ass["is_self_created"])
        self.assertEqual(p_ass["origin_label"], "老板分配")
        self.assertEqual(p_ass["probe_status"], "unprobed")
        self.assertEqual(p_ass["steps_done"], 1)
        self.assertEqual(p_ass["progress_pct"], 20)

        # 3) proj_legacy_same_name（即使 creator_name 同名，无 creator_user_id 也绝不判自建）
        p_leg = proj_map["proj_legacy_same_name"]
        self.assertFalse(p_leg["is_self_created"])
        self.assertEqual(p_leg["origin_label"], "老板分配")
        self.assertEqual(p_leg["probe_status"], "awaiting_retest")
        self.assertEqual(p_leg["steps_done"], 5)
        self.assertEqual(p_leg["progress_pct"], 100)

    def test_delete_route_order_precedence(self):
        """5. DELETE 路由正则匹配：先匹配 .../projects/{id} 收回，再匹配删整人"""
        path_unassign = "/api/admin/members/13805206088/projects/proj_self"
        m_proj = re.match(r"^/api/admin/members/([^/]+)/projects/([^/]+)$", path_unassign)
        self.assertIsNotNone(m_proj)
        self.assertEqual(m_proj.group(1), "13805206088")
        self.assertEqual(m_proj.group(2), "proj_self")

        path_delete_member = "/api/admin/members/13805206088"
        m_proj2 = re.match(r"^/api/admin/members/([^/]+)/projects/([^/]+)$", path_delete_member)
        self.assertIsNone(m_proj2)

    def test_ui_no_emoji_and_no_sop_text(self):
        """6. UI 规范合规：0 违规 Emoji，界面主文案严禁使用「SOP」"""
        web_index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "index.html")
        with open(web_index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 panel-home-members 与成员 JS
        panel_match = re.search(r'id="panel-home-members"[\s\S]*?</section>', content)
        self.assertIsNotNone(panel_match, "未找到 panel-home-members 节点")
        panel_html = panel_match.group(0)

        js_match = re.search(r'// ---- 成员交付看板管理[\s\S]*?function getStep0BridgeProps', content)
        self.assertIsNotNone(js_match, "未找到成员管理 JS 区域")
        member_js = js_match.group(0)

        # 1) 0 Emoji 检测
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
        emojis_in_panel = emoji_pattern.findall(panel_html)
        emojis_in_js = emoji_pattern.findall(member_js)
        self.assertEqual(len(emojis_in_panel), 0, f"panel-home-members 发现 Emoji: {emojis_in_panel}")
        self.assertEqual(len(emojis_in_js), 0, f"member JS 发现 Emoji: {emojis_in_js}")

        # 2) 界面主文案禁止 SOP
        self.assertNotIn("SOP", panel_html, "panel-home-members 出现 SOP 文案")
        self.assertNotIn("SOP", member_js, "成员管理 JS 出现 SOP 文案")

        # 3) 确认白话进度文案存在
        self.assertIn("还在豆包摸底", member_js)
        self.assertIn("豆包答案已存进项目", member_js)
        self.assertIn("待复测", member_js)
        self.assertIn("已结案", member_js)


class TestMemberApiIntegration(unittest.TestCase):
    """真实 HTTP 服务集成测试：验证 GET /api/admin/members、POST .../projects 与 DELETE .../projects/{id}"""

    @classmethod
    def setUpClass(cls):
        from tools.geo.server import GeoWebHandler, create_session
        from http.server import ThreadingHTTPServer

        cls._orig_roster_file = rbac.ROSTER_FILE
        cls.tmp_dir = tempfile.mkdtemp(prefix="geo_member_api_test_")
        rbac.ROSTER_FILE = os.path.join(cls.tmp_dir, "rbac_members.json")
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "members": [],
        })

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GeoWebHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        cls.token = create_session(
            username="开发者师兄",
            user_id="dev_uid_999",
            phone=DEV_PHONE,
            role="developer",
            credits=9999,
        )
        cls.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.token}",
        }

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        rbac.ROSTER_FILE = cls._orig_roster_file
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def _request(self, method: str, path: str, body: dict = None):
        import urllib.request
        import urllib.error
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8")
                return status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            err_raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(err_raw)
            except Exception:
                return e.code, {"error": err_raw}

    def test_full_member_management_lifecycle_via_api(self):
        # 1. 开通新成员 (POST /api/admin/members)
        st, res = self._request("POST", "/api/admin/members", {
            "name": "接口测试员工",
            "phone": "13805209999",
        })
        self.assertEqual(st, 200, res)
        self.assertTrue(res["success"])
        self.assertEqual(res["member"]["name"], "接口测试员工")
        self.assertEqual(len(res["member"]["permissions"]), len(rbac.PERMISSION_CODES))

        # 2. 读取成员大盘与透视 (GET /api/admin/members)
        st, res = self._request("GET", "/api/admin/members")
        self.assertEqual(st, 200)
        self.assertTrue(res["success"])
        self.assertIn("members", res)
        target = next((m for m in res["members"] if m.get("phone") == "13805209999"), None)
        self.assertIsNotNone(target)
        self.assertEqual(target["total_count"], 0)
        self.assertEqual(target["self_created_count"], 0)
        self.assertEqual(target["assigned_count"], 0)
        self.assertEqual(target["projects"], [])

        # 3. 追加分配已有企业 (POST /api/admin/members/{key}/projects)
        # 挑选现网真实存在的项目，例如 nextgeo
        st, res = self._request("POST", "/api/admin/members/13805209999/projects", {
            "project_id": "nextgeo"
        })
        self.assertEqual(st, 200, res)
        self.assertTrue(res["success"])

        # 再次读取，验证透视数据
        st, res = self._request("GET", "/api/admin/members")
        target = next((m for m in res["members"] if m.get("phone") == "13805209999"), None)
        self.assertEqual(target["total_count"], 1)
        self.assertEqual(len(target["projects"]), 1)
        proj_item = target["projects"][0]
        self.assertEqual(proj_item["client_id"], "nextgeo")
        self.assertIn("steps_done", proj_item)
        self.assertIn("progress_pct", proj_item)

        # 4. 收回企业管辖权 (DELETE /api/admin/members/{key}/projects/{project_id})
        st, res = self._request("DELETE", "/api/admin/members/13805209999/projects/nextgeo")
        self.assertEqual(st, 200, res)
        self.assertTrue(res["success"])

        # 核心验证：DELETE 收回企业管辖权后，该成员必须仍然存在，不可被整人删除！
        st, res = self._request("GET", "/api/admin/members")
        target = next((m for m in res["members"] if m.get("phone") == "13805209999"), None)
        self.assertIsNotNone(target, "收回企业管辖权误把成员本人删除了！")
        self.assertEqual(target["total_count"], 0)

        # 5. 最终删除成员 (DELETE /api/admin/members/{key})
        st, res = self._request("DELETE", "/api/admin/members/13805209999")
        self.assertEqual(st, 200, res)
        self.assertTrue(res["success"])

        # 确认彻底删除
        st, res = self._request("GET", "/api/admin/members")
        target = next((m for m in res["members"] if m.get("phone") == "13805209999"), None)
        self.assertIsNone(target)


if __name__ == "__main__":
    unittest.main()
