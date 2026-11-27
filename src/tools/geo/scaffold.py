#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段二：SaaS 交钥匙静态官网与大模型抓取底座编译引擎 (tools/geo/scaffold.py)
基于 templates/baicl-saas/index.html.tmpl 统一母版编译纯静态站点，
严格遵循有资料即渲染、无资料直接留白、零假数据、零 Emoji 与 custom_site 防覆盖保护。
"""

import argparse
import html
import json
import os
import re
import shutil
import sys
import time
from typing import Any, Dict, List, Optional

from . import utils as _utils
from .utils import coerce_bool, load_project_config

PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
ALLOWED_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MASTER_TEMPLATE_PATH = os.path.join(
    _utils.PROJECT_ROOT, "templates", "baicl-saas", "index.html.tmpl"
)


def _log(msg: str) -> None:
    print(msg)


def _esc(val: Any) -> str:
    return html.escape(str(val or ""), quote=True)


def _projects_base_dir() -> str:
    return os.path.realpath(_utils.PROJECTS_DIR)


def _validate_project_id(project_id: str) -> str:
    pid = str(project_id or "").strip()
    if not pid or not PROJECT_ID_RE.match(pid):
        raise ValueError(f"非法 project_id: {project_id}")
    base = _projects_base_dir()
    target = os.path.realpath(os.path.join(base, pid))
    if not target.startswith(base + os.sep):
        raise ValueError(f"非法 project_id 路径越界: {project_id}")
    return pid


def _apply_override_aliases(raw: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(raw)
    alias_pairs = (
        ("company_name", ("name", "client_name")),
        ("slogan", ("one_liner", "business_one_liner")),
        ("telephone", ("contact_phone", "phone")),
        ("official_url", ("domain",)),
        ("industry", ("category",)),
        ("area_served", ("target_audience",)),
        ("keywords", ("expected_queries",)),
        ("wechat_qr_file", ("wechat_qr",)),
    )
    for primary, fallbacks in alias_pairs:
        if not str(out.get(primary) or "").strip():
            for alt in fallbacks:
                val = out.get(alt)
                if val is not None and str(val).strip():
                    out[primary] = val
                    break
    return out


def _merge_config_overrides(
    project_id: str, cfg: dict, overrides: Optional[Dict[str, Any]]
) -> dict:
    merged = dict(cfg)
    if isinstance(overrides, dict) and overrides:
        normalized = _apply_override_aliases(overrides)
        for key, val in normalized.items():
            if val is None:
                continue
            if key == "custom_site":
                if coerce_bool(val):
                    merged["custom_site"] = True
                continue
            if isinstance(val, bool):
                merged[key] = val
            elif isinstance(val, str):
                if val.strip():
                    merged[key] = val.strip()
            elif isinstance(val, (list, dict)) and len(val) > 0:
                merged[key] = val

    company = str(merged.get("company_name") or merged.get("client_name") or "").strip()
    brand = str(merged.get("brand_name") or "").strip()
    if not brand and company:
        brand = company
    if not company and brand:
        company = brand
    if not company and not brand:
        company = project_id
        brand = project_id
    merged["company_name"] = company
    merged["brand_name"] = brand
    return merged


def _resolve_canonical_url(project_id: str, cfg: dict) -> str:
    raw = str(cfg.get("official_url") or "").strip()
    if not raw:
        return f"https://claw.baicl.cc/{project_id}/"
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw.lstrip("/")
    return raw.rstrip("/") + "/"


def _resolve_safe_image_asset(
    project_id: str, site_dir: str, raw_path: str, target_stem: str
) -> str:
    """统一校验图片路径（realpath 限定在 raw_materials/ 或 outputs/site/assets/ 内且白名单后缀）并安全复制到 assets/。"""
    cleaned = str(raw_path or "").strip()
    if not cleaned or ".." in cleaned.replace("\\", "/").split("/"):
        return ""
    if re.match(r"^(?:https?:|//|data:|javascript:)", cleaned, re.I):
        return ""

    pid = _validate_project_id(project_id)
    project_dir = os.path.join(_projects_base_dir(), pid)
    allowed_raw = os.path.realpath(os.path.join(project_dir, "raw_materials"))
    allowed_assets = os.path.realpath(os.path.join(site_dir, "assets"))

    if os.path.isabs(cleaned):
        cand = cleaned
    elif cleaned.startswith("assets/"):
        cand = os.path.join(site_dir, cleaned)
    elif cleaned.startswith(("raw_materials/", "outputs/")):
        cand = os.path.join(project_dir, cleaned)
    else:
        cand = os.path.join(project_dir, cleaned)
        if not os.path.exists(cand):
            cand = os.path.join(allowed_raw, cleaned)

    real_src = os.path.realpath(cand)
    in_raw = real_src.startswith(allowed_raw + os.sep)
    in_assets = real_src.startswith(allowed_assets + os.sep)
    if not (in_raw or in_assets) or not os.path.isfile(real_src):
        return ""

    ext = os.path.splitext(real_src)[1].lower()
    if ext not in ALLOWED_LOGO_EXTS:
        return ""

    os.makedirs(allowed_assets, exist_ok=True)
    if in_assets:
        return os.path.relpath(real_src, os.path.realpath(site_dir)).replace(os.sep, "/")

    dst_name = f"{target_stem}{ext}"
    for old_ext in ALLOWED_LOGO_EXTS:
        stale = os.path.join(allowed_assets, f"{target_stem}{old_ext}")
        if old_ext != ext and os.path.isfile(stale):
            os.remove(stale)
    dst = os.path.join(allowed_assets, dst_name)
    if os.path.realpath(dst) != real_src:
        shutil.copy2(real_src, dst)
    return f"assets/{dst_name}"


def _normalize_business_items(raw: Any) -> List[Dict[str, str]]:
    if not isinstance(raw, list):
        return []
    items: List[Dict[str, str]] = []
    for entry in raw:
        if isinstance(entry, dict):
            name = str(entry.get("name") or entry.get("title") or "").strip()
            desc = str(entry.get("description") or entry.get("desc") or "").strip()
            cycle = str(entry.get("cycle") or "").strip()
            price = str(entry.get("price") or "").strip()
            if name or desc:
                items.append(
                    {"name": name or desc, "description": desc if name else "", "cycle": cycle, "price": price}
                )
        elif isinstance(entry, str) and entry.strip():
            items.append({"name": entry.strip(), "description": "", "cycle": "", "price": ""})
    return items


def _normalize_difference_items(cfg: dict) -> List[Dict[str, str]]:
    raw = cfg.get("differences") if cfg.get("differences") else cfg.get("core_values")
    if isinstance(raw, str):
        raw = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if not isinstance(raw, list):
        return []
    items: List[Dict[str, str]] = []
    for entry in raw:
        if isinstance(entry, dict):
            title = str(entry.get("title") or entry.get("name") or "").strip()
            desc = str(entry.get("description") or entry.get("desc") or "").strip()
            if title or desc:
                items.append({"title": title or desc, "description": desc if title else ""})
        elif isinstance(entry, str) and entry.strip():
            items.append({"title": entry.strip(), "description": ""})
    return items


def _normalize_faq_items(raw: Any) -> List[Dict[str, str]]:
    if not isinstance(raw, list):
        return []
    items: List[Dict[str, str]] = []
    for entry in raw:
        if isinstance(entry, dict):
            q = str(entry.get("question") or entry.get("q") or "").strip()
            a = str(entry.get("answer") or entry.get("a") or "").strip()
            if q and a:
                items.append({"question": q, "answer": a})
        elif isinstance(entry, str) and entry.strip():
            text = entry.strip()
            if "|" in text:
                q_part, a_part = text.split("|", 1)
                q, a = q_part.strip(), a_part.strip()
                if q and a:
                    items.append({"question": q, "answer": a})
    return items


def _append_llms_sections(lines: List[str], cfg: dict) -> None:
    biz_items = _normalize_business_items(cfg.get("core_business"))
    if biz_items:
        lines.extend(["", "## 核心业务"])
        for b in biz_items:
            extras = [x for x in (f"周期: {b['cycle']}" if b["cycle"] else "", f"报价: {b['price']}" if b["price"] else "") if x]
            suffix = f" ({', '.join(extras)})" if extras else ""
            desc_part = f": {b['description']}" if b["description"] else ""
            lines.append(f"- {b['name']}{desc_part}{suffix}")

    diff_items = _normalize_difference_items(cfg)
    if diff_items:
        lines.extend(["", "## 差异化优势"])
        for d in diff_items:
            desc_part = f"：{d['description']}" if d["description"] else ""
            lines.append(f"- {d['title']}{desc_part}")

    faq_items = _normalize_faq_items(cfg.get("faqs"))
    if faq_items:
        lines.extend(["", "## 常见问题 (FAQ)"])
        for fq in faq_items:
            lines.append(f"- Q: {fq['question']}")
            lines.append(f"  A: {fq['answer']}")


def build_llms_txt(cfg: dict, canonical_url: str = "") -> str:
    company = str(cfg.get("company_name") or cfg.get("client_name") or "").strip()
    brand = str(cfg.get("brand_name") or company).strip()
    person = str(cfg.get("contact_person") or cfg.get("founder") or "").strip()
    site_url = canonical_url or _resolve_canonical_url(str(cfg.get("client_id") or "site"), cfg)
    heading = f"# {brand}" if brand == company else f"# {brand} ({company})"
    lines = [heading, ""]

    summary = str(
        cfg.get("nameplate") or cfg.get("company_profile") or cfg.get("slogan") or cfg.get("business_one_liner") or ""
    ).strip()
    if summary:
        lines.extend([f"> {summary}", ""])

    lines.append("## 企业基础信息")
    meta_pairs = (
        ("企业名称", company),
        ("品牌名称", brand if brand != company else ""),
        ("所属行业", str(cfg.get("industry") or "").strip()),
        ("服务区域", str(cfg.get("area_served") or "").strip()),
        ("联系人", person),
        ("联系电话", str(cfg.get("telephone") or "").strip()),
        ("联系微信", str(cfg.get("wechat") or "").strip()),
        ("联系地址", str(cfg.get("address") or "").strip()),
        ("官方网址", site_url),
    )
    for label, val in meta_pairs:
        if val:
            lines.append(f"- {label}: {val}")

    _append_llms_sections(lines, cfg)
    return "\n".join(lines).rstrip() + "\n"


def _build_org_node(cfg: dict, site_url: str, logo_rel: str) -> Dict[str, Any]:
    company = str(cfg.get("company_name") or cfg.get("client_name") or "").strip()
    brand = str(cfg.get("brand_name") or company).strip()
    org: Dict[str, Any] = {
        "@type": "Organization",
        "@id": f"{site_url}#organization",
        "name": brand or company,
        "url": site_url,
    }
    if company and company != brand:
        org["legalName"] = company
    desc = str(cfg.get("company_profile") or cfg.get("slogan") or cfg.get("business_one_liner") or "").strip()
    if desc:
        org["description"] = desc
    if logo_rel:
        org["logo"] = f"{site_url}{logo_rel.lstrip('/')}"
    telephone = str(cfg.get("telephone") or "").strip()
    if telephone:
        org["telephone"] = telephone
    area = str(cfg.get("area_served") or "").strip()
    if area:
        org["areaServed"] = area
    address = str(cfg.get("address") or "").strip()
    if address:
        org["address"] = {"@type": "PostalAddress", "streetAddress": address, "addressCountry": "CN"}
    person = str(cfg.get("contact_person") or cfg.get("founder") or "").strip()
    if person:
        p_node: Dict[str, Any] = {"@type": "Person", "name": person}
        ftitle = str(cfg.get("founder_title") or "").strip()
        if ftitle:
            p_node["jobTitle"] = ftitle
        org["founder"] = p_node
    if person or telephone:
        cp: Dict[str, Any] = {"@type": "ContactPoint", "contactType": "sales"}
        if person:
            cp["name"] = person
        if telephone:
            cp["telephone"] = telephone
        org["contactPoint"] = cp
    return org


def build_json_ld(cfg: dict, canonical_url: str = "", logo_rel: str = "") -> str:
    site_url = canonical_url or _resolve_canonical_url(str(cfg.get("client_id") or "site"), cfg)
    company = str(cfg.get("company_name") or cfg.get("client_name") or "").strip()
    brand = str(cfg.get("brand_name") or company).strip()

    graph: List[Dict[str, Any]] = [
        _build_org_node(cfg, site_url, logo_rel),
        {
            "@type": "WebSite",
            "@id": f"{site_url}#website",
            "url": site_url,
            "name": brand or company,
            "publisher": {"@id": f"{site_url}#organization"},
        },
    ]

    for idx, biz in enumerate(_normalize_business_items(cfg.get("core_business")), start=1):
        svc: Dict[str, Any] = {
            "@type": "Service",
            "@id": f"{site_url}#service-{idx}",
            "name": biz["name"],
            "provider": {"@id": f"{site_url}#organization"},
        }
        if biz["description"]:
            svc["description"] = biz["description"]
        graph.append(svc)

    faq_items = _normalize_faq_items(cfg.get("faqs"))
    if faq_items:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{site_url}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": fq["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": fq["answer"]},
                    }
                    for fq in faq_items
                ],
            }
        )

    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)


def build_robots_txt(cfg: dict, canonical_url: str = "") -> str:
    site_url = canonical_url or _resolve_canonical_url(str(cfg.get("client_id") or "site"), cfg)
    lines = [
        "# robots.txt for AI Search Crawlers",
        "User-agent: Bytespider",
        "Allow: /",
        "",
        "User-agent: Baiduspider",
        "Allow: /",
        "",
        "User-agent: Sogouspider",
        "Allow: /",
        "",
        "User-agent: Yisouspider",
        "Allow: /",
        "",
        "User-agent: DeepSeekBot",
        "Allow: /",
        "",
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {site_url}sitemap.xml",
    ]
    return "\n".join(lines) + "\n"


def build_sitemap_xml(canonical_url: str) -> str:
    today = time.strftime("%Y-%m-%d")
    loc = _esc(canonical_url)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{today}</lastmod>\n"
        "    <changefreq>weekly</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "  </url>\n"
        "</urlset>\n"
    )


def _render_header_and_hero_slots(cfg: dict, logo_rel: str) -> Dict[str, str]:
    brand = str(cfg.get("brand_name") or cfg.get("company_name") or "").strip()
    telephone = str(cfg.get("telephone") or "").strip()
    wechat = str(cfg.get("wechat") or "").strip()
    industry = str(cfg.get("industry") or "").strip()
    area = str(cfg.get("area_served") or "").strip()
    slogan = str(cfg.get("slogan") or cfg.get("business_one_liner") or "").strip()
    profile = str(cfg.get("company_profile") or "").strip()

    nav_logo = (
        f'<img src="{_esc(logo_rel)}" alt="{_esc(brand)}" class="saas-brand-logo">'
        if logo_rel
        else ""
    )
    if telephone:
        nav_cta = f'<a href="tel:{_esc(telephone)}" class="saas-btn saas-btn-sm saas-btn-primary">电话咨询：{_esc(telephone)}</a>'
    elif wechat:
        nav_cta = f'<a href="#contact-cta" class="saas-btn saas-btn-sm saas-btn-primary">微信咨询：{_esc(wechat)}</a>'
    else:
        nav_cta = ""

    badge_text = " · ".join([p for p in (industry, area) if p])
    hero_badge = (
        f'<div class="saas-badge"><span class="saas-badge-dot"></span><span>{_esc(badge_text)}</span></div>'
        if badge_text
        else ""
    )
    hero_slogan = f'<p class="saas-hero-slogan">{_esc(slogan)}</p>' if slogan else ""
    hero_profile = f'<div class="saas-hero-card"><p>{_esc(profile)}</p></div>' if profile else ""

    btns: List[str] = []
    if telephone:
        btns.append(f'<a href="tel:{_esc(telephone)}" class="saas-btn saas-btn-primary">致电咨询：{_esc(telephone)}</a>')
    if wechat:
        btns.append(f'<a href="#contact-cta" class="saas-btn saas-btn-secondary">联系微信：{_esc(wechat)}</a>')
    hero_actions = f'<div class="saas-hero-actions">{"".join(btns)}</div>' if btns else ""

    return {
        "NAV_LOGO_HTML": nav_logo,
        "NAV_CTA_HTML": nav_cta,
        "HERO_BADGE_HTML": hero_badge,
        "HERO_SLOGAN_HTML": hero_slogan,
        "HERO_PROFILE_HTML": hero_profile,
        "HERO_ACTIONS_HTML": hero_actions,
    }


def _render_services_section(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    grid_cls = "saas-grid-2" if len(items) <= 2 else "saas-grid-3"
    cards: List[str] = []
    for idx, item in enumerate(items, start=1):
        desc_html = f'<p class="saas-card-desc">{_esc(item["description"])}</p>' if item["description"] else ""
        metas: List[str] = []
        if item["cycle"]:
            metas.append(f'<span>交付周期：{_esc(item["cycle"])}</span>')
        if item["price"]:
            metas.append(f'<span>参考报价：{_esc(item["price"])}</span>')
        meta_html = f'<div class="saas-card-meta">{"".join(metas)}</div>' if metas else ""
        cards.append(
            '<article class="saas-card saas-card-tint">'
            f'<div><span class="saas-card-tag">SERVICE {idx:02d}</span>'
            f'<h3 class="saas-card-title">{_esc(item["name"])}</h3>{desc_html}</div>'
            f"{meta_html}</article>"
        )
    return (
        '<section id="services" class="saas-section saas-section-white">'
        '<div class="geo-container">'
        '<div class="saas-section-head">'
        '<p class="saas-eyebrow">Core Services</p>'
        '<h2 class="saas-h2">核心业务与产品服务</h2>'
        "</div>"
        f'<div class="{grid_cls}">{"".join(cards)}</div>'
        "</div></section>"
    )


def _render_differences_section(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    grid_cls = "saas-grid-2" if len(items) % 2 == 0 or len(items) <= 2 else "saas-grid-3"
    cards: List[str] = []
    for idx, item in enumerate(items, start=1):
        desc_html = f'<p class="saas-card-desc">{_esc(item["description"])}</p>' if item["description"] else ""
        cards.append(
            '<article class="saas-card">'
            f'<div><span class="saas-card-tag">ADVANTAGE {idx:02d}</span>'
            f'<h3 class="saas-card-title">{_esc(item["title"])}</h3>{desc_html}</div>'
            "</article>"
        )
    return (
        '<section id="advantages" class="saas-section saas-section-tint">'
        '<div class="geo-container">'
        '<div class="saas-section-head">'
        '<p class="saas-eyebrow">Core Advantages</p>'
        '<h2 class="saas-h2">差异化优势与服务保障</h2>'
        "</div>"
        f'<div class="{grid_cls}">{"".join(cards)}</div>'
        "</div></section>"
    )


def _render_faq_section(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    rows: List[str] = []
    for idx, fq in enumerate(items, start=1):
        q_text = fq["question"]
        prefix = "" if re.match(r"^Q\d+[：:]", q_text, re.I) else f"Q{idx}："
        rows.append(
            '<article class="saas-faq-item">'
            f'<h3 class="saas-faq-q">{_esc(prefix + q_text)}</h3>'
            f'<p class="saas-faq-a">{_esc(fq["answer"])}</p>'
            "</article>"
        )
    return (
        '<section id="faq" class="saas-section saas-section-white">'
        '<div class="geo-container">'
        '<div class="saas-section-head">'
        '<p class="saas-eyebrow">FAQ</p>'
        '<h2 class="saas-h2">常见问题解答</h2>'
        "</div>"
        f'<div class="saas-faq-list">{"".join(rows)}</div>'
        "</div></section>"
    )


def _render_cta_section(cfg: dict, qr_rel: str) -> str:
    brand = str(cfg.get("brand_name") or cfg.get("company_name") or "").strip()
    person = str(cfg.get("contact_person") or cfg.get("founder") or "").strip()
    telephone = str(cfg.get("telephone") or "").strip()
    wechat = str(cfg.get("wechat") or "").strip()
    if not (person or telephone or wechat or qr_rel):
        return ""

    title = f"业务合作咨询，直接联系{_esc(person)}" if person else f"欢迎联系{_esc(brand)}沟通需求"
    desc = f"欢迎就产品选型、技术方案与合作细节与{_esc(person or brand)}直接对接。"
    meta_parts: List[str] = []
    if person:
        meta_parts.append(f'<span><span class="saas-cta-meta-dot"></span> 直连负责人：{_esc(person)}</span>')
    if telephone:
        meta_parts.append(f"<span>电话：{_esc(telephone)}</span>")
    if wechat:
        meta_parts.append(f"<span>微信：{_esc(wechat)}</span>")
    meta_html = f'<div class="saas-cta-meta">{"<span>·</span>".join(meta_parts)}</div>' if meta_parts else ""

    side_parts: List[str] = []
    if qr_rel:
        alt_label = f"{person or brand}微信二维码"
        side_parts.append(
            f'<div class="saas-qr-box"><img src="{_esc(qr_rel)}" alt="{_esc(alt_label)}" class="saas-qr-img"></div>'
        )
    if telephone:
        side_parts.append(f'<a href="tel:{_esc(telephone)}" class="saas-cta-btn">一键拨打咨询：{_esc(telephone)}</a>')
    if wechat:
        side_parts.append(f'<div class="saas-cta-wechat-hint">微信号：{_esc(wechat)}</div>')
    elif qr_rel:
        side_parts.append('<div class="saas-cta-wechat-hint">微信扫码直接沟通</div>')
    side_html = f'<div class="saas-cta-side">{"".join(side_parts)}</div>' if side_parts else ""

    return (
        '<section id="contact-cta" class="saas-cta-wrap">'
        '<div class="geo-container"><div class="saas-cta-card">'
        '<div class="saas-cta-glow-tr"></div><div class="saas-cta-glow-bl"></div>'
        '<div class="saas-cta-grid">'
        f'<div><p class="saas-cta-eyebrow">Get Started</p><h2 class="saas-cta-title">{title}</h2>'
        f'<p class="saas-cta-desc">{desc}</p>{meta_html}</div>'
        f"{side_html}</div></div></div></section>"
    )


def _render_footer_slots(cfg: dict, logo_rel: str, qr_rel: str = "") -> Dict[str, str]:
    brand = str(cfg.get("brand_name") or cfg.get("company_name") or "").strip()
    person = str(cfg.get("contact_person") or cfg.get("founder") or "").strip()
    founder_title = str(cfg.get("founder_title") or "").strip()
    telephone = str(cfg.get("telephone") or "").strip()
    wechat = str(cfg.get("wechat") or "").strip()
    address = str(cfg.get("address") or "").strip()
    area = str(cfg.get("area_served") or "").strip()

    footer_logo = (
        f'<img src="{_esc(logo_rel)}" alt="{_esc(brand)}" class="saas-brand-logo">'
        if logo_rel
        else ""
    )
    lines: List[str] = []
    if person:
        p_label = f"{person}（{founder_title}）" if founder_title else person
        lines.append(f"<div>联系人：{_esc(p_label)}</div>")
    if telephone:
        lines.append(f'<div>电话：<a href="tel:{_esc(telephone)}">{_esc(telephone)}</a></div>')
    if wechat:
        lines.append(f"<div>微信：{_esc(wechat)}</div>")
    if address:
        lines.append(f"<div>地址：{_esc(address)}</div>")
    elif area:
        lines.append(f"<div>服务区域：{_esc(area)}</div>")

    if person:
        contact_link = f'<a href="#contact-cta">联系{_esc(person)}</a><span class="saas-dot">·</span>'
    elif telephone or wechat or qr_rel:
        contact_link = '<a href="#contact-cta">联系我们</a><span class="saas-dot">·</span>'
    else:
        contact_link = ""

    footer_contact = f'<div class="saas-footer-contact">{"".join(lines)}</div>' if lines else ""
    return {
        "FOOTER_LOGO_HTML": footer_logo,
        "FOOTER_CONTACT_HTML": footer_contact,
        "FOOTER_CONTACT_LINK_HTML": contact_link,
        "FOOTER_YEAR": time.strftime("%Y"),
    }


def build_turnkey_site_html(
    cfg: dict,
    json_ld_str: str,
    canonical_url: str = "",
    logo_rel: str = "",
    qr_rel: str = "",
    template_path: str = "",
) -> str:
    tmpl_file = template_path or MASTER_TEMPLATE_PATH
    with open(tmpl_file, "r", encoding="utf-8") as f:
        html_out = f.read()

    site_url = canonical_url or _resolve_canonical_url(str(cfg.get("client_id") or "site"), cfg)
    company = str(cfg.get("company_name") or cfg.get("client_name") or "").strip()
    brand = str(cfg.get("brand_name") or company).strip()
    page_title = f"{brand} - {company}" if (brand and company and brand != company) else (brand or company)
    meta_desc = str(
        cfg.get("company_profile") or cfg.get("business_one_liner") or cfg.get("slogan") or company
    ).strip()
    json_ld_script = (
        f'<script type="application/ld+json">\n{json_ld_str}\n  </script>'
        if (json_ld_str or "").strip()
        else ""
    )

    slots: Dict[str, str] = {
        "PAGE_TITLE": _esc(page_title),
        "META_DESCRIPTION": _esc(meta_desc),
        "CANONICAL_URL": _esc(site_url),
        "JSON_LD_SCRIPT": json_ld_script,
        "BRAND_NAME": _esc(brand),
        "COMPANY_NAME": _esc(company),
        "SERVICES_SECTION_HTML": _render_services_section(_normalize_business_items(cfg.get("core_business"))),
        "DIFFERENCES_SECTION_HTML": _render_differences_section(_normalize_difference_items(cfg)),
        "FAQ_SECTION_HTML": _render_faq_section(_normalize_faq_items(cfg.get("faqs"))),
        "CTA_SECTION_HTML": _render_cta_section(cfg, qr_rel),
    }
    slots.update(_render_header_and_hero_slots(cfg, logo_rel))
    slots.update(_render_footer_slots(cfg, logo_rel, qr_rel=qr_rel))

    for key, val in slots.items():
        html_out = html_out.replace("{{" + key + "}}", val)
    return html_out


def _write_site_and_root(
    out_dir: str, site_dir: str, filename: str, content: str, *, is_custom: bool, protect: bool = True
) -> bool:
    site_path = os.path.join(site_dir, filename)
    root_path = os.path.join(out_dir, filename)
    if protect and is_custom and os.path.exists(site_path):
        _log(f"[PROTECTED] custom_site=true，跳过覆盖已存在的 outputs/site/{filename}")
        return False
    with open(site_path, "w", encoding="utf-8") as f:
        f.write(content)
    if not (protect and is_custom and os.path.exists(root_path)):
        with open(root_path, "w", encoding="utf-8") as f:
            f.write(content)
    return True


def _build_delivery_doc(project_id: str, cfg: dict, canonical_url: str, preview_public: bool) -> str:
    company = cfg.get("company_name") or project_id
    state_label = "已开启" if preview_public else "已关闭（默认返回 404）"
    return (
        "# 02_站点技术底座改造交付包\n\n"
        f"- **客户项目**：{company} (`{project_id}`)\n"
        f"- **正式/目标网址**：{canonical_url}\n"
        f"- **路径预览地址**：`https://claw.baicl.cc/{project_id}/`（当前公网状态：{state_label}）\n\n"
        "## 静态产物清单 (`outputs/site/`)\n\n"
        "| 文件名 | 用途说明 |\n"
        "|---|---|\n"
        "| `index.html` | 基于 `www.baicl.cc` 统一母版编译的纯静态官网，内联防御性 CSS 且全站使用相对路径 |\n"
        "| `llms.txt` | 面向主流大模型爬虫的结构化 Markdown 实体与业务说明书 |\n"
        "| `schema.jsonld` | Schema.org JSON-LD 权威实体图谱元数据 |\n"
        "| `robots.txt` | 显式放行 Bytespider、DeepSeekBot 等主流 AI 爬虫规则 |\n"
        "| `sitemap.xml` | 标准 XML 站点地图索引 |\n"
    )


def is_preview_public(project_id: str) -> bool:
    pid = _validate_project_id(project_id)
    sentinel = os.path.join(_projects_base_dir(), pid, "outputs", "site", ".published")
    return os.path.isfile(sentinel)


def set_preview_public(project_id: str, enabled: bool) -> Dict[str, Any]:
    """无状态切换 claw.baicl.cc/{project_id}/ 公网可见开关（创建或删除 .published 哨兵文件）。"""
    pid = _validate_project_id(project_id)
    site_dir = os.path.join(_projects_base_dir(), pid, "outputs", "site")
    sentinel = os.path.join(site_dir, ".published")
    flag = coerce_bool(enabled)
    if flag:
        os.makedirs(site_dir, exist_ok=True)
        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(sentinel, "w", encoding="utf-8") as f:
            f.write(f"published_at: {now_utc}\n")
    elif os.path.exists(sentinel):
        os.remove(sentinel)
    return {
        "project_id": pid,
        "preview_public": flag,
        "sentinel_path": sentinel,
        "preview_url": f"https://claw.baicl.cc/{pid}/",
    }


def _check_narrative_warnings(cfg: dict) -> None:
    from .nameplate import check_nameplate_quartet, check_shell_narrative

    np = check_nameplate_quartet(cfg)
    for w in np.get("warnings") or []:
        _log(f"[WARN] 名片段检查：{w}")
    for risk in check_shell_narrative(
        cfg.get("nameplate"),
        cfg.get("company_profile"),
        cfg.get("slogan"),
        cfg.get("business_one_liner"),
    ):
        _log(f"[WARN] 叙事边界提醒：{risk}")


def _compile_site_files(
    cfg: dict, out_dir: str, site_dir: str, canonical_url: str, logo_rel: str, qr_rel: str, is_custom: bool
) -> None:
    llms_txt = build_llms_txt(cfg, canonical_url=canonical_url)
    _write_site_and_root(out_dir, site_dir, "llms.txt", llms_txt, is_custom=is_custom)

    schema_path = os.path.join(site_dir, "schema.jsonld")
    if is_custom and os.path.exists(schema_path):
        _log("[PROTECTED] custom_site=true，跳过覆盖已存在的 outputs/site/schema.jsonld")
        with open(schema_path, "r", encoding="utf-8") as f:
            json_ld = f.read()
    else:
        json_ld = build_json_ld(cfg, canonical_url=canonical_url, logo_rel=logo_rel)
        _write_site_and_root(out_dir, site_dir, "schema.jsonld", json_ld, is_custom=False)

    robots_txt = build_robots_txt(cfg, canonical_url=canonical_url)
    _write_site_and_root(out_dir, site_dir, "robots.txt", robots_txt, is_custom=is_custom, protect=False)

    sitemap_xml = build_sitemap_xml(canonical_url)
    _write_site_and_root(out_dir, site_dir, "sitemap.xml", sitemap_xml, is_custom=is_custom)

    site_index = os.path.join(site_dir, "index.html")
    if is_custom and os.path.exists(site_index):
        _log("[PROTECTED] custom_site=true，跳过覆盖已存在的 outputs/site/index.html 与定制子目录")
    else:
        site_html = build_turnkey_site_html(
            cfg, json_ld, canonical_url=canonical_url, logo_rel=logo_rel, qr_rel=qr_rel
        )
        _write_site_and_root(out_dir, site_dir, "index.html", site_html, is_custom=is_custom)


def run_scaffold(
    project_id: str,
    overrides: Optional[Dict[str, Any]] = None,
    publish_preview: Optional[bool] = None,
) -> Dict[str, Any]:
    """编译客户 SaaS 静态官网与大模型抓取五件套，支持内存覆盖参数与预览公网开关。"""
    pid = _validate_project_id(project_id)
    base_cfg = load_project_config(pid, projects_dir=_projects_base_dir())
    cfg = _merge_config_overrides(pid, base_cfg, overrides)
    out_dir = cfg["_outputs_dir"]
    site_dir = os.path.join(out_dir, "site")
    os.makedirs(site_dir, exist_ok=True)

    _check_narrative_warnings(cfg)
    is_custom = coerce_bool(cfg.get("custom_site", False))
    canonical_url = _resolve_canonical_url(pid, cfg)

    raw_logo = str(cfg.get("logo_file") or cfg.get("logo") or "").strip()
    raw_qr = str(cfg.get("wechat_qr_file") or cfg.get("wechat_qr") or "").strip()
    logo_rel = "" if is_custom else _resolve_safe_image_asset(pid, site_dir, raw_logo, "logo")
    qr_rel = "" if is_custom else _resolve_safe_image_asset(pid, site_dir, raw_qr, "wechat-qr")
    _compile_site_files(cfg, out_dir, site_dir, canonical_url, logo_rel, qr_rel, is_custom)

    if publish_preview is not None:
        set_preview_public(pid, publish_preview)
    public_now = is_preview_public(pid)

    doc_md = _build_delivery_doc(pid, cfg, canonical_url, public_now)
    with open(os.path.join(out_dir, "02_站点技术底座改造交付包.md"), "w", encoding="utf-8") as f:
        f.write(doc_md)

    return {
        "project_id": pid,
        "site_dir": site_dir,
        "canonical_url": canonical_url,
        "custom_site": is_custom,
        "preview_public": public_now,
        "preview_url": f"https://claw.baicl.cc/{pid}/",
        "files": ["index.html", "llms.txt", "schema.jsonld", "robots.txt", "sitemap.xml"],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="GEO SaaS 静态官网编译与预览公网开关工具")
    parser.add_argument("project_id", help="客户项目标识")
    parser.add_argument(
        "--preview",
        choices=["on", "off", "status"],
        default=None,
        help="仅切换或查询 claw.baicl.cc/{project_id}/ 公网访问开关（不重新编译页面）",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--publish", action="store_true", help="编译完成后开启公网预览")
    group.add_argument("--unpublish", action="store_true", help="编译完成后关闭公网预览")
    args = parser.parse_args(argv)

    if args.preview == "status":
        state = "on" if is_preview_public(args.project_id) else "off"
        _log(f"[PREVIEW] {args.project_id}: {state} (https://claw.baicl.cc/{args.project_id}/)")
        return 0
    if args.preview in ("on", "off"):
        res = set_preview_public(args.project_id, args.preview == "on")
        _log(f"[PREVIEW] {res['project_id']}: preview_public={res['preview_public']} ({res['preview_url']})")
        return 0

    pub_flag: Optional[bool] = True if args.publish else (False if args.unpublish else None)
    res = run_scaffold(args.project_id, publish_preview=pub_flag)
    _log(f"[OK] 站点已生成: {res['site_dir']} (preview_public={res['preview_public']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
