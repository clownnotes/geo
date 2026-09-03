# -*- coding: utf-8 -*-
"""大模型知识半衰期衰减监测与长效自愈中枢单元测试套件 (tests/test_decay_monitor.py)

强断言：
1. 3 组固定数值夹具（100%/90天、75%/33.7天、50%/14.0天）精确匹配；
2. 沙箱时间序列仿真与 20 号报告物理落盘；
3. 20 号报告强制包含沙箱保真免责话术；
4. decay_healing_pack 3 份自愈成果物物理存在；
5. API 鉴权拦截（401）与 /report 缺失返回 404。
"""

import json
import os
import shutil
import tempfile
import unittest
from io import BytesIO

from tools.geo.decay_monitor import (
    calculate_krr,
    estimate_half_life,
    decay_risk_level,
    track_knowledge_decay,
    generate_decay_healing_pack,
    get_decay_status,
)
from tools.geo.utils import PROJECTS_DIR


class TestDecayMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pid = "xuzhou_xuanyuan"
        cls.out_dir = os.path.join(PROJECTS_DIR, cls.test_pid, "outputs")

    def test_01_fixture_assertions(self):
        """测试 3 组固定数值夹具强断言"""
        # 夹具 1: S_current=12.0, S_baseline=12.0 => KRR=100.0%, t_1/2=90.0 (Safe)
        krr1 = calculate_krr(12.0, 12.0)
        hl1, l1 = estimate_half_life(krr1, delta_days=14.0)
        self.assertEqual(krr1, 100.0)
        self.assertEqual(hl1, 90.0)
        self.assertEqual(decay_risk_level(krr1), "safe")

        # 夹具 2: S_current=9.0, S_baseline=12.0 => KRR=75.0%, dt=14 => t_1/2=33.7 (Warning)
        krr2 = calculate_krr(9.0, 12.0)
        hl2, l2 = estimate_half_life(krr2, delta_days=14.0)
        self.assertEqual(krr2, 75.0)
        self.assertEqual(hl2, 33.7)
        self.assertEqual(decay_risk_level(krr2), "warning")

        # 夹具 3: S_current=6.0, S_baseline=12.0 => KRR=50.0%, dt=14 => t_1/2=14.0 (Danger)
        krr3 = calculate_krr(6.0, 12.0)
        hl3, l3 = estimate_half_life(krr3, delta_days=14.0)
        self.assertEqual(krr3, 50.0)
        self.assertEqual(hl3, 14.0)
        self.assertEqual(decay_risk_level(krr3), "danger")

    def test_02_track_knowledge_decay_sandbox(self):
        """测试沙箱下衰减监测与 20 号报告、JSON 时间序列落盘"""
        res = track_knowledge_decay(
            project_id=self.test_pid,
            models=["doubao", "deepseek", "kimi"],
            query_sample_size=5,
            use_live=False,
            delta_days=14.0,
        )
        self.assertTrue(res["success"])
        self.assertIn("summary", res)
        s = res["summary"]
        self.assertGreaterEqual(s["krr"], 0.0)
        self.assertLessEqual(s["krr"], 100.0)
        self.assertIn(s["risk_level"], ["safe", "warning", "danger"])
        self.assertEqual(s["total_probes"], 15)

        # 校验 JSON 文件落盘
        json_path = os.path.join(self.out_dir, "knowledge_decay_retention.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["project_id"], self.test_pid)
            self.assertGreater(len(d["time_series_records"]), 0)

        # 校验 20 号 Markdown 报告落盘与免责声明 (P0-5)
        report_path = os.path.join(self.out_dir, "20_大模型知识半衰期衰减监测与长效留存自愈报告.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn("⏳ 大模型知识半衰期衰减监测与长效留存自愈报告", md_content)
            self.assertIn("沙箱仿真不可替代真实大模型联网 API 实盘审计", md_content)

    def test_03_generate_decay_healing_pack(self):
        """测试自愈补量包 3 份落地文件生成"""
        pack = generate_decay_healing_pack(self.test_pid)
        self.assertTrue(pack["success"])
        files = pack.get("files", [])
        self.assertEqual(len(files), 3)
        for fp in files:
            self.assertTrue(os.path.exists(fp), f"文件未生成: {fp}")

        pack_dir = os.path.join(self.out_dir, "decay_healing_pack")
        f1 = os.path.join(pack_dir, "01_高衰减长尾搜索词定向强化清单.md")
        f2 = os.path.join(pack_dir, "02_大模型知识记忆自愈刷新文章草稿.md")
        f3 = os.path.join(pack_dir, "03_全渠道增量补量分发推荐计划表.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))

    def test_04_get_decay_status(self):
        """测试状态读取函数"""
        st = get_decay_status(self.test_pid)
        self.assertTrue(st["success"])
        self.assertTrue(st.get("has_records", False))

        # 测试不存在的项目
        st_none = get_decay_status("non_existent_project_xyz")
        self.assertTrue(st_none["success"])
        self.assertFalse(st_none.get("has_records", True))

    def test_05_api_auth_and_404(self):
        """测试 API 未授权 401 拦截与 20 号报告不存在时返回 404"""
        from tools.geo.server import GeoWebHandler, create_session

        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json

        # 1. 未授权请求 GET /api/projects/{id}/decay/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/decay/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)
        self.assertIn("未登录", captured.get("payload", {}).get("message", ""))

        # 2. 未授权请求 POST /api/projects/{id}/decay/track => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/decay/track"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 带有效鉴权访问一个不存在报告的项目 => 404
        from tools.geo.server import create_session
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = "/api/projects/dummy_no_report_project/decay/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 404)
        self.assertIn("20 号报告尚未生成", captured.get("payload", {}).get("message", ""))

    def test_06_p1_closing_assertions(self):
        """测试 Cursor P1 审查意见硬闭环断言 (首发基线固化 / delta_days兜底 / live话术自适应)"""
        from tools.geo.decay_monitor import (
            calculate_delta_days_from_ledger,
            generate_decay_report_markdown,
        )

        # 1. dt <= 0 严格兜底为 14.0 天 (P1-2)
        hl_zero, _ = estimate_half_life(75.0, delta_days=0)
        hl_neg, _ = estimate_half_life(75.0, delta_days=-5.0)
        self.assertEqual(hl_zero, 33.7)
        self.assertEqual(hl_neg, 33.7)

        # 2. 台账 delta_days 推算 (P1-2)
        dt_ledger = calculate_delta_days_from_ledger(self.test_pid)
        self.assertGreater(dt_ledger, 0.0)

        # 3. 全 Live 报告自适应话术声明 (P1-3)
        mock_live_data = {
            "client_name": "测试企业",
            "project_id": "test_live_prj",
            "timestamp": "2026-09-03 04:10:00",
            "summary": {
                "krr": 90.0,
                "half_life_days": 65.0,
                "decay_rate_lambda": 0.010,
                "risk_level": "safe",
                "use_live": True,
            },
            "probe_records": [
                {"is_live": True, "model": "doubao", "query": "q1", "score": 1.0},
                {"is_live": True, "model": "deepseek", "query": "q2", "score": 1.0},
            ],
            "time_series_records": [],
            "query_decay_breakdown": [],
        }
        live_report = generate_decay_report_markdown(mock_live_data)
        self.assertIn("数据说明与实盘审计声明", live_report)
        self.assertNotIn("沙箱仿真不可替代真实大模型联网 API 实盘审计", live_report)

        # 4. 验证默认主路径未被短路：delta_days=None 时优先走台账动态推算 (闭环 P1-2 主路径短路)
        res_default = track_knowledge_decay(self.test_pid, delta_days=None)
        expected_dt = calculate_delta_days_from_ledger(self.test_pid)
        self.assertEqual(res_default["summary"]["delta_days"], expected_dt)


if __name__ == "__main__":
    unittest.main()
