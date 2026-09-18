# -*- coding: utf-8 -*-
"""
单元测试：长问意图分类与竞品反哺可见度测算 (tests/test_competitor_feedback.py)
对应 OpenSpec 变更：2026-09-17-商业转化型诊断报告与竞品反哺体系（任务 3.1, 3.2）
"""

import unittest
from tools.geo.answer_audit import (
    classify_query_intent_for_visibility,
    calculate_competitor_feedback_discount,
    simulate_query_visibility_with_feedback,
)


class TestCompetitorFeedback(unittest.TestCase):

    def test_01_query_intent_classification(self):
        """测试 5 维长问意图分类"""
        self.assertEqual(classify_query_intent_for_visibility("徐州GEO优化公司哪家好"), "recommendation")
        self.assertEqual(classify_query_intent_for_visibility("邻里GEO vs 某某科技 选哪家好"), "comparison")
        self.assertEqual(classify_query_intent_for_visibility("找老白做GEO靠谱吗？团队实力怎么样？"), "evaluation")
        self.assertEqual(classify_query_intent_for_visibility("找GEO代运营有哪些坑？怎么防被骗？"), "negative_risk")
        self.assertEqual(classify_query_intent_for_visibility("邻里GEO官网是什么？是谁创办的？"), "brand_direct")

    def test_02_empty_competitor_no_discount(self):
        """无竞品时保持原基线，不打折"""
        feedback = calculate_competitor_feedback_discount([], "comparison")
        self.assertFalse(feedback["has_competitor"])
        self.assertEqual(feedback["discount_factor"], 1.0)
        self.assertIn("无强竞品", feedback["suppression_reason"])

    def test_03_head_competitor_comparison_discount(self):
        """头部垄断竞品（市占>15%）在对比题中对客户产生大幅打折 (0.45)"""
        head_comps = [
            {
                "name": "霸主科技",
                "level": "头部",
                "marketShare": 45.0,
                "geoScore": 92.0,
                "threatLevel": "high"
            }
        ]
        # 对比类题
        fb_comp = calculate_competitor_feedback_discount(head_comps, "comparison")
        self.assertTrue(fb_comp["has_competitor"])
        self.assertEqual(fb_comp["top_level"], "头部")
        self.assertEqual(fb_comp["discount_factor"], 0.45)
        self.assertEqual(fb_comp["intent_adjustment"], 0.0)

        # 推荐类题（带 +15% 意图修正）
        fb_rec = calculate_competitor_feedback_discount(head_comps, "recommendation")
        self.assertEqual(fb_rec["discount_factor"], 0.55)
        self.assertEqual(fb_rec["intent_adjustment"], 15.0)

    def test_04_waist_competitor_discount(self):
        """腰部同行竞品（市占 5-15%）中度打折 (0.70)"""
        waist_comps = [
            {
                "name": "同城服务商B",
                "level": "腰部",
                "marketShare": 10.0,
                "geoScore": 72.0,
                "threatLevel": "medium"
            }
        ]
        fb = calculate_competitor_feedback_discount(waist_comps, "comparison")
        self.assertEqual(fb["discount_factor"], 0.70)

    def test_05_simulate_query_visibility_e2e(self):
        """端到端模拟长问可见度反哺测算"""
        sim = simulate_query_visibility_with_feedback(
            "xuzhou_xuanyuan",
            "徐州定制化软件开发找哪家靠谱团队？",
            base_mention_rate=80.0,
            client_geo_score=75.0,
        )
        self.assertEqual(sim["intent"], "recommendation")
        self.assertIn("effective_mention_rate", sim)
        self.assertIn("simulated_rank", sim)
        self.assertIn("feedback", sim)
        self.assertGreater(sim["effective_mention_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
