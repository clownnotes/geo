#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 自动审查桥接脚本 (WorkBuddy Reviewer Bridge)
支持：
1. 全局运行：自动定位当前工作区根目录
2. 本地调用 WorkBuddy CLI (codebuddy -p)
3. 远程 SSH 调用 WorkBuddy CLI
4. 审查 OpenSpec 设计文档或 Git Diff，并将审查结果自动追加到 review-log.md
5. 严格锁定免费版模型（hy3），严禁调用任何收费模型；额度耗尽时明确提示换号。
"""

import os
import sys
import subprocess
import re
from datetime import datetime

CODEBUDDY_BIN = "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy"

def find_project_root():
    """从当前工作目录向上查找包含 .git 或 openspec 的根目录"""
    current = os.getcwd()
    while True:
        if os.path.exists(os.path.join(current, "openspec")) or os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.getcwd()

PROJECT_ROOT = find_project_root()
CHANGES_DIR = os.path.join(PROJECT_ROOT, "openspec", "changes")

def get_active_change(target_change=None):
    if not os.path.exists(CHANGES_DIR):
        return None
    if target_change:
        # 如果传入的是完整路径或变更名
        if os.path.exists(target_change) and os.path.isdir(target_change):
            return target_change, os.path.basename(os.path.normpath(target_change))
        candidate = os.path.join(CHANGES_DIR, target_change)
        if os.path.exists(candidate) and os.path.isdir(candidate):
            return candidate, target_change
        # 模糊前缀/包含匹配
        for item in os.listdir(CHANGES_DIR):
            if target_change in item:
                return os.path.join(CHANGES_DIR, item), item

    # 1. 优先通过 git status 探测当前正在修改的 OpenSpec 变更目录
    try:
        git_res = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if git_res.returncode == 0:
            lines = git_res.stdout.splitlines()
            # 优先匹配有明确已跟踪修改 (M) 的变更目录，避免被未跟踪的临时文件夹抢占
            modified_lines = [l for l in lines if "M" in l[:2]]
            candidate_lines = modified_lines if modified_lines else lines
            for line in candidate_lines:
                m = re.search(r"openspec/changes/([^/]+)/", line)
                if m and m.group(1) != "archive":
                    matched_name = m.group(1)
                    matched_path = os.path.join(CHANGES_DIR, matched_name)
                    if os.path.isdir(matched_path):
                        return matched_path, matched_name
    except Exception as e:
        pass

    # 2. 兜底寻找最新的未归档变更
    candidates = []
    for item in sorted(os.listdir(CHANGES_DIR), reverse=True):
        p = os.path.join(CHANGES_DIR, item)
        if os.path.isdir(p) and item != "archive" and not item.startswith("."):
            candidates.append((p, item))
    if candidates:
        return candidates[0]
    return None

def call_workbuddy(prompt, remote_host=None, model="deepseek-v4.1-flash"):
    """
    调用 WorkBuddy 进行审查 (默认使用 deepseek-v4.1-flash 模型，单次阻塞直调，零轮询零多余Token)
    统一使用 stdin 管道传递 prompt，彻底避免命令行参数长度 (ARG_MAX) 溢出。
    """
    if remote_host:
        cmd = ["ssh", remote_host, f"codebuddy -p --model {model}"]
    else:
        cmd = [CODEBUDDY_BIN, "-p", "--model", model]

    print(f"[*] 正在调用 WorkBuddy 审查模型 [{model}] (工作区: {PROJECT_ROOT})...")
    clean_env = os.environ.copy()
    for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]:
        clean_env.pop(k, None)
    clean_env["NO_PROXY"] = "*"
    clean_env["no_proxy"] = "*"
    try:
        result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, env=clean_env, timeout=240)
    except subprocess.TimeoutExpired:
        print("\n" + "="*80)
        print("🔴【WorkBuddy 调用超时 (超过 240s)】: 请检查网络或 WorkBuddy 响应")
        print("="*80 + "\n")
        return None, None

    if result.returncode != 0 or not result.stdout.strip():
        err_msg = result.stderr.strip() or '服务无响应/通道受限'
        print("\n" + "="*80)
        print(f"🔴【WorkBuddy 响应异常】: {err_msg}")
        print("="*80 + "\n")
        return None, None

    return result.stdout.strip(), model

def append_to_review_log(change_path, review_content, reviewer_name="WorkBuddy (hy3)"):
    log_path = os.path.join(change_path, "review-log.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"\n\n---\n\n### [{timestamp}] 审查意见（来自 {reviewer_name}）\n\n"
    entry += review_content + "\n"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[+] 审查意见已成功追加到 {log_path}")

def parse_review_conclusion(review_text):
    """解析审查结论标签"""
    if "[通过]" in review_text:
        return "APPROVED"
    elif "[需修正]" in review_text:
        return "NEEDS_FIX"
    elif "[待讨论]" in review_text:
        return "DISCUSS"
    return "UNKNOWN"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WorkBuddy OpenSpec 自动审查工具 (DeepSeek 4.1 Flash 极速通道)")
    parser.add_argument("--remote", help="远程 SSH 主机 (如 user@host)", default=None)
    parser.add_argument("--change", help="指定待审查的变更目录名称或路径", default=None)
    parser.add_argument("--stage", choices=["design", "code"], default="design", help="审查阶段：design(方案设计) 或 code(代码实现)")
    parser.add_argument("--model", default="deepseek-v4.1-flash", help="审查模型 ID (默认: deepseek-v4.1-flash)")
    parser.add_argument("--test", action="store_true", help="测试连通性")
    args = parser.parse_args()

    if args.test:
        resp, used = call_workbuddy("请用一句话确认连通性，并回复【WorkBuddy DeepSeek 4.1 Flash Reviewer 就绪】。", args.remote, args.model)
        if resp:
            print(f"WorkBuddy 回复: {resp}")
            sys.exit(0)
        else:
            sys.exit(5)

    active = get_active_change(args.change)
    
    # 提取审查上下文
    context = ""
    change_path = None
    if active:
        change_path, change_name = active
        print(f"[*] 发现活跃 OpenSpec 变更: {change_name}")
        proposal_file = os.path.join(change_path, "proposal.md")
        design_file = os.path.join(change_path, "design.md")
        tasks_file = os.path.join(change_path, "tasks.md")
        if os.path.exists(proposal_file):
            with open(proposal_file, "r", encoding="utf-8") as f: context += f"--- proposal.md ---\n{f.read()}\n\n"
        if os.path.exists(design_file):
            with open(design_file, "r", encoding="utf-8") as f: context += f"--- design.md ---\n{f.read()}\n\n"
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f: context += f"--- tasks.md ---\n{f.read()}\n\n"
    else:
        print(f"[*] 未发现活跃 OpenSpec 变更目录，执行纯代码 Git Diff 审查模式。")

    # 动态读取真实规则文件（保持 SSOT 单一真相源）
    rules_file = os.path.join(PROJECT_ROOT, "RULES.md")
    agents_file = os.path.join(PROJECT_ROOT, "AGENTS.md")
    rules_content = ""
    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_content += f"--- RULES.md (全量/高精节选) ---\n{f.read()[:30000]}\n\n"
    if os.path.exists(agents_file):
        with open(agents_file, "r", encoding="utf-8") as f:
            rules_content += f"--- AGENTS.md (全量/高精节选) ---\n{f.read()[:30000]}\n\n"

    diff_context = ""
    # 仅在 code(代码实现) 阶段提取真实业务代码 Diff；方案设计(design)阶段专注于规范与方案审查
    if args.stage == "code":
        exclude_patterns = [":!web/assets/**", ":!dist/**", ":!*.min.js", ":!*.map", ":!openspec/**"]
        target_dirs = ["web/", "scripts/", "tests/", "tools/"]
        # 纯只读提取业务源码变更，绝对不调用 git add/reset，杜绝改写用户索引 (解决 🔴1)
        stat_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--stat", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
        stat_text = stat_proc.stdout.strip()

        diff_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
        diff_text = diff_proc.stdout.strip()
        if not diff_text:
            diff_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "HEAD~1", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
            diff_text = diff_proc.stdout.strip()
            stat_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--stat", "HEAD~1", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
            stat_text = stat_proc.stdout.strip()

        # 检查未跟踪的新建源码文件 (如新抽象的 StudioHeader.vue)
        untracked_proc = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "web/", "scripts/", "tests/", "tools/"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        untracked_files = [f.strip() for f in untracked_proc.stdout.splitlines() if f.strip() and not any(p in f for p in ["web/assets/", "dist/", ".min.js", ".map"])]
        untracked_text = ""
        for uf in untracked_files:
            uf_path = os.path.join(PROJECT_ROOT, uf)
            if os.path.exists(uf_path) and os.path.isfile(uf_path):
                try:
                    with open(uf_path, "r", encoding="utf-8") as f:
                        untracked_text += f"\n--- 【新增加的新建源码文件（未跟踪）: {uf}】---\n{f.read()[:30000]}\n"
                except Exception:
                    pass
        if untracked_files:
            stat_text += "\n" + "\n".join([f" {uf} | (新创建未跟踪文件)" for uf in untracked_files])

        if diff_text or untracked_text:
            diff_context = f"\n--- 【Git Diff 变更摘要 (git diff --stat)】---\n{stat_text}\n\n--- 【Git Diff 业务源码变更代码】---\n{diff_text[:300000]}\n{untracked_text[:50000]}\n"
    else:
        diff_context = "\n--- 【开发状态说明】---\n当前处于【方案设计与架构定义阶段】（stage=design），尚未进入编码阶段，暂无代码 Diff。请重点审查 proposal.md、design.md 与 tasks.md 的严谨性、架构复用与合规性。\n"

    if not context and not diff_context.strip():
        print("[!] 未找到任何待审查的内容（没有活跃变更且没有 Git 改动）。")
        sys.exit(1)

    prompt = f"""你是本项目的严格代码审查者（Reviewer）。请基于以下全局规范、方案设计与代码 Diff 进行纯文本审查（严禁调用任何外部工具或 MCP）：

{rules_content}
{context}
{diff_context}

请严格遵守审阅规范，直接输出纯文本：
1. 对照 proposal.md / design.md / tasks.md 审查方案设计与代码实现是否严谨完整；
2. 审查核心关注点：
   - 是否严格遵循规范与架构复用（拒绝打补丁和重复面条代码）；
   - 是否存在浏览器兼容性风险（PC 浏览器桌面端、Safari/Chrome 双内核兼容、纯函数不依赖 DOM）或破坏现有业务；
   - 规则与设计是否有逻辑漏洞；
3. 问题级别分类（🔴 必须改、🟡 建议改、🟢 优化建议）；
4. 明确且唯一的结论标签（必须在末尾单独成行输出以下三个标签之一：`[通过]`、`[需修正]` 或 `[待讨论]`）。
"""

    review_res, used_model = call_workbuddy(prompt, args.remote, args.model)
    if not review_res:
        sys.exit(5)

    reviewer_label = f"WorkBuddy ({used_model}, 远程 {args.remote})" if args.remote else f"WorkBuddy ({used_model})"
    
    if change_path:
        append_to_review_log(change_path, review_res, reviewer_label)
    else:
        print("\n" + "="*40 + f" 审查意见 ({reviewer_label}) " + "="*40)
        print(review_res)
        print("="*90 + "\n")

    conclusion = parse_review_conclusion(review_res)
    print(f"[*] 审查结论: {conclusion}")
    if conclusion == "APPROVED":
        sys.exit(0)
    elif conclusion == "NEEDS_FIX":
        sys.exit(2)
    elif conclusion == "DISCUSS":
        sys.exit(3)
    else:
        sys.exit(4)
