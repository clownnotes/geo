# -*- coding: utf-8 -*-
"""新建空壳建档、probe_* profile、侦察回填 CLI 回归。"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.geo import utils as utils_mod
from tools.geo.probe_backfill import (
    apply_probe_backfill,
    build_probe_script,
    preview_probe_backfill,
)
from tools.geo.utils import (
    load_project_config,
    normalize_official_url,
    parse_simple_yaml,
    update_project_profile,
    validate_business_one_liner,
)


SAMPLE_PROBE = {
    "probed_at": "2026-09-10T19:35:00+08:00",
    "model_ui": "doubao",
    "summary": {
        "primary_local_competitor": "徐州东昊信息科技 (xzdonghao.com)",
        "founder_status": "被幻觉匹配为安徽广德短视频外包",
    },
    "items": [
        {
            "query": "徐州GEO优化公司哪家好",
            "mentioned_self": False,
            "url_present": False,
            "competitors_extracted": [
                {"name": "徐州东昊信息科技有限公司", "url": "www.xzdonghao.com", "is_real": True},
                {"name": "竞品A", "url": "", "is_real": True},
                {"name": "待核实公司", "url": "", "is_real": False},
            ],
        },
        {
            "query": "邻里GEO是做什么的",
            "mentioned_self": False,
            "url_present": False,
            "hallucination_detected": True,
            "competitors_extracted": [],
        },
    ],
}


class TestProbeBackfill(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo_probe_bf_")
        self.projects_dir = os.path.join(self.tmp, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        self._patch = patch.object(utils_mod, "PROJECTS_DIR", self.projects_dir)
        self._patch.start()
        self.pid = "shell_corp"
        p_dir = os.path.join(self.projects_dir, self.pid)
        os.makedirs(os.path.join(p_dir, "outputs"), exist_ok=True)
        os.makedirs(os.path.join(p_dir, "raw_materials"), exist_ok=True)
        yaml_text = """client_id: "shell_corp"
client_name: "徐州壳公司测试"
brand_name: "邻里GEO"
company_name: "徐州璇源网络科技有限公司"
industry: "企业GEO与AI搜索品牌答案源建设"
official_url: "https://nextgeo.baicl.cc"
area_served: "徐州本地"
contact_person: "老白"
keywords:
competitors:
probe_status: "unprobed"
probe_baseline_id: ""
probe_baseline_at: ""
"""
        with open(os.path.join(p_dir, "project.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_text)
        self.probe_path = os.path.join(self.tmp, "probe_doubao_20260910.json")
        with open(self.probe_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_PROBE, f, ensure_ascii=False)

    def tearDown(self):
        self._patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_lists_parse(self):
        cfg = load_project_config(self.pid)
        self.assertEqual(cfg.get("keywords"), [])
        self.assertEqual(cfg.get("competitors"), [])
        self.assertEqual(cfg.get("probe_status"), "unprobed")

    def test_create_yaml_no_fake_placeholders(self):
        """模拟 server 空壳写入：不应出现假词/假竞品。"""
        e = lambda s: s.replace('"', '\\"')
        kw_list, comp_list = [], []
        yaml_content = 'client_id: "x"\nkeywords:\n'
        for kw in (kw_list or []):
            yaml_content += f'  - "{e(kw)}"\n'
        yaml_content += "competitors:\n"
        for comp in (comp_list or []):
            yaml_content += f'  - "{e(comp)}"\n'
        yaml_content += 'probe_status: "unprobed"\n'
        data = parse_simple_yaml(yaml_content)
        self.assertEqual(data.get("keywords"), [])
        self.assertEqual(data.get("competitors"), [])
        self.assertNotIn("竞品A", str(data))
        self.assertNotIn("行业核心推荐词", str(data))

    def test_profile_probe_scalars(self):
        updated = update_project_profile(
            self.pid,
            {
                "probe_status": "awaiting_retest",
                "probe_baseline_id": "probe:doubao:20260910",
                "probe_baseline_at": "2026-09-10",
            },
        )
        self.assertEqual(updated.get("probe_status"), "awaiting_retest")
        self.assertEqual(updated.get("probe_baseline_id"), "probe:doubao:20260910")
        self.assertEqual(updated.get("probe_baseline_at"), "2026-09-10")

    def test_probe_script_range(self):
        payload = build_probe_script(self.pid)
        n = len(payload.get("items") or [])
        self.assertGreaterEqual(n, 6)
        self.assertLessEqual(n, 10)
        self.assertTrue(os.path.isfile(payload["output_path"]))
        # 首轮问句不应硬编码某竞品对打
        blob = " ".join(it["query"] for it in payload["items"])
        self.assertNotIn("东昊", blob)

    def test_preview_and_apply(self):
        prev = preview_probe_backfill(self.pid, self.probe_path)
        self.assertEqual(prev["source_probe"], "probe:doubao:20260910")
        names = [c["name"] for c in prev["competitor_candidates"]]
        self.assertIn("徐州东昊信息科技有限公司", names)
        self.assertNotIn("竞品A", names)
        self.assertTrue(any("徐州GEO" in q for q in prev["suggested_keywords"]))

        res = apply_probe_backfill(self.pid, self.probe_path, only_real=True)
        self.assertTrue(res["success"])
        cfg = load_project_config(self.pid)
        self.assertEqual(cfg.get("probe_status"), "baseline_ready")
        self.assertEqual(cfg.get("probe_baseline_id"), "probe:doubao:20260910")
        self.assertIn("徐州东昊信息科技有限公司", cfg.get("competitors") or [])
        self.assertNotIn("竞品A", cfg.get("competitors") or [])
        self.assertGreaterEqual(len(cfg.get("keywords") or []), 1)

    def test_apply_merge_keeps_existing_keywords(self):
        update_project_profile(
            self.pid,
            {
                "keywords": ["已有精修问句A", "徐州GEO优化公司哪家好"],
                "competitors": ["已有竞品X"],
            },
        )
        res = apply_probe_backfill(self.pid, self.probe_path, only_real=True, merge=True)
        self.assertTrue(res.get("merge"))
        cfg = load_project_config(self.pid)
        kws = cfg.get("keywords") or []
        comps = cfg.get("competitors") or []
        self.assertIn("已有精修问句A", kws)
        self.assertIn("徐州GEO优化公司哪家好", kws)
        self.assertIn("邻里GEO是做什么的", kws)
        self.assertIn("已有竞品X", comps)
        self.assertIn("徐州东昊信息科技有限公司", comps)

    def test_preview_from_probe_data(self):
        with open(self.probe_path, encoding="utf-8") as f:
            data = json.load(f)
        prev = preview_probe_backfill(self.pid, probe_data=data)
        self.assertEqual(prev["source_probe"], "probe:doubao:20260910")
        self.assertTrue(prev["suggested_keywords"])

    def test_normalize_official_url(self):
        url, pending = normalize_official_url("pidai.baicl.cc", client_id="pidai", site_pending=False)
        self.assertEqual(url, "https://pidai.baicl.cc")
        self.assertFalse(pending)
        url2, pending2 = normalize_official_url("", client_id="belt_scale", site_pending=True)
        self.assertEqual(url2, "https://belt_scale.baicl.cc")
        self.assertTrue(pending2)
        with self.assertRaises(ValueError):
            normalize_official_url("", client_id="x", site_pending=False)

    def test_business_one_liner_length(self):
        ok = validate_business_one_liner("徐州及周边高精度电子皮带秤研发生产与矿山电力行业技术服务")
        self.assertGreaterEqual(len(ok), 15)
        with self.assertRaises(ValueError):
            validate_business_one_liner("太短了")
        with self.assertRaises(ValueError):
            validate_business_one_liner("字" * 81)

    def test_site_pending_skips_url_question(self):
        update_project_profile(
            self.pid,
            {
                "site_pending": True,
                "business_one_liner": "徐州高精度电子皮带秤研发生产与矿山电力行业现场技术服务",
                "official_url": "https://shell_corp.baicl.cc",
            },
        )
        payload = build_probe_script(self.pid)
        self.assertTrue(payload.get("site_pending"))
        dims = [it.get("dimension") for it in payload["items"]]
        self.assertNotIn("URL", dims)
        blob = " ".join(it["query"] for it in payload["items"])
        self.assertNotIn("官网是什么", blob)
        self.assertGreaterEqual(len(payload["items"]), 6)


if __name__ == "__main__":
    unittest.main()
