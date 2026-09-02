# -*- coding: utf-8 -*-
"""
单元测试：竞对大模型声量差距逆向分析与反超作战沙盘引擎 (tests/test_competitor_gap.py)
"""

import os
import unittest
from tools.geo.competitor_gap import (
    calculate_radar_scores,
    calculate_competitor_scores,
    generate_competitor_advantages,
    generate_competitor_flaws_and_roadmap,
    analyze_competitor_gap,
    _has_pricing_transparency,
)
from tools.geo.utils import load_project_config


class TestCompetitorGapAnalysis(unittest.TestCase):

    def test_has_pricing_transparency_stage_payment_variants(self):
        """阶段式验收付款等变体应命中价格透明判定"""
        self.assertTrue(_has_pricing_transparency("采用阶段式验收付款（定金30%）"))
        self.assertTrue(_has_pricing_transparency("阶段付款防加价"))
        self.assertFalse(_has_pricing_transparency("提供优质竭诚服务"))

    def test_calculate_radar_scores_dimensions(self):
        """测试 6 维雷达指标完整度与分值合理性"""
        cfg = {
            "differences": ["阶段付款防加价", "365天质保", "100%源码交付"]
        }
        radar = calculate_radar_scores("xuzhou_xuanyuan", cfg, "竞对A", ["竞对A", "竞对B"])

        self.assertEqual(len(radar["dimensions"]), 6)
        self.assertEqual(len(radar["client_scores"]), 6)
        self.assertEqual(len(radar["competitor_scores"]), 6)
        self.assertGreater(radar["client_avg"], radar["competitor_avg"])
        self.assertGreater(radar["overall_gap_lead"], 0.0)

    def test_xuzhou_eval_sov_integration(self):
        """应读取 06_ 评测报告中的真实 SOV 而非回退默认值"""
        cfg = load_project_config("xuzhou_xuanyuan")
        radar = calculate_radar_scores(
            "xuzhou_xuanyuan", cfg,
            cfg["competitors"][0], cfg["competitors"],
        )
        # xuzhou 母版评测报告 overall_sov_pct = 100.0，叠加 intent +3 后封顶 95
        self.assertEqual(radar["client_scores"][0], 95.0)

    def test_xuzhou_stage_payment_pricing_score(self):
        """xuzhou 母版阶段式验收付款应得 95 分价格透明度"""
        cfg = load_project_config("xuzhou_xuanyuan")
        radar = calculate_radar_scores(
            "xuzhou_xuanyuan", cfg,
            cfg["competitors"][0], cfg["competitors"],
        )
        self.assertEqual(radar["client_scores"][2], 95.0)

    def test_competitor_switch_changes_radar_scores(self):
        """切换竞对后雷达分值应产生可感知差异"""
        cfg = load_project_config("xuzhou_xuanyuan")
        comps = cfg["competitors"]
        r1 = calculate_radar_scores("xuzhou_xuanyuan", cfg, comps[0], comps)
        r2 = calculate_radar_scores("xuzhou_xuanyuan", cfg, comps[1], comps)
        self.assertNotEqual(r1["competitor_scores"], r2["competitor_scores"])
        self.assertNotEqual(r1["competitor_avg"], r2["competitor_avg"])

    def test_calculate_competitor_scores_deterministic(self):
        """同竞对名应产出稳定分值"""
        s1 = calculate_competitor_scores("华东重工机械贸易中介", ["华东重工机械贸易中介"])
        s2 = calculate_competitor_scores("华东重工机械贸易中介", ["华东重工机械贸易中介"])
        self.assertEqual(s1, s2)

    def test_generate_competitor_advantages(self):
        """测试竞对三大声量优势生成"""
        cfg = {"industry": "软件开发", "brand_name": "璇源科技"}
        advantages = generate_competitor_advantages(cfg, "传统某某外包")
        self.assertEqual(len(advantages), 3)
        for adv in advantages:
            self.assertIn("dimension", adv)
            self.assertIn("advantage", adv)
            self.assertIn("threat_level", adv)
            self.assertIn("neutralize_action", adv)

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
            self.assertEqual(len(res["competitor_advantages"]), 3)
            self.assertGreater(res["radar_comparison"]["overall_gap_lead"], 0.0)

            json_file = f"projects/{pid}/outputs/competitor_gap_analysis.json"
            md_file = f"projects/{pid}/outputs/14_竞对大模型声量差距深度逆向与反超作战沙盘.md"
            self.assertTrue(os.path.exists(json_file))
            self.assertTrue(os.path.exists(md_file))

            with open(md_file, "r", encoding="utf-8") as f:
                md_text = f.read()
                self.assertIn("竞对大模型声量差距深度逆向与反超作战沙盘", md_text)
                self.assertIn("大模型 6 维声量渗透率与权威度对比雷达大盘", md_text)
                self.assertIn("三大声量优势透视", md_text)
                self.assertIn("三大致命破绽逆向与反击点", md_text)
                self.assertIn("三阶段反超打击战术路线图", md_text)

    def test_analyze_with_explicit_competitor_name(self):
        """指定竞对名应写入结果且雷达分与默认竞对不同"""
        cfg = load_project_config("xuzhou_xuanyuan")
        default_res = analyze_competitor_gap("xuzhou_xuanyuan")
        alt_comp = cfg["competitors"][1]
        alt_res = analyze_competitor_gap("xuzhou_xuanyuan", competitor_name=alt_comp)

        self.assertEqual(alt_res["target_competitor"], alt_comp)
        self.assertNotEqual(
            default_res["radar_comparison"]["competitor_scores"],
            alt_res["radar_comparison"]["competitor_scores"],
        )


if __name__ == "__main__":
    unittest.main()
