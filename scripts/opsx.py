#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 通用 OpenSpec CLI 辅助脚本 (opsx)，支持所有 AI 助手及人工调用。

import os
import sys
import shutil
import re
from datetime import datetime

# 基础目录配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGES_DIR = os.path.join(PROJECT_ROOT, "openspec", "changes")
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "openspec", "template", "collaborative-change")

# ANSI 颜色输出
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

def get_current_changes():
    """获取当前正在进行的变更目录（排除 archive 和隐藏文件）"""
    if not os.path.exists(CHANGES_DIR):
        os.makedirs(CHANGES_DIR, exist_ok=True)
        return []
    
    dirs = []
    for item in os.listdir(CHANGES_DIR):
        full_path = os.path.join(CHANGES_DIR, item)
        if os.path.isdir(full_path) and item != "archive" and not item.startswith("."):
            dirs.append(item)
    return dirs

def init_templates(change_path, change_name):
    """初始化模板文件"""
    # 1. 写 .openspec.yaml
    with open(os.path.join(change_path, ".openspec.yaml"), "w", encoding="utf-8") as f:
        f.write("schema: spec-driven\n")
        
    # 2. 写 proposal.md
    proposal_content = f"""# Proposal: {change_name}

## Why (为什么做)
- 描述痛点或背景需求。

## What Changes (改动了什么)
- 描述要做的核心修改内容。

## Capabilities (新增或修改的对外能力)
- 描述此项修改所带来的具体功能或接口。

## Impact (受影响的部分)
- 描述可能受影响的文件、依赖以及操作流程的改变。
"""
    with open(os.path.join(change_path, "proposal.md"), "w", encoding="utf-8") as f:
        f.write(proposal_content)

    # 3. 写 design.md
    design_content = f"""# Design: {change_name}

## Architecture (架构设计与对象关系)
- 识别涉及的实体/名词（根据面向对象三问）。
- 明确各对象之间的约束和外键关系。

## Interface (接口/API/前端组件设计)
- 前后端路由、参数和返回值定义。

## Database Schema / Data Structure (数据模型变更)
- 表结构修改或新增数据结构说明。
"""
    with open(os.path.join(change_path, "design.md"), "w", encoding="utf-8") as f:
        f.write(design_content)

    # 4. 写 tasks.md
    tasks_content = f"""## 1. 准备工作

- [ ] 1.1 确认要修改的文件，并在动手前核对全局规则。

## 2. 代码开发

- [ ] 2.1 编写核心业务与功能代码。
- [ ] 2.2 编写页面与交互逻辑。

## 3. 验证与测试

- [ ] 3.1 运行测试并进行手动验证。
"""
    with open(os.path.join(change_path, "tasks.md"), "w", encoding="utf-8") as f:
        f.write(tasks_content)

    # 5. 写 review-log.md
    review_log_src = os.path.join(TEMPLATE_DIR, "review-log.md")
    review_log_dest = os.path.join(change_path, "review-log.md")
    if os.path.exists(review_log_src):
        shutil.copy(review_log_src, review_log_dest)
    else:
        default_review_log = """# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

<!-- 下面是实际记录，按时间顺序往下追加 -->
"""
        with open(review_log_dest, "w", encoding="utf-8") as f:
            f.write(default_review_log)

def cmd_propose(args):
    if not args:
        print_red("错误: 请提供需求名称。例如: ./opsx propose 搭建-GEO-SOP-网站")
        sys.exit(1)
        
    change_name = args[0]
    
    # 检查当前是否有进行中的变更
    current = get_current_changes()
    if current:
        print_yellow(f"⚠️  警告: 当前已有正在进行的变更目录: {current[0]}")
        print_yellow("请先运行 `./opsx archive` 归档当前变更，或手动处理后再创建新需求。")
        sys.exit(1)
        
    # 生成中文命名的变更文件夹
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{date_str}-{change_name}"
    change_path = os.path.join(CHANGES_DIR, folder_name)
    
    if os.path.exists(change_path):
        print_red(f"错误: 目录已存在: {folder_name}")
        sys.exit(1)
        
    os.makedirs(change_path, exist_ok=True)
    init_templates(change_path, change_name)
    
    print_green(f"✅ 成功创建 OpenSpec 变更目录: openspec/changes/{folder_name}")
    print_bold("包含的文件有:")
    print("  📄 .openspec.yaml (配置标记)")
    print("  📄 proposal.md    (需求与背景定义)")
    print("  📄 design.md      (技术架构设计)")
    print("  📄 tasks.md       (细分开发任务清单)")
    print("  📄 review-log.md  (双端协作审核日志)")
    print("")
    print_blue("👉 请其他 AI 助手（如 Claude / Windsurf）先阅读此目录下的 proposal/design 并在 review-log.md 中对齐共识。")

def cmd_status(args):
    current = get_current_changes()
    if not current:
        print_yellow("📭 当前没有正在进行的 OpenSpec 变更任务。")
        return
        
    folder_name = current[0]
    change_path = os.path.join(CHANGES_DIR, folder_name)
    
    print_bold(f"\n===== 当前活动任务: {folder_name} =====")
    
    # 检查核心文件状态
    files = ["proposal.md", "design.md", "tasks.md", "review-log.md"]
    print("\n[文档状态]")
    for filename in files:
        f_path = os.path.join(change_path, filename)
        exists = "✅ 已创建" if os.path.exists(f_path) else "❌ 缺失"
        print(f"  - {filename:<15}: {exists}")
        
    # 检查 tasks.md 的进度
    tasks_file = os.path.join(change_path, "tasks.md")
    if os.path.exists(tasks_file):
        with open(tasks_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 寻找匹配的 - [ ] 或 - [x]
        all_tasks = re.findall(r"-\s*\[\s*([ xX/])\s*\]\s*(.*)", content)
        if all_tasks:
            total = len(all_tasks)
            completed = sum(1 for t in all_tasks if t[0].lower() == "x")
            in_progress = sum(1 for t in all_tasks if t[0] == "/")
            
            print("\n[开发进度]")
            print(f"  总任务数: {total} 个")
            print(f"  已完成  : {completed} 个")
            print(f"  进行中  : {in_progress} 个")
            
            progress_pct = (completed / total) * 100 if total > 0 else 0
            bar_len = 20
            filled_len = int(bar_len * completed // total) if total > 0 else 0
            bar = "█" * filled_len + "-" * (bar_len - filled_len)
            print(f"  进度条  : |{bar}| {progress_pct:.1f}%")
            
            print("\n[任务详细清单]")
            for t in all_tasks:
                status_icon = "✅ Done" if t[0].lower() == "x" else ("⏳ Running" if t[0] == "/" else "⬜️ Todo")
                print(f"  [{status_icon}] {t[1]}")
        else:
            print_yellow("\n⚠️  tasks.md 中未发现有效的任务标记 - [ ] 或 - [x]")
    else:
        print_red("\n❌ tasks.md 文件缺失，无法评估进度。")
    print("")

def cmd_archive(args):
    current = get_current_changes()
    if not current:
        print_yellow("📭 没有找到需要归档的变更任务。")
        return
        
    folder_name = current[0]
    src_path = os.path.join(CHANGES_DIR, folder_name)
    archive_dir = os.path.join(CHANGES_DIR, "archive")
    dest_path = os.path.join(archive_dir, folder_name)
    
    os.makedirs(archive_dir, exist_ok=True)
    
    if os.path.exists(dest_path):
        print_red(f"错误: 归档目标目录已存在: openspec/changes/archive/{folder_name}")
        print_red("请手动检查并清理冲突的归档目录。")
        sys.exit(1)
        
    shutil.move(src_path, dest_path)
    print_green(f"✅ 成功将当前变更归档至: openspec/changes/archive/{folder_name}")
    print_bold("💡 规范归档建议: 请执行 git add . && git commit -m '...' 提交变更！")

def show_help():
    print_bold("通用 OpenSpec CLI 工具 (opsx)")
    print("支持所有 AI 助手 (Antigravity, Windsurf, Claude Code 等) 使用统一的 OpenSpec 规范流程。")
    print("")
    print("可用命令:")
    print("  ./opsx propose <需求名>  - 初始化新需求变更目录和模板")
    print("  ./opsx status            - 检查当前正在进行的需求和任务进度")
    print("  ./opsx archive           - 归档当前已完成的需求")
    print("")

def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
        
    cmd = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if cmd == "propose":
        cmd_propose(args)
    elif cmd == "status":
        cmd_status(args)
    elif cmd == "archive":
        cmd_archive(args)
    elif cmd in ["--help", "-h", "help"]:
        show_help()
    else:
        print_red(f"未知命令: {cmd}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
