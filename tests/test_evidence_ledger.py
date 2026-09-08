#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""素材证据库与唯一真相源 — 单元/集成验证"""

import os
import shutil
import tempfile
import unittest

from tools.geo.ledger import (
    normalize_fact_key,
    source_id_for_url,
    upsert_evidence,
    merge_fact_proposals,
    load_facts,
    list_evidence,
    confirm_all_non_conflict,
    resolve_conflict,
    get_rewrite_fact_bundle,
    raw_paths,
    ensure_dirs,
)
from tools.geo.ingest import ingest_project_materials


class LedgerKeyTests(unittest.TestCase):
    def test_alias_normalize_delivery(self):
        self.assertEqual(normalize_fact_key("delivery_time"), "metric.delivery_days")
        self.assertEqual(normalize_fact_key("delivery_cycle_days"), "metric.delivery_days")
        self.assertEqual(normalize_fact_key("metric.delivery_days"), "metric.delivery_days")

    def test_cjk_and_empty_bare_use_hash_key(self):
        """Antigravity 修复：无 ASCII 裸名不得落到 custom. 空点。"""
        k1 = normalize_fact_key("交付周期")
        self.assertTrue(k1.startswith("custom.fact_"), k1)
        self.assertNotEqual(k1, "custom.")
        k2 = normalize_fact_key("...")
        self.assertTrue(k2.startswith("custom.fact_"), k2)
        self.assertEqual(normalize_fact_key(""), "custom.unknown")

    def test_alias_conflict_detection(self):
        td = tempfile.mkdtemp(prefix="geo_ledger_")
        try:
            cfg = {
                "company_name": "测试公司",
                "brand_name": "测品",
                "_project_dir": td,
                "_raw_materials_dir": os.path.join(td, "raw_materials"),
            }
            ensure_dirs(cfg)
            merge_fact_proposals(cfg, [{
                "fact_key": "delivery_time",
                "statement": "交付 15 天",
                "value": "15",
            }], source_id="url:a")
            confirm_all_non_conflict(cfg)
            merge_fact_proposals(cfg, [{
                "fact_key": "delivery_cycle_days",
                "statement": "交付 30 天",
                "value": "30",
            }], source_id="url:b")
            facts = {f["fact_key"]: f for f in load_facts(cfg)}
            self.assertIn("metric.delivery_days", facts)
            self.assertEqual(facts["metric.delivery_days"]["status"], "conflict")
            bundle = get_rewrite_fact_bundle(cfg)
            # 冲突时应沿用历史 15，不得采用 30
            used = {f["fact_key"]: f for f in bundle["facts"]}
            self.assertEqual(str(used["metric.delivery_days"]["value"]), "15")
        finally:
            shutil.rmtree(td, ignore_errors=True)


class ReadRawMaterialsCfgTests(unittest.TestCase):
    def test_temp_dir_without_cfg_no_project_lookup_crash(self):
        """显式无 cfg 时，临时目录不得因反推 project_id 抛错。"""
        from tools.geo.rewrite import read_raw_materials
        td = tempfile.mkdtemp(prefix="geo_raw_")
        try:
            with open(os.path.join(td, "raw_extracted_facts.md"), "w", encoding="utf-8") as f:
                f.write("# facts\n- a\n")
            text = read_raw_materials(td, budget=150, cfg=None)
            self.assertIn("facts", text)
        finally:
            shutil.rmtree(td, ignore_errors=True)


class EvidenceVaultTests(unittest.TestCase):
    def test_two_urls_two_evidence_files(self):
        td = tempfile.mkdtemp(prefix="geo_ev_")
        try:
            cfg = {
                "company_name": "双页公司",
                "brand_name": "双页",
                "official_url": "https://example.com/",
                "_project_dir": td,
                "_raw_materials_dir": os.path.join(td, "raw_materials"),
            }
            ensure_dirs(cfg)
            s1 = source_id_for_url("https://example.com/")
            s2 = source_id_for_url("https://example.com/about")
            self.assertNotEqual(s1, s2)
            upsert_evidence(cfg, s1, "# Home\nA", kind="url", url="https://example.com/")
            upsert_evidence(cfg, s2, "# About\nB", kind="url", url="https://example.com/about")
            ev = list_evidence(cfg)
            self.assertEqual(len(ev), 2)
            paths = raw_paths(cfg)
            # re-upsert same url overwrites count still 2
            upsert_evidence(cfg, s1, "# Home2\nA2", kind="url", url="https://example.com/")
            self.assertEqual(len(list_evidence(cfg)), 2)
            self.assertTrue(os.path.isdir(paths["evidence_dir"]))
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_compat_mirror_written(self):
        td = tempfile.mkdtemp(prefix="geo_mirror_")
        try:
            cfg = {
                "company_name": "镜像公司",
                "brand_name": "镜像",
                "_project_dir": td,
                "_raw_materials_dir": os.path.join(td, "raw_materials"),
            }
            ensure_dirs(cfg)
            merge_fact_proposals(cfg, [{
                "fact_key": "entity.brand_name",
                "statement": "品牌为镜像",
                "value": "镜像",
            }], source_id="paste:t")
            paths = raw_paths(cfg)
            self.assertTrue(os.path.isfile(paths["facts_jsonl"]))
            self.assertTrue(os.path.isfile(paths["facts_md"]))
            self.assertTrue(os.path.isfile(paths["compat_md"]))
            with open(paths["facts_md"], encoding="utf-8") as f:
                md1 = f.read()
            with open(paths["compat_md"], encoding="utf-8") as f:
                md2 = f.read()
            self.assertEqual(md1, md2)
        finally:
            shutil.rmtree(td, ignore_errors=True)


class IngestTextIntegrationTests(unittest.TestCase):
    def test_ingest_text_creates_evidence_and_ledger(self):
        # 使用真实项目目录结构：projects/<id>/
        root = tempfile.mkdtemp(prefix="geo_proj_root_")
        pid = "tmp_ledger_demo"
        proj = os.path.join(root, pid)
        os.makedirs(os.path.join(proj, "raw_materials"), exist_ok=True)
        os.makedirs(os.path.join(proj, "outputs"), exist_ok=True)
        yaml_path = os.path.join(proj, "project.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(
                "client_id: tmp_ledger_demo\n"
                "company_name: 提纯演示公司\n"
                "brand_name: 提纯演示\n"
                "industry: 软件服务\n"
                "official_url: https://demo.example.com\n"
                "area_served: 全国\n"
                "telephone: 400-000-0000\n"
                "founder: 张三\n"
            )
        try:
            # monkeypatch PROJECTS_DIR via writing under tools path is hard;
            # call ledger APIs directly to validate ingest helpers
            from tools.geo import utils as geo_utils
            old = geo_utils.PROJECTS_DIR
            geo_utils.PROJECTS_DIR = root
            try:
                res = ingest_project_materials(
                    pid,
                    raw_text="我们交付周期 15 天，质保 365 天，支持源码交付。联系电话 13800138000。",
                    filename="product_supplement.md",
                )
                self.assertTrue(res.get("success"))
                self.assertIn("merge", res)
                cfg = geo_utils.load_project_config(pid)
                self.assertGreaterEqual(len(list_evidence(cfg)), 1)
                self.assertTrue(os.path.isfile(os.path.join(cfg["_raw_materials_dir"], "raw_extracted_facts.md")))
                self.assertTrue(os.path.isfile(os.path.join(cfg["_raw_materials_dir"], "ledger", "facts.jsonl")))
            finally:
                geo_utils.PROJECTS_DIR = old
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
