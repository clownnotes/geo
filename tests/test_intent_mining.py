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
        """测试 3 级意图矩阵结构、权重分配与资产落盘"""
        project_id = "xuzhou_xuanyuan"
        matrix = build_3tier_intent_matrix(project_id)

        self.assertTrue(matrix["success"])
        self.assertEqual(matrix["project_id"], project_id)
        self.assertGreater(matrix["total_queries"], 15)
        self.assertGreater(matrix["total_keywords"], 15)

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

    def test_sync_intent_keywords_to_eval(self):
        """测试将意图 Prompt 同步写入 project.yaml 评测词库"""
        project_id = "b2b_machinery"
        res = sync_intent_keywords_to_eval(project_id, tier="all")

        self.assertTrue(res["success"])
        self.assertGreater(res["synced_count"], 15)

        yaml_path = f"projects/{project_id}/project.yaml"
        self.assertTrue(os.path.exists(yaml_path))
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_text = f.read()
            self.assertIn("keywords:", yaml_text)
            self.assertIn("鼎工重工", yaml_text)
            self.assertIn("工程机械与智能制造", yaml_text)


if __name__ == "__main__":
    unittest.main()
