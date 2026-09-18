# -*- coding: utf-8 -*-
"""单元测试：小毛驴统一账号认证 (SSO) 与鉴权中枢 (tests/test_auth_sso.py)"""

import io
import json
import os
import unittest
from unittest import mock

import tempfile
from tools.geo.auth_sso import (
    NextdoorAuthClient,
    DEFAULT_NEXTDOOR_BASE_URL,
    DEFAULT_SOURCE_CLIENT,
)
from tools.geo import server


class _FakeHTTPResponse:
    def __init__(self, data: dict, status: int = 200):
        self._raw = json.dumps(data).encode("utf-8")
        self._buf = io.BytesIO(self._raw)
        self.status = status

    def read(self):
        return self._buf.read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestAuthSSO(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_sessions_file = server.SESSIONS_FILE
        server.SESSIONS_FILE = os.path.join(self.tmp_dir.name, "sessions.json")
        self.client = NextdoorAuthClient(base_url="http://127.0.0.1:3001")
        self.client.clear_cache()
        server.ACTIVE_SESSIONS.clear()

    def tearDown(self):
        self.client.clear_cache()
        server.ACTIVE_SESSIONS.clear()
        server.SESSIONS_FILE = self.orig_sessions_file
        self.tmp_dir.cleanup()

    @mock.patch("urllib.request.urlopen")
    def test_login_success_and_snowflake_string(self, mock_urlopen):
        """验证登录成功且雪花 ID 强转为字符串，防止前端精度溢出"""
        # 模拟后端返回大整数雪花 ID
        fake_data = {
            "code": 0,
            "msg": "success",
            "data": {
                "token": "fake.jwt.token.abc",
                "user_id": 189238491028391023,
                "id": 189238491028391023,
                "name": "张工",
                "phone": "13150568888",
                "role": "admin",
                "credits": 500,
            }
        }
        mock_urlopen.return_value = _FakeHTTPResponse(fake_data)

        resp = self.client.login("13150568888", "correct_password")
        self.assertEqual(resp["code"], 0)
        self.assertIn("data", resp)
        self.assertEqual(resp["data"]["token"], "fake.jwt.token.abc")
        
        # 核心契约断言：雪花 ID 必须为 str
        self.assertIsInstance(resp["data"]["user_id"], str)
        self.assertEqual(resp["data"]["user_id"], "189238491028391023")
        self.assertIsInstance(resp["data"]["id"], str)
        self.assertEqual(resp["data"]["id"], "189238491028391023")

        # 验证自动建立内存缓存
        cached_user = self.client.verify_token("fake.jwt.token.abc")
        self.assertIsNotNone(cached_user)
        self.assertEqual(cached_user["name"], "张工")

    @mock.patch("urllib.request.urlopen")
    def test_login_failure_wrong_password(self, mock_urlopen):
        """验证密码错误时正确返回上游错误信封"""
        fake_data = {
            "code": 4001,
            "msg": "登录失败: 密码错误",
            "data": None
        }
        mock_urlopen.return_value = _FakeHTTPResponse(fake_data)

        resp = self.client.login("13150568888", "wrong_password")
        self.assertEqual(resp["code"], 4001)
        self.assertIn("密码错误", resp["msg"])
        self.assertIsNone(resp.get("data"))

    @mock.patch("urllib.request.urlopen")
    def test_get_me_profile(self, mock_urlopen):
        """验证通过 JWT 拉取个人资料画像"""
        fake_data = {
            "code": 0,
            "msg": "success",
            "data": {
                "id": 189238491028391099,
                "name": "李经理",
                "phone": "13800000000",
                "role": "editor",
                "credits": 120,
            }
        }
        mock_urlopen.return_value = _FakeHTTPResponse(fake_data)

        resp = self.client.get_me("jwt.test.token.xyz")
        self.assertEqual(resp["code"], 0)
        self.assertEqual(resp["data"]["name"], "李经理")
        self.assertIsInstance(resp["data"]["id"], str)
        self.assertEqual(resp["data"]["id"], "189238491028391099")

    @mock.patch("urllib.request.urlopen")
    def test_wechat_qr_proxy(self, mock_urlopen):
        """验证微信扫码二维码生成代理"""
        fake_data = {
            "code": 0,
            "msg": "success",
            "data": {
                "ticket": "qr_test_ticket_12345",
                "qr_url": "https://open.weixin.qq.com/connect/qrconnect?..."
            }
        }
        mock_urlopen.return_value = _FakeHTTPResponse(fake_data)

        resp = self.client.get_wechat_qr()
        self.assertEqual(resp["code"], 0)
        self.assertEqual(resp["data"]["ticket"], "qr_test_ticket_12345")

    @mock.patch("tools.geo.server.get_auth_client")
    def test_is_authenticated_with_remote_jwt(self, mock_get_client):
        """验证当本地无 session 时，自动向上游 Nextdoor 验证 JWT 并回填本地会话"""
        mock_client = mock.MagicMock()
        mock_client.verify_token.return_value = {
            "id": "189238491028391023",
            "name": "远程用户",
            "phone": "13912345678",
            "role": "admin",
            "credits": 999,
        }
        mock_get_client.return_value = mock_client

        token = "remote.jwt.token.valid"
        # 初始本地没有
        self.assertNotIn(token, server.ACTIVE_SESSIONS)

        authed = server.is_authenticated(token)
        self.assertTrue(authed)
        mock_client.verify_token.assert_called_once_with(token)

        # 检查回填
        self.assertIn(token, server.ACTIVE_SESSIONS)
        self.assertEqual(server.ACTIVE_SESSIONS[token]["username"], "远程用户")
        self.assertEqual(server.ACTIVE_SESSIONS[token]["source"], "nextdoor_jwt")

    @mock.patch("urllib.request.urlopen")
    def test_remove_hardcoded_credentials_bypass(self, mock_urlopen):
        """验证任务 2.5：废除旧版硬编码账密后门，即使传入原管理员手机号也必须通过小毛驴验证"""
        # 模拟 Nextdoor 拒绝此密码
        mock_urlopen.return_value = _FakeHTTPResponse({
            "code": 4001,
            "msg": "登录失败: 密码错误",
            "data": None
        })

        resp = self.client.login("13150568888", "17625188666")
        # 必须失败，绝不允许在本地因硬编码而后门放行
        self.assertEqual(resp["code"], 4001)
        self.assertIn("密码错误", resp["msg"])
        self.assertEqual(len(server.ACTIVE_SESSIONS), 0)


if __name__ == "__main__":
    unittest.main()
