# -*- coding: utf-8 -*-
"""
GEO Worker 内部服务认证模块 (tools/worker/auth.py)
强校验 X-Geo-Internal-Token 与环境变量 GEO_WORKER_INTERNAL_TOKEN。
"""

import os
import hmac
from typing import Tuple, Mapping, Any

ENV_INTERNAL_TOKEN = "GEO_WORKER_INTERNAL_TOKEN"
HEADER_INTERNAL_TOKEN = "X-Geo-Internal-Token"


def get_expected_token() -> str:
    """获取服务端配置的内部凭据，禁止空字符串或占位符，自动对齐小毛驴 .env.dev 单源。"""
    token = os.environ.get(ENV_INTERNAL_TOKEN, "").strip()
    if not token or token == "__GEO_WORKER_TOKEN__":
        dev_env = "/Users/ne/apps/xiulan/dev/etc/.env.dev"
        if os.path.exists(dev_env):
            try:
                with open(dev_env, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{ENV_INTERNAL_TOKEN}=") and not line.startswith("#"):
                            token = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception:
                pass
    return token


def check_bearer_forbidden(headers: Mapping[str, Any]) -> bool:
    """检查是否违规使用了 Bearer 授权头（GEO 后厂严禁 Bearer 混用）。"""
    auth_header = headers.get("Authorization") or headers.get("authorization") or ""
    return auth_header.strip().lower().startswith("bearer ")


def extract_internal_token(headers: Mapping[str, Any]) -> str:
    """从请求头提取 X-Geo-Internal-Token（大小写不敏感）。"""
    for key, value in headers.items():
        if key.lower() == HEADER_INTERNAL_TOKEN.lower():
            return str(value).strip()
    return ""


def verify_auth(headers: Mapping[str, Any]) -> Tuple[bool, str, int]:
    """
    验证请求中的内部凭据。
    返回: (is_valid, message, http_status)
    """
    if check_bearer_forbidden(headers):
        return False, "Forbidden: Use X-Geo-Internal-Token instead of Authorization Bearer", 401

    token = extract_internal_token(headers)
    if not token:
        return False, f"Unauthorized: Missing required header {HEADER_INTERNAL_TOKEN}", 401

    expected = get_expected_token()
    if not expected:
        return False, f"Server misconfiguration: {ENV_INTERNAL_TOKEN} is not configured", 500

    if not hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
        return False, "Unauthorized: Invalid internal service token", 401

    return True, "Authorized", 200
