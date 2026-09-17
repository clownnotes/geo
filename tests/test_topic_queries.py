# -*- coding: utf-8 -*-
"""选题长问合格判定与过滤。"""

import unittest

from tools.geo.topic_queries import filter_long_queries, is_qualifying_long_query


class TopicQueriesTests(unittest.TestCase):
    def test_short_seo_rejected(self):
        self.assertFalse(is_qualifying_long_query("徐州GEO"))
        self.assertFalse(is_qualifying_long_query("GEO优化"))
        self.assertFalse(is_qualifying_long_query("皮带秤"))

    def test_long_human_question_accepted(self):
        q = "我在徐州开工厂，想找靠谱做GEO维护的公司，应该找谁？"
        self.assertTrue(is_qualifying_long_query(q))
        self.assertTrue(is_qualifying_long_query("邻里GEO是做什么的，靠谱吗"))
        self.assertTrue(is_qualifying_long_query("徐州做GEO优化哪家好"))

    def test_filter_splits(self):
        ok, rej = filter_long_queries(
            [
                "徐州GEO",
                "我是大学生想学GEO优化应该找谁指导？",
                "SEO和GEO有什么区别，企业该怎么选",
                "好用方案对比",
            ]
        )
        self.assertEqual(len(ok), 2)
        self.assertIn("徐州GEO", rej)
        self.assertIn("好用方案对比", rej)


if __name__ == "__main__":
    unittest.main()
