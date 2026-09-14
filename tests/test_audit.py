#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段一体检：metrics 真源 + LLM 解读降级 + 无假排名。"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from tools.geo import audit


class AuditMetricsTests(unittest.TestCase):
    def test_compute_tech_score_deductions(self):
        base = {
            "is_online": True,
            "has_ssr": True,
            "has_llms_txt": True,
            "has_json_ld": True,
            "text_density_ratio": 20.0,
        }
        self.assertEqual(audit.compute_tech_score(base), 100)
        low = dict(base, has_llms_txt=False, text_density_ratio=6.0)
        self.assertEqual(audit.compute_tech_score(low), 60)
        offline = {"is_online": False}
        self.assertEqual(audit.compute_tech_score(offline), 10)

    def test_save_and_build_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = {"_outputs_dir": td, "client_id": "demo", "probe_baseline_id": "probe:doubao:20260913"}
            audit_data = {
                "url": "https://www.baicl.cc",
                "is_online": True,
                "status_code": 200,
                "html_size_kb": 10.0,
                "has_ssr": True,
                "has_llms_txt": True,
                "has_json_ld": True,
                "clean_text_length": 1000,
                "text_density_ratio": 8.0,
                "robots_status": "已主动配置本土 AI 爬虫规则",
                "warnings": [],
            }
            metrics = audit.build_metrics("demo", cfg, audit_data, llm_status="skipped", llm_provider="none")
            path = audit.save_audit_metrics(cfg, metrics)
            self.assertTrue(os.path.isfile(path))
            loaded = json.loads(open(path, encoding="utf-8").read())
            self.assertEqual(loaded["tech_score"], 85)
            self.assertTrue(loaded["has_llms_txt"])
            self.assertEqual(loaded["llm_status"], "skipped")

    def test_visibility_table_no_fake_rank_without_probe(self):
        cfg = {}
        md = audit.generate_visibility_table(cfg, {"available": False, "items": [], "summary": {}})
        self.assertIn("不编造", md)
        self.assertNotIn("未上榜（<10）", md)

    def test_visibility_table_uses_probe_items(self):
        snap = {
            "available": True,
            "probe_baseline_id": "probe:doubao:20260913",
            "probe_file": "competitor_probe_doubao_20260913_retest.json",
            "summary": {"brand_status": "误解", "founder_status": "幻觉"},
            "items": [
                {
                    "query": "邻里GEO是做什么的",
                    "mentioned_self": False,
                    "url_present": False,
                    "standpoint": "误解",
                    "hallucination_detected": True,
                    "doubao_verdict": "概念解构",
                    "competitors": ["东昊"],
                }
            ],
        }
        md = audit.generate_visibility_table({}, snap)
        self.assertIn("邻里GEO是做什么的", md)
        self.assertIn("幻觉风险", md)
        self.assertIn("东昊", md)
        self.assertNotIn("未上榜（<10）", md)

    def test_assemble_report_includes_mode_and_metrics_ref(self):
        cfg = {
            "client_name": "邻里GEO",
            "official_url": "https://www.baicl.cc",
            "industry": "GEO",
            "area_served": "徐州",
        }
        metrics = {
            "url": "https://www.baicl.cc",
            "tech_score": 85,
            "has_ssr": True,
            "has_llms_txt": True,
            "has_json_ld": True,
            "text_density_ratio": 8.0,
            "clean_text_length": 100,
            "robots_status": "已主动配置本土 AI 爬虫规则",
            "warnings": [],
            "llm_status": "skipped",
            "is_online": True,
        }
        report = audit.assemble_report(cfg, metrics, {"available": False, "items": [], "summary": {}}, "")
        self.assertIn("85 / 100", report)
        self.assertIn("audit_metrics.json", report)
        self.assertIn("未接通大模型", report)
        self.assertIn("站点底座技术体检明细", report)

    @patch("tools.geo.audit.call_llm_api")
    @patch("tools.geo.audit.resolve_llm_runtime", create=True)
    def test_llm_ok_and_failed(self, _resolve_unused, mock_call):
        # patch generate_llm_narrative internals via call_llm_api + resolve
        cfg = {"client_name": "X", "official_url": "https://www.baicl.cc"}
        metrics = {"tech_score": 80, "url": "https://www.baicl.cc", "warnings": []}
        snap = {"available": False, "items": [], "summary": {}}

        with patch("tools.geo.llm.resolve_llm_runtime", return_value={"provider": "nextdoor"}):
            mock_call.return_value = (True, "## 一、诊断结论先行\n\n很好\n\n## 四、建议\n\n- a", "nextdoor")
            text, status, prov = audit.generate_llm_narrative(cfg, metrics, snap)
            self.assertEqual(status, "ok")
            self.assertIn("很好", text)
            self.assertEqual(prov, "nextdoor")

            mock_call.return_value = (False, "timeout", "nextdoor")
            text2, status2, _ = audit.generate_llm_narrative(cfg, metrics, snap)
            self.assertEqual(status2, "failed")
            self.assertEqual(text2, "")

        with patch("tools.geo.llm.resolve_llm_runtime", return_value=None):
            text3, status3, prov3 = audit.generate_llm_narrative(cfg, metrics, snap)
            self.assertEqual(status3, "skipped")
            self.assertEqual(prov3, "none")
            self.assertEqual(text3, "")

    @patch("tools.geo.audit.inspect_website")
    def test_crawl_then_interpret_order(self, mock_inspect):
        mock_inspect.return_value = {
            "url": "https://www.baicl.cc",
            "is_online": True,
            "status_code": 200,
            "html_size_kb": 12.0,
            "has_ssr": True,
            "has_llms_txt": True,
            "has_json_ld": True,
            "clean_text_length": 800,
            "text_density_ratio": 20.0,
            "robots_status": "已主动配置本土 AI 爬虫规则",
            "warnings": [],
        }
        with tempfile.TemporaryDirectory() as td:
            proj = os.path.join(td, "projects", "demo")
            out = os.path.join(proj, "outputs")
            os.makedirs(out, exist_ok=True)
            cfg = {
                "client_id": "demo",
                "client_name": "Demo",
                "official_url": "https://www.baicl.cc",
                "industry": "GEO",
                "keywords": ["徐州GEO"],
                "competitors": ["东昊"],
                "_project_dir": proj,
                "_outputs_dir": out,
            }
            with patch("tools.geo.audit.load_project_config", return_value=cfg):
                with self.assertRaises(ValueError):
                    audit.run_audit_interpret("demo")
                crawl = audit.run_audit_crawl("demo")
                self.assertEqual(crawl["mode"], "crawl")
                self.assertEqual(crawl["metrics"]["llm_status"], "skipped")
                with patch("tools.geo.audit.generate_llm_narrative", return_value=("## 一\n\nok\n\n## 四\n\n-x", "ok", "nextdoor")):
                    inter = audit.run_audit_interpret("demo")
                self.assertEqual(inter["llm_status"], "ok")
                m = json.loads(open(os.path.join(out, "audit_metrics.json"), encoding="utf-8").read())
                self.assertEqual(m["llm_status"], "ok")

    @patch("tools.geo.audit.inspect_website")
    @patch("tools.geo.audit.generate_llm_narrative")
    def test_run_audit_writes_metrics(self, mock_llm, mock_inspect):
        mock_inspect.return_value = {
            "url": "https://www.baicl.cc",
            "is_online": True,
            "status_code": 200,
            "html_size_kb": 12.0,
            "has_ssr": True,
            "has_llms_txt": True,
            "has_json_ld": True,
            "clean_text_length": 800,
            "text_density_ratio": 20.0,
            "robots_status": "已主动配置本土 AI 爬虫规则",
            "warnings": [],
        }
        mock_llm.return_value = ("## 一、诊断结论先行\n\nok\n\n## 四、建议\n\n- x", "ok", "nextdoor")

        with tempfile.TemporaryDirectory() as td:
            proj = os.path.join(td, "projects", "demo")
            os.makedirs(os.path.join(proj, "outputs"), exist_ok=True)
            yaml_path = os.path.join(proj, "project.yaml")
            with open(yaml_path, "w", encoding="utf-8") as f:
                f.write(
                    'client_id: "demo"\n'
                    'client_name: "Demo"\n'
                    'official_url: "https://www.baicl.cc"\n'
                    'industry: "GEO"\n'
                    'keywords: ["徐州GEO"]\n'
                    'competitors: ["东昊"]\n'
                )

            with patch("tools.geo.audit.load_project_config") as load_cfg:
                load_cfg.return_value = {
                    "client_id": "demo",
                    "client_name": "Demo",
                    "official_url": "https://www.baicl.cc",
                    "industry": "GEO",
                    "keywords": ["徐州GEO"],
                    "competitors": ["东昊"],
                    "_project_dir": proj,
                    "_outputs_dir": os.path.join(proj, "outputs"),
                }
                out = audit.run_audit("demo", mode="full")
                self.assertTrue(os.path.isfile(out))
                metrics_path = os.path.join(proj, "outputs", "audit_metrics.json")
                self.assertTrue(os.path.isfile(metrics_path))
                with open(metrics_path, encoding="utf-8") as fh:
                    m = json.load(fh)
                self.assertEqual(m["tech_score"], 100)
                self.assertEqual(m["llm_status"], "ok")
                with open(out, encoding="utf-8") as fh:
                    body = fh.read()
                self.assertIn("100 / 100", body)
                self.assertNotIn("Day 0", body)
                self.assertNotIn("未上榜（<10）", body)


if __name__ == "__main__":
    unittest.main()
