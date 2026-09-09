# -*- coding: utf-8 -*-
"""合作方名册与项目改挂回归（OpenSpec 审查建议补测）。"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.geo import partners as partners_mod
from tools.geo.partners import (
    _dump_partners_yaml,
    _parse_partners_yaml,
    _slug_id,
    create_partner,
    load_partners,
    resolve_partner_name,
    set_project_partner_id,
    update_partner,
)

class TestPartnersRegistry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo_partners_")
        self.partners_file = os.path.join(self.tmp, "geo_partners.yaml")
        self.projects_dir = os.path.join(self.tmp, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        self._p_file = patch.object(partners_mod, "PARTNERS_FILE", self.partners_file)
        self._p_root_projects = patch.object(partners_mod, "PROJECTS_DIR", self.projects_dir)
        self._p_file.start()
        self._p_root_projects.start()

    def tearDown(self):
        self._p_file.stop()
        self._p_root_projects.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_project(self, project_id: str, partner_id: str = "") -> str:
        p_dir = os.path.join(self.projects_dir, project_id)
        os.makedirs(os.path.join(p_dir, "outputs"), exist_ok=True)
        yaml_path = os.path.join(p_dir, "project.yaml")
        lines = [
            f'client_id: "{project_id}"',
            f'client_name: "测试客户 {project_id}"',
            'industry: "测试行业"',
        ]
        if partner_id:
            lines.append(f'partner_id: "{partner_id}"')
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return p_dir

    def test_dump_roundtrip_with_quotes_and_newline(self):
        rows = [
            {
                "id": "agent_quote",
                "name": '渠道"张三"\n分公司',
                "status": "active",
                "created_at": "2026-09-09",
            }
        ]
        text = _dump_partners_yaml(rows)
        self.assertIn('\\"', text)
        self.assertIn("\\n", text)
        parsed = _parse_partners_yaml(text)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["name"], '渠道"张三"\n分公司')
        self.assertEqual(parsed[0]["id"], "agent_quote")

    def test_slug_chinese_unique_same_second(self):
        ids = {_slug_id("张三渠道") for _ in range(20)}
        self.assertGreaterEqual(len(ids), 18)
        for pid in ids:
            self.assertTrue(pid.startswith("agent_"))

    def test_slug_avoids_existing(self):
        existing = {"agent_demo"}
        pid = _slug_id("Demo", existing)
        self.assertNotEqual(pid, "agent_demo")
        self.assertTrue(pid.startswith("agent_demo") or pid.startswith("agent_"))

    def test_create_update_archive_clears_projects(self):
        # load_project_config 读真实 PROJECTS_DIR；改挂路径需同时 patch utils
        with patch("tools.geo.utils.PROJECTS_DIR", self.projects_dir), patch(
            "tools.geo.partners.load_project_config"
        ) as mock_load:

            def _load(pid: str):
                p_dir = os.path.join(self.projects_dir, pid)
                yaml_path = os.path.join(p_dir, "project.yaml")
                partner = ""
                with open(yaml_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("partner_id:"):
                            partner = line.split(":", 1)[1].strip().strip('"')
                return {"_project_dir": p_dir, "partner_id": partner, "client_id": pid}

            mock_load.side_effect = _load

            row = create_partner('李四"合资"')
            self.assertEqual(row["name"], '李四"合资"')
            self.assertTrue(os.path.exists(self.partners_file))

            reloaded = load_partners()
            self.assertEqual(reloaded[0]["name"], '李四"合资"')

            self._make_project("_tmp_partner_a")
            set_project_partner_id("_tmp_partner_a", row["id"])
            self.assertEqual(resolve_partner_name(row["id"]), '李四"合资"')

            update_partner(row["id"], status="archived")
            with open(
                os.path.join(self.projects_dir, "_tmp_partner_a", "project.yaml"),
                encoding="utf-8",
            ) as f:
                body = f.read()
            self.assertRegex(body, r'(?m)^partner_id:\s*""\s*$')
            archived = load_partners(include_archived=True)
            self.assertEqual(archived[0]["status"], "archived")
            active_only = load_partners(include_archived=False)
            self.assertEqual(active_only, [])

if __name__ == "__main__":
    unittest.main()
