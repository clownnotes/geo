# -*- coding: utf-8 -*-
"""
单元测试：大模型爬虫抓取仿真与 RAG 分块检索命中诊断中枢 (tests/test_crawler_rag_diag.py)
"""

import os
import unittest
from tools.geo.crawler import html_to_clean_markdown, simulate_crawler_fetch, is_ssrf_safe_url
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

    def test_ssrf_safety_protection(self):
        """测试 SSRF 内网私有地址拦截"""
        # 拦截 192.168.1.1
        safe, msg = is_ssrf_safe_url("http://192.168.1.1/admin")
        self.assertFalse(safe)
        self.assertIn("安全策略拦截", msg)

        # 拦截 10.0.0.1
        safe, msg = is_ssrf_safe_url("http://10.0.0.1:8080")
        self.assertFalse(safe)

        # 允许外部合法公网 URL
        safe, _ = is_ssrf_safe_url("https://example.com/test")
        self.assertTrue(safe)

    def test_simulate_crawler_fetch_warnings_and_structure(self):
        """测试爬虫仿真器结构返回与 SPA 警告"""
        # 测试无效地址返回
        res = simulate_crawler_fetch("http://192.168.1.55/test", spider_type="bytespider", timeout=1)
        self.assertFalse(res["success"])
        self.assertEqual(res["spider_type"], "bytespider")
        self.assertIn("Bytespider", res["user_agent"])
        self.assertGreaterEqual(len(res["warnings"]), 1)

    def test_score_single_chunk_boundaries(self):
        """测试单个 Chunk 评分与黄金块判定"""
        prof = {
            "company_name": "徐州璇源",
            "brand_name": "璇源科技",
            "founder": "段晓奇",
            "differences": ["365天质保", "100%移交"]
        }
        # 黄金块样例
        golden_chunk = {
            "chunk_id": 1,
            "tokens": 300,
            "chars": 500,
            "text": "【璇源科技】创始人段晓奇承诺：提供 365天 免费质保与 100% 源码交付。\n\n| 项目 | 优势 |\n| --- | --- |\n| 价格 | 透明 |\n\n### Q1：价格怎么样？\n答：公开透明。"
        }
        sc = score_single_chunk(golden_chunk, prof)
        self.assertGreaterEqual(sc["score"], 80)
        self.assertIn("黄金", sc["grade"])
        self.assertTrue(sc["has_table"])
        self.assertTrue(sc["has_faq"])
        self.assertIn("璇源科技", sc["entity_hits"])

        # 稀疏块样例
        sparse_chunk = {
            "chunk_id": 2,
            "tokens": 100,
            "chars": 150,
            "text": "这是一家致力于为广大客户提供优质服务的团队，欢迎咨询合作。"
        }
        sc2 = score_single_chunk(sparse_chunk, prof)
        self.assertLess(sc2["score"], 60)
        self.assertIn("稀疏", sc2["grade"])

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
        """测试四大母版项目的 RAG 切片体检与资产落盘"""
        for pid in ["xuzhou_xuanyuan", "b2b_machinery", "retail_catering", "local_legal"]:
            diag = diagnose_rag_chunks(pid, run_crawler=False)

            self.assertTrue(diag["success"])
            self.assertEqual(diag["project_id"], pid)
            self.assertGreater(diag["total_chunks"], 0)
            self.assertGreaterEqual(diag["rag_readiness_score"], 60.0)
            self.assertGreaterEqual(diag["entity_coverage_pct"], 40.0)
            self.assertIn("table_preservation_pct", diag)
            self.assertIn("qa_pairs_count", diag)

            # 验证落盘文件存在
            json_file = f"projects/{pid}/outputs/rag_chunks_diagnostic.json"
            md_file = f"projects/{pid}/outputs/12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md"
            self.assertTrue(os.path.exists(json_file))
            self.assertTrue(os.path.exists(md_file))

            with open(md_file, "r", encoding="utf-8") as f:
                md_text = f.read()
                self.assertIn("RAG 分块检索诊断报告", md_text)
                self.assertIn("大模型爬虫抓取仿真可见度体检", md_text)
                self.assertIn("RAG 切片核心量化指标大盘", md_text)
                self.assertIn("Chunk #1", md_text)


if __name__ == "__main__":
    unittest.main()
