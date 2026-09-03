# -*- coding: utf-8 -*-
"""大模型 API 客户端（OpenAI 兼容协议，零第三方依赖）。

支持 DeepSeek、豆包（火山方舟 Ark）、Kimi（Moonshot）。
严格按照 Spec 规范落实 API Key 链式降级读取契约。未配置 API Key 时返回 None 或抛 LlmUnavailable，
调用方必须提供离线降级路径（如 SandboxSimulator），保证流水线在演示/CI 环境可跑通。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Dict, Any, Optional, Tuple

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "api_key_envs": ["GEO_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"],
        "model_envs": ["DEEPSEEK_MODEL"],
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-seed-1-6-250615",
        "api_key_envs": ["GEO_DOUBAO_API_KEY", "DOUBAO_API_KEY", "ARK_API_KEY"],
        "model_envs": ["GEO_DOUBAO_ENDPOINT_ID", "DOUBAO_ENDPOINT_ID", "DOUBAO_ARK_MODEL"],
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "api_key_envs": ["GEO_KIMI_API_KEY", "MOONSHOT_API_KEY"],
        "model_envs": ["KIMI_MODEL", "MOONSHOT_MODEL"],
    },
}


class LlmUnavailable(RuntimeError):
    pass


def resolve_api_key(model: str) -> Optional[str]:
    """按链式降级顺序读取模型 API Key（优先 GEO_*，其次通用名，再次供应商专有别名）"""
    conf = PROVIDERS.get(model)
    if not conf:
        return None
    for env_name in conf.get("api_key_envs", []):
        val = os.getenv(env_name)
        if val and val.strip():
            return val.strip()
    return None


def resolve_model_name(model: str) -> str:
    """读取模型具体标识或推理接入点"""
    conf = PROVIDERS.get(model)
    if not conf:
        return model
    for env_name in conf.get("model_envs", []):
        val = os.getenv(env_name)
        if val and val.strip():
            return val.strip()
    return conf.get("default_model", model)


def available(model: str) -> bool:
    """检查指定模型是否已配置有效 Key"""
    return resolve_api_key(model) is not None


def call_model_raw(model: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
    """调用大模型并返回完整 raw JSON 字典与 content，供 Citation 解析器提取元数据。"""
    conf = PROVIDERS.get(model)
    if conf is None:
        raise LlmUnavailable(f"不支持的模型: {model}（可选: {', '.join(PROVIDERS)}）")

    api_key = resolve_api_key(model)
    if not api_key:
        raise LlmUnavailable(f"未设置环境变量 {conf.get('api_key_envs', [])}，无法调用 {model}")

    use_model = resolve_model_name(model)
    payload = {
        "model": use_model,
        "messages": [
            {"role": "system", "content": "你是一个客观严谨的中文商业分析与专业咨询推荐专家，请回答用户提问。如有参考资料，请在回答中客观标注引用与信源。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "search_enabled": True,  # 豆包/DeepSeek 联网插件开关（不支持时由供应商服务端忽略）
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
    except Exception as exc:
        raise LlmUnavailable(f"调用 {model} 失败: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LlmUnavailable(f"{model} 返回结构异常: {body}") from exc

    return {
        "content": content,
        "model": use_model,
        "raw_response": body
    }


def chat(model: str, prompt: str, timeout: int = 120) -> str:
    """单次对话调用；模型未配置 Key 时抛 LlmUnavailable。100% 向后兼容。"""
    res = call_model_raw(model, prompt, timeout=timeout)
    return res["content"]
