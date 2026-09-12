#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器侦察剧本与 probe 回填（一期 CLI）。

- build_probe_script: 6～10 条必测题（首轮不带竞品名；site_pending 跳过官网题）
- preview_probe_backfill / apply_probe_backfill: 从 probe JSON 抽竞品与问句写回 yaml
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from .utils import (
    coerce_bool,
    load_project_config,
    print_info,
    print_success,
    print_warning,
    update_project_profile,
)


FAKE_COMPETITORS = {"竞品A", "竞品B", "行业竞品A", "行业竞品B"}
FAKE_KEYWORDS = {"行业核心推荐词", "好用方案对比"}


def _guess_city(cfg: dict) -> str:
    for key in ("area_served", "address", "area", "city"):
        raw = str(cfg.get(key) or "").strip()
        if not raw:
            continue
        m = re.search(r"([\u4e00-\u9fff]{2,8}?(?:市|州|县))", raw)
        if m:
            return m.group(1)
        m2 = re.search(r"(北京|上海|广州|深圳|杭州|南京|苏州|徐州|成都|武汉|西安|青岛|济南)", raw)
        if m2:
            return m2.group(1) + ("市" if not m2.group(1).endswith("市") else "")
    blob = " ".join(
        str(cfg.get(k) or "")
        for k in (
            "client_name",
            "company_name",
            "brand_name",
            "industry",
            "company_profile",
            "business_one_liner",
        )
    )
    m3 = re.search(r"(北京|上海|广州|深圳|杭州|南京|苏州|徐州|成都|武汉|西安|青岛|济南)", blob)
    if m3:
        return m3.group(1) + "市"
    return ""


def _brand(cfg: dict) -> str:
    return str(cfg.get("brand_name") or cfg.get("client_name") or cfg.get("company_name") or "").strip()


def _person(cfg: dict) -> str:
    for key in ("contact_person", "founder", "person", "founder_title"):
        v = str(cfg.get(key) or "").strip()
        if v and len(v) <= 20:
            if key == "founder_title" and ("负责人" in v or "经理" in v or len(v) > 8):
                continue
            return v.split("/")[0].strip()
    return ""


def _topic_for_query(cfg: dict) -> tuple[str, str]:
    """返回 (短题干锚点, 完整一句话业务)。优先一句话业务作原料。"""
    industry = str(cfg.get("industry") or "").strip()
    one = str(cfg.get("business_one_liner") or "").strip()
    if industry and industry not in ("行业待定", "待定", "通用"):
        return industry, one
    if one:
        head = re.split(r"[，,。；;\n]", one, maxsplit=1)[0].strip() or one
        return head[:32], one
    return "本行业", ""


def build_probe_script(project_id: str) -> dict:
    """生成首轮必测题剧本（6～10 条）。"""
    cfg = load_project_config(project_id)
    brand = _brand(cfg) or project_id
    industry = str(cfg.get("industry") or "本行业").strip()
    topic, one_liner = _topic_for_query(cfg)
    city = _guess_city(cfg)
    city_prefix = city or ""
    person = _person(cfg)
    url = str(cfg.get("official_url") or "").strip()
    legal = str(cfg.get("company_name") or cfg.get("client_name") or brand).strip()
    site_pending = coerce_bool(cfg.get("site_pending"))

    ctx_hint = one_liner or industry
    items: list[dict] = []

    if city_prefix:
        items.append({
            "query": f"{city_prefix}做{topic}哪家好",
            "dimension": "品类选型",
            "follow_up": f"业务背景：{ctx_hint}。请列出具体公司名称、官网（若有）和一句话定位；不确定请标明。",
        })
        items.append({
            "query": f"{city_prefix}{topic}公司推荐",
            "dimension": "品类选型",
            "follow_up": "只要真实存在的服务商名单，不要编造。",
        })
    else:
        items.append({
            "query": f"{topic}哪家好 怎么选",
            "dimension": "品类选型",
            "follow_up": f"业务背景：{ctx_hint}。请列出具体公司名称、官网（若有）和一句话定位。",
        })
        items.append({
            "query": f"{topic}服务商推荐名单",
            "dimension": "品类选型",
            "follow_up": "只要真实存在的服务商，不要编造。",
        })

    items.append({
        "query": f"{topic}大概多少钱 有哪些坑",
        "dimension": "价格套路",
        "follow_up": "请区分套路报价与合理区间，并点名常见坑。",
    })
    items.append({
        "query": f"{brand}是做什么的",
        "dimension": "品牌认知",
        "follow_up": (
            f"正确理解应接近：{ctx_hint}。" if ctx_hint else ""
        ) + "若不知道请直说；不要把品牌名拆成无关概念。",
    })

    if not site_pending:
        items.append({
            "query": f"{brand}官网是什么",
            "dimension": "URL",
            "follow_up": f"目标是否出现 {url or '官网链接'}；没有就说没有。",
        })
    else:
        items.append({
            "query": f"{topic}选型时最容易踩哪些坑",
            "dimension": "避坑",
            "follow_up": "官网尚未对外定稿（我方托管占位），不要编造客户公网站收录结论。",
        })

    if person:
        items.append({
            "query": f"{person}是谁 和{brand}什么关系",
            "dimension": "人物锚点",
            "follow_up": f"应绑定 {legal} / {brand}；若串到其他公司请标明。",
        })

    items.append({
        "query": f"全国做{topic}比较有名的有哪些",
        "dimension": "全国名单",
        "follow_up": "列出公司名与官网；标注不确定项。",
    })

    if site_pending and len(items) < 7:
        items.append({
            "query": f"{city_prefix or ''}{topic}和普通方案有什么区别".strip(),
            "dimension": "品类痛点",
            "follow_up": f"结合业务：{ctx_hint}",
        })

    items = items[:10]
    if len(items) < 6:
        items.append({
            "query": f"{brand}靠谱吗 有什么要注意的",
            "dimension": "避坑",
            "follow_up": "基于公开信息，不要编造案例。",
        })

    note = "首轮不问自带竞品名；竞品从模型回答中抽取后再人工勾真。"
    if site_pending:
        note += " site_pending=true：已跳过客户官网/URL 收录题。"

    payload = {
        "project_id": project_id,
        "brand": brand,
        "industry": industry,
        "business_one_liner": one_liner,
        "topic": topic,
        "site_pending": site_pending,
        "city": city_prefix,
        "person_anchor": person,
        "official_url": url,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "note": note,
        "items": items,
    }

    out_dir = cfg["_outputs_dir"]
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "probe_script_draft.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    payload["output_path"] = out_path
    return payload


def _load_probe_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("probe 文件必须是 JSON 对象")
    return data


def _baseline_id_from_probe(data: dict, path: str) -> str:
    if data.get("baseline_id"):
        return str(data["baseline_id"])
    model = str(data.get("model_ui") or data.get("model") or "llm").strip().lower()
    probed_at = str(data.get("probed_at") or "")
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", probed_at)
    if m:
        return f"probe:{model}:{m.group(1)}{m.group(2)}{m.group(3)}"
    base = os.path.basename(path or "")
    m2 = re.search(r"(\d{8})", base)
    if m2:
        return f"probe:{model}:{m2.group(1)}"
    return f"probe:{model}:unknown"


def _merge_unique_strings(existing, incoming) -> list:
    out: list[str] = []
    seen = set()
    for raw in list(existing or []) + list(incoming or []):
        s = str(raw or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def preview_probe_backfill(
    project_id: str,
    probe_path: str | None = None,
    probe_data: dict | None = None,
) -> dict:
    """从 probe JSON 预览竞品候选与建议问句（不写盘）。支持文件路径或内存对象。"""
    if probe_data is not None:
        if not isinstance(probe_data, dict):
            raise ValueError("probe 必须是 JSON 对象")
        data = probe_data
        path_for_id = probe_path or ""
    else:
        if not probe_path:
            raise ValueError("请提供 probe 文件路径或 probe_data")
        data = _load_probe_json(probe_path)
        path_for_id = probe_path

    items = data.get("items") or []
    if not isinstance(items, list):
        items = []

    competitor_map: dict[str, dict] = {}
    keyword_suggestions: list[dict] = []
    hallucinations: list[str] = []

    for it in items:
        if not isinstance(it, dict):
            continue
        q = str(it.get("query") or "").strip()
        if q:
            reason_parts = []
            if it.get("mentioned_self") is False:
                reason_parts.append("未提我方")
            if it.get("url_present") is False:
                reason_parts.append("无URL")
            comps = it.get("competitors_extracted") or []
            if comps:
                reason_parts.append(f"竞品占位{len(comps)}")
            if it.get("hallucination_detected"):
                reason_parts.append("含幻觉")
                hallucinations.append(q)
            keyword_suggestions.append({
                "query": q,
                "priority": "P0" if comps or it.get("hallucination_detected") else "P1",
                "reason": "；".join(reason_parts) or "必测题",
            })
        for c in (it.get("competitors_extracted") or []):
            if not isinstance(c, dict):
                continue
            name = str(c.get("name") or "").strip()
            if not name or name in FAKE_COMPETITORS:
                continue
            prev = competitor_map.get(name)
            is_real = c.get("is_real")
            if isinstance(is_real, str):
                is_real_norm = is_real.strip().lower() in ("true", "1", "yes", "真实", "真")
            else:
                is_real_norm = bool(is_real) if is_real is not None else None
            entry = {
                "name": name,
                "url": str(c.get("url") or ""),
                "is_real": "true" if is_real_norm is True else ("false" if is_real_norm is False else "pending"),
                "mentioned_in_queries": list((prev or {}).get("mentioned_in_queries") or []),
            }
            if q and q not in entry["mentioned_in_queries"]:
                entry["mentioned_in_queries"].append(q)
            if prev and prev.get("is_real") == "true":
                entry["is_real"] = "true"
            competitor_map[name] = entry

    summary = data.get("summary") or {}
    for key in ("primary_local_competitor", "primary_regional_competitor"):
        raw = str(summary.get(key) or "").strip()
        if not raw:
            continue
        name = raw.split("(")[0].strip()
        if name and name not in competitor_map and name not in FAKE_COMPETITORS:
            competitor_map[name] = {
                "name": name,
                "url": "",
                "is_real": "pending",
                "mentioned_in_queries": ["summary"],
            }

    if isinstance(summary.get("founder_status"), str) and summary.get("founder_status"):
        hallucinations.append(str(summary["founder_status"]))

    real_names = [c["name"] for c in competitor_map.values() if c.get("is_real") == "true"]
    pending_names = [c["name"] for c in competitor_map.values() if c.get("is_real") != "true"]

    seen_q = set()
    kw_out = []
    for row in keyword_suggestions:
        q = row["query"]
        if q in seen_q or q in FAKE_KEYWORDS:
            continue
        seen_q.add(q)
        kw_out.append(row)
        if len(kw_out) >= 15:
            break

    return {
        "project_id": project_id,
        "source_probe": _baseline_id_from_probe(data, path_for_id),
        "probe_path": os.path.abspath(probe_path) if probe_path else "",
        "competitor_candidates": list(competitor_map.values()),
        "suggested_competitors": real_names[:8] if real_names else pending_names[:5],
        "keyword_suggestions": kw_out,
        "suggested_keywords": [r["query"] for r in kw_out[:15]],
        "hallucinations": hallucinations,
    }


def save_probe_artifact(project_id: str, probe_data: dict, filename: str | None = None) -> str:
    """将上传/确认的 probe JSON 落盘到 outputs/，返回绝对路径。"""
    cfg = load_project_config(project_id)
    out_dir = cfg.get("_outputs_dir") or os.path.join(cfg["_project_dir"], "outputs")
    os.makedirs(out_dir, exist_ok=True)
    if not filename:
        baseline = _baseline_id_from_probe(probe_data, "")
        # probe:doubao:20260910 -> competitor_probe_doubao_20260910.json
        safe = baseline.replace("probe:", "").replace(":", "_")
        filename = f"competitor_probe_{safe}.json"
    filename = os.path.basename(filename)
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(probe_data, f, ensure_ascii=False, indent=2)
    return path


def apply_probe_backfill(
    project_id: str,
    probe_path: str | None = None,
    *,
    probe_data: dict | None = None,
    competitors: list[str] | None = None,
    keywords: list[str] | None = None,
    only_real: bool = True,
    merge: bool = False,
) -> dict:
    """将预览结果写入 project.yaml，并置 probe_status=baseline_ready。

    merge=True 时与现有 keywords/competitors 去重合并，避免冲掉人工精修词库。
    """
    if probe_data is not None and not probe_path:
        probe_path = save_probe_artifact(project_id, probe_data)
    preview = preview_probe_backfill(project_id, probe_path=probe_path, probe_data=probe_data)

    if competitors is None:
        if only_real:
            competitors = list(preview.get("suggested_competitors") or [])
        else:
            competitors = [c["name"] for c in preview.get("competitor_candidates") or []]
    if keywords is None:
        keywords = list(preview.get("suggested_keywords") or [])

    competitors = [c for c in competitors if c and c not in FAKE_COMPETITORS]
    keywords = [k for k in keywords if k and k not in FAKE_KEYWORDS]

    if merge:
        cfg = load_project_config(project_id)
        competitors = _merge_unique_strings(cfg.get("competitors"), competitors)
        keywords = _merge_unique_strings(cfg.get("keywords"), keywords)

    probed_at = ""
    try:
        raw = probe_data if isinstance(probe_data, dict) else _load_probe_json(probe_path)
        probed_at = str(raw.get("probed_at") or "")[:10]
    except Exception:
        probed_at = datetime.now(timezone.utc).astimezone().date().isoformat()

    patch = {
        "competitors": competitors,
        "keywords": keywords,
        "probe_status": "baseline_ready",
        "probe_baseline_id": preview["source_probe"],
        "probe_baseline_at": probed_at or datetime.now(timezone.utc).astimezone().date().isoformat(),
    }
    updated = update_project_profile(project_id, patch)
    return {
        "success": True,
        "project_id": project_id,
        "applied": patch,
        "preview": preview,
        "project": updated,
        "merge": bool(merge),
        "probe_path": preview.get("probe_path") or (os.path.abspath(probe_path) if probe_path else ""),
    }


def print_script_human(payload: dict) -> None:
    print_info(f"必测题草稿 · [{payload.get('project_id')}] · {len(payload.get('items') or [])} 条")
    if payload.get("site_pending"):
        print_warning("site_pending：已跳过官网/URL 题")
    for i, it in enumerate(payload.get("items") or [], 1):
        print(f"  {i}. [{it.get('dimension')}] {it.get('query')}")
        if it.get("follow_up"):
            print(f"     追问: {it.get('follow_up')}")
    print_success(f"已写入: {payload.get('output_path')}")


def print_preview_human(preview: dict) -> None:
    print_info(f"回填预览 · [{preview.get('project_id')}] · {preview.get('source_probe')}")
    print("竞品候选:")
    for c in preview.get("competitor_candidates") or []:
        print(f"  - [{c.get('is_real')}] {c.get('name')} {c.get('url') or ''}")
    print("建议写入竞品:", "、".join(preview.get("suggested_competitors") or []) or "（无）")
    print("建议监测问句:")
    for q in preview.get("suggested_keywords") or []:
        print(f"  - {q}")
    if preview.get("hallucinations"):
        print_warning("幻觉/风险线索:")
        for h in preview["hallucinations"]:
            print(f"  - {h}")
