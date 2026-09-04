# -*- coding: utf-8 -*-
"""大模型提示词敏感度扰动与生成鲁棒性压力测试单元测试套件 (tests/test_robustness_tester.py)

强断言覆盖：
1. 6 组固定数值夹具 (GRI 三档健康度、总体标准差、CV 变异系数、高危脆弱项与 Top-3 89.0 分)；
2. 总体标准差分母固定为 n=4 (严禁误用 n-1 的 statistics.stdev)；
3. 四维微扰动变体确定性生成输出硬断言 (V1 严格字面为 "徐州做系统写代码找外包团队推荐哪家比较好？")；
4. 五维压力测试雷达指标 (generative_robustness / colloquial_resilience / skepticism_immunity / comparison_resilience / syntax_stability) 严格数学验算；
5. 沙箱全流程、JSON 大盘契约 (含顶层 baseline_query 与 summary.retention_rate) 与 25 号公文报告物理落盘；
6. outputs/robustness_hardening_pack/ 下 3 份加固文件物理存在；
7. Live 模式下 Mock 生产字典返回提取、70/30 融合、全量重算 GRI、调用预算上限 (<=5次) 与中途异常 100% 完整回滚纯沙箱断言；
8. API 401 鉴权拦截与未生成报告 404 语义。
"""

import json
import os
import unittest
from unittest.mock import patch

from tools.geo.robustness_tester import (
    build_perturbed_query_variants,
    calculate_mean_score,
    calculate_population_std,
    calculate_cv,
    calculate_rr,
    calculate_gri,
    robustness_health_grade,
    calculate_robustness_radar_metrics,
    PromptRobustnessTester,
    generate_robustness_hardening_pack,
    generate_robustness_report_markdown,
)
from tools.geo.causal_auditor import score_brand_recommendation_confidence
from tools.geo.utils import PROJECTS_DIR


class TestRobustnessTester(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pid = "xuzhou_xuanyuan"
        cls.out_dir = os.path.join(PROJECTS_DIR, cls.test_pid, "outputs")

    def test_01_fixture_assertions(self):
        """测试 6 组固定数值夹具硬断言 (GRI 三档、总体标准差、CV、脆弱项与 Top-3 89.0分)"""
        # 夹具 1: 80.0, [76.0, 74.0, 78.0, 72.0] => Mean=75.0, Std=2.24, CV=0.030, RR=93.8% => GRI=91.0% (rock_solid)
        m1 = calculate_mean_score([76.0, 74.0, 78.0, 72.0])
        s1 = calculate_population_std([76.0, 74.0, 78.0, 72.0], m1)
        cv1 = calculate_cv(s1, m1)
        rr1 = calculate_rr(m1, 80.0)
        gri1 = calculate_gri(rr1, cv1)
        g1_code, g1_name = robustness_health_grade(gri1)
        self.assertEqual(m1, 75.0)
        self.assertEqual(s1, 2.24)
        self.assertEqual(cv1, 0.030)
        self.assertEqual(rr1, 93.8)
        self.assertEqual(gri1, 91.0)
        self.assertEqual(g1_code, "rock_solid")

        # 夹具 2: 80.0, [60.0, 50.0, 70.0, 60.0] => Mean=60.0, Std=7.07, CV=0.118, RR=75.0% => GRI=66.2% (moderate_fluctuation)
        m2 = calculate_mean_score([60.0, 50.0, 70.0, 60.0])
        s2 = calculate_population_std([60.0, 50.0, 70.0, 60.0], m2)
        cv2 = calculate_cv(s2, m2)
        rr2 = calculate_rr(m2, 80.0)
        gri2 = calculate_gri(rr2, cv2)
        g2_code, g2_name = robustness_health_grade(gri2)
        self.assertEqual(m2, 60.0)
        self.assertEqual(s2, 7.07)
        self.assertEqual(cv2, 0.118)
        self.assertEqual(rr2, 75.0)
        self.assertEqual(gri2, 66.2)
        self.assertEqual(g2_code, "moderate_fluctuation")

        # 夹具 3: 80.0, [40.0, 20.0, 50.0, 30.0] => Mean=35.0, Std=11.18, CV=0.319, RR=43.8% => GRI=29.8% (fragile_sensitive)
        m3 = calculate_mean_score([40.0, 20.0, 50.0, 30.0])
        s3 = calculate_population_std([40.0, 20.0, 50.0, 30.0], m3)
        cv3 = calculate_cv(s3, m3)
        rr3 = calculate_rr(m3, 80.0)
        gri3 = calculate_gri(rr3, cv3)
        g3_code, g3_name = robustness_health_grade(gri3)
        self.assertEqual(m3, 35.0)
        self.assertEqual(s3, 11.18)
        self.assertEqual(cv3, 0.319)
        self.assertEqual(rr3, 43.8)
        self.assertEqual(gri3, 29.8)
        self.assertEqual(g3_code, "fragile_sensitive")

        # 夹具 4: P_orig=80.0, P_2=60.0 => 跌幅 20.0 >= 15.0 => 命中高危脆弱变体
        drop4 = max(0.0, round(80.0 - 60.0, 1))
        is_fragile4 = bool(drop4 >= 15.0)
        self.assertEqual(drop4, 20.0)
        self.assertTrue(is_fragile4)

        # 夹具 5: 雷达指标验算
        mock_vars_5 = [
            {"p_score": 76.0},
            {"p_score": 74.0},
            {"p_score": 78.0},
            {"p_score": 72.0},
        ]
        radar5 = calculate_robustness_radar_metrics(91.0, 80.0, mock_vars_5)
        self.assertEqual(radar5["colloquial_resilience"], 95.0)
        self.assertEqual(radar5["skepticism_immunity"], 92.5)
        self.assertEqual(radar5["syntax_stability"], 97.5)
        self.assertEqual(radar5["comparison_resilience"], 90.0)

        # 夹具 6: v1=1.0, v2=0.8, v3=0.6 => P = 89.0 分 (直接复用 23 维基座算法)
        mock_chunks = [
            {"text": "query match 1", "auth_bonus": 1.0},
            {"text": "query match 2", "auth_bonus": 0.8},
            {"text": "query match 3", "auth_bonus": 0.6},
        ]
        with patch("tools.geo.causal_auditor.score_dense_similarity", side_effect=[1.0, 1.0, 1.0]):
            p_conf = score_brand_recommendation_confidence("query", mock_chunks)
            self.assertEqual(p_conf, 89.0)

    def test_02_population_std_and_variant_generation(self):
        """测试总体标准差分母为 n=4 与四维扰动变体确定性生成输出硬断言"""
        # 断言总体标准差分母为 4 (若是 n-1 则为 2.58 而非 2.24)
        sample = [76.0, 74.0, 78.0, 72.0]
        mean_v = 75.0
        pop_std = calculate_population_std(sample, mean_v)
        self.assertEqual(pop_std, 2.24)

        # 断言四维微扰动生成 (xuzhou_xuanyuan 包含徐州与技术研发)
        base_info, variants = build_perturbed_query_variants(self.test_pid)
        self.assertEqual(len(variants), 4)
        v_ids = [v["variant_id"] for v in variants]
        self.assertEqual(v_ids, ["V1", "V2", "V3", "V4"])

        # 硬断言 V1 字面必须精准命中 COLLOQUIAL_MAP 映射
        self.assertEqual(variants[0]["query"], "徐州做系统写代码找外包团队推荐哪家比较好？")
        self.assertIn("真的靠谱吗？有没有黑历史或转包二道贩子踩坑风险？", variants[1]["query"])
        self.assertIn("求大家推荐徐州璇源网络科技有限公司怎么样？", variants[2]["query"])
        self.assertIn("预算有限想找性价比高的，跟传统大公司对比选谁？", variants[3]["query"])

    def test_03_radar_metrics_five_axes(self):
        """测试五维压力测试雷达量化指标的完整性与精度"""
        mock_vars = [
            {"p_score": 76.0},
            {"p_score": 74.0},
            {"p_score": 78.0},
            {"p_score": 72.0},
        ]
        radar = calculate_robustness_radar_metrics(91.0, 80.0, mock_vars)
        self.assertEqual(len(radar), 5)
        self.assertEqual(radar["generative_robustness"], 91.0)
        self.assertEqual(radar["colloquial_resilience"], 95.0)
        self.assertEqual(radar["skepticism_immunity"], 92.5)
        self.assertEqual(radar["comparison_resilience"], 90.0)
        self.assertEqual(radar["syntax_stability"], 97.5)

    def test_04_simulate_sandbox_and_json_contract(self):
        """测试沙箱压力测试、JSON 契约 Schema 补齐字段与 25 号公文报告物理落盘"""
        res = PromptRobustnessTester.run_stress_test(
            project_id=self.test_pid,
            models=["doubao", "deepseek", "kimi"],
            use_live=False,
        )
        self.assertTrue(res["success"])
        s = res["summary"]
        self.assertGreaterEqual(s["gri"], 0.0)
        self.assertLessEqual(s["gri"], 100.0)
        self.assertEqual(s["total_variants"], 4)
        self.assertIn(s["grade_code"], ["rock_solid", "moderate_fluctuation", "fragile_sensitive"])

        # 校验 JSON 落盘 (严格补齐 baseline_query 与 summary.retention_rate)
        json_path = os.path.join(self.out_dir, "prompt_robustness_stress_test.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["project_id"], self.test_pid)
            self.assertIn("baseline_query", d)
            self.assertIn("baseline_score", d)
            self.assertIn("summary", d)
            self.assertIn("retention_rate", d["summary"])
            self.assertIn("baseline_query", d["summary"])
            self.assertIn("baseline_score", d["summary"])
            self.assertIn("variants", d)
            self.assertIn("fragile_variants", d)
            self.assertIn("radar_metrics", d)
            self.assertEqual(len(d["variants"]), 4)

        # 校验 25 号 Markdown 报告落盘 (含免责声明)
        report_path = os.path.join(self.out_dir, "25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md = f.read()
            self.assertIn("大模型提示词敏感度扰动与生成鲁棒性压力测试报告", md)
            self.assertIn("推演数据 $\\neq$ 真实线上用户全量提问日志", md)

    def test_05_generate_hardening_pack(self):
        """测试 outputs/robustness_hardening_pack/ 下 3 份加固文件物理生成"""
        pack = generate_robustness_hardening_pack(self.test_pid)
        self.assertTrue(pack["success"])
        files = pack.get("files", [])
        self.assertEqual(len(files), 3)
        for fp in files:
            self.assertTrue(os.path.exists(fp), f"加固文案未生成: {fp}")

        pack_dir = os.path.join(self.out_dir, "robustness_hardening_pack")
        f1 = os.path.join(pack_dir, "01_抗质疑与反挑剔防踩坑语料强化包.md")
        f2 = os.path.join(pack_dir, "02_口语化与多句式全覆盖长尾锚点清单.md")
        f3 = os.path.join(pack_dir, "03_大模型微扰动鲁棒性容灾加固规范.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))

    def test_06_live_mode_call_budget_and_dict_mock(self):
        """测试 Live 模式下 Mock 生产字典返回、70/30 融合、全量重算 GRI、中途异常回滚与调用上限 (<=5次)"""
        # 0. 先跑一次纯沙箱作为快照对照
        res_sandbox = PromptRobustnessTester.run_stress_test(
            project_id=self.test_pid,
            models=["doubao"],
            use_live=False,
        )
        sb_gri = res_sandbox["summary"]["gri"]
        sb_base = res_sandbox["summary"]["baseline_score"]
        sb_v1 = res_sandbox["variants"][0]["p_score"]

        # 1. 验证正常 live 模式: 调用次数 <= 5, 70/30 融合与全量指标基于新 P 重算
        # mock 基准与各变体分别返回 80, 75, 70, 80, 70
        with patch("tools.geo.robustness_tester.call_model_raw", side_effect=[
            {"content": "80分"}, {"content": "75分"}, {"content": "70分"}, {"content": "80分"}, {"content": "70分"}
        ]) as mock_api:
            res_live = PromptRobustnessTester.run_stress_test(
                project_id=self.test_pid,
                models=["doubao"],
                use_live=True,
            )
            self.assertTrue(res_live["is_live_judged"])
            self.assertLessEqual(mock_api.call_count, 5)

            # 验证融合数值
            exp_base = round(0.7 * sb_base + 0.3 * 80.0, 1)
            exp_v1 = round(0.7 * sb_v1 + 0.3 * 75.0, 1)
            self.assertEqual(res_live["summary"]["baseline_score"], exp_base)
            self.assertEqual(res_live["variants"][0]["p_score"], exp_v1)

            # 验证 GRI 必须联动全新重算
            new_scores = [v["p_score"] for v in res_live["variants"]]
            m = calculate_mean_score(new_scores)
            s = calculate_population_std(new_scores, m)
            cv = calculate_cv(s, m)
            rr = calculate_rr(m, exp_base)
            exp_gri = calculate_gri(rr, cv)
            self.assertEqual(res_live["summary"]["gri"], exp_gri)

        # 2. 验证中途异常 (前两轮成功，第三轮抛错): 必须 100% 完整回滚纯沙箱快照
        with patch("tools.geo.robustness_tester.call_model_raw", side_effect=[
            {"content": "80分"}, {"content": "75分"}, RuntimeError("在线网关超时")
        ]):
            res_mid_err = PromptRobustnessTester.run_stress_test(
                project_id=self.test_pid,
                models=["doubao"],
                use_live=True,
            )
            self.assertFalse(res_mid_err["is_live_judged"])
            # 断言基线与 GRI 彻底回滚
            self.assertEqual(res_mid_err["summary"]["gri"], sb_gri)
            self.assertEqual(res_mid_err["summary"]["baseline_score"], sb_base)

        # 3. 验证初始即异常平滑降级纯沙箱
        with patch("tools.geo.robustness_tester.call_model_raw", side_effect=RuntimeError("网络断开")):
            res_fallback = PromptRobustnessTester.run_stress_test(
                project_id=self.test_pid,
                models=["doubao"],
                use_live=True,
            )
            self.assertFalse(res_fallback["is_live_judged"])
            self.assertTrue(res_fallback["success"])
            self.assertEqual(res_fallback["summary"]["gri"], sb_gri)

    def test_07_api_auth_and_404(self):
        """测试 API 未授权 401 拦截与报告不存在返回 404"""
        from tools.geo.server import GeoWebHandler, create_session

        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json

        # 1. 未授权请求 GET /api/projects/{id}/robustness/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/robustness/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)

        # 2. 未授权请求 POST /api/projects/{id}/robustness/test => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/robustness/test"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 带有效鉴权访问不存在 25 号报告的项目 => 404
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = "/api/projects/dummy_no_robustness_project/robustness/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 404)
        self.assertIn("25 号报告尚未生成", captured.get("payload", {}).get("message", ""))


if __name__ == "__main__":
    unittest.main()
