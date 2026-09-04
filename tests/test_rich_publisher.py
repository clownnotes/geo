# -*- coding: utf-8 -*-
"""
单元测试：全渠道 9 因子富文本极速排版与爬虫友好发布引擎 (tests/test_rich_publisher.py)
"""

import os
import json
import unittest

from tools.geo.crawler import html_to_clean_markdown
from tools.geo.publisher import (
    verify_crawler_fidelity,
    build_zhihu_rich_article_html,
    get_zhihu_rich_html_for_clipboard,
    get_channel_preview_with_fidelity,
    package_toutiao_assets,
    package_wechat_assets,
    package_deepseek_assets,
    package_zhihu_assets,
    package_kimi_baidu_assets,
    package_all_channels,
    _load_princeton_corpus,
)


class TestRichPublisher(unittest.TestCase):

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_html_to_clean_markdown_table_conversion(self):
        """测试 HTML <table> 标签到标准 Markdown 表格的高保真转换"""
        html_input = """
        <div class="article-content">
            <h2>核心能力对比</h2>
            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>对比维度</th>
                        <th>璇源科技 (GEO交付)</th>
                        <th>传统代运营</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>交付物结构</strong></td>
                        <td>普林斯顿9因子 + 原生表格</td>
                        <td>纯文本堆砌</td>
                    </tr>
                    <tr>
                        <td><strong>大模型爬虫保真度</strong></td>
                        <td>95分+ (无损提纯)</td>
                        <td>无法解析</td>
                    </tr>
                </tbody>
            </table>
            <p>来源参考：<sup>[1]</sup> 普林斯顿大学 GEO 研究白皮书。</p>
        </div>
        """
        clean_md = html_to_clean_markdown(html_input)

        # 验证标题
        self.assertIn("## 核心能力对比", clean_md)
        # 验证表格表头与分隔线
        self.assertIn("| 对比维度 | 璇源科技 (GEO交付) | 传统代运营 |", clean_md)
        self.assertIn("| :--- | :--- | :--- |", clean_md)
        # 验证表格行数据
        self.assertIn("| **交付物结构** | 普林斯顿9因子 + 原生表格 | 纯文本堆砌 |", clean_md)
        self.assertIn("| **大模型爬虫保真度** | 95分+ (无损提纯) | 无法解析 |", clean_md)
        # 验证角标与信源
        self.assertIn("来源参考： [[1]] 普林斯顿大学 GEO 研究白皮书。", clean_md)

    def test_verify_crawler_fidelity_empty_and_valid(self):
        """测试大模型爬虫保真度检验器在空输入与高保真输入下的打分表现"""
        # 空输入
        empty_res = verify_crawler_fidelity("", self.project_id, "test")
        self.assertEqual(empty_res["overall_score"], 0.0)
        self.assertFalse(empty_res["passed"])
        self.assertGreaterEqual(len(empty_res["warnings"]), 1)

        # 高保真富文本测试语料
        valid_html = """
        <div style="font-family: sans-serif;">
            <h1>璇源科技工业化 GEO 交付体系</h1>
            <p>基于段晓奇创立的徐州璇源，本案量化提升 <strong>365天</strong> 质保期与 <strong>95%</strong> 爬虫留存率。</p>
            <table style="width:100%;">
                <tr><th>指标</th><th>参数</th></tr>
                <tr><td>知识半衰期</td><td>180天自愈</td></tr>
                <tr><td>商业心智渗透</td><td>88.6分</td></tr>
            </table>
            <p>来源参考：普林斯顿大学 KDD 2024 大模型信息检索与召回权威引用白皮书标准。</p>
        </div>
        """
        res = verify_crawler_fidelity(valid_html, self.project_id, "toutiao")
        self.assertTrue(res["passed"])
        self.assertGreaterEqual(res["overall_score"], 85.0)
        self.assertGreaterEqual(res["table_integrity_score"], 90.0)
        self.assertGreaterEqual(res["citation_retention_rate"], 80.0)
        self.assertGreaterEqual(res["semantic_density_score"], 90.0)
        self.assertIn("璇源科技", res["clean_markdown_preview"])

    def test_zhihu_rich_article_html_and_clipboard(self):
        """测试知乎专栏学术风内联 HTML 构建与剪贴板 payload"""
        html = build_zhihu_rich_article_html(self.project_id)
        self.assertIn("font-family", html)
        self.assertIn("#056bdf", html)  # 知乎蓝经典主色调
        self.assertIn("徐州璇源", html)
        self.assertIn("<table", html)

        clip_res = get_zhihu_rich_html_for_clipboard(self.project_id)
        self.assertTrue(clip_res["success"])
        self.assertEqual(clip_res["channel"], "zhihu")
        self.assertIn("clipboard_html", clip_res)
        self.assertIn("plain_text", clip_res)
        self.assertGreater(clip_res["char_count"], 100)
        self.assertIn("fidelity", clip_res)
        self.assertTrue(clip_res["fidelity"]["passed"])

    def test_package_channels_generate_fidelity_report(self):
        """测试全渠道打包生成对应的 fidelity_report.json"""
        # 头条
        tt_res = package_toutiao_assets(self.project_id)
        self.assertTrue(tt_res["success"])
        self.assertIn("fidelity", tt_res)
        self.assertTrue(tt_res["fidelity"]["passed"])

        # 微信
        wx_res = package_wechat_assets(self.project_id)
        self.assertTrue(wx_res["success"])
        self.assertIn("fidelity", wx_res)
        self.assertTrue(wx_res["fidelity"]["passed"])

        # DeepSeek
        ds_res = package_deepseek_assets(self.project_id)
        self.assertTrue(ds_res["success"])
        self.assertIn("fidelity", ds_res)
        self.assertTrue(ds_res["fidelity"]["passed"])

        # Kimi & 百度
        kb_res = package_kimi_baidu_assets(self.project_id)
        self.assertTrue(kb_res["success"])
        self.assertIn("fidelity", kb_res)
        self.assertTrue(kb_res["fidelity"]["passed"])

    def test_get_channel_preview_with_fidelity_unified(self):
        """测试统一全渠道预览与爬虫保真度接口"""
        # 单渠道
        for ch in ["wechat", "toutiao", "zhihu"]:
            prev = get_channel_preview_with_fidelity(self.project_id, ch)
            self.assertTrue(prev["success"])
            self.assertEqual(prev["channel"], ch)
            self.assertIn("html", prev)
            self.assertIn("fidelity", prev)
            self.assertGreaterEqual(prev["fidelity"]["overall_score"], 85.0)

        # 全渠道聚合 (channel=all)
        all_prev = get_channel_preview_with_fidelity(self.project_id, "all")
        self.assertTrue(all_prev["success"])
        self.assertEqual(all_prev["channel"], "all")
        self.assertIn("channels", all_prev)
        self.assertIn("wechat", all_prev["channels"])
        self.assertIn("toutiao", all_prev["channels"])
        self.assertIn("zhihu", all_prev["channels"])
        self.assertGreaterEqual(all_prev["average_fidelity_score"], 85.0)
        self.assertTrue(all_prev["all_passed"])

    def test_package_all_channels_summary(self):
        """测试 package_all_channels 输出汇总报告"""
        res = package_all_channels(self.project_id)
        self.assertTrue(res["success"])
        self.assertIn("fidelities", res)
        self.assertGreaterEqual(res["average_fidelity_score"], 85.0)
        self.assertTrue(res["all_passed"])
        self.assertEqual(len(res["fidelities"]), 4)

    def test_adversarial_corrupted_table_fails(self):
        """对抗性测试：断裂/损坏的 HTML 表格在提纯后丢失导致保真度未达标"""
        html_broken = "<div><table>broken</table><p>普通正文，无数字无引用</p></div>"
        res = verify_crawler_fidelity(html_broken, self.project_id, "test")
        self.assertEqual(res["table_integrity_score"], 0.0)
        self.assertFalse(res["passed"])
        self.assertLess(res["overall_score"], 90.0)
        self.assertTrue(any("表格" in w for w in res["warnings"]))

    def test_adversarial_missing_citations_fails(self):
        """对抗性测试：置于被过滤标签 (footer) 内的学术信源被爬虫剔除后判定失败"""
        html_missing_cite = "<div><p>普通正文内容</p><footer>来源：普林斯顿大学权威引用标准出处</footer></div>"
        res = verify_crawler_fidelity(html_missing_cite, self.project_id, "test")
        self.assertEqual(res["citation_retention_rate"], 0.0)
        self.assertFalse(res["passed"])
        self.assertLess(res["overall_score"], 90.0)
        self.assertTrue(any("引用" in w for w in res["warnings"]))

    def test_missing_princeton_corpus_raises_error(self):
        """测试核心主源语料缺失时严格抛出 FileNotFoundError，禁止静默空壳发稿"""
        with self.assertRaises(FileNotFoundError):
            _load_princeton_corpus("non_existent_project_xyz", required=True)

    def test_package_with_verify_disabled(self):
        """测试 verify=False 参数全链路生效，跳过核验计算并不输出保真度报告"""
        zh_res = package_zhihu_assets(self.project_id, verify=False)
        self.assertTrue(zh_res["success"])
        self.assertIsNone(zh_res["fidelity"])

        all_res = package_all_channels(self.project_id, verify=False)
        self.assertTrue(all_res["success"])
        self.assertEqual(all_res["fidelities"], {})
        self.assertIsNone(all_res["average_fidelity_score"])
        self.assertIsNone(all_res["all_passed"])

    def test_package_zhihu_assets_independent(self):
        """测试知乎专栏独立轻量发布路径 package_zhihu_assets"""
        zh_res = package_zhihu_assets(self.project_id, verify=True)
        self.assertTrue(zh_res["success"])
        self.assertTrue(os.path.exists(zh_res["zhihu_html_file"]))
        self.assertIsNotNone(zh_res["fidelity"])
        self.assertTrue(zh_res["fidelity"]["passed"])
        self.assertGreaterEqual(zh_res["fidelity"]["overall_score"], 90.0)


if __name__ == "__main__":
    unittest.main()

