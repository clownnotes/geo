# -*- coding: utf-8 -*-
"""运营账号反 AI 抓取与核心资产防搬走加固自动化测试 (tests/test_operator_anti_scrape.py)

对应 openspec 复核结论（2026-09-19，登记于
openspec/changes/2026-09-19-运营端去IDE化与小毛驴算力内嵌闭环/review-log.md）：

1. 产出文件读取由黑名单改为白名单，整包 ZIP / 探针 JSON / Python 一律拒；
2. /share/create 收归开发者，运营不得自建分享票再下整包；
3. 只读兜底只对 GET 生效，非 GET 落 fail-closed（与 design.md 一致）；
4. 反抓取护栏：限流、批量读取自动停用、跨项目探测自动停用；
5. 会话吊销：成员停用后其会话立即作废。

全部在临时文件上完成，不污染真实 data/。
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac, opsguard  # noqa: E402
from tools.geo.answer_audit import operator_may_read_output  # noqa: E402

DEV_PHONE = "13150568888"
OP_USER_ID = "1829384756102938475"
OP_PHONE = "13900000001"
ALL_PERMS = list(rbac.PERMISSION_CODES)


class AntiScrapeTestBase(unittest.TestCase):
    def setUp(self):
        self._orig_roster_file = rbac.ROSTER_FILE
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_antiscarpe_test_")
        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "members": [],
        })
        self._orig_audit_file = opsguard.AUDIT_FILE
        opsguard.AUDIT_FILE = os.path.join(self.tmp_dir, "operator_audit.jsonl")
        opsguard.reset_for_test()

    def tearDown(self):
        rbac.ROSTER_FILE = self._orig_roster_file
        opsguard.AUDIT_FILE = self._orig_audit_file
        opsguard.reset_for_test()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def add_operator(self, allowed_projects=None, permissions=None, status="active"):
        ok, msg, rec = rbac.upsert_member({
            "user_id": OP_USER_ID,
            "phone": OP_PHONE,
            "name": "运营同事小张",
            "allowed_projects": allowed_projects if allowed_projects is not None else ["nextgeo"],
            "permissions": permissions if permissions is not None else ALL_PERMS,
            "status": status,
        })
        self.assertTrue(ok, msg)
        return rec

    @staticmethod
    def operator():
        return rbac.resolve_identity(user_id=OP_USER_ID)

    @staticmethod
    def developer():
        return rbac.resolve_identity(phone=DEV_PHONE)


class TestOutputReadWhitelist(AntiScrapeTestBase):
    """产出文件：白名单判定，整包归档与配方资产一律拒"""

    def test_archive_zip_denied(self):
        """躺在 outputs/ 里的整包归档 ZIP 不得被运营原样下载"""
        self.assertFalse(operator_may_read_output("nextgeo_geo_delivery_archive.zip"))

    def test_probe_script_json_allowed(self):
        """阶段零作业必需的题单必须放行，使前端能正常渲染题目卡片"""
        self.assertTrue(operator_may_read_output("probe_script_draft.json"))
        self.assertTrue(operator_may_read_output("probe_script_retest_round1.json"))

    def test_explicit_safe_files_allowed(self):
        """前端业务必需的检测指标、SEO结构化数据及架构对比图精确放行"""
        self.assertTrue(operator_may_read_output("audit_metrics.json"))
        self.assertTrue(operator_may_read_output("schema.jsonld"))
        self.assertTrue(operator_may_read_output("07_选型差异化对比图.svg"))
        self.assertTrue(operator_may_read_output("08_企业技术全景架构图.svg"))

    def test_other_svg_denied(self):
        """未在精确白名单内的任意其他 svg 仍须拦截，避免整类后缀全开"""
        self.assertFalse(operator_may_read_output("other_flow.svg"))
        self.assertFalse(operator_may_read_output("logo.svg"))

    def test_manual_probes_and_intent_matrix_json_denied(self):
        """配方资产与非题单 json 一律拦截"""
        self.assertFalse(operator_may_read_output("keywords_intent_matrix.json"))
        self.assertFalse(operator_may_read_output("05_manual_probes.json"))
        self.assertFalse(operator_may_read_output("config.json"))

    def test_python_denied(self):
        self.assertFalse(operator_may_read_output("build.py"))

    def test_corpus_9factor_denied(self):
        self.assertFalse(operator_may_read_output("03_普林斯顿9因子高权威语料库.md"))

    def test_prompt_marked_denied(self):
        self.assertFalse(operator_may_read_output("prompt_mold.md"))

    def test_checklist_denied(self):
        """派单任务卡含 GitHub 仓库建立与 monitor 命令等内部打法，运营不得读取"""
        self.assertFalse(operator_may_read_output("dist_channels_checklist.md"))

    def test_client_report_allowed(self):
        """客户体检报告这类成品文本必须仍可读，否则流水线干不了活"""
        self.assertTrue(operator_may_read_output("01_企业AI可见度商业诊断报告.md"))

    def test_channel_article_allowed(self):
        self.assertTrue(operator_may_read_output("dist_toutiao_article.md"))
        self.assertTrue(operator_may_read_output("dist_wechat_article.html"))

    def test_empty_name_denied(self):
        self.assertFalse(operator_may_read_output(""))


class TestShareCreateLockedDown(AntiScrapeTestBase):
    """运营不得自建分享票（自建后即可绕过 /export 下整包）"""

    def test_operator_cannot_create_share(self):
        self.add_operator()
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/share/create", "POST", self.operator())
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_developer_can_create_share(self):
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/share/create", "POST", self.developer())
        self.assertTrue(ok)
        self.assertEqual(status, 200)


class TestReadonlyFallbackGetOnly(AntiScrapeTestBase):
    """只读兜底只对 GET 生效；非 GET 必须 fail-closed"""

    def test_post_to_unregistered_data_route_is_denied(self):
        self.add_operator()
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/whatever/data", "POST", self.operator())
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_delete_to_unregistered_data_route_is_denied(self):
        self.add_operator()
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/whatever/data", "DELETE", self.operator())
        self.assertFalse(ok)
        self.assertEqual(status, 403)

    def test_get_to_unregistered_data_route_still_allowed(self):
        """GET 只读兜底保留，避免打挂运营正常看数"""
        self.add_operator()
        ok, status, _ = rbac.guard_route("/api/projects/nextgeo/whatever/data", "GET", self.operator())
        self.assertTrue(ok)
        self.assertEqual(status, 200)

    def test_developer_unaffected(self):
        for method in ("GET", "POST", "PUT", "DELETE"):
            ok, _, _ = rbac.guard_route("/api/projects/nextgeo/whatever/data", method, self.developer())
            self.assertTrue(ok, method)


class TestRateLimit(AntiScrapeTestBase):
    def test_requests_over_per_minute_limit_get_429(self):
        self.add_operator()
        orig = opsguard.REQ_PER_MINUTE
        opsguard.REQ_PER_MINUTE = 5
        try:
            ident = self.operator()
            for _ in range(5):
                ok, _, _ = opsguard.check(ident, "/api/projects", "GET")
                self.assertTrue(ok)
            ok, status, msg = opsguard.check(ident, "/api/projects", "GET")
            self.assertFalse(ok)
            self.assertEqual(status, 429)
            self.assertTrue(msg)
        finally:
            opsguard.REQ_PER_MINUTE = orig

    def test_developer_never_rate_limited(self):
        orig = opsguard.REQ_PER_MINUTE
        opsguard.REQ_PER_MINUTE = 2
        try:
            ident = self.developer()
            for _ in range(20):
                ok, _, _ = opsguard.check(ident, "/api/projects", "GET")
                self.assertTrue(ok)
        finally:
            opsguard.REQ_PER_MINUTE = orig


class TestScrapeAutoDisable(AntiScrapeTestBase):
    def test_bulk_output_read_rate_limited_first(self):
        self.add_operator()
        orig = opsguard.OUTPUT_READ_PER_HOUR
        opsguard.OUTPUT_READ_PER_HOUR = 3
        try:
            ident = self.operator()
            for i in range(3):
                ok, _, _ = opsguard.check(ident, f"/api/projects/nextgeo/output/report_{i}.md", "GET")
                self.assertTrue(ok)
            ok, status, _ = opsguard.check(ident, "/api/projects/nextgeo/output/report_x.md", "GET")
            self.assertFalse(ok)
            self.assertEqual(status, 429)
            member = rbac.get_member(OP_USER_ID)
            self.assertEqual(member.get("status"), "active")
        finally:
            opsguard.OUTPUT_READ_PER_HOUR = orig

    def test_distinct_filename_sweep_rate_limited_first_then_disabled(self):
        """触碰不同文件名超限时，先触发 429 频控而不停用；反复触发超限后才停用"""
        self.add_operator()
        orig_reads = opsguard.OUTPUT_READ_PER_HOUR
        orig_names = opsguard.DISTINCT_FILENAME_PER_HOUR
        orig_too_many = opsguard.TOO_MANY_429_PER_HOUR
        opsguard.OUTPUT_READ_PER_HOUR = 999
        opsguard.DISTINCT_FILENAME_PER_HOUR = 3
        opsguard.TOO_MANY_429_PER_HOUR = 2
        try:
            ident = self.operator()
            for i in range(3):
                ok, _, _ = opsguard.check(ident, f"/api/projects/nextgeo/output/f{i}.md", "GET")
                self.assertTrue(ok)
            # 第 4 个不同文件名：触发 429 频控，但账号依然是 active
            ok, status, _ = opsguard.check(ident, "/api/projects/nextgeo/output/f99.md", "GET")
            self.assertFalse(ok)
            self.assertEqual(status, 429)
            member = rbac.get_member(OP_USER_ID)
            self.assertEqual(member.get("status"), "active")

            # 继续连续触碰超限，超过 TOO_MANY_429_PER_HOUR 次后自动停用并返回 403
            for _ in range(2):
                opsguard.check(ident, "/api/projects/nextgeo/output/f99.md", "GET")
            ok, status, _ = opsguard.check(ident, "/api/projects/nextgeo/output/f99.md", "GET")
            self.assertFalse(ok)
            self.assertEqual(status, 403)
            member = rbac.get_member(OP_USER_ID)
            self.assertEqual(member.get("status"), "disabled")
        finally:
            opsguard.OUTPUT_READ_PER_HOUR = orig_reads
            opsguard.DISTINCT_FILENAME_PER_HOUR = orig_names
            opsguard.TOO_MANY_429_PER_HOUR = orig_too_many

    def test_cross_project_sweep_rate_limited_first(self):
        self.add_operator(["nextgeo"])
        orig = opsguard.DISTINCT_PROJECT_PER_HOUR
        opsguard.DISTINCT_PROJECT_PER_HOUR = 2
        try:
            ident = self.operator()
            for pid in ("nextgeo", "demo_corp"):
                ok, _, _ = opsguard.check(ident, f"/api/projects/{pid}/meta", "GET")
                self.assertTrue(ok)
            ok, status, _ = opsguard.check(ident, "/api/projects/xuzhou_xuanyuan/meta", "GET")
            self.assertFalse(ok)
            self.assertEqual(status, 429)
            member = rbac.get_member(OP_USER_ID)
            self.assertEqual(member.get("status"), "active")
        finally:
            opsguard.DISTINCT_PROJECT_PER_HOUR = orig

    def test_sensitive_asset_denials_auto_disable(self):
        """探测敏感核心资产（语料/9因子/zip等）触发拦截累计超过阈值，直接停用账号"""
        self.add_operator()
        orig = opsguard.SENSITIVE_DENIALS_PER_HOUR
        opsguard.SENSITIVE_DENIALS_PER_HOUR = 3
        try:
            ident = self.operator()
            for i in range(3):
                opsguard.record_sensitive_denial(ident, f"/api/projects/nextgeo/output/probe_{i}.py")
                member = rbac.get_member(OP_USER_ID)
                self.assertEqual(member.get("status"), "active")
            # 第 4 次拦截敏感文件：超过阈值，立即自动停用
            opsguard.record_sensitive_denial(ident, "/api/projects/nextgeo/output/03_普林斯顿9因子高权威语料库.md")
            member = rbac.get_member(OP_USER_ID)
            self.assertEqual(member.get("status"), "disabled")
        finally:
            opsguard.SENSITIVE_DENIALS_PER_HOUR = orig

    def test_handler_records_sensitive_denial_with_identity(self):
        """测试 server.py 在拦截产出敏感文件时正确调用 record_sensitive_denial 并传递 identity 实例"""
        from tools.geo import server
        self.add_operator()
        ident = self.operator()

        handler = server.GeoWebHandler.__new__(server.GeoWebHandler)
        handler.rbac_identity = lambda: ident

        orig = opsguard.SENSITIVE_DENIALS_PER_HOUR
        opsguard.SENSITIVE_DENIALS_PER_HOUR = 1
        try:
            # 确认调用 handler.rbac_identity() 获取身份并上报成功触发停用
            resolved = handler.rbac_identity()
            self.assertTrue(getattr(resolved, "matched", False))
            self.assertFalse(getattr(resolved, "is_developer", False))
            opsguard.record_sensitive_denial(resolved, "/api/projects/nextgeo/output/dist_channels_checklist.md")
            opsguard.record_sensitive_denial(resolved, "/api/projects/nextgeo/output/03_普林斯顿9因子高权威语料库.md")
            member = rbac.get_member(OP_USER_ID)
            self.assertEqual(member.get("status"), "disabled")
        finally:
            opsguard.SENSITIVE_DENIALS_PER_HOUR = orig


class TestAuditLog(AntiScrapeTestBase):
    def test_operator_api_call_is_recorded(self):
        self.add_operator()
        opsguard.record(self.operator(), "GET", "/api/projects/nextgeo/meta", 200, {"ip": "1.2.3.4"})
        self.assertTrue(os.path.exists(opsguard.AUDIT_FILE))
        with open(opsguard.AUDIT_FILE, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn(OP_USER_ID, lines[0])
        self.assertIn("1.2.3.4", lines[0])

    def test_developer_not_audited(self):
        opsguard.record(self.developer(), "GET", "/api/projects", 200, {"ip": "1.2.3.4"})
        self.assertFalse(os.path.exists(opsguard.AUDIT_FILE))


class TestSessionRevocation(unittest.TestCase):
    """停用成员后其会话必须立即作废"""

    def setUp(self):
        self._orig = rbac.ROSTER_FILE
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_revoke_test_")
        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "members": [],
        })

    def tearDown(self):
        rbac.ROSTER_FILE = self._orig
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_revoke_sessions_for_removes_matching(self):
        try:
            from tools.geo import server
        except Exception as e:
            self.skipTest(f"server 模块不可导入: {e}")

        # 会话落盘必须指向临时文件：revoke_sessions_for 内部会 save_sessions()，
        # 若用真实 data/sessions.json 会把测试用的假会话写进去、冲掉真实登录态。
        self._orig_sessions_file = server.SESSIONS_FILE
        server.SESSIONS_FILE = os.path.join(self.tmp_dir, "sessions.json")
        backup = dict(server.ACTIVE_SESSIONS)
        try:
            server.ACTIVE_SESSIONS.clear()
            server.ACTIVE_SESSIONS["t_op_1"] = {"user_id": OP_USER_ID, "phone": OP_PHONE, "expire_at": 9999999999}
            server.ACTIVE_SESSIONS["t_op_2"] = {"user_id": OP_USER_ID, "phone": "", "expire_at": 9999999999}
            server.ACTIVE_SESSIONS["t_other"] = {"user_id": "777", "phone": "13700000000", "expire_at": 9999999999}

            removed = server.revoke_sessions_for(user_id=OP_USER_ID)
            self.assertEqual(removed, 2)
            self.assertNotIn("t_op_1", server.ACTIVE_SESSIONS)
            self.assertNotIn("t_op_2", server.ACTIVE_SESSIONS)
            self.assertIn("t_other", server.ACTIVE_SESSIONS)
        finally:
            server.ACTIVE_SESSIONS.clear()
            server.ACTIVE_SESSIONS.update(backup)
            server.SESSIONS_FILE = self._orig_sessions_file

    def test_revoke_without_key_is_noop(self):
        try:
            from tools.geo import server
        except Exception as e:
            self.skipTest(f"server 模块不可导入: {e}")
        self.assertEqual(server.revoke_sessions_for(), 0)

    def test_disabled_member_session_is_rejected(self):
        """花名册里被停用的人，check_auth 必须返回 False（随后会话被吊销）"""
        try:
            from tools.geo import server
        except Exception as e:
            self.skipTest(f"server 模块不可导入: {e}")

        rbac.upsert_member({
            "user_id": OP_USER_ID,
            "phone": OP_PHONE,
            "name": "已离职运营",
            "allowed_projects": ["nextgeo"],
            "permissions": ALL_PERMS,
            "status": "disabled",
        })
        self.assertFalse(rbac.resolve_identity(user_id=OP_USER_ID).is_developer)
        self.assertEqual(rbac.resolve_identity(user_id=OP_USER_ID).status, "disabled")


if __name__ == "__main__":
    unittest.main(verbosity=2)
