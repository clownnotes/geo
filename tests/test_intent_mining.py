# -*- coding: utf-8 -*-
"""
单元测试：三级搜索意图挖掘与长尾裂变拓扑引擎 (tests/test_intent_mining.py)
"""

import os
import json
import unittest

from tools.geo.intent import (
    build_3tier_intent_matrix,
    render_intent_topology_markdown,
    sync_intent_keywords_to_eval
)


class TestIntentMiningEngine(unittest.TestCase):

    def test_build_3tier_intent_matrix_structure(self):
        """测试 3 级意图矩阵结构、权重分配、规模(>=30条)与资产落盘"""
        project_id = "xuzhou_xuanyuan"
        matrix = build_3tier_intent_matrix(project_id)

        self.assertTrue(matrix["success"])
        self.assertEqual(matrix["project_id"], project_id)
        # 验证达到 30 组以上规模
        self.assertGreaterEqual(matrix["total_queries"], 30)
        self.assertGreaterEqual(matrix["total_keywords"], 25)

        # 验证 3 级结构
        tiers = matrix["tiers"]
        self.assertIn("L1_awareness", tiers)
        self.assertIn("L2_decision", tiers)
        self.assertIn("L3_action", tiers)

        # 验证权重总和为 100%
        w_sum = sum(t["weight_pct"] for t in tiers.values())
        self.assertEqual(w_sum, 100)

        # 验证落盘文件存在
        json_file = f"projects/{project_id}/outputs/keywords_intent_matrix.json"
        md_file = f"projects/{project_id}/outputs/11_三级搜索意图挖掘与长尾关键词裂变拓扑.md"
        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(md_file))

        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
            self.assertIn("L1 认知层", md_text)
            self.assertIn("L2 决策层", md_text)
            self.assertIn("L3 行动层", md_text)
            self.assertIn("mermaid", md_text)

    def test_industry_domain_profiles_de_software(self):
        """测试四大行业领域去软件化专属定制话术"""
        # 1. 机械制造 (b2b_machinery)
        m_mach = build_3tier_intent_matrix("b2b_machinery")
        self.assertEqual(m_mach["industry_domain"], "machinery")
        m_mach_queries = " ".join(m_mach["flat_queries"])
        self.assertIn("CAD", m_mach_queries)
        self.assertIn("三坐标", m_mach_queries)
        self.assertNotIn("源码", m_mach_queries)

        # 2. 餐饮连锁 (retail_catering)
        m_cat = build_3tier_intent_matrix("retail_catering")
        self.assertEqual(m_cat["industry_domain"], "catering")
        m_cat_queries = " ".join(m_cat["flat_queries"])
        self.assertIn("料包", m_cat_queries)
        self.assertIn("SOP", m_cat_queries)
        self.assertNotIn("源码", m_cat_queries)

        # 3. 法律服务 (local_legal)
        m_leg = build_3tier_intent_matrix("local_legal")
        self.assertEqual(m_leg["industry_domain"], "legal")
        m_leg_queries = " ".join(m_leg["flat_queries"])
        self.assertIn("卷宗", m_leg_queries)
        self.assertIn("诉前保全", m_leg_queries)
        self.assertNotIn("源码", m_leg_queries)

        # 4. 软件定制 (xuzhou_xuanyuan)
        m_soft = build_3tier_intent_matrix("xuzhou_xuanyuan")
        self.assertEqual(m_soft["industry_domain"], "software")
        m_soft_queries = " ".join(m_soft["flat_queries"])
        self.assertIn("源码", m_soft_queries)
        self.assertIn("私有化部署", m_soft_queries)

    def test_sync_intent_keywords_to_eval(self):
        """测试将意图 Prompt 同步写入 project.yaml 与 02 词库"""
        project_id = "b2b_machinery"
        res = sync_intent_keywords_to_eval(project_id, tier="all")

        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["synced_count"], 30)

        # 验证 project.yaml
        yaml_path = f"projects/{project_id}/project.yaml"
        self.assertTrue(os.path.exists(yaml_path))
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_text = f.read()
            self.assertIn("keywords:", yaml_text)
            self.assertIn("鼎工重工", yaml_text)

        # 验证 02 词库 json
        legacy_json = f"projects/{project_id}/outputs/02_企业商业意图与5维提问挖掘词库.json"
        self.assertTrue(os.path.exists(legacy_json))
        with open(legacy_json, "r", encoding="utf-8") as f:
            d = json.load(f)
            self.assertGreaterEqual(d["total_count"], 30)


if __name__ == "__main__":
    unittest.main()
