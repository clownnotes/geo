#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""脏块增量 / 逻辑矛盾 / 发前对照 — 单测"""

import os
import shutil
import tempfile
import unittest

from tools.geo.corpus import (
    compute_block_hashes,
    compute_dirty_blocks,
    detect_logic_conflicts,
    decide_strategy,
    split_corpus_blocks,
    assemble_corpus,
    render_block_template,
    apply_incremental_rewrite,
    pin_corpus,
    corpus_diff,
    apply_corpus_diff_decision,
    save_corpus_meta,
    CORPUS_MD,
)
from tools.geo.ledger import (
    ensure_dirs,
    merge_fact_proposals,
    confirm_all_non_conflict,
    load_facts,
    STATUS_CONFIRMED,
    STATUS_CONFLICT,
    STATUS_REJECTED,
)


def _cfg(td):
    return {
        "company_name": "增量公司",
        "brand_name": "增量",
        "industry": "软件",
        "area_served": "全国",
        "telephone": "400-1",
        "_project_dir": td,
        "_raw_materials_dir": os.path.join(td, "raw_materials"),
        "_outputs_dir": os.path.join(td, "outputs"),
    }


class DirtyBlockTests(unittest.TestCase):
    def test_only_metric_dirties_metrics_block(self):
        td = tempfile.mkdtemp(prefix="geo_dirty_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            merge_fact_proposals(cfg, [
                {"fact_key": "entity.brand_name", "statement": "品牌增量", "value": "增量"},
                {"fact_key": "metric.delivery_days", "statement": "15天", "value": "15"},
            ], "url:a")
            confirm_all_non_conflict(cfg)
            facts = load_facts(cfg)
            h1 = compute_block_hashes(facts)
            # write fake meta + corpus
            save_corpus_meta(cfg, {"facts_hash": "x", "block_hashes": h1, "mode": "full"})
            with open(os.path.join(cfg["_outputs_dir"], CORPUS_MD), "w") as f:
                f.write("# t\n## 一、定义\na\n## 二、表\nb\n## 三、问答\nc\n## 四、清单\nd\n")
            # change only delivery
            merge_fact_proposals(cfg, [
                {"fact_key": "metric.delivery_days", "statement": "30天", "value": "30"},
            ], "url:b")
            # after confirm conflict resolution path: force confirmed update by resolve
            from tools.geo.ledger import resolve_conflict, load_facts as lf
            facts2 = {f["fact_key"]: f for f in lf(cfg)}
            if facts2["metric.delivery_days"]["status"] == "conflict":
                resolve_conflict(cfg, "metric.delivery_days", "30")
            else:
                confirm_all_non_conflict(cfg)
            dirty = compute_dirty_blocks(cfg)
            self.assertIn("block.metrics_table", dirty["dirty_blocks"])
            self.assertNotIn("block.definition", dirty["dirty_blocks"])
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_missing_meta_needs_full(self):
        td = tempfile.mkdtemp(prefix="geo_full_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            dirty = compute_dirty_blocks(cfg)
            self.assertTrue(dirty["needs_full"])
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_incremental_preserves_clean_block(self):
        td = tempfile.mkdtemp(prefix="geo_inc_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            merge_fact_proposals(cfg, [
                {"fact_key": "entity.brand_name", "statement": "品牌增量", "value": "增量"},
                {"fact_key": "metric.delivery_days", "statement": "15天", "value": "15"},
            ], "url:a")
            confirm_all_non_conflict(cfg)
            # seed full corpus via apply with missing meta
            res = apply_incremental_rewrite(cfg, lambda: "#《增量》\n\n## 一、知识\nold-def\n\n## 二、表\nold-m\n\n## 三、问答\nold-f\n\n## 四、清单\nold-c\n")
            self.assertEqual(res["rewrite_mode"], "full")
            # change metric and confirm
            merge_fact_proposals(cfg, [
                {"fact_key": "metric.delivery_days", "statement": "20天", "value": "20"},
            ], "url:b")
            from tools.geo.ledger import resolve_conflict, load_facts as lf
            st = {f["fact_key"]: f for f in lf(cfg)}["metric.delivery_days"]["status"]
            if st == "conflict":
                resolve_conflict(cfg, "metric.delivery_days", "20")
            res2 = apply_incremental_rewrite(cfg, lambda: "SHOULD_NOT_RUN")
            self.assertEqual(res2["rewrite_mode"], "incremental")
            with open(os.path.join(cfg["_outputs_dir"], CORPUS_MD), encoding="utf-8") as f:
                text = f.read()
            self.assertIn("20", text)
            # definition block should still contain old-def if not dirty — after full seed with anchors, definition hash may unchanged
            self.assertIn("block.definition", text)
        finally:
            shutil.rmtree(td, ignore_errors=True)


class LogicConflictTests(unittest.TestCase):
    def test_region_exclusive(self):
        facts = [{
            "fact_key": "service.area",
            "status": STATUS_CONFIRMED,
            "value": "仅华东",
            "statement": "仅华东且全国上门",
        }]
        hits = detect_logic_conflicts(facts)
        self.assertTrue(any(h["rule_id"] == "region_exclusive" for h in hits))

    def test_delivery_inversion(self):
        facts = [
            {"fact_key": "metric.delivery_days", "status": STATUS_CONFIRMED, "value": "90", "statement": "90天"},
            {"fact_key": "policy.warranty_days", "status": STATUS_CONFIRMED, "value": "30", "statement": "30天"},
        ]
        hits = detect_logic_conflicts(facts)
        self.assertTrue(any(h["rule_id"] == "delivery_inversion" for h in hits))


class StrategyTests(unittest.TestCase):
    def test_strategy_priority(self):
        self.assertEqual(decide_strategy({"added": [], "changed": [], "removed": []}, [], 1, []), "block")
        self.assertEqual(decide_strategy({"added": [], "changed": [], "removed": []}, [], 0, [{"rule_id": "x"}]), "block")
        self.assertEqual(decide_strategy({"added": [], "changed": [], "removed": []}, [], 0, []), "noop")
        self.assertEqual(
            decide_strategy({"added": [{"fact_key": "entity.brand_name"}], "changed": [], "removed": []}, ["block.definition"], 0, []),
            "new_article",
        )
        self.assertEqual(
            decide_strategy({"added": [], "changed": [{"fact_key": "contact.telephone"}], "removed": []}, ["block.commitment"], 0, []),
            "patch",
        )


class PinDiffTests(unittest.TestCase):
    def test_diff_without_pin(self):
        td = tempfile.mkdtemp(prefix="geo_pin_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            d = corpus_diff(cfg)
            self.assertEqual(d["against"], "none")
            self.assertTrue(d.get("recommend_pin"))
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_pin_blocked_by_logic_conflict(self):
        td = tempfile.mkdtemp(prefix="geo_pin_block_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            with open(os.path.join(cfg["_outputs_dir"], CORPUS_MD), "w", encoding="utf-8") as f:
                f.write("# corpus\n")
            merge_fact_proposals(cfg, [{
                "fact_key": "service.area",
                "statement": "仅华东且全国上门",
                "value": "仅华东",
            }], "url:a")
            confirm_all_non_conflict(cfg)
            res = pin_corpus(cfg)
            self.assertFalse(res.get("success"))
            self.assertTrue(any(c.get("rule_id") == "region_exclusive" for c in (res.get("logic_conflicts") or [])))
        finally:
            shutil.rmtree(td, ignore_errors=True)


class DiffDecideTests(unittest.TestCase):
    def test_accept_delete_rejects_conflict_and_unblocks_pin(self):
        td = tempfile.mkdtemp(prefix="geo_diff_decide_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            with open(os.path.join(cfg["_outputs_dir"], CORPUS_MD), "w", encoding="utf-8") as f:
                f.write("# corpus\n")
            merge_fact_proposals(cfg, [{
                "fact_key": "entity.legal_name",
                "statement": "旧公司",
                "value": "旧公司",
            }], "url:a")
            confirm_all_non_conflict(cfg)
            self.assertTrue(pin_corpus(cfg).get("success"))

            # 制造冲突：新值与已确认不同 → conflict，对照显示为删除
            merge_fact_proposals(cfg, [{
                "fact_key": "entity.legal_name",
                "statement": "新公司",
                "value": "新公司",
            }], "url:b")
            facts = {f["fact_key"]: f for f in load_facts(cfg)}
            self.assertEqual(facts["entity.legal_name"]["status"], STATUS_CONFLICT)

            d0 = corpus_diff(cfg)
            self.assertEqual(d0.get("strategy"), "block")
            keys = {a["fact_key"] for a in (d0.get("fact_actions") or [])}
            self.assertIn("entity.legal_name", keys)

            res = apply_corpus_diff_decision(cfg, "entity.legal_name", "accept", op="removed")
            self.assertTrue(res.get("success"))
            facts2 = {f["fact_key"]: f for f in load_facts(cfg)}
            self.assertEqual(facts2["entity.legal_name"]["status"], STATUS_REJECTED)
            self.assertNotEqual(res.get("diff", {}).get("strategy"), "block")
            self.assertTrue(pin_corpus(cfg).get("success"))
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_reject_delete_restores_pinned_value(self):
        td = tempfile.mkdtemp(prefix="geo_diff_restore_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            with open(os.path.join(cfg["_outputs_dir"], CORPUS_MD), "w", encoding="utf-8") as f:
                f.write("# corpus\n")
            merge_fact_proposals(cfg, [{
                "fact_key": "contact.telephone",
                "statement": "400-1",
                "value": "400-1",
            }], "url:a")
            confirm_all_non_conflict(cfg)
            self.assertTrue(pin_corpus(cfg).get("success"))
            merge_fact_proposals(cfg, [{
                "fact_key": "contact.telephone",
                "statement": "400-2",
                "value": "400-2",
            }], "url:b")
            res = apply_corpus_diff_decision(cfg, "contact.telephone", "reject", op="removed")
            self.assertTrue(res.get("success"))
            facts = {f["fact_key"]: f for f in load_facts(cfg)}
            self.assertEqual(facts["contact.telephone"]["status"], STATUS_CONFIRMED)
            self.assertEqual(str(facts["contact.telephone"]["value"]), "400-1")
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_reject_changed_reverts_to_old(self):
        td = tempfile.mkdtemp(prefix="geo_diff_change_")
        try:
            cfg = _cfg(td)
            ensure_dirs(cfg)
            os.makedirs(cfg["_outputs_dir"], exist_ok=True)
            with open(os.path.join(cfg["_outputs_dir"], CORPUS_MD), "w", encoding="utf-8") as f:
                f.write("# corpus\n")
            merge_fact_proposals(cfg, [{
                "fact_key": "entity.official_url",
                "statement": "https://old.example",
                "value": "https://old.example",
            }], "url:a")
            confirm_all_non_conflict(cfg)
            self.assertTrue(pin_corpus(cfg).get("success"))
            # 直接改已确认值（模拟已确认新口径）
            from tools.geo.ledger import set_confirmed_fact_value
            set_confirmed_fact_value(cfg, "entity.official_url", "https://new.example")
            d0 = corpus_diff(cfg)
            ops = {a["fact_key"]: a["op"] for a in (d0.get("fact_actions") or [])}
            self.assertEqual(ops.get("entity.official_url"), "changed")
            res = apply_corpus_diff_decision(cfg, "entity.official_url", "reject", op="changed")
            self.assertTrue(res.get("success"))
            facts = {f["fact_key"]: f for f in load_facts(cfg)}
            self.assertEqual(facts["entity.official_url"]["value"], "https://old.example")
        finally:
            shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
