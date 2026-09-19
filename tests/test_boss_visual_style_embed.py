# -*- coding: utf-8 -*-
"""
自动化测试：验证老板商业诊断报告高转化视觉样式嵌入（方案 B）
包含：DOM 节点存在性、样式切换逻辑、?raw=1 接口路由支持与 0 Emoji 商业红线
"""
import os
import re
import unittest

class TestBossVisualStyleEmbed(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.index_html_path = os.path.join(self.repo_root, "web", "index.html")
        self.server_py_path = os.path.join(self.repo_root, "tools", "geo", "server.py")

    def test_01_index_html_dom_elements_exist(self):
        """验证方案 B 相关的 DOM 元素完整性"""
        with open(self.index_html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 样式切换器胶囊按钮
        self.assertIn('id="boss-report-style-segmented"', content)
        self.assertIn('id="btn-boss-style-visual"', content)
        self.assertIn('id="btn-boss-style-md"', content)

        # 2. 全屏大屏按钮
        self.assertIn('openBossReportFullscreen()', content)
        self.assertIn('全屏大屏', content)

        # 3. 双预览容器（视觉大屏沙箱 + Markdown 底稿）
        self.assertIn('id="container-step-1-boss-visual"', content)
        self.assertIn('id="frame-step-1-boss-visual"', content)
        self.assertIn('id="boss-visual-placeholder"', content)
        self.assertIn('id="preview-step-1-boss"', content)

    def test_02_index_html_js_functions_exist(self):
        """验证前端 JS 切换与加载函数完整性"""
        with open(self.index_html_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("function switchBossReportStyle(", content)
        self.assertIn("async function loadBossReportVisual(", content)
        self.assertIn("function openBossReportFullscreen(", content)
        self.assertIn("switchBossReportStyle(currentBossReportStyle);", content)
        self.assertIn("loadBossReportVisual();", content)

    def test_03_server_py_supports_raw_output(self):
        """验证后端 server.py 的 /output/ 接口支持 ?raw=1"""
        with open(self.server_py_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('qs.get("raw", ["0"])[0] in ("1", "true")', content)
        self.assertIn('self._serve_static_file(target_file, filename)', content)

    def test_04_zero_emoji_compliance(self):
        """验证新增代码与变更区域严格遵守 0 Emoji 商业红线"""
        with open(self.index_html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 截取阶段一交付物卡片头部附近的区域
        start = content.find('id="boss-report-style-segmented"')
        self.assertGreater(start, 0)
        snippet = content[start:start + 1200]

        forbidden_emojis = ["⚡️", "💡", "⚠️", "⚙️", "💻", "🤝", "💎", "⚖️", "🎓", "💬", "🔴", "🟢", "🟡"]
        for em in forbidden_emojis:
            self.assertNotIn(em, snippet, f"新增代码块发现违规 Emoji: {em}")

if __name__ == "__main__":
    unittest.main()
