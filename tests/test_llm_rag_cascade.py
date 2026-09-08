# -*- coding: utf-8 -*-
"""阶段三 LLM 中枢与 RAG 级联回归测试。"""

import json
import os
import tempfile
import unittest
from unittest import mock

from tools.geo import llm as llm_mod
from tools.geo.llm import (
    mask_api_key,
    build_llm_status_payload,
    resolve_llm_runtime,
    save_llm_config,
    clear_status_cache,
    load_dotenv,
    atomic_write_env,
)
from tools.geo.rewrite import map_rag_api_fields, read_raw_materials, run_rewrite
from tools.geo.rag_diag import diagnose_rag_chunks
from tools.geo.utils import get_configured_llm, PROJECTS_DIR


class TestLlmRuntime(unittest.TestCase):
    def setUp(self):
        clear_status_cache()
        self._env_backup = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        clear_status_cache()

    def test_mask_short_key(self):
        self.assertEqual(mask_api_key("abc"), "***")
        self.assertTrue(mask_api_key("sk-abcdefghij").endswith("ghij"))

    def test_write_whitelist_rejects_foreign_keys(self):
        """白名单外的环境变量一律拒绝写入 .env，防任意键注入。"""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                atomic_write_env({"EVIL_KEY": "x"}, path=os.path.join(tmp, ".env"))

    def test_status_whitelist_no_plaintext_key(self):
        os.environ["GEO_LLM_DIRECT"] = "1"
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key-abcdef"
        os.environ["DEEPSEEK_MODEL"] = "deepseek-chat"
        with mock.patch("tools.geo.llm.ping_llm", return_value=("ready", 12)):
            payload = build_llm_status_payload(force_refresh=True)
        self.assertNotIn("api_key", payload)
        self.assertIn("api_key_masked", payload)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["provider"], "deepseek")

    def test_web_write_key_visible_to_utils(self):
        """DIRECT 模式下 DEEPSEEK_API_KEY 两侧同见。"""
        for k in list(os.environ.keys()):
            if "DEEPSEEK" in k or "ARK" in k or "DOUBAO" in k or "GEO_LLM" in k or "OPENAI" in k or "NEXTDOOR" in k:
                os.environ.pop(k, None)
        os.environ["GEO_LLM_DIRECT"] = "1"
        os.environ["DEEPSEEK_API_KEY"] = "sk-shared-key-12345678"
        rt = resolve_llm_runtime()
        util = get_configured_llm()
        self.assertIsNotNone(rt)
        self.assertIsNotNone(util)
        self.assertEqual(rt["api_key"], util["api_key"])
        self.assertEqual(rt["provider"], util["provider"])

    def test_fake_key_does_not_write_env(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            with open(env_path, "w") as f:
                f.write("# empty\n")
            with mock.patch("tools.geo.llm.ENV_PATH", env_path), \
                 mock.patch("tools.geo.llm.ping_llm", return_value=("auth_failed", 5)), \
                 mock.patch("tools.geo.llm.ensure_env_file", return_value=env_path):
                res = save_llm_config({
                    "provider": "deepseek",
                    "api_key": "sk-fake-bad-key",
                    "force_direct": True,
                })
            self.assertFalse(res["success"])
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("sk-fake-bad-key", content)

    def test_config_success_clears_ttl(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            open(env_path, "w").close()
            with mock.patch("tools.geo.llm.ENV_PATH", env_path), \
                 mock.patch("tools.geo.llm.ping_llm", return_value=("ready", 8)), \
                 mock.patch("tools.geo.llm.ensure_env_file", return_value=env_path), \
                 mock.patch("tools.geo.llm.atomic_write_env") as aw:
                aw.side_effect = lambda updates, path=None: atomic_write_env(updates, env_path)
                # seed cache
                llm_mod._STATUS_CACHE["payload"] = {"configured": False, "status": "offline"}
                llm_mod._STATUS_CACHE["ts"] = 9999999999
                res = save_llm_config({
                    "provider": "deepseek",
                    "api_key": "sk-good-key-abcdefg",
                    "force_direct": True,
                })
            self.assertTrue(res["success"])
            self.assertIsNone(llm_mod._STATUS_CACHE["payload"])

    def test_dotenv_override(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            with open(env_path, "w") as f:
                f.write("DEEPSEEK_API_KEY=from-dotenv-key-xxxx\n")
            os.environ["DEEPSEEK_API_KEY"] = "from-os-old"
            llm_mod._DOTENV_KEYS.clear()
            llm_mod._ENV_LOADED = False
            load_dotenv(env_path, override=True)
            self.assertEqual(os.environ["DEEPSEEK_API_KEY"], "from-dotenv-key-xxxx")


class TestRagCascade(unittest.TestCase):
    def test_map_rag_fields_drops_chunks(self):
        mapped = map_rag_api_fields({
            "success": True,
            "rag_readiness_score": 88.5,
            "total_chunks": 10,
            "golden_chunks_count": 7,
            "entity_coverage_pct": 90.0,
            "chunks": [{"text": "huge"}] * 100,
        })
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["score"], 88.5)
        self.assertEqual(mapped["golden_chunks"], 7)
        self.assertNotIn("chunks", mapped)

    def test_crawler_simulation_backfill(self):
        pid = "nextgeo"
        out_dir = os.path.join(PROJECTS_DIR, pid, "outputs")
        if not os.path.isdir(out_dir):
            self.skipTest("nextgeo outputs 不存在")
        json_path = os.path.join(out_dir, "rag_chunks_diagnostic.json")
        mother = os.path.join(out_dir, "03_普林斯顿9因子高权威语料库.md")
        if not os.path.exists(mother):
            self.skipTest("母盘不存在")

        fake_crawl = {"success": True, "spider_type": "bytespider", "http_status": 200, "elapsed_ms": 12, "token_estimate": 500, "jsonld_count": 1, "url": "https://example.com", "llms_txt": {"exists": True}, "warnings": []}
        prev = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                prev = json.load(f)
        try:
            seed = {
                "success": True,
                "analyzed_at": "2026-01-01 12:00:00",
                "crawler_simulation": fake_crawl,
                "rag_readiness_score": 1,
                "chunks": [],
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(seed, f)
            diag = diagnose_rag_chunks(pid, text_or_file=mother, run_crawler=False)
            self.assertIsNotNone(diag.get("crawler_simulation"))
            self.assertEqual(diag["crawler_simulation"]["spider_type"], "bytespider")
            self.assertEqual(diag.get("crawler_simulation_reused_from"), "2026-01-01 12:00:00")
        finally:
            if prev:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(prev, f, ensure_ascii=False, indent=2)

    def test_raw_materials_budget(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "raw_extracted_facts.md"), "w") as f:
                f.write("A" * 100)
            with open(os.path.join(td, "website_crawled_raw.md"), "w") as f:
                f.write("B" * 100)
            with open(os.path.join(td, "other.md"), "w") as f:
                f.write("C" * 100)
            text = read_raw_materials(td, budget=150)
            self.assertLessEqual(len(text.replace("<!-- 来源文件:", "").split("-->")[0]) + 150, 500)
            self.assertIn("A", text)
            self.assertTrue(len(text) <= 150 + 200)  # headers overhead


class TestRewriteFallback(unittest.TestCase):
    def test_rewrite_without_key_cascades(self):
        pid = "nextgeo"
        if not os.path.isdir(os.path.join(PROJECTS_DIR, pid)):
            self.skipTest("nextgeo 不存在")
        # 清除 Key 强制 Fallback
        keys = [k for k in os.environ if any(x in k for x in ("DEEPSEEK", "ARK", "DOUBAO", "GEO_LLM", "OPENAI", "GEO_DEEPSEEK", "GEO_DOUBAO"))]
        backup = {k: os.environ[k] for k in keys}
        for k in keys:
            del os.environ[k]
        llm_mod._ENV_LOADED = True
        clear_status_cache()
        try:
            with mock.patch("tools.geo.llm.resolve_llm_runtime", return_value=None):
                res = run_rewrite(pid, mode="full")
            self.assertTrue(res["success"])
            self.assertEqual(res["mode"], "fallback")
            self.assertIn("rag", res)
            self.assertTrue(os.path.exists(res["path"]))
        finally:
            os.environ.update(backup)


if __name__ == "__main__":
    unittest.main()
