# -*- coding: utf-8 -*-
"""小毛驴 Nextdoor 统一账号认证与 SSO 客户端 (tools/geo/auth_sso.py)

// [2026-09-18] [接入小毛驴统一API] 创建统一账号认证与单点登录客户端，废除本地硬编码账号
规范与契约：
1. 默认同机基地址：http://127.0.0.1:3001（禁止绕公网域名，支持 NEXTDOOR_BASE_URL 覆盖）；
2. 接入身份头：vio-source-client: geo；
3. 判定成功：code === 0；
4. 雪花 ID 全链路保证为 string（禁止 JS Number 溢出截断）；
5. 本地轻量缓存验证结果（TTL 60秒），降低对主后端的频繁网络请求。
"""

import json
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

# 默认同机配置与常量定义
DEFAULT_NEXTDOOR_BASE_URL = "http://127.0.0.1:3001"
DEFAULT_SOURCE_CLIENT = "geo"
DEFAULT_TIMEOUT_SEC = 10
TOKEN_CACHE_TTL_SEC = 60  # 校验通过缓存 60 秒


class NextdoorAuthClient:
    """小毛驴统一认证客户端 (单例/面向对象封装)"""

    def __init__(self, base_url: Optional[str] = None, source_client: Optional[str] = None):
        env_base = os.environ.get("NEXTDOOR_BASE_URL", "").strip()
        self.base_url = (base_url or env_base or DEFAULT_NEXTDOOR_BASE_URL).rstrip("/")
        self.source_client = source_client or os.environ.get("NEXTDOOR_SOURCE_CLIENT", DEFAULT_SOURCE_CLIENT)
        self.timeout = int(os.environ.get("NEXTDOOR_TIMEOUT_SEC", str(DEFAULT_TIMEOUT_SEC)))
        
        # 内存缓存结构：{ token: (user_dict, expire_timestamp) }
        self._token_cache: Dict[str, tuple] = {}
        self._cache_lock = threading.Lock()

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """底层网络调用与统一信封解析"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "vio-source-client": self.source_client,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                return json.loads(err_body)
            except Exception:
                return {
                    "code": e.code,
                    "msg": f"上游 Nextdoor HTTP 错误 ({e.code}): {e.reason}",
                    "data": None,
                }
        except urllib.error.URLError as e:
            return {
                "code": 502,
                "msg": f"无法连接小毛驴统一后端 ({self.base_url}): {e.reason}",
                "data": None,
            }
        except Exception as e:
            return {
                "code": 500,
                "msg": f"小毛驴统一后端请求异常: {str(e)}",
                "data": None,
            }

    def login(self, phone: str, password: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """手机号密码登录 -> POST /api/v1/xiulan/login"""
        payload: Dict[str, Any] = {
            "phone": str(phone).strip(),
            "password": str(password).strip(),
        }
        if device_id:
            payload["device_id"] = device_id
        
        resp = self._make_request("/api/v1/xiulan/login", method="POST", payload=payload)
        
        # 统一规范化雪花 ID 为字符串，防止前端精度丢失
        if resp.get("code") == 0 and isinstance(resp.get("data"), dict):
            data = resp["data"]
            if "user_id" in data:
                data["user_id"] = str(data["user_id"])
            if "id" in data:
                data["id"] = str(data["id"])
            
            # 记录缓存
            tok = data.get("token")
            if tok:
                with self._cache_lock:
                    self._token_cache[tok] = (data, time.time() + TOKEN_CACHE_TTL_SEC)

        return resp

    def get_me(self, token: str) -> Dict[str, Any]:
        """获取当前登录用户画像 -> GET /api/v1/xiulan/me"""
        if not token:
            return {"code": 401, "msg": "Token 不能为空", "data": None}
            
        resp = self._make_request("/api/v1/xiulan/me", method="GET", token=token)
        if resp.get("code") == 0 and isinstance(resp.get("data"), dict):
            data = resp["data"]
            if "id" in data:
                data["id"] = str(data["id"])
            if "user_id" in data:
                data["user_id"] = str(data["user_id"])
            with self._cache_lock:
                self._token_cache[token] = (data, time.time() + TOKEN_CACHE_TTL_SEC)
        return resp

    def get_wechat_qr(self) -> Dict[str, Any]:
        """微信扫码登录二维码生成 -> GET /api/auth/wechat-qr"""
        return self._make_request("/api/auth/wechat-qr", method="GET")

    def wx_login(self, code: str, app_id: str = "") -> Dict[str, Any]:
        """微信快捷登录 -> POST /api/v1/community/auth/wx-login"""
        payload = {"code": code, "app_id": app_id}
        resp = self._make_request("/api/v1/community/auth/wx-login", method="POST", payload=payload)
        if resp.get("code") == 0 and isinstance(resp.get("data"), dict):
            data = resp["data"]
            if "user_id" in data:
                data["user_id"] = str(data["user_id"])
            tok = data.get("token")
            if tok:
                with self._cache_lock:
                    self._token_cache[tok] = (data, time.time() + TOKEN_CACHE_TTL_SEC)
        return resp

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌有效性：先查缓存，过期或缺失时调用 /api/v1/xiulan/me 验真"""
        if not token:
            return None

        now = time.time()
        with self._cache_lock:
            cached = self._token_cache.get(token)
            if cached and cached[1] > now:
                return cached[0]

        # 缓存未命中或过期，向上游验证
        resp = self.get_me(token)
        if resp.get("code") == 0 and isinstance(resp.get("data"), dict):
            return resp["data"]

        # 验证失败，从缓存中清理
        with self._cache_lock:
            self._token_cache.pop(token, None)
        return None

    def clear_cache(self):
        """清空会话验真缓存"""
        with self._cache_lock:
            self._token_cache.clear()


# 全局单例客户端
_GLOBAL_CLIENT: Optional[NextdoorAuthClient] = None
_CLIENT_LOCK = threading.Lock()


def get_auth_client() -> NextdoorAuthClient:
    """获取或初始化统一认证单例"""
    global _GLOBAL_CLIENT
    with _CLIENT_LOCK:
        if _GLOBAL_CLIENT is None:
            _GLOBAL_CLIENT = NextdoorAuthClient()
        return _GLOBAL_CLIENT
