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
