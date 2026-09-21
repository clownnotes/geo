# -*- coding: utf-8 -*-
"""测试 opsguard 频控与严防自动封禁账号 (tests/test_opsguard_no_auto_ban.py)

// [2026-09-21] [阶段一帮助提示剥离与连点封禁逻辑废除]
验证：
1. 运营正常请求放行；
2. 超过请求频次返回 429 提示；
3. 核心铁律：即使短时间内连续触发十几次、几十次 429 频控，账号依然为 active，绝不自动停用！
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.geo import opsguard, rbac  # noqa: E402


class OpsGuardNoAutoBanTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.orig_roster_file = rbac.ROSTER_FILE
        self.orig_audit_file = opsguard.AUDIT_FILE
        self.orig_data_dir = opsguard.DATA_DIR

        rbac.ROSTER_FILE = os.path.join(self.tmp_dir, "rbac_members.json")
        opsguard.AUDIT_FILE = os.path.join(self.tmp_dir, "operator_audit.jsonl")
        opsguard.DATA_DIR = self.tmp_dir

        # 初始化花名册
        self.test_phone = "13800008888"
        self.test_uid = "test_operator_uid_123"
        init_roster = {
            "schema_version": 1,
            "developer_phones": ["13150568888"],
            "developer_user_ids": [],
            "members": [
                {
                    "user_id": self.test_uid,
                    "phone": self.test_phone,
                    "name": "测试运营",
                    "role": "operator",
                    "status": "active",
                    "allowed_projects": ["test_proj"],
                    "permissions": ["report:view"],
                    "created_at": "2026-09-21 12:00:00",
                    "updated_at": "2026-09-21 12:00:00",
                }
            ],
        }
        rbac.save_roster(init_roster)

        # 清空 opsguard 内存状态
        with opsguard._LOCK:
            opsguard._REQ_LOG.clear()
            opsguard._HOUR_BUCKET.clear()

        self.ident = rbac.resolve_identity(user_id=self.test_uid, phone=self.test_phone)

    def tearDown(self):
        rbac.ROSTER_FILE = self.orig_roster_file
        opsguard.AUDIT_FILE = self.orig_audit_file
        opsguard.DATA_DIR = self.orig_data_dir

    def test_rate_limit_returns_429_but_never_disables_account(self):
        """测试连续触发频控不会将账号置为 disabled"""
        # 发送超过 REQ_PER_MINUTE (300) 次请求
        for _ in range(opsguard.REQ_PER_MINUTE):
            ok, st, _ = opsguard.check(self.ident, "/api/projects/test_proj/data", "GET")
            self.assertTrue(ok)
            self.assertEqual(st, 200)

        # 连续触发 25 次 429
        for i in range(25):
            ok, st, msg = opsguard.check(self.ident, "/api/projects/test_proj/data", "GET")
            self.assertFalse(ok)
            self.assertEqual(st, 429, f"第 {i+1} 次应该返回 429，而不是封禁 403")
            self.assertIn("处理中", msg)

        # 验证花名册中的账号状态绝对依然是 active
        roster = rbac.load_roster()
        member = roster["members"][0]
        self.assertEqual(member["status"], "active", "连续连击/频控绝不允许自动将账号停用！")


if __name__ == "__main__":
    unittest.main()
