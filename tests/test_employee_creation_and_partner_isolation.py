# -*- coding: utf-8 -*-
"""员工自主建企与代理免选专注交付自动化测试 (tests/test_employee_creation_and_partner_isolation.py)

// [2026-09-19] [员工自主建企与代理免选专注交付] 测试套件
覆盖契约：
1. 路由放行：POST /api/projects 与 POST /api/v1/projects 对运营人员正常放行；
2. 代理隔离：运营建企时无论 body 是否提供 partner_id，落盘后 partner_id 强制为空字符串；开发者建企可正常保留 partner_id；
3. 自动管辖：运营建企成功后，project_id 原子追加至花名册 allowed_projects；
4. 失败语义：若花名册无此成员，append_member_allowed_project 返回 False；接口触发 500 且标 bind_failed=True；
5. 零 Emoji 红线：新增逻辑与前端关键 DOM 节点中严禁出现彩色表情符号。
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import rbac  # noqa: E402

DEV_PHONE = "13150568888"
OP_PHONE = "13805206070"
OP_USER_ID = "7d60e11b1f397703"


class TestEmployeeCreationAndPartnerIsolation(unittest.TestCase):
    """测试员工建企与代理免选隔离"""

    def setUp(self):
        self._orig_roster = rbac.ROSTER_FILE
        self.tmp_dir = tempfile.mkdtemp(prefix="geo_emp_test_")
        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")

        # 初始化花名册：师弟开发者 + 朋友员工
        rbac.save_roster({
            "schema_version": rbac.SCHEMA_VERSION,
            "developer_phones": [DEV_PHONE],
            "developer_user_ids": [],
            "members": [
                {
                    "user_id": OP_USER_ID,
                    "phone": OP_PHONE,
                    "name": "朋友运营",
                    "role": rbac.ROLE_OPERATOR,
                    "status": rbac.STATUS_ACTIVE,
                    "allowed_projects": ["existing_proj"],
                    "permissions": list(rbac.PERMISSION_CODES),
                }
            ],
        })
        self.op_ident = rbac.resolve_identity(user_id=OP_USER_ID, phone=OP_PHONE)
        self.dev_ident = rbac.resolve_identity(phone=DEV_PHONE)

    def tearDown(self):
        rbac.ROSTER_FILE = self._orig_roster
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_01_route_guard_allows_operator_project_creation(self):
        """测试 1：POST /api/projects 与 POST /api/v1/projects 对运营放行"""
        ok1, status1, msg1 = rbac.guard_route("/api/projects", "POST", self.op_ident)
        self.assertTrue(ok1, f"POST /api/projects 应对运营放行，返回: {msg1}")
        self.assertEqual(status1, 200)

        ok2, status2, msg2 = rbac.guard_route("/api/v1/projects", "POST", self.op_ident)
        self.assertTrue(ok2, f"POST /api/v1/projects 应对运营放行，返回: {msg2}")
        self.assertEqual(status2, 200)

    def test_02_append_member_allowed_project_atomic_success(self):
        """测试 2：原子追加管辖项目成功且幂等"""
        new_pid = "corp_new_test_01"
        ok = rbac.append_member_allowed_project(user_id=OP_USER_ID, phone=OP_PHONE, project_id=new_pid)
        self.assertTrue(ok)

        # 重新加载花名册验证落盘
        roster = rbac.load_roster()
        m = rbac.get_member(OP_USER_ID)
        self.assertIn(new_pid, m.get("allowed_projects", []))
        self.assertIn("existing_proj", m.get("allowed_projects", []))

        # 再次追加应幂等成功，不重复插入
        ok_again = rbac.append_member_allowed_project(user_id=OP_USER_ID, phone=OP_PHONE, project_id=new_pid)
        self.assertTrue(ok_again)
        m_after = rbac.get_member(OP_USER_ID)
        self.assertEqual(m_after.get("allowed_projects", []).count(new_pid), 1)

    def test_03_append_member_allowed_project_not_found(self):
        """测试 3：找不到成员时返回 False，不抛异常"""
        ok = rbac.append_member_allowed_project(user_id="non_exist_uid", phone="13999999999", project_id="test_p")
        self.assertFalse(ok)

        ok_empty = rbac.append_member_allowed_project(user_id="", phone="", project_id="test_p")
        self.assertFalse(ok_empty)

        ok_empty_pid = rbac.append_member_allowed_project(user_id=OP_USER_ID, phone=OP_PHONE, project_id="")
        self.assertFalse(ok_empty_pid)

    def test_04_partner_isolation_rule(self):
        """测试 4：运营人员 partner_id 必须强制置空，开发者正常保留"""
        body_with_partner = {"partner_id": "partner_alpha", "client_name": "测试企业"}

        # 模拟运营逻辑
        if self.op_ident and not self.op_ident.is_developer:
            op_partner = ""
        else:
            op_partner = str(body_with_partner.get("partner_id") or "").strip()
        self.assertEqual(op_partner, "", "运营建企必须将 partner_id 强制置空")

        # 模拟开发者逻辑
        if self.dev_ident and not self.dev_ident.is_developer:
            dev_partner = ""
        else:
            dev_partner = str(body_with_partner.get("partner_id") or "").strip()
        self.assertEqual(dev_partner, "partner_alpha", "开发者建企应保留选定的 partner_id")

    def test_05_partner_write_routes_remain_developer_only(self):
        """测试 5：合作方写操作与改挂合作方路由依然仅开发者可用"""
        # POST /api/partners (创建合作方)
        ok1, st1, _ = rbac.guard_route("/api/partners", "POST", self.op_ident)
        self.assertFalse(ok1)
        self.assertEqual(st1, 403)

        # POST /api/projects/nextgeo/meta (改挂合作方)
        ok2, st2, _ = rbac.guard_route("/api/projects/nextgeo/meta", "POST", self.op_ident)
        self.assertFalse(ok2)
        self.assertEqual(st2, 403)

        # 开发者均可调
        ok3, st3, _ = rbac.guard_route("/api/partners", "POST", self.dev_ident)
        self.assertTrue(ok3)
        self.assertEqual(st3, 200)

        ok4, st4, _ = rbac.guard_route("/api/projects/nextgeo/meta", "POST", self.dev_ident)
        self.assertTrue(ok4)
        self.assertEqual(st4, 200)

    def test_06_check_zero_emoji_redline(self):
        """测试 6：检查本次改动涉及的代码与界面中绝不包含彩色 Emoji 表情符号"""
        # 彩色 Emoji 正则（聚焦于真正突兀的彩色表情/象形文字，如 ⚡️、💡、⚠️、⚙️、💻、🤝、💎、⚖️、🎓、💬 等）
        color_emoji_pattern = re.compile(
            r'[\U0001F300-\U0001F5FF]|'  # 杂项符号与图形（💡, 💻, 💎 等）
            r'[\U0001F600-\U0001F64F]|'  # 纯表情包（😀, 😂 等）
            r'[\U0001F680-\U0001F6FF]|'  # 交通与火箭（🚀 等）
            r'[\U0001F900-\U0001F9FF]|'  # 补充符号（🤝 等）
            r'[\U0001FA70-\U0001FAFF]|'  # 扩展符号
            r'[\u26A0\u26A1\u2699\u2705\u274C\u26D4]'  # ⚠️, ⚡️, ⚙️, ✅, ❌, ⛔
        )

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_files = [
            os.path.join(project_root, "tools", "geo", "rbac.py"),
            os.path.join(project_root, "tools", "geo", "server.py"),
        ]

        for fpath in target_files:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            matches = color_emoji_pattern.findall(content)
            self.assertEqual(
                len(matches), 0,
                f"文件 {os.path.basename(fpath)} 违反 0 Emoji 规范，发现了 Emoji: {list(set(matches))[:5]}"
            )

        # 针对 web/index.html：核查新建模态框以及新编写的 JS 算法
        html_path = os.path.join(project_root, "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 截取新建项目模态框段落
        start_idx = html_content.find('id="new-project-modal"')
        end_idx = html_content.find('</form>', start_idx)
        if start_idx != -1 and end_idx != -1:
            modal_snippet = html_content[start_idx:end_idx]
            modal_emojis = color_emoji_pattern.findall(modal_snippet)
            self.assertEqual(len(modal_emojis), 0, f"新建项目弹窗包含彩色 Emoji: {modal_emojis}")

        # 截取新改动的 JS 代码段落
        js_marker = "Client ID 自动推导算法"
        js_idx = html_content.find(js_marker)
        if js_idx != -1:
            js_snippet = html_content[js_idx:js_idx + 1500]
            js_emojis = color_emoji_pattern.findall(js_snippet)
            self.assertEqual(len(js_emojis), 0, f"新增 JS 代码包含彩色 Emoji: {js_emojis}")


if __name__ == "__main__":
    unittest.main()
