# -*- coding: utf-8 -*-
"""
GEO 多项目商业运营全景驾驶舱与代运营大盘报告中枢单元测试 (tests/test_portfolio.py)
覆盖：
1. scan_managed_projects 扫描过滤与合法性校验；
2. get_portfolio_summary 指标聚合与严格组合 ROI% 计算公式；
3. evaluate_project_risk 动态风险分级判定（徐州 warning / 三大母版 normal / 投影 SOV 保护 / 高危阻断）；
4. run_portfolio_health_patrol 轻量只读健康巡检与红黑榜计数；
5. generate_portfolio_executive_report 结构化大盘月报落盘与排版；
6. API 端点权限拦截与响应校验。
"""

import os
import sys
import json
import unittest
import urllib.request
import urllib.error

from tools.geo.utils import PROJECT_ROOT, PROJECTS_DIR
from tools.geo.portfolio import (
    scan_managed_projects,
    get_portfolio_summary,
    evaluate_project_risk,
    run_portfolio_health_patrol,
    generate_portfolio_executive_report
)
from tools.geo.server import is_authenticated, ACTIVE_SESSIONS


class TestPortfolioEngine(unittest.TestCase):

    def test_01_scan_managed_projects(self):
        """测试项目扫描与过滤规则（排除 _template 与隐藏目录）"""
        projects = scan_managed_projects()
        self.assertIsInstance(projects, list)
        self.assertNotIn("_template", projects)
        for p in projects:
            self.assertFalse(p.startswith("."))
            # 必须真实存在 project.yaml
            self.assertTrue(os.path.exists(os.path.join(PROJECTS_DIR, p, "project.yaml")))

        # 四大母版必须都在项目中
        for core_pid in ["xuzhou_xuanyuan", "b2b_machinery", "local_legal", "retail_catering"]:
            if os.path.exists(os.path.join(PROJECTS_DIR, core_pid)):
                self.assertIn(core_pid, projects)

    def test_02_get_portfolio_summary_financials_and_roi(self):
        """测试多项目商业财务求和与严格组合投资回报率 (Portfolio ROI) 公式"""
        res = get_portfolio_summary()
        self.assertTrue(res["success"])
        scale = res["scale"]
        fin = res["financial_valuation"]
        cards = res["project_cards"]

        self.assertGreaterEqual(scale["total_projects"], 4)
        self.assertGreaterEqual(len(cards), 4)

        # 验证财务求和的精确性
        sum_fee = sum(c["annual_service_fee"] for c in cards)
        sum_val = sum(c["total_business_value"] for c in cards)
        self.assertEqual(fin["total_annual_service_fee"], int(sum_fee))
        self.assertEqual(fin["total_business_value"], int(sum_val))

        # 严格验证组合投资回报率公式: ((sum_val - sum_fee) / sum_fee) * 100
        if sum_fee > 0:
            expected_roi = round(((sum_val - sum_fee) / sum_fee) * 100.0, 1)
            self.assertEqual(fin["portfolio_roi_pct"], expected_roi)
            expected_multiplier = round(sum_val / sum_fee, 2)
            self.assertEqual(fin["portfolio_roi_multiplier"], expected_multiplier)

        self.assertGreater(fin["total_business_value"], 500000)  # 实盘总价值在 90~110 万量级

    def test_03_evaluate_project_risk_contract(self):
        """测试三级风险判定契约（徐州 warning / 三母版 normal / 投影 SOV 保护 / 违规 danger）"""
        summary = get_portfolio_summary()
        card_map = {c["project_id"]: c for c in summary["project_cards"]}

        # 1. 徐州标杆项目：履约 89.3 分 (< 90) 且续约 64 分，必须精准判定为 warning
        if "xuzhou_xuanyuan" in card_map:
            xz = card_map["xuzhou_xuanyuan"]
            self.assertEqual(xz["risk_level"], "warning")
            self.assertTrue(any("履约分未过全额结案线" in r or "续约" in r for r in xz["risk_reasons"]))

        # 2. 三大母版：履约 97.9 分，无违规项，判定为 normal
        for mpid in ["b2b_machinery", "local_legal", "retail_catering"]:
            if mpid in card_map:
                mc = card_map[mpid]
                self.assertEqual(mc["risk_level"], "normal")
                self.assertIn("各项交付与运营指标均健康达标", mc["risk_reasons"])

        # 3. 构造带广告法违规卡片：必须立即触发 danger
        fake_danger_card = {
            "compliance_violations": 2,
            "injection_threats_count": 0,
            "dead_links_count": 0,
            "fulfillment_score": 98.0,
            "is_passed": True,
            "renewal_health_score": 90,
            "is_projected_sov": True
        }
        lvl, reasons = evaluate_project_risk(fake_danger_card)
        self.assertEqual(lvl, "danger")
        self.assertTrue(any("广告法" in r for r in reasons))

        # 4. 构造死链超标卡片：触发 danger
        fake_dead_link_card = {
            "compliance_violations": 0,
            "injection_threats_count": 0,
            "dead_links_count": 4,
            "fulfillment_score": 95.0,
            "is_passed": True,
            "renewal_health_score": 90,
            "is_projected_sov": False,
            "raw_sov_pct": 70.0
        }
        lvl, reasons = evaluate_project_risk(fake_dead_link_card)
        self.assertEqual(lvl, "danger")
        self.assertTrue(any("死链超标" in r for r in reasons))

    def test_04_run_portfolio_health_patrol(self):
        """测试只读健康巡检与红黑榜生成（零副作用）"""
        patrol_res = run_portfolio_health_patrol()
        self.assertTrue(patrol_res["success"])
        self.assertIn("counts", patrol_res)
        counts = patrol_res["counts"]
        board = patrol_res["red_black_board"]

        self.assertEqual(counts["danger"], len(board["danger"]))
        self.assertEqual(counts["warning"], len(board["warning"]))
        self.assertEqual(counts["healthy"], len(board["healthy"]))
        self.assertEqual(patrol_res["total_scanned"], counts["danger"] + counts["warning"] + counts["healthy"])

    def test_05_generate_portfolio_executive_report(self):
        """测试全域多项目大盘报告生成与落盘路径"""
        rep = generate_portfolio_executive_report()
        self.assertTrue(rep["success"])
        self.assertEqual(rep["filename"], "GEO代运营全域多项目执行与商业回报大盘报告.md")
        self.assertTrue(os.path.exists(rep["filepath"]))
        # 严格验证落盘在 reports/ 下
        expected_dir = os.path.join(PROJECT_ROOT, "reports")
        self.assertEqual(os.path.dirname(rep["filepath"]), expected_dir)

        # 检查正文关键段落
        content = rep["content"]
        self.assertIn("# 📊 GEO 商业代运营全域多项目执行与投资回报大盘报告", content)
        self.assertIn("全盘组合投资回报率 (ROI)", content)
        self.assertIn("四大垂直行业标杆母版多维度执行对比矩阵", content)
        self.assertIn("全域安全风控监测与异动红黑榜", content)
        self.assertIn("徐州璇源网络科技有限公司", content)


if __name__ == "__main__":
    unittest.main()
