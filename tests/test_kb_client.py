# -*- coding: utf-8 -*-
"""
小毛驴知识库与公共素材上传客户端单测
"""

import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from tools.geo.kb_client import NextdoorKBClient


class TestKBClient(unittest.TestCase):

    def setUp(self):
        self.client = NextdoorKBClient(base_url="http://127.0.0.1:3001", source_client="geo")

    @patch("urllib.request.urlopen")
    def test_upload_file(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"code": 0, "msg": "success", "data": {"url": "https://cdn.example.com/logo.png"}}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.client.upload_file(
            token="test_jwt_123",
            file_bytes=b"PNG_FAKE_BYTES",
            filename="logo.png",
            content_type="image/png"
        )
        self.assertEqual(res.get("code"), 0)
        self.assertIn("url", res.get("data", {}))

        # 检查上游请求
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_full_url(), "http://127.0.0.1:3001/api/v1/community/uploads")
        self.assertEqual(req.headers.get("Vio-source-client"), "geo")
        self.assertEqual(req.headers.get("Authorization"), "Bearer test_jwt_123")

    @patch("urllib.request.urlopen")
    def test_add_document(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"code": 0, "msg": "success", "data": {"doc_id": "1768892187321049099"}}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.client.add_document(
            token="test_jwt_123",
            title="客户产品说明书",
            content="# 产品参数\n性能提升30%",
            doc_type="markdown",
            project_id="nextgeo"
        )
        self.assertEqual(res.get("code"), 0)
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_full_url(), "http://127.0.0.1:3001/api/kb/documents")

    @patch("urllib.request.urlopen")
    def test_chat_kb(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"code": 0, "msg": "success", "data": {"answer": "\xe8\xaf\xa5\xe4\xba\xa7\xe5\x93\x81\xe6\x80\xa7\xe8\x83\xbd\xe6\x8f\x90\xe5\x8d\x8730%"}}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.client.chat_kb(
            token="test_jwt_123",
            query="该产品的性能如何？",
            project_id="nextgeo"
        )
        self.assertEqual(res.get("code"), 0)
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_full_url(), "http://127.0.0.1:3001/api/kb/chat")


if __name__ == "__main__":
    unittest.main()
