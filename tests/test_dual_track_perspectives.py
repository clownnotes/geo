# -*- coding: utf-8 -*-
"""开发者与写文同事双轨视界解耦与白盒流水线复原自动化测试 (tests/test_dual_track_perspectives.py)

对应 OpenSpec 变更：2026-09-21-开发者与写文同事双轨视界解耦与白盒流水线复原
测试覆盖：
1. 静态 DOM 权限属性与双轨标记验证：
   - 阶段 0：getStep0BridgeProps 包含 isDeveloper，Step0App/ProbeStep 组件受 isDeveloper 保护
   - 阶段 1：技术版 Tab 带 data-geo-dev-only；老板版开发者卡片带 data-geo-dev-only（含复制商业报告与追加豆包）；写文同事卡片带 data-geo-writer-only（含小毛驴一键生成）
   - 阶段 2：导出源码包 (.zip) 带 data-geo-dev-only
   - 阶段 3：复制 9 因子全文带 data-geo-dev-only
   - 阶段 4：头条/知乎 IDE 工地带 data-geo-dev-only；SOP 派单卡带 data-geo-dev-only
   - 阶段 5：商业 ROI 看板根节点带 data-geo-dev-only
   - 全局：applyRbacUi 对 data-geo-writer-only 的互斥显隐控制
2. 关键路由 RBAC 隔离验证：
   - 开发者专属接口（/site/download, /acceptance/download-zip, /answer-rewrite/pack, /diag/deepen-prompt）在写文同事身份下返回 403
   - ROI 计算接口（/roi/calculate）在写文同事身份下返回 200 放行
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(PROJECT_ROOT, "web", "index.html")
STEP0_APP_PATH = os.path.join(PROJECT_ROOT, "web", "step0-src", "Step0App.vue")
STEP0_JS_PATH = os.path.join(PROJECT_ROOT, "web", "assets", "step0", "step0.js")


class DualTrackPerspectivesTest(unittest.TestCase):

    def setUp(self):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            self.html = f.read()

        with open(STEP0_APP_PATH, "r", encoding="utf-8") as f:
            self.step0_vue = f.read()

        self.writer = rbac.Identity(
            user_id="304212040660824064",
            phone="13805206070",
            name="写文同事",
            is_developer=False,
            role="operator",
            status="active",
            allowed_projects=["nextgeo"],
            permissions=["keyword:manage", "ai:generate", "article:edit", "preview:view", "report:view"],
            matched=True,
        )

        self.developer = rbac.Identity(
            user_id="100000000000000001",
            phone="13900000001",
            name="工程师",
            is_developer=True,
            role="developer",
            status="active",
            allowed_projects=["*"],
            permissions=["*"],
            matched=True,
        )

    def test_global_rbac_ui_dual_track(self):
        """1. applyRbacUi 必须同时控制 data-geo-dev-only 与 data-geo-writer-only"""
        self.assertIn("data-geo-dev-only", self.html)
        self.assertIn("data-geo-writer-only", self.html)

        # 检查 applyRbacUi 内部实现
        self.assertIn("document.querySelectorAll('[data-geo-writer-only]')", self.html)
        self.assertIn("isDeveloper()", self.html)

        # 检查 bridge 传递 isDeveloper
        bridge_match = re.search(r'function\s+getStep0BridgeProps\s*\(\)\s*\{([\s\S]*?)\}', self.html)
        self.assertIsNotNone(bridge_match, "未找到 getStep0BridgeProps 函数")
        self.assertIn("isDeveloper:", bridge_match.group(1), "getStep0BridgeProps 必须注入 isDeveloper")

    def test_step0_dual_track_vue(self):
        """2. 阶段零 Vue 组件岛必须支持 isDeveloper 双轨隔离"""
        self.assertIn(":is-developer=\"isDeveloper\"", self.step0_vue)
        self.assertIn("copyQualityPrompt", self.step0_vue)
        self.assertIn("copyCursorPrompt", self.step0_vue)
        self.assertIn("copyAntigravityPrompt", self.step0_vue)
        self.assertIn("copyPreviewForIde", self.step0_vue)

        # 编译后产物必须存在且非空
        self.assertTrue(os.path.exists(STEP0_JS_PATH), "web/assets/step0/step0.js 必须存在")
        self.assertGreater(os.path.getsize(STEP0_JS_PATH), 50000, "step0.js 产物体积必须正常")

    def test_step1_dual_track_dom(self):
        """3. 阶段一双轨 DOM 结构验证"""
        # 技术版 Tab 必须挂 data-geo-dev-only
        tech_tab = re.search(r'<button[^>]*id="tab-audit-top-tech"[^>]*>', self.html)
        self.assertIsNotNone(tech_tab, "未找到 tab-audit-top-tech")
        self.assertIn("data-geo-dev-only", tech_tab.group(0))

        # 老板版开发者卡片挂 data-geo-dev-only，并包含步骤 ③ 和 ④
        boss_dev_card = re.search(r'<div\s+data-geo-dev-only[^>]*data-page-node-id="iWQvwGq9UK4pQWwhx88qPm"[^>]*>([\s\S]*?)</div>\s*<!-- 写文同事专属', self.html)
        self.assertIsNotNone(boss_dev_card, "未找到阶段一老板版开发者专属卡片")
        content = boss_dev_card.group(1)
        self.assertIn("copyBossAuditToIde", content, "开发者卡片必须包含 copyBossAuditToIde")
        self.assertIn("copyDiagDeepenPrompt(this, 'boss')", content, "开发者卡片必须包含 copyDiagDeepenPrompt")

        # 老板版写文同事卡片挂 data-geo-writer-only，包含小毛驴一键生成
        writer_card = re.search(r'<div\s+data-geo-writer-only[^>]*>([\s\S]*?)</div>\s*<!-- 老板版专属交付物', self.html)
        self.assertIsNotNone(writer_card, "未找到阶段一写文同事专属卡片")
        w_content = writer_card.group(1)
        self.assertIn("runWriterStep1AiGenerate(event)", w_content, "写文同事卡片必须包含 runWriterStep1AiGenerate")

        # 技术版卡片必须包含步骤 ③ 和 ④
        tech_card = re.search(r'<div[^>]*data-page-node-id="LFenwGZo9zMJtDCU3es27n"[^>]*>([\s\S]*?)<div[^>]*data-page-node-id="NXPrrvjVtilvJD5qzG9hlL"', self.html)
        self.assertIsNotNone(tech_card, "未找到技术体检版操作卡片")
        t_content = tech_card.group(1)
        self.assertIn("copyStep1AuditToIde(this)", t_content)
        self.assertIn("copyDiagDeepenPrompt(this, 'tech')", t_content)

        # 3.6 switchAuditTopTab 必须在重设 className 后调用 applyRbacUi() 防洗掉 hidden
        switch_func = re.search(r'function\s+switchAuditTopTab\s*\([^\)]*\)\s*\{([\s\S]*?)\n\s*function\s+switchAuditReportView', self.html)
        self.assertIsNotNone(switch_func, "未找到 switchAuditTopTab 函数")
        self.assertIn("applyRbacUi()", switch_func.group(1), "switchAuditTopTab 必须在末尾调用 applyRbacUi() 重新应用权限隐藏")

        # 3.7 runWriterStep1AiGenerate 防连点锁必须在查摸底之前加上
        writer_func = re.search(r'async\s+function\s+runWriterStep1AiGenerate\s*\([^\)]*\)\s*\{([\s\S]*?)\n\s*async\s+function\s+refreshDiagDeepenProbeHint', self.html)
        self.assertIsNotNone(writer_func, "未找到 runWriterStep1AiGenerate 函数")
        w_code = writer_func.group(1)
        lock_idx = w_code.find("isStep1AuditRunning = true")
        probe_idx = w_code.find("checkHasProbe()")
        self.assertNotEqual(lock_idx, -1, "runWriterStep1AiGenerate 必须设置 isStep1AuditRunning = true")
        self.assertNotEqual(probe_idx, -1, "runWriterStep1AiGenerate 必须调用 checkHasProbe()")
        self.assertLess(lock_idx, probe_idx, "isStep1AuditRunning = true 必须在 checkHasProbe() 前上锁防连点")

    def test_step2_and_3_danger_actions_hidden(self):
        """4. 阶段二源码包下载与阶段三 9 因子全文复制必须有 data-geo-dev-only"""
        # 阶段二源码包
        zip_btn = re.search(r'<button[^>]*onclick="downloadSiteZip\(\)"[^>]*>', self.html)
        self.assertIsNotNone(zip_btn)
        self.assertIn("data-geo-dev-only", zip_btn.group(0))

        # 阶段三 9 因子全文复制
        corpus_copy = re.search(r'<button[^>]*copyOutput\([\'"]03_普林斯顿9因子高权威语料库\.md[\'"]\)[^>]*>', self.html)
        self.assertIsNotNone(corpus_copy)
        self.assertIn("data-geo-dev-only", corpus_copy.group(0))

    def test_step4_dual_track_and_sop(self):
        """5. 阶段四 IDE 工地与 SOP 派单卡双轨验证"""
        # 头条 IDE 工地
        self.assertIn("copyIdeRewritePack('toutiao', this)", self.html)
        self.assertIn("copyWritebackCommand('toutiao', this)", self.html)

        # 知乎 IDE 工地
        self.assertIn("copyIdeRewritePack('zhihu', this)", self.html)
        self.assertIn("copyWritebackCommand('zhihu', this)", self.html)

        # SOP 派单卡必须挂 data-geo-dev-only
        sop_card = re.search(r'<div\s+data-geo-dev-only[^>]*data-page-node-id="HHOhnVq8tKphgZZGFCBur8"[^>]*>([\s\S]*?)<div class="flex items-center justify-between pt-4 border-t', self.html)
        self.assertIsNotNone(sop_card, "未找到阶段四 SOP 派单卡")
        self.assertIn("dist_channels_checklist.md", sop_card.group(1))

    def test_step5_roi_board_dev_only(self):
        """6. 阶段五商业 ROI 看板整块必须是开发者专属"""
        roi_card = re.search(r'<div\s+data-geo-dev-only[^>]*data-page-node-id="yPfnpxGWhCfJviBGrFEgUA"[^>]*>', self.html)
        self.assertIsNotNone(roi_card, "未找到阶段五商业 ROI 看板")

    def test_rbac_critical_endpoints_dual_track(self):
        """7. 接口权限隔离断言：写文同事禁止调用开发者专属接口，但允许调用商业 ROI 计算"""
        # 开发者专属接口列表（必须包含 :developer 标记）
        dev_endpoints = [
            "/api/projects/nextgeo/site/download",
            "/api/projects/nextgeo/acceptance/download-zip",
            "/api/projects/nextgeo/answer-rewrite/pack",
            "/api/projects/nextgeo/answer-rewrite/writeback-cmd",
            "/api/projects/nextgeo/diag/deepen-prompt",
        ]

        for path in dev_endpoints:
            # 开发者请求：200 放行
            allowed, status, _ = rbac.guard_route(path, "GET", self.developer)
            self.assertTrue(allowed, f"开发者访问 {path} 应该被允许，却得到 {status}")

            # 写文同事请求：403 拦截
            allowed, status, _ = rbac.guard_route(path, "GET", self.writer)
            self.assertFalse(allowed, f"写文同事访问 {path} 必须被拦截 403，却得到允许")
            self.assertEqual(status, 403, f"写文同事访问 {path} 状态码必须是 403，实际得到 {status}")

        # ROI 计算接口：写文同事有 report:view 权限，必须放行（返回 200）
        roi_path = "/api/projects/nextgeo/roi/calculate"
        allowed, status, _ = rbac.guard_route(roi_path, "POST", self.writer)
        self.assertTrue(allowed, f"写文同事访问 {roi_path} 应该被允许，却得到 {status}")


if __name__ == "__main__":
    unittest.main()
