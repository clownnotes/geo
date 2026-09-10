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

def _unescape_yaml_quoted(raw: str) -> str:
    """解析双引号标量中的 \\n / \\\" / \\\\（与 partners._escape_yaml_str 对称）。"""
    s = (raw or "").strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        body = s[1:-1]
        out: list[str] = []
        i = 0
        while i < len(body):
            if body[i] == "\\" and i + 1 < len(body):
                nxt = body[i + 1]
                if nxt == "n":
                    out.append("\n")
                elif nxt == '"':
                    out.append('"')
                elif nxt == "\\":
                    out.append("\\")
                else:
                    out.append(nxt)
                i += 2
                continue
            out.append(body[i])
            i += 1
        return "".join(out)
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


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
            val = _unescape_yaml_quoted(line[2:].strip())
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
                # bool / 未加引号数字保持简单字符串语义
                low = val.lower()
                if low in ("true", "false") and not (val.startswith('"') or val.startswith("'")):
                    data[key] = low == "true"
                else:
                    data[key] = _unescape_yaml_quoted(val)
                
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


def _escape_yaml_double(value) -> str:
    s = str(value if value is not None else "")
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
    return f'"{s}"'


def _normalize_profile_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [ln.strip() for ln in value.replace("\r", "").split("\n") if ln.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _upsert_yaml_scalar(content: str, key: str, value, *, as_bool: bool = False) -> str:
    if as_bool:
        rendered = "true" if bool(value) else "false"
    else:
        rendered = _escape_yaml_double(value)
    pattern = rf"(?m)^{re.escape(key)}\s*:.*$"
    line = f"{key}: {rendered}"
    if re.search(pattern, content):
        return re.sub(pattern, line, content, count=1)
    return content.rstrip() + f"\n{line}\n"


def _upsert_yaml_alias_scalars(content: str, primary_key: str, aliases: list[str], value) -> str:
    """写入主字段；若文件中已有别名键则同步更新，避免读侧仍吃到旧值。"""
    content = _upsert_yaml_scalar(content, primary_key, value)
    for alias in aliases:
        if re.search(rf"(?m)^{re.escape(alias)}\s*:", content):
            content = _upsert_yaml_scalar(content, alias, value)
    return content


def _replace_yaml_string_list(content: str, key: str, items: list[str]) -> str:
    block_lines = [f"{key}:"]
    for it in items:
        block_lines.append(f"  - {_escape_yaml_double(it)}")
    block = "\n".join(block_lines) + "\n"
    # 替换顶层 list 块（遇下一顶层键或文件尾结束）；保留块前注释尽量不动
    pattern = rf"(?ms)^{re.escape(key)}\s*:\n(?:(?:[ \t]*#[^\n]*\n)|(?:[ \t]*- [^\n]*\n))*"
    if re.search(pattern, content):
        return re.sub(pattern, block, content, count=1)
    return content.rstrip() + "\n\n" + block


def update_project_profile(project_id: str, patch: dict) -> dict:
    """
    更新 project.yaml 建档主档字段（保留未改动段落与注释结构的尽力而为）。
    不可改 client_id。返回加载后的安全配置（无 _ 私有路径）。
    """
    if not project_id or project_id.startswith("_"):
        raise ValueError("无效的项目 ID")
    cfg = load_project_config(project_id)
    yaml_path = os.path.join(cfg["_project_dir"], "project.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    scalar_keys = (
        "client_name",
        "brand_name",
        "company_name",
        "industry",
        "official_url",
        "slogan",
        "company_profile",
        "wechat",
    )
    for key in scalar_keys:
        if key in patch:
            content = _upsert_yaml_scalar(content, key, patch.get(key) or "")

    if "contact_person" in patch:
        content = _upsert_yaml_alias_scalars(
            content, "contact_person", ["founder", "person"], patch.get("contact_person") or ""
        )
    if "telephone" in patch:
        content = _upsert_yaml_alias_scalars(
            content, "telephone", ["phone"], patch.get("telephone") or ""
        )
    if "area_served" in patch:
        content = _upsert_yaml_alias_scalars(
            content, "area_served", ["address", "area"], patch.get("area_served") or ""
        )

    if "partner_id" in patch:
        content = _upsert_yaml_scalar(content, "partner_id", str(patch.get("partner_id") or "").strip())

    if "custom_site" in patch:
        content = _upsert_yaml_scalar(content, "custom_site", bool(patch.get("custom_site")), as_bool=True)

    if "keywords" in patch:
        content = _replace_yaml_string_list(content, "keywords", _normalize_profile_list(patch.get("keywords")))
    if "competitors" in patch:
        content = _replace_yaml_string_list(content, "competitors", _normalize_profile_list(patch.get("competitors")))

    # 优势：优先写已有键；都没有则写 core_values
    if "core_values" in patch or "differences" in patch:
        values = _normalize_profile_list(patch.get("core_values") if "core_values" in patch else patch.get("differences"))
        has_cv = bool(re.search(r"(?m)^core_values\s*:", content))
        has_diff = bool(re.search(r"(?m)^differences\s*:", content))
        if has_cv or not has_diff:
            content = _replace_yaml_string_list(content, "core_values", values)
        if has_diff:
            content = _replace_yaml_string_list(content, "differences", values)

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)

    fresh = load_project_config(project_id)
    return {k: v for k, v in fresh.items() if not k.startswith("_")}


def append_project_keywords(project_id: str, new_keywords: list) -> tuple:
    """
    向 project.yaml 的 keywords 列表安全追加新词（保留原有 YAML 结构与注释，仅增量写入）。
    返回: (added_list, total_count)
    """
    cfg = load_project_config(project_id)
    yaml_path = os.path.join(cfg["_project_dir"], "project.yaml")
    existing = cfg.get("keywords", [])
    if isinstance(existing, str):
        existing = [k.strip() for k in existing.split("\n") if k.strip()]

    existing_set = set(existing)
    added = []
    for item in new_keywords:
        text = item.get("prompt") if isinstance(item, dict) else str(item)
        text = text.strip()
        if text and text not in existing_set:
            existing_set.add(text)
            added.append(text)

    if not added:
        return [], len(existing)

    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    append_lines = "\n".join(
        '  - "' + k.replace("\\", "\\\\").replace('"', '\\"') + '"' for k in added
    )

    if "keywords:" in content:
        content = re.sub(
            r"(keywords:\n(?:[ \t]*- [^\n]+\n)*)",
            lambda m: m.group(1) + append_lines + "\n",
            content,
            count=1,
        )
    else:
        content = content.rstrip() + f"\n\nkeywords:\n{append_lines}\n"

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)

    return added, len(existing) + len(added)


def save_project_output(target, filename: str, content: str) -> str:
    """保存交付物到客户 outputs 目录（支持传入 cfg 字典或 project_id 字符串）"""
    if isinstance(target, str):
        target = load_project_config(target)
    out_path = os.path.join(target["_outputs_dir"], filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path

def get_configured_llm() -> dict:
    """薄封装：统一走 llm.resolve_llm_runtime()（禁止第二套 env 判断）。"""
    from .llm import resolve_llm_runtime
    return resolve_llm_runtime()

def call_llm_api(prompt: str, system_prompt: str = None, model: str = None, timeout: int = 30) -> tuple:
    """
    统一大模型调用：默认 Nextdoor 开放 API；GEO_LLM_DIRECT=1 时厂商直连。
    返回 (success: bool, result_text: str, provider_name: str)
    """
    from .llm import call_via_runtime, resolve_llm_runtime

    llm_info = resolve_llm_runtime()
    if not llm_info:
        return False, "未配置 Nextdoor JWT（NEXTDOOR_JWT_TOKEN）；应急直连需 GEO_LLM_DIRECT=1", "none"
    return call_via_runtime(llm_info, prompt, system_prompt=system_prompt, timeout=timeout, model_override=model)

