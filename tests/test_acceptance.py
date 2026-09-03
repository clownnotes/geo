# -*- coding: utf-8 -*-
"""
单元测试：GEO 全景 16 维商业验收门户与结案交付中枢 (tests/test_acceptance.py)
"""

import os
import unittest
import zipfile
from tools.geo.acceptance import (
    DELIVERABLES_MANIFEST,
    calculate_fulfillment_score,
    generate_acceptance_report,
    export_project_archive_zip,
    generate_print_acceptance_html
)
from tools.geo.share import (
    create_share_link,
    get_share_portal_data
)
from tools.geo.utils import PROJECTS_DIR


class TestAcceptanceAndDeliveryHub(unittest.TestCase):

    def test_deliverables_manifest_16_dimensions(self):
        """测试 16 维全景主交付物清单结构完整性（分母严格为 16 项主报告）"""
        self.assertEqual(len(DELIVERABLES_MANIFEST), 16)
        
        indices = {item["index"] for item in DELIVERABLES_MANIFEST}
        # 必须包含 01 到 16 的核心主报告编号
        for expected_idx in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16"]:
            self.assertIn(expected_idx, indices, f"缺失编号 {expected_idx} 资产项")

        for item in DELIVERABLES_MANIFEST:
            self.assertIn("key", item)
            self.assertIn("name", item)
            self.assertIn("file", item)
            self.assertIn("candidates", item)
            self.assertIn("stage", item)
            self.assertGreater(len(item["name"]), 0)
            self.assertGreater(len(item["candidates"]), 0)

    def test_calculate_fulfillment_score_dual_track(self):
        """测试双轨制履约达成率评分与 16 维全景主报告核验"""
        res = calculate_fulfillment_score("xuzhou_xuanyuan")
        self.assertTrue(res["success"])
        # 轨 A：6 维合同商业履约分
        self.assertGreaterEqual(res["total_fulfillment_score"], 80.0)
        self.assertEqual(len(res["breakdown"]), 6)

        # 轨 B：16 维主交付物齐套率
        self.assertIn("manifest_summary", res)
        m_summary = res["manifest_summary"]
        self.assertEqual(m_summary["total_files"], 16)
        self.assertEqual(m_summary["generated_files"], 16)
        self.assertEqual(m_summary["generation_rate_pct"], 100.0)
        self.assertEqual(len(m_summary["missing_items"]), 0)

    def test_generate_acceptance_report(self):
        """测试《00_GEO商业交付验收结案确认单.md》自动生成与 summary JSON 持久化"""
        rep = generate_acceptance_report("xuzhou_xuanyuan")
        self.assertTrue(rep["success"])
        self.assertEqual(rep["filename"], "00_GEO商业交付验收结案确认单.md")
        self.assertIn("🏛️ GEO 生成式引擎优化商业交付验收结案确认单", rep["content"])
        self.assertIn("16 维全景交付产物数字资产清单", rep["content"])
        self.assertIn("双方验收签章与确认", rep["content"])

        # 检查 outputs 目录文件落地
        p_dir = os.path.join(PROJECTS_DIR, "xuzhou_xuanyuan", "outputs")
        report_file = os.path.join(p_dir, "00_GEO商业交付验收结案确认单.md")
        summary_file = os.path.join(p_dir, "acceptance_summary.json")
        self.assertTrue(os.path.exists(report_file))
        self.assertTrue(os.path.exists(summary_file))

    def test_export_project_archive_zip_security_exclusions(self):
        """测试 16 维全套交付物打包为 ZIP 归档压缩包并严格排除敏感内部文件"""
        zip_path = export_project_archive_zip("xuzhou_xuanyuan")
        self.assertTrue(os.path.exists(zip_path))
        self.assertGreater(os.path.getsize(zip_path), 10 * 1024)

        # 检查 ZIP 内容是否涵盖核心资产且排除了敏感内部配置
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("00_GEO商业交付验收结案确认单.md", namelist)
            self.assertIn("03_普林斯顿9因子高权威语料库.md", namelist)
            self.assertIn("16_大模型提示词注入防御与品牌隔离盾牌报告.md", namelist)
            
            # 严格排查敏感内部文件与临时目录
            for item in namelist:
                self.assertNotIn("roi_settings.json", item, "ZIP 归档包中泄露了内部财务配置 roi_settings.json")
                self.assertNotIn(".compliance_backup", item, "ZIP 归档包中包含了合规历史备份目录")
                self.assertFalse(item.endswith(".pyc"), "ZIP 归档包中包含了 Python 缓存文件")

    def test_share_portal_integration(self):
        """测试甲方免密只读门户与 16 维资产数据无缝装配"""
        lnk = create_share_link("xuzhou_xuanyuan", expire_days=7)
        token = lnk["token"]
        data = get_share_portal_data(token)
        self.assertTrue(data["success"])
        self.assertIn("acceptance_summary", data)
        self.assertIn("injection_guard_summary", data)
        self.assertIn("citation_auth_summary", data)
        self.assertIn("archive_info", data)
        self.assertTrue(data["archive_info"]["exists"])
        self.assertIn("deliverables", data)
        self.assertIn("acceptance", data["deliverables"])
        self.assertIn("injection_guard", data["deliverables"])

    def test_print_acceptance_html(self):
        """测试 A4 打印版结案单 HTML 渲染"""
        html = generate_print_acceptance_html("xuzhou_xuanyuan")
        self.assertIn("GEO商业交付验收结案确认单", html)
        self.assertIn("甲方（客户企业）", html)
        self.assertIn("乙方（交付服务商）", html)

    def test_four_industry_templates_full_coverage(self):
        """测试四大垂直行业母版 16 维全景资产 100% 齐套覆盖"""
        for pid in ["xuzhou_xuanyuan", "b2b_machinery", "local_legal", "retail_catering"]:
            ful = calculate_fulfillment_score(pid)
            self.assertTrue(ful["success"], f"{pid} 履约计算失败")
            ms = ful["manifest_summary"]
            self.assertEqual(ms["generation_rate_pct"], 100.0, f"{pid} 齐套率未达 100%: 缺失 {ms.get('missing_items')}")
            self.assertEqual(ms["generated_files"], 16, f"{pid} 生成数量不符合 16 项标准")


if __name__ == "__main__":
    unittest.main()
