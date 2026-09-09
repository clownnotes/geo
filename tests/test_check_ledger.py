# -*- coding: utf-8 -*-
"""运维检测台账：逾期判定与 UTC 边界回归。"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from tools.geo import check_ledger as cl


class TestCheckLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo_check_ledger_")
        self.log = os.path.join(self.tmp, "ops_check_logs.jsonl")
        self.projects = os.path.join(self.tmp, "projects")
        os.makedirs(self.projects, exist_ok=True)
        self._p_log = patch.object(cl, "LOG_FILE", self.log)
        self._p_data = patch.object(cl, "DATA_DIR", self.tmp)
        self._p_proj = patch.object(cl, "PROJECTS_DIR", self.projects)
        self._p_log.start()
        self._p_data.start()
        self._p_proj.start()

    def tearDown(self):
        self._p_log.stop()
        self._p_data.stop()
        self._p_proj.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mk_project(self, pid, name):
        d = os.path.join(self.projects, pid)
        os.makedirs(os.path.join(d, "outputs"), exist_ok=True)
        with open(os.path.join(d, "project.yaml"), "w", encoding="utf-8") as f:
            f.write(f'client_id: "{pid}"\nclient_name: "{name}"\nindustry: "测试"\n')

    def test_never_without_manual(self):
        self._mk_project("p_never", "从未测")
        with patch.object(cl, "load_project_config") as mock_cfg, patch.object(
            cl, "load_notification_settings", return_value={"warn_days": 7, "overdue_days": 14, "min_manual_keywords": 1}
        ):
            mock_cfg.side_effect = lambda pid: {
                "_project_dir": os.path.join(self.projects, pid),
                "_outputs_dir": os.path.join(self.projects, pid, "outputs"),
                "client_name": "从未测",
            }
            ledger = cl.build_check_ledger()
        self.assertEqual(ledger["rows"][0]["status"], "never")
        self.assertEqual(ledger["summary"]["never"], 1)

    def test_overdue_and_ok_and_sort_never_first(self):
        self._mk_project("p_old", "旧客户")
        self._mk_project("p_new", "新客户")
        self._mk_project("p_none", "空客户")
        now = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)
        old_at = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh_at = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cl.append_check_log(project_id="p_old", mode="manual_probe", keywords=["词A"], sov_pct=40, at=old_at)
        cl.append_check_log(project_id="p_new", mode="manual_probe", keywords=["词B"], sov_pct=70, at=fresh_at)
        # API 不清逾期
        cl.append_check_log(project_id="p_none", mode="api_patrol", keywords=[], sov_pct=10, at=fresh_at)

        with patch.object(cl, "load_project_config") as mock_cfg, patch.object(
            cl, "load_notification_settings",
            return_value={"warn_days": 7, "overdue_days": 14, "min_manual_keywords": 1},
        ):
            mock_cfg.side_effect = lambda pid: {
                "_project_dir": os.path.join(self.projects, pid),
                "_outputs_dir": os.path.join(self.projects, pid, "outputs"),
                "client_name": {"p_old": "旧客户", "p_new": "新客户", "p_none": "空客户"}[pid],
            }
            ledger = cl.build_check_ledger(now=now)

        by_id = {r["project_id"]: r for r in ledger["rows"]}
        self.assertEqual(by_id["p_none"]["status"], "never")
        self.assertEqual(by_id["p_old"]["status"], "overdue")
        self.assertEqual(by_id["p_new"]["status"], "ok")
        self.assertEqual(ledger["rows"][0]["status"], "never")
        self.assertTrue(by_id["p_new"].get("sample_note"))

    def test_timezone_boundary_warn_overdue(self):
        """边界前后 1 天：LA / UTC / +08 下 days_since 档位一致。"""
        self._mk_project("p_b", "边界客户")
        now = datetime(2026, 9, 9, 15, 0, 0, tzinfo=timezone.utc)
        # 恰超 7 天一点 → warn；恰超 14 → overdue
        at_warn = (now - timedelta(days=7, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        at_over = (now - timedelta(days=14, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        for label, at, expect in (("warn", at_warn, "warn"), ("over", at_over, "overdue")):
            # 清空日志
            open(self.log, "w").close()
            cl.append_check_log(project_id="p_b", mode="manual_probe", keywords=["k"], sov_pct=50, at=at)
            with patch.object(cl, "load_project_config") as mock_cfg, patch.object(
                cl, "load_notification_settings",
                return_value={"warn_days": 7, "overdue_days": 14, "min_manual_keywords": 1},
            ):
                mock_cfg.return_value = {
                    "_project_dir": os.path.join(self.projects, "p_b"),
                    "_outputs_dir": os.path.join(self.projects, "p_b", "outputs"),
                    "client_name": "边界客户",
                }
                # 三种「本地墙钟」换算到同一 UTC now
                for offset_hours in (-7, 0, 8):
                    local_now = now.astimezone(timezone(timedelta(hours=offset_hours)))
                    # build 内部统一用 utc now 参数
                    ledger = cl.build_check_ledger(now=local_now)
                    self.assertEqual(
                        ledger["rows"][0]["status"],
                        expect,
                        msg=f"{label} offset={offset_hours}",
                    )

    def test_days_since_utc_helper(self):
        now = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)
        at = "2026-09-02T12:00:00Z"
        d = cl.days_since_utc(at, now=now)
        self.assertAlmostEqual(d, 7.0, places=5)


if __name__ == "__main__":
    unittest.main()
