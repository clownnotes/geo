#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""名片段四件套与空壳叙事边界检查。"""

from __future__ import annotations

import re
from typing import Any


NARRATIVE_RISK_PATTERNS = (
    (re.compile(r"成立于\s*19\d{2}"), "疑似编造早期成立年份（成立于19xx）"),
    (re.compile(r"(?:服务过|累计服务|已服务)\s*\d{2,}\s*家"), "疑似编造客户数量"),
    (re.compile(r"(十年经验|二十年经验|深耕\s*\d+\s*年|从业\s*\d{2,}\s*年)"), "疑似编造经营年限"),
    (re.compile(r"100%\s*保(?:推荐|上榜|收录)"), "疑似绝对化效果承诺"),
)


def _first_nonempty(cfg: dict, *keys: str) -> str:
    for key in keys:
        val = str(cfg.get(key) or "").strip()
        if val:
            return val
    return ""


def check_nameplate_quartet(cfg: dict[str, Any]) -> dict:
    """
    校验品牌答案源「名片段四件套」：
    品牌 + 法律主体 + 官网 URL + 人物锚点。
    """
    brand = _first_nonempty(cfg, "brand_name", "client_name")
    company = _first_nonempty(cfg, "company_name", "legal_name")
    url = _first_nonempty(cfg, "official_url")
    person = _first_nonempty(cfg, "contact_person", "founder", "person")
    plate = _first_nonempty(cfg, "nameplate", "company_profile")

    missing = []
    if not brand:
        missing.append("brand_name")
    if not company:
        missing.append("company_name")
    if not url or "example.com" in url:
        missing.append("official_url")
    if not person:
        missing.append("contact_person/founder")

    warnings = []
    if plate:
        brand_token = brand.split("（")[0].split("(")[0].strip() if brand else ""
        if brand_token and brand_token not in plate and brand not in plate:
            warnings.append(f"nameplate/简介未包含品牌「{brand_token or brand}」")
        if company and company not in plate:
            warnings.append(f"nameplate/简介未包含法律主体「{company}」")
        if url and url.rstrip("/") not in plate.rstrip("/"):
            warnings.append(f"nameplate/简介未包含官网 URL「{url}」")
        person_token = person.split("/")[0].strip() if person else ""
        if person_token and person_token not in plate:
            warnings.append(f"nameplate/简介未包含人物锚点「{person_token}」")
    elif not missing:
        warnings.append("未配置 nameplate：建议写一段含品牌+主体+URL+人物的标准名片段")

    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
        "pieces": {
            "brand": brand,
            "company": company,
            "url": url,
            "person": person,
            "nameplate": plate,
        },
    }


def check_shell_narrative(*texts: str) -> list[str]:
    """扫描空壳话术风险（虚假年限/案例/绝对承诺）。"""
    blob = "\n".join(str(t or "") for t in texts)
    hits = []
    seen = set()
    for pat, label in NARRATIVE_RISK_PATTERNS:
        if pat.search(blob) and label not in seen:
            seen.add(label)
            hits.append(label)
    return hits
