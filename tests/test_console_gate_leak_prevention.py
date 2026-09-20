# -*- coding: utf-8 -*-
"""
单元与冒烟测试：纯内部未登录代码物理隔离与敏感文件防泄露
测试范围：
1. 未登录访客访问根路径仅返回纯净独立的 web/login.html，严禁泄露内部管理台 DOM/JS/SOP代码；
2. 敏感文件与源码（/.env, /tools/geo/server.py, /AGENTS.md, /data/rbac_members.json 等）未登录一律 404；
3. /api/auth/status 未登录时不自动发票、不返回 repo_root；
4. 登录后通过 Cookie/Token 访问 / 正常获得完整管理工作台 web/index.html；
5. 登出后清空 Cookie 并自动退回登录页，旧 Token 失效。
"""

import os
import sys
import unittest
import urllib.request
import urllib.error
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SERVER_URL = os.environ.get("GEO_TEST_SERVER", "http://127.0.0.1:8088")

class TestConsoleGateLeakPrevention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 确认测试服务器是否在线
        try:
            req = urllib.request.Request(f"{SERVER_URL}/", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                cls.server_online = True
        except Exception:
            cls.server_online = False

    def setUp(self):
        if not self.server_online:
            self.skipTest(f"测试目标服务器未运行于 {SERVER_URL}，跳过在线测试")

    def test_01_unauthenticated_root_serves_only_login_page(self):
        """未登录访问根路径只返回独立登录页，绝不包含内部工作台代码"""
        req = urllib.request.Request(f"{SERVER_URL}/", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("<title>GEO 交付管理端 - 登录</title>", body)
            self.assertIn('id="login-form"', body)
            # 严格断言：不得包含任何工作台内部特征词
            self.assertNotIn("dashboard-view", body)
            self.assertNotIn("wizard-view", body)
            self.assertNotIn("step-0-probe", body)
            self.assertNotIn("keywords_count", body)
            self.assertNotIn("ACTIVE_SESSIONS", body)
            self.assertLess(len(body), 20000, "登录页体积应保持在轻量级范围(<20KB)")

    def test_02_unauthenticated_web_index_bypass_intercepted(self):
        """未登录试图通过 /web/index.html 绕过，同样只返回独立登录页"""
        req = urllib.request.Request(f"{SERVER_URL}/web/index.html", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("<title>GEO 交付管理端 - 登录</title>", body)
            self.assertNotIn("dashboard-view", body)

    def test_03_unauthenticated_sensitive_files_all_404(self):
        """未登录访问任何配置文件、后端源码、文档、花名册均必须返回 404"""
        sensitive_paths = [
            "/.env",
            "/.env.dev",
            "/.env.prod",
            "/tools/geo/server.py",
            "/AGENTS.md",
            "/README.md",
            "/package.json",
            "/data/rbac_members.json",
            "/sites/nextgeo/",
            "/docs/",
            "/llms.txt",
            "/api/projects",
            "/api/benchmark/industries",
        ]
        for path in sensitive_paths:
            url = f"{SERVER_URL}{path}"
            with self.subTest(path=path):
                req = urllib.request.Request(url, method="GET")
                try:
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        self.fail(f"路径 {path} 未登录应返回 404，但返回了 {resp.status}")
                except urllib.error.HTTPError as e:
                    self.assertEqual(e.code, 404, f"路径 {path} 期望 404，实际得到 {e.code}")

    def test_04_unauthenticated_auth_status_does_not_leak_or_create_session(self):
        """未登录状态下请求 /api/auth/status 只返回未登录，不发放 Session，不泄露 repo_root"""
        req = urllib.request.Request(f"{SERVER_URL}/api/auth/status", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(data.get("authenticated"))
            self.assertNotIn("repo_root", data)
            self.assertNotIn("cd_cmd", data)
            self.assertNotIn("token", data)
            self.assertNotIn("allowed_projects", data)

    def test_05_authenticated_user_accesses_workspace(self):
        """持有有效 Session 的成员访问根路径，服务端放行并返回完整管理工作台"""
        from tools.geo.server import create_session
        test_token = create_session("运营同事", user_id="7d60e11b1f397703", phone="13805206070", role="operator")
        
        req = urllib.request.Request(f"{SERVER_URL}/", headers={"Cookie": f"geo_token={test_token}"}, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("dashboard-view", body)
            self.assertIn("GEO 商业交付与 SOP 流水线管理工作台", body)
            self.assertGreater(len(body), 500000, "完整工作台体积应大于 500KB")

        # 登出测试
        logout_req = urllib.request.Request(
            f"{SERVER_URL}/api/auth/logout",
            data=b"{}",
            headers={
                "Cookie": f"geo_token={test_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(logout_req, timeout=3) as lresp:
            self.assertEqual(lresp.status, 200)
            cookie_hdr = lresp.headers.get("Set-Cookie", "")
            self.assertIn("geo_token=", cookie_hdr)
            self.assertIn("Expires=", cookie_hdr)

        # 再次用旧 Token 访问，必须被拦截退回登录页
        retry_req = urllib.request.Request(f"{SERVER_URL}/", headers={"Cookie": f"geo_token={test_token}"}, method="GET")
        with urllib.request.urlopen(retry_req, timeout=3) as rresp:
            self.assertEqual(rresp.status, 200)
            rbody = rresp.read().decode("utf-8")
            self.assertIn("<title>GEO 交付管理端 - 登录</title>", rbody)
            self.assertNotIn("dashboard-view", rbody)


if __name__ == "__main__":
    unittest.main()
