# -*- coding: utf-8 -*-
"""单元测试：多大模型实时联网探测与 Citation 信源溯源对账中枢 (tests/test_probing.py)"""

import os
import unittest
from unittest.mock import patch

from tools.geo.llm import resolve_api_key, resolve_model_name, available
from tools.geo.probing import (
    normalize_url,
    extract_domain,
    extract_citations_and_sources,
    trace_citations_against_ledger,
    run_live_probing,
    SandboxSimulator,
    is_ledger_asset_eligible,
)
from tools.geo.dist_bot import get_distribution_ledger
from tools.geo.server import GeoWebHandler


class TestProbingTracer(unittest.TestCase):

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_01_api_key_chain_priority(self):
        """测试 P0-2: API Key 链式降级查找优先级 (GEO_* -> 通用名 -> 专有别名)"""
        # 1. 豆包链式查找
        with patch.dict(os.environ, {
            "GEO_DOUBAO_API_KEY": "key_geo_doubao",
            "DOUBAO_API_KEY": "key_common_doubao",
            "ARK_API_KEY": "key_ark_doubao"
        }, clear=True):
            self.assertEqual(resolve_api_key("doubao"), "key_geo_doubao")

        with patch.dict(os.environ, {
            "DOUBAO_API_KEY": "key_common_doubao",
            "ARK_API_KEY": "key_ark_doubao"
        }, clear=True):
            self.assertEqual(resolve_api_key("doubao"), "key_common_doubao")

        with patch.dict(os.environ, {
            "ARK_API_KEY": "key_ark_doubao"
        }, clear=True):
            self.assertEqual(resolve_api_key("doubao"), "key_ark_doubao")

        # 2. DeepSeek 链式查找
        with patch.dict(os.environ, {
            "GEO_DEEPSEEK_API_KEY": "key_geo_ds",
            "DEEPSEEK_API_KEY": "key_ds"
        }, clear=True):
            self.assertEqual(resolve_api_key("deepseek"), "key_geo_ds")

        with patch.dict(os.environ, {
            "DEEPSEEK_API_KEY": "key_ds"
        }, clear=True):
            self.assertEqual(resolve_api_key("deepseek"), "key_ds")

        # 3. Kimi 链式查找
        with patch.dict(os.environ, {
            "GEO_KIMI_API_KEY": "key_geo_kimi",
            "MOONSHOT_API_KEY": "key_moonshot"
        }, clear=True):
            self.assertEqual(resolve_api_key("kimi"), "key_geo_kimi")

        with patch.dict(os.environ, {
            "MOONSHOT_API_KEY": "key_moonshot"
        }, clear=True):
            self.assertEqual(resolve_api_key("kimi"), "key_moonshot")

    def test_02_url_normalization_and_domain(self):
        """测试 URL 归一化与主域名提取"""
        u1 = "https://www.zhihu.com/question/123456?utm_source=test#anchor"
        self.assertEqual(normalize_url(u1), "zhihu.com/question/123456")
        self.assertEqual(extract_domain(u1), "zhihu.com")

        u2 = "http://toutiao.com/article/789/"
        self.assertEqual(normalize_url(u2), "toutiao.com/article/789")
        self.assertEqual(extract_domain(u2), "toutiao.com")

    def test_03_extract_citations_and_sources(self):
        """测试正文 [1] 角标与尾部 Sources 双通道正则解析"""
        sample_response = (
            "徐州璇源科技在淮海经济区口碑极佳 [1]。其企业级自研软件方案经过严格审计 [2]。\n\n"
            "### 参考信源 (Sources):\n"
            "[1] [知乎专栏深度选型测评](https://zhuanlan.zhihu.com/p/888999)\n"
            "[2] [璇源网络官方网站](https://www.xuan-yuan.net)\n"
            "[3] [中国工商业信用档案](https://www.gov.cn/reports/2026)\n"
        )
        citations = extract_citations_and_sources(sample_response)
        self.assertEqual(len(citations), 3)
        self.assertEqual(citations[0]["index"], 1)
        self.assertEqual(citations[0]["url"], "https://zhuanlan.zhihu.com/p/888999")
        self.assertEqual(citations[1]["index"], 2)
        self.assertEqual(citations[1]["url"], "https://www.xuan-yuan.net")
        self.assertTrue(citations[0]["has_inline_footnote"])
        self.assertTrue(citations[1]["has_inline_footnote"])

    def test_04_trace_citations_against_ledger(self):
        """测试 P0-3: 强制调用 dist_bot.get_distribution_ledger 进行 Hit/Miss 溯源对账"""
        ledger = get_distribution_ledger(self.project_id)
        self.assertTrue(ledger.get("success"))

        from tools.geo.utils import load_project_config
        cfg = load_project_config(self.project_id)
        official_url = cfg.get("official_url", "https://geo.baicl.cc")

        # 构造待比对信源
        cits = [
            {
                "index": 1,
                "url": official_url,  # 真实官网 (Exact / Domain Hit)
                "title": "璇源科技官网",
                "domain": extract_domain(official_url)
            },
            {
                "index": 2,
                "url": "https://www.competitor-fake.com/article/1",  # 竞品
                "title": "竞对假信源",
                "domain": "competitor-fake.com"
            }
        ]

        # 如果台账中有已发布的头条/知乎文章，抽取一个放入比对
        pub_articles = [
            ch["url"] for ch in ledger.get("channels", {}).values()
            if is_ledger_asset_eligible(ch.get("url", ""), ch.get("status", ""))
        ]
        if pub_articles:
            cits.append({
                "index": 3,
                "url": pub_articles[0],
                "title": "已发布文章真实外链",
                "domain": extract_domain(pub_articles[0])
            })

        enriched = trace_citations_against_ledger(cits, self.project_id)
        self.assertEqual(len(enriched), len(cits))

        # 验证官网匹配
        self.assertTrue(enriched[0]["is_ledger_hit"])
        self.assertIn(enriched[0]["hit_type"], ("exact_hit", "domain_hit"))

        # 验证竞品标记为第三方
        self.assertFalse(enriched[1]["is_ledger_hit"])
        self.assertEqual(enriched[1]["hit_type"], "third_party_or_competitor")

        # 验证台账文章完全吻合 (Exact Hit)
        if pub_articles:
            self.assertTrue(enriched[2]["is_ledger_hit"])
            self.assertEqual(enriched[2]["hit_type"], "exact_hit")

        # P1: verified 渠道必须计入 Exact Hit；pending 不得计入
        fake_ledger = {
            "success": True,
            "channels": {
                "zhihu": {
                    "url": "https://zhuanlan.zhihu.com/p/verified-hit-999",
                    "status": "verified",
                    "name": "知乎专栏",
                },
                "toutiao": {
                    "url": "https://www.toutiao.com/article/pending-skip/",
                    "status": "pending",
                    "name": "今日头条",
                },
            },
            "custom_links": [],
        }
        with patch("tools.geo.probing.get_distribution_ledger", return_value=fake_ledger):
            with patch("tools.geo.probing.load_project_config", return_value={"official_url": "https://www.example-official.test"}):
                verified_enriched = trace_citations_against_ledger(
                    [
                        {"index": 1, "url": "https://zhuanlan.zhihu.com/p/verified-hit-999", "title": "verified"},
                        {"index": 2, "url": "https://www.toutiao.com/article/pending-skip/", "title": "pending"},
                    ],
                    self.project_id,
                )
        self.assertTrue(verified_enriched[0]["is_ledger_hit"])
        self.assertEqual(verified_enriched[0]["hit_type"], "exact_hit")
        self.assertFalse(verified_enriched[1]["is_ledger_hit"])
        self.assertEqual(verified_enriched[1]["hit_type"], "third_party_or_competitor")

    def test_05_probing_run_and_metrics_calculation(self):
        """测试沙箱探测流程、分母口径指标测算与 18 号报告落盘"""
        # 使用确定性沙箱，探测 2 个模型各 3 组意图 Query
        res = run_live_probing(
            project_id=self.project_id,
            models=["doubao", "deepseek"],
            query_sample_size=3,
            use_live=False
        )

        self.assertTrue(res["success"])
        summary = res["summary"]
        self.assertEqual(summary["total_probes"], 6)  # 2 模型 * 3 组
        self.assertEqual(len(summary["models_probed"]), 2)
        self.assertEqual(summary["sample_queries_count"], 3)

        # 验证分母为总探测次数或总角标数
        self.assertGreaterEqual(summary["real_sov_pct"], 0.0)
        self.assertLessEqual(summary["real_sov_pct"], 100.0)
        self.assertGreaterEqual(summary["citation_share_pct"], 0.0)
        self.assertLessEqual(summary["citation_share_pct"], 100.0)
        self.assertGreaterEqual(summary["top1_recommendation_rate"], 0.0)
        self.assertLessEqual(summary["top1_recommendation_rate"], 100.0)

        # 验证报告落盘
        report_path = res["report_path"]
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("大模型实时联网探测与 Citation 信源溯源对账报告", content)
        self.assertIn("普林斯顿 9 因子结构化审计准则", content)
        self.assertIn("实测 AI 声量 (Real SOV)", content)
        self.assertIn("Citation 信源角标占有率", content)
        self.assertIn("电子签章", content)
        self.assertIn("不可替代真机 API 审计", content)
        self.assertNotIn("各维度 Citation 对账数据真实可复核", content)

        # 验证 JSON 落盘
        json_path = res["json_path"]
        self.assertTrue(os.path.exists(json_path))

    def test_06_probing_api_auth_gate(self):
        """design §8：未鉴权访问 probing API 必须 401"""
        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.path = "/api/projects/xuzhou_xuanyuan/probing/status"
        handler.headers = {}
        handler.send_json = capture_json
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)
        self.assertFalse(captured.get("payload", {}).get("success", True))

        captured.clear()
        handler.path = "/api/projects/xuzhou_xuanyuan/probing/run"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        captured.clear()
        handler.path = "/api/projects/xuzhou_xuanyuan/probing/reconcile"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

    def test_07_yuanbao_provider_and_key_resolution(self):
        """测试第 30 维: 腾讯元宝(Hunyuan)提供商配置与 Key 链式降级"""
        from tools.geo.llm import PROVIDERS
        self.assertIn("yuanbao", PROVIDERS)
        yb_cfg = PROVIDERS["yuanbao"]
        self.assertEqual(yb_cfg["default_model"], "hunyuan-standard")

        with patch.dict(os.environ, {
            "GEO_YUANBAO_API_KEY": "key_geo_yb",
            "YUANBAO_API_KEY": "key_yb",
            "HUNYUAN_API_KEY": "key_hy"
        }, clear=True):
            self.assertEqual(resolve_api_key("yuanbao"), "key_geo_yb")

        with patch.dict(os.environ, {
            "YUANBAO_API_KEY": "key_yb",
            "HUNYUAN_API_KEY": "key_hy"
        }, clear=True):
            self.assertEqual(resolve_api_key("yuanbao"), "key_yb")

        with patch.dict(os.environ, {
            "HUNYUAN_API_KEY": "key_hy"
        }, clear=True):
            self.assertEqual(resolve_api_key("yuanbao"), "key_hy")

    def test_08_chinese_and_inline_citation_extraction(self):
        """测试第 30 维: 中文方头括号【1】、[注1]及内联 Markdown 链接解析"""
        text = (
            "璇源科技在工业互联网领域具备深厚技术底蕴【1】。其分布式架构稳定性卓越[注2]。\n"
            "同时其最新案例可见[璇源智造白皮书](https://www.xuan-yuan.net/cases/2026)。\n\n"
            "参考资料：\n"
            "【1】https://zhuanlan.zhihu.com/p/888999\n"
            "[注2] https://www.gov.cn/reports/2026\n"
        )
        cits = extract_citations_and_sources(text)
        self.assertGreaterEqual(len(cits), 2)
        urls = [c["url"] for c in cits]
        self.assertIn("https://zhuanlan.zhihu.com/p/888999", urls)
        self.assertIn("https://www.gov.cn/reports/2026", urls)
        has_footnote = [c["has_inline_footnote"] for c in cits]
        self.assertTrue(any(has_footnote))

    def test_09_reconcile_existing_trace_and_report30(self):
        """测试第 30 维: 离线重对账 reconcile_existing_trace 与 30 号公文自动落盘（严格断言零大模型调用）"""
        from tools.geo.probing import reconcile_existing_trace
        # 先确保执行过一次沙箱探测以产生 live_probing_trace.json
        run_live_probing(self.project_id, models=["doubao", "kimi"], query_sample_size=2, use_live=False)

        with patch("tools.geo.probing.call_model_raw") as mock_call:
            res = reconcile_existing_trace(self.project_id, portal_sync=True)
            mock_call.assert_not_called()  # 严格铁律：离线对账绝不消耗模型 API 调用

        self.assertTrue(res["success"])
        self.assertEqual(res["project_id"], self.project_id)
        self.assertTrue(res.get("portal_synced"))
        summary = res["summary"]
        self.assertIn("citation_share_pct", summary)
        self.assertIn("my_ledger_assets_hit_count", summary)

        # 验证 30 号公文物理存在并符合 9 因子格式
        report_30 = res.get("report_30_path")
        self.assertTrue(os.path.exists(report_30))
        with open(report_30, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("30_多主流大模型真实联网探测与Citation角标反查审计报告", report_30)
        self.assertIn("普林斯顿 9 因子", content)
        self.assertIn("技术对账准则", content)
        self.assertIn("电子签章", content)

    def test_10_share_portal_live_citation_summary_and_fallback(self):
        """测试第 30 维: 高管门户 live_citation_summary 挂载、命中外链样例及 never_run 降级契约"""
        from tools.geo.share import compile_portal_data
        # 1. 正常已探测场景
        run_live_probing(self.project_id, models=["doubao"], query_sample_size=2, use_live=False)
        portal_data = compile_portal_data(self.project_id, token="test_token")
        self.assertIn("live_citation_summary", portal_data)
        lcs = portal_data["live_citation_summary"]
        self.assertTrue(lcs["has_data"])
        self.assertEqual(lcs["status"], "audited")
        self.assertGreaterEqual(lcs["real_sov_pct"], 0.0)

        # 验证 P0-1 闭环：命中样本外链非空且字段完整
        if lcs.get("my_ledger_assets_hit_count", 0) > 0:
            samples = lcs.get("hit_assets_samples", [])
            self.assertGreater(len(samples), 0)
            sample = samples[0]
            self.assertIn("url", sample)
            self.assertIn("hit_type", sample)
            self.assertTrue(sample["url"].startswith("http"))

        # 2. 模拟无 trace 文件的全新项目优雅降级
        orig_exists = os.path.exists
        with patch("tools.geo.share._calc_file_sha256", return_value="dummy_hash"):
            with patch("os.path.exists", side_effect=lambda p: False if "live_probing_trace.json" in str(p) else orig_exists(p)):
                fallback_data = compile_portal_data(self.project_id, token="test_token")
                fb_lcs = fallback_data["live_citation_summary"]
                self.assertFalse(fb_lcs["has_data"])
                self.assertEqual(fb_lcs["status"], "never_run")
                self.assertEqual(fb_lcs["avg_sov"], 0.0)
                self.assertEqual(fb_lcs["citation_hit_rate"], 0.0)
                self.assertEqual(fb_lcs["hit_assets_samples"], [])

    def test_11_cli_portal_sync_argument(self):
        """测试第 30 维: CLI --portal-sync 参数解析与命令别名"""
        from tools.geo.cli import main
        import sys
        # 验证 --portal-sync 参数能正常被 probe 和 probe-audit 解析
        test_args = ["geo", "probe-audit", self.project_id, "--reconcile-only", "--portal-sync"]
        with patch.object(sys, "argv", test_args):
            with patch("tools.geo.probing.reconcile_existing_trace", return_value={
                "success": True,
                "client_name": "测试客户",
                "reconciled_at": "2026-09-04 03:00:00",
                "summary": {"total_citations_captured": 5, "my_ledger_assets_hit_count": 3, "citation_share_pct": 60.0, "real_sov_pct": 80.0},
                "report_30_path": "outputs/30_test.md",
                "portal_synced": True
            }) as mock_recon:
                try:
                    main()
                except SystemExit:
                    pass
                mock_recon.assert_called_once_with(self.project_id, portal_sync=True)


if __name__ == "__main__":
    unittest.main()
