# -*- coding: utf-8 -*-
"""大模型 API 客户端与统一运行时解析（零第三方依赖）。

唯一解析入口：resolve_llm_runtime()
默认走小毛驴 Nextdoor 开放 API（JWT + vio-source-client）；
仅 GEO_LLM_DIRECT=1 时走厂商 OpenAI 兼容直连。
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(_TOOLS_DIR))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# 记录从 .env 文件加载的键名（用于 source 溯源）
_DOTENV_KEYS: set = set()
_ENV_LOADED = False

# status TTL 缓存
_STATUS_CACHE: Dict[str, Any] = {"payload": None, "ts": 0.0}
_STATUS_LOCK = threading.Lock()
STATUS_TTL_SECONDS = 60

DEFAULT_NEXTDOOR_BASE_URL = "http://127.0.0.1:3001"
DEFAULT_NEXTDOOR_SOURCE_CLIENT = "geo"
DEFAULT_NEXTDOOR_CHAT_MODE = "flash"

# Web 配置允许写入的环境变量白名单
CONFIG_WRITE_WHITELIST = frozenset({
    # Nextdoor 主路径
    "NEXTDOOR_BASE_URL",
    "NEXTDOOR_JWT_TOKEN",
    "NEXTDOOR_SOURCE_CLIENT",
    "NEXTDOOR_CHAT_MODE",
    "GEO_LLM_DIRECT",
    # 应急直连（仅 GEO_LLM_DIRECT=1）
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_BASE_URL",
    "ARK_API_KEY",
    "DOUBAO_API_KEY",
    "DOUBAO_MODEL",
    "ARK_BASE_URL",
    "GEO_LLM_API_KEY",
    "GEO_LLM_BASE_URL",
    "GEO_LLM_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
})

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        # 主写入键在前；GEO_* 仅兼容只读
        "api_key_envs": ["DEEPSEEK_API_KEY", "GEO_DEEPSEEK_API_KEY"],
        "model_envs": ["DEEPSEEK_MODEL"],
        "base_url_envs": ["DEEPSEEK_BASE_URL"],
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-pro-32k",
        "api_key_envs": ["ARK_API_KEY", "DOUBAO_API_KEY", "GEO_DOUBAO_API_KEY"],
        "model_envs": ["DOUBAO_MODEL", "GEO_DOUBAO_ENDPOINT_ID", "DOUBAO_ENDPOINT_ID", "DOUBAO_ARK_MODEL"],
        "base_url_envs": ["ARK_BASE_URL"],
    },
    "openai_compatible": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "api_key_envs": ["GEO_LLM_API_KEY", "OPENAI_API_KEY"],
        "model_envs": ["GEO_LLM_MODEL", "OPENAI_MODEL"],
        "base_url_envs": ["GEO_LLM_BASE_URL", "OPENAI_BASE_URL"],
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "api_key_envs": ["GEO_KIMI_API_KEY", "MOONSHOT_API_KEY"],
        "model_envs": ["KIMI_MODEL", "MOONSHOT_MODEL"],
        "base_url_envs": [],
    },
    "yuanbao": {
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "default_model": "hunyuan-standard",
        "api_key_envs": ["GEO_YUANBAO_API_KEY", "YUANBAO_API_KEY", "HUNYUAN_API_KEY"],
        "model_envs": ["YUANBAO_MODEL", "HUNYUAN_MODEL"],
        "base_url_envs": [],
    },
}

# 主链路探测顺序（与 utils 历史行为一致）
RUNTIME_PROVIDER_ORDER = ("deepseek", "doubao", "openai_compatible")


class LlmUnavailable(RuntimeError):
    pass


def ensure_env_file(path: str = None) -> str:
    """确保 .env 存在；缺失则创建空文件（权限 0600）。"""
    env_path = path or ENV_PATH
    if not os.path.exists(env_path):
        fd = os.open(env_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
        try:
            os.write(fd, b"# GEO LLM configuration (gitignored)\n")
        finally:
            os.close(fd)
    return env_path


def load_dotenv(path: str = None, override: bool = True) -> None:
    """加载 .env；默认覆盖 os.environ（禁止 setdefault 被旧 OS 值压死）。"""
    global _ENV_LOADED, _DOTENV_KEYS
    env_path = ensure_env_file(path)
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        _ENV_LOADED = True
        return

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = val
            _DOTENV_KEYS.add(key)
    _ENV_LOADED = True


def _ensure_loaded() -> None:
    if not _ENV_LOADED:
        load_dotenv(override=True)


def _first_env(names: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """返回 (value, env_name)。"""
    for name in names:
        val = os.environ.get(name)
        if val and str(val).strip():
            return str(val).strip(), name
    return None, None


def _source_for_key(env_name: Optional[str]) -> str:
    if not env_name:
        return "none"
    if env_name in _DOTENV_KEYS:
        return ".env"
    return "env"


def resolve_api_key(model: str) -> Optional[str]:
    """按链式降级顺序读取模型 API Key。"""
    _ensure_loaded()
    conf = PROVIDERS.get(model)
    if not conf:
        return None
    val, _ = _first_env(conf.get("api_key_envs", []))
    return val


def resolve_model_name(model: str) -> str:
    _ensure_loaded()
    conf = PROVIDERS.get(model)
    if not conf:
        return model
    val, _ = _first_env(conf.get("model_envs", []))
    if val:
        return val
    return conf.get("default_model", model)


def resolve_base_url(model: str) -> str:
    _ensure_loaded()
    conf = PROVIDERS.get(model)
    if not conf:
        return ""
    val, _ = _first_env(conf.get("base_url_envs", []))
    if val:
        return val.rstrip("/")
    return str(conf.get("base_url", "")).rstrip("/")


def available(model: str) -> bool:
    return resolve_api_key(model) is not None


def _direct_enabled() -> bool:
    return os.environ.get("GEO_LLM_DIRECT", "").strip().lower() in ("1", "true", "yes", "on")


def resolve_nextdoor_runtime() -> Optional[Dict[str, Any]]:
    """解析 Nextdoor 开放 API 运行时（需 JWT）。"""
    _ensure_loaded()
    jwt, key_env = _first_env(["NEXTDOOR_JWT_TOKEN"])
    if not jwt:
        return None
    base_val, _ = _first_env(["NEXTDOOR_BASE_URL"])
    brand_val, _ = _first_env(["NEXTDOOR_SOURCE_CLIENT"])
    mode_val, _ = _first_env(["NEXTDOOR_CHAT_MODE"])
    mode = (mode_val or DEFAULT_NEXTDOOR_CHAT_MODE).strip().lower()
    if mode not in ("flash", "think", "auto"):
        mode = DEFAULT_NEXTDOOR_CHAT_MODE
    return {
        "configured": True,
        "provider": "nextdoor",
        "model": mode,  # 专属链下不改梯队；字段复用给 Tag 展示
        "mode": mode,
        "brand": (brand_val or DEFAULT_NEXTDOOR_SOURCE_CLIENT).strip() or DEFAULT_NEXTDOOR_SOURCE_CLIENT,
        "api_key": jwt,
        "base_url": (base_val or DEFAULT_NEXTDOOR_BASE_URL).rstrip("/"),
        "source": _source_for_key(key_env),
        "key_env": key_env,
    }


def resolve_direct_runtime() -> Optional[Dict[str, Any]]:
    """厂商 OpenAI 兼容直连（仅 GEO_LLM_DIRECT=1）。"""
    _ensure_loaded()
    for provider in RUNTIME_PROVIDER_ORDER:
        conf = PROVIDERS[provider]
        api_key, key_env = _first_env(conf.get("api_key_envs", []))
        if not api_key:
            continue
        model_val, _ = _first_env(conf.get("model_envs", []))
        base_val, _ = _first_env(conf.get("base_url_envs", []))
        return {
            "configured": True,
            "provider": provider,
            "model": model_val or conf["default_model"],
            "mode": None,
            "brand": None,
            "api_key": api_key,
            "base_url": (base_val or conf["base_url"]).rstrip("/"),
            "source": _source_for_key(key_env),
            "key_env": key_env,
        }
    return None


def resolve_llm_runtime() -> Optional[Dict[str, Any]]:
    """统一运行时：默认 Nextdoor；GEO_LLM_DIRECT=1 时厂商直连。"""
    _ensure_loaded()
    if _direct_enabled():
        return resolve_direct_runtime()
    return resolve_nextdoor_runtime()


def mask_api_key(api_key: Optional[str]) -> str:
    if not api_key:
        return ""
    if len(api_key) < 8:
        return "*" * len(api_key)
    if len(api_key) > 24:
        return f"{api_key[:6]}…{api_key[-4:]}"
    return f"{api_key[:2]}****{api_key[-4:]}"


def clear_status_cache() -> None:
    with _STATUS_LOCK:
        _STATUS_CACHE["payload"] = None
        _STATUS_CACHE["ts"] = 0.0


def _extract_sse_delta_content(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""
    if obj.get("_heartbeat") or obj.get("_hit") or obj.get("_queue"):
        return ""
    if obj.get("event") == "error":
        return ""
    choices = obj.get("choices")
    if isinstance(choices, list) and choices:
        delta = choices[0].get("delta") if isinstance(choices[0], dict) else None
        if isinstance(delta, dict):
            return str(delta.get("content") or "")
        if isinstance(delta, str):
            return delta
        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(msg, dict):
            return str(msg.get("content") or "")
    delta = obj.get("delta")
    if isinstance(delta, str):
        return delta
    if isinstance(delta, dict):
        return str(delta.get("content") or "")
    return ""


def _aggregate_sse_stream(resp) -> str:
    parts: List[str] = []
    err_msg = None
    while True:
        raw = resp.readline()
        if not raw:
            break
        line = raw.decode("utf-8", errors="ignore").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and (obj.get("event") == "error" or (obj.get("code") and obj.get("code") != 0 and "choices" not in obj)):
            err_msg = obj.get("msg") or obj.get("message") or str(obj.get("code"))
            continue
        chunk = _extract_sse_delta_content(obj)
        if chunk:
            parts.append(chunk)
    text = "".join(parts).strip()
    if not text and err_msg:
        raise LlmUnavailable(f"Nextdoor SSE 错误: {err_msg}")
    return text


def call_nextdoor_chat(
    runtime: Dict[str, Any],
    messages: List[Dict[str, str]],
    timeout: int = 120,
    stream: bool = True,
) -> str:
    """调用 POST /api/v1/xiulan/chat；默认 SSE 聚合正文。"""
    base = runtime["base_url"].rstrip("/")
    endpoint = f"{base}/api/v1/xiulan/chat"
    payload = {
        "mode": runtime.get("mode") or DEFAULT_NEXTDOOR_CHAT_MODE,
        "messages": messages,
        "stream": bool(stream),
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {runtime['api_key']}",
        "vio-source-client": runtime.get("brand") or DEFAULT_NEXTDOOR_SOURCE_CLIENT,
        "Accept": "text/event-stream" if stream else "application/json",
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if stream or "text/event-stream" in ctype:
                return _aggregate_sse_stream(resp)
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        raise LlmUnavailable(f"Nextdoor HTTP {e.code}: {raw[:300]}") from e
    except LlmUnavailable:
        raise
    except Exception as exc:
        raise LlmUnavailable(f"Nextdoor 调用失败: {exc}") from exc

    if isinstance(body, dict) and body.get("code") not in (None, 0, "0"):
        raise LlmUnavailable(f"Nextdoor 业务错误: {body.get('msg') or body.get('code')}")
    data = body.get("data", body) if isinstance(body, dict) else body
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            msg = choices[0].get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if content:
                return str(content).strip()
        if data.get("content"):
            return str(data["content"]).strip()
    raise LlmUnavailable(f"Nextdoor 返回结构异常: {str(body)[:300]}")


def call_direct_chat(
    runtime: Dict[str, Any],
    messages: List[Dict[str, str]],
    timeout: int = 120,
    model_override: Optional[str] = None,
) -> str:
    target_model = runtime["model"]
    shorthands = {"deepseek", "doubao", "openai", "gpt", "ark", "qwen", "ernie", "openai_compatible", "nextdoor"}
    if model_override and model_override.lower() not in shorthands:
        target_model = model_override
    base_url = runtime["base_url"].rstrip("/")
    endpoint = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url
    payload = {"model": target_model, "messages": messages, "temperature": 0.3}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {runtime['api_key']}",
    }
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def call_via_runtime(
    runtime: Dict[str, Any],
    prompt: str,
    system_prompt: Optional[str] = None,
    timeout: int = 30,
    model_override: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """统一调用入口。返回 (ok, text_or_error, provider)。"""
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    provider = runtime.get("provider") or "none"
    try:
        if provider == "nextdoor":
            text = call_nextdoor_chat(runtime, messages, timeout=timeout, stream=True)
        else:
            text = call_direct_chat(runtime, messages, timeout=timeout, model_override=model_override)
        return True, text, provider
    except Exception as exc:
        return False, str(exc), provider


def ping_llm(runtime: Dict[str, Any], timeout: int = 10) -> Tuple[str, Optional[int]]:
    """
    探测连通性。
    返回 (status, latency_ms)：ready / auth_failed / unreachable
    """
    started = time.time()
    try:
        if runtime.get("provider") == "nextdoor":
            call_nextdoor_chat(
                runtime,
                [{"role": "user", "content": "ping"}],
                timeout=timeout,
                stream=False,
            )
            return "ready", int((time.time() - started) * 1000)
        base = runtime["base_url"].rstrip("/")
        endpoint = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base
        payload = {
            "model": runtime["model"],
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {runtime['api_key']}",
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
        return "ready", int((time.time() - started) * 1000)
    except urllib.error.HTTPError as e:
        latency = int((time.time() - started) * 1000)
        if e.code in (401, 403):
            return "auth_failed", latency
        if e.code in (400, 404, 422):
            return "ready", latency
        return "unreachable", latency
    except Exception as exc:
        latency = int((time.time() - started) * 1000)
        msg = str(exc).lower()
        if "401" in msg or "403" in msg or "鉴权" in msg or "unauthorized" in msg:
            return "auth_failed", latency
        return "unreachable", latency


def build_llm_status_payload(force_refresh: bool = False) -> Dict[str, Any]:
    """按白名单组装 status；禁止透传含明文 Key 的内部 dict。"""
    now = time.time()
    with _STATUS_LOCK:
        cached = _STATUS_CACHE.get("payload")
        ts = float(_STATUS_CACHE.get("ts") or 0)
        if (
            not force_refresh
            and cached is not None
            and (now - ts) < STATUS_TTL_SECONDS
        ):
            out = dict(cached)
            out["cached"] = True
            return out

    runtime = resolve_llm_runtime()
    if not runtime:
        payload = {
            "configured": False,
            "provider": None,
            "model": None,
            "mode": None,
            "brand": None,
            "base_url": None,
            "source": "none",
            "api_key_masked": "",
            "latency_ms": None,
            "status": "offline",
            "message": "未配置 NEXTDOOR_JWT_TOKEN（或未开启 GEO_LLM_DIRECT）",
            "cached": False,
        }
    else:
        status, latency = ping_llm(runtime, timeout=10)
        payload = {
            "configured": True,
            "provider": runtime["provider"],
            "model": runtime.get("model"),
            "mode": runtime.get("mode"),
            "brand": runtime.get("brand"),
            "base_url": runtime["base_url"],
            "source": runtime["source"],
            "api_key_masked": mask_api_key(runtime["api_key"]),
            "latency_ms": latency,
            "status": status,
            "message": "",
            "cached": False,
        }

    with _STATUS_LOCK:
        _STATUS_CACHE["payload"] = {k: v for k, v in payload.items() if k != "cached"}
        _STATUS_CACHE["ts"] = now
    return payload


def _read_env_map(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            if key:
                data[key] = val.strip().strip('"').strip("'")
    return data


def atomic_write_env(updates: Dict[str, str], path: str = None) -> str:
    """合并写入 .env：tmp + os.replace；权限 0600；强制覆盖 os.environ。"""
    global _DOTENV_KEYS
    env_path = ensure_env_file(path)
    current = _read_env_map(env_path)
    for k, v in updates.items():
        if k not in CONFIG_WRITE_WHITELIST:
            raise ValueError(f"不允许写入环境变量: {k}")
        current[k] = v
        os.environ[k] = v
        _DOTENV_KEYS.add(k)

    lines = ["# GEO LLM configuration (gitignored)", ""]
    for k in sorted(current.keys()):
        lines.append(f"{k}={current[k]}")
    content = "\n".join(lines) + "\n"

    dir_name = os.path.dirname(env_path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".env.", dir=dir_name, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, env_path)
        try:
            os.chmod(env_path, 0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return env_path


def save_llm_config(body: dict) -> Dict[str, Any]:
    """
    Web 配置入口：默认写 Nextdoor 凭证；Ping 失败不落盘；成功清空 TTL。
    body(nextdoor): {provider?:nextdoor, jwt_token|api_key, base_url?, source_client?, mode?}
    body(direct 应急): {provider:deepseek|doubao|openai_compatible, api_key, model?, base_url?} 且需 GEO_LLM_DIRECT
    """
    provider = (body.get("provider") or "nextdoor").strip().lower()
    if provider in ("nextdoor", "xiaomaolv", "小毛驴"):
        jwt = (body.get("jwt_token") or body.get("api_key") or "").strip()
        if not jwt:
            return {"success": False, "message": "NEXTDOOR_JWT_TOKEN 不能为空"}
        base_url = (body.get("base_url") or "").strip() or DEFAULT_NEXTDOOR_BASE_URL
        brand = (body.get("source_client") or body.get("brand") or "").strip() or DEFAULT_NEXTDOOR_SOURCE_CLIENT
        mode = (body.get("mode") or "").strip().lower() or DEFAULT_NEXTDOOR_CHAT_MODE
        if mode not in ("flash", "think", "auto"):
            mode = DEFAULT_NEXTDOOR_CHAT_MODE
        updates = {
            "NEXTDOOR_JWT_TOKEN": jwt,
            "NEXTDOOR_BASE_URL": base_url.rstrip("/"),
            "NEXTDOOR_SOURCE_CLIENT": brand,
            "NEXTDOOR_CHAT_MODE": mode,
            "GEO_LLM_DIRECT": "0",
        }
        runtime = {
            "provider": "nextdoor",
            "model": mode,
            "mode": mode,
            "brand": brand,
            "api_key": jwt,
            "base_url": base_url.rstrip("/"),
        }
        status, latency = ping_llm(runtime, timeout=10)
        if status != "ready":
            return {
                "success": False,
                "message": f"Nextdoor 连通/鉴权探测失败（{status}），未写入 .env",
                "status": status,
                "latency_ms": latency,
            }
        atomic_write_env(updates)
        clear_status_cache()
        return {
            "success": True,
            "message": "小毛驴 / Nextdoor 配置已保存",
            "provider": "nextdoor",
            "model": mode,
            "mode": mode,
            "brand": brand,
            "status": "ready",
            "latency_ms": latency,
            "api_key_masked": mask_api_key(jwt),
        }

    # 应急直连：仅当显式打开 DIRECT 或 body.force_direct
    force_direct = _direct_enabled() or str(body.get("force_direct") or "").lower() in ("1", "true", "yes")
    if not force_direct:
        return {
            "success": False,
            "message": "默认仅支持 Nextdoor。应急厂商直连请设 GEO_LLM_DIRECT=1 或传 force_direct=true",
        }

    api_key = (body.get("api_key") or "").strip()
    model = (body.get("model") or "").strip()
    base_url = (body.get("base_url") or "").strip()
    if not api_key:
        return {"success": False, "message": "API Key 不能为空"}

    updates: Dict[str, str] = {"GEO_LLM_DIRECT": "1"}
    if provider == "deepseek":
        updates["DEEPSEEK_API_KEY"] = api_key
        if model:
            updates["DEEPSEEK_MODEL"] = model
        if base_url:
            updates["DEEPSEEK_BASE_URL"] = base_url
        runtime = {
            "provider": "deepseek",
            "model": model or PROVIDERS["deepseek"]["default_model"],
            "api_key": api_key,
            "base_url": (base_url or PROVIDERS["deepseek"]["base_url"]).rstrip("/"),
        }
    elif provider in ("doubao", "ark"):
        updates["ARK_API_KEY"] = api_key
        updates["DOUBAO_API_KEY"] = api_key
        if model:
            updates["DOUBAO_MODEL"] = model
        if base_url:
            updates["ARK_BASE_URL"] = base_url
        runtime = {
            "provider": "doubao",
            "model": model or PROVIDERS["doubao"]["default_model"],
            "api_key": api_key,
            "base_url": (base_url or PROVIDERS["doubao"]["base_url"]).rstrip("/"),
        }
    elif provider in ("openai", "openai_compatible", "proxy"):
        updates["GEO_LLM_API_KEY"] = api_key
        if model:
            updates["GEO_LLM_MODEL"] = model
        if base_url:
            updates["GEO_LLM_BASE_URL"] = base_url
        runtime = {
            "provider": "openai_compatible",
            "model": model or PROVIDERS["openai_compatible"]["default_model"],
            "api_key": api_key,
            "base_url": (base_url or PROVIDERS["openai_compatible"]["base_url"]).rstrip("/"),
        }
    else:
        return {"success": False, "message": f"不支持的 provider: {provider}"}

    status, latency = ping_llm(runtime, timeout=10)
    if status != "ready":
        return {
            "success": False,
            "message": f"连通/鉴权探测失败（{status}），未写入 .env",
            "status": status,
            "latency_ms": latency,
        }

    atomic_write_env(updates)
    clear_status_cache()
    return {
        "success": True,
        "message": "应急直连配置已保存（GEO_LLM_DIRECT=1）",
        "provider": runtime["provider"],
        "model": runtime["model"],
        "status": "ready",
        "latency_ms": latency,
        "api_key_masked": mask_api_key(api_key),
    }


def call_model_raw(model: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
    """调用大模型并返回完整 raw JSON 字典与 content（默认经 Nextdoor）。"""
    _ensure_loaded()
    runtime = resolve_llm_runtime()
    if runtime and runtime.get("provider") == "nextdoor":
        ok, text, prov = call_via_runtime(runtime, prompt, timeout=timeout)
        if not ok:
            raise LlmUnavailable(text)
        return {"content": text, "model": runtime.get("mode") or "flash", "raw_response": {"provider": prov}}

    # DIRECT 或指定厂商探测
    conf = PROVIDERS.get(model)
    if conf is None and runtime and runtime.get("provider") in PROVIDERS:
        model = runtime["provider"]
        conf = PROVIDERS.get(model)
    if conf is None:
        raise LlmUnavailable(f"不支持的模型: {model}（可选: {', '.join(PROVIDERS)}）；或配置 NEXTDOOR_JWT_TOKEN")

    if not _direct_enabled() and not runtime:
        raise LlmUnavailable("未配置 NEXTDOOR_JWT_TOKEN；厂商直连需 GEO_LLM_DIRECT=1")

    api_key = resolve_api_key(model) if conf else None
    if not api_key and runtime:
        api_key = runtime.get("api_key")
        use_model = runtime.get("model")
        base_url = runtime.get("base_url")
    else:
        if not api_key:
            raise LlmUnavailable(f"未设置环境变量 {conf.get('api_key_envs', [])}，无法调用 {model}")
        use_model = resolve_model_name(model)
        base_url = resolve_base_url(model)

    payload = {
        "model": use_model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个客观严谨的中文商业分析与专业咨询推荐专家，请回答用户提问。如有参考资料，请在回答中客观标注引用与信源。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "search_enabled": True,
    }

    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise LlmUnavailable(f"调用 {model} 失败: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LlmUnavailable(f"{model} 返回结构异常: {body}") from exc

    return {
        "content": content,
        "model": use_model,
        "raw_response": body,
    }


def chat(model: str, prompt: str, timeout: int = 120) -> str:
    res = call_model_raw(model, prompt, timeout=timeout)
    return res["content"]


# 模块导入时加载 .env
try:
    load_dotenv(override=True)
except Exception:
    pass
