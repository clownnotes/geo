"""大模型 API 客户端（OpenAI 兼容协议，零第三方依赖）。

支持 DeepSeek 与豆包（火山方舟 Ark Seed）。未配置 API Key 时返回 None，
调用方必须提供离线降级路径，保证流水线在演示/CI 环境可跑通。
"""
from __future__ import annotations

import json
import os
import urllib.request

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "doubao": {
        # 火山方舟 OpenAI 兼容接口
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_env": "DOUBAO_ARK_MODEL",  # 推理接入点，如 doubao-seed-1-6-250615
        "model": "doubao-seed-1-6-250615",
        "api_key_env": "DOUBAO_API_KEY",
    },
}


class LlmUnavailable(RuntimeError):
    pass


def available(model: str) -> bool:
    conf = PROVIDERS.get(model)
    return bool(conf and os.getenv(conf["api_key_env"]))


def chat(model: str, prompt: str, timeout: int = 120) -> str:
    """单次对话调用；模型未配置 Key 时抛 LlmUnavailable。"""
    conf = PROVIDERS.get(model)
    if conf is None:
        raise LlmUnavailable(f"不支持的模型: {model}（可选: {', '.join(PROVIDERS)}）")
    api_key = os.getenv(conf["api_key_env"])
    if not api_key:
        raise LlmUnavailable(f"未设置环境变量 {conf['api_key_env']}，无法调用 {model}")
    use_model = os.getenv(conf.get("model_env", ""), "") or conf["model"]
    payload = {
        "model": use_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "search_enabled": True,  # 豆包/DeepSeek 联网检索开关（不支持时被忽略）
    }
    req = urllib.request.Request(
        conf["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # 网络/接口异常统一包装，便于调用方降级
        raise LlmUnavailable(f"调用 {model} 失败: {exc}") from exc
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LlmUnavailable(f"{model} 返回结构异常: {body}") from exc
