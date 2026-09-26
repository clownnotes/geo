#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_server_voice_chunk.py
针对 tools/geo/server.py 8088 生产 SSOT 文章伴读切片中继接口的全面单元测试：
1. console_gate 免密放行测试 (GET / POST)
2. 参数强校验（缺失、非法字符路径穿越、voice 目录逃逸、越界）
3. IP 令牌桶限流防护 (60次/分钟) 与防伪造 X-Forwarded-For 穿透
4. 字典内存淘汰 (TTL Cleanup) 防内存膨胀
5. 本地 30 天磁盘 LRU 真实缓存命中与 _send_audio_data 调度
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
            server.VOICE_CHUNK_LAST_CLEANUP = 0

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

    def test_rate_limiting_ttl_cleanup(self):
        """测试过期 IP 记录自动淘汰，防止内存无界增长"""
        now = time.time()
        with server.VOICE_CHUNK_LOCK:
            # 注入一个 120 秒前过期的旧 IP 记录
            server.VOICE_CHUNK_IP_RECORDS["expired_ip_1"] = [now - 120.0]
            server.VOICE_CHUNK_IP_RECORDS["active_ip_1"] = [now - 5.0]
            server.VOICE_CHUNK_LAST_CLEANUP = now - 100.0  # 触发全局清理阈值

        # 发起一次请求触发清理
        server.check_voice_rate_limit("new_ip_2")

        with server.VOICE_CHUNK_LOCK:
            self.assertNotIn("expired_ip_1", server.VOICE_CHUNK_IP_RECORDS, "过期 IP 记录应被清理")
            self.assertIn("active_ip_1", server.VOICE_CHUNK_IP_RECORDS, "活跃 IP 记录必须保留")

    def test_get_client_ip_anti_spoofing(self):
        """测试 get_client_ip 防伪造头绕过与可信代理提取"""
        class MockReq:
            def __init__(self, direct_ip, headers):
                self.client_address = (direct_ip, 12345)
                self.headers = headers

        # 场景 A: 直连请求（非本机反代），完全忽略任何伪造的 X-Forwarded-For 与 X-Real-IP
        req_direct = MockReq("203.0.113.88", {
            "X-Forwarded-For": "1.1.1.1, 2.2.2.2",
            "X-Real-IP": "3.3.3.3"
        })
        ip_direct = server.GeoWebHandler.get_client_ip(req_direct)
        self.assertEqual(ip_direct, "203.0.113.88", "公网直连对端必须直接采信物理套接字 IP，绝不信任伪造头")

        # 场景 B: 来自本机反向代理 (127.0.0.1)，优先采信反代覆盖的 X-Real-IP
        req_proxy_real = MockReq("127.0.0.1", {
            "X-Forwarded-For": "203.0.113.7, 198.51.100.15",
            "X-Real-IP": "198.51.100.15"
        })
        ip_proxy_real = server.GeoWebHandler.get_client_ip(req_proxy_real)
        self.assertEqual(ip_proxy_real, "198.51.100.15")

        # 场景 C: 来自本机反向代理，客户端在 X-Forwarded-For 前插伪造 IP，必须取列表最后一位真实 IP
        req_proxy_xff = MockReq("127.0.0.1", {
            "X-Forwarded-For": "203.0.113.7, 198.51.100.22"
        })
        ip_proxy_xff = server.GeoWebHandler.get_client_ip(req_proxy_xff)
        self.assertEqual(ip_proxy_xff, "198.51.100.22", "必须提取反代追加在末尾的真实客户端 IP")

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

        dummy = DummyHandler()
        allowed = server.GeoWebHandler.console_gate(dummy, "/api/voice/article-chunk", "POST")
        self.assertTrue(allowed, "POST /api/voice/article-chunk 必须被 console_gate 免密放行")

        allowed_get = server.GeoWebHandler.console_gate(dummy, "/api/voice/article-chunk", "GET")
        self.assertTrue(allowed_get, "GET /api/voice/article-chunk 必须被 console_gate 免密放行以支持原生流式播放")

    def test_cache_hit_fast_path(self):
        """测试本地 30 天磁盘真实缓存命中分支与 _send_audio_data 调度"""
        article_id = "test-sample-article-hit"
        chunk_idx = 0
        voice = "standard_female_warm"
        
        cache_dir = os.path.join(server.PROJECT_ROOT, "storage", "audio_cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{article_id}_{chunk_idx}_{voice}.mp3")

        dummy_mp3 = b"ID3_DUMMY_MP3_DATA_FOR_CACHE_HIT_TEST"
        with open(cache_file, "wb") as f:
            f.write(dummy_mp3)

        try:
            class MockCacheHitHandler:
                def __init__(self):
                    self.command = "POST"
                    self.sent_audio = None
                    self.cache_tag = None
                def get_client_ip(self):
                    return "127.0.0.1"
                def read_json_body(self):
                    return {
                        "article_id": article_id,
                        "chunk_index": chunk_idx,
                        "voice": voice
                    }
                def _send_audio_data(self, audio_data, cache_hit):
                    self.sent_audio = audio_data
                    self.cache_tag = cache_hit

            h = MockCacheHitHandler()
            server.GeoWebHandler.handle_article_chunk(h)

            self.assertEqual(h.cache_tag, "HIT", "缓存命中必须标记 HIT")
            self.assertEqual(h.sent_audio, dummy_mp3, "必须透传本地缓存文件的完整二进制内容")
        finally:
            if os.path.exists(cache_file):
                os.remove(cache_file)

    def test_parameter_defenses(self):
        """测试路径穿越、voice目录逃逸、非法参数与段落越界的防御拦截"""
        class MockHandler:
            def __init__(self, body_dict):
                self.command = "POST"
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

        # 1. article_id 路径穿越攻击
        h1 = MockHandler({"article_id": "../etc/passwd", "chunk_index": 0, "voice": "standard_female_warm"})
        server.GeoWebHandler.handle_article_chunk(h1)
        self.assertEqual(h1.sent_status, 400)
        self.assertIn("非法或缺失的 article_id", h1.sent_json.get("msg", ""))

        # 2. voice 路径穿越逃逸攻击
        h_voice = MockHandler({"article_id": "valid-slug", "chunk_index": 0, "voice": "../../../../escape"})
        server.GeoWebHandler.handle_article_chunk(h_voice)
        self.assertEqual(h_voice.sent_status, 400)
        self.assertIn("非法或缺失的 voice", h_voice.sent_json.get("msg", ""))

        # 3. 非法特殊字符
        h2 = MockHandler({"article_id": "slug;rm -rf /", "chunk_index": 0})
        server.GeoWebHandler.handle_article_chunk(h2)
        self.assertEqual(h2.sent_status, 400)

        # 4. 非法 chunk_index (负数)
        h3 = MockHandler({"article_id": "valid-slug", "chunk_index": -1})
        server.GeoWebHandler.handle_article_chunk(h3)
        self.assertEqual(h3.sent_status, 400)

        # 5. 不存在的文章
        h4 = MockHandler({"article_id": "non-existent-article-xyz-999", "chunk_index": 0})
        server.GeoWebHandler.handle_article_chunk(h4)
        self.assertEqual(h4.sent_status, 404)

if __name__ == '__main__':
    unittest.main()
