# -*- coding: utf-8 -*-
"""
单元测试：大模型 Citation 信源权威度权重评分与外链信任度推演中枢 (tests/test_citation_authority.py)
"""

import os
import unittest
from tools.geo.citation_authority import (
    CHANNEL_AUTHORITY_DB,
    score_single_backlink,
    evaluate_project_citation_authority,
    _load_backlinks_from_ledger,
)
from tools.geo.utils import load_project_config


class TestCitationAuthority(unittest.TestCase):

    def test_channel_authority_db_structure(self):
        """测试基础渠道库五大模型生态亲和度完整性"""
        required_channels = ["toutiao", "zhihu", "wechat", "github", "baijiahao", "kimi", "official"]
        required_models = ["doubao", "deepseek", "yuanbao", "kimi", "baidu"]

        for ch in required_channels:
            self.assertIn(ch, CHANNEL_AUTHORITY_DB)
            info = CHANNEL_AUTHORITY_DB[ch]
            self.assertIn("domain_authority", info)
            self.assertIn("affinity", info)
            for m in required_models:
                self.assertIn(m, info["affinity"])
                self.assertGreaterEqual(info["affinity"][m], 50.0)
                self.assertLessEqual(info["affinity"][m], 100.0)

    def test_score_single_backlink_live_and_dead(self):
        """测试单条外链存活与死链权威分惩罚机制"""
        # 存活链
        live_link = {
            "channel": "zhihu",
            "url": "https://zhuanlan.zhihu.com/p/123",
            "title": "技术选型长文",
            "status_code": 200,
            "latency_ms": 120
        }
        res_live = score_single_backlink(live_link)
        self.assertTrue(res_live["is_live"])
        self.assertGreaterEqual(res_live["domain_authority"], 90.0)
        self.assertGreater(res_live["estimated_citation_rate"], 85.0)
        self.assertIn("DeepSeek", res_live["best_fit_models"][0])

        # 死链
        dead_link = {
            "channel": "zhihu",
            "url": "https://zhuanlan.zhihu.com/p/404",
            "title": "失效链接",
            "status_code": 404,
            "latency_ms": 2000
        }
        res_dead = score_single_backlink(dead_link)
        self.assertFalse(res_dead["is_live"])
        self.assertLess(res_dead["domain_authority"], 30.0)

    def test_load_backlinks_from_dist_ledger(self):
        """应从 dist_ledger.json channels/custom_links 读取真实外链，而非空 links 数组"""
        cfg = load_project_config("xuzhou_xuanyuan")
        links = _load_backlinks_from_ledger("xuzhou_xuanyuan", cfg, cfg["brand_name"], cfg["company_name"], cfg.get("industry", ""))
        self.assertGreaterEqual(len(links), 3)
        urls = [l["url"] for l in links]
        self.assertTrue(any("toutiao.com" in u for u in urls))
        self.assertTrue(any("zhihu.com" in u for u in urls))
        self.assertTrue(any("geo.baicl.cc" in u for u in urls))

    def test_baidu_channel_alias_maps_to_baijiahao(self):
        """台账 baidu 渠道应映射到 baijiahao 权威库"""
        res = score_single_backlink({
            "channel": "baidu",
            "url": "https://baijiahao.baidu.com/s?id=123",
            "title": "百科词条",
            "status_code": 200,
            "latency_ms": 120,
        })
        self.assertEqual(res["channel"], "baijiahao")
        self.assertGreater(res["affinities"]["baidu"], 95.0)

    def test_evaluate_project_citation_authority_benchmark(self):
        """测试四大母版项目信源权威评估与资产落盘"""
        for pid in ["xuzhou_xuanyuan", "b2b_machinery", "retail_catering", "local_legal"]:
            res = evaluate_project_citation_authority(pid)

            self.assertTrue(res["success"])
            self.assertEqual(res["project_id"], pid)
            self.assertGreater(res["overall_authority_score"], 70.0)
            self.assertGreater(res["estimated_citation_rate"], 70.0)
            if pid == "xuzhou_xuanyuan":
                self.assertGreaterEqual(res["total_backlinks"], 3)
            self.assertIn("model_affinity_summary", res)
            self.assertEqual(len(res["model_affinity_summary"]), 5)

            # 验证落盘文件
            json_file = f"projects/{pid}/outputs/citation_authority_matrix.json"
            md_file = f"projects/{pid}/outputs/15_大模型Citation信源权威度与外链信任度评分报告.md"
            self.assertTrue(os.path.exists(json_file))
            self.assertTrue(os.path.exists(md_file))

            with open(md_file, "r", encoding="utf-8") as f:
                md_text = f.read()
                self.assertIn("大模型 Citation 信源权威度与外链信任度评分报告", md_text)
                self.assertIn("五大本土大模型生态亲和度大盘", md_text)
                self.assertIn("全渠道落地外链权威度明细表", md_text)
                self.assertIn("全案信源提权与提效行动指南", md_text)


if __name__ == "__main__":
    unittest.main()
