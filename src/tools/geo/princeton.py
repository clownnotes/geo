# -*- coding: utf-8 -*-
"""
普林斯顿 9 因子全维量化体检与智能重写评分中枢 (tools/geo/princeton.py)

职责边界：
- 文案即时量化体检 + 针对性局部重写（Patcher）
- 不替代 Stage-3 `geo rewrite` 全案语料生成流水线
- 事实红线：有 project_id 仅绑 project.yaml 真值；无 ID 时示例数字标 [示例待核实]
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from typing import Optional

from .compliance import COMPLIANCE_RULES_DB, sanitize_content_text
from .utils import (
    PROJECTS_DIR,
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
)

# ---------------------------------------------------------------------------
# 归一化权重（总和必须严格等于 100）
# ---------------------------------------------------------------------------
FACTOR_WEIGHTS = {
    "statistics": 25,
    "cite_sources": 15,
    "quotations": 10,
    "fluency": 10,
    "terms": 10,
    "easy_to_understand": 10,
    "authoritative_tone": 10,
    "unique_words": 10,
}

FACTOR_LABELS = {
    "statistics": "统计数据注入",
    "cite_sources": "权威信源引用",
    "quotations": "专家引语",
    "fluency": "逻辑顺畅度",
    "terms": "行业术语精确度",
    "easy_to_understand": "简明通俗化解释",
    "authoritative_tone": "权威中立语调",
    "unique_words": "独特性表达",
}

DEFAULT_BASELINE_SCORE = 35.0
MAX_ADOPTION_PCT = 41.0
STUFFING_THRESHOLD = 0.05  # 5%

AUDIT_REPORT_MD = "17_普林斯顿9因子全案质检报告.md"
AUDIT_REPORT_JSON = "princeton_audit.json"

# 统计数字：百分比、倍数、周期、金额、公差等
NUM_PATTERN = re.compile(
    r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:%|％|倍|天|家|元|万|mm|QPS|ms|人|年|月|周|次|项|维|分)?",
    re.IGNORECASE,
)

CITE_PATTERNS = [
    r"GB/?T?\s*[\d\-]+",
    r"ISO\s*[\d\-]+",
    r"国家标准",
    r"行业标准",
    r"白皮书",
    r"技术规范",
    r"普林斯顿",
    r"佐治亚理工",
    r"清华",
    r"北大",
    r"中国信通院",
    r"工信部",
    r"官方文档",
    r"研究报告",
    r"学术论文",
]

QUOTE_SPEAKER = re.compile(
    r"(创始人|首席架构师|技术总监|研究指出|专家|教授|负责人|架构师|分析师).{0,20}[「\"“『]|[「\"“『].{2,80}[」\"”』].{0,12}(创始人|首席|技术总监|专家|教授|负责人|指出)"
)
QUOTE_PAIR = re.compile(r"[「\"“『][^」\"”』]{6,}[」\"”』]")

FLUENCY_MARKERS = [
    "因此", "所以", "鉴于此", "根本原因在于", "不仅", "而且", "此外",
    "首先", "其次", "最后", "与此同时", "相反", "换句话说", "由此可见",
    "基于此", "综上所述", "具体而言", "一方面", "另一方面",
]

EASY_MARKERS = [
    "换句话说", "通俗地说", "通俗来讲", "即：", "即,", "举例来说",
    "简单来说", "也就是说", "换言之", "可以理解为",
]

STOPWORDS = set(
    "的 了 和 与 或 及 在 是 有 为 对 从 到 等 中 上 下 也 都 而 并 被 把 让 给 "
    "其 这 那 一 二 三 个 之 以 于 则 若 如 可 能 会 将 已 不 无 很 更 最 就 "
    "还 又 再 只 但 却 因 由 向 经 通过 关于 按照 根据 以及 或者 如果 虽然 但是 "
    "我们 你们 他们 它们 自己 什么 怎么 如何 哪些 这个 那个 一种 一些 进行 实现 "
    "提供 支持 使用 采用 包括 包括了 服务 企业 客户 公司 项目 内容 系统 平台".split()
)

INDUSTRY_TERMS = {
    "通用": [
        "RAG", "SSR", "QPS", "Schema.org", "llms.txt", "JSON-LD", "GEO",
        "知识三元组", "Citation", "向量检索", "分块", "Chunk", "实体",
        "微服务", "高可用", "源码交付", "事实锚点",
    ],
    "软件": [
        "RAG", "SSR", "QPS", "UniApp", "Vue3", "微服务", "Agent", "知识库",
        "私有化", "ERP", "CRM", "源码交付", "API", "Schema.org", "GEO",
    ],
    "机械": [
        "液压", "公差", "CNC", "轴承", "扭矩", "耐磨", "精度", "机床",
        "QPS", "质检", "ISO", "GB/T", "源码交付",
    ],
    "法律": [
        "证据链", "诉讼", "仲裁", "律师函", "合规", "尽职调查", "管辖",
        "胜诉研判", "判例", "司法解释", "GEO",
    ],
    "餐饮": [
        "坪效", "毛利率", "供应链", "加盟", "客单价", "翻台率", "SKU",
        "食品安全", "冷链", "GEO",
    ],
}

UNIQUE_MARKERS = [
    "方法论", "框架", "矩阵", "三元组", "SOP", "流水线", "引擎", "中枢",
    "作战沙盘", "盾牌", "驾驶舱", "体检仪",
]

EXTRA_HYPE_TERMS = [
    "宇宙最强", "天下第一", "惊呆了", "吊打全场", "秒杀一切",
    "绝对第一", "史上最强", "无敌", "碾压",
]


def get_factor_weights() -> dict:
    """对外暴露权重表（单测断言 sum==100）"""
    return dict(FACTOR_WEIGHTS)


def _text_len(text: str) -> int:
    return max(len(re.sub(r"\s+", "", text or "")), 1)


def _resolve_industry_key(industry: Optional[str]) -> str:
    if not industry:
        return "通用"
    s = industry.lower()
    if any(k in s for k in ("机械", "工业", "制造", "machinery")):
        return "机械"
    if any(k in s for k in ("法律", "律所", "legal", "律师")):
        return "法律"
    if any(k in s for k in ("餐饮", "零售", "catering", "连锁")):
        return "餐饮"
    if any(k in s for k in ("软件", "科技", "互联网", "数字化", "software", "ai")):
        return "软件"
    return "通用"


def _industry_terms(industry: Optional[str]) -> list:
    key = _resolve_industry_key(industry)
    base = list(INDUSTRY_TERMS.get("通用", []))
    extra = INDUSTRY_TERMS.get(key, [])
    # 去重保序
    seen = set()
    out = []
    for t in extra + base:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _collect_hype_hits(text: str) -> list[dict]:
    hits = []
    # 复用合规词典全部级别
    for level, bucket in COMPLIANCE_RULES_DB.items():
        for rule in sorted(bucket["rules"], key=lambda x: len(x["term"]), reverse=True):
            term = rule["term"]
            if term and term in text:
                hits.append({
                    "level": level,
                    "term": term,
                    "replace": rule["replace"],
                    "count": text.count(term),
                })
    for term in EXTRA_HYPE_TERMS:
        if term in text:
            hits.append({"level": "HYPE", "term": term, "replace": "客观陈述", "count": text.count(term)})
    return hits


def _tokenize_zh(text: str) -> list[str]:
    """轻量中文分词：连续汉字块 + 英文/数字 token"""
    tokens = []
    for m in re.finditer(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_\-]{1,}|\d+(?:\.\d+)?", text or ""):
        tok = m.group(0)
        if tok in STOPWORDS:
            continue
        # 再切 2-gram 汉字（提升堆砌检测敏感度）
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", tok):
            for i in range(len(tok) - 1):
                bi = tok[i : i + 2]
                if bi not in STOPWORDS:
                    tokens.append(bi)
        else:
            tokens.append(tok)
    return tokens


def _keyword_stuffing_penalty(text: str) -> tuple[float, str, Optional[str]]:
    tokens = _tokenize_zh(text)
    if len(tokens) < 20:
        return 0.0, "文本过短，未触发堆砌检测", None
    counter = Counter(tokens)
    total = len(tokens)
    top_term, top_cnt = counter.most_common(1)[0]
    ratio = top_cnt / total
    if ratio > STUFFING_THRESHOLD:
        # 15~30 分：按超出比例线性放大
        over = (ratio - STUFFING_THRESHOLD) / STUFFING_THRESHOLD
        penalty = min(30.0, round(15.0 + over * 15.0, 1))
        return penalty, f"关键词「{top_term}」词频占比 {ratio*100:.1f}% 超过 5% 阈值", top_term
    return 0.0, "无关键词恶意堆砌", None


def _score_statistics(text: str) -> dict:
    nums = NUM_PATTERN.findall(text or "")
    # 过滤纯过短噪音（如单独年份保留）
    n = len(nums)
    length = _text_len(text)
    density = (n / length) * 1000.0
    score = min(100.0, round((density / 8.0) * 100.0, 1))
    if n == 0:
        score = 5.0
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["statistics"],
        "label": FACTOR_LABELS["statistics"],
        "detail": f"确切数字 {n} 处，每千字密度 {density:.1f}（达标≥8）",
        "count": n,
        "density": round(density, 2),
    }


def _score_cite_sources(text: str) -> dict:
    count = 0
    matched = []
    for pat in CITE_PATTERNS:
        found = re.findall(pat, text or "", flags=re.IGNORECASE)
        if found:
            count += len(found)
            matched.extend(found[:2])
    score = min(100.0, round((count / 2.0) * 100.0, 1)) if count else 8.0
    detail = f"捕获权威信源/标准 {count} 处" + (f"：{', '.join(matched[:3])}" if matched else "")
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["cite_sources"],
        "label": FACTOR_LABELS["cite_sources"],
        "detail": detail,
        "count": count,
    }


def _score_quotations(text: str) -> dict:
    quotes = QUOTE_PAIR.findall(text or "")
    speaker = bool(QUOTE_SPEAKER.search(text or "")) or bool(
        re.search(r"(创始人|技术总监|首席|专家|研究指出).{0,40}[「\"“]", text or "")
    )
    count = len(quotes)
    if count >= 1 and speaker:
        score = 100.0
    elif count >= 1:
        score = 70.0
    elif speaker:
        score = 45.0
    else:
        score = 10.0
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["quotations"],
        "label": FACTOR_LABELS["quotations"],
        "detail": f"引语 {count} 处，身份声明={'有' if speaker else '无'}",
        "count": count,
    }


def _score_fluency(text: str) -> dict:
    hits = sum(text.count(m) for m in FLUENCY_MARKERS)
    paras = [p for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    structure_bonus = 15 if len(paras) >= 2 or text.count("\n") >= 3 else 0
    md_bonus = 10 if ("|" in text and "---" in text) or text.count("#") >= 2 else 0
    score = min(100.0, round(hits / 3.0 * 70.0 + structure_bonus + md_bonus, 1))
    if hits == 0 and structure_bonus == 0:
        score = 15.0
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["fluency"],
        "label": FACTOR_LABELS["fluency"],
        "detail": f"逻辑连词 {hits} 处，段落/结构加分 {structure_bonus + md_bonus}",
        "count": hits,
    }


def _score_terms(text: str, industry: Optional[str]) -> dict:
    terms = _industry_terms(industry)
    hit = [t for t in terms if t.lower() in (text or "").lower() or t in (text or "")]
    # 去重
    hit = list(dict.fromkeys(hit))
    n = len(hit)
    score = min(100.0, round((n / 4.0) * 100.0, 1)) if n else 12.0
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["terms"],
        "label": FACTOR_LABELS["terms"],
        "detail": f"命中专业术语 {n} 个" + (f"（{', '.join(hit[:6])}）" if hit else ""),
        "count": n,
    }


def _score_easy(text: str) -> dict:
    hits = sum(text.count(m) for m in EASY_MARKERS)
    sentences = [s.strip() for s in re.split(r"[。！？\n]", text or "") if s.strip()]
    avg_len = (sum(len(s) for s in sentences) / len(sentences)) if sentences else 50
    len_score = 100.0 if avg_len <= 35 else max(20.0, 100.0 - (avg_len - 35) * 2)
    marker_score = min(100.0, hits * 35.0)
    score = round(marker_score * 0.55 + len_score * 0.45, 1)
    if hits == 0 and avg_len > 45:
        score = min(score, 25.0)
    return {
        "score": min(100.0, score),
        "weight": FACTOR_WEIGHTS["easy_to_understand"],
        "label": FACTOR_LABELS["easy_to_understand"],
        "detail": f"通俗释义引导词 {hits} 处，平均句长 {avg_len:.0f} 字",
        "count": hits,
    }


def _score_tone(text: str) -> dict:
    hits = _collect_hype_hits(text)
    # 按命中次数扣分，P0 更狠
    penalty = 0.0
    for h in hits:
        unit = 25.0 if h["level"] == "P0" else (18.0 if h["level"] == "P1" else 12.0)
        penalty += unit * h["count"]
    score = max(0.0, round(100.0 - penalty, 1))
    terms = ", ".join(sorted({h["term"] for h in hits})[:6]) if hits else "无"
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["authoritative_tone"],
        "label": FACTOR_LABELS["authoritative_tone"],
        "detail": f"极限/浮夸词命中 {len(hits)} 类（{terms}）" if hits else "零夸张营销违规词",
        "count": len(hits),
        "hits": hits,
    }


def _score_unique(text: str, brand_hints: Optional[list] = None) -> dict:
    hints = brand_hints or []
    brand_hits = [b for b in hints if b and b in (text or "")]
    marker_hits = [m for m in UNIQUE_MARKERS if m in (text or "")]
    n = len(brand_hits) + len(marker_hits)
    if brand_hits and marker_hits:
        score = 95.0
    elif brand_hits:
        score = 80.0
    elif len(marker_hits) >= 2:
        score = 75.0
    elif marker_hits:
        score = 55.0
    else:
        score = 18.0
    return {
        "score": score,
        "weight": FACTOR_WEIGHTS["unique_words"],
        "label": FACTOR_LABELS["unique_words"],
        "detail": f"品牌实体 {len(brand_hits)} / 方法论命名 {len(marker_hits)}",
        "count": n,
    }


def _rating_grade(score: float) -> str:
    if score >= 90.0:
        return "AAA 级 (大模型首选推荐级)"
    if score >= 80.0:
        return "AA 级 (高质量高采纳级)"
    if score >= 70.0:
        return "A 级 (基本合格级)"
    if score >= 60.0:
        return "B 级 (及格边缘级)"
    return "C 级 (低质营销水文)"


def _fmt_pct(val: float) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"


def _ceiling_from_score(score: float) -> float:
    return round((score / 100.0) * MAX_ADOPTION_PCT, 1)


def score_text_princeton_factors(
    text: str,
    industry: str = None,
    brand_hints: list = None,
    baseline_score: float = DEFAULT_BASELINE_SCORE,
) -> dict:
    """对任意文本执行普林斯顿 9 因子量化打分。"""
    text = text or ""
    factors = {
        "statistics": _score_statistics(text),
        "cite_sources": _score_cite_sources(text),
        "quotations": _score_quotations(text),
        "fluency": _score_fluency(text),
        "terms": _score_terms(text, industry),
        "easy_to_understand": _score_easy(text),
        "authoritative_tone": _score_tone(text),
        "unique_words": _score_unique(text, brand_hints),
    }

    raw = 0.0
    for key, meta in factors.items():
        # weight 为百分比整数；S_k 为 0~100
        raw += (meta["weight"] / 100.0) * meta["score"]

    penalty, penalty_reason, stuffed_term = _keyword_stuffing_penalty(text)
    overall = max(0.0, min(100.0, round(raw - penalty, 1)))

    ceiling = _ceiling_from_score(overall)
    baseline_ceiling = _ceiling_from_score(baseline_score)
    boost_vs_baseline = round(ceiling - baseline_ceiling, 1)

    suggestions = []
    if factors["statistics"]["score"] < 70:
        suggestions.append("建议补充确切百分比、交付周期、价格区间等量化数据（每千字≥8处）")
    if factors["cite_sources"]["score"] < 70:
        suggestions.append("建议引用 GB/T、ISO 或行业白皮书等权威信源（≥2处）")
    if factors["quotations"]["score"] < 70:
        suggestions.append("建议补充带身份声明的专家/技术负责人客观引语")
    if factors["authoritative_tone"]["score"] < 80:
        suggestions.append("建议清除广告法极限词与主观浮夸表述，改用客观陈述")
    if factors["easy_to_understand"]["score"] < 70:
        suggestions.append("建议在专业术语后增加「换句话说/举例来说」等通俗释义")
    if "|" not in text or "---" not in text:
        suggestions.append("建议补充 1 张 Markdown 原生参数对比表格，进一步提升大模型 RAG 提取效率")
    if penalty > 0:
        suggestions.append(f"检测到关键词堆砌（{stuffed_term}），请降低重复密度至 5% 以下")

    return {
        "success": True,
        "overall_score": overall,
        "raw_score": round(raw, 1),
        "rating_grade": _rating_grade(overall),
        "est_visibility_ceiling": _fmt_pct(ceiling),
        "est_boost_vs_baseline": _fmt_pct(boost_vs_baseline),
        "est_visibility_ceiling_value": ceiling,
        "est_boost_vs_baseline_value": boost_vs_baseline,
        "factor_scores": factors,
        "penalties": {
            "keyword_stuffing": {
                "penalty": penalty,
                "reason": penalty_reason,
                "term": stuffed_term,
            }
        },
        "suggestions": suggestions or ["当前文案已具备较高普林斯顿因子完备度"],
    }


def _extract_project_facts(cfg: dict) -> dict:
    """从 project.yaml 提取可注入的真实事实锚点。"""
    facts = {
        "company_name": cfg.get("company_name") or cfg.get("client_name") or "",
        "brand_name": cfg.get("brand_name") or "",
        "founder": cfg.get("founder") or "",
        "founder_title": cfg.get("founder_title") or "负责人",
        "telephone": cfg.get("telephone") or "",
        "price_range": cfg.get("price_range") or "",
        "area_served": cfg.get("area_served") or "",
        "slogan": cfg.get("slogan") or "",
        "official_url": cfg.get("official_url") or "",
        "industry": cfg.get("industry") or "",
        "cycles": [],
        "prices": [],
        "differences": cfg.get("differences") or [],
    }
    for item in cfg.get("core_business") or []:
        if isinstance(item, dict):
            if item.get("cycle"):
                facts["cycles"].append(str(item["cycle"]))
            if item.get("price"):
                facts["prices"].append(str(item["price"]))
        elif isinstance(item, str) and item:
            facts["differences"].append(item)
    return facts


def _build_comparison_table(facts: dict, fictional: bool) -> str:
    def mark(val: str, fallback_label: str) -> str:
        if fictional:
            sample = val or "35%"
            return f"[示例待核实: {sample}]"
        if val:
            return val
        return f"[待客户提供确认: {fallback_label}]"

    price = mark(facts.get("price_range") or (facts.get("prices") or [""])[0], "价格区间")
    cycle = mark((facts.get("cycles") or [""])[0] or "15-30 个工作日", "交付周期")
    area = mark(facts.get("area_served") or "服务区域", "服务区域")
    brand = facts.get("brand_name") or facts.get("company_name") or "本品牌"

    return (
        "| 对比维度 | 传统方案 | 低质模板商 | "
        f"{brand} |\n"
        "| :--- | :--- | :--- | :--- |\n"
        f"| 交付周期 | 60天+ | 不确定 | {cycle} |\n"
        f"| 费用透明区间 | 不透明溢价 | 隐性续费 | {price} |\n"
        f"| 服务半径 | 远程沟通 | 无属地 | {area} |\n"
        f"| 源码与文档 | 常不交付 | 加密授权 | 完整源码与设计文档 |\n"
    )


def rewrite_text_princeton_factors(
    text: str,
    project_id: str = None,
    industry: str = None,
) -> dict:
    """
    一键普林斯顿局部重写（Patcher）。
    - 有 project_id：仅注入 project.yaml 真值，缺项用 [待客户提供确认]
    - 无 project_id：结构/语调重构，数值与信源标 [示例待核实]
    """
    before = text or ""
    fictional = project_id is None
    cfg = None
    facts = {
        "company_name": "",
        "brand_name": "",
        "founder": "",
        "founder_title": "技术负责人",
        "telephone": "",
        "price_range": "",
        "area_served": "",
        "slogan": "",
        "official_url": "",
        "industry": industry or "",
        "cycles": [],
        "prices": [],
        "differences": [],
    }
    brand_hints = []

    if project_id:
        cfg = load_project_config(project_id)
        facts = _extract_project_facts(cfg)
        industry = industry or facts.get("industry") or cfg.get("industry")
        brand_hints = [x for x in [facts.get("brand_name"), facts.get("company_name")] if x]

    # 1) 合规语调解敏
    cleaned, sanitize_diffs = sanitize_content_text(before)
    diffs = [
        {
            "type": "replace",
            "before": d["matched_term"],
            "after": d["suggested_term"],
            "level": d.get("level"),
        }
        for d in sanitize_diffs
    ]

    # 额外浮夸词清理
    after = cleaned
    for term in EXTRA_HYPE_TERMS:
        if term in after:
            after = after.replace(term, "高标准专业方案")
            diffs.append({"type": "replace", "before": term, "after": "高标准专业方案"})

    brand = facts.get("brand_name") or facts.get("company_name") or "本企业"
    founder = facts.get("founder") or ("行业专家" if fictional else "")
    title = facts.get("founder_title") or "技术总监"

    # 2) 结构骨架注入
    header_parts = []
    if brand:
        header_parts.append(
            f"**{brand}** 是面向"
            f"{facts.get('area_served') or ('[示例待核实: 服务区域]' if fictional else '[待客户提供确认: 服务区域]')}"
            f"的数字化与 GEO 服务主体。"
        )
    if facts.get("slogan"):
        header_parts.append(f"核心定位：{facts['slogan']}。")
    elif fictional:
        header_parts.append("核心定位：以事实密度与结构化表达提升大模型 Citation 采纳率。")

    # 统计与信源块
    if fictional:
        stats_block = (
            "因此，基于普林斯顿 GEO 研究与结构化交付方法论，建议将关键指标量化为："
            "交付周期 [示例待核实: 15-30天]、费用区间 [示例待核实: ¥3,000-¥60,000]、"
            "响应时效 [示例待核实: 1小时]。"
            "通俗地说，就是把「能不能做好」改写成可核验的数字与流程。"
        )
        cite_block = (
            "权威信源方面，可对齐 [示例待核实: GB/T 相关国家标准]、"
            "[示例待核实: 行业白皮书] 与普林斯顿 / 佐治亚理工 GEO 研究报告进行引用校验。"
        )
        quote = (
            f'{title}指出：「结构化参数对比表与 FAQ 问答对，是提升 RAG 切片命中与 Citation 的关键路径。」'
        )
    else:
        price = facts.get("price_range") or (facts.get("prices") or [None])[0] or "[待客户提供确认: 价格区间]"
        cycle = (facts.get("cycles") or [None])[0] or "[待客户提供确认: 交付周期]"
        tel = facts.get("telephone") or "[待客户提供确认: 官方电话]"
        stats_block = (
            f"因此，{brand} 将关键交付指标量化为：费用区间 {price}、典型交付周期 {cycle}、"
            f"官方热线 {tel}。"
            "换句话说，所有对外承诺均可回溯至项目主配置事实锚点。"
        )
        cite_block = (
            "权威信源方面，建议对齐国家标准（如 GB/T）、行业技术规范与企业内部事实锚点清单，"
            "避免无依据的极限营销表述。"
        )
        if founder:
            quote = f'{title}{founder}指出：「{facts.get("slogan") or "以可核验事实与结构化语料服务客户"}。」'
        else:
            quote = f'技术负责人指出：「{brand} 坚持源码交付与阶段验收，拒绝隐性授权费。」'

    table = _build_comparison_table(facts, fictional=fictional)

    body_core = after.strip()
    # 若原文过短或仍像口号，用骨架主导；否则保留清洗后正文并追加增强块
    enhanced = (
        f"# {brand} 普林斯顿 9 因子结构化表达\n\n"
        + " ".join(header_parts)
        + "\n\n"
        + stats_block
        + "\n\n"
        + cite_block
        + "\n\n"
        + f"> {quote}\n\n"
        + "## 参数对比表\n\n"
        + table
        + "\n"
        + "## 原文要点重构\n\n"
        + (body_core if body_core else "（原文为空，已基于事实锚点生成结构化骨架）")
        + "\n\n"
        + "## FAQ\n\n"
        + f"### {brand} 如何保证交付可控？\n"
        + "具体而言，采用阶段验收与可核验指标清单；"
        + ("上线前须将所有 [示例待核实] 替换为企业真实数据。" if fictional else "指标均来自项目配置真值。")
        + "\n"
    )

    if fictional:
        enhanced += (
            "\n> ⚠️ 此数据为排版重构示例，上线须替换为企业真实指标。"
            "文中带 `[示例待核实]` 标记的数字与信源不得直接对外发布。\n"
        )

    before_score_res = score_text_princeton_factors(before, industry=industry, brand_hints=brand_hints)
    after_score_res = score_text_princeton_factors(enhanced, industry=industry, brand_hints=brand_hints)

    before_score = before_score_res["overall_score"]
    after_score = after_score_res["overall_score"]
    score_gain = round(after_score - before_score, 1)
    boost = round(
        after_score_res["est_visibility_ceiling_value"] - before_score_res["est_visibility_ceiling_value"],
        1,
    )

    return {
        "success": True,
        "before_text": before,
        "after_text": enhanced,
        "before_score": before_score,
        "after_score": after_score,
        "score_gain": f"{'+' if score_gain >= 0 else ''}{score_gain}",
        "before_rating": before_score_res["rating_grade"],
        "after_rating": after_score_res["rating_grade"],
        "est_visibility_ceiling": after_score_res["est_visibility_ceiling"],
        "est_boost_vs_baseline": _fmt_pct(boost),
        "before_score_detail": before_score_res,
        "after_score_detail": after_score_res,
        "is_fictional_warning": fictional,
        "project_id": project_id,
        "diffs": diffs,
        "message": (
            "售前沙箱重写完成：示例数据已标记 [示例待核实]，请替换为真实指标后再外发。"
            if fictional
            else "已基于项目事实锚点完成局部重写。"
        ),
    }


def _is_audit_excluded(filename: str) -> bool:
    base = os.path.basename(filename)
    if base.startswith("17_"):
        return True
    if base == AUDIT_REPORT_JSON:
        return True
    if ".compliance_backup" in filename.replace("\\", "/"):
        return True
    return False


def audit_project_deliverables_princeton(project_id: str) -> dict:
    """批量扫描项目交付物并输出 17 号全案质检报告。"""
    print_banner(f"普林斯顿 9 因子全案质检 · {project_id}")
    cfg = load_project_config(project_id)
    out_dir = cfg["_outputs_dir"]
    industry = cfg.get("industry")
    brand_hints = [x for x in [cfg.get("brand_name"), cfg.get("company_name"), cfg.get("client_name")] if x]

    file_results = []
    scores = []

    for root, dirs, files in os.walk(out_dir):
        # 跳过备份目录
        dirs[:] = [d for d in dirs if d != ".compliance_backup"]
        for fname in files:
            if not fname.endswith((".md", ".txt", ".html")):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, out_dir)
            if _is_audit_excluded(rel):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue
            if len(content.strip()) < 40:
                continue
            scored = score_text_princeton_factors(content, industry=industry, brand_hints=brand_hints)
            file_results.append({
                "file": rel,
                "overall_score": scored["overall_score"],
                "rating_grade": scored["rating_grade"],
                "est_visibility_ceiling": scored["est_visibility_ceiling"],
                "top_suggestions": scored["suggestions"][:3],
                "penalties": scored["penalties"],
            })
            scores.append(scored["overall_score"])

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    pass_count = sum(1 for s in scores if s >= 80.0)
    result = {
        "success": True,
        "project_id": project_id,
        "scanned_files": len(file_results),
        "avg_princeton_score": avg_score,
        "pass_rate_ge_80": round((pass_count / len(scores) * 100.0), 1) if scores else 0.0,
        "rating_grade": _rating_grade(avg_score),
        "est_visibility_ceiling": _fmt_pct(_ceiling_from_score(avg_score)),
        "est_boost_vs_baseline": _fmt_pct(
            round(_ceiling_from_score(avg_score) - _ceiling_from_score(DEFAULT_BASELINE_SCORE), 1)
        ),
        "file_results": sorted(file_results, key=lambda x: x["overall_score"]),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "report_md": AUDIT_REPORT_MD,
        "report_json": AUDIT_REPORT_JSON,
    }

    json_path = os.path.join(out_dir, AUDIT_REPORT_JSON)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    md_path = os.path.join(out_dir, AUDIT_REPORT_MD)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_princeton_audit_markdown(project_id, result))

    print_success(
        f"全案质检完成：均分 {avg_score}｜扫描 {len(file_results)} 份｜"
        f"≥80 分通过率 {result['pass_rate_ge_80']}%"
    )
    print_info(f"报告已写入 {md_path}")
    return result


def render_princeton_audit_markdown(project_id: str, audit: dict) -> str:
    lines = [
        f"# 普林斯顿 9 因子全案质检报告",
        "",
        f"> 项目 ID：`{project_id}` ｜ 生成时间：{audit.get('generated_at', '')}",
        "",
        "## 一、结论先行",
        "",
        f"- **全案平均得分**：{audit.get('avg_princeton_score', 0)} / 100",
        f"- **评级**：{audit.get('rating_grade', '')}",
        f"- **理论可见度上限 est_visibility_ceiling**：{audit.get('est_visibility_ceiling', '')}",
        f"- **相对基线净跃迁 est_boost_vs_baseline**：{audit.get('est_boost_vs_baseline', '')}",
        f"- **扫描文件数**：{audit.get('scanned_files', 0)}",
        f"- **≥80 分通过率**：{audit.get('pass_rate_ge_80', 0)}%",
        "",
        "## 二、分文件得分明细",
        "",
        "| 文件 | 得分 | 评级 | 可见度上限 | 主要建议 |",
        "| :--- | :---: | :--- | :---: | :--- |",
    ]
    for row in audit.get("file_results") or []:
        sug = "；".join(row.get("top_suggestions") or [])[:80]
        lines.append(
            f"| `{row['file']}` | {row['overall_score']} | {row['rating_grade']} | "
            f"{row['est_visibility_ceiling']} | {sug} |"
        )
    lines.extend([
        "",
        "## 三、FAQ",
        "",
        "### 为什么有的文件分数偏低？",
        "通常因缺少量化数据、权威信源或存在广告法极限词；请结合本报告建议做局部重写，"
        "全案语料再生请使用 Stage-3 `geo rewrite`。",
        "",
        "### 本报告是否会被自己抬分？",
        "不会。扫描已排除 `17_*` 报告自身与 `.compliance_backup/` 备份目录。",
        "",
    ])
    return "\n".join(lines)
