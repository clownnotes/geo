# -*- coding: utf-8 -*-
"""大模型 API 客户端与统一运行时解析（OpenAI 兼容协议，零第三方依赖）。

唯一解析入口：resolve_llm_runtime()
Web 写入键名钉死：DEEPSEEK_API_KEY / ARK_API_KEY（见 design §2.1）
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

# Web 配置允许写入的环境变量白名单
CONFIG_WRITE_WHITELIST = frozenset({
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


def resolve_llm_runtime() -> Optional[Dict[str, Any]]:
    """统一运行时解析：DeepSeek → 豆包 → OpenAI 兼容。含 source，含明文 api_key（仅内部）。"""
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
            "api_key": api_key,
            "base_url": (base_val or conf["base_url"]).rstrip("/"),
            "source": _source_for_key(key_env),
            "key_env": key_env,
        }
    return None


def mask_api_key(api_key: Optional[str]) -> str:
    if not api_key:
        return ""
    if len(api_key) < 8:
        return "*" * len(api_key)
    return f"{api_key[:2]}****{api_key[-4:]}"


def clear_status_cache() -> None:
    with _STATUS_LOCK:
        _STATUS_CACHE["payload"] = None
        _STATUS_CACHE["ts"] = 0.0


def ping_llm(runtime: Dict[str, Any], timeout: int = 10) -> Tuple[str, Optional[int]]:
    """
    统一走 chat/completions 极小探测。
    返回 (status, latency_ms)：ready / auth_failed / unreachable
    """
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
    started = time.time()
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
        latency = int((time.time() - started) * 1000)
        return "ready", latency
    except urllib.error.HTTPError as e:
        latency = int((time.time() - started) * 1000)
        if e.code in (401, 403):
            return "auth_failed", latency
        # 部分供应商对极小请求返回 400 但仍说明鉴权通
        if e.code in (400, 404, 422):
            return "ready", latency
        return "unreachable", latency
    except Exception:
        latency = int((time.time() - started) * 1000)
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
            "base_url": None,
            "source": "none",
            "api_key_masked": "",
            "latency_ms": None,
            "status": "offline",
            "cached": False,
        }
    else:
        status, latency = ping_llm(runtime, timeout=10)
        payload = {
            "configured": True,
            "provider": runtime["provider"],
            "model": runtime["model"],
            "base_url": runtime["base_url"],
            "source": runtime["source"],
            "api_key_masked": mask_api_key(runtime["api_key"]),
            "latency_ms": latency,
            "status": status if status != "ready" else "ready",
            "cached": False,
        }
        if status == "auth_failed":
            payload["status"] = "auth_failed"
        elif status == "unreachable":
            payload["status"] = "unreachable"

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
    Web 配置入口：按 §2.1 唯一键写入；Ping 失败不落盘；成功清空 TTL。
    body: {provider, api_key, model?, base_url?}
    """
    provider = (body.get("provider") or "deepseek").strip().lower()
    api_key = (body.get("api_key") or "").strip()
    model = (body.get("model") or "").strip()
    base_url = (body.get("base_url") or "").strip()

    if not api_key:
        return {"success": False, "message": "API Key 不能为空"}

    updates: Dict[str, str] = {}
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
        updates["DOUBAO_API_KEY"] = api_key  # 同步同值
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
        "message": "大模型配置已保存",
        "provider": runtime["provider"],
        "model": runtime["model"],
        "status": "ready",
        "latency_ms": latency,
        "api_key_masked": mask_api_key(api_key),
    }


def call_model_raw(model: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
    """调用大模型并返回完整 raw JSON 字典与 content。"""
    _ensure_loaded()
    conf = PROVIDERS.get(model)
    if conf is None:
        raise LlmUnavailable(f"不支持的模型: {model}（可选: {', '.join(PROVIDERS)}）")

    api_key = resolve_api_key(model)
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
