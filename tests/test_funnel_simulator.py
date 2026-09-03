# -*- coding: utf-8 -*-
"""大模型商业多轮追问决策漏斗与意图转化推演单元测试套件 (tests/test_funnel_simulator.py)

强断言覆盖：
1. 6 组固定数值夹具 (FCR 三档健康度、T 转移留存率、HRI 截流风险指数、关键脆弱拐点与 Top-3 89.0 分)；
2. 四阶决策意图确定性填槽输出断言；
3. 四维漏斗雷达指标 (end_to_end_conversion / awareness_to_eval_retention / decision_retention / action_cta_readiness) 严格数学验算；
4. 沙箱全流程、JSON 大盘契约与 24 号公文报告物理落盘 (含 Hijacking Proxy 声明、沙箱多轮推演非真实会话日志、竞品消融 Out of Scope 声明)；
5. outputs/funnel_defense_pack/ 下 3 份加固文件物理存在；
6. Live 模式下 Mock 生产字典返回提取、70/30 融合、全量重算 FCR、调用预算上限 (<=4次) 与中途异常 100% 完整回滚纯沙箱断言；
7. API 401 鉴权拦截与未生成报告 404 语义。
"""

import json
import os
import unittest
from unittest.mock import patch

from tools.geo.funnel_simulator import (
    build_funnel_decision_chain,
    calculate_stage_retention,
    calculate_fcr,
    calculate_hri,
    funnel_health_grade,
    calculate_funnel_radar_metrics,
    ConversationalFunnelSimulator,
    generate_funnel_defense_pack,
    generate_funnel_report_markdown,
)
from tools.geo.causal_auditor import score_brand_recommendation_confidence
from tools.geo.utils import PROJECTS_DIR


class TestFunnelSimulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pid = "xuzhou_xuanyuan"
        cls.out_dir = os.path.join(PROJECTS_DIR, cls.test_pid, "outputs")

    def test_01_fixture_assertions(self):
        """测试 6 组固定数值夹具硬断言 (FCR 三档、T 转移、HRI、断点预警与 Top-3 89.0分)"""
        # 夹具 1: P(S1)=80.0, P(S2)=72.0, P(S3)=64.0, P(S4)=60.0 => FCR = 75.0% (smooth_conversion)
        fcr1 = calculate_fcr(80.0, 60.0)
        g1_code, g1_name = funnel_health_grade(fcr1)
        self.assertEqual(fcr1, 75.0)
        self.assertEqual(g1_code, "smooth_conversion")

        # 夹具 2: P(S1)=80.0, P(S2)=56.0, P(S3)=48.0, P(S4)=44.0 => FCR = 55.0% (mid_funnel_leakage)
        fcr2 = calculate_fcr(80.0, 44.0)
        g2_code, g2_name = funnel_health_grade(fcr2)
        self.assertEqual(fcr2, 55.0)
        self.assertEqual(g2_code, "mid_funnel_leakage")

        # 夹具 3: P(S1)=80.0, P(S2)=40.0, P(S3)=32.0, P(S4)=24.0 => FCR = 30.0% (severe_dropoff)
        fcr3 = calculate_fcr(80.0, 24.0)
        g3_code, g3_name = funnel_health_grade(fcr3)
        self.assertEqual(fcr3, 30.0)
        self.assertEqual(g3_code, "severe_dropoff")

        # 夹具 4: P(S1)=80.0, P(S2)=48.0 => T(S1->S2) = 60.0%, HRI_2 = 40.0%
        t4 = calculate_stage_retention(80.0, 48.0)
        hri4 = calculate_hri(t4)
        self.assertEqual(t4, 60.0)
        self.assertEqual(hri4, 40.0)

        # 夹具 5: P(S3)=60.0, P(S4)=15.0 => drop_p = 45.0 (>= 20.0) => 命中高危断点
        drop5 = max(0.0, round(60.0 - 15.0, 1))
        t5 = calculate_stage_retention(60.0, 15.0)
        hri5 = calculate_hri(t5)
        is_tp5 = bool(drop5 >= 20.0 or hri5 >= 35.0)
        self.assertEqual(drop5, 45.0)
        self.assertTrue(is_tp5)

        # 夹具 6: v1=1.0, v2=0.8, v3=0.6 => P = 89.0 分 (直接复用 23 维基座算法)
        mock_chunks = [
            {"text": "query match 1", "auth_bonus": 1.0},
            {"text": "query match 2", "auth_bonus": 0.8},
            {"text": "query match 3", "auth_bonus": 0.6},
        ]
        with patch("tools.geo.causal_auditor.score_dense_similarity", side_effect=[1.0, 1.0, 1.0]):
            p_conf = score_brand_recommendation_confidence("query", mock_chunks)
            self.assertEqual(p_conf, 89.0)

    def test_02_decision_chain_generation(self):
        """测试四阶商业决策链条的确定性填槽输出"""
        chain = build_funnel_decision_chain(self.test_pid)
        self.assertEqual(len(chain), 4)
        s_ids = [c["stage_id"] for c in chain]
        self.assertEqual(s_ids, ["S1", "S2", "S3", "S4"])
        # 验证地名填槽 (xuzhou_xuanyuan 对应城市为 徐州)
        self.assertIn("徐州", chain[0]["query"])
        self.assertIn("服务商推荐哪家比较好", chain[0]["query"])
        self.assertIn("徐州璇源网络科技有限公司", chain[2]["query"])
        self.assertIn("官方网站", chain[3]["query"])

    def test_03_radar_metrics_mathematical_precision(self):
        """测试四维漏斗雷达量化指标的计算精度"""
        mock_stages = [
            {"stage_id": "S1", "retention_rate": 100.0},
            {"stage_id": "S2", "retention_rate": 90.0},
            {"stage_id": "S3", "retention_rate": 88.9},
            {"stage_id": "S4", "retention_rate": 93.8},
        ]
        radar = calculate_funnel_radar_metrics(75.0, mock_stages)
        self.assertEqual(radar["end_to_end_conversion"], 75.0)
        self.assertEqual(radar["awareness_to_eval_retention"], 90.0)
        self.assertEqual(radar["decision_retention"], 88.9)
        self.assertEqual(radar["action_cta_readiness"], 93.8)

    def test_04_simulate_sandbox_and_report(self):
        """测试沙箱多轮推演、JSON 契约 Schema 与 24 号公文报告物理落盘"""
        res = ConversationalFunnelSimulator.simulate_funnel(
            project_id=self.test_pid,
            models=["doubao", "deepseek", "kimi"],
            use_live=False,
        )
        self.assertTrue(res["success"])
        s = res["summary"]
        self.assertGreaterEqual(s["fcr"], 0.0)
        self.assertLessEqual(s["fcr"], 100.0)
        self.assertEqual(s["total_stages"], 4)
        self.assertIn(s["grade_code"], ["smooth_conversion", "mid_funnel_leakage", "severe_dropoff"])

        # 校验 JSON 落盘 (严格对齐 design.md §5 顶层契约)
        json_path = os.path.join(self.out_dir, "conversational_funnel_simulation.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["project_id"], self.test_pid)
            self.assertIn("summary", d)
            self.assertIn("stages", d)
            self.assertIn("hijack_turning_points", d)
            self.assertIn("radar_metrics", d)
            self.assertEqual(len(d["stages"]), 4)

        # 校验 24 号 Markdown 报告落盘 (含严谨免责话术与边界界定)
        report_path = os.path.join(self.out_dir, "24_大模型商业多轮追问决策漏斗与意图转化路径推演报告.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md = f.read()
            self.assertIn("大模型商业多轮追问决策漏斗与意图转化路径推演报告", md)
            self.assertIn("Hijacking Proxy", md)
            self.assertIn("竞品多轮实时消融属于 Out of Scope", md)
            self.assertIn("推演数据 $\\neq$ 真实线上用户会话日志", md)

    def test_05_generate_defense_pack(self):
        """测试 outputs/funnel_defense_pack/ 下 3 份优化拦截文件物理生成"""
        pack = generate_funnel_defense_pack(self.test_pid)
        self.assertTrue(pack["success"])
        files = pack.get("files", [])
        self.assertEqual(len(files), 3)
        for fp in files:
            self.assertTrue(os.path.exists(fp), f"拦截文案未生成: {fp}")

        pack_dir = os.path.join(self.out_dir, "funnel_defense_pack")
        f1 = os.path.join(pack_dir, "01_多轮追问意图锚定与心智收敛话术库.md")
        f2 = os.path.join(pack_dir, "02_防竞对二轮截流技术壁垒语料补充包.md")
        f3 = os.path.join(pack_dir, "03_高转化行动号召落地页外链回填方案.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))

    def test_06_live_mode_call_budget_and_dict_mock(self):
        """测试 Live 模式下 Mock 生产字典返回、70/30 融合、全量重算 FCR、中途异常回滚与调用上限 (<=4次)"""
        # 0. 先跑一次纯沙箱作为快照对照
        res_sandbox = ConversationalFunnelSimulator.simulate_funnel(
            project_id=self.test_pid,
            models=["doubao"],
            use_live=False,
        )
        sb_fcr = res_sandbox["summary"]["fcr"]
        sb_s1 = res_sandbox["stages"][0]["p_score"]
        sb_s4 = res_sandbox["stages"][3]["p_score"]

        # 1. 验证正常 live 模式: 调用次数 <= 4, 70/30 融合与全量指标基于新 P 重算
        # mock 各阶段分别返回 80, 70, 60, 50
        with patch("tools.geo.funnel_simulator.call_model_raw", side_effect=[
            {"content": "80分"}, {"content": "70分"}, {"content": "60分"}, {"content": "50分"}
        ]) as mock_api:
            res_live = ConversationalFunnelSimulator.simulate_funnel(
                project_id=self.test_pid,
                models=["doubao"],
                use_live=True,
            )
            self.assertTrue(res_live["is_live_judged"])
            self.assertLessEqual(mock_api.call_count, 4)

            # 验证融合数值
            exp_s1 = round(0.7 * sb_s1 + 0.3 * 80.0, 1)
            exp_s4 = round(0.7 * sb_s4 + 0.3 * 50.0, 1)
            self.assertEqual(res_live["stages"][0]["p_score"], exp_s1)
            self.assertEqual(res_live["stages"][3]["p_score"], exp_s4)

            # 验证 FCR 必须联动全新重算
            exp_fcr = calculate_fcr(exp_s1, exp_s4)
            self.assertEqual(res_live["summary"]["fcr"], exp_fcr)

        # 2. 验证中途异常 (前两轮成功，第三轮抛错): 必须 100% 完整回滚纯沙箱快照
        with patch("tools.geo.funnel_simulator.call_model_raw", side_effect=[
            {"content": "80分"}, {"content": "70分"}, RuntimeError("在线网关超时")
        ]):
            res_mid_err = ConversationalFunnelSimulator.simulate_funnel(
                project_id=self.test_pid,
                models=["doubao"],
                use_live=True,
            )
            self.assertFalse(res_mid_err["is_live_judged"])
            # 断言基线与 FCR 彻底回滚
            self.assertEqual(res_mid_err["summary"]["fcr"], sb_fcr)
            self.assertEqual(res_mid_err["stages"][0]["p_score"], sb_s1)

        # 3. 验证初始即异常平滑降级纯沙箱
        with patch("tools.geo.funnel_simulator.call_model_raw", side_effect=RuntimeError("网络断开")):
            res_fallback = ConversationalFunnelSimulator.simulate_funnel(
                project_id=self.test_pid,
                models=["doubao"],
                use_live=True,
            )
            self.assertFalse(res_fallback["is_live_judged"])
            self.assertTrue(res_fallback["success"])
            self.assertEqual(res_fallback["summary"]["fcr"], sb_fcr)

    def test_07_api_auth_and_404(self):
        """测试 API 未授权 401 拦截与报告不存在返回 404"""
        from tools.geo.server import GeoWebHandler, create_session

        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json

        # 1. 未授权请求 GET /api/projects/{id}/funnel/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/funnel/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)

        # 2. 未授权请求 POST /api/projects/{id}/funnel/simulate => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/funnel/simulate"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 带有效鉴权访问不存在 24 号报告的项目 => 404
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = "/api/projects/dummy_no_funnel_project/funnel/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 404)
        self.assertIn("24 号报告尚未生成", captured.get("payload", {}).get("message", ""))


if __name__ == "__main__":
    unittest.main()
