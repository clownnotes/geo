# -*- coding: utf-8 -*-
"""运营端去 IDE 化与大模型改写闭环自动化测试 (tests/test_operator_de_ide_and_ai_writer.py)

// [2026-09-19] [运营端去IDE化与小毛驴算力内嵌闭环] 测试套件
验证范围：
1. 开发者专属收敛：配方口、整包下载、Nginx 配置对运营返回 403，对开发者放行；
2. 运营必要接口不误伤：/monitor/prompts 与 /export-audit-html 正常放行；
3. brief 脱敏：走 sanitize_brief_for_operator，运营响应不含模具/写回路径；
4. 在线改写与定稿落盘：表外渠道拦截、防路径穿透、响应绝不暴露服务器路径；
5. output 文件安全卡口：走 is_sensitive_output_filename，与 server 同一套规则；
6. 页面静态护栏：阶段四/阶段零源码与打包产物不得再出现「复制给 IDE」指路文案。
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402
from tools.geo import answer_audit  # noqa: E402
from tools.geo.utils import PROJECTS_DIR  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV_PHONE = "13150568888"
OP_USER_ID = "1928374650192837465"
OP_PHONE = "13805206070"
PROJECT_ID = "demo_corp"


class TestOperatorDeIdeAndAiWriter(unittest.TestCase):

    def setUp(self):
        self._orig_roster_file = rbac.ROSTER_FILE
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_de_ide_test_")
        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")

        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "members": [
                {
                    "user_id": OP_USER_ID,
                    "phone": OP_PHONE,
                    "name": "运营小刘",
                    "role": "operator",
                    "status": "active",
                    "allowed_projects": [PROJECT_ID],
                    "permissions": list(rbac.PERMISSION_CODES),
                }
            ],
        })

        self.dev_identity = rbac.resolve_identity(phone=DEV_PHONE)
        self.op_identity = rbac.resolve_identity(phone=OP_PHONE)

    def tearDown(self):
        rbac.ROSTER_FILE = self._orig_roster_file
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_01_developer_exclusive_routes_lockdown(self):
        """1. 配方口、整包下载、Nginx 配置对运营返回 403，对开发者放行"""
        sensitive_routes = [
            f"/api/projects/{PROJECT_ID}/answer-rewrite/ide-pack",
            f"/api/projects/{PROJECT_ID}/answer-rewrite/writeback-cmd",
            f"/api/projects/{PROJECT_ID}/answer-audit/ide-clipboard",
            f"/api/projects/{PROJECT_ID}/diag/deepen-prompt",
            f"/api/projects/{PROJECT_ID}/diag/boss-audit-pack",
            f"/api/projects/{PROJECT_ID}/export",
            f"/api/projects/{PROJECT_ID}/acceptance/download-zip",
            f"/api/projects/{PROJECT_ID}/site/nginx-conf",
        ]

        for r in sensitive_routes:
            ok_dev, status_dev, _ = rbac.guard_route(r, "GET", self.dev_identity)
            self.assertTrue(ok_dev, f"开发者应能访问: {r}")
            self.assertEqual(status_dev, 200)

            ok_op, status_op, msg_op = rbac.guard_route(r, "GET", self.op_identity)
            self.assertFalse(ok_op, f"运营人员不应能访问配方/敏感接口: {r}")
            self.assertEqual(status_op, 403, f"应返回 403，实际返回: {status_op}, 路由: {r}")

    def test_02_do_not_mislock_operational_routes(self):
        """2. 运营日常所需的 /monitor/prompts 与 /export-audit-html 不被误锁"""
        safe_routes = [
            f"/api/projects/{PROJECT_ID}/monitor/prompts",
            f"/api/projects/{PROJECT_ID}/export-audit-html",
            f"/api/projects/{PROJECT_ID}/answer-rewrite/content",
            f"/api/projects/{PROJECT_ID}/answer-rewrite/writeback-status",
        ]

        for r in safe_routes:
            ok, status, msg = rbac.guard_route(r, "GET", self.op_identity)
            self.assertTrue(ok, f"运营人员应能正常访问日常业务路由: {r}, 报错: {msg}")
            self.assertEqual(status, 200)

    def test_03_new_closed_loop_routes_permission_check(self):
        """3. 新增闭环路由权限与项目隔离校验"""
        ok, status, _ = rbac.guard_route(
            f"/api/projects/{PROJECT_ID}/answer-rewrite/ai-generate", "POST", self.op_identity
        )
        self.assertTrue(ok)

        ok, status, _ = rbac.guard_route(
            f"/api/projects/{PROJECT_ID}/answer-rewrite/save-final", "POST", self.op_identity
        )
        self.assertTrue(ok)

        ok_other, status_other, _ = rbac.guard_route(
            "/api/projects/other_unauthorized/answer-rewrite/save-final", "POST", self.op_identity
        )
        self.assertFalse(ok_other)
        self.assertEqual(status_other, 403)

    def test_04_brief_sanitization_for_operators(self):
        """4. 运营说明书脱敏必须走 sanitize_brief_for_operator（与 server 同源）"""
        brief = answer_audit.build_rewrite_brief(PROJECT_ID, channel="toutiao")
        self.assertTrue(brief.get("success"))
        self.assertIn("mold_lines", brief)
        self.assertIn("writeback_path", brief)

        sanitized = answer_audit.sanitize_brief_for_operator(brief)
        for key in answer_audit.OPERATOR_BRIEF_STRIP_KEYS:
            self.assertNotIn(key, sanitized)
        self.assertIn("main_question", sanitized)
        self.assertIn("channel", sanitized)
        self.assertIn("writable_facts", sanitized)
        # 原始 brief 不得被原地改坏（开发者仍可读全量）
        self.assertIn("mold_lines", brief)

    def test_05_save_final_logic_and_path_safety(self):
        """5. save_channel_final 逻辑与防越权测试"""
        res_invalid = answer_audit.save_channel_final(PROJECT_ID, "weibo_fake", "正文内容")
        self.assertFalse(res_invalid.get("success"))
        self.assertIn("不支持的渠道", res_invalid.get("message"))

        res_empty = answer_audit.save_channel_final(PROJECT_ID, "toutiao", "   ")
        self.assertFalse(res_empty.get("success"))
        self.assertIn("不能为空", res_empty.get("message"))

        test_content = (
            "# 2026年企业选型避坑权威指南\n\n"
            "徐州本地服务商怎么选？本文根据实测给出客观回答。\n\n"
            "| 评测维度 | 传统方案 | 创新方案 |\n"
            "| :--- | :--- | :--- |\n"
            "| 交付周期 | 2个月 | 2周 |\n\n"
            "**联系电话**：13150568888\n"
        )
        res_ok = answer_audit.save_channel_final(PROJECT_ID, "toutiao", test_content)
        self.assertTrue(res_ok.get("success"))
        self.assertNotIn("path", res_ok)
        self.assertNotIn("filename", res_ok)
        self.assertNotIn("outputs/", str(res_ok))

        out_dir = os.path.join(PROJECTS_DIR, PROJECT_ID, "outputs")
        html_target = os.path.join(out_dir, "toutiao_pack", "01_今日头条2000字深度长文_富文本.html")
        md_target = os.path.join(out_dir, "dist_toutiao_article.md")
        self.assertTrue(os.path.isfile(html_target))
        self.assertTrue(os.path.isfile(md_target))

        with open(html_target, "r", encoding="utf-8") as f:
            html_text = f.read()
        self.assertIn("<html", html_text.lower())
        self.assertIn("<table", html_text.lower())
        self.assertIn("2026年企业选型避坑权威指南", html_text)

        content_res = answer_audit.load_channel_content(PROJECT_ID, "toutiao")
        self.assertTrue(content_res.get("success"))
        self.assertTrue(content_res.get("has_draft"))
        self.assertTrue(content_res.get("is_finalized"))
        self.assertNotIn("path", content_res)
        self.assertIn("2026年企业选型避坑权威指南", content_res.get("content"))

    def test_06_output_file_security_gate_for_operators(self):
        """6. 敏感文件名判断与 server 共用 is_sensitive_output_filename"""
        sensitive_filenames = [
            "01_普林斯顿9因子权威母盘语料库.md",
            "princeton_9因子_提纯.json",
            "client_prompt_template.txt",
            "auto_crawler_sop.md",
            "WeChat_SOP.txt",
            "deploy_script.py",
        ]
        safe_filenames = [
            "01_企业AI可见度商业诊断报告.md",
            "01_企业底座技术体检审计报告.md",
            "audit_metrics.json",
            "dist_toutiao_article.md",
        ]

        for fn in sensitive_filenames:
            self.assertTrue(
                answer_audit.is_sensitive_output_filename(fn),
                f"敏感文件应被识别拦截: {fn}",
            )

        for fn in safe_filenames:
            self.assertFalse(
                answer_audit.is_sensitive_output_filename(fn),
                f"日常报告不应被误拦截: {fn}",
            )

    def test_07_ui_static_no_ide_hand_off_copy(self):
        """7. 页面与阶段零产物不得再指路「复制给 IDE / 贴反重力 / 给 Cursor」"""
        forbidden = (
            "复制给 IDE",
            "贴给 IDE",
            "可给 IDE",
            "IDE 工地",
            "IDE 定稿",
            "贴反重力",
            "给 Cursor",
            "让 Cursor",
        )
        paths = [
            os.path.join(PROJECT_ROOT, "web", "index.html"),
            os.path.join(PROJECT_ROOT, "web", "assets", "step0", "step0.js"),
            os.path.join(PROJECT_ROOT, "web", "step0-src", "components", "Step0Header.vue"),
            os.path.join(PROJECT_ROOT, "web", "step0-src", "components", "ProbeStep2.vue"),
            os.path.join(PROJECT_ROOT, "web", "step0-src", "components", "ProbeStep3.vue"),
            os.path.join(PROJECT_ROOT, "web", "step0-src", "plainCopy.js"),
            os.path.join(PROJECT_ROOT, "web", "step0-src", "useStep0.js"),
        ]
        for path in paths:
            self.assertTrue(os.path.isfile(path), f"缺少文件: {path}")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            for needle in forbidden:
                self.assertNotIn(
                    needle,
                    text,
                    f"{os.path.relpath(path, PROJECT_ROOT)} 仍含运营外泄文案: {needle}",
                )


if __name__ == "__main__":
    unittest.main()
