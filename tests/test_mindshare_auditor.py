# -*- coding: utf-8 -*-
"""大模型品牌商业心智渗透率与商业转化价值审计单元测试套件 (tests/test_mindshare_auditor.py)

强断言覆盖：
1. 4 组固定数值夹具 (含 MPI 三档区间与 AEV 48454 元严格公式验算)；
2. 缺档策略断言: 缺失 19/20 档案时严格按中性 50.0 兜底并标记 imputed；
3. 沙箱时间序列仿真与 21 号报告物理落盘 (含沙箱免责与财务非凭证声明)；
4. commercial_roi_pitch 3 份高管商务成果物物理存在；
5. Live 模式下自适应实盘审计话术；
6. API 鉴权拦截 (401) 与无报告返回 404。
"""

import json
import os
import shutil
import tempfile
import unittest

from tools.geo.mindshare_auditor import (
    calculate_mpi,
    mindshare_grade,
    estimate_commercial_conversion_value,
    audit_mindshare_penetration,
    generate_commercial_pitch_pack,
    generate_mindshare_report_markdown,
    get_mindshare_status,
)
from tools.geo.utils import PROJECTS_DIR


class TestMindshareAuditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pid = "xuzhou_xuanyuan"
        cls.out_dir = os.path.join(PROJECTS_DIR, cls.test_pid, "outputs")

    def test_01_fixture_assertions(self):
        """测试 4 组固定数值夹具强断言 (MPI 三档与 AEV 48454元)"""
        # 夹具 1: SOV=80.0, Cit=60.0, BRS=90.0, KRR=100.0 => MPI=80.5 (strong_contender)
        m1 = calculate_mpi(80.0, 60.0, 90.0, 100.0)
        g1_code, g1_name = mindshare_grade(m1)
        self.assertEqual(m1, 80.5)
        self.assertEqual(g1_code, "strong_contender")

        # 夹具 2: SOV=100.0, Cit=80.0, BRS=100.0, KRR=100.0 => MPI=95.0 (market_leader)
        m2 = calculate_mpi(100.0, 80.0, 100.0, 100.0)
        g2_code, g2_name = mindshare_grade(m2)
        self.assertEqual(m2, 95.0)
        self.assertEqual(g2_code, "market_leader")

        # 夹具 3: SOV=40.0, Cit=20.0, BRS=60.0, KRR=50.0 => MPI=41.5 (underrepresented)
        m3 = calculate_mpi(40.0, 20.0, 60.0, 50.0)
        g3_code, g3_name = mindshare_grade(m3)
        self.assertEqual(m3, 41.5)
        self.assertEqual(g3_code, "underrepresented")

        # 夹具 4: |Q|=5, MPI=88.5, CPA=150, factor=0.20 => AEV=48454 元 (闭环 P0-1)
        aev_data = estimate_commercial_conversion_value(
            mpi=88.5, query_count=5, industry="software", cpa_override=150, conversion_factor=0.20
        )
        self.assertEqual(aev_data["annual_aev_yuan"], 48454)
        self.assertEqual(aev_data["cpa_unit_price"], 150)
        self.assertEqual(aev_data["conversion_factor"], 0.20)

    def test_02_audit_sandbox_and_report_generation(self):
        """测试沙箱模式下商业心智审计、JSON 数据大盘与 21 号报告落盘"""
        res = audit_mindshare_penetration(
            project_id=self.test_pid,
            models=["doubao", "deepseek", "kimi"],
            query_sample_size=5,
            use_live=False,
        )
        self.assertTrue(res["success"])
        self.assertIn("summary", res)
        s = res["summary"]
        self.assertGreaterEqual(s["mpi"], 0.0)
        self.assertLessEqual(s["mpi"], 100.0)
        self.assertIn(s["mindshare_grade"], ["market_leader", "strong_contender", "moderate_visibility", "underrepresented"])
        self.assertGreater(s["annual_aev_yuan"], 0)
        self.assertEqual(s["total_probes"], 15)

        # 校验 JSON 落盘
        json_path = os.path.join(self.out_dir, "mindshare_conversion_audit.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["project_id"], self.test_pid)
            self.assertIn("radar_metrics", d)
            self.assertIn("query_audits", d)

        # 校验 21 号 Markdown 报告落盘与免责声明
        report_path = os.path.join(self.out_dir, "21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn("大模型品牌商业心智渗透率与商业转化价值审计公文报告", md_content)
            self.assertIn("沙箱仿真不可替代真实大模型联网 API 实盘审计", md_content)
            self.assertIn("不作为企业财税审计、资产评估或法定会计记账凭证", md_content)

    def test_03_generate_commercial_pitch_pack(self):
        """测试 outputs/commercial_roi_pitch/ 下 3 份高管商务成果物生成"""
        pack = generate_commercial_pitch_pack(self.test_pid)
        self.assertTrue(pack["success"])
        files = pack.get("files", [])
        self.assertEqual(len(files), 3)
        for fp in files:
            self.assertTrue(os.path.exists(fp), f"高管文件未生成: {fp}")

        pack_dir = os.path.join(self.out_dir, "commercial_roi_pitch")
        f1 = os.path.join(pack_dir, "01_企业大模型商业心智渗透率与竞对对标董事会简报.md")
        f2 = os.path.join(pack_dir, "02_GEO全案代运营商业回报率ROI与等效广告价值测算书.md")
        f3 = os.path.join(pack_dir, "03_下一阶段大模型商业心智护城河强化与续约规划建议书.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))

    def test_04_missing_files_imputed_fallback(self):
        """测试无 19/20 号 outputs 文件时，严格采用中性分 50.0 兜底策略 (闭环 P0-2)"""
        # 在一个临时独立虚拟项目中运行审计
        dummy_pid = "temp_imputed_test_project"
        dummy_dir = os.path.join(PROJECTS_DIR, dummy_pid)
        dummy_out = os.path.join(dummy_dir, "outputs")
        os.makedirs(dummy_out, exist_ok=True)
        try:
            with open(os.path.join(dummy_dir, "project.yaml"), "w", encoding="utf-8") as f:
                f.write("client_name: 临时缺档测试企业\nindustry: default\n")

            res = audit_mindshare_penetration(dummy_pid, query_sample_size=3, use_live=False)
            s = res["summary"]
            # 必须严格断言：缺失 19/20 号文件时，按中性 50.0 兜底，严禁填 95/85 乐观分
            self.assertEqual(s["brs_score"], 50.0)
            self.assertTrue(s["brs_imputed"])
            self.assertEqual(s["krr_rate"], 50.0)
            self.assertTrue(s["krr_imputed"])
        finally:
            if os.path.exists(dummy_dir):
                shutil.rmtree(dummy_dir)

    def test_05_live_report_declaration_adaptive(self):
        """测试 Live 模式下报告自适应切换实盘审计声明"""
        mock_live_data = {
            "client_name": "测试企业",
            "project_id": "test_live_prj",
            "timestamp": "2026-09-03 04:30:00",
            "summary": {
                "mpi": 92.0,
                "grade_name": "🟢 五星心智垄断",
                "annual_aev_yuan": 50000,
                "cpa_unit_price": 150,
                "weighted_sov_rate": 90.0,
                "citation_rate": 80.0,
                "brs_score": 98.0,
                "krr_rate": 95.0,
                "use_live": True,
            },
            "probe_records": [
                {"is_live": True, "model": "doubao", "score": 1.0},
                {"is_live": True, "model": "deepseek", "score": 1.0},
            ],
            "radar_metrics": {},
            "query_audits": [],
        }
        live_report = generate_mindshare_report_markdown(mock_live_data)
        self.assertIn("数据说明与实盘审计声明", live_report)
        self.assertNotIn("沙箱仿真不可替代真实大模型联网 API 实盘审计", live_report)
        self.assertIn("不作为企业财税审计、资产评估或法定会计记账凭证", live_report)

    def test_06_api_auth_and_404(self):
        """测试 API 未授权 401 拦截与 21 号报告不存在时返回 404"""
        from tools.geo.server import GeoWebHandler, create_session

        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json

        # 1. 未授权请求 GET /api/projects/{id}/mindshare/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/mindshare/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)
        self.assertIn("未登录", captured.get("payload", {}).get("message", ""))

        # 2. 未授权请求 POST /api/projects/{id}/mindshare/audit => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/mindshare/audit"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 带有效鉴权访问不存在 21 号报告的项目 => 404
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = "/api/projects/dummy_no_report_project/mindshare/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 404)
        self.assertIn("21 号报告尚未生成", captured.get("payload", {}).get("message", ""))

    def test_07_query_sampling_from_flat_queries(self):
        """测试 Query 采样优先读取 keywords_intent_matrix.json 的 flat_queries 真实字段 (闭环 Cursor 审查)"""
        from tools.geo.mindshare_auditor import _sample_business_queries

        # 1. 真实项目读取测试
        qs = _sample_business_queries(self.test_pid, limit=5)
        self.assertEqual(len(qs), 5)
        matrix_file = os.path.join(self.out_dir, "keywords_intent_matrix.json")
        with open(matrix_file, "r", encoding="utf-8") as f:
            mat = json.load(f)
            flat_set = set(mat.get("flat_queries", []))
        for q in qs:
            self.assertIn(q, flat_set, f"采样 Query 不属于 flat_queries 原句: {q}")

        # 2. 独立沙箱测试：验证当仅有 flat_queries 时精准采纳，绝不退化为 keywords 拼接
        dummy_pid = "temp_flat_queries_test"
        dummy_dir = os.path.join(PROJECTS_DIR, dummy_pid)
        dummy_out = os.path.join(dummy_dir, "outputs")
        os.makedirs(dummy_out, exist_ok=True)
        try:
            with open(os.path.join(dummy_dir, "project.yaml"), "w", encoding="utf-8") as f:
                f.write("keywords: ['应当被忽略的备用词项']\n")
            with open(os.path.join(dummy_out, "keywords_intent_matrix.json"), "w", encoding="utf-8") as f:
                json.dump({"flat_queries": ["专有商业意图Q1", "专有商业意图Q2", "专有商业意图Q3"]}, f)

            sampled = _sample_business_queries(dummy_pid, limit=3)
            self.assertEqual(sampled, ["专有商业意图Q1", "专有商业意图Q2", "专有商业意图Q3"])
            self.assertNotIn("应当被忽略的备用词项 哪家实力强选型推荐", sampled)
        finally:
            if os.path.exists(dummy_dir):
                shutil.rmtree(dummy_dir)


if __name__ == "__main__":
    unittest.main()
