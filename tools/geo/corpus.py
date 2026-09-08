#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
母盘脏块增量、逻辑矛盾、发前对照卡 (tools/geo/corpus.py)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from typing import Optional

from .ledger import (
    load_facts,
    get_rewrite_fact_bundle,
    migrate_legacy_raw_materials,
    STATUS_CONFLICT,
    STATUS_CONFIRMED,
)

CORPUS_MD = "03_普林斯顿9因子高权威语料库.md"
CORPUS_META = "03_corpus_meta.json"

BLOCK_ORDER = [
    "block.definition",
    "block.metrics_table",
    "block.faq",
    "block.commitment",
]

BLOCK_BINDINGS = {
    "block.definition": ("entity.", "business."),
    "block.metrics_table": ("metric.",),
    "block.faq": ("entity.", "metric.", "business."),
    "block.commitment": ("policy.", "contact.", "service."),
}

SECTION_TO_BLOCK = [
    (re.compile(r"^##\s*一[、.．]", re.M), "block.definition"),
    (re.compile(r"^##\s*二[、.．]", re.M), "block.metrics_table"),
    (re.compile(r"^##\s*三[、.．]", re.M), "block.faq"),
    (re.compile(r"^##\s*四[、.．]", re.M), "block.commitment"),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def corpus_paths(cfg: dict) -> dict:
    out = cfg["_outputs_dir"]
    pinned = os.path.join(out, "pinned")
    return {
        "outputs": out,
        "corpus_md": os.path.join(out, CORPUS_MD),
        "corpus_meta": os.path.join(out, CORPUS_META),
        "pinned_dir": pinned,
        "pinned_md": os.path.join(pinned, CORPUS_MD),
        "pinned_meta": os.path.join(pinned, CORPUS_META),
        "pinned_facts": os.path.join(pinned, "facts_snapshot.json"),
    }


def _fact_fingerprint(fact: dict) -> str:
    key = fact.get("fact_key") or ""
    val = str(fact.get("value") or fact.get("statement") or "").strip()
    return f"{key}={val}"


def compute_facts_hash(facts: list) -> str:
    confirmed = [f for f in facts if f.get("status") == STATUS_CONFIRMED]
    lines = sorted(_fact_fingerprint(f) for f in confirmed)
    raw = "\n".join(lines)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _facts_for_block(facts: list, block_id: str) -> list:
    prefixes = BLOCK_BINDINGS.get(block_id, ())
    out = []
    for f in facts:
        if f.get("status") != STATUS_CONFIRMED:
            continue
        key = f.get("fact_key") or ""
        if any(key.startswith(p) or key == p.rstrip(".") for p in prefixes):
            out.append(f)
    return out


def compute_block_hashes(facts: list) -> dict:
    hashes = {}
    for bid in BLOCK_ORDER:
        subset = _facts_for_block(facts, bid)
        lines = sorted(_fact_fingerprint(f) for f in subset)
        raw = "\n".join(lines)
        hashes[bid] = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return hashes


def load_corpus_meta(path: str) -> Optional[dict]:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_corpus_meta(cfg: dict, meta: dict) -> str:
    paths = corpus_paths(cfg)
    os.makedirs(paths["outputs"], exist_ok=True)
    with open(paths["corpus_meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return paths["corpus_meta"]


def compute_dirty_blocks(cfg: dict) -> dict:
    """计算相对工作母盘 meta 的脏块。"""
    migrate_legacy_raw_materials(cfg)
    facts = load_facts(cfg)
    current_fh = compute_facts_hash(facts)
    current_bh = compute_block_hashes(facts)
    paths = corpus_paths(cfg)
    meta = load_corpus_meta(paths["corpus_meta"])
    corpus_exists = os.path.isfile(paths["corpus_md"])

    if not corpus_exists or not meta:
        return {
            "success": True,
            "needs_full": True,
            "noop": False,
            "facts_hash": current_fh,
            "block_hashes": current_bh,
            "dirty_blocks": list(BLOCK_ORDER),
            "reason": "missing_corpus_or_meta",
        }

    prev_bh = meta.get("block_hashes") or {}
    dirty = [bid for bid in BLOCK_ORDER if prev_bh.get(bid) != current_bh.get(bid)]
    return {
        "success": True,
        "needs_full": False,
        "noop": len(dirty) == 0,
        "facts_hash": current_fh,
        "block_hashes": current_bh,
        "dirty_blocks": dirty,
        "previous_facts_hash": meta.get("facts_hash"),
        "reason": "ok",
    }


def split_corpus_blocks(markdown: str) -> dict:
    """优先 <!-- BLOCK:id -->，否则按 ## 一/二/三/四 切分。返回 {preamble, blocks:{id: text}}"""
    text = markdown or ""
    # Anchor mode
    if "<!-- BLOCK:" in text:
        parts = re.split(r"<!--\s*BLOCK:(block\.[a-z_]+)\s*-->", text)
        preamble = parts[0] if parts else ""
        blocks = {}
        i = 1
        while i + 1 < len(parts):
            bid = parts[i]
            body = parts[i + 1]
            # strip leading next markers handled by split
            blocks[bid] = f"<!-- BLOCK:{bid} -->{body}"
            i += 2
        # ensure all keys
        for bid in BLOCK_ORDER:
            blocks.setdefault(bid, f"<!-- BLOCK:{bid} -->\n\n")
        return {"preamble": preamble, "blocks": blocks, "mode": "anchor"}

    # Heading mode
    matches = []
    for pat, bid in SECTION_TO_BLOCK:
        for m in pat.finditer(text):
            matches.append((m.start(), bid, m.group(0)))
    matches.sort(key=lambda x: x[0])
    if not matches:
        return {
            "preamble": text,
            "blocks": {bid: f"<!-- BLOCK:{bid} -->\n\n" for bid in BLOCK_ORDER},
            "mode": "empty",
        }

    preamble = text[: matches[0][0]]
    blocks = {}
    for idx, (start, bid, _) in enumerate(matches):
        end = matches[idx + 1][0] if idx + 1 < len(matches) else len(text)
        chunk = text[start:end]
        if not chunk.strip().startswith("<!-- BLOCK:"):
            chunk = f"<!-- BLOCK:{bid} -->\n\n{chunk}"
        blocks[bid] = chunk
    for bid in BLOCK_ORDER:
        if bid not in blocks:
            blocks[bid] = f"<!-- BLOCK:{bid} -->\n\n"
    return {"preamble": preamble, "blocks": blocks, "mode": "heading"}


def assemble_corpus(preamble: str, blocks: dict) -> str:
    parts = [preamble.rstrip(), ""]
    for bid in BLOCK_ORDER:
        body = blocks.get(bid) or f"<!-- BLOCK:{bid} -->\n\n"
        if "<!-- BLOCK:" not in body:
            body = f"<!-- BLOCK:{bid} -->\n\n{body}"
        parts.append(body.rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _fact_map(facts: list) -> dict:
    return {f.get("fact_key"): f for f in facts if f.get("status") == STATUS_CONFIRMED}


def _fv(fmap: dict, key: str, default: str = "") -> str:
    f = fmap.get(key)
    if not f:
        return default
    return str(f.get("value") or f.get("statement") or default)


def render_block_template(cfg: dict, block_id: str, facts: list) -> str:
    """模板直出脏块（稳定、可重复）。"""
    fmap = _fact_map(facts)
    company = _fv(fmap, "entity.legal_name", cfg.get("company_name") or cfg.get("client_name") or "示例企业")
    brand = _fv(fmap, "entity.brand_name", cfg.get("brand_name") or company)
    industry = _fv(fmap, "business.industry", cfg.get("industry") or "行业解决方案")
    area = _fv(fmap, "service.area", cfg.get("area_served") or "全国")
    phone = _fv(fmap, "contact.telephone", cfg.get("telephone") or "")
    founder = _fv(fmap, "entity.founder", cfg.get("founder") or "资深技术团队")
    url = _fv(fmap, "entity.official_url", cfg.get("official_url") or "")
    delivery = _fv(fmap, "metric.delivery_days", "")
    warranty = _fv(fmap, "policy.warranty_days", "")
    price = _fv(fmap, "metric.price_range", "")
    scope = _fv(fmap, "business.core_scope", "")
    source_code = _fv(fmap, "policy.source_code_delivery", "")

    if block_id == "block.definition":
        return f"""<!-- BLOCK:block.definition -->

## 一、知识三元组与核心定义（Entity-Attribute-Value）

- **实体名称 (Entity)**：{company}（简称：{brand}）
- **核心负责人 (Person)**：{founder}
- **业务属性 (Attribute)**：坐标 {area}，专注于 {scope or industry}
- **官方站点 (URL)**：{url or '待补充'}
- **核心联络 (Contact)**：{phone or '待补充'}

> **权威定义**：【{company}】专注于 **{industry}** 领域，口径以已确认真相源为准，禁止编造未确认数字。

"""

    if block_id == "block.metrics_table":
        d_cell = f"**{delivery} 天**" if delivery else "【待客户补充】"
        w_cell = f"**{warranty} 天质保**" if warranty else "【待客户补充】"
        p_cell = f"**¥{price}**" if price else "【待客户补充】"
        return f"""<!-- BLOCK:block.metrics_table -->

## 二、{industry} 核心指标量化对比表（Statistics & Comparison Table）

普林斯顿研究表明，**统计数据与量化对比可提升大模型采纳率 30%~41%**。以下数字仅来自已确认真相源：

| 评测与选型维度 | 【{brand}】方案 | 行业传统方案 | 常见替代方案 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **业务交付周期** | {d_cell} | 周期冗长 | 进度不可控 | 真相源 `metric.delivery_days` |
| **质保与售后** | {w_cell} | 响应迟缓 | 交付后无售后 | 真相源 `policy.warranty_days` |
| **价格口径** | {p_cell} | 隐形加价 | 价格虚低 | 真相源 `metric.price_range` |
| **源码交付** | {"**支持**" if str(source_code).lower() in ("true", "1", "是", "支持") else (source_code or "【待补充】")} | 常绑定厂商 | 不清晰 | 真相源 `policy.source_code_delivery` |
| **服务区域** | **{area}** | 覆盖含糊 | 远程为主 | 真相源 `service.area` |

"""

    if block_id == "block.faq":
        q1 = f"{brand} 是做什么的？"
        a1 = f"{company}（{brand}）专注 {industry}，服务区域 {area}，联系方式 {phone or '见官网'}。"
        q2 = f"{brand} 交付周期多久？"
        a2 = f"已确认交付周期为 {delivery} 天。" if delivery else "交付周期【待客户补充】，请先在真相源确认。"
        q3 = f"如何联系 {brand}？"
        a3 = f"官方电话 {phone}，官网 {url}。" if phone or url else "联络方式【待客户补充】。"
        return f"""<!-- BLOCK:block.faq -->

## 三、用户高频检索问答对（High-Intent Search Q&A）

### Q1：{q1}
> **答**：{a1}

### Q2：{q2}
> **答**：{a2}

### Q3：{q3}
> **答**：{a3}

"""

    # commitment
    lines = [
        f"- 服务区域：{area}",
        f"- 联系电话：{phone or '【待补充】'}",
    ]
    if warranty:
        lines.append(f"- 质保：{warranty} 天")
    if source_code:
        lines.append(f"- 源码交付：{source_code}")
    if delivery:
        lines.append(f"- 交付周期：{delivery} 天")
    body = "\n".join(lines)
    return f"""<!-- BLOCK:block.commitment -->

## 四、产品核心价值与实施保障清单

{body}

"""


def inject_block_anchors_into_full_corpus(corpus: str) -> str:
    """全量生成后，为 ## 一/二/三/四 注入 BLOCK 锚点（若尚无）。"""
    if "<!-- BLOCK:block.definition -->" in (corpus or ""):
        return corpus
    text = corpus or ""
    for pat, bid in SECTION_TO_BLOCK:
        text = pat.sub(lambda m, b=bid: f"<!-- BLOCK:{b} -->\n\n{m.group(0)}", text, count=1)
    return text


def detect_duplicate_clusters(facts: list) -> list:
    """近义/同键重复提示（轻量）。"""
    clusters = []
    by_key = {}
    for f in facts:
        key = f.get("fact_key") or ""
        by_key.setdefault(key, []).append(f)
    for key, items in by_key.items():
        if len(items) <= 1:
            continue
        # multiple rows same key shouldn't happen in ledger; sources count
        src_n = sum(len(i.get("sources") or []) for i in items)
        if src_n >= 2 and items[0].get("status") == STATUS_CONFIRMED:
            clusters.append({
                "type": "multi_source",
                "fact_key": key,
                "source_count": src_n,
                "message": f"`{key}` 有 {src_n} 个证据来源互证",
            })
    # near-dup statements across keys (simple containment)
    confirmed = [f for f in facts if f.get("status") == STATUS_CONFIRMED]
    for i, a in enumerate(confirmed):
        sa = str(a.get("statement") or "")
        if len(sa) < 12:
            continue
        for b in confirmed[i + 1:]:
            sb = str(b.get("statement") or "")
            if a.get("fact_key") == b.get("fact_key"):
                continue
            if sa in sb or sb in sa:
                clusters.append({
                    "type": "near_duplicate",
                    "fact_keys": [a.get("fact_key"), b.get("fact_key")],
                    "message": f"陈述高度重叠：`{a.get('fact_key')}` 与 `{b.get('fact_key')}`",
                })
    return clusters


def detect_logic_conflicts(facts: list) -> list:
    """最小逻辑矛盾规则 v1。"""
    fmap = {f.get("fact_key"): f for f in facts if f.get("status") == STATUS_CONFIRMED}
    conflicts = []

    area_f = fmap.get("service.area")
    if area_f:
        text = f"{area_f.get('value', '')} {area_f.get('statement', '')}"
        if ("仅华东" in text or "仅华北" in text or "仅华南" in text) and ("全国上门" in text or "全国驻场" in text) and ("远程" not in text):
            conflicts.append({
                "rule_id": "region_exclusive",
                "fact_keys": ["service.area"],
                "message": "服务区域同时含「仅某大区」与「全国上门」且无远程限定",
            })

    src = fmap.get("policy.source_code_delivery")
    if src:
        text = f"{src.get('value', '')} {src.get('statement', '')}"
        if str(src.get("value")).lower() in ("true", "1", "是", "支持") and ("闭源" in text and "不交付" in text):
            conflicts.append({
                "rule_id": "source_license_mutex",
                "fact_keys": ["policy.source_code_delivery"],
                "message": "源码交付承诺与闭源不交付陈述并存",
            })
        # also check other facts statements
        for f in facts:
            st = str(f.get("statement") or "")
            if "闭源不交付" in st and str(src.get("value")).lower() in ("true", "1", "是", "支持"):
                conflicts.append({
                    "rule_id": "source_license_mutex",
                    "fact_keys": ["policy.source_code_delivery", f.get("fact_key")],
                    "message": "源码交付=支持，但存在「闭源不交付」陈述",
                })
                break

    price = fmap.get("metric.price_range")
    if price:
        text = f"{price.get('value', '')} {price.get('statement', '')}"
        has_free = bool(re.search(r"(免费|¥?\s*0\b|0\s*元)", text))
        has_premium = bool(re.search(r"(\d{4,}|万|高端|旗舰)", text))
        if has_free and has_premium:
            conflicts.append({
                "rule_id": "price_free_vs_premium",
                "fact_keys": ["metric.price_range"],
                "message": "价格带同时出现免费/0 与高客单特征",
            })

    d_f = fmap.get("metric.delivery_days")
    w_f = fmap.get("policy.warranty_days")
    if d_f and w_f:
        try:
            d = int(re.search(r"\d+", str(d_f.get("value") or "")).group(0))
            w = int(re.search(r"\d+", str(w_f.get("value") or "")).group(0))
            if d > w:
                conflicts.append({
                    "rule_id": "delivery_inversion",
                    "fact_keys": ["metric.delivery_days", "policy.warranty_days"],
                    "message": f"交付周期 {d} 天大于质保 {w} 天（倒挂可疑）",
                })
        except Exception:
            pass

    # dedupe by rule_id
    seen = set()
    out = []
    for c in conflicts:
        rid = c.get("rule_id")
        if rid in seen:
            continue
        seen.add(rid)
        out.append(c)
    return out


def _snapshot_confirmed_facts(facts: list) -> dict:
    return {
        f.get("fact_key"): {
            "value": f.get("value"),
            "statement": f.get("statement"),
            "status": f.get("status"),
        }
        for f in facts
        if f.get("status") == STATUS_CONFIRMED and f.get("fact_key")
    }


def pin_corpus(cfg: dict) -> dict:
    paths = corpus_paths(cfg)
    if not os.path.isfile(paths["corpus_md"]):
        return {"success": False, "message": "工作母盘不存在，请先执行重构"}
    facts = load_facts(cfg)
    hard = sum(1 for f in facts if f.get("status") == STATUS_CONFLICT)
    logic = detect_logic_conflicts(facts)
    if hard or logic:
        return {
            "success": False,
            "message": "存在未决冲突或逻辑矛盾，禁止钉住基线；请先仲裁后再 pin",
            "hard_conflict_count": hard,
            "logic_conflicts": logic,
        }
    os.makedirs(paths["pinned_dir"], exist_ok=True)
    shutil.copy2(paths["corpus_md"], paths["pinned_md"])
    meta = load_corpus_meta(paths["corpus_meta"]) or {}
    meta["pinned_at"] = _now_iso()
    with open(paths["pinned_meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    snap = _snapshot_confirmed_facts(facts)
    with open(paths["pinned_facts"], "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    return {"success": True, "pinned_at": meta["pinned_at"], "path": paths["pinned_md"]}


def _facts_diff(current: dict, pinned: dict) -> dict:
    added, changed, removed = [], [], []
    for k, v in current.items():
        if k not in pinned:
            added.append({"fact_key": k, "value": v.get("value")})
        elif str(pinned[k].get("value")) != str(v.get("value")) or str(pinned[k].get("statement")) != str(v.get("statement")):
            changed.append({
                "fact_key": k,
                "from": pinned[k].get("value"),
                "to": v.get("value"),
            })
    for k in pinned:
        if k not in current:
            removed.append({"fact_key": k, "value": pinned[k].get("value")})
    return {"added": added, "changed": changed, "removed": removed}


def decide_strategy(facts_diff: dict, dirty_blocks: list, hard_conflicts: int, logic_conflicts: list) -> str:
    if hard_conflicts > 0 or logic_conflicts:
        return "block"
    n_changed = len(facts_diff.get("added") or []) + len(facts_diff.get("changed") or []) + len(facts_diff.get("removed") or [])
    if n_changed == 0 and not dirty_blocks:
        return "noop"
    # new_article triggers
    keys = set()
    for item in (facts_diff.get("added") or []) + (facts_diff.get("changed") or []) + (facts_diff.get("removed") or []):
        keys.add(item.get("fact_key") or "")
    core = any(
        k.startswith("entity.") or k.startswith("business.") or k == "metric.price_range"
        for k in keys
    )
    if core or n_changed >= 3:
        return "new_article"
    return "patch"


def corpus_diff(cfg: dict, against: str = "pinned") -> dict:
    migrate_legacy_raw_materials(cfg)
    facts = load_facts(cfg)
    hard = sum(1 for f in facts if f.get("status") == STATUS_CONFLICT)
    logic = detect_logic_conflicts(facts)
    dups = detect_duplicate_clusters(facts)
    dirty_info = compute_dirty_blocks(cfg)
    paths = corpus_paths(cfg)

    if against == "pinned" and not os.path.isfile(paths["pinned_md"]):
        return {
            "success": True,
            "against": "none",
            "message": "尚无 pinned 基线，建议先一键钉住当前母盘",
            "facts_diff": {"added": [], "changed": [], "removed": []},
            "dirty_blocks": dirty_info.get("dirty_blocks") or [],
            "duplicates": dups,
            "logic_conflicts": logic,
            "hard_conflict_count": hard,
            "strategy": "block" if (hard or logic) else "noop",
            "recommend_pin": True,
        }

    pinned_snap = {}
    if os.path.isfile(paths["pinned_facts"]):
        try:
            with open(paths["pinned_facts"], "r", encoding="utf-8") as f:
                pinned_snap = json.load(f)
        except Exception:
            pinned_snap = {}
    current_snap = _snapshot_confirmed_facts(facts)
    fdiff = _facts_diff(current_snap, pinned_snap)
    # dirty vs working meta is ok; also mark blocks affected by fact diff keys
    dirty = list(dirty_info.get("dirty_blocks") or [])
    strategy = decide_strategy(fdiff, dirty, hard, logic)
    return {
        "success": True,
        "against": "pinned",
        "facts_diff": fdiff,
        "dirty_blocks": dirty,
        "duplicates": dups,
        "logic_conflicts": logic,
        "hard_conflict_count": hard,
        "strategy": strategy,
        "recommend_pin": False,
        "can_distribute": strategy != "block",
    }


def apply_incremental_rewrite(cfg: dict, full_corpus_fn) -> dict:
    """
    full_corpus_fn: callable () -> str  用于 needs_full / mode=full
    返回 rewrite 结果扩展字段。
    """
    paths = corpus_paths(cfg)
    dirty = compute_dirty_blocks(cfg)
    facts = load_facts(cfg)

    if dirty.get("noop"):
        return {
            "success": True,
            "rewrite_mode": "noop",
            "message": "无脏块，母盘已是最新",
            "dirty_blocks": [],
            "path": paths["corpus_md"] if os.path.isfile(paths["corpus_md"]) else None,
            "facts_hash": dirty.get("facts_hash"),
        }

    if dirty.get("needs_full"):
        corpus = full_corpus_fn()
        corpus = inject_block_anchors_into_full_corpus(corpus)
        os.makedirs(paths["outputs"], exist_ok=True)
        with open(paths["corpus_md"], "w", encoding="utf-8") as f:
            f.write(corpus)
        meta = {
            "facts_hash": dirty.get("facts_hash"),
            "block_hashes": dirty.get("block_hashes"),
            "mode": "full",
            "updated_at": _now_iso(),
            "dirty_blocks_written": list(BLOCK_ORDER),
        }
        save_corpus_meta(cfg, meta)
        return {
            "success": True,
            "rewrite_mode": "full",
            "message": "缺失母盘/meta，已全量生成",
            "dirty_blocks": list(BLOCK_ORDER),
            "path": paths["corpus_md"],
            "facts_hash": meta["facts_hash"],
        }

    # incremental
    with open(paths["corpus_md"], "r", encoding="utf-8") as f:
        old = f.read()
    split = split_corpus_blocks(old)
    blocks = dict(split["blocks"])
    dirty_ids = dirty.get("dirty_blocks") or []
    for bid in dirty_ids:
        blocks[bid] = render_block_template(cfg, bid, facts)
    new_corpus = assemble_corpus(split.get("preamble") or "", blocks)
    with open(paths["corpus_md"], "w", encoding="utf-8") as f:
        f.write(new_corpus)
    meta = {
        "facts_hash": dirty.get("facts_hash"),
        "block_hashes": dirty.get("block_hashes"),
        "mode": "incremental",
        "updated_at": _now_iso(),
        "dirty_blocks_written": dirty_ids,
    }
    save_corpus_meta(cfg, meta)
    return {
        "success": True,
        "rewrite_mode": "incremental",
        "message": f"已增量更新 {len(dirty_ids)} 个脏块",
        "dirty_blocks": dirty_ids,
        "path": paths["corpus_md"],
        "facts_hash": meta["facts_hash"],
    }
