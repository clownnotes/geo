# -*- coding: utf-8 -*-
"""母盘版本坐标系与责任田协作规范

对应 openspec 变更：2026-09-21-母盘版本坐标系与责任田协作规范
"""

import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402
from tools.geo.utils import load_project_config  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MasterVersionTest(unittest.TestCase):

    def setUp(self):
        self.writer = rbac.Identity(
            user_id="304212040660824064",
            phone="13805206070",
            name="写文同事",
            is_developer=False,
            role="operator",
            status="active",
            allowed_projects=["nextgeo", "demo_corp"],
            permissions=["keyword:manage", "ai:generate", "article:edit", "preview:view", "report:view"],
            matched=True,
        )
        self.dev = rbac.Identity(
            user_id="1",
            phone="10000000000",
            name="开发者",
            is_developer=True,
            role="developer",
            status="active",
            allowed_projects=[],
            permissions=[],
            matched=True,
        )

    def test_template_has_master_version_without_owner(self):
        path = os.path.join(PROJECT_ROOT, "projects", "_template", "project.yaml")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertRegex(text, r'(?m)^master_version:\s*"1\.0\.0"\s*$')
        self.assertNotRegex(text, r'(?m)^owner\s*:')

    def test_load_project_config_defaults_missing_version(self):
        with tempfile.TemporaryDirectory() as td:
            proj = os.path.join(td, "tmp_proj")
            os.makedirs(proj)
            with open(os.path.join(proj, "project.yaml"), "w", encoding="utf-8") as f:
                f.write('client_id: "tmp_proj"\nclient_name: "临时"\n')
            cfg = load_project_config("tmp_proj", projects_dir=td)
            self.assertEqual(cfg["master_version"], "1.0.0")
            with open(os.path.join(proj, "project.yaml"), "r", encoding="utf-8") as f:
                self.assertNotIn("master_version", f.read())

    def test_load_project_config_keeps_valid_version(self):
        with tempfile.TemporaryDirectory() as td:
            proj = os.path.join(td, "tmp_proj")
            os.makedirs(proj)
            with open(os.path.join(proj, "project.yaml"), "w", encoding="utf-8") as f:
                f.write('client_id: "tmp_proj"\nmaster_version: "2.3.4"\n')
            cfg = load_project_config("tmp_proj", projects_dir=td)
            self.assertEqual(cfg["master_version"], "2.3.4")

    def test_writer_raw_materials_post_denied_get_allowed(self):
        path = "/api/projects/nextgeo/raw_materials"
        ok, status, msg = rbac.guard_route(path, "POST", self.writer)
        self.assertFalse(ok)
        self.assertEqual(status, 403)
        self.assertIn("开发者专属", msg)

        ok, status, msg = rbac.guard_route(path, "GET", self.writer)
        self.assertTrue(ok, msg)
        self.assertEqual(status, 200)

        ok, status, msg = rbac.guard_route(path, "POST", self.dev)
        self.assertTrue(ok, msg)

    def test_raw_materials_not_in_method_blind_suffix_table(self):
        self.assertNotIn("/raw_materials", rbac.ROUTE_DEVELOPER_SUFFIXES)

    def test_writer_article_edit_still_works(self):
        ok, status, msg = rbac.guard_route(
            "/api/projects/nextgeo/answer-rewrite/save-final", "POST", self.writer
        )
        self.assertTrue(ok, msg)
        self.assertEqual(status, 200)

    def test_create_article_template_writes_version_next_to_date(self):
        path = os.path.join(PROJECT_ROOT, "scripts", "create_article.py")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn('"datePublished": "{date}T08:00:00+08:00"', text)
        self.assertIn('"version": "{master_version}"', text)
        self.assertIn("def read_master_version", text)
        self.assertNotIn("author_seat", text)

    def test_articles_without_version_stay_in_current_list(self):
        from scripts.build_blog_index import (
            article_in_current_generation,
            split_articles_by_master,
        )

        self.assertTrue(article_in_current_generation("", "2.0.0"))
        self.assertTrue(article_in_current_generation("2.1.0", "2.0.0"))
        self.assertFalse(article_in_current_generation("1.9.0", "2.0.0"))

        current, archived = split_articles_by_master(
            [
                {"title": "旧无坐标", "master_version": ""},
                {"title": "当前代", "master_version": "2.0.1"},
                {"title": "上一代", "master_version": "1.5.0"},
            ],
            "2.0.0",
        )
        titles_cur = [a["title"] for a in current]
        titles_arc = [a["title"] for a in archived]
        self.assertEqual(titles_cur, ["旧无坐标", "当前代"])
        self.assertEqual(titles_arc, ["上一代"])

    def test_frontend_has_no_post_raw_materials_save(self):
        """现码没有向 POST /raw_materials 写母盘的按钮；唯一调用是 GET。"""
        path = os.path.join(PROJECT_ROOT, "web", "index.html")
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        posts = re.findall(
            r'fetch\(`/api/projects/\$\{[^}]+\}/raw_materials`[\s\S]{0,200}?method:\s*[\'"]POST[\'"]',
            html,
        )
        self.assertEqual(posts, [], "不应出现对 /raw_materials 的 POST 保存入口")
        self.assertIn("/raw_materials", html)


if __name__ == "__main__":
    unittest.main()
