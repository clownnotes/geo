# -*- coding: utf-8 -*-
"""
单元测试：分发台账智能回填、域名提取、去重与存活审计引擎 (tests/test_dist_bot_ledger.py)
"""

import os
import json
import unittest

from tools.geo.dist_bot import (
    parse_mixed_links,
    _calculate_metrics,
    batch_backfill_urls,
    get_distribution_ledger,
    render_ledger_markdown,
    save_ledger_and_markdown
)


class TestDistBotLedger(unittest.TestCase):

    def test_parse_mixed_links_domains(self):
        """测试从杂乱混合文本中准确提取 URL 并识别所属平台渠道"""
        mixed_text = """
        今天把客户的文章全部发布了，请查收：
        1. 今日头条：https://www.toutiao.com/article/7456789/
        2. 知乎专栏：https://zhuanlan.zhihu.com/p/8901234
        3. 微信公众号：https://mp.weixin.qq.com/s/abcdef123456
        4. GitHub 开源：https://github.com/company/repo
        5. Kimi 研报：https://kimi.moonshot.cn/chat/test1234
        6. 百度百科：https://baike.baidu.com/item/科技公司
        7. 外部垂直媒体：https://www.36kr.com/p/123456
        """
        items = parse_mixed_links(mixed_text)
        self.assertEqual(len(items), 7)

        channels = [it["channel"] for it in items]
        self.assertEqual(channels, ["toutiao", "zhihu", "wechat", "github", "kimi", "baidu", "custom"])

    def test_calculate_metrics_dual_rate(self):
        """测试填报完成率与真实存活率的双轨严格计算"""
        mock_channels = {
            "toutiao": {"weight_pct": 50, "url": "https://toutiao.com/1", "status": "verified"},
            "zhihu": {"weight_pct": 25, "url": "https://zhihu.com/1", "status": "published"},  # 已填报但未探活
            "wechat": {"weight_pct": 10, "url": "https://weixin.qq.com/1", "status": "failed"}, # 探活失败死链
            "github": {"weight_pct": 5, "url": "", "status": "pending"},                       # 未填报
            "kimi": {"weight_pct": 5, "url": "https://kimi.ai/1", "status": "verified"},
            "baidu": {"weight_pct": 5, "url": "", "status": "pending"},
            "juejin": {"weight_pct": 0, "url": "", "status": "pending"}
        }

        m = _calculate_metrics(mock_channels)
        self.assertEqual(m["total_channels"], 7)
        self.assertEqual(m["published_channels"], 4)  # toutiao, zhihu, wechat, kimi (4条有URL)
        self.assertEqual(m["alive_channels"], 2)      # toutiao, kimi (2条verified)
        self.assertEqual(m["dead_channels"], 1)       # wechat (1条failed)

        # 填报完成率：4 / 7 = 57.1%
        self.assertEqual(m["completion_rate_pct"], 57.1)
        # 加权填报完成率：(50 + 25 + 10 + 5) / 100 = 90.0%
        self.assertEqual(m["weighted_completion_pct"], 90.0)

        # 真实存活率：2 / 7 = 28.6%
        self.assertEqual(m["alive_rate_pct"], 28.6)
        # 加权真实存活率：(50 + 5) / 100 = 55.0%
        self.assertEqual(m["weighted_alive_pct"], 55.0)

    def test_batch_backfill_deduplication_and_custom(self):
        """测试批量回填去重、覆盖与 custom 链接隔离不抢占"""
        project_id = "xuzhou_xuanyuan"

        # 先重置为初始干净台账
        from tools.geo.dist_bot import save_ledger_and_markdown, DEFAULT_CHANNELS
        save_ledger_and_markdown(project_id, json.loads(json.dumps(DEFAULT_CHANNELS)), custom_links=[])

        # 首次回填 3 条（2 条标准渠道 + 1 条 custom 外部链接）
        raw1 = """
        头条: https://www.toutiao.com/article/111/
        知乎: https://zhuanlan.zhihu.com/p/222/
        未知媒体: https://www.36kr.com/p/999/
        """
        res1 = batch_backfill_urls(project_id, raw1, verify_now=False)
        self.assertTrue(res1["success"])
        self.assertEqual(res1["added_count"], 3)
        self.assertEqual(res1["duplicates"], 0)
        self.assertEqual(res1["overwritten"], 0)

        # 再次回填相同内容（完全重复）+ 1 个覆盖知乎的新链接
        raw2 = """
        头条: https://www.toutiao.com/article/111/
        知乎新链接: https://zhuanlan.zhihu.com/p/333/
        未知媒体: https://www.36kr.com/p/999/
        """
        res2 = batch_backfill_urls(project_id, raw2, verify_now=False)
        self.assertTrue(res2["success"])
        self.assertEqual(res2["duplicates"], 2)      # 头条和36氪重复跳过
        self.assertEqual(res2["overwritten"], 1)     # 知乎被新URL覆盖
        self.assertEqual(res2["added_count"], 0)

        # 验证 Markdown 台账落盘
        md_path = f"projects/{project_id}/outputs/04_全网分发渠道执行与存活台账.md"
        self.assertTrue(os.path.exists(md_path))
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
            self.assertIn("填报完成率", md_text)
            self.assertIn("真实存活率", md_text)
            self.assertIn("36kr.com", md_text)


if __name__ == "__main__":
    unittest.main()
