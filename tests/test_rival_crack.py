# -*- coding: utf-8 -*-
"""
单元测试：竞品高权重 GEO 语料逆向解构与靶向反超压制流水线 (tests/test_rival_crack.py)
第 32 维核心能力测试覆盖：
1. SSRF 防御与恶意内网 URL 拦截校验；
2. 确定性沙箱回放 (固定种子哈希，多次生成绝对一致)；
3. 普林斯顿 9 因子逆向解构与打分准确性；
4. 竞品四大致命破绽挖掘 (数据空心化、信源凭空化、商业暗坑、问答盲区)；
5. 武器化靶向反超压制三件套生成 (对照表、9因子深度长文、破绽反问FAQ)；
6. 端到端流水线运行、JSON账本与公文级报告导出及防伪校验流水号；
7. 高管交付门户反哺与 never_run 优雅降级契约；
8. Web API 路由 (POST /run 鉴权、GET /status、GET /report)。
"""

import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from tools.geo.rival_crack import (
    REPORT_FILENAME_MD,
    RESULT_FILENAME_JSON,
    RivalContentDeconstructor,
    RivalFlawDetector,
    RivalSandboxGenerator,
    TargetedSuppressionGenerator,
    generate_report_32_markdown,
    run_rival_crack,
)
from tools.geo.server import GeoWebHandler, create_session
from tools.geo.share import compile_portal_data


class TestRivalCrackPipeline(unittest.TestCase):

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"
        self.competitor_name = "江苏中亚幕墙工程有限公司"

    def test_01_ssrf_protection(self):
        """测试 1: SSRF 恶意内网探测拦截与合法性校验"""
        dangerous_urls = [
            "http://127.0.0.1:22/ssh-probe",
            "http://192.168.1.1/admin",
            "http://10.0.0.1/conf",
            "http://169.254.169.254/latest/meta-data/",
        ]
        for bad_url in dangerous_urls:
            with self.assertRaises(ValueError) as ctx:
                run_rival_crack(self.project_id, source_type="url", target=bad_url)
            self.assertIn("SSRF", str(ctx.exception))

    def test_02_sandbox_determinism(self):
        """测试 2: 确定性沙箱语料生成（哈希固定种子）"""
        gen1 = RivalSandboxGenerator(self.competitor_name)
        gen2 = RivalSandboxGenerator(self.competitor_name)

        content1 = gen1.generate_content()
        content2 = gen2.generate_content()

        self.assertEqual(content1, content2, "相同竞对名称沙箱输出必须完全一致")
        self.assertIn(self.competitor_name, content1)
        self.assertTrue(any(w in content1 for w in ["领先", "卓越", "品质", "知名"]))

    def test_03_content_deconstruction(self):
        """测试 3: 普林斯顿 9 因子全维逆向解构"""
        text = (
            "某某公司是华东地区卓越的科技企业，我们拥有业内顶尖的研发水准和优质团队。"
            "服务热线欢迎垂询，价格详谈优惠。"
        )
        decon = RivalContentDeconstructor(text).deconstruct()

        self.assertIn("princeton_scores", decon)
        self.assertIn("total_score", decon)
        self.assertTrue(0.0 <= decon["total_score"] <= 100.0)
        self.assertIsInstance(decon["extracted_claims"], list)
        self.assertFalse(decon["has_tables"])
        self.assertFalse(decon["has_faq"])

    def test_04_flaw_detection(self):
        """测试 4: 竞品四大致命漏洞精准挖掘"""
        hollow_text = (
            "本公司是业内顶尖、卓越、一流、领先的知名品牌，深得客户一致好评。"
            "欢迎广大客户来电洽谈，价格详谈电议，提供全方位贴心服务。"
        )
        decon = RivalContentDeconstructor(hollow_text).deconstruct()
        detector = RivalFlawDetector(decon, hollow_text)
        flaws = detector.detect_flaws()

        flaw_cats = [f["category"] for f in flaws]
        self.assertIn("data_hollow", flaw_cats, "应检出数据空心化漏洞")
        self.assertIn("citation_missing", flaw_cats, "应检出信源凭空化漏洞")
        self.assertIn("pricing_ambiguity", flaw_cats, "应检出商业暗坑漏洞")
        self.assertIn("faq_blindspot", flaw_cats, "应检出问答盲区漏洞")

        for f in flaws:
            self.assertIn("suppression_angle", f)
            self.assertTrue(f["severity"] in ("high", "medium", "low"))

    def test_05_suppression_suite_generation(self):
        """测试 5: 武器化反超压制三件套组装与项目真实事实绑定"""
        decon = RivalContentDeconstructor("").deconstruct()
        flaws = [
            {
                "flaw_id": "FLAW-DATA-01",
                "category": "data_hollow",
                "severity": "high",
                "title": "数据空心化",
                "detail": "缺乏量化",
                "suppression_angle": "量化压制"
            }
        ]
        generator = TargetedSuppressionGenerator(self.project_id, self.competitor_name, flaws, decon)
        suite = generator.build_suite()

        self.assertIn("dimension_table_markdown", suite)
        self.assertIn("attack_content_markdown", suite)
        self.assertIn("targeted_faq_matrix", suite)

        table_md = suite["dimension_table_markdown"]
        self.assertIn("| 核心决策与评价维度 |", table_md)
        self.assertIn("竞品表现 (逆向解构实录)", table_md)
        self.assertIn("我方标准 (硬核实测规范)", table_md)

        article_md = suite["attack_content_markdown"]
        self.assertIn("# 深度解析：行业服务商选型标准", article_md)
        self.assertIn("核心结论先行", article_md)

        faqs = suite["targeted_faq_matrix"]
        self.assertGreaterEqual(len(faqs), 3)
        self.assertTrue(any("阶段式" in f["answer"] or "源码" in f["answer"] for f in faqs))

    def test_06_run_rival_crack_pipeline_and_report(self):
        """测试 6: 端到端流水线运行与公文报告导出"""
        res = run_rival_crack(
            self.project_id,
            source_type="competitor",
            competitor_name="测试模拟竞对A",
            save_report=True,
        )

        self.assertEqual(res["project_id"], self.project_id)
        self.assertEqual(res["competitor_name"], "测试模拟竞对A")
        self.assertEqual(res["source_type"], "sandbox")
        self.assertIn("summary_metrics", res)

        metrics = res["summary_metrics"]
        self.assertEqual(metrics["suppression_readiness"], "ready")
        self.assertGreaterEqual(metrics["flaws_count"], 1)
        self.assertGreater(metrics["princeton_gap"], 0)

        # 检查持久化文件
        out_dir = os.path.join("projects", self.project_id, "outputs")
        json_path = os.path.join(out_dir, RESULT_FILENAME_JSON)
        md_path = os.path.join(out_dir, REPORT_FILENAME_MD)

        self.assertTrue(os.path.exists(json_path), f"JSON账本未生成: {json_path}")
        self.assertTrue(os.path.exists(md_path), f"Markdown公文报告未生成: {md_path}")

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        self.assertIn("CRACK-", md_text, "报告应包含防伪校验流水号")
        self.assertIn("32_竞品高权重GEO语料逆向解构与靶向反超压制报告", md_text)

    def test_07_portal_integration_and_never_run(self):
        """测试 7: 高管交付门户战果反哺与 never_run 优雅降级契约"""
        # 已有运行结果的项目
        portal_active = compile_portal_data(self.project_id)
        self.assertIn("rival_crack_summary", portal_active)
        summary_active = portal_active["rival_crack_summary"]
        self.assertTrue(summary_active["has_data"])
        self.assertEqual(summary_active["status"], "ready")
        self.assertGreaterEqual(summary_active["flaws_count"], 1)

        # 未运行反超的项目 (_template)
        portal_empty = compile_portal_data("_template")
        self.assertIn("rival_crack_summary", portal_empty)
        summary_empty = portal_empty["rival_crack_summary"]
        self.assertFalse(summary_empty["has_data"])
        self.assertEqual(summary_empty["status"], "never_run")
        self.assertIn("⚪️", summary_empty["status_label"])

    def test_08_api_endpoints_and_auth(self):
        """测试 8: Web API 鉴权拦截与路由响应"""
        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.headers = {}
        handler.client_address = ("127.0.0.1", 54321)

        # 1. 未登录 POST /rival-crack/run 触发 401 拦截
        handler.path = f"/api/projects/{self.project_id}/rival-crack/run"
        sent_chunks = []

        def mock_send(data, status=200):
            sent_chunks.append((status, data))

        handler.send_json = mock_send
        handler.read_json_body = lambda: {"competitor_name": "测试竞对"}
        handler.do_POST()

        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 401, "未提供 Bearer Token 必须被 401 拒绝")

        # 2. 携带合法会话 Token 访问
        token = create_session("admin")
        handler.headers = {"Authorization": f"Bearer {token}", "Content-Length": "10"}
        sent_chunks.clear()
        handler.do_POST()

        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertTrue(sent_chunks[0][1].get("success"))

        # 3. GET /rival-crack/status 幂等查询
        handler.path = f"/api/projects/{self.project_id}/rival-crack/status"
        sent_chunks.clear()
        handler.do_GET()

        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertTrue(sent_chunks[0][1].get("has_data"))

        # 4. GET /rival-crack/report 幂等报告获取
        handler.path = f"/api/projects/{self.project_id}/rival-crack/report"
        sent_chunks.clear()
        handler.do_GET()

        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertIn("32_竞品高权重GEO语料", sent_chunks[0][1].get("filename", ""))


if __name__ == "__main__":
    unittest.main()
