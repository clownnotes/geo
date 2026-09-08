#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯一真相源（Canonical Fact Ledger）与证据库辅助模块。
L1 evidence/ 多来源并存；L2 ledger/facts.jsonl 为 SSOT；兼容镜像 raw_extracted_facts.md。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

STANDARD_FACT_KEYS = {
    "entity.legal_name": "实体",
    "entity.brand_name": "实体",
    "entity.official_url": "实体",
    "entity.founder": "实体",
    "business.industry": "业务",
    "business.core_scope": "业务",
    "service.area": "服务",
    "metric.delivery_days": "量化指标",
    "metric.price_range": "量化指标",
    "policy.warranty_days": "承诺",
    "policy.source_code_delivery": "承诺",
    "contact.telephone": "联络",
}

ALIAS_TO_STANDARD = {
    "company_name": "entity.legal_name",
    "legal_entity": "entity.legal_name",
    "legal_name": "entity.legal_name",
    "brand": "entity.brand_name",
    "brand_alias": "entity.brand_name",
    "brand_name": "entity.brand_name",
    "website": "entity.official_url",
    "homepage": "entity.official_url",
    "official_site": "entity.official_url",
    "official_url": "entity.official_url",
    "ceo": "entity.founder",
    "founder_name": "entity.founder",
    "founder": "entity.founder",
    "industry": "business.industry",
    "sector": "business.industry",
    "core_business": "business.core_scope",
    "scope": "business.core_scope",
    "services": "business.core_scope",
    "core_scope": "business.core_scope",
    "area_served": "service.area",
    "region": "service.area",
    "coverage": "service.area",
    "service_area": "service.area",
    "delivery_time": "metric.delivery_days",
    "delivery_cycle_days": "metric.delivery_days",
    "sla_days": "metric.delivery_days",
    "delivery_days": "metric.delivery_days",
    "price": "metric.price_range",
    "fee_range": "metric.price_range",
    "cost": "metric.price_range",
    "price_range": "metric.price_range",
    "warranty": "policy.warranty_days",
    "guarantee_days": "policy.warranty_days",
    "warranty_days": "policy.warranty_days",
    "source_delivery": "policy.source_code_delivery",
    "code_handover": "policy.source_code_delivery",
    "source_code_delivery": "policy.source_code_delivery",
    "phone": "contact.telephone",
    "hotline": "contact.telephone",
    "tel": "contact.telephone",
    "telephone": "contact.telephone",
}

AUTO_CONFIRM_KEYS = {"entity.official_url"}

STATUS_PROPOSED = "proposed"
STATUS_CONFIRMED = "confirmed"
STATUS_CONFLICT = "conflict"
STATUS_REJECTED = "rejected"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_fact_key(raw_key: str) -> str:
    """将别名或自由键归一到标准 fact_key。"""
    if not raw_key:
        return "custom.unknown"
    key = raw_key.strip().lower().replace(" ", "_").replace("-", "_")
    key = re.sub(r"[^a-z0-9_./]", "", key)
    if key in STANDARD_FACT_KEYS:
        return key
    bare = key.split(".")[-1] if "." in key else key
    if key in ALIAS_TO_STANDARD:
        return ALIAS_TO_STANDARD[key]
    if bare in ALIAS_TO_STANDARD:
        return ALIAS_TO_STANDARD[bare]
    if key.startswith("custom.") and len(bare) > 0:
        return key
    if "." in key and key.split(".")[0] in ("entity", "business", "service", "metric", "policy", "contact") and len(bare) > 0:
        return key
    if not bare:
        digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:8]
        return f"custom.fact_{digest}"
    return f"custom.{bare}"


def source_id_for_url(url: str) -> str:
    normalized = (url or "").strip()
    if not normalized.startswith(("http://", "https://")):
        normalized = "https://" + normalized
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
    return f"url:{digest}"


def source_id_for_paste(filename: str) -> str:
    safe = os.path.basename((filename or "custom_material.md").strip()) or "custom_material.md"
    safe = re.sub(r"[^\w.\-]+", "_", safe)
    if not safe.endswith((".md", ".txt")):
        safe += ".md"
    stem = os.path.splitext(safe)[0]
    return f"paste:{stem}"


def evidence_filename_for_source(source_id: str) -> str:
    if source_id.startswith("url:"):
        return f"url_{source_id.split(':', 1)[1]}.md"
    if source_id.startswith("paste:"):
        return f"paste_{source_id.split(':', 1)[1]}.md"
    digest = hashlib.sha1(source_id.encode("utf-8")).hexdigest()[:12]
    return f"src_{digest}.md"


def raw_paths(cfg: dict) -> dict:
    raw_dir = cfg["_raw_materials_dir"]
    evidence_dir = os.path.join(raw_dir, "evidence")
    ledger_dir = os.path.join(raw_dir, "ledger")
    return {
        "raw_dir": raw_dir,
        "evidence_dir": evidence_dir,
        "ledger_dir": ledger_dir,
        "index_path": os.path.join(evidence_dir, "index.json"),
        "facts_jsonl": os.path.join(ledger_dir, "facts.jsonl"),
        "facts_md": os.path.join(ledger_dir, "facts.md"),
        "compat_md": os.path.join(raw_dir, "raw_extracted_facts.md"),
    }


def ensure_dirs(cfg: dict) -> dict:
    paths = raw_paths(cfg)
    os.makedirs(paths["evidence_dir"], exist_ok=True)
    os.makedirs(paths["ledger_dir"], exist_ok=True)
    return paths


def load_evidence_index(cfg: dict) -> list:
    paths = ensure_dirs(cfg)
    if not os.path.exists(paths["index_path"]):
        return []
    try:
        with open(paths["index_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_evidence_index(cfg: dict, index: list) -> None:
    paths = ensure_dirs(cfg)
    with open(paths["index_path"], "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def upsert_evidence(
    cfg: dict,
    source_id: str,
    content: str,
    *,
    kind: str,
    url: str = None,
    title: str = None,
) -> dict:
    """写入/覆盖单来源证据，更新 index。"""
    paths = ensure_dirs(cfg)
    fname = evidence_filename_for_source(source_id)
    abs_path = os.path.join(paths["evidence_dir"], fname)
    text = (content or "").strip()
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(text)

    if not title:
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else source_id

    entry = {
        "source_id": source_id,
        "kind": kind,
        "url": url,
        "title": title,
        "path": f"evidence/{fname}",
        "chars": len(text),
        "fetched_at": _now_iso(),
    }
    index = [e for e in load_evidence_index(cfg) if e.get("source_id") != source_id]
    index.append(entry)
    index.sort(key=lambda x: x.get("fetched_at") or "", reverse=True)
    save_evidence_index(cfg, index)
    return entry


def delete_evidence(cfg: dict, source_id: str) -> bool:
    paths = ensure_dirs(cfg)
    index = load_evidence_index(cfg)
    target = next((e for e in index if e.get("source_id") == source_id), None)
    if not target:
        return False
    abs_path = os.path.join(paths["raw_dir"], target.get("path") or "")
    if os.path.isfile(abs_path):
        os.remove(abs_path)
    save_evidence_index(cfg, [e for e in index if e.get("source_id") != source_id])
    return True


def list_evidence(cfg: dict) -> list:
    return load_evidence_index(cfg)


def read_evidence_body(cfg: dict, source_id: str) -> Optional[str]:
    paths = ensure_dirs(cfg)
    index = load_evidence_index(cfg)
    target = next((e for e in index if e.get("source_id") == source_id), None)
    if not target:
        return None
    abs_path = os.path.join(paths["raw_dir"], target.get("path") or "")
    if not os.path.isfile(abs_path):
        return None
    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_facts(cfg: dict) -> list:
    paths = ensure_dirs(cfg)
    if not os.path.exists(paths["facts_jsonl"]):
        return []
    facts = []
    with open(paths["facts_jsonl"], "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                facts.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return facts


def save_facts(cfg: dict, facts: list) -> None:
    paths = ensure_dirs(cfg)
    with open(paths["facts_jsonl"], "w", encoding="utf-8") as f:
        for fact in facts:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")
    md = render_facts_md(facts, cfg)
    with open(paths["facts_md"], "w", encoding="utf-8") as f:
        f.write(md)
    with open(paths["compat_md"], "w", encoding="utf-8") as f:
        f.write(md)


def render_facts_md(facts: list, cfg: dict = None) -> str:
    company = ""
    if cfg:
        company = cfg.get("company_name") or cfg.get("client_name") or ""
    title = f"{company} 核心知识事实三元组清单" if company else "核心知识事实三元组清单"
    lines = [
        f"# {title} (Fact Ledger)",
        "",
        f"> 更新时间: {_now_iso()} ｜ 条目数: {len(facts)} ｜ SSOT: ledger/facts.jsonl",
        "",
    ]
    if not facts:
        lines.append("- （暂无事实条目）")
        return "\n".join(lines) + "\n"

    order = {STATUS_CONFLICT: 0, STATUS_PROPOSED: 1, STATUS_CONFIRMED: 2, STATUS_REJECTED: 3}
    sorted_facts = sorted(facts, key=lambda x: (order.get(x.get("status"), 9), x.get("fact_key") or ""))
    for fact in sorted_facts:
        status = fact.get("status", STATUS_PROPOSED)
        category = fact.get("category") or STANDARD_FACT_KEYS.get(fact.get("fact_key"), "事实")
        statement = fact.get("statement") or ""
        key = fact.get("fact_key") or "custom.unknown"
        src_n = len(fact.get("sources") or [])
        lines.append(f"- **[{category}] [{status}] `{key}`**：{statement} （来源 {src_n}）")
        if status == STATUS_CONFLICT and fact.get("candidates"):
            for c in fact["candidates"]:
                lines.append(f"  - 候选: {c.get('value')} — {c.get('statement', '')}")
    return "\n".join(lines) + "\n"


def _norm_value(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _values_equal(a: Any, b: Any) -> bool:
    return _norm_value(a).lower() == _norm_value(b).lower()


def merge_fact_proposals(
    cfg: dict,
    proposals: list,
    source_id: str,
    fetched_at: str = None,
) -> dict:
    """
    将提案事实合并进 ledger。
    proposals: [{fact_key, category?, statement, value?, unit?, excerpt?}, ...]
    """
    ensure_dirs(cfg)
    facts = load_facts(cfg)
    by_key = {f.get("fact_key"): f for f in facts if f.get("fact_key")}
    fetched_at = fetched_at or _now_iso()

    stats = {"added": 0, "updated": 0, "conflicts": 0, "unchanged": 0}

    for prop in proposals or []:
        key = normalize_fact_key(prop.get("fact_key") or "")
        statement = (prop.get("statement") or "").strip()
        value = prop.get("value")
        if value is None or str(value).strip() == "":
            value = statement
        value = _norm_value(value)
        if not statement and not value:
            continue

        source_ref = {
            "source_id": source_id,
            "excerpt": (prop.get("excerpt") or statement or value)[:240],
            "fetched_at": fetched_at,
        }
        category = prop.get("category") or STANDARD_FACT_KEYS.get(key, "事实")
        unit = prop.get("unit") or ""

        existing = by_key.get(key)
        if not existing:
            status = STATUS_CONFIRMED if key in AUTO_CONFIRM_KEYS else STATUS_PROPOSED
            entry = {
                "fact_key": key,
                "category": category,
                "statement": statement or value,
                "value": value,
                "unit": unit,
                "status": status,
                "sources": [source_ref],
                "candidates": [],
                "confirmed_snapshot": None,
                "updated_at": fetched_at,
            }
            by_key[key] = entry
            stats["added"] += 1
            continue

        # attach source if new
        sources = existing.get("sources") or []
        if not any(s.get("source_id") == source_id for s in sources):
            sources.append(source_ref)
            existing["sources"] = sources

        if _values_equal(existing.get("value"), value) or _values_equal(existing.get("statement"), statement):
            existing["updated_at"] = fetched_at
            if existing.get("status") == STATUS_CONFLICT:
                pass
            stats["unchanged"] += 1
            continue

        # value differs
        if existing.get("status") == STATUS_CONFIRMED:
            # keep confirmed as snapshot, enter conflict
            existing["confirmed_snapshot"] = {
                "value": existing.get("value"),
                "statement": existing.get("statement"),
            }
            candidates = existing.get("candidates") or []
            candidates.append({
                "value": value,
                "statement": statement or value,
                "source_id": source_id,
                "fetched_at": fetched_at,
            })
            existing["candidates"] = candidates
            existing["status"] = STATUS_CONFLICT
            existing["updated_at"] = fetched_at
            stats["conflicts"] += 1
        elif existing.get("status") == STATUS_CONFLICT:
            candidates = existing.get("candidates") or []
            if not any(_values_equal(c.get("value"), value) for c in candidates):
                candidates.append({
                    "value": value,
                    "statement": statement or value,
                    "source_id": source_id,
                    "fetched_at": fetched_at,
                })
                existing["candidates"] = candidates
            existing["updated_at"] = fetched_at
            stats["conflicts"] += 1
        else:
            # proposed: update to newer proposal
            existing["statement"] = statement or value
            existing["value"] = value
            existing["unit"] = unit or existing.get("unit") or ""
            existing["category"] = category
            existing["updated_at"] = fetched_at
            stats["updated"] += 1

    merged = list(by_key.values())
    save_facts(cfg, merged)
    return stats


def confirm_fact(cfg: dict, fact_key: str) -> dict:
    key = normalize_fact_key(fact_key)
    facts = load_facts(cfg)
    found = False
    for fact in facts:
        if fact.get("fact_key") != key:
            continue
        found = True
        if fact.get("status") == STATUS_CONFLICT:
            return {"success": False, "message": f"`{key}` 处于冲突状态，请先仲裁"}
        fact["status"] = STATUS_CONFIRMED
        fact["confirmed_snapshot"] = {
            "value": fact.get("value"),
            "statement": fact.get("statement"),
        }
        fact["candidates"] = []
        fact["updated_at"] = _now_iso()
        break
    if not found:
        return {"success": False, "message": f"未找到事实键 `{key}`"}
    save_facts(cfg, facts)
    return {"success": True, "fact_key": key, "status": STATUS_CONFIRMED}


def confirm_all_non_conflict(cfg: dict) -> dict:
    """兼容旧调用：默认开启语义预检。"""
    return confirm_all_with_semantic_precheck(cfg, semantic=True)


def _fact_label(fact: dict) -> str:
    return (fact.get("statement") or fact.get("value") or "").strip()


def _rule_based_semantic_pairs(facts: list) -> list:
    """
    轻量规则预检（不依赖 LLM）：同键已在 merge 处理；此处抓跨键明显互斥。
    返回 [{key_a, key_b, reason, statement_a, statement_b}, ...]
    """
    by_key = {f.get("fact_key"): f for f in facts if f.get("fact_key")}
    pairs = []

    def add(ka, kb, reason):
        if ka not in by_key or kb not in by_key:
            return
        if by_key[ka].get("status") == STATUS_REJECTED or by_key[kb].get("status") == STATUS_REJECTED:
            return
        pairs.append({
            "key_a": ka,
            "key_b": kb,
            "reason": reason,
            "statement_a": _fact_label(by_key[ka]),
            "statement_b": _fact_label(by_key[kb]),
        })

    price = _fact_label(by_key.get("metric.price_range") or {})
    delivery = _fact_label(by_key.get("metric.delivery_days") or {})
    area = _fact_label(by_key.get("service.area") or {})
    code = _fact_label(by_key.get("policy.source_code_delivery") or {})

    free_pat = re.compile(r"(免费|0\s*元|零费用|不要钱)")
    paid_pat = re.compile(r"(收费|付费|\d+\s*元|万元|报价|套餐价)")
    if free_pat.search(price) and paid_pat.search(price):
        add("metric.price_range", "metric.price_range", "同一价格事实同时含免费与收费表述")
    if free_pat.search(price) and paid_pat.search(delivery):
        add("metric.price_range", "metric.delivery_days", "价格宣称免费但交付/周期文案含收费口径")
    if re.search(r"不提供|不交付|不给源码|闭源", code) and re.search(r"交付源码|提供源码|开源|附源码", code + " " + delivery):
        add("policy.source_code_delivery", "metric.delivery_days", "源码交付承诺与否定表述并存")

    # 服务区域互斥词（简化）
    exclusive = [("仅限徐州", "全国"), ("仅徐州", "全国"), ("本地专属", "全国")]
    for a, b in exclusive:
        if a in area and b in area:
            add("service.area", "service.area", f"服务区域同时出现互斥口径「{a}」与「{b}」")

    # 同 category 多条 proposed：数值明显不同（抽取数字集合不相交）
    proposed = [f for f in facts if f.get("status") == STATUS_PROPOSED]
    for i, fa in enumerate(proposed):
        for fb in proposed[i + 1 :]:
            if (fa.get("category") or "") != (fb.get("category") or ""):
                continue
            if fa.get("fact_key") == fb.get("fact_key"):
                continue
            sa, sb = _fact_label(fa), _fact_label(fb)
            nums_a = set(re.findall(r"\d+(?:\.\d+)?", sa))
            nums_b = set(re.findall(r"\d+(?:\.\d+)?", sb))
            if nums_a and nums_b and nums_a.isdisjoint(nums_b) and len(sa) < 80 and len(sb) < 80:
                # 同类别且数字完全无交集，提示人工（例如两个不同交付天数键）
                if (fa.get("category") or "") == "量化指标":
                    pairs.append({
                        "key_a": fa.get("fact_key"),
                        "key_b": fb.get("fact_key"),
                        "reason": "同属量化指标但数字口径互不重叠，可能互相矛盾",
                        "statement_a": sa,
                        "statement_b": sb,
                    })

    # 去重
    seen = set()
    out = []
    for p in pairs:
        k = tuple(sorted([p["key_a"], p["key_b"]])) + (p["reason"],)
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def _llm_semantic_conflict_pairs(facts: list) -> list:
    """调用 Nextdoor/LLM 做跨事实语义冲突扫描；失败则返回空列表。"""
    from .utils import call_llm_api, get_configured_llm

    if not get_configured_llm():
        return []
    active = [
        f for f in facts
        if f.get("status") in (STATUS_PROPOSED, STATUS_CONFIRMED) and _fact_label(f)
    ]
    if len(active) < 2:
        return []
    lines = []
    for f in active[:40]:
        lines.append(f"- key={f.get('fact_key')} status={f.get('status')} | {_fact_label(f)[:160]}")
    system = (
        "你是 GEO 事实一致性审核员。只找出互相矛盾、无法同时成立的事实对。"
        "忽略单纯互补信息。输出 JSON 数组，每项："
        '{"key_a":"...","key_b":"...","reason":"一句话中文原因"}。'
        "无冲突输出 []。不要 Markdown。"
    )
    user = "事实清单：\n" + "\n".join(lines) + "\n\n请输出冲突对 JSON 数组："
    ok, text, _ = call_llm_api(user, system, timeout=45)
    if not ok or not text:
        return []
    m = re.search(r"\[[\s\S]*\]", text.strip())
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    by_key = {f.get("fact_key"): f for f in active}
    for item in arr if isinstance(arr, list) else []:
        if not isinstance(item, dict):
            continue
        ka = normalize_fact_key(item.get("key_a") or "")
        kb = normalize_fact_key(item.get("key_b") or "")
        if ka not in by_key or kb not in by_key:
            continue
        out.append({
            "key_a": ka,
            "key_b": kb,
            "reason": (item.get("reason") or "语义冲突").strip()[:200],
            "statement_a": _fact_label(by_key[ka]),
            "statement_b": _fact_label(by_key[kb]),
        })
    return out


def _apply_cross_conflict(facts: list, pair: dict) -> bool:
    """将冲突对中涉及的 proposed（及双确认互斥）标为 conflict。返回是否改动。"""
    by_key = {f.get("fact_key"): f for f in facts}
    ka, kb = pair.get("key_a"), pair.get("key_b")
    fa, fb = by_key.get(ka), by_key.get(kb)
    if not fa or not fb:
        return False

    reason = pair.get("reason") or "语义冲突"
    now = _now_iso()
    changed = False

    def bump(target, other, other_key: str):
        nonlocal changed
        if target.get("status") == STATUS_REJECTED:
            return
        # 提案：必须标冲突；已确认仅当对方也是已确认（双确认互斥）时才降级
        if target.get("status") == STATUS_CONFIRMED and other.get("status") != STATUS_CONFIRMED:
            return
        cand = {
            "value": _fact_label(other),
            "statement": f"[语义冲突↔{other_key}] {reason}｜对方：{_fact_label(other)[:120]}",
            "source_id": "semantic_precheck",
            "fetched_at": now,
        }
        cands = target.get("candidates") or []
        if not any((c.get("statement") or "") == cand["statement"] for c in cands):
            cands.append(cand)
            target["candidates"] = cands
            changed = True
        if target.get("status") != STATUS_CONFLICT:
            if target.get("status") == STATUS_CONFIRMED:
                target["confirmed_snapshot"] = {
                    "value": target.get("value"),
                    "statement": target.get("statement"),
                }
            target["status"] = STATUS_CONFLICT
            target["updated_at"] = now
            changed = True

    if ka == kb:
        # 单条事实内部互斥（如价格同时写免费与收费）
        if fa.get("status") == STATUS_PROPOSED or fa.get("status") == STATUS_CONFIRMED:
            cand = {
                "value": _fact_label(fa),
                "statement": f"[语义自检] {reason}",
                "source_id": "semantic_precheck",
                "fetched_at": now,
            }
            cands = fa.get("candidates") or []
            if not any((c.get("statement") or "") == cand["statement"] for c in cands):
                cands.append(cand)
                fa["candidates"] = cands
                changed = True
            if fa.get("status") != STATUS_CONFLICT:
                if fa.get("status") == STATUS_CONFIRMED:
                    fa["confirmed_snapshot"] = {
                        "value": fa.get("value"),
                        "statement": fa.get("statement"),
                    }
                fa["status"] = STATUS_CONFLICT
                fa["updated_at"] = now
                changed = True
        return changed

    bump(fa, fb, kb)
    bump(fb, fa, ka)
    return changed


def scan_and_flag_semantic_conflicts(cfg: dict, use_llm: bool = True) -> dict:
    """规则 + 可选 LLM 预检，把冲突提案标为 conflict。"""
    ensure_dirs(cfg)
    facts = load_facts(cfg)
    pairs = _rule_based_semantic_pairs(facts)
    llm_pairs = []
    if use_llm:
        try:
            llm_pairs = _llm_semantic_conflict_pairs(facts)
        except Exception:
            llm_pairs = []
    # merge pairs
    all_pairs = []
    seen = set()
    for p in pairs + llm_pairs:
        k = tuple(sorted([p["key_a"], p["key_b"]]))
        if k in seen:
            continue
        seen.add(k)
        all_pairs.append(p)

    flagged = 0
    for p in all_pairs:
        if _apply_cross_conflict(facts, p):
            flagged += 1
    if flagged:
        save_facts(cfg, facts)
    return {
        "success": True,
        "flagged_pairs": len(all_pairs),
        "flagged_applied": flagged,
        "pairs": all_pairs,
        "llm_used": bool(llm_pairs) or (use_llm and bool(get_configured_llm_safe())),
    }


def get_configured_llm_safe() -> bool:
    try:
        from .utils import get_configured_llm
        return bool(get_configured_llm())
    except Exception:
        return False


def confirm_all_with_semantic_precheck(cfg: dict, semantic: bool = True, use_llm: bool = True) -> dict:
    """
    一键确认前先做语义/规则冲突预检：命中则标 conflict 并跳过；
    仅确认剩余 proposed。
    """
    pre = {"flagged_pairs": 0, "flagged_applied": 0, "pairs": [], "llm_used": False}
    if semantic:
        pre = scan_and_flag_semantic_conflicts(cfg, use_llm=use_llm)

    facts = load_facts(cfg)
    n = 0
    for fact in facts:
        if fact.get("status") == STATUS_PROPOSED:
            fact["status"] = STATUS_CONFIRMED
            fact["confirmed_snapshot"] = {
                "value": fact.get("value"),
                "statement": fact.get("statement"),
            }
            fact["candidates"] = []
            fact["updated_at"] = _now_iso()
            n += 1
    save_facts(cfg, facts)
    return {
        "success": True,
        "confirmed_count": n,
        "semantic_precheck": semantic,
        "flagged_pairs": pre.get("flagged_pairs", 0),
        "flagged_applied": pre.get("flagged_applied", 0),
        "conflict_pairs": pre.get("pairs") or [],
        "llm_used": pre.get("llm_used", False),
    }


def resolve_conflict(cfg: dict, fact_key: str, chosen_value: str, note: str = None) -> dict:
    key = normalize_fact_key(fact_key)
    facts = load_facts(cfg)
    found = False
    chosen = _norm_value(chosen_value)
    for fact in facts:
        if fact.get("fact_key") != key:
            continue
        found = True
        statement = fact.get("statement") or chosen
        # pick matching candidate statement if any
        for c in fact.get("candidates") or []:
            if _values_equal(c.get("value"), chosen) or _values_equal(c.get("statement"), chosen):
                statement = c.get("statement") or chosen
                break
        if fact.get("confirmed_snapshot") and (
            _values_equal(fact["confirmed_snapshot"].get("value"), chosen)
            or _values_equal(fact["confirmed_snapshot"].get("statement"), chosen)
        ):
            statement = fact["confirmed_snapshot"].get("statement") or chosen

        fact["value"] = chosen
        fact["statement"] = statement
        fact["status"] = STATUS_CONFIRMED
        fact["confirmed_snapshot"] = {"value": chosen, "statement": statement}
        fact["candidates"] = []
        fact["resolve_note"] = note or ""
        fact["updated_at"] = _now_iso()
        break
    if not found:
        return {"success": False, "message": f"未找到事实键 `{key}`"}
    save_facts(cfg, facts)
    return {"success": True, "fact_key": key, "value": chosen, "status": STATUS_CONFIRMED}


def get_rewrite_fact_bundle(cfg: dict) -> dict:
    """
    供 rewrite 消费：仅 confirmed；冲突有历史 confirmed 则沿用并记 warning。
    """
    facts = load_facts(cfg)
    used = []
    warnings = []
    skipped = []

    for fact in facts:
        status = fact.get("status")
        key = fact.get("fact_key")
        if status == STATUS_CONFIRMED:
            used.append(fact)
        elif status == STATUS_CONFLICT:
            snap = fact.get("confirmed_snapshot")
            if snap and (snap.get("value") or snap.get("statement")):
                used.append({
                    **fact,
                    "value": snap.get("value"),
                    "statement": snap.get("statement"),
                    "status": STATUS_CONFIRMED,
                    "_degraded_from_conflict": True,
                })
                warnings.append(f"`{key}` 冲突未决，沿用历史已确认值")
            else:
                skipped.append(key)
                warnings.append(f"`{key}` 冲突未决且无历史确认，已跳过（禁止编造）")
        elif status == STATUS_PROPOSED:
            skipped.append(key)

    md_lines = ["# 已确认真相源（供普林斯顿重构）", ""]
    if warnings:
        md_lines.append("> 告警：")
        for w in warnings:
            md_lines.append(f"> - {w}")
        md_lines.append("")
    if not used:
        md_lines.append("- （尚无已确认事实；请先在真相源面板确认，或继续基于 project.yaml 画像降级生成）")
    else:
        for fact in used:
            cat = fact.get("category") or "事实"
            md_lines.append(
                f"- **[{cat}] `{fact.get('fact_key')}`**：{fact.get('statement') or fact.get('value')}"
            )
    return {
        "facts": used,
        "warnings": warnings,
        "skipped": skipped,
        "confirmed_count": len(used),
        "conflict_count": sum(1 for f in facts if f.get("status") == STATUS_CONFLICT),
        "proposed_count": sum(1 for f in facts if f.get("status") == STATUS_PROPOSED),
        "markdown": "\n".join(md_lines) + "\n",
    }


def seed_facts_from_config(cfg: dict, source_id: str = "paste:project_yaml") -> list:
    """从 project.yaml 生成基础提案事实。"""
    company = cfg.get("company_name") or cfg.get("client_name") or ""
    brand = cfg.get("brand_name") or company
    proposals = []
    mapping = [
        ("entity.legal_name", company, "企业全称"),
        ("entity.brand_name", brand, "品牌简称"),
        ("entity.official_url", cfg.get("official_url") or "", "官方网站"),
        ("entity.founder", cfg.get("founder") or "", "核心负责人"),
        ("business.industry", cfg.get("industry") or "", "所属行业"),
        ("service.area", cfg.get("area_served") or "", "服务区域"),
        ("contact.telephone", cfg.get("telephone") or "", "联系热线"),
    ]
    for key, value, label in mapping:
        if not value:
            continue
        proposals.append({
            "fact_key": key,
            "category": STANDARD_FACT_KEYS.get(key, "事实"),
            "statement": f"{label}为 {value}",
            "value": str(value),
            "excerpt": str(value),
        })
    return proposals


def proposals_from_markdown_facts(md_text: str) -> list:
    """尽力从旧 raw_extracted_facts.md 列表解析提案。"""
    proposals = []
    for m in re.finditer(r"^-\s+\*\*\[([^\]]+)\]\s*([^*]+)\*\*[：:]\s*(.+)$", md_text or "", re.M):
        category, name, statement = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        # heuristic key from name
        key_guess = name
        for alias, std in ALIAS_TO_STANDARD.items():
            if alias in name.lower() or any(a in name for a in alias.split("_")):
                key_guess = std
                break
        # Chinese heuristics
        if "官网" in name or "网站" in name:
            key_guess = "entity.official_url"
        elif "电话" in name or "热线" in name:
            key_guess = "contact.telephone"
        elif "交付" in name and ("周期" in name or "天" in statement):
            key_guess = "metric.delivery_days"
        elif "质保" in name:
            key_guess = "policy.warranty_days"
        elif "区域" in name or "覆盖" in name:
            key_guess = "service.area"
        elif "行业" in name:
            key_guess = "business.industry"
        elif "主体" in name or "企业" in name:
            key_guess = "entity.legal_name"
        elif "品牌" in name:
            key_guess = "entity.brand_name"
        elif "负责人" in name or "带头人" in name:
            key_guess = "entity.founder"
        elif "业务" in name:
            key_guess = "business.core_scope"
        elif "源码" in name:
            key_guess = "policy.source_code_delivery"
        else:
            ascii_name = re.sub(r"[^a-z0-9_]+", "", name.lower()).strip("_")
            if ascii_name:
                key_guess = f"custom.{ascii_name[:40]}"
            else:
                digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
                key_guess = f"custom.fact_{digest}"

        value = statement
        num = re.search(r"(\d+)\s*天", statement)
        if key_guess == "metric.delivery_days" and num:
            value = num.group(1)
        num2 = re.search(r"(\d+)\s*天", statement)
        if key_guess == "policy.warranty_days" and num2:
            value = num2.group(1)

        proposals.append({
            "fact_key": key_guess,
            "category": category,
            "statement": statement,
            "value": value,
            "excerpt": statement[:240],
        })
    return proposals


def migrate_legacy_raw_materials(cfg: dict) -> dict:
    """幂等：将旧单文件迁入 evidence/ + ledger。"""
    paths = ensure_dirs(cfg)
    raw_dir = paths["raw_dir"]
    migrated = {"evidence": [], "facts_seeded": False}

    # already migrated?
    index = load_evidence_index(cfg)
    facts = load_facts(cfg)

    legacy_website = os.path.join(raw_dir, "website_crawled_raw.md")
    if os.path.isfile(legacy_website):
        with open(legacy_website, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
        url = cfg.get("official_url") or ""
        m = re.search(r"抓取自官方来源:\s*\[([^\]]+)\]\(([^)]+)\)", body)
        if m:
            url = m.group(2).strip() or url
        if not url:
            # try any http link
            m2 = re.search(r"https?://[^\s\)]+", body)
            url = m2.group(0) if m2 else "https://legacy.local/website"
        sid = source_id_for_url(url)
        if not any(e.get("source_id") == sid for e in index):
            upsert_evidence(cfg, sid, body, kind="url", url=url, title="迁自 website_crawled_raw.md")
            migrated["evidence"].append(sid)

    for fname in os.listdir(raw_dir) if os.path.isdir(raw_dir) else []:
        if fname in ("website_crawled_raw.md", "raw_extracted_facts.md"):
            continue
        if fname in ("evidence", "ledger"):
            continue
        fpath = os.path.join(raw_dir, fname)
        if not os.path.isfile(fpath):
            continue
        if not fname.endswith((".md", ".txt")):
            continue
        sid = source_id_for_paste(fname)
        if any(e.get("source_id") == sid for e in load_evidence_index(cfg)):
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
        upsert_evidence(cfg, sid, body, kind="paste", title=fname)
        migrated["evidence"].append(sid)

    if not facts:
        proposals = seed_facts_from_config(cfg)
        compat = paths["compat_md"]
        if os.path.isfile(compat):
            with open(compat, "r", encoding="utf-8", errors="ignore") as f:
                proposals.extend(proposals_from_markdown_facts(f.read()))
        if proposals:
            # seed as confirmed for historical continuity (design: default confirmed for historically effective)
            stats = merge_fact_proposals(cfg, proposals, source_id="paste:legacy_migration")
            # elevate non-conflict to confirmed
            confirm_all_non_conflict(cfg)
            migrated["facts_seeded"] = True
            migrated["merge"] = stats

    return migrated


def collect_all_evidence_text(cfg: dict, budget: int = 50000) -> str:
    """汇总全部证据正文（供提取）。"""
    migrate_legacy_raw_materials(cfg)
    parts = []
    used = 0
    for entry in list_evidence(cfg):
        body = read_evidence_body(cfg, entry.get("source_id")) or ""
        if not body:
            continue
        remaining = budget - used
        if remaining <= 0:
            break
        chunk = body[:remaining]
        parts.append(f"\n\n<!-- 来源: {entry.get('source_id')} -->\n{chunk}")
        used += len(chunk)
    return "".join(parts).strip()
