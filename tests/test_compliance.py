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
    sanitize_project_deliverables
)


class TestComplianceAndSanitization(unittest.TestCase):

    def test_sanitize_content_text_p0_p1_p2(self):
        """测试敏感词精准命中与智能替换 Diff"""
        sample_text = (
            "我们是全国第一的行业第一品牌，提供国家级品质保证。\n"
            "加微信免费领资料，稳赚不赔绝对保真。\n"
            "律师团队承诺包打赢，机械设备永不磨损零故障。"
        )

        clean_text, diffs = sanitize_content_text(sample_text)

        # 断言替换效果
        self.assertNotIn("全国第一", clean_text)
        self.assertNotIn("国家级", clean_text)
        self.assertNotIn("加微信", clean_text)
        self.assertNotIn("包打赢", clean_text)
        self.assertNotIn("零故障", clean_text)

        self.assertIn("业内高标准", clean_text)
        self.assertIn("对接官方直营团队", clean_text)
        self.assertIn("胜诉研判", clean_text)

        # 断言 Diff 记录
        self.assertGreaterEqual(len(diffs), 5)
        terms = [d["matched_term"] for d in diffs]
        self.assertIn("国家级", terms)
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
        """测试四大母版项目的合规体检、报告落盘与一键脱敏"""
        for pid in ["xuzhou_xuanyuan", "b2b_machinery", "retail_catering", "local_legal"]:
            res = inspect_content_compliance(pid)

            self.assertTrue(res["success"])
            self.assertEqual(res["project_id"], pid)
            self.assertIn("compliance_score", res)
            self.assertGreaterEqual(res["compliance_score"], 50.0)

            # 验证落盘文件
            json_file = f"projects/{pid}/outputs/compliance_inspection.json"
            md_file = f"projects/{pid}/outputs/13_多渠道内容合规与广告法风控审查报告.md"
            self.assertTrue(os.path.exists(json_file))
            self.assertTrue(os.path.exists(md_file))

            with open(md_file, "r", encoding="utf-8") as f:
                md_text = f.read()
                self.assertIn("多渠道内容合规审查与广告法风控审查报告", md_text)
                self.assertIn("内容合规与风控大盘", md_text)
                self.assertIn("多渠道发稿合规作战红线指南", md_text)

            # 测试一键脱敏执行
            san_res = sanitize_project_deliverables(pid)
            self.assertTrue(san_res["success"])
            self.assertGreaterEqual(san_res["latest_compliance_score"], 80.0)


if __name__ == "__main__":
    unittest.main()
