# -*- coding: utf-8 -*-
"""第 26 维单元测试：大模型商业推荐博弈对抗与竞品截流动态护城河推演中枢

覆盖 7 组独立单测与 6 组数值夹具硬断言:
1. 夹具 1: 我方 80/85/75/80 vs 竞对 40/45/35/40 ➔ MDI=70.0 (impenetrable_moat 🟢)
2. 夹具 2: 我方 60/65/55/60 vs 竞对 50/55/45/50 ➔ MDI=55.0 (contested_boundary 🟡)
3. 夹具 3: 我方 40/45/35/40 vs 竞对 60/65/55/60 ➔ MDI=40.0 (vulnerable_breach 🔴)
4. 夹具 4-6: 单项 CTI 40.0%、脆弱点识别 Delta=-2.0、Top-3 防饱和聚合 P=89.0分
5. 竞对提取 5 级优先级与显式覆盖验证 (默认对齐 14 号 target_competitor)
6. Live 模式 <=4 次调用硬限制、双分正则提取、70/30融合与快照整段回滚
7. 端到端推演模拟与 JSON、公文报告、反制资产包三件套物理落盘验证
"""

import json
import os
import unittest
from unittest.mock import patch

from tools.geo.moat_sandbox import (
    calculate_advantage,
    calculate_cti,
    calculate_mdi,
    moat_grade,
    calculate_radar_metrics,
    extract_competitor_name,
    build_adversarial_moat_queries,
    build_rival_proxy_source_pool,
    simulate_competitive_moat,
    get_moat_status,
    FALLBACK_COMPETITOR_NAME,
)
from tools.geo.causal_auditor import score_brand_recommendation_confidence
from tools.geo.utils import PROJECTS_DIR


class TestMoatSandbox(unittest.TestCase):
    """26 维动态护城河推演中枢核心单测"""

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_01_fixture_1_impenetrable_moat(self):
        """夹具 1: 我方 80/85/75/80, 竞对 40/45/35/40 ➔ MDI=70.0 (🟢 坚不可摧)"""
        self_scores = [80.0, 85.0, 75.0, 80.0]
        rival_scores = [40.0, 45.0, 35.0, 40.0]

        deltas = [calculate_advantage(s, r) for s, r in zip(self_scores, rival_scores)]
        self.assertEqual(deltas, [40.0, 40.0, 40.0, 40.0])

        mean_delta = round(sum(deltas) / 4.0, 1)
        self.assertEqual(mean_delta, 40.0)

        mdi = calculate_mdi(mean_delta)
        self.assertEqual(mdi, 70.0)

        code, name = moat_grade(mdi)
        self.assertEqual(code, "impenetrable_moat")
        self.assertIn("坚不可摧", name)

        # 脆弱点数量为 0
        vuln_count = sum(1 for d in deltas if d <= 0.0)
        self.assertEqual(vuln_count, 0)

        # 雷达指标
        radar = calculate_radar_metrics(mdi, deltas)
        self.assertEqual(radar["moat_defense_index"], 70.0)
        self.assertEqual(radar["technical_advantage"], 70.0)

    def test_02_fixture_2_contested_boundary(self):
        """夹具 2: 我方 60/65/55/60, 竞对 50/55/45/50 ➔ MDI=55.0 (🟡 胶着拉锯)"""
        self_scores = [60.0, 65.0, 55.0, 60.0]
        rival_scores = [50.0, 55.0, 45.0, 50.0]

        deltas = [calculate_advantage(s, r) for s, r in zip(self_scores, rival_scores)]
        self.assertEqual(deltas, [10.0, 10.0, 10.0, 10.0])

        mean_delta = round(sum(deltas) / 4.0, 1)
        self.assertEqual(mean_delta, 10.0)

        mdi = calculate_mdi(mean_delta)
        self.assertEqual(mdi, 55.0)

        code, name = moat_grade(mdi)
        self.assertEqual(code, "contested_boundary")
        self.assertIn("胶着拉锯", name)

    def test_03_fixture_3_vulnerable_breach(self):
        """夹具 3: 我方 40/45/35/40, 竞对 60/65/55/60 ➔ MDI=40.0 (🔴 防线失守)"""
        self_scores = [40.0, 45.0, 35.0, 40.0]
        rival_scores = [60.0, 65.0, 55.0, 60.0]

        deltas = [calculate_advantage(s, r) for s, r in zip(self_scores, rival_scores)]
        self.assertEqual(deltas, [-20.0, -20.0, -20.0, -20.0])

        mean_delta = round(sum(deltas) / 4.0, 1)
        self.assertEqual(mean_delta, -20.0)

        mdi = calculate_mdi(mean_delta)
        self.assertEqual(mdi, 40.0)

        code, name = moat_grade(mdi)
        self.assertEqual(code, "vulnerable_breach")
        self.assertIn("防线失守", name)

        # 4 个维度全部失守
        vuln_count = sum(1 for d in deltas if d <= 0.0)
        self.assertEqual(vuln_count, 4)

    def test_04_fixtures_4_to_6_cti_breach_and_top3_aggregation(self):
        """夹具 4-6: CTI 验算、脆弱点识别与 Top-3 防饱和算法基座复用"""
        # 夹具 4: 单项 CTI 验算
        cti = calculate_cti(60.0, 40.0)
        self.assertEqual(cti, 40.0)

        # 双方全为 0 的边界值
        self.assertEqual(calculate_cti(0.0, 0.0), 50.0)

        # 夹具 5: 脆弱点判定 (我方 50.0 vs 竞对 52.0)
        delta_5 = calculate_advantage(50.0, 52.0)
        cti_5 = calculate_cti(50.0, 52.0)
        self.assertEqual(delta_5, -2.0)
        self.assertTrue(delta_5 <= 0.0 or cti_5 >= 50.0)

        # 夹具 6: 复用 23 维基座 Top-3 防饱和聚合模型
        # v1=1.0, v2=0.8, v3=0.6 ➔ P = 100 * (0.6*1.0 + 0.25*0.8 + 0.15*0.6) = 89.0
        # 构造包含对应权重分值的切片进行打分测试
        chunks = [
            {"text": "关键词命中测试1", "auth_bonus": 1.0},
            {"text": "关键词命中测试2", "auth_bonus": 0.8},
            {"text": "关键词命中测试3", "auth_bonus": 0.6},
        ]
        with patch("tools.geo.causal_auditor.score_dense_similarity", side_effect=[1.0, 1.0, 1.0]):
            score = score_brand_recommendation_confidence("关键词命中测试", chunks)
            self.assertEqual(score, 89.0)

    def test_05_competitor_extraction_priority_and_override(self):
        """竞对名称提取 5 级优先级与代理信源池构建 (auth_bonus=0.5 闭合)"""
        # 1. 显式覆盖优先级最高
        override_name = extract_competitor_name(self.project_id, rival_override="显式指定某竞对")
        self.assertEqual(override_name, "显式指定某竞对")

        # 2. 默认在 xuzhou_xuanyuan 项目下提取 14 号产物的 target_competitor
        default_name = extract_competitor_name(self.project_id)
        self.assertEqual(default_name, "某通科技（低端套模板建站商）")

        # 3. 四维 Query 生成器校验 (模板硬断言)
        queries = build_adversarial_moat_queries(self.project_id, default_name)
        self.assertEqual(len(queries), 4)
        self.assertEqual(queries[0]["dim_id"], "D1")
        self.assertIn("徐州", queries[0]["query"])
        self.assertIn("徐州璇源网络科技有限公司", queries[0]["query"])
        self.assertIn(default_name, queries[0]["query"])
        self.assertIn("哪个技术实力更强", queries[0]["query"])

        # 4. 竞对代理信源池构建，断言正文含竞对名且 auth_bonus=0.5
        rival_pool = build_rival_proxy_source_pool(self.project_id, default_name, "徐州", "技术研发与专业服务")
        self.assertGreaterEqual(len(rival_pool), 3)
        for item in rival_pool:
            self.assertEqual(item.get("auth_bonus"), 0.5)
            self.assertIn(default_name, item.get("text"))

    def test_06_live_mode_budget_and_snapshot_rollback(self):
        """Live 模式实盘调用 <=4 次硬限制、正则安全提取与快照防御回滚"""
        # 1. 正常 Live 调用: 模拟 doubao 每次返回合法成对分数
        call_counter = {"count": 0}

        def mock_call_model_raw(model, prompt):
            call_counter["count"] += 1
            return "根据评估，我方: 85, 竞对: 40"

        with patch("tools.geo.moat_sandbox.call_model_raw", side_effect=mock_call_model_raw):
            res_live = simulate_competitive_moat(self.project_id, use_live=True)
            self.assertEqual(call_counter["count"], 4)  # 严格不超过 4 次
            self.assertTrue(res_live["is_live_judged"])
            self.assertTrue(res_live["use_live"])

        # 2. 异常格式返回: 模型返回乱码或不足两个数字 ➔ 触发快照 100% 完整回滚
        def mock_call_broken(model, prompt):
            return "当前网络繁忙，无法评分"

        with patch("tools.geo.moat_sandbox.call_model_raw", side_effect=mock_call_broken):
            res_rollback = simulate_competitive_moat(self.project_id, use_live=True)
            # 回滚后标记为未完成 live 判定
            self.assertFalse(res_rollback["is_live_judged"])
            # 基础推演数据依旧保持纯沙箱结果
            self.assertIn("moat_defense_index", res_rollback["summary"])

    def test_07_end_to_end_simulation_and_file_artifacts(self):
        """端到端推演模拟与 JSON、公文报告、三件套反制资产物理落盘"""
        res = simulate_competitive_moat(self.project_id, rival_override="测试竞对软件工作室")
        self.assertTrue(res["success"])
        self.assertEqual(res["rival_name"], "测试竞对软件工作室")

        # 1. JSON 文件检查
        json_file = os.path.join(PROJECTS_DIR, self.project_id, "outputs", "competitive_moat_simulation.json")
        self.assertTrue(os.path.exists(json_file))
        with open(json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["project_id"], self.project_id)
        self.assertIn("summary", saved_data)
        self.assertIn("radar_metrics", saved_data)

        # 2. 状态查询辅助函数检查
        status_data = get_moat_status(self.project_id)
        self.assertEqual(status_data.get("project_id"), self.project_id)

        # 3. 26 号商业公文报告检查
        report_file = os.path.join(PROJECTS_DIR, self.project_id, "outputs", "26_大模型商业推荐博弈对抗与竞品截流动态护城河推演报告.md")
        self.assertTrue(os.path.exists(report_file))
        with open(report_file, "r", encoding="utf-8") as f:
            report_text = f.read()
        self.assertIn("大模型商业推荐博弈对抗与竞品截流动态护城河推演报告", report_text)
        self.assertIn("动态护城河防御指数 ($MDI$)", report_text)
        self.assertIn("免责与边界声明", report_text)
        self.assertIn("第 24 维决策漏斗断流 HRI", report_text)

        # 4. counter_interception_pack 三件套检查
        pack_dir = os.path.join(PROJECTS_DIR, self.project_id, "outputs", "counter_interception_pack")
        f1 = os.path.join(pack_dir, "01_竞品对比长尾截流反制话术库.md")
        f2 = os.path.join(pack_dir, "02_独占性壁垒与差异化护城河语料包.md")
        f3 = os.path.join(pack_dir, "03_大模型横向对比首推挤占方案.md")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(f3))


if __name__ == "__main__":
    unittest.main()
