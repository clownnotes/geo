#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 通用工具库 (tools/geo/utils.py)
包含项目目录管理、简易零依赖 YAML 解析器、输出文件存储及 ANSI 格式化打印。
"""

import os
import re

# 基础目录定位
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TOOLS_DIR))
PROJECTS_DIR = os.path.join(PROJECT_ROOT, "projects")

# ANSI 颜色定义
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BLUE = "\033[94m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"

def print_green(msg): print(f"{COLOR_GREEN}{msg}{COLOR_RESET}")
def print_yellow(msg): print(f"{COLOR_YELLOW}{msg}{COLOR_RESET}")
def print_red(msg): print(f"{COLOR_RED}{msg}{COLOR_RESET}")
def print_blue(msg): print(f"{COLOR_BLUE}{msg}{COLOR_RESET}")
def print_bold(msg): print(f"{COLOR_BOLD}{msg}{COLOR_RESET}")

def print_banner(title: str):
    print("\n" + "=" * 60)
    print_bold(f" 🚀 {title}")
    print("=" * 60 + "\n")

def print_info(msg: str):
    print(f"ℹ️  {msg}")

def print_success(msg: str):
    print_green(f"✅ {msg}")

def print_warning(msg: str):
    print_yellow(f"⚠️  {msg}")

def print_error(msg: str):
    print_red(f"❌ {msg}")

def parse_simple_yaml(content: str) -> dict:
    """
    轻量级零依赖 YAML 解析器
    支持键值对、嵌套单级字典以及字符串列表
    """
    data = {}
    current_list_key = None
    
    for raw_line in content.splitlines():
        line = raw_line.strip()
        # 忽略空行和注释
        if not line or line.startswith("#"):
            continue
            
        # 列表项处理
        if line.startswith("- ") and current_list_key:
            val = line[2:].strip().strip('"\'')
            data[current_list_key].append(val)
            continue
            
        # 键值对处理
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            
            if not val:  # 开启新列表
                current_list_key = key
                data[key] = []
            else:
                current_list_key = None
                val = val.strip('"\'')
                data[key] = val
                
    return data

def load_project_config(project_id: str) -> dict:
    """加载指定客户的项目配置文件 project.yaml"""
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    config_file = os.path.join(project_dir, "project.yaml")
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"未找到客户项目配置文件: {config_file}")
        
    with open(config_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    cfg = parse_simple_yaml(content)
    # 兼容 client_name 与 company_name
    if "company_name" in cfg and "client_name" not in cfg:
        cfg["client_name"] = cfg["company_name"]
    if "client_name" in cfg and "company_name" not in cfg:
        cfg["company_name"] = cfg["client_name"]

    cfg["_project_dir"] = project_dir
    cfg["_outputs_dir"] = os.path.join(project_dir, "outputs")
    cfg["_raw_materials_dir"] = os.path.join(project_dir, "raw_materials")
    
    # 确保输出和原始资料目录存在
    os.makedirs(cfg["_outputs_dir"], exist_ok=True)
    os.makedirs(cfg["_raw_materials_dir"], exist_ok=True)
    
    return cfg

def save_project_output(target, filename: str, content: str) -> str:
    """保存交付物到客户 outputs 目录（支持传入 cfg 字典或 project_id 字符串）"""
    if isinstance(target, str):
        target = load_project_config(target)
    out_path = os.path.join(target["_outputs_dir"], filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path

def get_configured_llm() -> dict:
    """获取当前系统配置的可用 LLM 供应商信息"""
    # 1. 优先检查 DeepSeek
    if os.environ.get("DEEPSEEK_API_KEY"):
        return {
            "provider": "deepseek",
            "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            "api_key": os.environ.get("DEEPSEEK_API_KEY"),
            "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        }
    # 2. 检查 豆包 / 火山方舟
    if os.environ.get("ARK_API_KEY") or os.environ.get("DOUBAO_API_KEY"):
        return {
            "provider": "doubao",
            "model": os.environ.get("DOUBAO_MODEL", "doubao-pro-32k"),
            "api_key": os.environ.get("ARK_API_KEY") or os.environ.get("DOUBAO_API_KEY"),
            "base_url": os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        }
    # 3. 检查 通用 OpenAI 或代理
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("GEO_LLM_API_KEY"):
        return {
            "provider": "openai_compatible",
            "model": os.environ.get("GEO_LLM_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": os.environ.get("GEO_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            "base_url": (os.environ.get("GEO_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        }
    return None

def call_llm_api(prompt: str, system_prompt: str = None, model: str = None, timeout: int = 30) -> tuple:
    """
    零依赖调用大模型 OpenAI 兼容接口 (/chat/completions)
    返回 (success: bool, result_text: str, provider_name: str)
    """
    import json
    import urllib.request
    import urllib.error

    llm_info = get_configured_llm()
    if not llm_info:
        return False, "未配置大模型 API Key（DEEPSEEK_API_KEY / ARK_API_KEY / OPENAI_API_KEY）", "none"

    # 只有当 model 看起来是真实的模型名（含 "-"）时才覆盖，避免传入 "deepseek"/"doubao" 等简写导致 API 报错
    _PROVIDER_SHORTHANDS = {"deepseek", "doubao", "openai", "gpt", "ark", "qwen", "ernie"}
    target_model = llm_info["model"]
    if model and model.lower() not in _PROVIDER_SHORTHANDS:
        target_model = model
    base_url = llm_info["base_url"]
    endpoint = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": 0.3
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {llm_info['api_key']}"
    }

    try:
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return True, content.strip(), llm_info["provider"]
    except urllib.error.HTTPError as e:
        err_msg = f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}"
        return False, err_msg, llm_info["provider"]
    except Exception as e:
        return False, str(e), llm_info["provider"]

