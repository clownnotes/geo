# -*- coding: utf-8 -*-
"""
单元测试：全网主流 AI 爬虫真实访问捕获与真机抓取日志审计中枢 (tests/test_spider_auditor.py)
第 31 维核心能力单测覆盖：
1. 主流大模型爬虫 UA 指纹匹配准确性 (国内 5 大主流 + 国际标杆)；
2. Nginx Combined 及宽容日志解析引擎鲁棒性与异常防护；
3. 确定性高保真沙箱回放 (哈希种子固定，多次生成绝对一致)；
4. 量化审计算法 (状态码分布、成功率、WAF 403 阻断率、核心资产抓取率、健康度分级)；
5. 普林斯顿 9 因子 31 号公文 Markdown 结构与防伪哈希生成；
6. 高管只读交付门户战果反哺与 never_run 优雅降级契约；
7. Web API 路由与 Bearer Token 鉴权保护。
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from tools.geo.spider_auditor import (
    AI_SPIDER_REGISTRY,
    identify_ai_spider,
    parse_access_log_line,
    parse_access_log_file,
    SandboxLogGenerator,
    audit_spider_access,
    generate_report_31_markdown,
)
from tools.geo.share import compile_portal_data
from tools.geo.server import GeoWebHandler, is_authenticated, create_session


class TestSpiderAuditor(unittest.TestCase):

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_01_spider_identification(self):
        """测试 P1-1: 主流大模型爬虫 UA 特征指纹识别准确度"""
        cases = [
            ("Mozilla/5.0 (compatible; Bytespider; https://zhanzhang.toutiao.com/)", "bytespider"),
            ("Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)", "baidu"),
            ("Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)", "baidu"),
            ("Mozilla/5.0 (compatible; DeepSeek-Crawler/1.0; +https://www.deepseek.com)", "deepseek"),
            ("Mozilla/5.0 (compatible; DeepSeekBot/1.0; +https://www.deepseek.com)", "deepseek"),
            ("Mozilla/5.0 (compatible; MoonshotBot/1.0; +https://www.moonshot.cn)", "moonshot"),
            ("Mozilla/5.0 (compatible; TencentHunyuanBot/1.0; +https://hunyuan.tencent.com)", "hunyuan"),
            ("Mozilla/5.0 (compatible; Qwen-Bot/1.0; +https://www.aliyun.com)", "qwen"),
            ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)", "gptbot"),
            ("Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)", "claudebot"),
            ("Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)", "perplexity"),
            ("Mozilla/5.0 (compatible; Google-Extended; +https://developers.google.com/search)", "google"),
        ]

        for ua, expected_key in cases:
            s_key, s_info = identify_ai_spider(ua)
            self.assertEqual(s_key, expected_key, f"UA 识别不符合预期: {ua}")
            self.assertIsNotNone(s_info)
            self.assertIn("name", s_info)
            self.assertIn("family", s_info)

        # 非 AI 爬虫应返回 (None, None)
        normal_browser = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
        s_key, s_info = identify_ai_spider(normal_browser)
        self.assertIsNone(s_key)
        self.assertIsNone(s_info)

        # 空或异常 UA
        self.assertEqual(identify_ai_spider(""), (None, None))
        self.assertEqual(identify_ai_spider(None), (None, None))

    def test_02_log_parsing_robustness(self):
        """测试 P1-2: Nginx Combined 与宽容解析器鲁棒性及异常阻断"""
        valid_line = (
            '111.225.148.12 - - [04/Sep/2026:10:15:32 +0800] '
            '"GET /llms.txt HTTP/1.1" 200 4096 "-" '
            '"Mozilla/5.0 (compatible; Bytespider; https://zhanzhang.toutiao.com/)"'
        )
        parsed = parse_access_log_line(valid_line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["ip"], "111.225.148.12")
        self.assertEqual(parsed["method"], "GET")
        self.assertEqual(parsed["path"], "/llms.txt")
        self.assertEqual(parsed["status"], 200)
        self.assertEqual(parsed["bytes"], 4096)
        self.assertIn("Bytespider", parsed["user_agent"])

        # 畸形或注释行应静默返回 None，绝不崩溃
        self.assertIsNone(parse_access_log_line("# This is a comment"))
        self.assertIsNone(parse_access_log_line(""))
        self.assertIsNone(parse_access_log_line("invalid gibberish string"))

        # 文件批量解析
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
            tmp.write(valid_line + "\n")
            tmp.write("# comment\n")
            tmp.write("\n")
            tmp.write('110.242.68.3 - - [04/Sep/2026:10:16:00 +0800] "GET /schema.jsonld HTTP/1.1" 304 0 "-" "Baiduspider"\n')
            tmp_path = tmp.name

        try:
            entries = parse_access_log_file(tmp_path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["status"], 200)
            self.assertEqual(entries[1]["status"], 304)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_03_deterministic_sandbox(self):
        """测试 P1-3: 确定性沙箱日志回放器的幂等与稳定性"""
        logs1 = SandboxLogGenerator.generate_logs(self.project_id, count=128)
        logs2 = SandboxLogGenerator.generate_logs(self.project_id, count=128)

        self.assertEqual(len(logs1), 128)
        self.assertEqual(len(logs2), 128)

        # 验证固定种子下生成内容 100% 相同
        for i in range(len(logs1)):
            self.assertEqual(logs1[i]["user_agent"], logs2[i]["user_agent"])
            self.assertEqual(logs1[i]["path"], logs2[i]["path"])
            self.assertEqual(logs1[i]["status"], logs2[i]["status"])
            self.assertEqual(logs1[i]["ip"], logs2[i]["ip"])

        # 验证包含主流核心爬虫与 /llms.txt
        uas = [e["user_agent"] for e in logs1]
        paths = [e["path"] for e in logs1]
        self.assertTrue(any("Bytespider" in u for u in uas))
        self.assertTrue(any("DeepSeek" in u for u in uas))
        self.assertTrue(any("Baiduspider" in u for u in uas))
        self.assertIn("/llms.txt", paths)
        self.assertIn("/schema.jsonld", paths)

    def test_04_audit_spider_access_pipeline_and_metrics(self):
        """测试第 31 维核心审计算法、指标聚合与公文落盘"""
        res = audit_spider_access(self.project_id, save_report=True)

        self.assertEqual(res["project_id"], self.project_id)
        self.assertIn("summary", res)
        summary = res["summary"]

        # 检查指标量化字段
        self.assertGreater(summary["total_ai_hits"], 0)
        self.assertGreaterEqual(summary["unique_spiders_count"], 4)
        self.assertGreaterEqual(summary["success_rate_pct"], 90.0)
        self.assertEqual(summary["blocked_rate_pct"], 0.0)
        self.assertGreater(summary["llms_txt_hit_count"], 0)
        self.assertEqual(summary["health_grade"], "safe")
        self.assertIn("🟢", summary["health_status_label"])

        # 检查核心资产覆盖清单
        core_assets = res["core_assets_audit"]
        self.assertTrue(len(core_assets) >= 4)
        paths = [a["path"] for a in core_assets]
        self.assertIn("/llms.txt", paths)
        self.assertIn("/schema.jsonld", paths)
        self.assertIn("/robots.txt", paths)

        # 检查物理落盘文件
        out_dir = os.path.join("projects", self.project_id, "outputs")
        json_file = os.path.join(out_dir, "spider_access_audit.json")
        report_file = os.path.join(out_dir, "31_全网主流AI爬虫真实访问捕获与真机抓取日志审计报告.md")

        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(report_file))

        with open(report_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 验证普林斯顿 9 因子结构
        self.assertIn("# 31_全网主流AI爬虫真实访问捕获与真机抓取日志审计报告", md_content)
        self.assertIn("一、 审计结论先行", md_content)
        self.assertIn("二、 主流 AI 爬虫真实抓取频次与份额分布矩阵", md_content)
        self.assertIn("三、 GEO 核心事实资产抓取健康度深度对账", md_content)
        self.assertIn("四、 WAF 安全策略与 403 误杀拦截诊断", md_content)
        self.assertIn("五、 典型高频事实问答对 (FAQ)", md_content)
        self.assertIn("六、 SOP 代运营巡检与维护指令", md_content)
        self.assertIn("七、 数字化防伪签名与审计对账存证", md_content)
        self.assertIn("SHA256:", md_content)

    def test_05_custom_log_with_blocked_and_warning_grades(self):
        """测试异常状态码分支：检测到 403 阻断触发 danger 预警"""
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
            # 模拟 Bytespider 遭遇 403 拦截
            tmp.write('111.225.148.12 - - [04/Sep/2026:10:00:00 +0800] "GET /llms.txt HTTP/1.1" 403 512 "-" "Bytespider"\n')
            tmp.write('110.242.68.3 - - [04/Sep/2026:10:01:00 +0800] "GET /robots.txt HTTP/1.1" 200 120 "-" "Baiduspider"\n')
            tmp_path = tmp.name

        try:
            res = audit_spider_access(self.project_id, log_file=tmp_path, save_report=False)
            summary = res["summary"]
            self.assertEqual(summary["total_ai_hits"], 2)
            self.assertGreater(summary["blocked_rate_pct"], 0)
            self.assertEqual(summary["health_grade"], "danger")
            self.assertIn("🔴", summary["health_status_label"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_06_portal_integration_and_never_run_contract(self):
        """测试 P0-1: 高管只读交付门户数据反哺与 never_run 优雅降级契约"""
        # 1. 存在审计账本时的正常加载
        portal_data = compile_portal_data(self.project_id)
        self.assertIn("spider_access_summary", portal_data)
        s_sum = portal_data["spider_access_summary"]
        self.assertTrue(s_sum["has_data"])
        self.assertEqual(s_sum["status"], "audited")
        self.assertGreater(s_sum["total_ai_hits"], 0)
        self.assertIn("spider_breakdown", s_sum)
        self.assertIn("core_assets_audit", s_sum)
        self.assertIn("recent_crawl_stream", s_sum)
        self.assertIn("spider_access_audit", portal_data["deliverables"])

        # 2. 无审计账本时的严格 never_run 优雅降级 (测试 retail_catering 模板项目)
        fallback_data = compile_portal_data("retail_catering")
        f_sum = fallback_data["spider_access_summary"]
        self.assertFalse(f_sum["has_data"])
        self.assertEqual(f_sum["status"], "never_run")
        self.assertEqual(f_sum["total_ai_hits"], 0)
        self.assertIn("待执行", f_sum["status_label"])

    def test_07_api_auth_gate_and_routes(self):
        """测试 P0-2: Web 端 API 路由挂载与 Bearer Token 鉴权保护"""
        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json
        handler.read_json_body = lambda: {}

        # 1. 未授权请求 POST /api/projects/{id}/spider-audit/run => 401
        captured.clear()
        handler.path = f"/api/projects/{self.project_id}/spider-audit/run"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 2. 未授权请求 GET /api/projects/{id}/spider-audit/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.project_id}/spider-audit/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 授权请求 POST /api/projects/{id}/spider-audit/run 正常放行
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = f"/api/projects/{self.project_id}/spider-audit/run"
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status", 200), 200)
        self.assertTrue(captured.get("payload", {}).get("success"))
        self.assertEqual(captured["payload"]["data"]["project_id"], self.project_id)

        # 4. 授权请求 GET /api/projects/{id}/spider-audit/status 正常放行
        captured.clear()
        handler.path = f"/api/projects/{self.project_id}/spider-audit/status"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status", 200), 200)
        self.assertTrue(captured.get("payload", {}).get("success"))
        self.assertTrue(captured["payload"]["has_data"])

        # 5. 授权请求 GET /api/projects/{id}/spider-audit/report 正常放行
        captured.clear()
        handler.path = f"/api/projects/{self.project_id}/spider-audit/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status", 200), 200)
        self.assertTrue(captured.get("payload", {}).get("success"))
        self.assertIn("31_全网主流AI爬虫真实访问捕获与真机抓取日志审计报告.md", captured["payload"]["filename"])


if __name__ == "__main__":
    unittest.main()
