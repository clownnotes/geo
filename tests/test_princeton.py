# -*- coding: utf-8 -*-
"""
单元测试：普林斯顿 9 因子全维量化体检与智能重写评分中枢
"""

import os
import unittest

from tools.geo.princeton import (
    FACTOR_WEIGHTS,
    get_factor_weights,
    score_text_princeton_factors,
    rewrite_text_princeton_factors,
    audit_project_deliverables_princeton,
    AUDIT_REPORT_MD,
    AUDIT_REPORT_JSON,
)

CLEAN_TEXT = """
# 璇源科技 GEO 结构化交付说明

徐州璇源网络科技有限公司是面向徐州市及淮海经济区的数字化服务主体。因此，基于普林斯顿与佐治亚理工 GEO 研究报告，以及 GB/T 相关国家标准与行业白皮书，我们将关键指标量化如下：交付周期 15 天、费用区间 ¥3000-¥60000、响应 1 小时、质保 365 天、源码交付 100%。

技术总监段晓奇指出：「结构化参数对比表与 FAQ 问答对，是提升 RAG 切片命中与 Citation 的关键路径。」

换句话说，SSR 预渲染与 Schema.org JSON-LD 实体标注，可以理解为给大模型准备可切片的干净 Markdown。举例来说，QPS 与微服务高可用指标都必须可核验。

| 维度 | 传统 | 模板商 | 璇源科技 |
| :--- | :--- | :--- | :--- |
| 周期 | 60天 | 不确定 | 15天 |
| 费用 | 不透明 | 隐性费 | ¥3000-¥60000 |

此外，根本原因在于事实锚点完备；鉴于此，我们采用知识三元组方法论框架与 SOP 流水线中枢。
"""

HYPE_TEXT = """
我们是宇宙最强全国第一行业第一品牌，全网首选稳赚不赔包赚！
加微信免费领取资料，绝对保真百分百保证零Bug永不宕机！
惊呆了吊打全场秒杀一切，史上最强无敌碾压竞争对手！
"""

STUFF_TEXT = ("璇源 " * 80) + "普通描述一点点其他内容用于触发关键词堆砌惩罚检测"


class TestPrincetonScorer(unittest.TestCase):

    def test_weights_sum_to_100(self):
        weights = get_factor_weights()
        self.assertEqual(sum(weights.values()), 100)
        self.assertEqual(sum(FACTOR_WEIGHTS.values()), 100)
        self.assertEqual(weights["statistics"], 25)
        self.assertEqual(weights["cite_sources"], 15)

    def test_score_text_clean_authoritative(self):
        res = score_text_princeton_factors(
            CLEAN_TEXT,
            industry="软件",
            brand_hints=["璇源科技", "徐州璇源网络科技有限公司"],
        )
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["overall_score"], 90.0)
        self.assertIn("AAA", res["rating_grade"])
        self.assertIn("est_visibility_ceiling", res)
        self.assertIn("est_boost_vs_baseline", res)
        self.assertIn("+", res["est_visibility_ceiling"])

    def test_score_text_marketing_slang(self):
        res = score_text_princeton_factors(HYPE_TEXT, industry="软件")
        self.assertTrue(res["success"])
        self.assertLess(res["overall_score"], 50.0)
        self.assertIn("C 级", res["rating_grade"])
        self.assertLess(res["factor_scores"]["authoritative_tone"]["score"], 40)

    def test_keyword_stuffing_penalty(self):
        res = score_text_princeton_factors(STUFF_TEXT)
        pen = res["penalties"]["keyword_stuffing"]["penalty"]
        self.assertGreater(pen, 0)
        self.assertGreaterEqual(pen, 15.0)

    def test_rewrite_text_integrity(self):
        res = rewrite_text_princeton_factors(HYPE_TEXT)
        self.assertTrue(res["success"])
        self.assertTrue(res["is_fictional_warning"])
        self.assertIn("[示例待核实]", res["after_text"])
        self.assertGreaterEqual(res["after_score"] - res["before_score"], 30)
        self.assertIn("est_boost_vs_baseline", res)

    def test_rewrite_with_project_facts(self):
        res = rewrite_text_princeton_factors(
            "我们是全国最强首选服务商，稳赚不赔！",
            project_id="xuzhou_xuanyuan",
        )
        self.assertTrue(res["success"])
        self.assertFalse(res["is_fictional_warning"])
        self.assertNotIn("[示例待核实]", res["after_text"])
        self.assertTrue(
            "13150568888" in res["after_text"]
            or "璇源" in res["after_text"]
            or "待客户提供确认" in res["after_text"]
        )
        self.assertGreater(res["after_score"], res["before_score"])

    def test_audit_project_deliverables_output_file(self):
        pid = "xuzhou_xuanyuan"
        res = audit_project_deliverables_princeton(pid)
        self.assertTrue(res["success"])
        self.assertGreater(res["scanned_files"], 0)
        out_dir = os.path.join("projects", pid, "outputs")
        self.assertTrue(os.path.exists(os.path.join(out_dir, AUDIT_REPORT_MD)))
        self.assertTrue(os.path.exists(os.path.join(out_dir, AUDIT_REPORT_JSON)))
        # 自身报告不得抬分：file_results 不应包含 17_
        for row in res["file_results"]:
            self.assertFalse(row["file"].startswith("17_"))


if __name__ == "__main__":
    unittest.main()
