# -*- coding: utf-8 -*-
"""
单元测试：11 维标准竞品 Schema、检索模板与 <=5 截断逻辑 (tests/test_competitor_gap_v2.py)
对应 OpenSpec 变更：2026-09-17-商业转化型诊断报告与竞品反哺体系（任务 2.1, 2.2, 2.3）
"""

import os
import json
import unittest
from tools.geo.competitor_gap import (
    COMPETITOR_SEARCH_TEMPLATES,
    build_competitor_search_queries,
    derive_competitor_level_and_threat,
    normalize_competitor_profile,
    filter_and_cap_competitors,
    build_structured_competitor_analysis,
    render_structured_competitors_table,
    render_competitor_gap_markdown,
)


class TestCompetitorGapV2(unittest.TestCase):

    def test_01_search_query_templates(self):
        """测试 7 大真实检索查询词模板生成"""
        queries = build_competitor_search_queries("本地生活GEO", "邻里GEO")
        self.assertEqual(len(queries), 7)
        self.assertIn("本地生活GEO 排名 2026", queries)
        self.assertIn("邻里GEO 竞品 对比", queries)
        self.assertIn("2026 本地生活GEO 市场份额", queries)

    def test_02_level_and_threat_anchor(self):
        """测试市占率与分级/威胁等级锚定逻辑"""
        # 头部: >15%
        lvl, threat = derive_competitor_level_and_threat(market_share=25.0, geo_score=85.0)
        self.assertEqual(lvl, "头部")
        self.assertEqual(threat, "high")

        # 腰部: 5-15%
        lvl, threat = derive_competitor_level_and_threat(market_share=8.0, geo_score=70.0)
        self.assertEqual(lvl, "腰部")
        self.assertEqual(threat, "medium")

        # 长尾: <5%
        lvl, threat = derive_competitor_level_and_threat(market_share=2.0, geo_score=50.0)
        self.assertEqual(lvl, "长尾")
        self.assertEqual(threat, "low")

    def test_03_normalize_competitor_11_dimensions(self):
        """测试 11 维 Schema 标准化完整性与默认值"""
        raw = {
            "name": "杭州爱搜索",
            "category": "GEO优化服务",
            "geoScore": 92,
            "marketShare": 43.0,
            "source": "real",
            "strengths": ["全域GEO源头厂", "自研引擎"],
            "weaknesses": ["价格偏高"],
            "productFeatures": ["技术壁垒高"],
            "description": "全域GEO源头厂，自研引擎",
            "website": "https://example.com",
        }
        profile = normalize_competitor_profile(raw)

        # 检查全部 11 维字段
        required_keys = [
            "name", "level", "category", "geoScore", "marketShare",
            "threatLevel", "strengths", "weaknesses", "productFeatures",
            "description", "website", "source"
        ]
        for k in required_keys:
            self.assertIn(k, profile)

        self.assertEqual(profile["name"], "杭州爱搜索")
        self.assertEqual(profile["level"], "头部")
        self.assertEqual(profile["threatLevel"], "high")
        self.assertEqual(profile["source"], "real")

    def test_04_virtual_source_tagging(self):
        """AI 推理补充字段强制标 source: 'virtual'"""
        raw = {
            "name": "某虚构竞品公司",
            "source": "virtual"
        }
        profile = normalize_competitor_profile(raw, default_category="软件开发")
        self.assertEqual(profile["source"], "virtual")
        self.assertIsNone(profile["marketShare"])
        self.assertGreater(profile["geoScore"], 0.0)

    def test_05_cap_max_5_competitors(self):
        """竞品数量必须严格约束在 <=5 家，且真实数据优先、大份额优先"""
        candidates = [
            {"name": "虚拟1", "source": "virtual", "marketShare": 1.0, "geoScore": 50},
            {"name": "真实头部1", "source": "real", "marketShare": 40.0, "geoScore": 90},
            {"name": "真实头部2", "source": "real", "marketShare": 30.0, "geoScore": 85},
            {"name": "虚拟头部", "source": "virtual", "marketShare": 20.0, "geoScore": 80},
            {"name": "真实腰部", "source": "real", "marketShare": 10.0, "geoScore": 75},
            {"name": "虚拟腰部", "source": "virtual", "marketShare": 8.0, "geoScore": 60},
            {"name": "虚拟长尾", "source": "virtual", "marketShare": 2.0, "geoScore": 40},
        ]
        capped = filter_and_cap_competitors(candidates, max_count=5)
        self.assertEqual(len(capped), 5)
        # 真实数据必须排在前面
        self.assertEqual(capped[0]["name"], "真实头部1")
        self.assertEqual(capped[1]["name"], "真实头部2")
        self.assertEqual(capped[2]["name"], "真实腰部")

    def test_06_render_table_0_emoji(self):
        """测试 Markdown 表格渲染严格遵守 0 Emoji 规范"""
        competitors = [
            {
                "name": "博盈科技",
                "level": "头部",
                "geoScore": 84,
                "marketShare": 48.0,
                "threatLevel": "high",
                "source": "real",
                "description": "本地霸主",
            },
            {
                "name": "某推演竞品",
                "level": "腰部",
                "geoScore": 70,
                "marketShare": None,
                "threatLevel": "medium",
                "source": "virtual",
                "description": "虚拟推演标杆",
            },
        ]
        table_md = render_structured_competitors_table(competitors)
        self.assertIn("[真实]", table_md)
        self.assertIn("[虚拟]", table_md)
        # 绝不能出现 Emoji
        for emoji in ["⚠️", "🟢", "🟡", "🔴", "📊", "🔥", "⚡️"]:
            self.assertNotIn(emoji, table_md)

    def test_07_build_structured_analysis_file(self):
        """测试 build_structured_competitor_analysis 输出文件与 Schema 完整性"""
        res = build_structured_competitor_analysis("xuzhou_xuanyuan")
        self.assertEqual(res["client_id"], "xuzhou_xuanyuan")
        self.assertIn("competitors", res)
        self.assertLessEqual(len(res["competitors"]), 5)
        self.assertIn("brandStrengths", res)
        self.assertIn("brandWeaknesses", res)
        self.assertIn("marketPosition", res)
        self.assertIn("source_summary", res)

        json_file = "projects/xuzhou_xuanyuan/outputs/competitor_analysis.json"
        self.assertTrue(os.path.exists(json_file))
        with open(json_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
            self.assertEqual(saved["client_id"], "xuzhou_xuanyuan")

        md_file = "projects/xuzhou_xuanyuan/outputs/06_同赛道竞品结构化档案与多维战力对照.md"
        self.assertTrue(os.path.exists(md_file))
        md = open(md_file, encoding="utf-8").read()
        self.assertIn("[虚拟]", md)
        for emoji in ["⚠️", "🟢", "🟡", "🔴", "📊", "🔥", "⚡️", "🏆"]:
            self.assertNotIn(emoji, md)
    def test_08_legacy_radar_markdown_0_emoji(self):
        """旧路径 render_competitor_gap_markdown 也必须 0 Emoji（tasks 2.4）"""
        gap = {
            "company_name": "测试公司",
            "brand_name": "测试品牌",
            "industry": "GEO",
            "target_competitor": "对照竞品",
            "analyzed_at": "2026-09-17 00:00:00",
            "radar_comparison": {
                "dimensions": ["价格透明度", "开源技术壁垒"],
                "client_scores": [80, 70],
                "competitor_scores": [60, 90],
                "client_avg": 75,
                "competitor_avg": 75,
                "overall_gap_lead": 0,
            },
            "competitor_advantages": [],
            "competitor_flaws": [],
            "leapfrog_roadmap": [],
        }
        md = render_competitor_gap_markdown("demo", gap)
        self.assertIn("领先 +20分", md)
        self.assertIn("落后 -20分", md)
        self.assertIn("综合持平", md)
        for emoji in ["⚠️", "🟢", "🟡", "🔴", "⚪", "📊", "🔥", "⚡️", "✅", "❌"]:
            self.assertNotIn(emoji, md)


if __name__ == "__main__":
    unittest.main()
