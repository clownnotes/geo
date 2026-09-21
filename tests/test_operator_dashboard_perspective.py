# -*- coding: utf-8 -*-
"""运营端仪表盘角色视角改造与待办台账测试 (tests/test_operator_dashboard_perspective.py)

对应 openspec 变更：2026-09-20-运营端仪表盘角色视角改造与待办台账
覆盖：
1. 静态 HTML 结构与角色隔离：
   - panel-home-dashboard 内部包含 dashboard-dev-section (带 data-geo-dev-only) 与 dashboard-ops-section；
   - 运营四宫格：我的管辖企业、待真机实测、未完成交付、声量异常数 (严禁已结案企业)；
   - 待办列表容器 ops-action-list 存在；
   - 运营专属区绝对不包含金额符号（¥）、组合 ROI、估值等财务词汇；
   - 0 Emoji 违规，主文案严禁出现「SOP」；
   - 各控件完备白话帮助（title / toggleMetricHint）；
2. 服务端台账数据与时序位次：
   - build_check_ledger 返回行带 doubao_rank、doubao_rank_label、sov_alert、alert_reason；
   - summary 包含 sov_alert_count；
3. RBAC 租户多账号隔离：
   - 运营端 filter_check_ledger 严格按 allowed_projects 裁剪 rows 并重新计算 summary (包含 sov_alert_count)。
"""

import json
import os
import re
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import check_ledger  # noqa: E402
from tools.geo import rbac  # noqa: E402


class OperatorDashboardPerspectiveTest(unittest.TestCase):

    def setUp(self):
        self.web_index_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "index.html"
        )
        with open(self.web_index_path, "r", encoding="utf-8") as f:
            self.html_content = f.read()

    def test_dashboard_dev_ops_container_split(self):
        """1. 仪表盘容器按角色物理拆分：开发者区带 data-geo-dev-only，运营区独立存在"""
        # 提取 panel-home-dashboard
        dash_m = re.search(r'<section id="panel-home-dashboard"[\s\S]*?</section>', self.html_content)
        self.assertIsNotNone(dash_m, "未找到 panel-home-dashboard")
        dash_html = dash_m.group(0)

        # 检查开发者专属 section
        self.assertIn('id="dashboard-dev-section"', dash_html)
        dev_m = re.search(r'<div id="dashboard-dev-section"[^>]*data-geo-dev-only', dash_html)
        self.assertIsNotNone(dev_m, "dashboard-dev-section 必须包含 data-geo-dev-only 属性")

        # 检查运营专属 section
        self.assertIn('id="dashboard-ops-section"', dash_html)

        # 检查说明文案双向互斥
        self.assertIn('id="dashboard-desc-dev"', dash_html)
        self.assertIn('id="dashboard-desc-ops"', dash_html)

    def test_ops_four_cards_metrics_and_title(self):
        """2. 运营四宫格指标严格对应：我的管辖企业 / 待真机实测 / 未完成交付 / 声量异常数（严禁已结案企业）"""
        dash_m = re.search(r'<div id="dashboard-ops-section"[\s\S]*?</div>\s*</div>\s*</div>\s*</section>', self.html_content)
        self.assertIsNotNone(dash_m, "未找到 dashboard-ops-section")
        ops_html = dash_m.group(0)

        # DOM ID 存在性
        self.assertIn('id="ops-stat-my-projects"', ops_html)
        self.assertIn('id="ops-stat-need-probe"', ops_html)
        self.assertIn('id="ops-stat-pending-stage"', ops_html)
        self.assertIn('id="ops-stat-sov-alert"', ops_html)
        self.assertIn('id="ops-action-list"', ops_html)

        # 标题核对：第四格必须是「声量异常数」，禁止使用「已结案企业」
        self.assertIn("我的管辖企业", ops_html)
        self.assertIn("待真机实测", ops_html)
        self.assertIn("未完成交付", ops_html)
        self.assertIn("声量异常数", ops_html)
        self.assertNotIn("已结案企业", ops_html, "第四格违规使用了「已结案企业」，对齐产品必须为「声量异常数」")

    def test_ops_section_strictly_no_financial_terms(self):
        """3. 运营专属区绝对脱敏：禁止出现金额符号（¥）、商业总价值、组合 ROI 等财务词汇"""
        ops_m = re.search(r'<div id="dashboard-ops-section"[\s\S]*?</div>\s*</div>\s*</div>\s*</section>', self.html_content)
        self.assertIsNotNone(ops_m)
        ops_html = ops_m.group(0)

        self.assertNotIn("¥", ops_html, "运营专属区发现了金额符号 ¥")
        self.assertNotIn("商业总价值", ops_html, "运营专属区发现了商业总价值")
        self.assertNotIn("组合 ROI", ops_html, "运营专属区发现了组合 ROI")
        self.assertNotIn("portfolio_total_value", ops_html, "运营专属区绑定了全域财务弹窗")

    def test_ops_section_no_emoji_and_no_sop_text(self):
        """4. 视觉规范合规：运营区 0 Emoji，界面主文案严禁使用「SOP」"""
        ops_m = re.search(r'<div id="dashboard-ops-section"[\s\S]*?</div>\s*</div>\s*</div>\s*</section>', self.html_content)
        self.assertIsNotNone(ops_m)
        ops_html = ops_m.group(0)

        # 0 Emoji 检测
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
        emojis = emoji_pattern.findall(ops_html)
        self.assertEqual(len(emojis), 0, f"dashboard-ops-section 发现了 Emoji: {emojis}")

        # 禁止 SOP 主文案
        self.assertNotIn("SOP", ops_html, "dashboard-ops-section 主文案出现了 SOP")

    def test_ops_help_hints_present(self):
        """5. 白话帮助规范：四宫格、真机引导条、待办按钮具有 title 或 toggleMetricHint 气泡"""
        ops_m = re.search(r'<div id="dashboard-ops-section"[\s\S]*?</div>\s*</div>\s*</div>\s*</section>', self.html_content)
        self.assertIsNotNone(ops_m)
        ops_html = ops_m.group(0)

        # 检查各指标的问号气泡调用
        self.assertIn("toggleMetricHint(event,'ops_probe_badge')", ops_html)
        self.assertIn("toggleMetricHint(event,'ops_stat_my_projects')", ops_html)
        self.assertIn("toggleMetricHint(event,'ops_stat_need_probe')", ops_html)
        self.assertIn("toggleMetricHint(event,'ops_stat_pending_stage')", ops_html)
        self.assertIn("toggleMetricHint(event,'ops_stat_sov_alert')", ops_html)

        # 检查 METRIC_HINTS 中有对应的条目
        self.assertIn("ops_stat_my_projects:", self.html_content)
        self.assertIn("ops_stat_need_probe:", self.html_content)
        self.assertIn("ops_stat_pending_stage:", self.html_content)
        self.assertIn("ops_stat_sov_alert:", self.html_content)
        self.assertIn("ops_probe_badge:", self.html_content)

    def test_ops_probe_button_opens_manual_modal_not_step5(self):
        """5b. 「去真机回填」必须走 openManualCheckForProject，禁止 enterWizard(..., 5) 误进阶段五"""
        fn_m = re.search(
            r"async function renderOpsDashboard\(\) \{[\s\S]*?\n    \}",
            self.html_content,
        )
        self.assertIsNotNone(fn_m, "未找到 renderOpsDashboard")
        fn_body = fn_m.group(0)
        self.assertIn("openManualCheckForProject(", fn_body)
        self.assertIn("去真机回填", fn_body)
        # 去真机回填按钮的 onclick 必须是 openManualCheckForProject
        probe_btn = re.search(
            r'onclick="([^"]+)"[^>]*>去真机回填<',
            fn_body,
        )
        self.assertIsNotNone(probe_btn, "未找到「去真机回填」按钮")
        self.assertIn(
            "openManualCheckForProject(",
            probe_btn.group(1),
            "「去真机回填」未调用 openManualCheckForProject",
        )
        self.assertNotIn("enterWizard(", probe_btn.group(1))

        entry_m = re.search(
            r"async function openManualCheckForProject\([\s\S]*?\n    \}",
            self.html_content,
        )
        self.assertIsNotNone(entry_m, "未找到 openManualCheckForProject")
        entry = entry_m.group(0)
        self.assertIn("openManualProbeModal", entry)
        self.assertIn("mon-probing", entry)
    def test_check_ledger_backend_enrichment(self):
        """6. 后端台账注入豆包位次与声量异动状态"""
        res = check_ledger.build_check_ledger()
        self.assertTrue(res.get("success"))
        self.assertIn("rows", res)
        self.assertIn("summary", res)
        self.assertIn("sov_alert_count", res["summary"])

        # 遍历 rows，确保字段规范完整
        for r in res["rows"]:
            self.assertIn("doubao_rank", r)
            self.assertIn("doubao_rank_label", r)
            self.assertIn("sov_alert", r)
            self.assertIn("alert_reason", r)
            self.assertIsInstance(r["sov_alert"], bool)
            self.assertIsInstance(r["doubao_rank_label"], str)

    def test_rbac_check_ledger_filtering_for_operator(self):
        """7. 运营人员台账过滤：按 allowed_projects 裁剪，重算 summary (含 sov_alert_count)"""
        mock_payload = {
            "success": True,
            "policy": {"warn_days": 7, "overdue_days": 14},
            "summary": {
                "never": 2, "overdue": 1, "warn": 1, "ok": 2, "sov_alert_count": 3, "total": 6
            },
            "rows": [
                {"project_id": "proj_mine_1", "status": "overdue", "sov_alert": True},
                {"project_id": "proj_mine_2", "status": "ok", "sov_alert": False},
                {"project_id": "proj_other_1", "status": "never", "sov_alert": True},
                {"project_id": "proj_other_2", "status": "ok", "sov_alert": True},
            ]
        }

        # 构造运营身份
        op_ident = rbac.Identity(
            matched=True,
            is_developer=False,
            role="operator",
            name="测试运营",
            phone="13805206070",
            user_id="op_123",
            allowed_projects=["proj_mine_1", "proj_mine_2"],
            permissions=list(rbac.PERMISSION_CODES),
        )

        filtered = rbac.filter_check_ledger(mock_payload, op_ident)
        self.assertEqual(len(filtered["rows"]), 2)
        pids = [r["project_id"] for r in filtered["rows"]]
        self.assertEqual(set(pids), {"proj_mine_1", "proj_mine_2"})

        # 核对重新计算后的 summary
        s = filtered["summary"]
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["overdue"], 1)
        self.assertEqual(s["ok"], 1)
        self.assertEqual(s["never"], 0)
        self.assertEqual(s["sov_alert_count"], 1, "sov_alert_count 必须按管辖项目重新计算")

    def test_manual_check_lightweight_and_rbac_defense(self):
        """8. 真机回填轻量化与防卫改造：
        - openManualCheckForProject 不得调用 enterWizard(，防止并发预载未授权物料
        - loadStepPreviews 中 Step 3 普林斯顿语料库必须在 isDeveloper() 保护下
        - ROUTE_PUBLIC 包含 /api/auth/status
        - ROUTE_AUTHENTICATED 包含 /api/benchmark/industries
        - ROUTE_PERMISSION_SUFFIXES 包含 /publish/preview
        """
        # 1. 提取 openManualCheckForProject 函数体
        fn_m = re.search(
            r"async function openManualCheckForProject\([\s\S]*?\n    \}",
            self.html_content,
        )
        self.assertIsNotNone(fn_m)
        fn_code = fn_m.group(0)
        self.assertNotIn("enterWizard(", fn_code, "openManualCheckForProject 绝不能调用 enterWizard")
        self.assertIn("openManualProbeModal", fn_code)

        # 2. 检查 loadStepPreviews 中普林斯顿语料库的权限防卫
        load_preview_m = re.search(
            r"async function loadStepPreviews\(\)[\s\S]*?\n    \}",
            self.html_content,
        )
        self.assertIsNotNone(load_preview_m)
        lp_code = load_preview_m.group(0)
        self.assertIn("if (isDeveloper())", lp_code)
        self.assertIn("03_普林斯顿9因子高权威语料库.md", lp_code)

        # 3. 检查 RBAC 路由表（[2026-09-20] 行业大盘基准已收敛为开发者专属）
        self.assertIn("/api/auth/status", rbac.ROUTE_PUBLIC)
        self.assertIn("/api/benchmark/industries", rbac.ROUTE_DEVELOPER)
        self.assertTrue(any(s[0] == "/publish/preview" for s in rbac.ROUTE_PERMISSION_SUFFIXES))

    def test_manual_probe_resets_on_project_switch(self):
        """9. 换企业打开粘贴框必须重置词与答案（防跨企业状态残留）"""
        self.assertIn("function resetManualProbeUiForProject(", self.html_content)
        self.assertIn("boundProjectId", self.html_content)
        # openManualCheckForProject 必须主动 reset
        fn_m = re.search(
            r"async function openManualCheckForProject\([\s\S]*?\n    \}",
            self.html_content,
        )
        self.assertIsNotNone(fn_m)
        self.assertIn("resetManualProbeUiForProject", fn_m.group(0))
        # openManualProbeModal 换企业时也要 reset
        modal_m = re.search(
            r"async function openManualProbeModal\(\) \{[\s\S]*?\n    \}",
            self.html_content,
        )
        self.assertIsNotNone(modal_m)
        modal = modal_m.group(0)
        self.assertIn("boundProjectId !== currentProjectId", modal)
        self.assertIn("resetManualProbeUiForProject", modal)


if __name__ == "__main__":
    unittest.main()
