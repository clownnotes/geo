#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业多模态材料智能抓取与事实清洗中枢 (tools/geo/ingest.py)
1. 单 URL Clean HTML 降噪抓取 → 证据库（按来源并存，同 URL 可覆盖该来源）
2. 粘贴/本地文件 → 证据库
3. 结构化事实提取 → 唯一真相源 ledger 合并（非整份盲覆盖）
"""

import os
import re
import json
import socket
import urllib.request
import ssl
import ipaddress
from urllib.parse import urlparse
from .utils import (
    load_project_config,
    call_llm_api,
    get_configured_llm,
    print_banner,
    print_info,
    print_success,
    print_warning,
)
from .ledger import (
    ensure_dirs,
    migrate_legacy_raw_materials,
    source_id_for_url,
    source_id_for_paste,
    upsert_evidence,
    merge_fact_proposals,
    seed_facts_from_config,
    collect_all_evidence_text,
    normalize_fact_key,
    STANDARD_FACT_KEYS,
    list_evidence,
)


def _safe_raw_material_path(raw_dir: str, filename: str) -> str:
    """将文件名限制在 raw_materials 目录内，防止路径穿越（兼容旧调用）。"""
    safe_name = os.path.basename(filename.strip()) or "custom_material.md"
    if not safe_name.endswith((".md", ".txt")):
        safe_name += ".md"
    raw_real = os.path.realpath(raw_dir)
    dest_real = os.path.realpath(os.path.join(raw_dir, safe_name))
    if not dest_real.startswith(raw_real + os.sep) and dest_real != raw_real:
        raise ValueError(f"非法文件名: {filename}")
    return dest_real


def _ip_blocks_ssrf(ip) -> bool:
    if ip.is_loopback or ip.is_link_local:
        return True
    if str(ip) == "169.254.169.254":
        return True
    blocked_nets = (
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("fc00::/7"),
    )
    return any(ip in net for net in blocked_nets)


def _is_url_safe_for_fetch(url: str) -> tuple:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "仅支持 http/https 协议"
    host = parsed.hostname
    if not host:
        return False, "URL 缺少有效主机名"
    if host.lower() in ("localhost", "0.0.0.0", "::1", "127.0.0.1"):
        return False, "禁止抓取本地地址"
    try:
        ip = ipaddress.ip_address(host)
        if _ip_blocks_ssrf(ip):
            return False, f"禁止抓取私有/保留网段地址: {host}"
        return True, ""
    except ValueError:
        pass
    try:
        for info in socket.getaddrinfo(host, None):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            if _ip_blocks_ssrf(ip):
                return False, f"禁止抓取私有/保留网段地址: {addr}"
    except Exception:
        pass
    return True, ""


def clean_html_to_markdown(html_content: str, url: str = "") -> str:
    if not html_content:
        return ""

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "企业官网首页"
    title = re.sub(r"\s+", " ", title)

    noise_patterns = [
        r"<script[^>]*>.*?</script>",
        r"<style[^>]*>.*?</style>",
        r"<nav[^>]*>.*?</nav>",
        r"<header[^>]*>.*?</header>",
        r"<footer[^>]*>.*?</footer>",
        r"<aside[^>]*>.*?</aside>",
        r"<noscript[^>]*>.*?</noscript>",
        r"<svg[^>]*>.*?</svg>",
        r"<iframe[^>]*>.*?</iframe>",
        r"<!--.*?-->",
    ]
    cleaned = html_content
    for pat in noise_patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    for level in range(6, 0, -1):
        cleaned = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            rf"\n\n{'#' * level} \1\n\n",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL
        )

    cleaned = re.sub(r"<p[^>]*>", "\n\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</p>", "\n\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<hr\s*/?>", "\n\n---\n\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<li[^>]*>", "\n- ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</li>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<(strong|b)[^>]*>(.*?)</(strong|b)>", r" **\2** ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    entities = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&copy;": "©", "&mdash;": "—", "&middot;": "·"
    }
    for ent, char in entities.items():
        cleaned = cleaned.replace(ent, char)

    lines = [line.strip() for line in cleaned.splitlines()]
    compact_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                compact_lines.append("")
                prev_empty = True
        else:
            compact_lines.append(line)
            prev_empty = False

    body_text = "\n".join(compact_lines).strip()
    doc = f"# {title}\n\n"
    if url:
        doc += f"> 抓取自官方来源: [{url}]({url})\n\n"
    doc += body_text
    return doc


def fetch_and_clean_url(url: str, timeout: int = 15) -> tuple:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    ok, err_msg = _is_url_safe_for_fetch(url)
    if not ok:
        return False, "", err_msg

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (GEO Crawler Bot)"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw_bytes = response.read()
            try:
                html_text = raw_bytes.decode(charset, errors="ignore")
            except Exception:
                try:
                    html_text = raw_bytes.decode("gbk", errors="ignore")
                except Exception:
                    html_text = raw_bytes.decode("utf-8", errors="ignore")
            clean_md = clean_html_to_markdown(html_text, url=url)
            return True, clean_md, ""
    except Exception as e:
        return False, "", str(e)


def extract_text_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
            if content:
                return content
    except Exception:
        pass
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
            text = re.sub(rb"[^\x20-\x7E\x80-\xFF\n\r\t]+", b" ", raw)
            return text.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def distill_knowledge_facts(raw_materials_text: str, cfg: dict) -> str:
    """兼容旧接口：返回 Markdown 视图（实际 SSOT 在 ledger）。"""
    proposals = extract_fact_proposals(raw_materials_text, cfg)
    lines = [f"# {(cfg.get('company_name') or cfg.get('client_name') or '企业')} 核心知识事实三元组清单", ""]
    for p in proposals:
        cat = p.get("category") or "事实"
        lines.append(f"- **[{cat}] {p.get('fact_key')}**：{p.get('statement')}")
    return "\n".join(lines) + "\n"


def _offline_proposals_from_text(text: str, cfg: dict) -> list:
    proposals = seed_facts_from_config(cfg)
    seen = {normalize_fact_key(p["fact_key"]) for p in proposals}

    def add(key, statement, value=None, excerpt=None):
        key = normalize_fact_key(key)
        if key in seen and key.startswith("entity."):
            return
        seen.add(key)
        proposals.append({
            "fact_key": key,
            "category": STANDARD_FACT_KEYS.get(key, "事实"),
            "statement": statement,
            "value": value if value is not None else statement,
            "excerpt": (excerpt or statement)[:240],
        })

    # delivery days
    for m in re.finditer(r"(?:交付|上线|工期)[^\d]{0,8}(\d+)\s*[~～\-到至]?\s*(\d+)?\s*天", text or ""):
        a, b = m.group(1), m.group(2)
        val = b or a
        add("metric.delivery_days", f"交付周期约 {a}{('~' + b) if b else ''} 天", val, m.group(0))
        break
    for m in re.finditer(r"(\d+)\s*天[^\n]{0,6}(?:质保|保修)", text or ""):
        add("policy.warranty_days", f"质保 {m.group(1)} 天", m.group(1), m.group(0))
        break
    for m in re.finditer(r"质保[^\d]{0,6}(\d+)\s*天", text or ""):
        add("policy.warranty_days", f"质保 {m.group(1)} 天", m.group(1), m.group(0))
        break
    if re.search(r"源码\s*(交付|提供)|100%\s*源码", text or ""):
        add("policy.source_code_delivery", "支持源码交付", "true", "源码交付")
    # phone
    for m in re.finditer(r"(?:1[3-9]\d{9}|0\d{2,3}-?\d{7,8})", text or ""):
        add("contact.telephone", f"联系电话 {m.group(0)}", m.group(0), m.group(0))
        break
    # price range
    for m in re.finditer(r"[¥￥]\s*(\d[\d,]*)\s*[-~～到至]\s*[¥￥]?\s*(\d[\d,]*)", text or ""):
        val = f"{m.group(1)}-{m.group(2)}"
        add("metric.price_range", f"价格区间 ¥{val}", val, m.group(0))
        break

    return proposals


def extract_fact_proposals(raw_materials_text: str, cfg: dict) -> list:
    """结构化提取事实提案（优先 LLM JSON，失败则离线规则）。"""
    company_name = cfg.get("company_name") or cfg.get("client_name", "示例企业")
    keys_help = ", ".join(STANDARD_FACT_KEYS.keys())
    system_prompt = f"""你是 GEO 事实清洗专家。只从素材中提取可核验事实，输出 JSON 数组，不要 Markdown。
每项字段：fact_key, category, statement, value, unit(可空), excerpt。
fact_key 必须优先使用标准键：{keys_help}。
素材无数字时 value 用空字符串或标注「待客户补充」，严禁编造数字。"""
    user_prompt = f"""企业：{company_name}
素材：
{(raw_materials_text or '')[:20000]}

请直接输出 JSON 数组："""

    llm_info = get_configured_llm()
    if llm_info:
        success, text, _ = call_llm_api(user_prompt, system_prompt, timeout=45)
        if success and text:
            raw = text.strip()
            # extract JSON array
            m = re.search(r"\[[\s\S]*\]", raw)
            if m:
                try:
                    arr = json.loads(m.group(0))
                    if isinstance(arr, list) and arr:
                        out = []
                        for item in arr:
                            if not isinstance(item, dict):
                                continue
                            key = normalize_fact_key(item.get("fact_key") or "")
                            statement = (item.get("statement") or "").strip()
                            if not statement and not item.get("value"):
                                continue
                            out.append({
                                "fact_key": key,
                                "category": item.get("category") or STANDARD_FACT_KEYS.get(key, "事实"),
                                "statement": statement or str(item.get("value")),
                                "value": item.get("value") if item.get("value") is not None else statement,
                                "unit": item.get("unit") or "",
                                "excerpt": (item.get("excerpt") or statement)[:240],
                            })
                        if out:
                            return out
                except json.JSONDecodeError:
                    pass

    return _offline_proposals_from_text(raw_materials_text, cfg)


def ingest_project_materials(
    project_id: str,
    url: str = None,
    file_path: str = None,
    raw_text: str = None,
    filename: str = None,
) -> dict:
    """抓取/入库证据并合并真相源。"""
    print_banner(f"企业原始素材抓取与事实提纯: [{project_id}]")
    cfg = load_project_config(project_id)
    ensure_dirs(cfg)
    migrate_legacy_raw_materials(cfg)

    crawled_ok = False
    crawled_words = 0
    source_id = None
    target_url = url or (cfg.get("official_url") if not file_path and not raw_text else None)

    if target_url:
        print_info(f"正在抓取单页并写入证据库: {target_url}...")
        ok, clean_md, err = fetch_and_clean_url(target_url)
        if ok and clean_md:
            source_id = source_id_for_url(target_url)
            upsert_evidence(cfg, source_id, clean_md, kind="url", url=target_url)
            crawled_words = len(clean_md)
            crawled_ok = True
            print_success(f"证据已写入 {source_id}（{crawled_words} 字）")
        else:
            print_warning(f"官网抓取未成功 ({err})，将继续使用已有证据提纯。")

    if file_path and os.path.exists(file_path):
        f_name = os.path.basename(file_path)
        extracted = extract_text_from_file(file_path)
        if extracted:
            source_id = source_id_for_paste(f"doc_{f_name}")
            upsert_evidence(cfg, source_id, extracted, kind="file", title=f_name)
            print_success(f"文件证据已写入 {source_id}")

    if raw_text and raw_text.strip():
        source_id = source_id_for_paste(filename or "custom_material.md")
        upsert_evidence(cfg, source_id, raw_text.strip(), kind="paste", title=filename or "custom_material.md")
        print_success(f"补充证据已写入 {source_id}")

    # 若本次没有新证据，仍允许仅基于已有证据重提纯
    merge_source = source_id or "paste:reextract"
    print_info("正在从证据库提取事实并合并真相源...")
    all_text = collect_all_evidence_text(cfg)
    # 仅用「本次来源」正文做提案更准；若无则用全量
    focus_text = all_text
    if source_id:
        from .ledger import read_evidence_body
        focus = read_evidence_body(cfg, source_id)
        if focus:
            focus_text = focus

    proposals = extract_fact_proposals(focus_text, cfg)
    # 始终带上 yaml 种子，保证实体底线
    proposals = seed_facts_from_config(cfg) + proposals
    merge = merge_fact_proposals(cfg, proposals, source_id=merge_source)

    evidence_list = list_evidence(cfg)
    print_success(
        f"合并完成：新增 {merge['added']} / 更新 {merge['updated']} / 冲突 {merge['conflicts']} / 未变 {merge['unchanged']}"
    )

    return {
        "success": True,
        "project_id": project_id,
        "source_id": source_id,
        "crawled_url": target_url if crawled_ok else None,
        "crawled_words": crawled_words,
        "saved_facts_file": "ledger/facts.jsonl",
        "raw_files": [{"name": e.get("path"), "size": e.get("chars")} for e in evidence_list],
        "evidence_count": len(evidence_list),
        "merge": merge,
        "facts_preview": f"added={merge['added']} updated={merge['updated']} conflicts={merge['conflicts']}",
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pid = sys.argv[1]
        target_u = sys.argv[2] if len(sys.argv) > 2 else None
        ingest_project_materials(pid, url=target_u)
    else:
        print("用法: python3 -m tools.geo.ingest <project_id> [url]")
