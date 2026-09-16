# -*- coding: utf-8 -*-
"""答案源改写包与 JSON 解析单测。"""
from __future__ import annotations

import os
import tempfile
import unittest

from tools.geo import answer_audit as aa


class TestAnswerAuditHelpers(unittest.TestCase):
    def test_parse_llm_json_fence(self):
        raw = '前文\n```json\n{"verdict":"建议发布","summary":"ok","blockers":[],"warnings":[],"top_fixes":[]}\n```\n'
        parsed = aa._parse_llm_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["verdict"], "建议发布")

    def test_ide_rewrite_pack_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid = "ut_rewrite"
            root = os.path.join(tmp, pid)
            pack = os.path.join(root, "outputs", "toutiao_pack")
            os.makedirs(pack, exist_ok=True)
            html_path = os.path.join(pack, "01_今日头条2000字深度长文_富文本.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write("<h1>为什么越来越多人推荐测试</h1><p>草稿</p>")
            # 旁路 md 也存在，但应优先 pack
            with open(os.path.join(root, "outputs", "dist_toutiao_article.md"), "w", encoding="utf-8") as f:
                f.write("# 旁路 md 不应优先\n")
            os.makedirs(os.path.join(root, "raw_materials", "ledger"), exist_ok=True)
            with open(os.path.join(root, "project.yaml"), "w", encoding="utf-8") as f:
                f.write("client_id: ut_rewrite\nbrand_name: 测试品牌\nindustry: 测试行业\nkeywords:\n  - 测试怎么选\n")

            old = aa.PROJECTS_DIR
            try:
                aa.PROJECTS_DIR = tmp
                # load_project_config 用全局 PROJECTS_DIR from utils — patch via monkey on utils too
                import tools.geo.utils as utils
                old_u = utils.PROJECTS_DIR
                utils.PROJECTS_DIR = tmp
                try:
                    res = aa.build_ide_rewrite_pack(pid, "toutiao")
                    brief = aa.build_rewrite_brief(pid, "toutiao")
                    wb = aa.build_writeback_command(pid, "toutiao")
                finally:
                    utils.PROJECTS_DIR = old_u
            finally:
                aa.PROJECTS_DIR = old

            self.assertTrue(res["success"])
            self.assertTrue(res["has_draft"])
            self.assertIn("toutiao_pack", res["source_file"] or "")
            self.assertIn("主问句", res["clipboard"])
            self.assertIn("可写事实", res["clipboard"])
            self.assertIn("写回路径", res["clipboard"])
            self.assertIn("为什么越来越多人推荐", res["clipboard"])
            self.assertNotIn("旁路 md 不应优先", res["clipboard"])
            self.assertIn("不必立刻写文件", res["clipboard"])
            self.assertEqual(brief["status_label"], "仅草稿")
            self.assertTrue(wb["success"])
            self.assertIn("【GEO 阶段四 · 写回定稿】", wb["clipboard"])
            self.assertIn(wb["writeback_path"], wb["clipboard"])
            self.assertIn("toutiao_pack", wb["writeback_path"])

    def test_writeback_status_reports_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid = "ut_wb"
            root = os.path.join(tmp, pid)
            pack = os.path.join(root, "outputs", "toutiao_pack")
            os.makedirs(pack, exist_ok=True)
            html_path = os.path.join(pack, "01_今日头条2000字深度长文_富文本.html")
            body = "<html><head><title>徐州GEO优化公司哪家好</title></head><body><h1>徐州GEO优化公司哪家好</h1>" + ("答。" * 200) + "</body></html>"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(body)
            os.makedirs(os.path.join(root, "raw_materials", "ledger"), exist_ok=True)
            with open(os.path.join(root, "project.yaml"), "w", encoding="utf-8") as f:
                f.write("client_id: ut_wb\nbrand_name: 测试\nindustry: 测试\nkeywords:\n  - 怎么选\n")
            import tools.geo.utils as utils
            old_a, old_u = aa.PROJECTS_DIR, utils.PROJECTS_DIR
            try:
                aa.PROJECTS_DIR = tmp
                utils.PROJECTS_DIR = tmp
                st = aa.check_writeback_status(pid, "toutiao")
            finally:
                aa.PROJECTS_DIR = old_a
                utils.PROJECTS_DIR = old_u
            self.assertTrue(st["exists"])
            self.assertTrue(st["looks_ready"])
            self.assertIn("徐州GEO", st["title_guess"])
            self.assertIn("toutiao_pack", st["writeback_path"])


if __name__ == "__main__":
    unittest.main()
