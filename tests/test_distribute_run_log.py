# -*- coding: utf-8 -*-
import json
import os
import unittest

from tools.geo.distribute import (
    DistributeRunTracker,
    get_latest_distribute_run_log,
    enrich_distribute_run_log_packs,
    _redact_runtime,
    DISTRIBUTE_RUN_LOG_FILENAME,
)
from tools.geo.utils import load_project_config


class TestDistributeRunLog(unittest.TestCase):
    project_id = "demo_corp"

    def test_tracker_save_and_load(self):
        cfg = load_project_config(self.project_id)
        tr = DistributeRunTracker(self.project_id)
        tr.record_llm_call(
            channel="toutiao",
            name="今日头条专版生成",
            duration_ms=42,
            status="success",
            prompt_system="sys",
            prompt_user="Bearer eyJhbGciOi.fake.token should scrub",
            raw_output="# ok",
        )
        out_dir = cfg["_outputs_dir"]
        sample = os.path.join(out_dir, "dist_channels_checklist.md")
        if not os.path.isfile(sample):
            with open(sample, "w", encoding="utf-8") as f:
                f.write("checklist")
        tr.record_artifact(out_dir, "dist_channels_checklist.md", "执行清单")
        path = tr.save()
        self.assertTrue(path and os.path.isfile(path))
        with open(path, encoding="utf-8") as f:
            log = json.load(f)
        self.assertTrue(log["run_id"].startswith("dist_run_"))
        self.assertEqual(log["llm_calls"][0]["duration_ms"], 42)
        blob = json.dumps(log)
        self.assertNotIn("eyJhbGciOi.fake.token", blob)
        self.assertIn("[REDACTED]", blob)
        enrich_distribute_run_log_packs(self.project_id, packs_ok=False)
        res = get_latest_distribute_run_log(self.project_id)
        self.assertTrue(res["success"] and res["has_log"])
        self.assertEqual(res["log"]["run_id"], log["run_id"])

    def test_redact_runtime_no_full_url(self):
        rt = _redact_runtime({
            "provider": "nextdoor",
            "brand": "geo",
            "mode": "flash",
            "base_url": "http://10.0.0.8:3002",
            "api_key": "secret-jwt",
        })
        self.assertEqual(rt["base_url_host"], "***")
        self.assertNotIn("api_key", rt)
        self.assertEqual(rt["endpoint"], "/api/v1/xiulan/chat")


if __name__ == "__main__":
    unittest.main()
