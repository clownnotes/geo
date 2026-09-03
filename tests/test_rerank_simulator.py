# -*- coding: utf-8 -*-
"""跨大模型 RAG 混合检索召回与重排序挤占演习沙盘单元测试套件 (tests/test_rerank_simulator.py)

强断言覆盖：
1. 5 组固定数值夹具 (CPR 三档、Cross-Encoder 77.0分与 COR 80.0%)；
2. Dense 字符 2-gram 余弦模拟与 BM25 词频超参闭环；
3. Query 采样严格优先读取 flat_queries 真实字段；
4. 沙箱演习全流程、JSON 大盘与 22 号公文报告物理落盘 (含沙箱免责与技术演练说明)；
5. outputs/rerank_reinforcement_pack/ 下 3 份强化文件物理存在；
6. Live 模式下自适应实盘审计声明；
7. API 401 鉴权拦截与未生成报告 404 语义。
"""

import json
import os
import shutil
import unittest

from tools.geo.rerank_simulator import (
    score_dense_similarity,
    score_sparse_bm25,
    calculate_rrf_rankings,
    score_cross_encoder_rerank,
    calculate_cpr,
    calculate_cor,
    rerank_grade,
    simulate_rag_rerank_competition,
    generate_rerank_reinforcement_pack,
    generate_rerank_report_markdown,
    _sample_business_queries,
)
from tools.geo.utils import PROJECTS_DIR


class TestRerankSimulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pid = "xuzhou_xuanyuan"
        cls.out_dir = os.path.join(PROJECTS_DIR, cls.test_pid, "outputs")

    def test_01_fixture_assertions(self):
        """测试 5 组固定数值夹具强断言 (CPR 三档、Rerank 77.0分与 COR 80.0%)"""
        # 夹具 1: N_my=12, T_slots=15 => CPR = 80.0% (full_penetration)
        cpr1 = calculate_cpr(12, 15)
        g1_code, g1_name = rerank_grade(cpr1)
        self.assertEqual(cpr1, 80.0)
        self.assertEqual(g1_code, "full_penetration")

        # 夹具 2: N_my=10, T_slots=15 => CPR = 66.7% (partial_contention)
        cpr2 = calculate_cpr(10, 15)
        g2_code, g2_name = rerank_grade(cpr2)
        self.assertEqual(cpr2, 66.7)
        self.assertEqual(g2_code, "partial_contention")

        # 夹具 3: N_my=7, T_slots=15 => CPR = 46.7% (severe_dropout)
        cpr3 = calculate_cpr(7, 15)
        g3_code, g3_name = rerank_grade(cpr3)
        self.assertEqual(cpr3, 46.7)
        self.assertEqual(g3_code, "severe_dropout")

        # 夹具 4: S_dense=0.8, S_sparse=0.6, AuthBonus=1.0 => S_rerank = 77.0 分 (闭环 P0-2)
        score4 = score_cross_encoder_rerank(0.8, 0.6, 1.0)
        self.assertEqual(score4, 77.0)

        # 夹具 5: N_ousted=8, N_comp_candidates=10 => COR = 80.0% (闭环 P0-1)
        cor5 = calculate_cor(8, 10)
        self.assertEqual(cor5, 80.0)

    def test_02_dense_and_sparse_algorithms(self):
        """测试 Dense 余弦与 Sparse BM25 算法基础性质"""
        q = "徐州软件定制开发哪家实力强"
        doc_hit = "徐州璇源网络科技有限公司专业从事徐州软件定制开发，技术实力雄厚"
        doc_miss = "今天天气晴朗，非常适合户外散步和野餐"

        # Dense 相似度
        s_dense_hit = score_dense_similarity(q, doc_hit)
        s_dense_miss = score_dense_similarity(q, doc_miss)
        self.assertGreater(s_dense_hit, 0.3)
        self.assertLess(s_dense_miss, 0.1)

        # BM25 词频
        s_bm25_hit = score_sparse_bm25(q, doc_hit)
        s_bm25_miss = score_sparse_bm25(q, doc_miss)
        self.assertGreater(s_bm25_hit, s_bm25_miss)

        # RRF 倒数融合
        rrf = calculate_rrf_rankings([0.8, 0.2], [0.7, 0.3])
        self.assertEqual(len(rrf), 2)
        self.assertGreater(rrf[0], rrf[1])

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
        """测试沙箱演习、JSON 大盘与 22 号公文报告物理落盘与免责声明"""
        res = simulate_rag_rerank_competition(
            project_id=self.test_pid,
            models=["doubao", "deepseek", "kimi"],
            query_sample_size=5,
            use_live=False,
        )
        self.assertTrue(res["success"])
        s = res["summary"]
        self.assertGreaterEqual(s["cpr"], 0.0)
        self.assertLessEqual(s["cpr"], 100.0)
        self.assertIn(s["grade_code"], ["full_penetration", "partial_contention", "severe_dropout"])
        self.assertEqual(s["total_slots"], 15)

        # 校验 JSON 落盘 (严格区分于 12 号诊断文件)
        json_path = os.path.join(self.out_dir, "rag_rerank_simulation.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertEqual(d["project_id"], self.test_pid)
            self.assertIn("radar_metrics", d)
            self.assertIn("query_rerank_details", d)

        # 校验 22 号 Markdown 报告落盘
        report_path = os.path.join(self.out_dir, "22_跨大模型RAG混合检索召回与重排序挤占演习报告.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn("跨大模型 RAG 混合检索召回与重排序挤占演习报告", md_content)
            self.assertIn("沙箱仿真不可替代真实大模型联网 API 实盘审计", md_content)
            self.assertIn("各大模型内部权重参数受版本动态迭代影响", md_content)

    def test_05_generate_reinforcement_pack(self):
        """测试 outputs/rerank_reinforcement_pack/ 下 3 份强化文案物理生成"""
        pack = generate_rerank_reinforcement_pack(self.test_pid)
        self.assertTrue(pack["success"])
        files = pack.get("files", [])
        self.assertEqual(len(files), 3)
        for fp in files:
            self.assertTrue(os.path.exists(fp), f"强化文件未生成: {fp}")

        pack_dir = os.path.join(self.out_dir, "rerank_reinforcement_pack")
        f1 = os.path.join(pack_dir, "01_Dense密集语义增强与长尾Prompt锚点对齐清单.md")
        f2 = os.path.join(pack_dir, "02_BM25高频稀疏关键词注入与拓扑优化切片草稿.md")
        f3 = os.path.join(pack_dir, "03_Top3黄金上下文穿透力防御与重排序加固方案.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))

    def test_06_live_report_declaration_adaptive(self):
        """测试 Live 模式下自适应切换实盘审计声明"""
        mock_live_data = {
            "client_name": "测试企业",
            "project_id": "test_live_prj",
            "timestamp": "2026-09-03 05:00:00",
            "use_live": True,
            "summary": {
                "cpr": 93.3,
                "cor": 90.0,
                "grade_name": "🟢 全面穿透 (Full Penetration)",
                "total_queries": 5,
                "total_slots": 15,
                "my_slots_won": 14,
                "comp_slots_ousted": 9,
                "comp_candidates_total": 10,
                "avg_rerank_score": 85.0,
            },
            "radar_metrics": {},
            "query_rerank_details": [],
        }
        live_report = generate_rerank_report_markdown(mock_live_data)
        self.assertIn("数据说明与实盘审计声明", live_report)
        self.assertNotIn("沙箱仿真不可替代真实大模型联网 API 实盘审计", live_report)
        self.assertIn("各大模型内部权重参数受版本动态迭代影响", live_report)

    def test_07_api_auth_and_404(self):
        """测试 API 未授权 401 拦截与报告不存在返回 404"""
        from tools.geo.server import GeoWebHandler, create_session

        captured = {}

        def capture_json(payload, status=200, headers=None):
            captured["payload"] = payload
            captured["status"] = status

        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.send_json = capture_json

        # 1. 未授权请求 GET /api/projects/{id}/rerank/status => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/rerank/status"
        handler.headers = {}
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 401)

        # 2. 未授权请求 POST /api/projects/{id}/rerank/simulate => 401
        captured.clear()
        handler.path = f"/api/projects/{self.test_pid}/rerank/simulate"
        handler.headers = {}
        GeoWebHandler.do_POST(handler)
        self.assertEqual(captured.get("status"), 401)

        # 3. 带有效鉴权访问不存在 22 号报告的项目 => 404
        valid_token = create_session("admin")
        captured.clear()
        handler.headers = {"Authorization": f"Bearer {valid_token}"}
        handler.path = "/api/projects/dummy_no_rerank_project/rerank/report"
        GeoWebHandler.do_GET(handler)
        self.assertEqual(captured.get("status"), 404)
        self.assertIn("22 号报告尚未生成", captured.get("payload", {}).get("message", ""))

    def test_08_bm25_pool_max_normalization_and_live_judge_injection(self):
        """测试 BM25 全池 max 归一化与 live 模式下 Judge 裁决分注入精排打分 (闭环 Cursor 审查)"""
        from unittest.mock import patch
        from tools.geo.rerank_simulator import RerankSandboxSimulator, score_sparse_bm25_raw

        # 1. 验证 BM25 全池 max 归一化
        q = "直营团队软件定制开发"
        candidates = [
            {"id": "c1", "owner": "my", "title": "直营团队", "text": "直营团队软件定制开发交付有保障", "auth_bonus": 1.0},
            {"id": "c2", "owner": "competitor", "title": "泛行业", "text": "行业资讯与新闻概览", "auth_bonus": 0.3},
        ]
        raw1 = score_sparse_bm25_raw(q, candidates[0]["text"])
        raw2 = score_sparse_bm25_raw(q, candidates[1]["text"])
        self.assertGreater(raw1, raw2)

        # 2. 验证纯沙箱模式精排得分
        res_sandbox = RerankSandboxSimulator.simulate_query_rerank(q, candidates, use_live=False)
        self.assertFalse(res_sandbox["is_live_judged"])
        c1_score_sandbox = res_sandbox["top3"][0]["rerank_score"]

        # 3. 验证 live 模式下 Mock 大模型裁判给出高分 95 分，精排得分被成功融合修正
        with patch("tools.geo.rerank_simulator.call_model_raw", return_value="评分结果: 95 分"):
            res_live = RerankSandboxSimulator.simulate_query_rerank(
                q, candidates, use_live=True, live_model="doubao"
            )
            self.assertTrue(res_live["is_live_judged"])
            c1_score_live = res_live["top3"][0]["rerank_score"]
            expected_score = round(0.7 * c1_score_sandbox + 0.3 * 95.0, 1)
            self.assertEqual(c1_score_live, expected_score)

        # 4. 验证 live 模式下若大模型调用异常，平滑回退纯沙箱且 is_live_judged 为 False
        with patch("tools.geo.rerank_simulator.call_model_raw", side_effect=RuntimeError("API 超时")):
            res_fallback = RerankSandboxSimulator.simulate_query_rerank(
                q, candidates, use_live=True, live_model="doubao"
            )
            self.assertFalse(res_fallback["is_live_judged"])
            self.assertEqual(res_fallback["top3"][0]["rerank_score"], c1_score_sandbox)


if __name__ == "__main__":
    unittest.main()
