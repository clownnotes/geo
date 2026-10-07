#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qoder 专家团外部参谋自动审查脚本 (Qoder Reviewer Bridge)
使用 Qoder CLI (Qwen3.8-Flash 1M 上下文极高深度思考) 审查代码与规范
包含四大防幻觉门禁硬闸：
1. design.md 必须存在
2. design.md 必须包含三大支柱（用户立规原文、第一个AI理解与决定、1对1映射推导链条表）
3. 审查结果自动追加到 review-log.md
4. 严格解析 [通过] / [需修正] / [待讨论] 结论
"""

import os
import sys
import subprocess
import shutil
import re
from datetime import datetime

QODER_BIN = "/Users/a1/.qoder/entry/qoder"

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
        if os.path.exists(target_change) and os.path.isdir(target_change):
            return target_change, os.path.basename(os.path.normpath(target_change))
        candidate = os.path.join(CHANGES_DIR, target_change)
        if os.path.exists(candidate) and os.path.isdir(candidate):
            return candidate, target_change
        for item in os.listdir(CHANGES_DIR):
            if target_change in item:
                return os.path.join(CHANGES_DIR, item), item

    # 1. 优先通过 git status 探测当前正在修改的 OpenSpec 变更目录
    try:
        git_res = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if git_res.returncode == 0:
            lines = git_res.stdout.splitlines()
            modified_lines = [l for l in lines if "M" in l[:2]]
            candidate_lines = modified_lines if modified_lines else lines
            for line in candidate_lines:
                m = re.search(r"openspec/changes/([^/]+)/", line)
                if m and m.group(1) != "archive":
                    matched_name = m.group(1)
                    matched_path = os.path.join(CHANGES_DIR, matched_name)
                    if os.path.isdir(matched_path):
                        return matched_path, matched_name
    except Exception:
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

def verify_design_gate(change_path):
    """
    【双 AI 防幻觉硬门禁 · 2026-10-06 师弟立规】
    design.md 架构设计绝对不可缺失！必须包含三大核心支柱：
    ① 0.1 👤 用户核心决策与立规原文 (第一真理源)
    ② 0.2 🤖 第一个 AI（Antigravity）理解与技术决定
    ③ 0.3 🔗 1对1 映射推导链条表 (Derivation Chain SSOT)
    """
    if not change_path:
        return True
    design_file = os.path.join(change_path, "design.md")
    if not os.path.exists(design_file):
        print("\n" + "="*80)
        print("🔴【门禁拦截 · design.md 缺失】: 当前变更目录未找到 design.md 架构设计文档！")
        print("  师弟立规铁律：任何变更必须具备 design.md，严禁跳过设计文档送审！")
        print("="*80 + "\n")
        return False

    with open(design_file, "r", encoding="utf-8") as f:
        content = f.read()

    pillars = [
        ("0.1", "用户核心决策与立规原文"),
        ("0.2", "第一个 AI"),
        ("0.3", "1对1 映射推导链条表"),
    ]
    missing = []
    for num, name in pillars:
        if num not in content and name not in content:
            missing.append(f"{num} {name}")

    if missing:
        print("\n" + "="*80)
        print(f"🔴【门禁拦截 · design.md 缺少核心支柱】: 缺失项: {', '.join(missing)}")
        print("  师弟立规铁律：design.md 必须包含三大支柱与 1对1 映射推导链条表！")
        print("="*80 + "\n")
        return False

    return True

def call_qoder(prompt, model="Qwen3.8-Flash"):
    """
    调用 Qoder CLI 进行外部参谋审查 (统一使用 stdin 管道传递 prompt，杜绝 ARG_MAX 命令行溢出)
    """
    if not os.path.exists(QODER_BIN):
        print(f"🔴【Qoder 未找到】: 找不到本地二进制 {QODER_BIN}")
        return None, None

    cmd = [
        QODER_BIN, "-p", "-m", model,
        "--no-session-persistence",
        "--tools", "",
        "--system-prompt", "你是只读纯文本代码审查专家。你没有任何外部工具权限，严禁输出任何 <tool_call> 标签或 XML 函数调用语法。所有审查所需代码和规范均已完整提供。请直接输出纯文本 Markdown 审查报告，并在末尾单独成行输出唯一结论标签：[通过]、[需修正] 或 [待讨论]。",
        "--"
    ]
    print(f"[*] 正在调用 Qoder 外部审查参谋 [{model}] (工作区: {PROJECT_ROOT})...")
    try:
        result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print("\n" + "="*80)
        print("🔴【Qoder 调用超时 (超过 300s)】: 请检查网络或 Qoder 响应")
        print("="*80 + "\n")
        return None, None

    output = result.stdout.strip()
    # 过滤可能的前置警告行
    lines = output.splitlines()
    clean_lines = [l for l in lines if not l.startswith("Detected 1 skill name conflict")]
    cleaned_output = "\n".join(clean_lines).strip()

    if result.returncode != 0 or not cleaned_output:
        err_msg = result.stderr.strip() or output or '服务无响应'
        print("\n" + "="*80)
        print(f"🔴【Qoder 响应异常】: {err_msg}")
        print("="*80 + "\n")
        return None, None

    return cleaned_output, model

def append_to_review_log(change_path, review_content, reviewer_name="Qoder (Qwen3.8-Flash)"):
    log_path = os.path.join(change_path, "review-log.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"\n\n---\n\n### [{timestamp}] 审查意见（来自 {reviewer_name}）\n\n"
    entry += review_content + "\n"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[+] 审查意见已成功追加到 {log_path}")

def parse_review_conclusion(review_text):
    if "[通过]" in review_text:
        return "APPROVED"
    elif "[需修正]" in review_text:
        return "NEEDS_FIX"
    elif "[待讨论]" in review_text:
        return "DISCUSS"
    return "UNKNOWN"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Qoder OpenSpec 外部参谋自动审查工具 (Qwen 3.8-Flash 极高思考)")
    parser.add_argument("--change", help="指定待审查的变更目录名称或路径", default=None)
    parser.add_argument("--stage", choices=["design", "code"], default="code", help="审查阶段：design(方案设计) 或 code(代码实现)")
    parser.add_argument("--model", default="Qwen3.8-Flash", help="审查模型 (默认: Qwen3.8-Flash)")
    parser.add_argument("--test", action="store_true", help="测试连通性")
    args = parser.parse_args()

    if args.test:
        resp, used = call_qoder("请用一句话确认连通性，并回复【Qoder Qwen3.8-Flash Reviewer 就绪】。", args.model)
        if resp:
            print(f"Qoder 回复: {resp}")
            sys.exit(0)
        else:
            sys.exit(5)

    active = get_active_change(args.change)
    change_path = None
    context = ""
    if active:
        change_path, change_name = active
        print(f"[*] 发现活跃 OpenSpec 变更: {change_name}")

        # 门禁核验
        if not verify_design_gate(change_path):
            sys.exit(1)

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

    rules_file = os.path.join(PROJECT_ROOT, "RULES.md")
    agents_file = os.path.join(PROJECT_ROOT, "AGENTS.md")
    rules_content = ""
    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_content += f"--- RULES.md ---\n{f.read()[:30000]}\n\n"
    if os.path.exists(agents_file):
        with open(agents_file, "r", encoding="utf-8") as f:
            rules_content += f"--- AGENTS.md ---\n{f.read()[:30000]}\n\n"

    diff_context = ""
    if args.stage == "code":
        exclude_patterns = [":!src/web/assets/**", ":!web/assets/**", ":!dist/**", ":!*.min.js", ":!*.map", ":!openspec/**"]
        target_dirs = ["src/", "web/", "scripts/", "tests/", "tools/", "geo", "package.json"]
        stat_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--stat", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
        stat_text = stat_proc.stdout.strip()

        diff_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
        diff_text = diff_proc.stdout.strip()
        if not diff_text:
            diff_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "HEAD~1", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
            diff_text = diff_proc.stdout.strip()
            stat_proc = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--stat", "HEAD~1", "HEAD", "--"] + target_dirs + exclude_patterns, cwd=PROJECT_ROOT, capture_output=True, text=True)
            stat_text = stat_proc.stdout.strip()

        untracked_proc = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "src/", "web/", "scripts/", "tests/", "tools/"], cwd=PROJECT_ROOT, capture_output=True, text=True)
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
        diff_context = "\n--- 【开发状态说明】---\n当前处于【方案设计阶段】（stage=design），重点审查规范严谨性。\n"

    if not context and not diff_context.strip():
        print("[!] 未找到任何待审查的内容。")
        sys.exit(1)

    prompt = f"""你是本项目的外部特邀独立代码审查专家（Reviewer）。请基于以下全局规范、方案设计与真实业务代码 Diff 进行纯文本严苛审查：

{rules_content}
{context}
{diff_context}

【审查红线禁令与执行铁律】：
1. 你当前运行在纯文本审查只读模式，严禁调用任何工具，严禁输出任何 <tool_call>、<function=...> 等 XML 标签！
2. 所有审查所需的代码 Diff、文件内容与全局规则已经在上方完整提供，无需也不允许发起额外查询；
3. 请直接输出标准纯文本 Markdown 格式审查报告，按以下问题级别分类：
   - 🔴 必须改（阻断性 Bug 或违背立规）
   - 🟡 建议改（可优化或潜在风险）
   - 🟢 优化建议（代码可读性或微小体验）
4. 审查报告最后一行必须且只能单独成行输出以下唯一结论标签之一：
[通过]
或
[需修正]
或
[待讨论]
"""

    review_res, used_model = call_qoder(prompt, args.model)
    if not review_res:
        sys.exit(5)

    conclusion = parse_review_conclusion(review_res)
    print(f"[*] 审查结论: {conclusion}")

    reviewer_label = f"Qoder ({used_model})"
    if change_path and conclusion != "UNKNOWN":
        append_to_review_log(change_path, review_res, reviewer_label)
    else:
        print("\n" + "="*40 + f" 审查意见 ({reviewer_label}) " + "="*40)
        print(review_res)
        print("="*90 + "\n")
    if conclusion == "APPROVED":
        sys.exit(0)
    elif conclusion == "NEEDS_FIX":
        sys.exit(2)
    elif conclusion == "DISCUSS":
        sys.exit(3)
    else:
        sys.exit(4)
