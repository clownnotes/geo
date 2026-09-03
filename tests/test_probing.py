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


if __name__ == "__main__":
    unittest.main()
