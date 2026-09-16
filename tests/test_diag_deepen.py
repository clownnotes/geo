# -*- coding: utf-8 -*-
"""diag_deepen：深化提示词组装 + 探活 answer_full 覆盖度。"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.geo import diag_deepen
from tools.geo import utils as utils_mod


class DiagDeepenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo_diag_deepen_")
        self.projects = os.path.join(self.tmp, "projects")
        os.makedirs(self.projects)
        self.pid = "demo_deepen"
        self.pdir = os.path.join(self.projects, self.pid)
        self.outdir = os.path.join(self.pdir, "outputs")
        os.makedirs(self.outdir)
        with open(os.path.join(self.pdir, "project.yaml"), "w", encoding="utf-8") as f:
            f.write(f'client_id: "{self.pid}"\nclient_name: "Demo"\n')

        self._patches = [
            patch.object(utils_mod, "PROJECTS_DIR", self.projects),
            patch.object(diag_deepen, "PROJECTS_DIR", self.projects),
            patch.object(diag_deepen, "PROJECT_ROOT", utils_mod.PROJECT_ROOT),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_probe(self, name, items):
        path = os.path.join(self.outdir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"probed_at": "2026-09-16T12:00:00+08:00", "items": items}, f, ensure_ascii=False)

    def test_audit_marks_verdict_only_as_gap(self):
        self._write_probe(
            "competitor_probe_20260916.json",
            [
                {"query": "q1", "doubao_verdict": "不认识", "mentioned_self": False},
                {"query": "q2", "answer_full": "短"},
            ],
        )
        audit = diag_deepen.audit_probe_answer_coverage(self.pid)
        self.assertTrue(audit["success"])
        self.assertEqual(audit["items_total"], 2)
        self.assertEqual(audit["items_with_full"], 0)
        self.assertFalse(audit["has_usable_full_answers"])

    def test_audit_accepts_long_answer_full(self):
        long_ans = "这是豆包的完整回答原文。" * 10  # > 80 chars
        self._write_probe(
            "competitor_probe_ok.json",
            [
                {"query": "q1", "answer_full": long_ans, "doubao_verdict": "中性"},
                {"query": "q2", "answer_text": long_ans},
            ],
        )
        audit = diag_deepen.audit_probe_answer_coverage(self.pid)
        self.assertEqual(audit["items_with_full"], 2)
        self.assertTrue(audit["has_usable_full_answers"])

    def test_build_prompt_appends_gap_note(self):
        self._write_probe(
            "competitor_probe_gap.json",
            [{"query": "q1", "doubao_verdict": "不认识"}],
        )
        res = diag_deepen.build_diag_deepen_prompt(self.pid)
        self.assertTrue(res["success"])
        self.assertIn(self.pid, res["clipboard"])
        self.assertIn("落盘缺口", res["clipboard"])
        self.assertFalse(res["probe_audit"]["has_usable_full_answers"])


if __name__ == "__main__":
    unittest.main()
