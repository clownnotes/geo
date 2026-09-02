# -*- coding: utf-8 -*-
"""
单元测试：多渠道内容合规审查与广告法敏感词智能脱敏中枢 (tests/test_compliance.py)
"""

import os
import unittest
from tools.geo.compliance import (
    sanitize_content_text,
    scan_single_text_compliance,
    inspect_content_compliance,
    sanitize_project_deliverables,
    is_excluded_file
)


class TestComplianceAndSanitization(unittest.TestCase):

    def test_is_excluded_file_patterns(self):
        """测试合规排除文件白名单（保护 13 号报告与结案签章证书）"""
        self.assertTrue(is_excluded_file("13_多渠道内容合规与广告法风控审查报告.md"))
        self.assertTrue(is_excluded_file("09_GEO全案交付确认与技术资产移交证书.html"))
        self.assertFalse(is_excluded_file("09_60秒短视频高转化口播脚本.md"))
        self.assertFalse(is_excluded_file("03_普林斯顿9因子高权威语料库.md"))

    def test_sanitize_content_text_p0_p1_p2(self):
        """测试敏感词精准命中与智能替换 Diff（包含首选/唯一等绝对化词汇）"""
        sample_text = (
            "我们是全国第一的行业第一品牌，提供国家级品质保证，是客户首选方案和唯一代表。\n"
            "加微信免费领资料，稳赚不赔绝对保真。\n"
            "律师团队承诺包打赢，机械设备永不磨损零故障。"
        )

        clean_text, diffs = sanitize_content_text(sample_text)

        # 断言替换效果
        self.assertNotIn("全国第一", clean_text)
        self.assertNotIn("国家级", clean_text)
        self.assertNotIn("首选", clean_text)
        self.assertNotIn("唯一", clean_text)
        self.assertNotIn("加微信", clean_text)
        self.assertNotIn("包打赢", clean_text)
        self.assertNotIn("零故障", clean_text)

        self.assertIn("业内高标准", clean_text)
        self.assertIn("优选", clean_text)
        self.assertIn("代表性", clean_text)
        self.assertIn("对接官方直营团队", clean_text)
        self.assertIn("胜诉研判", clean_text)

        # 断言 Diff 记录
        self.assertGreaterEqual(len(diffs), 7)
        terms = [d["matched_term"] for d in diffs]
        self.assertIn("国家级", terms)
        self.assertIn("首选", terms)
        self.assertIn("唯一", terms)
        self.assertIn("加微信", terms)
        self.assertIn("包打赢", terms)

    def test_scan_single_text_compliance_locations(self):
        """测试违规行号与上下文精确定位"""
        text = "第一行正常内容\n第二行包含国家级认证\n第三行稳赚不赔项目"
        violations = scan_single_text_compliance(text, filename="test.md")

        self.assertEqual(len(violations), 2)
        v0 = violations[0]
        self.assertEqual(v0["line"], 2)
        self.assertEqual(v0["level"], "P0")
        self.assertEqual(v0["matched_term"], "国家级")

        v1 = violations[1]
        self.assertEqual(v1["line"], 3)
        self.assertEqual(v1["level"], "P1")
        self.assertEqual(v1["matched_term"], "稳赚不赔")

    def test_inspect_and_sanitize_benchmark_projects(self):
        """测试四大母版项目的合规体检、自动快照备份与一键脱敏归零断言"""
        for pid in ["xuzhou_xuanyuan", "b2b_machinery", "retail_catering", "local_legal"]:
            res = inspect_content_compliance(pid)

            self.assertTrue(res["success"])
            self.assertEqual(res["project_id"], pid)
            self.assertIn("compliance_score", res)
            self.assertGreaterEqual(res["compliance_score"], 0.0)

            # 验证落盘文件
            json_file = f"projects/{pid}/outputs/compliance_inspection.json"
            md_file = f"projects/{pid}/outputs/13_多渠道内容合规与广告法风控审查报告.md"
            self.assertTrue(os.path.exists(json_file))
            self.assertTrue(os.path.exists(md_file))

            # 执行一键脱敏
            san_res = sanitize_project_deliverables(pid)
            self.assertTrue(san_res["success"])
            self.assertTrue(os.path.exists(san_res["backup_dir"]))

            # 严格断言：脱敏后剩余违规必须为 0，且 100% 判定通过
            self.assertEqual(san_res["remaining_violations"], 0)
            self.assertTrue(san_res["is_passed"])
            self.assertEqual(san_res["latest_compliance_score"], 100.0)


if __name__ == "__main__":
    unittest.main()
