#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：第 34 维 豆包搜索极速收录与全链路索引保障中枢 (tests/test_doubao_indexer.py)
测试范围：
1. 六维收录要素体检器与事实红线（未实测严禁捏造虚假百分比，必须为 None）；
2. 专属提权加速包生成器 outputs/doubao_booster_pack/ 四件套完整性与纯语义快照；
3. 商业意图收录对账研判器 (DoubaoLiveVerifier) 状态归类与首推对账；
4. 34 号公文结案报告落盘、格式校验与防伪哈希水印 (DOUBAO-INDEX-)；
5. CLI 命令行 doubao-index 全参数执行与异常兜底；
6. REST API 接口 (/doubao-index/audit, /boost, /report) 鉴权拦截与路由响应；
7. 高管只读交付门户反哺与 never_run 优雅降级契约；
8. Bytespider 403 阻断惩罚逻辑与 Nginx WAF 建议。
"""

import os
import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock

from tools.geo.doubao_indexer import (
    DoubaoCheckItem,
    DoubaoIntentStatus,
    DoubaoAuditResult,
    DoubaoReadinessAuditor,
    DoubaoBoosterPackGenerator,
    DoubaoLiveVerifier,
    generate_report_34_markdown,
    run_doubao_indexer,
)
from tools.geo.share import compile_portal_data
from tools.geo.server import GeoWebHandler, create_session
from tools.geo.utils import PROJECTS_DIR


class TestDoubaoIndexerPipeline(unittest.TestCase):
    """第 34 维豆包搜索极速收录与全链路保障中枢测试套件"""

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_01_readiness_audit_and_fact_redline(self):
        """测试 1: 六维收录要素体检器与事实红线约束（空项目严禁捏造假数据）"""
        # 针对真实项目进行体检
        auditor = DoubaoReadinessAuditor(self.project_id)
        checks, drs, grade, label, hits, blocked = auditor.audit()

        self.assertEqual(len(checks), 6, "六维体检指标必须完整覆盖 6 项")
        check_ids = {c.check_id for c in checks}
        expected_ids = {
            "CHK-ROBOTS", "CHK-LLMS-TXT", "CHK-SCHEMA",
            "CHK-BYTESPIDER-HIT", "CHK-TOUTIAO-PACK", "CHK-DOUBAO-PROBE"
        }
        self.assertEqual(check_ids, expected_ids)
        self.assertEqual(drs, 100.0)
        self.assertEqual(grade, "A+")
        self.assertIn("🌟", label)
        self.assertGreater(hits, 0)
        self.assertEqual(blocked, 0.0)

        # 针对无资产空项目：严禁捏造虚假百分比，DRS 必须为 None，评级为 pending
        empty_auditor = DoubaoReadinessAuditor("_template")
        e_checks, e_drs, e_grade, e_label, e_hits, e_blocked = empty_auditor.audit()
        self.assertIsNone(e_drs, "无实测空项目 DRS 就绪指数严禁捏造，必须恒为 None")
        self.assertEqual(e_grade, "pending", "无实测空项目评级必须恒为 pending")
        self.assertIn("待实测", e_label, "无实测空项目状态标签必须明确标示待实测")

    def test_02_booster_pack_generation(self):
        """测试 2: 专属提权加速包生成器 outputs/doubao_booster_pack/ 四件套完整性与纯语义快照"""
        booster = DoubaoBoosterPackGenerator(self.project_id)
        files = booster.generate_pack()

        self.assertEqual(len(files), 4, "提权加速包必须生成 4 项核心提权资产")
        pack_dir = os.path.join(PROJECTS_DIR, self.project_id, "outputs", "doubao_booster_pack")
        self.assertTrue(os.path.exists(pack_dir))

        # 1. 极简静态快照 HTML
        f_html = os.path.join(pack_dir, "01_Bytespider专享极简静态快照.html")
        self.assertTrue(os.path.exists(f_html))
        with open(f_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        self.assertIn("Bytespider", html_content)
        self.assertNotIn("<script", html_content, "极简快照严禁包含前端 JS，确保爬虫提取保真度 100%")
        self.assertIn("统一社会信用代码", html_content)
        # 事实红线核对：严禁虚假占位符 91320300MA1WXXXXXX 与 400-800-6688，必须使用真实电话 13150568888 与真实业务
        self.assertNotIn("91320300MA1WXXXXXX", html_content, "严禁将假统一信用代码写入对外快照")
        self.assertNotIn("400-800-6688", html_content, "严禁将假客服电话写入对外快照")
        self.assertIn("13150568888", html_content, "必须正确读取 project.yaml 真实电话 telephone")
        self.assertIn("微信/抖音小程序与移动端定制", html_content, "必须正确提取真实核心业务矩阵")

        # 2. 今日头条与微头条提权文案
        f_toutiao = os.path.join(pack_dir, "02_今日头条与微头条极速收录提权文案.md")
        self.assertTrue(os.path.exists(f_toutiao))
        with open(f_toutiao, "r", encoding="utf-8") as f:
            tt_content = f.read()
        self.assertIn("150 字微头条", tt_content)
        self.assertNotIn("91320300MA1WXXXXXX", tt_content)
        self.assertNotIn("400-800-6688", tt_content)
        self.assertIn("13150568888", tt_content)

        # 3. 豆包高意向 Q&A JSON
        f_qa = os.path.join(pack_dir, "03_豆包高意向Q&A微问答对.json")
        self.assertTrue(os.path.exists(f_qa))
        with open(f_qa, "r", encoding="utf-8") as f:
            qa_data = json.load(f)
        self.assertIn("qa_pairs", qa_data)
        self.assertEqual(len(qa_data["qa_pairs"]), 10, "必须包含 10 组高频高意向 Q&A 问答对")

        # 4. 排障 Checklist
        f_check = os.path.join(pack_dir, "04_豆包收录排障与白名单Checklist.md")
        self.assertTrue(os.path.exists(f_check))

    def test_03_intent_verification(self):
        """测试 3: 商业意图收录对账研判器 (DoubaoLiveVerifier) 状态归类与首推对账"""
        verifier = DoubaoLiveVerifier(self.project_id)
        intents = verifier.verify_intents()

        self.assertGreater(len(intents), 0, "必须成功读取意图词矩阵并完成豆包对账")
        valid_statuses = {"indexed_top1", "indexed_recommended", "crawled_pending", "missing_or_cold"}
        for it in intents:
            self.assertIn(it.status, valid_statuses)
            self.assertTrue(bool(it.query))
            self.assertTrue(bool(it.status_label))
            self.assertTrue(bool(it.suggested_action))

        # 验证真实探测首推对账（消费 live_probing_trace.json 真实字段）
        self.assertEqual(intents[0].query, "徐州市及淮海经济区做行业数字化找哪家团队靠谱？")
        self.assertEqual(intents[0].status, "indexed_top1")
        self.assertTrue(intents[0].doubao_top1)
        self.assertTrue(intents[0].citation_found)
        self.assertIn("🟢", intents[0].status_label)

    def test_04_report_34_and_hash_anti_counterfeit(self):
        """测试 4: 34 号公文结案报告落盘、防伪水印与 DOUBAO-INDEX- 校验"""
        res = run_doubao_indexer(self.project_id, do_audit=True, do_boost=True, do_verify=True, save_report=True)

        report_path = res.get("report_file")
        self.assertTrue(bool(report_path) and os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md = f.read()

        self.assertIn("# 34_豆包大模型搜索极速收录与全链路索引保障报告", md)
        self.assertIn("DOUBAO-INDEX-", md, "报告必须包含防伪流水号")
        self.assertIn("豆包收录就绪指数 (DRS)", md)
        self.assertIn("Bytespider", md)
        self.assertIn("今日头条与微头条", md)

        # 校验 JSON 审计文件
        audit_json_path = os.path.join(PROJECTS_DIR, self.project_id, "outputs", "doubao_index_audit.json")
        self.assertTrue(os.path.exists(audit_json_path))
        with open(audit_json_path, "r", encoding="utf-8") as f:
            j_data = json.load(f)
        self.assertEqual(j_data["project_id"], self.project_id)
        self.assertEqual(j_data["drs_score"], 100.0)

    def test_05_cli_execution(self):
        """测试 5: CLI 命令行 doubao-index 执行逻辑"""
        from tools.geo.cli import main
        import sys
        from unittest.mock import patch

        # 测试 --dry-run 模式
        test_args = ["geo", "doubao-index", self.project_id, "--dry-run"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        # 测试未提供项目 ID 报错拦截
        empty_args = ["geo", "doubao-index"]
        with patch.object(sys, "argv", empty_args):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 1)

    def test_06_server_rest_api_auth(self):
        """测试 6: REST API 接口 (/doubao-index/audit, /boost, /report) 鉴权拦截与路由响应"""
        # 1. 未授权请求必须被 401 拦截
        unauth_handler = MagicMock(spec=GeoWebHandler)
        unauth_handler.path = f"/api/projects/{self.project_id}/doubao-index/audit"
        unauth_handler.headers = {}
        unauth_handler.get_auth_token = MagicMock(return_value="")
        send_json_mock = MagicMock()
        unauth_handler.send_json = send_json_mock

        GeoWebHandler.do_GET(unauth_handler)
        send_json_mock.assert_called_with({"success": False, "message": "未登录或登录已失效，请重新登录！"}, status=401)

        # 2. 授权请求正常获取体检数据
        valid_token = create_session("admin")
        auth_handler = MagicMock(spec=GeoWebHandler)
        auth_handler.path = f"/api/projects/{self.project_id}/doubao-index/audit"
        auth_handler.headers = {"Authorization": f"Bearer {valid_token}"}
        auth_handler.get_auth_token = MagicMock(return_value=valid_token)
        auth_send_mock = MagicMock()
        auth_handler.send_json = auth_send_mock

        GeoWebHandler.do_GET(auth_handler)
        self.assertTrue(auth_send_mock.called)
        call_args = auth_send_mock.call_args[0][0]
        self.assertTrue(call_args.get("success"))
        self.assertEqual(call_args.get("data", {}).get("project_id"), self.project_id)

        # 3. 报告只读获取
        rep_handler = MagicMock(spec=GeoWebHandler)
        rep_handler.path = f"/api/projects/{self.project_id}/doubao-index/report"
        rep_handler.headers = {"Authorization": f"Bearer {valid_token}"}
        rep_handler.get_auth_token = MagicMock(return_value=valid_token)
        rep_send_mock = MagicMock()
        rep_handler.send_json = rep_send_mock

        GeoWebHandler.do_GET(rep_handler)
        self.assertTrue(rep_send_mock.called)
        rep_call_args = rep_send_mock.call_args[0][0]
        self.assertTrue(rep_call_args.get("success"))
        self.assertIn("34_豆包大模型搜索极速收录与全链路索引保障报告", rep_call_args.get("content", ""))

        # 4. POST /doubao-index/boost 提权触发
        boost_handler = MagicMock(spec=GeoWebHandler)
        boost_handler.path = f"/api/projects/{self.project_id}/doubao-index/boost"
        boost_handler.headers = {"Authorization": f"Bearer {valid_token}"}
        boost_handler.get_auth_token = MagicMock(return_value=valid_token)
        boost_send_mock = MagicMock()
        boost_handler.send_json = boost_send_mock

        GeoWebHandler.do_POST(boost_handler)
        self.assertTrue(boost_send_mock.called)
        boost_call_args = boost_send_mock.call_args[0][0]
        self.assertTrue(boost_call_args.get("success"))

    def test_07_portal_integration_and_never_run(self):
        """测试 7: 高管只读交付门户反哺与 never_run 优雅降级契约"""
        # 1. 针对已生成 34 维数据的项目进行聚合
        portal_data = compile_portal_data(self.project_id)
        self.assertIn("doubao_index_summary", portal_data)
        summary = portal_data["doubao_index_summary"]
        self.assertTrue(summary["has_data"])
        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["drs_score"], 100.0)
        self.assertEqual(summary["grade"], "A+")
        self.assertTrue(summary["toutiao_pack_ready"])
        self.assertTrue(summary["booster_pack_ready"])
        self.assertIn("# 34_豆包大模型搜索极速收录与全链路索引保障报告", portal_data["deliverables"]["doubao_index_audit"])

        # 2. 针对未运行过的项目测试优雅降级
        t_data = compile_portal_data("_template")
        t_summary = t_data["doubao_index_summary"]
        self.assertFalse(t_summary["has_data"])
        self.assertEqual(t_summary["status"], "never_run")
        self.assertIsNone(t_summary["drs_score"])
        self.assertEqual(t_summary["grade"], "pending")
        self.assertFalse(t_summary["booster_pack_ready"])

    def test_08_bytespider_403_penalty(self):
        """测试 8: Bytespider 抓取 403 阻断惩罚逻辑与 Nginx WAF 建议"""
        from unittest.mock import patch

        # 模拟爬虫审计日志中包含 Bytespider 403 阻断记录
        mock_spider_data = {
            "summary": {"total_hits": 100},
            "spider_breakdown": {
                "bytespider": {
                    "hits": 50,
                    "status_403": 25  # 50% 阻断率
                }
            }
        }
        auditor = DoubaoReadinessAuditor(self.project_id)
        with patch.object(auditor, "_read_json_safe", return_value=mock_spider_data):
            checks, drs, grade, label, hits, blocked = auditor.audit()
            chk_byte = next(c for c in checks if c.check_id == "CHK-BYTESPIDER-HIT")
            self.assertFalse(chk_byte.passed)
            self.assertEqual(blocked, 50.0)
            self.assertEqual(chk_byte.score, 0.0)  # 100 - 50*2 = 0
            self.assertIn("WAF", chk_byte.suggested_action)


if __name__ == "__main__":
    unittest.main()
