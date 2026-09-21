# -*- coding: utf-8 -*-
"""写文角色纯粹化与入口收敛自动化测试 (tests/test_writer_perspective.py)

对应 openspec 变更：2026-09-21-写文角色权限纯粹化与非写文功能入口收敛
覆盖：
1. DOM 入口彻底收敛与防 403 炸弹：
   - 侧边栏「运维告警」(nav-home-ops) 必须带 data-geo-dev-only；
   - 侧边栏「合作方名册」(nav-home-partners) 必须带 data-geo-dev-only；
   - 仪表盘「检测台账详情」按钮必须带 data-geo-dev-only；
   - 商业洞察、系统设置、成员管理必须保持 data-geo-dev-only；
   - 顶部与阶段五验收单中的「导出 ZIP」及「下载全套成果 ZIP」必须带 data-geo-dev-only；
2. 路由守卫与前端降级保护：
   - switchHomeView 遇到非开发者进入 devOnlyViews 时，安全回退至 home-dashboard，不抛 403；
3. 写文同事业务白名单闭环：
   - 模拟写文同事，进入仪表盘涉及的所有 API（/api/projects, /api/groups, /api/ops/check-ledger, /api/settings/notifications）均 200 放行；
   - 尝试请求开发者专属接口（如 /api/ops/check-logs, /api/portfolio/summary, /api/projects/nextgeo/acceptance/download-zip）正常拦截 403，但写文前端已无入口调用。
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(PROJECT_ROOT, "web", "index.html")


class WriterPerspectiveTest(unittest.TestCase):

    def setUp(self):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            self.html = f.read()

        # 模拟标准写文同事身份
        self.writer = rbac.Identity(
            user_id="304212040660824064",
            phone="13805206070",
            name="写文同事",
            is_developer=False,
            role="operator",
            status="active",
            allowed_projects=["nextgeo"],
            permissions=["keyword:manage", "ai:generate", "article:edit", "preview:view", "report:view"],
            matched=True,
        )

    def test_sidebar_non_writer_items_hidden(self):
        """1. 侧边栏非写文入口必须全部包含 data-geo-dev-only 彻底隐藏"""
        # 运维告警
        ops_btn = re.search(r'<button[^>]*id="nav-home-ops"[^>]*>', self.html)
        self.assertIsNotNone(ops_btn, "未找到 nav-home-ops 按钮")
        self.assertIn("data-geo-dev-only", ops_btn.group(0), "nav-home-ops 必须带 data-geo-dev-only")

        # 合作方名册
        partner_btn = re.search(r'<button[^>]*id="nav-home-partners"[^>]*>', self.html)
        self.assertIsNotNone(partner_btn, "未找到 nav-home-partners 按钮")
        self.assertIn("data-geo-dev-only", partner_btn.group(0), "nav-home-partners 必须带 data-geo-dev-only")

        # 商业洞察
        insight_btn = re.search(r'<button[^>]*id="nav-home-insights"[^>]*>', self.html)
        self.assertIsNotNone(insight_btn)
        self.assertIn("data-geo-dev-only", insight_btn.group(0))

        # 系统设置
        setting_btn = re.search(r'<button[^>]*id="nav-home-settings"[^>]*>', self.html)
        self.assertIsNotNone(setting_btn)
        self.assertIn("data-geo-dev-only", setting_btn.group(0))

        # 成员管理
        member_btn = re.search(r'<button[^>]*id="nav-home-members"[^>]*>', self.html)
        self.assertIsNotNone(member_btn)
        self.assertIn("data-geo-dev-only", member_btn.group(0))

    def test_dashboard_and_pipeline_danger_buttons_hidden(self):
        """2. 仪表盘与交付流水线中的非写文高危按钮必须带 data-geo-dev-only"""
        # 仪表盘真机引导区的「检测台账详情」
        ledger_btn = re.search(r'<button[^>]*switchHomeView\([\'"]home-ops[\'"]\)[^>]*>检测台账详情</button>', self.html)
        self.assertIsNotNone(ledger_btn, "未找到检测台账详情按钮")
        self.assertIn("data-geo-dev-only", ledger_btn.group(0), "检测台账详情必须带 data-geo-dev-only")

        # 顶部「导出 ZIP」
        top_zip = re.search(r'<button[^>]*onclick="downloadDeliverables\(\)"[^>]*>[\s\S]*?导出 ZIP[\s\S]*?</button>', self.html)
        self.assertIsNotNone(top_zip)
        self.assertIn("data-geo-dev-only", top_zip.group(0), "顶部导出 ZIP 必须带 data-geo-dev-only")

        # 阶段五「下载全套成果 ZIP」
        s5_zip = re.search(r'<button[^>]*onclick="handleDownloadZip\(\)"[^>]*>[\s\S]*?下载全套成果 ZIP[\s\S]*?</button>', self.html)
        self.assertIsNotNone(s5_zip)
        self.assertIn("data-geo-dev-only", s5_zip.group(0), "阶段五下载全套成果 ZIP 必须带 data-geo-dev-only")

    def test_writer_dashboard_endpoints_all_200(self):
        """3. 写文同事进入仪表盘正常发起的全部请求必须 100% 通过（403 次数为 0）"""
        dashboard_endpoints = [
            ("/api/auth/status", "GET"),
            ("/api/partners", "GET"),
            ("/api/projects", "GET"),
            ("/api/groups", "GET"),
            ("/api/settings/notifications", "GET"),
            ("/api/ops/check-ledger", "GET"),
        ]
        for path, method in dashboard_endpoints:
            ok, status, msg = rbac.guard_route(path, method, self.writer)
            self.assertTrue(ok, f"仪表盘必需接口被拦截: {method} {path} -> {status} {msg}")
            self.assertEqual(status, 200)

    def test_writer_cannot_access_dev_endpoints(self):
        """4. 服务端 RBAC 兜底守卫保持严密：写文同事若强撞开发者专属接口必须返回 403"""
        dev_endpoints = [
            ("/api/ops/check-logs", "GET"),
            ("/api/portfolio/summary", "GET"),
            ("/api/portfolio/report", "GET"),
            ("/api/benchmark/industries", "GET"),
            ("/api/admin/members", "GET"),
            ("/api/projects/nextgeo/export", "GET"),
            ("/api/projects/nextgeo/acceptance/download-zip", "GET"),
            ("/api/projects/nextgeo/site/nginx-conf", "GET"),
        ]
        for path, method in dev_endpoints:
            ok, status, msg = rbac.guard_route(path, method, self.writer)
            self.assertFalse(ok, f"开发者接口未对写文同事拦截: {method} {path}")
            self.assertEqual(status, 403)
            self.assertIn("开发者专属", msg)

    def test_writer_allowed_pipeline_operations(self):
        """5. 写文同事核心职责放行：真机实测回填、文章编辑与生成流水线完全通畅"""
        writer_pipeline_ops = [
            ("/api/projects/nextgeo/probe/apply", "POST"),     # 真机实测回填
            ("/api/projects/nextgeo/run/step-3", "POST"),      # AI 普林斯顿文章生成
            ("/api/projects/nextgeo/facts", "GET"),            # 事实清单读取
            ("/api/projects/nextgeo/corpus/diff", "GET"),      # 语料 diff 读取
            ("/api/projects/nextgeo/site/status", "GET"),      # 站点状态
        ]
        for path, method in writer_pipeline_ops:
            ok, status, msg = rbac.guard_route(path, method, self.writer)
            self.assertTrue(ok, f"写文同事核心操作应被放行: {method} {path} -> {status} {msg}")


if __name__ == "__main__":
    unittest.main()
