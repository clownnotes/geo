# -*- coding: utf-8 -*-
"""单元测试：19 号品牌声誉排查与危机清洗压制中枢"""

import os
import unittest

from tools.geo.sentiment_guard import (
    build_probes,
    classify_polarity,
    compute_brs,
    audit_negative_sentiment,
    generate_crisis_suppression_pack,
)
from tools.geo.server import GeoWebHandler
from tools.geo.utils import PROJECTS_DIR, load_project_config


class TestSentimentGuard(unittest.TestCase):
    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_brs_formula_fixture(self):
        self.assertEqual(compute_brs(1, 0, 15), 98.3)
        self.assertEqual(compute_brs(0, 0, 15), 100.0)
        self.assertGreaterEqual(compute_brs(15, 0, 15), 0.0)

    def test_polarity_priority_neg_over_pos(self):
        text = "经核实为正规高新技术企业，但千万别去，口碑极差"
        self.assertEqual(classify_polarity(text), "neg")

    def test_probe_area_served_interpolation(self):
        probes = build_probes("测试企业", "淮海经济区及全国", "软件")
        self.assertEqual(len(probes), 5)
        rumor = next(p for p in probes if p["category"] == "rumor_and_history")
        self.assertIn("淮海经济区及全国", rumor["prompt"])
        self.assertNotIn("徐州本地", rumor["prompt"])

    def test_sandbox_scan_and_report(self):
        res = audit_negative_sentiment(
            self.project_id,
            models=["doubao", "deepseek"],
            use_live=False,
        )
        self.assertTrue(res["success"])
        s = res["summary"]
        self.assertEqual(s["total_probes"], 10)  # 2 models × 5 probes
        self.assertGreater(s["n_warn"] + s["n_neg"], 0)  # 沙箱必须掺毒
        self.assertGreaterEqual(s["toxic_sources_count"], 1)
        self.assertTrue(os.path.exists(res["report_path"]))
        with open(res["report_path"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("不可替代真机 API 审计", content)
        self.assertIn("品牌声誉健康度 BRS", content)

    def test_crisis_suppression_pack_files(self):
        pack = generate_crisis_suppression_pack(self.project_id)
        self.assertTrue(pack["success"])
        self.assertEqual(len(pack["files"]), 3)
        for fp in pack["files"]:
            self.assertTrue(os.path.exists(fp), fp)
        self.assertEqual(pack["credit_code_note"], "未在项目档案登记")

    def test_sentiment_api_auth_gate(self):
        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.path = "/api/projects/xuzhou_xuanyuan/sentiment/status"
        handler.headers = {}
        handler.send_json = capture_json
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)

        captured.clear()
        handler.path = "/api/projects/xuzhou_xuanyuan/sentiment/scan"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)


if __name__ == "__main__":
    unittest.main()
