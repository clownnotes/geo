# -*- coding: utf-8 -*-
"""Nextdoor 开放 API 作为默认 LLM 入口的单元测试。"""

import io
import json
import os
import tempfile
import unittest
from unittest import mock

from tools.geo import llm as llm_mod
from tools.geo.llm import (
    LlmUnavailable,
    _aggregate_sse_stream,
    _extract_sse_delta_content,
    build_llm_status_payload,
    call_nextdoor_chat,
    call_via_runtime,
    clear_status_cache,
    resolve_llm_runtime,
    resolve_nextdoor_runtime,
    save_llm_config,
    atomic_write_env,
)
from tools.geo.utils import call_llm_api


class _FakeSSEResp:
    def __init__(self, lines):
        self._buf = io.BytesIO("\n".join(lines).encode("utf-8") + b"\n")

    def readline(self):
        return self._buf.readline()


class TestNextdoorRuntime(unittest.TestCase):
    def setUp(self):
        clear_status_cache()
        self._env_backup = dict(os.environ)
        for k in list(os.environ.keys()):
            if k.startswith("NEXTDOOR_") or k in ("GEO_LLM_DIRECT", "DEEPSEEK_API_KEY", "ARK_API_KEY"):
                os.environ.pop(k, None)
        llm_mod._DOTENV_KEYS.clear()
        llm_mod._ENV_LOADED = True

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        clear_status_cache()

    def test_default_prefers_nextdoor_over_deepseek(self):
        os.environ["DEEPSEEK_API_KEY"] = "sk-should-not-win"
        os.environ["NEXTDOOR_JWT_TOKEN"] = "eyJhbGciOi.test.jwt.tokenvalue"
        rt = resolve_llm_runtime()
        self.assertIsNotNone(rt)
        self.assertEqual(rt["provider"], "nextdoor")
        self.assertEqual(rt["brand"], "geo")
        self.assertEqual(rt["mode"], "auto")
        self.assertEqual(rt["model"], "dedicated_chain")
        self.assertIn("调度档", rt["mode_label"])
        self.assertIn("auto", rt["mode_label"])

    def test_direct_flag_uses_vendor(self):
        os.environ["GEO_LLM_DIRECT"] = "1"
        os.environ["DEEPSEEK_API_KEY"] = "sk-direct-key-abcdef"
        os.environ["NEXTDOOR_JWT_TOKEN"] = "eyJ-should-ignore"
        rt = resolve_llm_runtime()
        self.assertEqual(rt["provider"], "deepseek")

    def test_no_jwt_returns_none(self):
        os.environ["DEEPSEEK_API_KEY"] = "sk-only"
        self.assertIsNone(resolve_nextdoor_runtime())
        self.assertIsNone(resolve_llm_runtime())

    def test_sse_delta_extract(self):
        obj = {"choices": [{"delta": {"content": "你好"}}]}
        self.assertEqual(_extract_sse_delta_content(obj), "你好")
        self.assertEqual(_extract_sse_delta_content({"_heartbeat": True}), "")
        self.assertEqual(_extract_sse_delta_content({"_hit": {"model": "x"}}), "")

    def test_sse_aggregate(self):
        lines = [
            'data: {"choices":[{"delta":{"content":"甲"}}]}',
            'data: {"_heartbeat": true}',
            'data: {"choices":[{"delta":{"content":"乙"}}]}',
            "data: [DONE]",
        ]
        text = _aggregate_sse_stream(_FakeSSEResp(lines))
        self.assertEqual(text, "甲乙")

    def test_call_via_runtime_nextdoor(self):
        runtime = {
            "provider": "nextdoor",
            "mode": "flash",
            "brand": "geo",
            "api_key": "jwt-x",
            "base_url": "http://127.0.0.1:3001",
        }
        with mock.patch("tools.geo.llm.call_nextdoor_chat", return_value="重构正文"):
            ok, text, prov = call_via_runtime(runtime, "提示", system_prompt="系统", timeout=5)
        self.assertTrue(ok)
        self.assertEqual(text, "重构正文")
        self.assertEqual(prov, "nextdoor")

    def test_prefers_api_key_over_jwt(self):
        os.environ["NEXTDOOR_JWT_TOKEN"] = "eyJ-old-jwt"
        os.environ["NEXTDOOR_API_KEY"] = "ndsk_machine_key_abcdefghijklmnop"
        rt = resolve_nextdoor_runtime()
        self.assertEqual(rt["api_key"], "ndsk_machine_key_abcdefghijklmnop")
        self.assertEqual(rt["auth_kind"], "api_key")

    def test_call_llm_api_without_config(self):
        ok, msg, prov = call_llm_api("hi")
        self.assertFalse(ok)
        self.assertEqual(prov, "none")
        self.assertIn("NEXTDOOR_API_KEY", msg)

    def test_status_nextdoor_fields(self):
        os.environ["NEXTDOOR_JWT_TOKEN"] = "eyJhbGciOi.abcdefghijklmnopqrstuvwxyz"
        os.environ["NEXTDOOR_SOURCE_CLIENT"] = "geo"
        with mock.patch("tools.geo.llm.ping_llm", return_value=("ready", 9)):
            payload = build_llm_status_payload(force_refresh=True)
        self.assertEqual(payload["provider"], "nextdoor")
        self.assertEqual(payload["brand"], "geo")
        self.assertEqual(payload["mode"], "auto")
        self.assertEqual(payload["model"], "dedicated_chain")
        self.assertIn("mode_label", payload)
        self.assertNotIn("api_key", payload)
        self.assertTrue(payload["api_key_masked"])

    def test_save_nextdoor_ping_fail_no_write(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            open(env_path, "w").close()
            with mock.patch("tools.geo.llm.ENV_PATH", env_path), \
                 mock.patch("tools.geo.llm.ping_llm", return_value=("auth_failed", 3)), \
                 mock.patch("tools.geo.llm.ensure_env_file", return_value=env_path):
                res = save_llm_config({
                    "provider": "nextdoor",
                    "jwt_token": "bad-jwt-token-value",
                })
            self.assertFalse(res["success"])
            with open(env_path, "r", encoding="utf-8") as f:
                self.assertNotIn("bad-jwt-token-value", f.read())

    def test_save_nextdoor_api_key_success(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            open(env_path, "w").close()
            with mock.patch("tools.geo.llm.ENV_PATH", env_path), \
                 mock.patch("tools.geo.llm.ping_llm", return_value=("ready", 11)), \
                 mock.patch("tools.geo.llm.ensure_env_file", return_value=env_path), \
                 mock.patch("tools.geo.llm.atomic_write_env") as aw:
                aw.side_effect = lambda updates, path=None: atomic_write_env(updates, env_path)
                res = save_llm_config({
                    "provider": "nextdoor",
                    "api_key": "ndsk_good_machine_key_abcdefghijklmn",
                    "source_client": "geo",
                    "mode": "flash",
                    "base_url": "http://127.0.0.1:3001",
                })
            self.assertTrue(res["success"])
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("NEXTDOOR_API_KEY=", content)
            self.assertIn("GEO_LLM_DIRECT=0", content)

    def test_call_nextdoor_falls_back_to_auto(self):
        runtime = {
            "provider": "nextdoor",
            "mode": "flash",
            "brand": "geo",
            "api_key": "ndsk_x",
            "base_url": "http://127.0.0.1:3001",
        }
        modes = []

        def fake_urlopen(req, timeout=0):
            import json as _json
            body = _json.loads(req.data.decode("utf-8"))
            modes.append(body["mode"])
            if body["mode"] == "flash":
                raise LlmUnavailable("flash pool down")
            class Resp:
                headers = {"Content-Type": "application/json"}
                def read(self):
                    return _json.dumps({
                        "code": 0,
                        "data": {"choices": [{"message": {"content": "ok-auto"}}]},
                    }).encode("utf-8")
                def __enter__(self): return self
                def __exit__(self, *a): pass
            return Resp()

        with mock.patch("tools.geo.llm.urllib.request.urlopen", side_effect=fake_urlopen):
            # stream=False 避免走 SSE 分支
            text = call_nextdoor_chat(runtime, [{"role": "user", "content": "hi"}], timeout=5, stream=False)
        self.assertEqual(text, "ok-auto")
        self.assertEqual(modes, ["flash", "auto"])


if __name__ == "__main__":
    unittest.main()
