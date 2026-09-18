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


if __name__ == "__main__":
    unittest.main()


