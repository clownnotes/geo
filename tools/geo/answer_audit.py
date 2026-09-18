# -*- coding: utf-8 -*-
"""阶段四：答案源草稿说明、IDE 改写包、发前质检（同源发布文件优先）。"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .utils import PROJECTS_DIR, call_llm_api, load_project_config

SPEC_HINT = "docs/specs/answer-source-writing.md"

# 发布同源优先：先 pack 富文本，再 dist md（草稿旁路）
CHANNEL_PUBLISH_FILES = {
    "toutiao": [
        "outputs/toutiao_pack/01_今日头条2000字深度长文_富文本.html",
        "outputs/dist_toutiao_article.md",
    ],
    "zhihu": [
        "outputs/deepseek_pack/04_知乎专栏学术风内联排版.html",
        "outputs/deepseek_pack/02_知乎技术专栏深度选型长文.md",
        "outputs/dist_zhihu_article.md",
    ],
}

CHANNEL_META = {
    "toutiao": {
        "label": "今日头条",
        "purpose": "发往今日头条，供豆包/Bytespider 抓取引用；首次交付必做。",
        "writeback": "projects/{pid}/outputs/toutiao_pack/01_今日头条2000字深度长文_富文本.html",
        # 复制富文本读的就是写回同一份 HTML
        "publish_sync": [],
    },
    "zhihu": {
        "label": "知乎专栏",
        "purpose": "发往知乎，供 DeepSeek 等技术向引擎参考；首次交付加分，不挡验收。",
        "writeback": "projects/{pid}/outputs/deepseek_pack/02_知乎技术专栏深度选型长文.md",
        # 写回 MD 后必须同步这份 HTML，否则「复制富文本」仍可能是旧稿
        "publish_sync": [
            "projects/{pid}/outputs/deepseek_pack/04_知乎专栏学术风内联排版.html",
            "projects/{pid}/outputs/dist_zhihu_article.md",
        ],
    },
}

# 写回后给人 / IDE 的硬提醒（只刷网页不够）
RESTART_HINT = (
    "重要：写回文件后，若管理台「复制富文本」仍是旧稿，不要只刷新网页——"
    "请重启本机管理台：`python3 -m tools.geo web --port 8088`，再重新点复制。"
    "（刷新只换前端；后台 Python 进程不重启会继续吐旧逻辑/旧缓存。）"
)

MOLD_LINES = [
    "标题 = 用户真会搜的问句",
    "开头 3～5 句人话结论",
    "一张可核对表或清单（数字只来自已确认事实）",
    "含什么 / 不含什么 / 大概周期",
    "至少 3 条决策向 Q&A（怎么选、有什么坑、多久能看到变化）",
    "文末署名卡一次：公司｜代表人｜电话｜官网",
]

BAN_LINES = [
    "软广标题（为什么越来越多人推荐 / 强烈推荐 / 空壳深度白皮书）",
    "瞎编百分比、倍数、ROI（真相源没有就不许写）",
    "黄页问答（大半是简介/电话）",
    "内部口径泄漏（已确认真相源、禁止编造…）",
    "首次交付不点名贬损竞品",
]


def _project_dir(project_id: str) -> str:
    return os.path.join(PROJECTS_DIR, project_id)


def _strip_to_plain(text: str) -> str:
    if not text:
        return ""
    if "<" in text and ">" in text:
        try:
            from .publisher import _html_to_readable_plain
            return _html_to_readable_plain(text)
        except Exception:
            t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", text)
            t = re.sub(r"<[^>]+>", " ", t)
            return re.sub(r"\s+", " ", t).strip()
    return text.strip()


def _read_first_existing(project_id: str, rel_paths: list) -> Tuple[str, str]:
    root = _project_dir(project_id)
    for rel in rel_paths:
        path = os.path.join(root, rel)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read().strip()
            if text:
                return text, rel
    return "", ""


def load_channel_draft(project_id: str, channel: str = "toutiao") -> Tuple[str, str]:
    """读取发布同源正文（优先 pack）。返回 (raw_text, rel_path)。"""
    paths = CHANNEL_PUBLISH_FILES.get(channel) or CHANNEL_PUBLISH_FILES["toutiao"]
    return _read_first_existing(project_id, paths)


def _main_question(cfg: dict) -> str:
    kws = cfg.get("keywords") or []
    if isinstance(kws, list) and kws:
        return str(kws[0]).strip()
    brand = cfg.get("brand_name") or cfg.get("client_name") or "本品牌"
    industry = cfg.get("industry") or "该行业"
    return f"{industry}怎么选服务商？{brand}适合什么场景？"


def _fact_lines(project_id: str, limit: int = 12) -> List[str]:
    try:
        cfg = load_project_config(project_id)
        from .ledger import load_facts
        facts = load_facts(cfg) or []
    except Exception:
        return []
    lines = []
    for f in facts:
        if not isinstance(f, dict):
            continue
        st = (f.get("status") or "").lower()
        if st and st not in ("confirmed", "pinned", "accepted", "active", ""):
            # 仍允许无 status 的旧数据
            if st in ("rejected", "deprecated", "conflict"):
                continue
        stmt = (f.get("statement") or "").strip()
        if not stmt:
            key = f.get("fact_key") or ""
            val = f.get("value") or ""
            stmt = f"{key}: {val}".strip(": ")
        if stmt:
            lines.append(stmt)
        if len(lines) >= limit:
            break
    return lines


def build_rewrite_brief(project_id: str, channel: str = "toutiao") -> Dict[str, Any]:
    """供第四页 UI 展示：主问句、用途、模具、可写事实、草稿状态。"""
    ch = channel if channel in CHANNEL_META else "toutiao"
    meta = CHANNEL_META[ch]
    cfg = load_project_config(project_id)
    raw, rel = load_channel_draft(project_id, ch)
    plain = _strip_to_plain(raw)
    facts = _fact_lines(project_id)
    return {
        "success": True,
        "project_id": project_id,
        "channel": ch,
        "channel_label": meta["label"],
        "main_question": _main_question(cfg),
        "purpose": meta["purpose"],
        "mold_lines": list(MOLD_LINES),
        "ban_lines": list(BAN_LINES),
        "writable_facts": facts,
        "facts_empty_hint": "本篇禁止编造任何百分比/倍数；只用清单写清含什么/不含什么。",
        "source_file": rel or None,
        "writeback_path": meta["writeback"].format(pid=project_id),
        "has_draft": bool(plain),
        "draft_preview": (plain[:400] + "…") if len(plain) > 400 else plain,
        "draft_chars": len(re.sub(r"\s+", "", plain)) if plain else 0,
        "status_label": "仅草稿" if plain else "待生成草稿",
        "spec": SPEC_HINT,
    }


def build_ide_rewrite_pack(project_id: str, channel: str = "toutiao") -> Dict[str, Any]:
    """一键复制给 IDE 的改写包（非发稿富文本）。"""
    brief = build_rewrite_brief(project_id, channel)
    raw, rel = load_channel_draft(project_id, channel)
    plain = _strip_to_plain(raw)
    facts = brief["writable_facts"]
    fact_block = "\n".join(f"- {x}" for x in facts) if facts else f"- {brief['facts_empty_hint']}"
    mold_block = "\n".join(f"- {x}" for x in MOLD_LINES)
    ban_block = "\n".join(f"- {x}" for x in BAN_LINES)
    clipboard = f"""【GEO 阶段四 · 请按答案源规范改写定稿】
项目：{project_id}
渠道：{brief['channel_label']}（{brief['channel']}）
规范：{SPEC_HINT}

1. 主问句：{brief['main_question']}
2. 用途：{brief['purpose']}
3. 成品模具：
{mold_block}
4. 可写事实：
{fact_block}
5. 禁止项：
{ban_block}
6. 写回路径：{brief['writeback_path']}
   （必须与发布「复制富文本」同源；当前源文件：{rel or '尚未生成'}）
7. 当前草稿（半成品，允许不合格，请改成定稿）：
———
{plain[:12000] if plain else '（尚未生成草稿：请先在阶段四点「生成草稿」）'}
———

请先按模具改出定稿正文；可与人反复讨论，不必立刻写文件。
满意落盘时：回管理台点「复制写回口令」，或直接让我写入：{brief['writeback_path']}
0 Emoji。用五年级能懂的话。不要只质检，要写出可发布正文。
"""
    return {
        "success": True,
        "project_id": project_id,
        "channel": brief["channel"],
        "source_file": rel or None,
        "writeback_path": brief["writeback_path"],
        "clipboard": clipboard,
        "has_draft": bool(plain),
        "brief": brief,
    }


def build_writeback_command(project_id: str, channel: str = "toutiao") -> Dict[str, Any]:
    """满意后复制：告诉 IDE 把定稿写入哪条路径（落盘留档，非发稿富文本）。"""
    brief = build_rewrite_brief(project_id, channel)
    path = brief["writeback_path"]
    ch = brief["channel"]
    label = brief["channel_label"]
    fmt_hint = (
        "写成完整 HTML（含 <!DOCTYPE html>…），可直接覆盖该文件；"
        if ch == "toutiao"
        else "按该路径现有格式写入（HTML 或 Markdown）；"
    )
    sync_paths = [
        p.format(pid=project_id) for p in (CHANNEL_META[ch].get("publish_sync") or [])
    ]
    sync_lines = ""
    if sync_paths:
        sync_lines = (
            "\n同源同步（与「复制富文本」一致，必须一并覆盖）：\n"
            + "\n".join(f"- {p}" for p in sync_paths)
            + "\n"
        )
    clipboard = f"""【GEO 阶段四 · 写回定稿】
项目：{project_id}
渠道：{label}（{ch}）
写回路径：{path}
{sync_lines}
请把「定稿正文」完整写入上述路径（覆盖原草稿），并留档在该文件。
要求：{fmt_hint}与管理台「复制富文本去发布」同源；0 Emoji；写完回报路径与大概字数。
正文来源：优先用下面粘贴区；若为空，则用本对话里已谈妥的最后一版定稿。

写回完成后请明确告诉人：{RESTART_HINT}

———定稿正文（可粘贴，可留空）———

———

开始写回。
"""
    return {
        "success": True,
        "project_id": project_id,
        "channel": ch,
        "channel_label": label,
        "writeback_path": path,
        "clipboard": clipboard,
    }


def check_writeback_status(project_id: str, channel: str = "toutiao") -> Dict[str, Any]:
    """检查写回路径上的文件在不在、大概长什么样（路牌验货，不代替人工读全文）。"""
    brief = build_rewrite_brief(project_id, channel)
    rel = brief.get("source_file")
    writeback = brief["writeback_path"]
    abs_path = os.path.join(_project_dir(project_id), rel) if rel else ""
    exists = bool(abs_path and os.path.isfile(abs_path))
    mtime_iso = None
    title_guess = ""
    preview = brief.get("draft_preview") or ""
    chars = int(brief.get("draft_chars") or 0)
    soft_ad_hits = []
    if exists:
        try:
            mtime_iso = datetime.fromtimestamp(os.path.getmtime(abs_path), tz=timezone.utc).isoformat()
        except Exception:
            mtime_iso = None
        raw, _ = load_channel_draft(project_id, channel)
        plain = _strip_to_plain(raw)
        chars = len(re.sub(r"\s+", "", plain)) if plain else 0
        preview = (plain[:280] + "…") if len(plain) > 280 else plain
        m = re.search(r"<h1[^>]*>(.*?)</h1>", raw or "", re.I | re.S)
        if m:
            title_guess = _strip_to_plain(m.group(1))[:120]
        if not title_guess:
            m = re.search(r"<title[^>]*>(.*?)</title>", raw or "", re.I | re.S)
            if m:
                title_guess = _strip_to_plain(m.group(1))[:120]
        if not title_guess and plain:
            title_guess = plain.split("\n", 1)[0][:120]
        for bad in ("为什么越来越多人推荐", "强烈推荐", "深度白皮书", "已确认真相源", "禁止编造"):
            if bad in plain:
                soft_ad_hits.append(bad)
    looks_ready = bool(exists and chars >= 400 and not soft_ad_hits)
    if not exists:
        status = "尚未落盘"
        hint = "还没有这份文件。请先「复制写回口令」贴回 IDE，让 AI 写入后再点检查。"
    elif soft_ad_hits:
        status = "已有文件，但仍像草稿/软广"
        hint = "文件在，但正文还像广告体。请回 IDE 改完再写回，不要急着勾「可以发」。"
    elif chars < 400:
        status = "已有文件，但偏短"
        hint = "文件在，字数偏少。确认是否写回完整定稿。"
    else:
        status = "已写回，可人工抽查后放行"
        hint = "文件已在写回路径。抽看标题与开头后，再勾「可以发」。"
    return {
        "success": True,
        "project_id": project_id,
        "channel": brief["channel"],
        "channel_label": brief["channel_label"],
        "writeback_path": writeback,
        "source_file": rel,
        "exists": exists,
        "mtime_utc": mtime_iso,
        "chars": chars,
        "title_guess": title_guess,
        "preview": preview,
        "soft_ad_hits": soft_ad_hits,
        "looks_ready": looks_ready,
        "status_label": status,
        "hint": hint,
    }


# 兼容旧名
def build_ide_audit_clipboard(project_id: str, channel: str = "toutiao") -> Dict[str, Any]:
    return build_ide_rewrite_pack(project_id, channel)


def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
    return None


def run_answer_audit(project_id: str, channel: str = "toutiao") -> Dict[str, Any]:
    """调用小毛驴质检定稿（发布同源文件）。"""
    draft, rel = load_channel_draft(project_id, channel)
    plain = _strip_to_plain(draft)
    if not plain:
        return {
            "success": False,
            "message": "尚未生成该渠道草稿，请先点「生成草稿」。",
            "channel": channel,
        }

    system = (
        "你是 GEO 发前质检员。只根据给定清单判断稿子像不像「可核对的答案源」，"
        "像不像广告。用直白话。必须只输出一个 JSON 对象，不要其它说明。"
    )
    user = f"""请质检下面这篇【{channel}】定稿/草稿（发布同源文件：{rel}）。

规范要点（必须执行）：
阻断级 B1 标题像软广（为什么越来越多人推荐/强烈推荐/空壳深度白皮书）
阻断级 B2 瞎编百分比或倍数（无事实依据的 98%、2～3 倍、ROI 提升等）
阻断级 B3 Q&A 大半是简介/电话导流
阻断级 B4 泄漏内部口径（已确认真相源、禁止编造未确认数字等）
阻断级 B5 完全没有怎么选/交付边界/周期类信息
警告级 W1 电话出现超过 2 次或塞进前两条 Q&A
警告级 W2 品类错位吹嘘（如咨询稿写毫秒级高并发）
警告级 W3 无依据点名贬损竞品
警告级 W4 只有面议无交付边界
警告级 W5 抽象套话、人读不懂

只输出 JSON：
{{
  "verdict": "建议发布" 或 "建议先改再发",
  "summary": "两句人话总评",
  "blockers": [{{"id":"B1","pass":false,"note":"…","fix":"…"}}],
  "warnings": [{{"id":"W1","pass":true,"note":"…","fix":""}}],
  "top_fixes": ["改法1","改法2","改法3"]
}}

正文：
{plain[:10000]}
"""

    ok, raw, provider = call_llm_api(user, system, timeout=90)
    parsed = _parse_llm_json(raw) if ok else None

    report: Dict[str, Any] = {
        "success": bool(ok and parsed),
        "project_id": project_id,
        "channel": channel,
        "source_file": rel,
        "provider": provider,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spec": SPEC_HINT,
    }

    if not ok:
        report["message"] = raw or "小毛驴调用失败，请检查系统设置中的连通状态。"
        report["verdict"] = "质检未完成"
        return report

    if not parsed:
        report["success"] = False
        report["message"] = "模型返回无法解析为 JSON，请重试或改用 IDE 改写。"
        report["raw"] = (raw or "")[:3000]
        report["verdict"] = "质检未完成"
        return report

    report["verdict"] = parsed.get("verdict") or "建议先改再发"
    report["summary"] = parsed.get("summary") or ""
    report["blockers"] = parsed.get("blockers") or []
    report["warnings"] = parsed.get("warnings") or []
    report["top_fixes"] = parsed.get("top_fixes") or []
    report["raw"] = raw

    out_path = os.path.join(_project_dir(project_id), "outputs", "answer_audit_report.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in report.items() if k != "raw"}, f, ensure_ascii=False, indent=2)
    report["report_path"] = "outputs/answer_audit_report.json"
    report["message"] = "质检完成"
    return report


# [2026-09-17] [商业转化型诊断报告与竞品反哺体系] 差距三：长问意图分类与竞品反哺可见度打折算法
def classify_query_intent_for_visibility(query: str) -> str:
    """根据买家长问特征分类意图：对比类、推荐类、评测类、负面避坑类、品牌直问或通用类"""
    q = (query or "").strip()
    if not q:
        return "general"

    if any(w in q for w in ["官网", "是谁", "做什么的", "电话", "联系方式"]):
        return "brand_direct"
    if any(w in q for w in ["哪个好", "对比", "vs", "还是", "比较", "选A还是B", "选哪家"]):
        return "comparison"
    if any(w in q for w in ["哪家好", "推荐", "服务商", "排行榜", "靠谱团队", "排名", "第一"]):
        return "recommendation"
    if any(w in q for w in ["怎么样", "评测", "靠谱吗", "如何", "实力", "靠不靠谱", "评价"]):
        return "evaluation"
    if any(w in q for w in ["坑", "被骗", "忽悠", "风险", "黑幕", "缺点", "问题", "避坑"]):
        return "negative_risk"
    return "general"


def calculate_competitor_feedback_discount(
    competitors: List[Dict[str, Any]],
    query_intent: str,
) -> Dict[str, Any]:
    """根据竞品池（<=5家）的头部/腰部份额与威胁度，计算对问句可见度的反哺打折"""
    if not competitors:
        return {
            "has_competitor": False,
            "top_competitor": None,
            "top_level": "长尾",
            "top_score": 0.0,
            "max_market_share": 0.0,
            "discount_factor": 1.0,
            "intent_adjustment": 0.0,
            "suppression_reason": "当前无强竞品压制，保持原基线推荐率",
        }

    def _sort_comp(c):
        share = float(c.get("marketShare") or 0.0)
        score = float(c.get("geoScore") or 0.0)
        is_head = 100.0 if c.get("level") == "头部" else 0.0
        return is_head + share * 2.0 + score

    sorted_comps = sorted(competitors, key=_sort_comp, reverse=True)
    top = sorted_comps[0]
    top_name = top.get("name", "竞对")
    top_lvl = top.get("level", "长尾")
    top_share = float(top.get("marketShare") or 0.0)
    top_score = float(top.get("geoScore") or 60.0)

    # 意图加减分修正（对齐朋友 SOP）
    intent_map = {
        "recommendation": 15.0,
        "evaluation": 5.0,
        "comparison": 0.0,
        "negative_risk": -10.0,
        "brand_direct": 0.0,
        "general": 0.0,
    }
    intent_adj = intent_map.get(query_intent, 0.0)

    # 基础打折系数（头部大幅打折，腰部适度打折，长尾无打折）
    if top_lvl == "头部" or top_share > 15.0:
        base_discount = 0.45 if query_intent == "comparison" else 0.55
        reason = f"受头部竞品【{top_name}】强声量垄断压制，对比与推荐位被稀释"
    elif top_lvl == "腰部" or top_share >= 5.0:
        base_discount = 0.70 if query_intent == "comparison" else 0.80
        reason = f"受腰部同行【{top_name}】分流截流，需补齐差异化证据链"
    else:
        base_discount = 1.0
        reason = "同赛道处于相对真空或长尾分散态，竞对截流阻力较小"

    return {
        "has_competitor": True,
        "top_competitor": top_name,
        "top_level": top_lvl,
        "top_score": top_score,
        "max_market_share": top_share,
        "discount_factor": base_discount,
        "intent_adjustment": intent_adj,
        "suppression_reason": reason,
    }


def simulate_query_visibility_with_feedback(
    project_id: str,
    query: str,
    base_mention_rate: float = 75.0,
    client_geo_score: float = 70.0,
) -> Dict[str, Any]:
    """将竞品反哺联动至单条长问的实际提及率与排名推演中"""
    from .competitor_gap import build_structured_competitor_analysis

    out_dir = os.path.join(_project_dir(project_id), "outputs")
    comp_json = os.path.join(out_dir, "competitor_analysis.json")
    if os.path.exists(comp_json):
        try:
            with open(comp_json, "r", encoding="utf-8") as f:
                comp_data = json.load(f)
        except Exception:
            comp_data = build_structured_competitor_analysis(project_id)
    else:
        comp_data = build_structured_competitor_analysis(project_id)

    competitors = comp_data.get("competitors", [])
    intent = classify_query_intent_for_visibility(query)
    feedback = calculate_competitor_feedback_discount(competitors, intent)

    discount = feedback["discount_factor"]
    intent_adj = feedback["intent_adjustment"]

    # 有效提及率 = 基准提及率 * 打折系数 + 意图修正
    effective_rate = round(max(0.0, min(100.0, (base_mention_rate * discount) + intent_adj)), 1)

    # 预估排名逻辑（如果头部竞品分数明显高于我方，我方在对比题无法进入前 2）
    top_score = feedback.get("top_score", 60.0)
    if feedback["has_competitor"] and feedback["top_level"] == "头部":
        if top_score - client_geo_score >= 15.0:
            simulated_rank = 3
        elif top_score > client_geo_score:
            simulated_rank = 2
        else:
            simulated_rank = 1
    elif feedback["has_competitor"] and feedback["top_level"] == "腰部":
        simulated_rank = 2 if top_score > client_geo_score else 1
    else:
        simulated_rank = 1

    return {
        "query": query,
        "intent": intent,
        "base_mention_rate": base_mention_rate,
        "effective_mention_rate": effective_rate,
        "simulated_rank": simulated_rank,
        "feedback": feedback,
        "suppressed": bool(discount < 1.0),
    }

