#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段一：客户现状体检与商业诊断器 (tools/geo/audit.py)

分层：
1. Python 真抓官网 → audit_metrics.json（技术真源）；
2. 可选小毛驴 / Nextdoor LLM 只写商业解读，禁止改写技术布尔与 tech_score；
3. 生成《企业 AI 可见度现状体检与商业诊断报告》。
"""

from __future__ import annotations

import json
import os
import re
import socket
import ssl
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .utils import (
    call_llm_api,
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
    save_project_output,
)

AUDIT_REPORT_FILE = "01_企业AI可见度现状体检与商业诊断报告.md"
AUDIT_METRICS_FILE = "audit_metrics.json"
LLM_TIMEOUT_SEC = 60


def _resolve_dualstack(host: str, port: int = 443) -> dict[str, list[str]]:
    """解析 A/AAAA，供自检；不做优选，原样暴露双栈情况。"""
    v4: list[str] = []
    v6: list[str] = []
    try:
        for family, _t, _p, _c, sockaddr in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            ip = sockaddr[0]
            if family == socket.AF_INET and ip not in v4:
                v4.append(ip)
            elif family == socket.AF_INET6 and ip not in v6:
                v6.append(ip)
    except socket.gaierror:
        pass
    return {"a": v4, "aaaa": v6}


def _probe_ip(host: str, ip: str, port: int = 443, timeout: float = 5.0) -> str:
    """探测单地址 TCP/TLS；返回 ok / 错误摘要。"""
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    sock = None
    try:
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port) if family == socket.AF_INET else (ip, port, 0, 0))
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            sock = None  # ownership transferred
            ssock.sendall(
                f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
            )
            _ = ssock.recv(64)
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


def fetch_url_content(url: str, user_agent: str = "Mozilla/5.0 (compatible; Bytespider/2.0)") -> tuple:
    """抓取网页内容，返回 (status_code, html_content, headers)。

    不强制 IPv4：系统解析顺序与双栈可达性原样暴露，便于发现官网/CDN IPv6 问题。
    """
    if not str(url).startswith(("http://", "https://")):
        url = "https://" + url
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            html = response.read().decode("utf-8", errors="ignore")
            return response.status, html, dict(response.headers)
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}", {}


def inspect_website(url: str) -> dict:
    """全面诊断目标网站的 AI 爬虫亲和度（纯 HTTP，无 LLM）。"""
    if not url.startswith("http"):
        url = "https://" + url

    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    dual = _resolve_dualstack(host) if host else {"a": [], "aaaa": []}
    dual_probe = {
        "a": {ip: _probe_ip(host, ip) for ip in dual["a"][:3]},
        "aaaa": {ip: _probe_ip(host, ip) for ip in dual["aaaa"][:3]},
    }

    status, html, _headers = fetch_url_content(url)

    results: dict[str, Any] = {
        "url": url,
        "is_online": status == 200,
        "status_code": status,
        "html_size_kb": round(len(html) / 1024, 2) if status == 200 else 0,
        "has_llms_txt": False,
        "has_json_ld": False,
        "has_ssr": False,
        "clean_text_length": 0,
        "text_density_ratio": 0.0,
        "robots_status": "未检测",
        "warnings": [],
        "dns": dual,
        "dualstack_probe": dual_probe,
    }

    # 双栈自检：有 AAAA 但本机全部连不上 → 明确告警（可能是本机无公网 IPv6，也可能是 CDN IPv6 未开通）
    if dual["aaaa"]:
        aaaa_ok = any(v == "ok" for v in dual_probe["aaaa"].values())
        a_ok = any(v == "ok" for v in dual_probe["a"].values()) if dual["a"] else False
        if not aaaa_ok:
            results["warnings"].append(
                "【双栈】DNS 已返回 AAAA，但本机无法用 IPv6 连上 443。"
                "若本机无公网 IPv6，属客户端限制；请用具备 IPv6 的网络复核，并确认 EdgeOne「IPv6 访问」已开启。"
                f" 探测={dual_probe['aaaa']}"
            )
        if dual["a"] and not a_ok and not aaaa_ok:
            results["warnings"].append("【双栈】本机 IPv4/IPv6 均无法 TLS 连通，站点或本地网络异常。")

    if status != 200:
        results["warnings"].append(f"站点无法正常访问或超时 (HTTP {status})，请核对域名。详情: {html[:180]}")
        return results

    clean_text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<style.*?</style>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<[^>]+>", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    results["clean_text_length"] = len(clean_text)
    if results["html_size_kb"] > 0:
        results["text_density_ratio"] = round(
            (len(clean_text) / (results["html_size_kb"] * 1024)) * 100, 2
        )

    is_csr_shell = bool(re.search(r'<div id=["\'](app|root|__next)["\']>\s*</div>', html))
    if is_csr_shell and len(clean_text) < 200:
        results["has_ssr"] = False
        results["warnings"].append(
            "【严重】检测到纯客户端 CSR 渲染（空壳挂载点）。大模型爬虫无法执行复杂 JS，将抓取为空白！"
        )
    else:
        results["has_ssr"] = True

    if 'type="application/ld+json"' in html or "application/ld+json" in html:
        results["has_json_ld"] = True
    else:
        results["warnings"].append(
            "【缺失】未检测到 Schema.org (JSON-LD) 结构化元数据，大模型无法直接提取实体属性。"
        )

    llms_url = url.rstrip("/") + "/llms.txt"
    llms_status, llms_text, _ = fetch_url_content(llms_url)
    if llms_status == 200 and len(llms_text) > 20:
        results["has_llms_txt"] = True
    else:
        results["warnings"].append(
            "【缺失】未部署 /llms.txt 规范索引，大模型无法毫秒级读取站点结构。"
        )

    robots_url = url.rstrip("/") + "/robots.txt"
    r_status, r_text, _ = fetch_url_content(robots_url)
    if r_status == 200:
        if "Bytespider" in r_text or "Baiduspider" in r_text or "Sogouspider" in r_text:
            results["robots_status"] = "已主动配置本土 AI 爬虫规则"
        else:
            results["robots_status"] = "标准通用配置（未明确放行 Bytespider）"
    else:
        results["robots_status"] = "未部署 robots.txt"

    return results


def compute_tech_score(audit_data: dict) -> int:
    """按真抓结果计算技术健康分（10～100）。"""
    if not audit_data.get("is_online"):
        return 10
    tech_score = 100
    if not audit_data.get("has_ssr", True):
        tech_score -= 40
    if not audit_data.get("has_llms_txt", False):
        tech_score -= 25
    if not audit_data.get("has_json_ld", False):
        tech_score -= 20
    if float(audit_data.get("text_density_ratio") or 0) < 15:
        tech_score -= 15
    return max(tech_score, 10)


def _normalize_list(raw) -> list[str]:
    if isinstance(raw, str):
        return [x.strip() for x in raw.split("\n") if x.strip()]
    if isinstance(raw, list):
        out = []
        for x in raw:
            s = str(x or "").strip()
            if s:
                out.append(s)
        return out
    return []


def load_probe_snapshot(cfg: dict) -> dict:
    """从 outputs 最新 competitor_probe_*.json 抽取可见度摘要（无假排名）。"""
    out_dir = cfg.get("_outputs_dir") or ""
    baseline_id = str(cfg.get("probe_baseline_id") or "").strip()
    empty = {
        "probe_baseline_id": baseline_id,
        "available": False,
        "items": [],
        "summary": {},
    }
    if not out_dir or not os.path.isdir(out_dir):
        return empty

    candidates = []
    for name in os.listdir(out_dir):
        if name.startswith("competitor_probe") and name.endswith(".json"):
            path = os.path.join(out_dir, name)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            candidates.append((mtime, path, name))
    if not candidates:
        return empty

    candidates.sort(key=lambda x: x[0], reverse=True)
    _mtime, path, name = candidates[0]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return empty

    items = []
    for it in data.get("items") or []:
        if not isinstance(it, dict):
            continue
        q = str(it.get("query") or "").strip()
        if not q:
            continue
        comps = it.get("competitors_extracted") or []
        names = []
        for c in comps:
            if isinstance(c, dict) and c.get("name"):
                names.append(str(c["name"]).strip())
            elif isinstance(c, str) and c.strip():
                names.append(c.strip())
        items.append(
            {
                "query": q,
                "mentioned_self": bool(it.get("mentioned_self")),
                "url_present": bool(it.get("url_present")),
                "standpoint": str(it.get("standpoint") or "").strip(),
                "hallucination_detected": bool(it.get("hallucination_detected")),
                "doubao_verdict": str(it.get("doubao_verdict") or "").strip(),
                "competitors": names[:8],
            }
        )

    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return {
        "probe_baseline_id": baseline_id or str(data.get("source_probe") or name),
        "available": bool(items),
        "probe_file": name,
        "items": items,
        "summary": {
            "brand_status": str(summary.get("brand_status") or "").strip(),
            "founder_status": str(summary.get("founder_status") or "").strip(),
            "self_mentioned_overall": summary.get("self_mentioned_overall"),
            "self_url_present_overall": summary.get("self_url_present_overall"),
        },
    }


def build_metrics(
    project_id: str,
    cfg: dict,
    audit_data: dict,
    *,
    probe_snap: dict | None = None,
    llm_status: str = "skipped",
    llm_provider: str = "none",
) -> dict:
    """组装并返回 audit_metrics 字典。"""
    probe_snap = probe_snap or {}
    tech_score = compute_tech_score(audit_data)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return {
        "project_id": project_id,
        "probed_at": now,
        "url": audit_data.get("url") or cfg.get("official_url") or "",
        "is_online": bool(audit_data.get("is_online")),
        "status_code": int(audit_data.get("status_code") or 0),
        "html_size_kb": float(audit_data.get("html_size_kb") or 0),
        "has_ssr": bool(audit_data.get("has_ssr")),
        "has_llms_txt": bool(audit_data.get("has_llms_txt")),
        "has_json_ld": bool(audit_data.get("has_json_ld")),
        "clean_text_length": int(audit_data.get("clean_text_length") or 0),
        "text_density_ratio": float(audit_data.get("text_density_ratio") or 0),
        "robots_status": str(audit_data.get("robots_status") or ""),
        "warnings": list(audit_data.get("warnings") or []),
        "dns": audit_data.get("dns") or {"a": [], "aaaa": []},
        "dualstack_probe": audit_data.get("dualstack_probe") or {"a": {}, "aaaa": {}},
        "tech_score": tech_score,
        "llm_status": llm_status,
        "llm_provider": llm_provider,
        "probe_baseline_id": str(
            probe_snap.get("probe_baseline_id") or cfg.get("probe_baseline_id") or ""
        ),
    }


def save_audit_metrics(cfg: dict, metrics: dict) -> str:
    """落盘 audit_metrics.json，返回绝对路径。"""
    out_dir = cfg.get("_outputs_dir")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, AUDIT_METRICS_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    return path


def _rating_label(tech_score: int) -> str:
    if tech_score >= 85:
        return "良好"
    if tech_score >= 70:
        return "基本达标"
    if tech_score >= 40:
        return "待优化"
    return "底座薄弱"


def _mode_banner(metrics: dict) -> str:
    status = metrics.get("llm_status") or "skipped"
    if status == "ok":
        return "技术分来自 Python 真抓；商业解读由小毛驴 / Nextdoor 大模型生成（禁止改写技术检测结果）"
    if status == "failed":
        return "技术分来自 Python 真抓；商业解读调用失败，本报告仅含真抓技术段 + 规则降级建议"
    return "技术分来自 Python 真抓；未接通大模型（NEXTDOOR_JWT_TOKEN），商业段为规则降级稿"


def generate_visibility_table(cfg: dict, probe_snap: dict) -> str:
    """可见度表：有 probe 用真值；否则明示待侦察。"""
    lines = [
        "## 三、大模型可见度对照（引用阶段零侦察，非假排名）",
        "",
    ]
    if not probe_snap.get("available"):
        lines.extend(
            [
                "> 尚无可用的 `competitor_probe_*.json`。请先完成阶段零侦察回填；此处**不编造**关键词排名。",
                "",
                "| 说明 | 状态 |",
                "| :--- | :--- |",
                "| 侦察基线 | 待侦察 / 待复测 |",
                "",
            ]
        )
        return "\n".join(lines)

    bid = probe_snap.get("probe_baseline_id") or cfg.get("probe_baseline_id") or "（未标注）"
    pfile = probe_snap.get("probe_file") or ""
    lines.append(f"> 来源：`{pfile}` · 基线 `{bid}`")
    lines.append("")
    summary = probe_snap.get("summary") or {}
    if summary.get("brand_status") or summary.get("founder_status"):
        lines.append(
            f"- 品牌侧摘要：{summary.get('brand_status') or '（无）'}"
        )
        lines.append(
            f"- 人物侧摘要：{summary.get('founder_status') or '（无）'}"
        )
        lines.append("")

    lines.extend(
        [
            "| 监测问句 | 是否提及我方 | 官网 URL | 立场/备注 | 抽出竞品 |",
            "| :--- | :---: | :---: | :--- | :--- |",
        ]
    )
    for it in probe_snap.get("items") or []:
        comps = "、".join(it.get("competitors") or []) or "—"
        note = it.get("standpoint") or it.get("doubao_verdict") or "—"
        if it.get("hallucination_detected"):
            note = f"幻觉风险 · {note}"
        lines.append(
            f"| {it.get('query')} | "
            f"{'是' if it.get('mentioned_self') else '否'} | "
            f"{'有' if it.get('url_present') else '无'} | "
            f"{note} | {comps} |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_tech_section(metrics: dict) -> str:
    """技术表与问题清单（只读 metrics）。"""
    has_ssr = bool(metrics.get("has_ssr"))
    has_llms = bool(metrics.get("has_llms_txt"))
    has_ld = bool(metrics.get("has_json_ld"))
    density = float(metrics.get("text_density_ratio") or 0)
    clean_len = int(metrics.get("clean_text_length") or 0)
    robots = str(metrics.get("robots_status") or "")

    section = f"""## 二、站点底座技术体检明细（Technical Audit · 真抓）

| 诊断维度 | 现状检测值 | 标准规范要求 | 诊断结论 | 权重扣分 |
| :--- | :--- | :--- | :--- | :---: |
| **渲染模式 (SSR)** | {"服务端预渲染/静态" if has_ssr else "客户端 CSR 空壳"} | 必须为 SSR/SSG，输出 Clean DOM | {"符合要求" if has_ssr else "AI 抓取易为空白"} | {"-0" if has_ssr else "-40"} |
| **AI 索引标准 (/llms.txt)** | {"已部署" if has_llms else "未部署"} | 根目录提供纯 Markdown 结构化摘要 | {"正常" if has_llms else "缺少 AI 毫秒读取入口"} | {"-0" if has_llms else "-25"} |
| **实体元数据 (JSON-LD)** | {"已配置" if has_ld else "未发现"} | HTML 内置 Schema.org 组织/产品标签 | {"符合" if has_ld else "难以精准识别公司实体"} | {"-0" if has_ld else "-20"} |
| **有效文本密度** | {density}%（正文 {clean_len} 字符） | 文本密度建议 > 15%～20% | {"良好" if density >= 15 else "代码与标签占比偏高"} | {"-0" if density >= 15 else "-15"} |
| **爬虫放行 (robots.txt)** | {robots} | 主动放行 Bytespider、Baiduspider、Sogouspider 等 | 见左列 | -0 |

### 检测到的关键问题清单
"""
    warnings = metrics.get("warnings") or []
    if warnings:
        for w in warnings:
            section += f"- {w}\n"
    else:
        section += "- 站点基础架构未检测到阻碍 AI 抓取的严重缺陷。\n"
    section += "\n"
    return section


def generate_fallback_narrative(cfg: dict, metrics: dict, probe_snap: dict) -> str:
    """无 LLM 时的规则降级商业段（不编造排名）。"""
    client = cfg.get("client_name") or "目标客户"
    score = int(metrics.get("tech_score") or 10)
    gaps = []
    if not metrics.get("is_online"):
        gaps.append("官网不可访问或超时")
    if not metrics.get("has_ssr"):
        gaps.append("CSR 空壳风险")
    if not metrics.get("has_llms_txt"):
        gaps.append("缺少 /llms.txt")
    if not metrics.get("has_json_ld"):
        gaps.append("缺少 JSON-LD")
    if float(metrics.get("text_density_ratio") or 0) < 15:
        gaps.append("文本密度偏低")
    if not probe_snap.get("available"):
        gaps.append("尚无阶段零侦察基线")

    gap_text = "、".join(gaps) if gaps else "技术底座无明显硬伤，下一步重点看内容与分发"

    return f"""## 一、诊断结论先行（规则降级稿）

1. **技术健康分**：{score} / 100（{_rating_label(score)}）。分数仅反映真抓技术项，不代表大模型推荐率。
2. **优先缺口**：{gap_text}。
3. **商业影响**：潜在买家若用豆包 / DeepSeek 提问，是否提到「{client}」取决于公开证据与侦察结果；请结合第三节 probe 表，勿把技术分当成声量分。

## 四、GEO 交付执行建议（四步）

1. **技术底座**：按第二节缺口补齐 llms.txt / Schema / 文本密度 / robots。
2. **名片段与事实源**：统一品牌 + 主体 + 官网 + 人物口径，写入官网与第三方。
3. **矩阵分发**：头条 / 知乎 / 微信等按客户词库占位（阶段四）。
4. **监测复测**：固定问句周报，对照阶段零基线（阶段五）。
"""


def build_llm_prompt(cfg: dict, metrics: dict, probe_snap: dict) -> tuple[str, str]:
    """构造系统提示与用户提示。"""
    system = (
        "你是 GEO 售前诊断顾问。根据给定的【真抓技术指标】与【侦察摘要】写中文 Markdown 商业解读。"
        "严禁改写、否定或编造技术检测布尔值与 tech_score。"
        "严禁编造关键词排名或虚构未提供的 probe 结果。"
        "只输出两个二级标题的正文："
        "## 一、诊断结论先行（Executive Summary）"
        "与"
        "## 四、GEO 商业化交付执行建议（四步破局路线）"
        "不要输出技术体检表（第二节由系统插入）。"
    )
    payload = {
        "client_name": cfg.get("client_name"),
        "brand_name": cfg.get("brand_name"),
        "company_name": cfg.get("company_name"),
        "official_url": cfg.get("official_url"),
        "business_one_liner": cfg.get("business_one_liner") or cfg.get("slogan") or "",
        "industry": cfg.get("industry"),
        "competitors": _normalize_list(cfg.get("competitors"))[:12],
        "keywords_sample": _normalize_list(cfg.get("keywords"))[:20],
        "metrics": {
            "tech_score": metrics.get("tech_score"),
            "url": metrics.get("url"),
            "is_online": metrics.get("is_online"),
            "has_ssr": metrics.get("has_ssr"),
            "has_llms_txt": metrics.get("has_llms_txt"),
            "has_json_ld": metrics.get("has_json_ld"),
            "text_density_ratio": metrics.get("text_density_ratio"),
            "robots_status": metrics.get("robots_status"),
            "warnings": metrics.get("warnings"),
        },
        "probe": {
            "available": probe_snap.get("available"),
            "probe_baseline_id": probe_snap.get("probe_baseline_id"),
            "summary": probe_snap.get("summary"),
            "items": (probe_snap.get("items") or [])[:12],
        },
    }
    user = (
        "请基于下列 JSON 写商业解读（结论 + 四步建议）。技术分已算定，勿重算或篡改。\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    return system, user


def generate_llm_narrative(cfg: dict, metrics: dict, probe_snap: dict) -> tuple[str, str, str]:
    """
    调用大模型生成商业段。
    返回 (narrative_md, llm_status, llm_provider)
    """
    try:
        from .llm import resolve_llm_runtime

        runtime = resolve_llm_runtime()
    except Exception:
        runtime = None

    if not runtime:
        return "", "skipped", "none"

    provider = str(runtime.get("provider") or runtime.get("channel") or "nextdoor")
    system, user = build_llm_prompt(cfg, metrics, probe_snap)
    ok, text, used = call_llm_api(user, system_prompt=system, timeout=LLM_TIMEOUT_SEC)
    if not ok or not (text or "").strip():
        print_warning(f"商业解读 LLM 失败：{text or 'empty'}")
        return "", "failed", used or provider
    body = text.strip()
    if "## 一" not in body and "诊断结论" not in body:
        body = "## 一、诊断结论先行（Executive Summary）\n\n" + body
    return body, "ok", used or provider


def assemble_report(
    cfg: dict,
    metrics: dict,
    probe_snap: dict,
    narrative: str,
) -> str:
    """拼装最终 Markdown 报告。"""
    client_name = cfg.get("client_name") or "目标客户"
    domain = metrics.get("url") or cfg.get("official_url") or ""
    industry = cfg.get("industry") or "行业未指定"
    area_served = cfg.get("area_served") or "全国"
    tech_score = int(metrics.get("tech_score") or 10)
    date_str = datetime.now().strftime("%Y年%m月%d日")
    mode = _mode_banner(metrics)

    if not (narrative or "").strip():
        narrative = generate_fallback_narrative(cfg, metrics, probe_snap)

    # 确保叙事含第四节时，技术与可见度插在结论之后
    tech = generate_tech_section(metrics)
    vis = generate_visibility_table(cfg, probe_snap)

    # 若 LLM 已含一、四，把二、三插到一之后、四之前
    if "## 四" in narrative:
        head, tail = narrative.split("## 四", 1)
        middle = tech + vis + "## 四" + tail
        body = head.rstrip() + "\n\n" + middle.lstrip()
    else:
        body = narrative.rstrip() + "\n\n" + tech + vis

    report = f"""# 《{client_name}》AI 可见度现状体检与商业诊断报告

> **评测中枢**：邻里 GEO 工业级商业交付中心  
> **报告日期**：{date_str}  
> **评测对象**：{client_name}（官网：`{domain}`）  
> **服务腹地**：{area_served}  
> **行业领域**：{industry}  
> **评测模式**：{mode}  
> **综合健康评分（技术真抓）**：**{tech_score} / 100 分**（评级：{_rating_label(tech_score)}）  
> **指标真源**：`outputs/{AUDIT_METRICS_FILE}`

---

{body.rstrip()}
"""
    return report


def generate_audit_report(
    cfg: dict,
    audit_data: dict,
    *,
    metrics: dict | None = None,
    probe_snap: dict | None = None,
    narrative: str = "",
) -> str:
    """兼容旧调用：无 metrics 时现场计算。"""
    probe_snap = probe_snap or {"available": False, "items": [], "summary": {}}
    if metrics is None:
        metrics = build_metrics(
            str(cfg.get("client_id") or ""),
            cfg,
            audit_data,
            probe_snap=probe_snap,
        )
    return assemble_report(cfg, metrics, probe_snap, narrative)


def load_audit_metrics(cfg: dict) -> dict | None:
    """读取已落盘的 audit_metrics.json；不存在则返回 None。"""
    out_dir = cfg.get("_outputs_dir") or ""
    path = os.path.join(out_dir, AUDIT_METRICS_FILE)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def metrics_to_audit_data(metrics: dict) -> dict:
    """把 metrics 还原成 assemble 可用的 audit_data 形态。"""
    return {
        "url": metrics.get("url") or "",
        "is_online": bool(metrics.get("is_online")),
        "status_code": int(metrics.get("status_code") or 0),
        "html_size_kb": float(metrics.get("html_size_kb") or 0),
        "has_ssr": bool(metrics.get("has_ssr")),
        "has_llms_txt": bool(metrics.get("has_llms_txt")),
        "has_json_ld": bool(metrics.get("has_json_ld")),
        "clean_text_length": int(metrics.get("clean_text_length") or 0),
        "text_density_ratio": float(metrics.get("text_density_ratio") or 0),
        "robots_status": str(metrics.get("robots_status") or ""),
        "warnings": list(metrics.get("warnings") or []),
        "dns": metrics.get("dns") or {"a": [], "aaaa": []},
        "dualstack_probe": metrics.get("dualstack_probe") or {"a": {}, "aaaa": {}},
    }


def run_audit_crawl(project_id: str, custom_url: str = None) -> dict:
    """仅真抓：写 metrics + 技术/降级报告，不调大模型。"""
    print_banner("阶段一①：真抓技术指标")
    cfg = load_project_config(project_id)
    target_url = custom_url or cfg.get("official_url", "https://example.com")
    print_info(f"正在对客户 [{cfg.get('client_name')}] 官网进行抓取体检: {target_url}")
    audit_data = inspect_website(target_url)
    probe_snap = load_probe_snapshot(cfg)
    metrics = build_metrics(
        project_id,
        cfg,
        audit_data,
        probe_snap=probe_snap,
        llm_status="skipped",
        llm_provider="none",
    )
    metrics_path = save_audit_metrics(cfg, metrics)
    print_info(f"技术真源已落盘: {metrics_path}")
    report_content = assemble_report(cfg, metrics, probe_snap, "")
    out_path = save_project_output(cfg, AUDIT_REPORT_FILE, report_content)
    print_success(f"真抓完成：{out_path}（tech_score={metrics.get('tech_score')}）")
    return {
        "mode": "crawl",
        "report_path": out_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
        "message": f"① 真抓完成：技术分 {metrics.get('tech_score')} / 100。可再点「② 小毛驴解读」。",
    }


def run_audit_interpret(project_id: str) -> dict:
    """仅解读：读取已有 metrics，调小毛驴写商业段并重写报告。"""
    print_banner("阶段一②：小毛驴商业解读")
    cfg = load_project_config(project_id)
    metrics = load_audit_metrics(cfg)
    if not metrics:
        raise ValueError("尚未真抓：请先执行「① 真抓指标」，生成 outputs/audit_metrics.json")
    probe_snap = load_probe_snapshot(cfg)
    print_info("调用小毛驴 / Nextdoor 生成商业解读...")
    narrative, llm_status, llm_provider = generate_llm_narrative(cfg, metrics, probe_snap)
    metrics = dict(metrics)
    metrics["llm_status"] = llm_status
    metrics["llm_provider"] = llm_provider
    metrics_path = save_audit_metrics(cfg, metrics)
    report_content = assemble_report(cfg, metrics, probe_snap, narrative)
    out_path = save_project_output(cfg, AUDIT_REPORT_FILE, report_content)
    if llm_status == "ok":
        msg = "② 小毛驴解读完成，报告商业段已更新。"
    elif llm_status == "failed":
        msg = "② 解读调用失败，已保留真抓报告并标注降级（请看控制台具体原因：本机无 3001 需开隧道 / 机器密钥 / 专属链）。"
    else:
        msg = "② 未接通大模型，已用规则降级稿（请配置小毛驴 JWT）。"
    print_success(f"{msg} → {out_path}（llm={llm_status}/{llm_provider}）")
    return {
        "mode": "interpret",
        "report_path": out_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
        "llm_status": llm_status,
        "llm_provider": llm_provider,
        "message": msg,
    }


def run_audit(project_id: str, custom_url: str = None, mode: str = "full") -> str:
    """
    阶段一体检。
    mode:
      - crawl: 仅真抓
      - interpret: 仅解读（需已有 metrics）
      - full: 真抓后再解读（CLI 默认兼容）
    返回报告路径。
    """
    m = (mode or "full").strip().lower()
    if m == "crawl":
        return run_audit_crawl(project_id, custom_url=custom_url)["report_path"]
    if m == "interpret":
        return run_audit_interpret(project_id)["report_path"]

    # full：先抓再解读
    crawl_res = run_audit_crawl(project_id, custom_url=custom_url)
    try:
        interpret_res = run_audit_interpret(project_id)
        return interpret_res["report_path"]
    except Exception as e:
        print_warning(f"解读阶段跳过/失败，保留真抓报告: {e}")
        return crawl_res["report_path"]
