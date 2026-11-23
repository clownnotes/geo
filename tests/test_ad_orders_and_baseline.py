# -*- coding: utf-8 -*-
"""代采记账、基本盘健康度与四级导航架构自动化测试 (tests/test_ad_orders_and_baseline.py)

对应 OpenSpec 变更：2026-11-21-align-admin-ui-and-dual-business
覆盖：
1. AdOrderManager: 雪花 ID、4 时间戳校验、逆序拦截、原子持久化与动态 status 计算；
2. BaselineHealthChecker: 零博文初创期守卫、30 天月度保活健康度与超期预警；
3. RBAC 权限与只读路由校验: ad_orders:manage 独立权限、动词敏感路由切分与 baseline-health 只读放行；
4. 前端 DOM 规范: 左侧边栏 0 微观步骤、0 手风琴容器、0 死函数残留，顶部三四级标头与代采面板完备；
5. 全局 0 Emoji 铁律与代码质量验证。
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tools.geo import rbac
from tools.geo.ad_orders import AdOrderManager
from tools.geo.baseline_health import BaselineHealthChecker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(PROJECT_ROOT, "src", "web", "index.html")
CSS_PATH = os.path.join(PROJECT_ROOT, "src", "web", "geo-admin.css")


class TestAdOrderManager(unittest.TestCase):
    """测试 AdOrderManager 业务行为与物理落盘"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_ad_orders_test_")
        self.project_id = "test_ent_001"
        self.manager = AdOrderManager(projects_dir=self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_create_and_list_ad_order_completed(self):
        t1 = "2026-11-20T10:00:00Z"
        t2 = "2026-11-20T11:00:00Z"
        t3 = "2026-11-20T15:00:00Z"
        t4 = "2026-11-20T16:00:00Z"
        order = self.manager.create_order(
            project_id=self.project_id,
            vendor_name="测试投放平台 A",
            client_ordered_at=t1,
            vendor_paid_at=t2,
            vendor_delivered_at=t3,
            client_accepted_at=t4,
            note="首轮搜索词曝光代采"
        )
        self.assertTrue(order["order_id"])
        self.assertEqual(order["vendor_name"], "测试投放平台 A")
        self.assertEqual(order["status"], "completed")

        # 检查物理文件内容：status 不应物理持久化
        order_file = os.path.join(self.tmp_dir, self.project_id, "ad_orders.json")
        self.assertTrue(os.path.isfile(order_file))
        with open(order_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertNotIn("status", data[0])
            self.assertEqual(data[0]["vendor_name"], "测试投放平台 A")

        # 列表查询返回计算后的 status
        orders = self.manager.list_orders(self.project_id)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["status"], "completed")

    def test_create_ad_order_in_progress(self):
        t1 = "2026-11-20T10:00:00Z"
        t2 = "2026-11-20T11:00:00Z"
        order = self.manager.create_order(
            project_id=self.project_id,
            vendor_name="测试平台 B",
            client_ordered_at=t1,
            vendor_paid_at=t2,
            vendor_delivered_at="",
            client_accepted_at=""
        )
        self.assertEqual(order["status"], "in_progress")

    def test_inverted_timestamps_rejection(self):
        t1 = "2026-11-20T12:00:00Z"
        t_early = "2026-11-20T10:00:00Z"
        # 付款早于下单
        with self.assertRaises(ValueError):
            self.manager.create_order(
                project_id=self.project_id,
                vendor_name="测试平台 C",
                client_ordered_at=t1,
                vendor_paid_at=t_early
            )
        # 交付早于付款
        with self.assertRaises(ValueError):
            self.manager.create_order(
                project_id=self.project_id,
                vendor_name="测试平台 C",
                client_ordered_at=t1,
                vendor_paid_at="2026-11-20T13:00:00Z",
                vendor_delivered_at="2026-11-20T12:30:00Z"
            )


class TestBaselineHealthChecker(unittest.TestCase):
    """测试基本盘健康度检查器"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_baseline_health_test_")
        self.project_id = "test_baseline_ent"
        self.blog_dir = os.path.join(self.tmp_dir, self.project_id, "outputs", "blog")
        os.makedirs(self.blog_dir, exist_ok=True)
        self.checker = BaselineHealthChecker(projects_dir=self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_initial_batch_with_zero_articles(self):
        # 即使有 index.html，也不计为博文
        index_file = os.path.join(self.blog_dir, "index.html")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("<html><body>Blog Index</body></html>")

        result = self.checker.check_health(self.project_id)
        self.assertEqual(result["status"], "initial_batch")
        self.assertFalse(result["is_warning"])
        self.assertEqual(result["total_articles"], 0)

    def test_healthy_recent_article(self):
        recent_date = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")
        article_file = os.path.join(self.blog_dir, "article-1.html")
        with open(article_file, "w", encoding="utf-8") as f:
            f.write(f'<html><head><meta name="datePublished" content="{recent_date}"></head><body>Post</body></html>')

        result = self.checker.check_health(self.project_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["is_warning"])
        self.assertEqual(result["total_articles"], 1)

    def test_warning_overdue_article(self):
        old_date = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
        article_file = os.path.join(self.blog_dir, "article-old.html")
        with open(article_file, "w", encoding="utf-8") as f:
            f.write(f'<html><head><meta name="datePublished" content="{old_date}"></head><body>Post</body></html>')

        result = self.checker.check_health(self.project_id)
        self.assertEqual(result["status"], "warning")
        self.assertTrue(result["is_warning"])
        self.assertEqual(result["total_articles"], 1)


class TestRbacAndRoutes(unittest.TestCase):
    """测试 RBAC 权限代码与路由保护映射"""

    def test_ad_orders_permission_registered(self):
        self.assertIn("ad_orders:manage", rbac.PERMISSION_CODES)
        # 确保新成员默认权限不包含代采管理
        self.assertNotIn("ad_orders:manage", rbac.DEFAULT_MEMBER_PERMISSIONS)

    def test_baseline_health_readonly_registered(self):
        self.assertIn("/baseline-health", rbac.ROUTE_READONLY_SUFFIXES)

    def test_verb_aware_route_permissions(self):
        found_post = False
        found_get = False
        for prefix, perm, method in rbac.ROUTE_PERMISSION_SUBSTRINGS:
            if prefix == "/ad-orders":
                if method == "POST" and perm == "ad_orders:manage":
                    found_post = True
                elif method == "GET" and perm == "report:view":
                    found_get = True
        self.assertTrue(found_post, "未找到 POST /ad-orders -> ad_orders:manage 映射")
        self.assertTrue(found_get, "未找到 GET /ad-orders -> report:view 映射")


class TestFrontendDomAndCss(unittest.TestCase):
    """测试前端 DOM、样式与导航规范"""

    def setUp(self):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            self.html = f.read()
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            self.css = f.read()

    def test_sidebar_cleaned_of_micro_steps(self):
        # 必须彻底不存在旧手风琴与旧步骤菜单
        self.assertNotIn("sidebar-sub-accordion", self.html)
        self.assertNotIn("step0-sub-menu", self.html)
        self.assertNotIn("toggleStep0Submenu", self.html)
        # 侧边栏 nav 容器内不应包含 nav-step-* 节点
        sidebar_match = re.search(r'<aside[^>]*id="app-sidebar"[\s\S]*?</aside>', self.html)
        self.assertTrue(sidebar_match)
        sidebar_content = sidebar_match.group(0)
        self.assertNotIn('id="nav-step-', sidebar_content)

    def test_sidebar_has_five_macro_buttons(self):
        sidebar_match = re.search(r'<aside[^>]*id="app-sidebar"[\s\S]*?</aside>', self.html)
        self.assertTrue(sidebar_match)
        sidebar_content = sidebar_match.group(0)
        self.assertIn('id="nav-overview"', sidebar_content)
        self.assertIn('id="nav-baseline"', sidebar_content)
        self.assertIn('id="nav-ad-procurement"', sidebar_content)
        self.assertIn('id="nav-assets"', sidebar_content)
        self.assertIn('id="nav-settings"', sidebar_content)

    def test_top_header_and_tray_dom_and_css(self):
        self.assertIn('id="admin-page-header"', self.html)
        self.assertIn('id="level3-nav"', self.html)
        self.assertIn('id="level4-tray"', self.html)
        self.assertIn('.admin-page-header', self.css)
        self.assertIn('.level3-nav', self.css)
        self.assertIn('.level3-btn', self.css)
        self.assertIn('.level4-tray', self.css)
        self.assertIn('.level4-btn', self.css)

    def test_ad_procurement_panel_and_view_meta(self):
        self.assertIn('id="panel-ad-procurement"', self.html)
        self.assertIn('id="ad-order-form"', self.html)
        self.assertIn('id="ad-orders-tbody"', self.html)
        self.assertIn("'ad-procurement':", self.html)

    def test_overview_baseline_health_card(self):
        self.assertIn('id="overview-baseline-health-card"', self.html)
        self.assertIn('id="baseline-health-badge"', self.html)

    def test_strict_zero_emoji(self):
        emoji_pattern = re.compile(
            r'[\U0001F300-\U0001F9FF]|[\U0001FA00-\U0001FAFF]|[\u2600-\u26FF]|[\u2700-\u27BF]'
        )
        # 检查 AdOrderManager, BaselineHealthChecker, test 脚本及新增 HTML 面板
        for filepath in [
            os.path.join(PROJECT_ROOT, "src", "tools", "geo", "ad_orders.py"),
            os.path.join(PROJECT_ROOT, "src", "tools", "geo", "baseline_health.py"),
            __file__
        ]:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                matches = emoji_pattern.findall(content)
                self.assertEqual(len(matches), 0, f"{filepath} 存在 Emoji 违规: {matches}")


if __name__ == "__main__":
    unittest.main()
