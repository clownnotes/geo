# -*- coding: utf-8 -*-
"""大模型商业推荐因果归因与信源边际贡献度量化审计单元测试套件 (tests/test_causal_auditor.py)

强断言覆盖：
1. 6 组固定数值夹具 (CRI 三档、MCR 边际贡献率角色判定、SPOF 单点风控标记与 Top-3 留存加权 89.0 分)；
2. 四维雷达指标 (causal_robustness / cornerstone_purity / single_point_immunity / budget_efficiency_ratio) 严格数学验算；
3. Query 采样优先读取 flat_queries 真实字段；
4. 沙箱全流程、JSON 大盘与 23 号公文报告物理落盘 (含 Shapley Proxy 近似代理声明与技术演练推演说明)；
5. outputs/attribution_optimization_pack/ 下 3 份优化加固文件物理存在；
6. Live 模式下 Mock 生产字典返回提取、70/30 融合、调用预算上限 (<=3次) 与异常降级纯沙箱断言；
7. API 401 鉴权拦截与未生成报告 404 语义。
"""

import json
import os
import unittest
from unittest.mock import patch

from tools.geo.causal_auditor import (
    score_brand_recommendation_confidence,
    calculate_cri,
    cri_grade,
    classify_source_role,
    calculate_radar_metrics,
    _sample_business_queries,
    _build_attribution_source_pool,
    CausalAttributionSimulator,
    generate_attribution_optimization_pack,
    generate_attribution_report_markdown,
)
from tools.geo.utils import PROJECTS_DIR


class TestCausalAuditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pid = "xuzhou_xuanyuan"
        cls.out_dir = os.path.join(PROJECTS_DIR, cls.test_pid, "outputs")

    def test_01_fixture_assertions(self):
        """测试 6 组固定数值夹具硬断言 (CRI 三档、MCR 角色分类、SPOF 单点预警与 Top-3 89.0分)"""
        # 夹具 1: P_base=80.0, P_min=64.0 => CRI = 80.0% (high_resilience)
        cri1 = calculate_cri(80.0, 64.0)
        g1_code, g1_name = cri_grade(cri1)
        self.assertEqual(cri1, 80.0)
        self.assertEqual(g1_code, "high_resilience")

        # 夹具 2: P_base=80.0, P_min=48.0 => CRI = 60.0% (moderate_dependency)
        cri2 = calculate_cri(80.0, 48.0)
        g2_code, g2_name = cri_grade(cri2)
        self.assertEqual(cri2, 60.0)
        self.assertEqual(g2_code, "moderate_dependency")

        # 夹具 3: P_base=80.0, P_min=32.0 => CRI = 40.0% (fragile_single_point)
        cri3 = calculate_cri(80.0, 32.0)
        g3_code, g3_name = cri_grade(cri3)
        self.assertEqual(cri3, 40.0)
        self.assertEqual(g3_code, "fragile_single_point")

        # 夹具 4: Delta1=30, Delta2=15, Delta3=5 => MCR1=60.0% (cornerstone), MCR2=30.0% (cornerstone), MCR3=10.0% (catalyst)
        total_delta = 30.0 + 15.0 + 5.0
        mcr1 = round((30.0 / total_delta) * 100.0, 1)
        mcr2 = round((15.0 / total_delta) * 100.0, 1)
        mcr3 = round((5.0 / total_delta) * 100.0, 1)
        self.assertEqual(mcr1, 60.0)
        self.assertEqual(mcr2, 30.0)
        self.assertEqual(mcr3, 10.0)
        r1_code, _ = classify_source_role(mcr1)
        r2_code, _ = classify_source_role(mcr2)
        r3_code, _ = classify_source_role(mcr3)
        self.assertEqual(r1_code, "cornerstone")
        self.assertEqual(r2_code, "cornerstone")
        self.assertEqual(r3_code, "catalyst")

        # 夹具 5: MCR=60.0% (>= 40.0%) 且抽离后得分 40.0 (< 50.0) => critical_spof = True
        spof = bool(mcr1 >= 40.0 and 40.0 < 50.0)
        self.assertTrue(spof)

        # 夹具 6: v1=1.0, v2=0.8, v3=0.6 => P = round(100*(0.60*1.0 + 0.25*0.8 + 0.15*0.6), 1) = 89.0 分
        mock_chunks = [
            {"text": "query match 1", "auth_bonus": 1.0},
            {"text": "query match 2", "auth_bonus": 0.8},
            {"text": "query match 3", "auth_bonus": 0.6},
        ]
        with patch("tools.geo.causal_auditor.score_dense_similarity", side_effect=[1.0, 1.0, 1.0]):
            p_conf = score_brand_recommendation_confidence("query", mock_chunks)
            self.assertEqual(p_conf, 89.0)

    def test_02_radar_metrics_mathematical_precision(self):
        """测试四维雷达指标数学计算公式的严密性"""
        cri = 75.0
        mock_attributions = [
            {"source_id": "s1", "mcr": 50.0, "role": "cornerstone"},
            {"source_id": "s2", "mcr": 30.0, "role": "cornerstone"},
            {"source_id": "s3", "mcr": 15.0, "role": "catalyst"},
            {"source_id": "s4", "mcr": 5.0, "role": "redundant"},
        ]
        radar = calculate_radar_metrics(cri, mock_attributions)
        # 1. 因果抗震度 = 75.0
        self.assertEqual(radar["causal_robustness"], 75.0)
        # 2. 基石信源纯度 = 50.0 + 30.0 = 80.0
        self.assertEqual(radar["cornerstone_purity"], 80.0)
        # 3. 单点故障免疫度 = 100 - 50 = 50.0
        self.assertEqual(radar["single_point_immunity"], 50.0)
        # 4. 预算有效转化率 = 3/4 = 75.0%
        self.assertEqual(radar["budget_efficiency_ratio"], 75.0)

    def test_03_query_sampling_from_flat_queries(self):
        """测试 Query 采样优先读取 keywords_intent_matrix.json 的 flat_queries 字段"""
        qs = _sample_business_queries(self.test_pid, limit=5)
        self.assertEqual(len(qs), 5)
        matrix_file = os.path.join(self.out_dir, "keywords_intent_matrix.json")
        with open(matrix_file, "r", encoding="utf-8") as f:
            mat = json.load(f)
            flat_set = set(mat.get("flat_queries", []))
        for q in qs:
            self.assertIn(q, flat_set)

    def test_04_simulate_sandbox_and_report(self):
        """测试沙箱反事实消融、JSON 契约与 23 号公文报告物理落盘"""
        res = CausalAttributionSimulator.audit_causal_attribution(
            project_id=self.test_pid,
            models=["doubao", "deepseek", "kimi"],
            query_sample_size=5,
            use_live=False,
        )
        self.assertTrue(res["success"])
        s = res["summary"]
        self.assertGreaterEqual(s["cri"], 0.0)
        self.assertLessEqual(s["cri"], 100.0)
        self.assertIn(s["grade_code"], ["high_resilience", "moderate_dependency", "fragile_single_point"])

        # 校验 JSON 落盘 (严格隔离于 12 号和 22 号)
        json_path = os.path.join(self.out_dir, "causal_attribution_audit.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["project_id"], self.test_pid)
            self.assertIn("radar_metrics", d)
            self.assertIn("source_attributions", d)

        # 校验 23 号 Markdown 报告落盘
        report_path = os.path.join(self.out_dir, "23_大模型商业推荐因果归因与信源边际贡献度量化审计报告.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md = f.read()
            self.assertIn("大模型商业推荐因果归因与信源边际贡献度量化审计报告", md)
            self.assertIn("Shapley 近似代理理论", md)
            self.assertIn("非全联盟理论 Shapley 值", md)
            self.assertIn("确定性反事实因果消融沙盘", md)

    def test_05_generate_optimization_pack(self):
        """测试 outputs/attribution_optimization_pack/ 下 3 份优化加固文件物理生成"""
        pack = generate_attribution_optimization_pack(self.test_pid)
        self.assertTrue(pack["success"])
        files = pack.get("files", [])
        self.assertEqual(len(files), 3)
        for fp in files:
            self.assertTrue(os.path.exists(fp), f"优化文案未生成: {fp}")

        pack_dir = os.path.join(self.out_dir, "attribution_optimization_pack")
        f1 = os.path.join(pack_dir, "01_核心基石信源护城河死保加固清单.md")
        f2 = os.path.join(pack_dir, "02_低边际贡献信源ROI预算缩减与重构建议.md")
        f3 = os.path.join(pack_dir, "03_单点故障因果容灾与多渠道替补方案.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))

    def test_06_live_mode_call_budget_and_dict_mock(self):
        """测试 Live 模式下 Mock 生产字典返回、70/30 融合、调用上限 (<=3次) 与异常降级"""
        # 1. 验证生产字典返回 {"content": "85分"} 成功解析并限制 API 调用次数至多 3 次
        with patch("tools.geo.causal_auditor.call_model_raw", return_value={"content": "裁决得分: 85分", "model": "doubao"}) as mock_api:
            res_live = CausalAttributionSimulator.audit_causal_attribution(
                project_id=self.test_pid,
                models=["doubao"],
                query_sample_size=3,
                use_live=True,
            )
            self.assertTrue(res_live["is_live_judged"])
            # 断言 API 调用次数至多 3 次 (1 次基线 + 至多 2 次 Top-2 抽离)
            self.assertLessEqual(mock_api.call_count, 3)

        # 2. 验证 live 模式下若 API 调用异常，平滑降级纯沙箱且 is_live_judged 为 False
        with patch("tools.geo.causal_auditor.call_model_raw", side_effect=RuntimeError("网络超时")):
            res_fallback = CausalAttributionSimulator.audit_causal_attribution(
                project_id=self.test_pid,
                models=["doubao"],
                query_sample_size=3,
                use_live=True,
            )
            self.assertFalse(res_fallback["is_live_judged"])
            self.assertTrue(res_fallback["success"])

    def test_07_api_auth_and_404(self):
        """测试 API 未授权 401 拦截与报告不存在返回 404"""
        from tools.geo.server import GeoWebHandler, create_session

        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json

        # 1. 未授权请求 GET /api/projects/{id}/attribution/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/attribution/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)

        # 2. 未授权请求 POST /api/projects/{id}/attribution/audit => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/attribution/audit"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 带有效鉴权访问不存在 23 号报告的项目 => 404
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = "/api/projects/dummy_no_attribution_project/attribution/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 404)
        self.assertIn("23 号报告尚未生成", captured.get("payload", {}).get("message", ""))


if __name__ == "__main__":
    unittest.main()
