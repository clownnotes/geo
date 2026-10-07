"""诊断深化：IDE 提示词组装 + 侦察 JSON 是否含豆包全文。"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from .utils import PROJECT_ROOT, PROJECTS_DIR, load_project_config

DEEPEN_PROMPT_REL = os.path.join(
    "openspec",
    "changes",
    "archive",
    "2026-09-16-对照苍何诊断与答题卡母盘的交付提升探讨",
    "prompts",
    "diag-deepen-report-ide.md",
)

# 每题至少要有这么长的正文才算「有全文」
_MIN_ANSWER_CHARS = 80
_ANSWER_KEYS = (
    "answer_full",
    "answer_text",
    "full_answer",
    "raw_answer",
    "doubao_answer",
    "response_full",
)


def deepen_prompt_path() -> str:
    return os.path.join(PROJECT_ROOT, DEEPEN_PROMPT_REL)


def build_diag_deepen_prompt(project_id: str) -> Dict[str, Any]:
    """读取 OpenSpec 提示词模板，填入项目 id，并附上侦察全文缺口提示。"""
    path = deepen_prompt_path()
    if not os.path.isfile(path):
        return {
            "success": False,
            "message": f"找不到深化提示词文件：{DEEPEN_PROMPT_REL}",
        }
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    text = raw.replace("<project_id>", project_id).replace("projects/<project_id>/", f"projects/{project_id}/")
    audit = audit_probe_answer_coverage(project_id)
    gap_note = ""
    if not audit.get("has_usable_full_answers"):
        gap_note = (
            "\n\n---\n【落盘缺口 · 管理台自动附上】\n"
            f"当前侦察 JSON 多数题目没有足够长的豆包全文（answer_full）。"
            f"已扫描 {audit.get('files_scanned', 0)} 个文件，"
            f"有全文的题目约 {audit.get('items_with_full', 0)} / {audit.get('items_total', 0)}。\n"
            "请先按阶段零「②收工说明书」要求重写/补写 competitor_probe_*.json（每题必须含 answer_full），"
            "再写深化报告；没有原文就写「本轮未落全文」，禁止编造豆包说过的话。\n"
        )
        text = text + gap_note
    return {
        "success": True,
        "project_id": project_id,
        "clipboard": text,
        "prompt_path": DEEPEN_PROMPT_REL,
        "probe_audit": audit,
    }


def _item_answer_text(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    for k in _ANSWER_KEYS:
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def audit_probe_answer_coverage(project_id: str) -> Dict[str, Any]:
    """检查 outputs/competitor_probe_*.json 是否带有足够长的回答全文。"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    files: List[str] = []
    items_total = 0
    items_with_full = 0
    samples: List[Dict[str, Any]] = []
    if os.path.isdir(out_dir):
        for name in sorted(os.listdir(out_dir)):
            if not re.match(r"^competitor_probe_.*\.json$", name, re.I):
                continue
            abs_path = os.path.join(out_dir, name)
            if not os.path.isfile(abs_path):
                continue
            files.append(name)
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                continue
            for it in items:
                items_total += 1
                ans = _item_answer_text(it if isinstance(it, dict) else {})
                if len(ans) >= _MIN_ANSWER_CHARS:
                    items_with_full += 1
                elif len(samples) < 3 and isinstance(it, dict):
                    samples.append(
                        {
                            "file": name,
                            "query": (it.get("query") or "")[:80],
                            "has_verdict_only": bool(it.get("doubao_verdict")),
                            "answer_len": len(ans),
                        }
                    )
    has_usable = items_total > 0 and items_with_full >= max(1, items_total // 2)
    return {
        "success": True,
        "project_id": project_id,
        "files_scanned": len(files),
        "files": files[-5:],
        "items_total": items_total,
        "items_with_full": items_with_full,
        "min_chars": _MIN_ANSWER_CHARS,
        "has_usable_full_answers": has_usable,
        "gap_samples": samples,
        "hint": (
            "多数题目已有 answer_full，可供②深化报告使用。"
            if has_usable
            else "侦察结果多半只有摘要/勾选字段，缺少豆包全文。收工落盘须写入 answer_full。"
        ),
    }
