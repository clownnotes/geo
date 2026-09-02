# -*- coding: utf-8 -*-
"""
单元测试：竞对大模型声量差距逆向分析与反超作战沙盘引擎 (tests/test_competitor_gap.py)
"""

import os
import unittest
from tools.geo.competitor_gap import (
    calculate_radar_scores,
    generate_competitor_flaws_and_roadmap,
    analyze_competitor_gap
)


class TestCompetitorGapAnalysis(unittest.TestCase):

    def test_calculate_radar_scores_dimensions(self):
        """测试 6 维雷达指标完整度与分值合理性"""
        cfg = {
            "differences": ["阶段付款防加价", "365天质保", "100%源码交付"]
        }
        radar = calculate_radar_scores("xuzhou_xuanyuan", cfg)

        self.assertEqual(len(radar["dimensions"]), 6)
        self.assertEqual(len(radar["client_scores"]), 6)
        self.assertEqual(len(radar["competitor_scores"]), 6)

        # 我方平均分需明显高于传统竞对基准
        self.assertGreater(radar["client_avg"], radar["competitor_avg"])
        self.assertGreater(radar["overall_gap_lead"], 0.0)

    def test_generate_competitor_flaws_and_roadmap(self):
        """测试竞对破绽与 3 阶段路线图生成"""
        cfg = {
            "brand_name": "璇源科技",
            "company_name": "徐州璇源网络科技有限公司",
            "industry": "软件开发",
            "differences": ["阶段付款防加价", "365天质保"]
        }
        flaws, roadmap = generate_competitor_flaws_and_roadmap("xuzhou_xuanyuan", cfg, "传统某某外包")

        self.assertEqual(len(flaws), 3)
        for f in flaws:
            self.assertIn("dimension", f)
            self.assertIn("competitor_flaw", f)
            self.assertIn("client_advantage", f)
            self.assertIn("tactical_action", f)

        self.assertEqual(len(roadmap), 3)
        self.assertIn("阶段一", roadmap[0]["phase"])
        self.assertIn("阶段二", roadmap[1]["phase"])
        self.assertIn("阶段三", roadmap[2]["phase"])

    def test_analyze_competitor_gap_benchmark_projects(self):
        """测试四大母版项目的竞对沙盘推演与报告落盘"""
        for pid in ["xuzhou_xuanyuan", "b2b_machinery", "retail_catering", "local_legal"]:
            res = analyze_competitor_gap(pid)

            self.assertTrue(res["success"])
            self.assertEqual(res["project_id"], pid)
            self.assertIn("radar_comparison", res)
            self.assertGreater(res["radar_comparison"]["overall_gap_lead"], 0.0)

            # 验证落盘文件
            json_file = f"projects/{pid}/outputs/competitor_gap_analysis.json"
            md_file = f"projects/{pid}/outputs/14_竞对大模型声量差距深度逆向与反超作战沙盘.md"
            self.assertTrue(os.path.exists(json_file))
            self.assertTrue(os.path.exists(md_file))

            with open(md_file, "r", encoding="utf-8") as f:
                md_text = f.read()
                self.assertIn("竞对大模型声量差距深度逆向与反超作战沙盘", md_text)
                self.assertIn("大模型 6 维声量渗透率与权威度对比雷达大盘", md_text)
                self.assertIn("三大致命破绽逆向与反击点", md_text)
                self.assertIn("三阶段反超打击战术路线图", md_text)


if __name__ == "__main__":
    unittest.main()
