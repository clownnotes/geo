# -*- coding: utf-8 -*-
"""
单元测试：双层商业转化型诊断报告生成与 0 Emoji 验证 (tests/test_conversion_report.py)
对应 OpenSpec 变更：2026-09-17-商业转化型诊断报告与竞品反哺体系（任务 4.1, 4.2, 4.3, 4.4）
"""

import os
import unittest
from tools.geo.audit import assemble_report, build_boss_psychology_report
from tools.geo.share import build_audit_report_html_document


class TestConversionReport(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            "client_name": "邻里GEO（NextGEO）",
            "brand_name": "NextGEO",
            "official_url": "https://www.baicl.cc",
            "industry": "企业级GEO答案源建设",
            "area_served": "江苏省徐州市及全国远程",
            "founder": "老白",
            "client_id": "xuzhou_xuanyuan",
        }
        self.metrics = {
            "url": "https://www.baicl.cc",
            "tech_score": 85,
            "has_ssr": True,
            "has_llms_txt": True,
            "has_json_ld": True,
            "text_density_ratio": 6.9,
            "clean_text_length": 2500,
            "robots_status": "已主动配置本土 AI 爬虫规则",
            "warnings": ["【双栈】IPv6 连通性提示"],
            "llm_status": "skipped",
            "is_online": True,
        }
        self.probe_snap = {
            "available": True,
            "probe_baseline_id": "probe:doubao:20260913",
            "probe_file": "competitor_probe_doubao_20260913_retest.json",
            "summary": {"brand_status": "误解", "founder_status": "中性"},
            "items": [
                {
                    "query": "徐州GEO优化公司哪家好",
                    "mentioned_self": False,
                    "url_present": False,
                    "standpoint": "不认识",
                    "hallucination_detected": True,
                    "competitors": ["亿企邦", "企优托"],
                },
                {
                    "query": "邻里GEO是做什么的",
                    "mentioned_self": False,
                    "url_present": False,
                    "standpoint": "误解",
                    "hallucination_detected": True,
                    "competitors": ["成都好卷"],
                },
                {
                    "query": "徐州璇源网络科技有限公司做什么的",
                    "mentioned_self": True,
                    "url_present": True,
                    "standpoint": "中性",
                    "hallucination_detected": False,
                    "competitors": [],
                },
            ],
        }

    def test_01_boss_psychology_seven_sections(self):
        """测试老板心理学转化层包含完整的转化章节与经济账"""
        boss_md = build_boss_psychology_report(self.cfg, self.metrics, self.probe_snap)

        # 检查核心转化节点
        self.assertIn("① 一页结论（老板速读版）", boss_md)
        self.assertIn("AI 可见度四维评分卡", boss_md)
        self.assertIn("你正在流失的，是 3 类本该进你微信的高价值询盘", boss_md)
        self.assertIn("[品牌直问询盘]", boss_md)
        self.assertIn("[信任词询盘]", boss_md)
        self.assertIn("[品类词询盘]", boss_md)

        self.assertIn("② 好消息：你的资产其实很能打（不用推倒重来）", boss_md)
        self.assertIn("③ 坏消息：AI 现在根本认不出你的品牌（这才是丢单的地方）", boss_md)
        self.assertIn("④ 四步破局路线：从「能被读到」到「被首位推荐」", boss_md)
        self.assertIn("⑤ 30 天后，你能拿到什么", boss_md)
        self.assertIn("⑥ 下一步：把这份免费体检变成真实询盘", boss_md)

    def test_02_dual_layer_report_structure(self):
        """测试组装后的双层报告：上层转化层 + 底层工程师附录"""
        full_md = assemble_report(self.cfg, self.metrics, self.probe_snap)

        # 上层检查
        self.assertIn("一页结论（老板速读版）", full_md)
        self.assertIn("30 天后，你能拿到什么", full_md)

        # 底层工程师技术附录检查（完整保留）
        self.assertIn("附录：技术底座与工程巡检详版（工程师审计依据）", full_md)
        self.assertIn("站点底座技术体检明细", full_md)
        self.assertIn("audit_metrics.json", full_md)
        self.assertIn("85 / 100", full_md)

    def test_03_zero_emoji_rule(self):
        """严格核查报告正文不含任何彩色 Emoji 表情"""
        full_md = assemble_report(self.cfg, self.metrics, self.probe_snap)
        banned_emojis = ["⚠️", "🟢", "🟡", "🔴", "📊", "⚡️", "🔥", "💡", "🤝"]
        for emoji in banned_emojis:
            self.assertNotIn(emoji, full_md, f"违规检测到 Emoji: {emoji}")

    def test_04_html_rendering_e2e(self):
        """测试将生成的双层报告渲染为客户版 HTML 文档"""
        full_md = assemble_report(self.cfg, self.metrics, self.probe_snap)
        html_doc = build_audit_report_html_document("xuzhou_xuanyuan", markdown=full_md)
        self.assertTrue(html_doc["success"])
        html_str = html_doc["html"]
        self.assertIn("一页结论", html_str)
        self.assertIn("30 天后，你能拿到什么", html_str)
        self.assertIn("附录：技术底座与工程巡检详版", html_str)

    def test_05_independent_boss_and_tech_reports(self):
        """测试方案 A 独立生成纯净老板版与纯净工程师版，各司其职互不干扰"""
        from tools.geo.audit import assemble_boss_report, assemble_tech_report
        boss_md = assemble_boss_report(self.cfg, self.metrics, self.probe_snap)
        tech_md = assemble_tech_report(self.cfg, self.metrics, self.probe_snap)

        # 老板版验证：有转化全流程，绝不含生涩工程附录
        self.assertIn("AI 可见度商业诊断报告", boss_md)
        self.assertIn("一页结论（老板速读版）", boss_md)
        self.assertIn("30 天后，你能拿到什么", boss_md)
        self.assertNotIn("附录：技术底座与工程巡检详版", boss_md)

        # 工程师版验证：问题 + 改造方案；不含老板焦虑 CTA / 商业调试话
        self.assertIn("站点底座技术体检与工程审计报告", tech_md)
        self.assertIn("站点底座技术体检明细", tech_md)
        self.assertIn("问题与改造方案对照", tech_md)
        self.assertIn("工程师内部施工稿", tech_md)
        self.assertNotIn("一页结论（老板速读版）", tech_md)
        self.assertNotIn("30 天后，你能拿到什么", tech_md)
        self.assertNotIn("【品牌答案源极速筑基体验包】", tech_md)
        self.assertNotIn("商业解读调用失败", tech_md)
        self.assertNotIn("限时体验计划", tech_md)

        # 0 Emoji 检查
        banned = ["⚠️", "🟢", "🟡", "🔴", "📊", "⚡️", "🔥", "💡", "🤝"]
        for e in banned:
            self.assertNotIn(e, boss_md)
            self.assertNotIn(e, tech_md)

    def test_06_html_export_views(self):
        """测试按 view=boss 和 view=tech 导出对应的专属自包含 HTML"""
        from tools.geo.share import build_audit_report_html_document, AUDIT_REPORT_HTML_BOSS, AUDIT_REPORT_HTML_TECH
        boss_doc = build_audit_report_html_document("xuzhou_xuanyuan", view="boss")
        tech_doc = build_audit_report_html_document("xuzhou_xuanyuan", view="tech")

        self.assertTrue(boss_doc["success"])
        self.assertTrue(tech_doc["success"])
        self.assertEqual(boss_doc["filename"], AUDIT_REPORT_HTML_BOSS)
        self.assertEqual(tech_doc["filename"], AUDIT_REPORT_HTML_TECH)
        self.assertIn("AI 可见度商业诊断报告", boss_doc["html"])
        self.assertIn("站点底座技术体检与工程审计报告", tech_doc["html"])

        # 0 Emoji 质检
        banned = ["⚠️", "🟢", "🟡", "🔴", "📊", "⚡️", "🔥", "💡", "🤝"]
        for e in banned:
            self.assertNotIn(e, boss_doc["html"])
            self.assertNotIn(e, tech_doc["html"])

    def test_07_stage1_ui_copy_static_assertions(self):
        """阶段 9：两边各 4 步定稿文案 + 交付物解耦 + 0 Emoji"""
        from pathlib import Path

        html = Path(__file__).resolve().parents[1].joinpath("web", "index.html").read_text(
            encoding="utf-8"
        )
        start = html.find('id="panel-step-1-diag"')
        end = html.find('id="panel-step-2-scaffold"')
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        panel = html[start:end]

        for needle in (
            'id="tab-audit-top-boss"',
            'id="tab-audit-top-tech"',
            'id="view-audit-boss"',
            'id="view-audit-tech"',
        ):
            self.assertIn(needle, panel)

        boss_view_start = panel.find('id="view-audit-boss"')
        tech_view_start = panel.find('id="view-audit-tech"')
        boss_panel = panel[boss_view_start:tech_view_start]
        tech_panel = panel[tech_view_start:]

        for boss_step in (
            "① 真抓网络与底座指标",
            "② 直出商业诊断与焦虑转化初稿（程序生成 · 0 幻觉）",
            "③ 复制商业报告与转化初稿（给 IDE 润色）",
            "④ 追加豆包问答稿与提示词（给 IDE 参考）",
        ):
            self.assertIn(boss_step, boss_panel)

        # 卡片内不得再放冗余导出 HTML 主步骤
        self.assertNotIn("④ 导出老板商业报告 (HTML)", boss_panel)
        self.assertNotIn('id="btn-step-1-export-boss"', boss_panel)
        # 导出仍在交付物右上角
        self.assertIn("下载老板商业报告 (HTML)", boss_panel)

        for tech_step in (
            "① 真抓网络与底座指标",
            "② 直出技术体检与改造方案初稿（程序生成 · 0 幻觉）",
            "③ 复制技术指标与改造方案初稿（给 IDE 再审）",
            "④ 追加豆包问答稿与提示词（给 IDE 参考）",
        ):
            self.assertIn(tech_step, tech_panel)

        self.assertIn("交付物：01_企业AI可见度商业诊断报告.md", boss_panel)
        # 交付物行不得挂 metrics；帮助文案可提及落盘文件名
        self.assertNotIn("交付物：01_企业AI可见度商业诊断报告.md · audit_metrics.json", boss_panel)
        self.assertIn("交付物：01_企业底座技术体检审计报告.md · audit_metrics.json", tech_panel)

        self.assertIn("请先点「① 真抓网络与底座指标」", html)

        for bad in (
            "复制②深化提示词（给 IDE）",
            "已复制②深化提示词",
            "① 直出商业诊断骨架（程序计算 · 0 幻觉）",
        ):
            self.assertNotIn(bad, html)

        for e in ("⚠️", "🟢", "🟡", "🔴", "📊", "⚡️", "🔥", "💡"):
            self.assertNotIn(e, panel)

    def test_08_interpret_requires_metrics_plain_toast(self):
        """无 audit_metrics 时 interpret / boss_direct 抛出统一人话提示"""
        import tempfile
        from unittest.mock import patch
        from tools.geo import audit as audit_mod

        with tempfile.TemporaryDirectory() as td:
            proj = os.path.join(td, "projects", "demo")
            out = os.path.join(proj, "outputs")
            os.makedirs(out, exist_ok=True)
            cfg = {
                "client_id": "demo",
                "client_name": "Demo",
                "official_url": "https://www.baicl.cc",
                "_project_dir": proj,
                "_outputs_dir": out,
            }
            with patch("tools.geo.audit.load_project_config", return_value=cfg):
                with self.assertRaises(ValueError) as ctx:
                    audit_mod.run_audit_interpret("demo")
                self.assertIn("请先点「① 真抓网络与底座指标」", str(ctx.exception))
                with self.assertRaises(ValueError) as ctx2:
                    audit_mod.run_audit_boss_direct("demo")
                self.assertIn("请先点「① 真抓网络与底座指标」", str(ctx2.exception))

    def test_09_boss_audit_clipboard_pack_4_tiers(self):
        """测试 build_boss_audit_clipboard_pack 产出四层全证据链并保持 0 Emoji"""
        from tools.geo.audit import build_boss_audit_clipboard_pack
        res = build_boss_audit_clipboard_pack("nextgeo")
        self.assertTrue(res.get("success"))
        clip = res.get("clipboard", "")
        self.assertIn("—— 第一层：阶段零豆包实测一手答题卡", clip)
        self.assertIn("—— 第二层：Python 客观直出商业诊断骨架", clip)
        self.assertIn("—— 第三层：发给小毛驴的原始 Prompt 提示词", clip)
        self.assertIn("—— 第四层：小毛驴写出的初稿与状态", clip)
        for e in ("⚠️", "🟢", "🟡", "🔴", "📊", "⚡️", "🔥", "💡"):
            self.assertNotIn(e, clip)

    def test_10_button_help_tooltips_and_optional_tag(self):
        """阶段 9：8 个主步骤小问号 + 可选小毛驴文案"""
        with open(
            os.path.join(os.path.dirname(__file__), "..", "web", "index.html"),
            encoding="utf-8",
        ) as f:
            html = f.read()
        start = html.find('id="panel-step-1-diag"')
        end = html.find('id="panel-step-2-scaffold"')
        panel = html[start:end]

        self.assertGreaterEqual(panel.count('data-lucide="help-circle"'), 8)
        self.assertIn("调小毛驴补反差话术（可选）", panel)
        self.assertIn("贩卖焦虑", panel)
        self.assertIn("问题清单 + 对应改造步骤", panel)
        self.assertIn("焦虑转化润色提示词", panel)
        self.assertIn("架构师改造提示词", panel)

    def test_11_boss_conversion_html_template(self):
        """测试高转化老板商业诊断报告 HTML 纯原生自包含模板生成与 7 大核心区块"""
        from tools.geo.share import build_audit_report_html_document
        res = build_audit_report_html_document("nextgeo", view="boss")
        self.assertTrue(res.get("success"), "应当生成成功")
        html = res.get("html", "")

        # 1. 验证关键浅紫色流光美学样式
        self.assertIn("linear-gradient(135deg, #ede9fe 0%", html, "应当包含浅紫色流光渐变背景")
        self.assertIn(".dr-hero__score-group", html, "应当包含磨砂白独立仪表盘")
        self.assertIn("backdrop-filter:blur(10px)", html, "应当具备高质感毛玻璃效果")

        # 2. 验证三个原生动态 SVG 图表
        self.assertIn("dr-hero__score-ring-fill", html, "应当包含动态圆环进度条")
        self.assertIn("基建完善度", html, "应当包含雷达图指标")
        self.assertIn("认知准确性", html, "应当包含雷达图指标")
        self.assertIn("探索层提及率", html, "应当包含三色环形分布图")

        # 3. 验证 5 大商业诊断核心区块
        self.assertIn("AI 可见度商业诊断报告", html)
        self.assertIn("诊 断 概 览", html)
        self.assertIn("好消息：你的技术资产其实很能打", html)
        self.assertIn("坏消息：AI 现在根本认不出你的品牌", html)
        self.assertIn("竞品占位透视：谁在吃你的入口", html)
        self.assertIn("四步破局：从「能被读到」到「被推荐」", html)
        self.assertIn("AIVO 四维评分（思维分析）", html)

        # 验证按用户要求：彻底删除原图 1「评测元信息（数据真源）」
        self.assertNotIn("评 测 元 信 息（数据真源）", html, "图 1 评测元信息必须已删除")

        # 4. 验证终章收官大卡片（宣传语金句与原图 2 联系方式深度融合）
        self.assertIn("dr-slogan", html)
        self.assertIn("当你清楚要做什么，全世界都会为你让路", html)
        self.assertIn("dr-slogan__action", html, "宣传语卡片内必须包含行动转化专区")
        self.assertIn("电话/微信", html)
        self.assertIn("官网", html)
        self.assertIn("起步档：企业 GEO 全案服务", html)

        # 5. 严格验证收尾排版顺序：思维分析 -> 终章宣传语与联系方式大卡片
        pos_aivo = html.find("AIVO 四维评分（思维分析）")
        pos_slogan = html.find("当你清楚要做什么，全世界都会为你让路")

        self.assertGreater(pos_aivo, 0, "AIVO 四维评分必须存在")
        self.assertGreater(pos_slogan, pos_aivo, "宣传语与联系方式收官大卡片必须在思维分析之后作为最终收尾")

    def test_12_boss_conversion_html_zero_emoji(self):
        """严格断言生成的高转化老板商业报告 HTML 绝对 0 Emoji 违规"""
        import re
        from tools.geo.boss_report_html import extract_conversion_report_data, assemble_boss_conversion_html
        data = extract_conversion_report_data("nextgeo")
        html = assemble_boss_conversion_html(data)

        # 常见 Emoji 与 Unicode Emoji 范围
        emoji_pattern = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)
        matches = emoji_pattern.findall(html)
        self.assertEqual(len(matches), 0, f"生成的 HTML 中发现违规 Emoji: {set(matches)}")

        # 关键状态符号不得有彩色表情符号
        for bad_emoji in ("🔴", "🟢", "🟡", "⚠️", "⚡️", "💡", "📊", "🤝", "💎", "⚙️", "💻"):
            self.assertNotIn(bad_emoji, html, f"HTML 中不得包含表情符号: {bad_emoji}")

    def test_13_downloads_html_reordered_and_zero_emoji(self):
        """验证 Downloads 目录下的交付 HTML 文件已删除 footer，联系方式已融入宣传语且 0 Emoji"""
        import re
        downloads_file = "/Volumes/a1/Downloads/邻里GEO-AI可见度诊断报告（转化版）.html"
        if not os.path.exists(downloads_file):
            return
        with open(downloads_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查删除图 1(评测元信息)
        self.assertNotIn("评 测 元 信 息（数据真源）", content)

        # 检查金句和融入的联系方式
        self.assertIn("当你清楚要做什么，全世界都会为你让路", content)
        self.assertIn("nextdoor8", content)
        self.assertIn("13150568888", content)
        self.assertIn("baicl.cc", content)
        self.assertIn("起步档：企业 GEO 全案服务", content)

        p_aivo = content.find("AIVO 四维评分（思维分析）")
        p_slogan = content.find("当你清楚要做什么，全世界都会为你让路")

        self.assertGreater(p_aivo, 0)
        self.assertGreater(p_slogan, p_aivo)

        # 0 Emoji 检查
        emoji_pattern = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)
        matches = emoji_pattern.findall(content)
        self.assertEqual(len(matches), 0, f"Downloads HTML 中发现违规 Emoji: {set(matches)}")
        for bad_emoji in ("🔴", "🟢", "🟡", "⚠️", "⚡️", "💡", "📊", "🤝", "💎", "⚙️", "💻"):
            self.assertNotIn(bad_emoji, content)

        # 0 Emoji 检查
        emoji_pattern = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)
        matches = emoji_pattern.findall(content)
        self.assertEqual(len(matches), 0, f"Downloads HTML 中发现违规 Emoji: {set(matches)}")
        for bad_emoji in ("🔴", "🟢", "🟡", "⚠️", "⚡️", "💡", "📊", "🤝", "💎", "⚙️", "💻"):
            self.assertNotIn(bad_emoji, content)


if __name__ == "__main__":
    unittest.main()


