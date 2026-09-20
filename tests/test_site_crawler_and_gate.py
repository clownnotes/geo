# -*- coding: utf-8 -*-
"""
单元与回归测试：官网公开静态页面放行与 AI 爬虫协议绝对优先保障
测试范围：
1. 未登录公网访客与 AI 爬虫访问公开官网 /sites/nextgeo/ 必须返回 200 OK，严禁包含 noindex 阻断头；
2. 访问 /sites/nextgeo（缺少尾部斜杠）必须强制 301 重定向至 /sites/nextgeo/；
3. 根目录大模型爬虫探针 /robots.txt, /llms.txt, /sitemap.xml 未登录必须放行并返回 200 OK；
4. 敏感配置文件与后端代码（/.env, /tools/geo/server.py, /AGENTS.md 等）未登录必须坚决返回 404；
5. 私有管理后台接口（/api/projects/nextgeo）未登录必须坚决返回 404；
6. 根路径 / 未登录只下发独立的轻量登录页。
"""

import os
import sys
import time
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo.server import GeoWebHandler


class TestSiteCrawlerAndGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GeoWebHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_01_unauthenticated_public_site_serves_200_without_noindex(self):
        """未登录公网访客与 AI 爬虫访问 /sites/nextgeo/ 必须 200，且严禁携带 noindex 响应头"""
        req = urllib.request.Request(
            f"{self.base_url}/sites/nextgeo/",
            headers={"User-Agent": "Mozilla/5.0 (compatible; Bytespider; +https://zhanzhang.toutiao.com/)"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("<title>", body.lower())
            # 必须严禁携带任何阻止大模型爬虫收录的 noindex/nofollow 响应头
            robots_tag = resp.headers.get("X-Robots-Tag", "")
            self.assertNotIn("noindex", robots_tag.lower(), "公开官网绝对严禁附加 noindex 响应头！")
            self.assertNotIn("noarchive", robots_tag.lower())

    def test_02_unauthenticated_site_trailing_slash_redirects_301(self):
        """未登录访问缺少尾部斜杠的 /sites/nextgeo 必须 301 重定向，防止 CSS 与图片相对路径 404"""
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirectHandler)
        req = urllib.request.Request(f"{self.base_url}/sites/nextgeo", method="GET")
        try:
            resp = opener.open(req, timeout=5)
            self.assertEqual(resp.status, 301)
            self.assertTrue(resp.headers.get("Location", "").endswith("/sites/nextgeo/"))
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 301)
            self.assertTrue(e.headers.get("Location", "").endswith("/sites/nextgeo/"))

    def test_03_unauthenticated_crawler_files_serve_200(self):
        """各大 AI 爬虫访问根目录 /robots.txt, /llms.txt, /sitemap.xml 必须 200 秒开"""
        crawler_probes = ["/robots.txt", "/llms.txt", "/sitemap.xml"]
        for probe in crawler_probes:
            with self.subTest(probe=probe):
                req = urllib.request.Request(
                    f"{self.base_url}{probe}",
                    headers={"User-Agent": "DeepSeek-R1-Bot/1.0"},
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.assertEqual(resp.status, 200, f"探针 {probe} 应返回 200")
                    content = resp.read().decode("utf-8")
                    self.assertGreater(len(content), 20, f"探针 {probe} 内容不应为空")
                    robots_tag = resp.headers.get("X-Robots-Tag", "")
                    self.assertNotIn("noindex", robots_tag.lower())

    def test_04_unauthenticated_sensitive_code_remains_404(self):
        """未登录访问敏感代码和内部配置（/.env, server.py 等）必须坚决返回 404，安全不打折"""
        sensitive_targets = [
            "/.env",
            "/.env.dev",
            "/tools/geo/server.py",
            "/AGENTS.md",
            "/data/rbac_members.json",
        ]
        for target in sensitive_targets:
            with self.subTest(target=target):
                req = urllib.request.Request(f"{self.base_url}{target}", method="GET")
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        self.fail(f"敏感文件 {target} 未登录应返回 404，但返回了 {resp.status}")
                except urllib.error.HTTPError as e:
                    self.assertEqual(e.code, 404, f"敏感文件 {target} 必须返回 404，实际得到 {e.code}")

    def test_05_unauthenticated_private_api_remains_404(self):
        """未登录访问内部私有业务 API 必须坚决返回 404，不暴露数据结构"""
        private_apis = [
            "/api/projects",
            "/api/projects/nextgeo",
            "/api/ops/members",
        ]
        for api in private_apis:
            with self.subTest(api=api):
                req = urllib.request.Request(f"{self.base_url}{api}", method="GET")
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        self.fail(f"私有接口 {api} 未登录应返回 404，但返回了 {resp.status}")
                except urllib.error.HTTPError as e:
                    self.assertEqual(e.code, 404, f"私有接口 {api} 必须返回 404，实际得到 {e.code}")

    def test_06_unauthenticated_root_serves_login_page_only(self):
        """未登录普通浏览器访问根路径 / 只下发独立登录页"""
        req = urllib.request.Request(f"{self.base_url}/", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("登录", body)
            self.assertNotIn("dashboard-view", body)


if __name__ == "__main__":
    unittest.main()
