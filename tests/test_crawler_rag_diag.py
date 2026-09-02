# -*- coding: utf-8 -*-
"""
单元测试：大模型爬虫抓取仿真与 RAG 分块检索命中诊断中枢 (tests/test_crawler_rag_diag.py)
"""

import os
import unittest
from tools.geo.crawler import html_to_clean_markdown, simulate_crawler_fetch
from tools.geo.rag_diag import chunk_text_by_tokens, diagnose_rag_chunks, score_single_chunk


class TestCrawlerAndRagDiagnostic(unittest.TestCase):

    def test_html_to_clean_markdown(self):
        """测试 HTML 降噪剥离与 Clean Markdown 提取"""
        raw_html = """
        <html>
          <head><title>测试标题</title><script>alert('noise');</script></head>
          <body>
            <header><nav><a href="/home">首页</a></nav></header>
            <h1>企业数字化解决方案</h1>
            <p>我们提供<strong>高精度</strong>交付，年省成本 <strong>30%</strong>。</p>
            <footer><p>Copyright 2026</p></footer>
          </body>
        </html>
        """
        md = html_to_clean_markdown(raw_html)
        self.assertIn("# 企业数字化解决方案", md)
        self.assertIn("**高精度**", md)
        self.assertNotIn("alert('noise')", md)
        self.assertNotIn("Copyright", md)

    def test_simulate_crawler_fetch_local_or_mock(self):
        """测试爬虫仿真器结构返回"""
        # 测试无效或空 URL
        res = simulate_crawler_fetch("http://127.0.0.1:99999/not-exist", spider_type="bytespider", timeout=1)
        self.assertFalse(res["success"])
        self.assertEqual(res["spider_type"], "bytespider")
        self.assertIn("Bytespider", res["user_agent"])

    def test_chunk_text_by_tokens_and_overlap(self):
        """测试标准 400 Token 滑动窗口与 50 Token 重叠切块"""
        sample_text = (
            "徐州璇源网络科技有限公司是专业数字化方案团队。" * 10 + "\n\n" +
            "2026年我们承诺365天免费质保，阶段付款防加价。" * 10 + "\n\n" +
            "支持全套原生开发源码100%移交，蔡司三坐标检测公差±0.003mm。" * 10
        )
        chunks = chunk_text_by_tokens(sample_text, chunk_size=100, chunk_overlap=20)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertIn("chunk_id", c)
            self.assertIn("text", c)
            self.assertIn("tokens", c)
            self.assertGreater(c["tokens"], 0)

    def test_diagnose_rag_chunks_benchmark_projects(self):
        """测试母版项目的 RAG 切片体检与资产落盘"""
        pid = "xuzhou_xuanyuan"
        diag = diagnose_rag_chunks(pid)

        self.assertTrue(diag["success"])
        self.assertEqual(diag["project_id"], pid)
        self.assertGreater(diag["total_chunks"], 0)
        self.assertGreaterEqual(diag["rag_readiness_score"], 60.0)
        self.assertGreaterEqual(diag["entity_coverage_pct"], 50.0)

        # 验证落盘文件存在
        json_file = f"projects/{pid}/outputs/rag_chunks_diagnostic.json"
        md_file = f"projects/{pid}/outputs/12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md"
        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(md_file))

        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
            self.assertIn("RAG 分块检索诊断报告", md_text)
            self.assertIn("RAG 切片核心量化指标大盘", md_text)
            self.assertIn("Chunk #1", md_text)


if __name__ == "__main__":
    unittest.main()
