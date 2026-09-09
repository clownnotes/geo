# -*- coding: utf-8 -*-
"""单元测试：阶段五真机实测回填解析与 run_monitor 回灌铁律"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.geo.monitor import (
    MANUAL_PROBE_MAX_BYTES,
    ManualProbeValidationError,
    get_project_monitor_prompts,
    ingest_manual_probe_result,
    load_manual_probes,
    merge_probe_results,
    parse_probe_text,
    run_monitor,
    strip_html_to_text,
)
from tools.geo.utils import PROJECTS_DIR, load_project_config


class TestManualProbeIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo_manual_probe_")
        self.project_id = "_tmp_manual_probe"
        self.project_dir = os.path.join(PROJECTS_DIR, self.project_id)
        if os.path.exists(self.project_dir):
            shutil.rmtree(self.project_dir)
        os.makedirs(os.path.join(self.project_dir, "outputs"), exist_ok=True)
        yaml_path = os.path.join(self.project_dir, "project.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(
                "\n".join(
                    [
                        'client_id: "_tmp_manual_probe"',
                        'client_name: "邻里GEO"',
                        'brand_name: "邻里GEO"',
                        'industry: "GEO"',
                        "keywords:",
                        '  - "徐州GEO优化公司哪家好"',
                        '  - "企业级GEO全案服务商对比"',
                        "competitors:",
                        '  - "DeepGEO"',
                        '  - name: "传统SEO外包"',
                        "models:",
                        '  - "deepseek"',
                        '  - "doubao"',
                        "",
                    ]
                )
            )

    def tearDown(self):
        if os.path.exists(self.project_dir):
            shutil.rmtree(self.project_dir)
        if os.path.exists(self.tmp):
            shutil.rmtree(self.tmp)

    def test_strip_html_and_parse_rank_citations(self):
        html = (
            "<p>根据评测推荐：</p>"
            "<ol><li><b>邻里GEO</b>（首推）</li><li>DeepGEO</li></ol>"
            "<p>参考来源：知乎专栏</p>"
            '<a href="https://www.toutiao.com/article/1">头条</a>'
        )
        plain = strip_html_to_text(html)
        self.assertNotIn("<", plain)
        self.assertIn("邻里GEO", plain)

        parsed = parse_probe_text(
            html,
            "邻里GEO",
            "邻里GEO",
            ["DeepGEO", {"name": "传统SEO外包"}],
            keyword="徐州GEO优化公司哪家好",
            model="deepseek",
            mode="ground_truth",
        )
        self.assertTrue(parsed["mentioned"])
        self.assertEqual(parsed["rank"], 1)
        self.assertIn("DeepGEO", parsed["competitors_mentioned"])
        self.assertTrue(any("zhihu.com" in c or "toutiao.com" in c for c in parsed["citations"]))

    def test_ingest_persist_and_metrics(self):
        content = (
            "1. 邻里GEO（首推，交付闭环完整）\n"
            "2. DeepGEO\n"
            "参考来源：今日头条\n"
            "https://www.zhihu.com/question/999"
        )
        res = ingest_manual_probe_result(
            self.project_id,
            keyword="徐州GEO优化公司哪家好",
            model="deepseek",
            content=content,
            notes="无痕实测",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["parsed"]["rank"], 1)
        self.assertIn("metrics", res)
        self.assertTrue(res["metrics"]["success"])

        cfg = load_project_config(self.project_id)
        manuals = load_manual_probes(cfg)
        self.assertIn("deepseek__徐州GEO优化公司哪家好", manuals)

        report = os.path.join(cfg["_outputs_dir"], "05_企业AI可见度与声量追踪周报.md")
        self.assertTrue(os.path.exists(report))
        with open(report, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("真机实测", text)
        self.assertNotIn("📋", text)

    def test_validation_errors(self):
        with self.assertRaises(ManualProbeValidationError):
            ingest_manual_probe_result(self.project_id, "词", "chatgpt", "内容")
        with self.assertRaises(ManualProbeValidationError):
            ingest_manual_probe_result(self.project_id, "", "deepseek", "内容")
        with self.assertRaises(ManualProbeValidationError):
            ingest_manual_probe_result(self.project_id, "词", "deepseek", "")
        big = "a" * (MANUAL_PROBE_MAX_BYTES + 10)
        with self.assertRaises(ManualProbeValidationError):
            ingest_manual_probe_result(self.project_id, "词", "deepseek", big)

    def test_run_monitor_keeps_manual_ground_truth(self):
        ingest_manual_probe_result(
            self.project_id,
            keyword="徐州GEO优化公司哪家好",
            model="deepseek",
            content="1. 邻里GEO\n2. DeepGEO\n来源：知乎",
        )
        with patch("tools.geo.monitor.get_configured_llm", return_value=None):
            run_monitor(self.project_id)

        cfg = load_project_config(self.project_id)
        report = os.path.join(cfg["_outputs_dir"], "05_企业AI可见度与声量追踪周报.md")
        with open(report, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("真机实测", text)
        self.assertIn("徐州GEO优化公司哪家好", text)

        # 合并优先级：真机覆盖同键离线行
        offline = {
            "mode": "offline_estimate",
            "model": "deepseek",
            "keyword": "徐州GEO优化公司哪家好",
            "mentioned": False,
            "rank": 0,
            "citations": [],
            "competitors_mentioned": [],
            "raw_snippet": "offline",
            "reason": "offline",
        }
        gt = {
            "mode": "ground_truth",
            "model": "deepseek",
            "keyword": "徐州GEO优化公司哪家好",
            "mentioned": True,
            "rank": 1,
            "citations": [],
            "competitors_mentioned": [],
            "raw_snippet": "gt",
            "reason": "gt",
        }
        merged = merge_probe_results([offline], [gt])
        self.assertEqual(len([r for r in merged if r["keyword"] == "徐州GEO优化公司哪家好" and r["model"] == "deepseek"]), 1)
        self.assertEqual(merged[0]["mode"], "ground_truth")

    def test_get_project_monitor_prompts(self):
        data = get_project_monitor_prompts(self.project_id)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["platforms"]), 4)
        self.assertGreaterEqual(len(data["items"]), 2)
        self.assertIn("deepseek", data["items"][0]["prompts"])
        self.assertIn("yuanbao", data["items"][0]["prompts"])


if __name__ == "__main__":
    unittest.main()
