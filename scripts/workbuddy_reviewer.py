#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 跨 IDE 独立审查脚本 (scripts/workbuddy_reviewer.py)
用于自动调用 WorkBuddy (混元 3 免费通道) 对当前 OpenSpec 活跃变更进行严格对抗审查，并写入 review-log.md。
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

CODEBUDDY_BIN = "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy"
if not os.path.exists(CODEBUDDY_BIN):
    which_bin = shutil.which("codebuddy")
    if which_bin:
        CODEBUDDY_BIN = which_bin

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHANGES_DIR = os.path.join(PROJECT_ROOT, "openspec", "changes")


def get_active_change():
    if not os.path.exists(CHANGES_DIR):
        return None
    for item in sorted(os.listdir(CHANGES_DIR)):
        p = os.path.join(CHANGES_DIR, item)
        if os.path.isdir(p) and item != "archive" and not item.startswith("."):
            return p, item
    return None


def call_workbuddy(prompt: str, model: str = "hy3", fallback_model: str = "hy3") -> str:
    if not os.path.exists(CODEBUDDY_BIN):
        print(f"[!] 未检测到 WorkBuddy CLI 二进制路径: {CODEBUDDY_BIN}")
        return None

    cmd = [CODEBUDDY_BIN, "-p", "-y", "--no-session-persistence", "--model", model, "--", prompt]
    print(f"[*] 正在调用 WorkBuddy 独立审查模型 [通道: {model} (免费)] (工作区: {PROJECT_ROOT})...")

    result = None
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print(f"[!] 混元三免费通道 ({model}) 调用超时 (120s)...")

    if result is None or result.returncode != 0 or not result.stdout.strip():
        print(f"[!] 混元三免费通道 ({model}) 调用受限或失败: {result.stderr.strip() if result else '超时/无响应'}")
        print(f"[*] 正在自动尝试备用通道 ({fallback_model})...")
        fallback_cmd = [CODEBUDDY_BIN, "-p", "-y", "--no-session-persistence", "--model", fallback_model, "--", prompt]
        try:
            result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0 or not result.stdout.strip():
                print(f"[!] WorkBuddy 备用通道调用亦失败: {result.stderr.strip()}")
                return None
        except subprocess.TimeoutExpired:
            print("[!] WorkBuddy 备用通道亦超时")
            return None

    return result.stdout.strip()


def append_to_review_log(change_path: str, review_content: str, reviewer_label: str = "WorkBuddy"):
    log_path = os.path.join(change_path, "review-log.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = f"\n\n---\n\n### {timestamp} {reviewer_label}\n\n"
    entry += review_content + "\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[+] 审查意见已成功追加到 {log_path}")


def parse_review_conclusion(review_text: str) -> str:
    if "[通过]" in review_text:
        return "APPROVED"
    elif "[需修正]" in review_text:
        return "NEEDS_FIX"
    elif "[待讨论]" in review_text:
        return "DISCUSS"
    return "UNKNOWN"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="WorkBuddy OpenSpec 自动审查工具")
    parser.add_argument("--stage", choices=["design", "code"], default="code", help="审查阶段")
    parser.add_argument("--model", default="hy3", help="主审查模型 ID (默认: hy3 免费版)")
    parser.add_argument("--fallback-model", default="hy3", help="备用审查模型 ID")
    parser.add_argument("--test", action="store_true", help="测试连通性")
    args = parser.parse_args()

    if args.test:
        resp = call_workbuddy("请用一句话确认连通性，并回复【WorkBuddy Reviewer 就绪】。", model=args.model, fallback_model=args.fallback_model)
        print(f"WorkBuddy 回复: {resp}")
        sys.exit(0)

    active = get_active_change()
    if not active:
        print("[!] 当前没有正在进行的活跃 OpenSpec 变更！")
        sys.exit(1)

    change_path, change_name = active
    print(f"[*] 发现活跃 OpenSpec 变更: {change_name}")

    context = ""
    for fn in ["proposal.md", "design.md", "tasks.md"]:
        fp = os.path.join(change_path, fn)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                context += f"--- {fn} ---\n{f.read()}\n\n"

    agents_file = os.path.join(PROJECT_ROOT, "AGENTS.md")
    agents_content = ""
    if os.path.exists(agents_file):
        with open(agents_file, "r", encoding="utf-8") as f:
            agents_content = f"--- AGENTS.md (全局规范与红线) ---\n{f.read()[:1000]}\n\n"

    # 提取核心代码
    code_summary = ""
    auth_file = os.path.join(PROJECT_ROOT, "tools/geo/citation_authority.py")
    if os.path.exists(auth_file):
        with open(auth_file, "r", encoding="utf-8") as f:
            code_summary = f"\n=== 核心实现: tools/geo/citation_authority.py ===\n{f.read()[:2500]}\n"

    prompt = f"""你是本项目的严格代码与架构独立审查者（Reviewer）。
请根据以下 OpenSpec 规范与实际交付的代码对【{change_name}】进行严格验收审查：

{agents_content}
{context[:2500]}
{code_summary}

=== 审查要点 ===
1. 【核心能力交付】：CHANNEL_AUTHORITY_DB 权威库、五大模型亲和度矩阵与单链采纳率推演是否完整交付；
2. 【安全与规范红线】：是否遵守 AGENTS.md 约束（本地 8088 验证、严禁私自推生产）；
3. 【异常与健壮性】：死链状态惩罚、时延加权、数据落盘与 JSON 导出是否健壮；
4. 【四行业母版验证】：是否支持四行业母版批量推演并生成 15_*.md 与 JSON 交付物。

请输出以下结构：
- 一、审查结论（在最后一行明确单独输出 `[通过]`、`[需修正]` 或 `[待讨论]`）
- 二、🔴 关键问题（如有阻断性安全/业务漏洞）
- 三、🟡 改进建议（如有架构或体验优化空间）
- 四、🟢 落地亮点总结
"""

    review_res = call_workbuddy(prompt, model=args.model, fallback_model=args.fallback_model)
    if not review_res:
        print("[!] 审查调用失败，请检查 WorkBuddy 运行状态。")
        sys.exit(1)

    model_label = f"{args.model} -> {args.fallback_model}"
    reviewer_label = f"WorkBuddy ({model_label}) [独立跨 IDE 审查]"

    append_to_review_log(change_path, review_res, reviewer_label)

    print("\n" + "="*45 + f" 审查意见 ({reviewer_label}) " + "="*45)
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


if __name__ == "__main__":
    main()
