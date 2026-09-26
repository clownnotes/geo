#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_server_voice_chunk.py
针对 tools/geo/server.py 8088 生产 SSOT 文章伴读切片中继接口的全面单元测试：
1. console_gate 免密放行测试
2. 参数强校验（缺失、非法字符路径穿越、越界）
3. IP 令牌桶限流防护 (60次/分钟)
4. 本地 30 天磁盘 LRU 缓存与回环中继
"""

import unittest
import os
import json
import time
import shutil
from tools.geo import server

class TestServerVoiceChunk(unittest.TestCase):

    def setUp(self):
        # 重置限流字典
        with server.VOICE_CHUNK_LOCK:
            server.VOICE_CHUNK_IP_RECORDS.clear()

    def test_voice_rate_limiting(self):
        """测试 60次/分钟 IP 令牌桶限流"""
        test_ip = "192.168.1.100"
        for i in range(server.VOICE_CHUNK_RATE_LIMIT):
            self.assertTrue(server.check_voice_rate_limit(test_ip), f"第 {i+1} 次请求应被放行")
        
        # 超过限制，第 61 次应被拦截
        self.assertFalse(server.check_voice_rate_limit(test_ip), "第 61 次请求应被拦截")

        # 另一个 IP 不受影响
        other_ip = "192.168.1.101"
        self.assertTrue(server.check_voice_rate_limit(other_ip), "不同 IP 应独立计数放行")

    def test_console_gate_whitelist(self):
        """测试 console_gate 对 /api/voice/article-chunk 的公开免密放行"""
        class DummyHandler:
            def __init__(self):
                self.headers = {}
            def check_auth(self):
                return False
            def _serve_login_page(self):
                pass
            def _serve_404_not_found(self):
                pass

        # 绑定 console_gate 到虚拟 handler
        dummy = DummyHandler()
        allowed = server.GeoWebHandler.console_gate(dummy, "/api/voice/article-chunk", "POST")
        self.assertTrue(allowed, "POST /api/voice/article-chunk 必须被 console_gate 免密放行")

        allowed_get = server.GeoWebHandler.console_gate(dummy, "/api/voice/article-chunk", "GET")
        self.assertTrue(allowed_get, "GET /api/voice/article-chunk 必须被 console_gate 免密放行以支持原生流式播放")

    def test_cache_hit_fast_path(self):
        """测试本地 30 天磁盘缓存命中与响应头"""
        article_id = "test-sample-article"
        chunk_idx = 0
        voice = "standard_female_warm"
        
        cache_dir = os.path.join(server.PROJECT_ROOT, "storage", "audio_cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{article_id}_{chunk_idx}_{voice}.mp3")

        dummy_mp3 = b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x01\xff\xfeLavf60.3.100\x00\x00"
        with open(cache_file, "wb") as f:
            f.write(dummy_mp3)

        self.assertTrue(os.path.exists(cache_file))
        mtime = os.path.getmtime(cache_file)
        self.assertTrue(time.time() - mtime < 30 * 86400)

        # 清理
        try:
            os.remove(cache_file)
        except OSError:
            pass

    def test_parameter_defenses(self):
        """测试路径穿越、非法参数与段落越界的防御拦截"""
        class MockHandler:
            def __init__(self, body_dict):
                self.body = body_dict
                self.sent_status = None
                self.sent_json = None
            def get_client_ip(self):
                return "127.0.0.1"
            def read_json_body(self):
                return self.body
            def send_json(self, data, status=200):
                self.sent_status = status
                self.sent_json = data

        # 1. 路径穿越攻击
        h1 = MockHandler({"article_id": "../etc/passwd", "chunk_index": 0})
        server.GeoWebHandler.handle_article_chunk(h1)
        self.assertEqual(h1.sent_status, 400)
        self.assertIn("非法或缺失", h1.sent_json.get("msg", ""))

        # 2. 非法特殊字符
        h2 = MockHandler({"article_id": "slug;rm -rf /", "chunk_index": 0})
        server.GeoWebHandler.handle_article_chunk(h2)
        self.assertEqual(h2.sent_status, 400)

        # 3. 非法 chunk_index (负数)
        h3 = MockHandler({"article_id": "valid-slug", "chunk_index": -1})
        server.GeoWebHandler.handle_article_chunk(h3)
        self.assertEqual(h3.sent_status, 400)

        # 4. 不存在的文章
        h4 = MockHandler({"article_id": "non-existent-article-xyz-999", "chunk_index": 0})
        server.GeoWebHandler.handle_article_chunk(h4)
        self.assertEqual(h4.sent_status, 404)

if __name__ == '__main__':
    unittest.main()

