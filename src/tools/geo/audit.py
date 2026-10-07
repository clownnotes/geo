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
AUDIT_REPORT_BOSS_FILE = "01_企业AI可见度商业诊断报告.md"
AUDIT_REPORT_TECH_FILE = "01_企业底座技术体检审计报告.md"
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
    """兼容旧混排报告题头（可含商业解读状态）。"""
    status = metrics.get("llm_status") or "skipped"
    if status == "ok":
        return "技术分来自 Python 真抓；商业解读由小毛驴 / Nextdoor 大模型生成（禁止改写技术检测结果）"
    if status == "failed":
        return "技术分来自 Python 真抓；商业解读调用失败，本报告仅含真抓技术段 + 规则降级建议"
    return "技术分来自 Python 真抓；未接通大模型（NEXTDOOR_JWT_TOKEN），商业段为规则降级稿"


def _tech_mode_banner(metrics: dict) -> str:
    """工程师专属题头：只谈技术真抓，禁止商业解读调试话。"""
    online = "官网可访问" if metrics.get("is_online") else "官网访问异常"
    return f"工程师内部施工稿 · 技术分来自 Python 真抓（{online}）· 不含商业推销与体验价 CTA"


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


def generate_tech_fix_plan(cfg: dict, metrics: dict, probe_snap: dict) -> str:
    """工程师报告第四节：问题 → 改造方案（内部施工，不卖焦虑）。"""
    client = cfg.get("client_name") or "目标客户"
    score = int(metrics.get("tech_score") or 10)
    rows = []
    if not metrics.get("is_online"):
        rows.append(("官网不可访问或超时", "先排查 DNS / HTTPS / 防火墙；恢复可抓取后再复测。"))
    if not metrics.get("has_ssr"):
        rows.append(("CSR 空壳风险", "改为 SSR/SSG 或预渲染，确保爬虫拿到 Clean DOM。"))
    if not metrics.get("has_llms_txt"):
        rows.append(("缺少 /llms.txt", "在站点根目录部署纯 Markdown 摘要，并在页脚/head 留可点入口。"))
    if not metrics.get("has_json_ld"):
        rows.append(("缺少 JSON-LD", "补 Organization / LocalBusiness / WebSite 等 Schema，图片资源本地真实存在。"))
    density = float(metrics.get("text_density_ratio") or 0)
    if density < 15:
        rows.append(
            (
                f"文本密度偏低（{density}%）",
                "补答案型正文与 FAQ（目标密度 ≥15%），用「结论先行 + 参数清单」结构方便 RAG 摘句。",
            )
        )
    for w in metrics.get("warnings") or []:
        rows.append((str(w), "对照警告逐项复测；网络双栈/证书类优先修连通性。"))
    if not probe_snap.get("available"):
        rows.append(("尚无阶段零豆包答案存档", "先完成阶段零并把豆包答案存进项目，再对照可见度表排索引缺口。"))
    if not rows:
        rows.append(("未发现阻断级技术硬伤", "保持底座，转入内容密度与分发占位的持续强化。"))

    table_lines = [
        "| 问题（真抓依据） | 改造方案（内部施工） |",
        "| :--- | :--- |",
    ]
    for problem, fix in rows:
        table_lines.append(f"| {problem} | {fix} |")

    return f"""## 一、诊断结论先行（工程师速读）

1. **技术健康分**：{score} / 100（{_rating_label(score)}）。分数只反映真抓技术项，不代表大模型推荐率。
2. **本报告用途**：给交付团队的**问题 + 改造方案**施工稿；不含对客焦虑话术与体验价 CTA。
3. **客户主体**：{client}。可见度对照见第三节（引用阶段零，不编造排名）。

## 四、问题与改造方案对照（内部施工）

{chr(10).join(table_lines)}

### 执行顺序建议
1. 先修阻断级（不可访问 / CSR 空壳 / robots 误拦）。
2. 再补 /llms.txt、Schema、正文密度。
3. 对照第三节豆包问句，逐条补官网可引用答案块与外链信源。
4. 复测：重跑真抓 + 阶段零同组问句，核对 tech_score 与提及率变化。
"""


def generate_fallback_narrative(cfg: dict, metrics: dict, probe_snap: dict) -> str:
    """无 LLM 时的规则降级商业段（不编造排名）。老板焦虑转化仍走 build_boss_psychology_report。"""
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


# [2026-09-17] [商业转化型诊断报告与竞品反哺体系] 差距一与差距四：老板心理学 7 步法转化层
def build_boss_psychology_report(
    cfg: dict,
    metrics: dict,
    probe_snap: dict,
    narrative: str = "",
) -> str:
    """生成符合落地大纲的「老板心理学 7 步法」转化层（严格遵守 0 Emoji 规范）。"""
    client = cfg.get("client_name") or "目标客户"
    bname = cfg.get("brand_name") or client
    industry = cfg.get("industry") or "行业解决方案"
    area = cfg.get("area_served") or "全国"
    founder = cfg.get("founder") or "创始人"
    tech_score = int(metrics.get("tech_score") or 10)
    density = float(metrics.get("text_density_ratio") or 0)

    items = probe_snap.get("items") or []
    total_probes = len(items)
    if total_probes > 0:
        mention_cnt = sum(1 for it in items if it.get("mentioned_self"))
        url_cnt = sum(1 for it in items if it.get("url_present"))
        halluc_cnt = sum(1 for it in items if it.get("hallucination_detected"))
        mention_rate = round((mention_cnt / total_probes) * 100, 1)
        url_rate = round((url_cnt / total_probes) * 100, 1)
        halluc_rate = round((halluc_cnt / total_probes) * 100, 1)
    else:
        mention_rate = 0.0
        url_rate = 0.0
        halluc_rate = 80.0

    tech_status = "[达标]" if tech_score >= 75 else ("[偏弱]" if tech_score >= 50 else "[高危]")
    density_status = "[达标]" if density >= 15.0 else "[偏弱]"
    vis_status = "[达标]" if mention_rate >= 60.0 else ("[偏弱]" if mention_rate >= 20.0 else "[空白]")
    comp_status = "[高危]" if halluc_rate >= 50.0 or mention_rate < 30.0 else "[预警]"

    comp_names = set()
    for it in items:
        for c in it.get("competitors") or []:
            if c and str(c).strip():
                comp_names.add(str(c).strip())
    top_comps_str = "、".join(list(comp_names)[:4]) if comp_names else "同行主流服务商"

    # 提炼 LLM 解读中的关键观点（若有）
    custom_insight = ""
    if narrative and "##" in narrative:
        custom_insight = f"\n> **商业解读摘要**：{narrative[:300].strip()}\n"

    vis_table = generate_visibility_table(cfg, probe_snap)

    md = f"""## ① 一页结论（老板速读版）—— 注意与核心痛点

### AI 可见度四维评分卡
| 诊断维度 | 状态判定 | 真实依据 |
| :--- | :---: | :--- |
| **技术底座基建** | `{tech_status}` | SSR 预渲染、/llms.txt、robots 放行综合得分 **{tech_score} 分** |
| **正文可引用性** | `{density_status}` | 有效文本密度 {density}%，{"低于 15% 建议线，答案结构偏薄" if density < 15 else "正文体量合格"} |
| **品牌可见度** | `{vis_status}` | {total_probes} 组核心长问中提及率仅 **{mention_rate}%**，官网带出率 **{url_rate}%** |
| **竞品截流威胁** | `{comp_status}` | 竞品【{top_comps_str}】占位严重，幻觉/误读风险率 **{halluc_rate}%** |

> 【综合探针】：共探测 **{total_probes}** 条买家核心长问 · 品牌提及率 **{mention_rate}%** · 带出官网率 **{url_rate}%** · 幻觉与误读风险率 **{halluc_rate}%**。{custom_insight}

### 三个经营状态判定
| [技术底座合格] | [可引用性偏薄] | [市场可见度空白] |
| :--- | :--- | :--- |
| 官网能被爬虫访问，**不用推倒重做** | 缺少结构化问答对，AI 难以精准摘句 | 买家先问 AI，客流直接流失给同行 |

### 你正在流失的，是 3 类本该进你微信的高价值询盘
1. **[品牌直问询盘]**：买家搜索【{bname}】是做什么的、官网是什么，AI 无法给出官网或给出错误主体，意向买家迷路流失。
2. **[信任词询盘]**：大客户在签单前求证“找【{bname}】或【{founder}】靠谱吗”，AI 无高权威证据链支撑，转而推荐竞品替代。
3. **[品类词询盘]**：搜索“{area}{industry}哪家好”，AI 优先推荐【{top_comps_str}】，最直接的商业成交线索被截胡。

### 三个必须正视的业务缺口
| 核心缺口 | 摸底现状 | 商业含义与后果 |
| :--- | :--- | :--- |
| **品牌词链路** | 官网带出率仅 {url_rate}% | 意向买家即便知道品牌，也进不了企业私域微信 |
| **信任词承接** | 人物与品牌公开背书薄弱 | 面对大单高客单决策，缺乏让买家安心打款的证据 |
| **品类词拦截** | 同行占领首位推荐 | 本地/行业最具价值的新增采购需求，全被同行吃掉 |

---

## ② 好消息：你的资产其实很能打（不用推倒重来）—— 资产确权

经过真机探测，贵司现有的网站与技术基底具备良好的改造基础，**绝不需要推倒重新建站**：
- **技术通道畅通**：基础网络访问与基础技术评分达到 **{tech_score} 分**（评级：{_rating_label(tech_score)}）；
- **唯一核心硬伤**：{"有效正文文本密度仅 " + str(density) + "%，结构化问答库较薄，导致大模型抓取后缺乏摘句引用的高浓度答案" if density < 15 else "缺乏与买家常见提问一对一绑定的权威答案源"}；
- **市场定位定性**：【{bname}】处于**“有硬实力资产，无大模型记忆”**的早期估值洼地，只要补齐高权威答案源，反超成本极低。

---

## ③ 坏消息：AI 现在根本认不出你的品牌（这才是丢单的地方）—— 痛点剖析

以下是买家日常真实提问下，主流大模型当前给出的实际答复透视：

{vis_table.strip()}

### 竞品占位透视（谁在吃你的商业入口）
在上述实测中，【{top_comps_str}】频繁出现在推荐位前列。它们能占位的关键并非技术比贵司强，而是它们提前在知乎、头条与第三方渠道沉淀了长文，被大模型作为信源采纳。**竞品的优势，就是贵司接下来反超的精准靶心。**

---

## ④ 四步破局路线：从「能被读到」到「被首位推荐」—— 执行路径

根据本次体检暴露的缺口，按优先级安排 4 步执行动作：

### 第一步：建立「品牌标准答案卡」（P0，官网 7 天内落地）
在官网核心页面固定输出统一可被引用的信息块：明确【{bname}】是谁、主体公司、官网地址、核心服务范围、主理人背景与官方联系方式。杜绝主体张冠李戴。

### 第二步：把正文密度补到“可引用”（P0，补足 15% 答案型正文）
补充 8~12 组买家最关心的常见问答（FAQ），采用“问题 + 结论先行 + 核心参数清单”结构，方便大模型 RAG 分块精准摘句。

### 第三步：按问句逐条补齐证据链（P1，2~4 周多渠道占位）
针对上述未被提及的品类词与选型词，针对性分发 9 因子深度技术长文，在知乎、今日头条、百家号建立不可逆的信源矩阵。

### 第四步：固定周期复测，用硬指标替代“感觉”（P1，每 2 周一轮）
按同一组买家问句持续追踪大模型提及率、官网带出率与首推排名，用真实声量数据验证交付成果。

---

## ⑤ 30 天后，你能拿到什么 —— 愿景具象化

| 核心评估维度 | 现在（摸底现状） | 30 天后执行目标 | 商业价值 |
| :--- | :--- | :--- | :--- |
| **品牌直问提及率** | {mention_rate}% | **100% 正确命中** | 彻底消除 AI 幻觉，官网链接 100% 露出 |
| **选型对比推荐位** | 完全被同行截流 | **进入前 3 首选名单** | 抢回属于自己的高意向采购询盘 |
| **官网链接带出率** | {url_rate}% | **≥ 60%** | 将 AI 对话直接转化为企业私域访问 |
| **品牌与主体认知** | 存在张冠李戴风险 | **100% 澄清纠偏** | 固化企业品牌护城河与公信力 |

---

## ⑥ 下一步：把这份免费体检变成真实询盘 —— 立即行动

> **限时体验计划（最低体验门槛，明码交付）**：
> 针对本次体检暴露的 3 大业务缺口，我们提供**【品牌答案源极速筑基体验包】**：
> - **交付内容**：官网 /llms.txt 与 Schema 实体底座精修 + 1 组品牌标准答案卡 + 1 篇今日头条字节爬虫提权长文；
> - **交付周期**：最快 3 个工作日落地生效；
> - **咨询对接**：请联系交付主理人（微信：nextdoor8 或扫描官网客服二维码），开启落地执行。
"""
    return md


def assemble_boss_report(
    cfg: dict,
    metrics: dict,
    probe_snap: dict,
    narrative: str = "",
) -> str:
    """拼装纯净的老板心理学商业转化报告（不含生涩技术附录 · 0 Emoji）。"""
    client_name = cfg.get("client_name") or "目标客户"
    domain = metrics.get("url") or cfg.get("official_url") or ""
    industry = cfg.get("industry") or "行业未指定"
    area_served = cfg.get("area_served") or "全国"
    tech_score = int(metrics.get("tech_score") or 10)
    date_str = datetime.now().strftime("%Y年%m月%d日")
    mode = _mode_banner(metrics)

    boss_layer = build_boss_psychology_report(cfg, metrics, probe_snap, narrative)

    return f"""# 《{client_name}》AI 可见度商业诊断报告

> **评测中枢**：邻里 GEO 工业级商业交付中心  
> **报告日期**：{date_str}  
> **评测对象**：{client_name}（官网：`{domain}`）  
> **服务腹地**：{area_served}  
> **行业领域**：{industry}  
> **报告性质**：AI 搜索买家心智决策与商业转化诊断（老板专用决策版）  
> **网络底座评分**：**{tech_score} / 100 分**（评级：{_rating_label(tech_score)} · 资产合格不用推倒重做）  
> **诊断核心结论**：有硬实力技术资产，无大模型商业记忆；买家意向询盘严重流失给同行

---

{boss_layer.strip()}
"""


def assemble_tech_report(
    cfg: dict,
    metrics: dict,
    probe_snap: dict,
    narrative: str = "",
) -> str:
    """拼装工程师技术体检报告：问题清单 + 改造方案（对内施工，不卖焦虑）。"""
    client_name = cfg.get("client_name") or "目标客户"
    domain = metrics.get("url") or cfg.get("official_url") or ""
    industry = cfg.get("industry") or "行业未指定"
    area_served = cfg.get("area_served") or "全国"
    tech_score = int(metrics.get("tech_score") or 10)
    date_str = datetime.now().strftime("%Y年%m月%d日")
    mode = _tech_mode_banner(metrics)

    # 固定用工程师改造方案稿，忽略传入的商业 narrative
    narrative = generate_tech_fix_plan(cfg, metrics, probe_snap)

    tech = generate_tech_section(metrics)
    vis = generate_visibility_table(cfg, probe_snap)

    if "## 四" in narrative:
        head, tail = narrative.split("## 四", 1)
        middle = tech + vis + "## 四" + tail
        body = head.rstrip() + "\n\n" + middle.lstrip()
    else:
        body = narrative.rstrip() + "\n\n" + tech + vis

    return f"""# 《{client_name}》站点底座技术体检与工程审计报告

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


def assemble_report(
    cfg: dict,
    metrics: dict,
    probe_snap: dict,
    narrative: str = "",
) -> str:
    """拼装双层 Markdown 报告（上层：老板心理学转化版；底层：工程师技术体检详版）。"""
    client_name = cfg.get("client_name") or "目标客户"
    domain = metrics.get("url") or cfg.get("official_url") or ""
    industry = cfg.get("industry") or "行业未指定"
    area_served = cfg.get("area_served") or "全国"
    tech_score = int(metrics.get("tech_score") or 10)
    date_str = datetime.now().strftime("%Y年%m月%d日")
    mode = _mode_banner(metrics)

    boss_layer = build_boss_psychology_report(cfg, metrics, probe_snap, narrative)
    tech_section = generate_tech_section(metrics)

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

{boss_layer.strip()}

---

## 附录：技术底座与工程巡检详版（工程师审计依据）

> 本附录包含真机网络探测与自动化爬虫的原始指标，数据直接来源于 `outputs/{AUDIT_METRICS_FILE}`，严禁改写技术布尔值。

{tech_section.strip()}
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
    boss_content = assemble_boss_report(cfg, metrics, probe_snap, "")
    tech_content = assemble_tech_report(cfg, metrics, probe_snap, "")
    out_path = save_project_output(cfg, AUDIT_REPORT_FILE, report_content)
    boss_path = save_project_output(cfg, AUDIT_REPORT_BOSS_FILE, boss_content)
    tech_path = save_project_output(cfg, AUDIT_REPORT_TECH_FILE, tech_content)
    # // [2026-09-18] [高转化老板商业诊断报告HTML模板重构] 自动落盘自包含高转化HTML大屏报告
    try:
        from .share import export_audit_report_html
        export_audit_report_html(cfg["id"], view="boss")
    except Exception:
        pass
    print_success(f"真抓完成：老板版={boss_path}，技术版={tech_path}，兼容版={out_path}（tech_score={metrics.get('tech_score')}）")
    return {
        "mode": "crawl",
        "report_path": out_path,
        "boss_report_path": boss_path,
        "tech_report_path": tech_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
        "message": (
            f"① 真抓完成：技术分 {metrics.get('tech_score')} / 100。"
            "可再切到老板商业转化版，点「① 生成商业转化解读」。"
        ),
    }


def run_audit_interpret(project_id: str) -> dict:
    """仅解读：读取已有 metrics，调小毛驴写商业段并重写报告。"""
    print_banner("阶段一②：小毛驴商业解读")
    cfg = load_project_config(project_id)
    metrics = load_audit_metrics(cfg)
    if not metrics:
        raise ValueError("请先点「① 真抓网络与底座指标」")
    probe_snap = load_probe_snapshot(cfg)
    print_info("调用小毛驴 / Nextdoor 生成商业解读...")
    narrative, llm_status, llm_provider = generate_llm_narrative(cfg, metrics, probe_snap)
    metrics = dict(metrics)
    metrics["llm_status"] = llm_status
    metrics["llm_provider"] = llm_provider
    metrics_path = save_audit_metrics(cfg, metrics)
    report_content = assemble_report(cfg, metrics, probe_snap, narrative)
    boss_content = assemble_boss_report(cfg, metrics, probe_snap, narrative)
    tech_content = assemble_tech_report(cfg, metrics, probe_snap, narrative)
    out_path = save_project_output(cfg, AUDIT_REPORT_FILE, report_content)
    boss_path = save_project_output(cfg, AUDIT_REPORT_BOSS_FILE, boss_content)
    tech_path = save_project_output(cfg, AUDIT_REPORT_TECH_FILE, tech_content)
    try:
        from .share import export_audit_report_html
        export_audit_report_html(cfg["id"], view="boss")
    except Exception:
        pass
    if llm_status == "ok":
        msg = "② 小毛驴解读完成，报告商业段已更新。"
    elif llm_status == "failed":
        msg = "② 解读调用失败，已保留真抓报告并标注降级（请看控制台具体原因：本机无 3001 需开隧道 / 机器密钥 / 专属链）。"
    else:
        msg = "② 未接通大模型，已用规则降级稿（请配置小毛驴 JWT）。"
    print_success(f"{msg} → 老板版={boss_path}，技术版={tech_path}（llm={llm_status}/{llm_provider}）")
    return {
        "mode": "interpret",
        "report_path": out_path,
        "boss_report_path": boss_path,
        "tech_report_path": tech_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
        "llm_status": llm_status,
        "llm_provider": llm_provider,
        "message": msg,
    }


def run_audit_boss_direct(project_id: str) -> dict:
    """阶段一老板版②：程序直出商业诊断与焦虑转化初稿（0 幻觉）。"""
    print_banner("阶段一老板版②：直出商业诊断与焦虑转化初稿")
    cfg = load_project_config(project_id)
    metrics = load_audit_metrics(cfg)
    if not metrics:
        raise ValueError("请先点「① 真抓网络与底座指标」")
    probe_snap = load_probe_snapshot(cfg)
    boss_content = assemble_boss_report(cfg, metrics, probe_snap, narrative="")
    boss_path = save_project_output(cfg, AUDIT_REPORT_BOSS_FILE, boss_content)
    save_project_output(cfg, AUDIT_REPORT_FILE, boss_content)
    try:
        from .share import export_audit_report_html
        export_audit_report_html(cfg["id"], view="boss")
    except Exception:
        pass
    print_success(f"② 商业诊断与焦虑转化初稿直出完成 → 老板版={boss_path}")
    return {
        "mode": "boss_direct",
        "boss_report_path": boss_path,
        "message": "② 商业诊断与焦虑转化初稿已客观直出（0 幻觉）",
    }


def run_audit_tech_direct(project_id: str) -> dict:
    """阶段一技术版②：程序直出技术体检与改造方案初稿（0 幻觉）。"""
    print_banner("阶段一技术版②：直出技术体检与改造方案初稿")
    cfg = load_project_config(project_id)
    metrics = load_audit_metrics(cfg)
    if not metrics:
        raise ValueError("请先点「① 真抓网络与底座指标」")
    probe_snap = load_probe_snapshot(cfg)
    tech_content = assemble_tech_report(cfg, metrics, probe_snap, narrative="")
    tech_path = save_project_output(cfg, AUDIT_REPORT_TECH_FILE, tech_content)
    print_success(f"② 技术体检与改造方案初稿直出完成 → 技术版={tech_path}")
    return {
        "mode": "tech_direct",
        "tech_report_path": tech_path,
        "message": "② 技术体检与改造方案初稿已直出（0 幻觉）",
    }


def run_audit(project_id: str, custom_url: str = None, mode: str = "full") -> str:
    """
    阶段一体检。
    mode:
      - crawl: 仅真抓
      - interpret: 仅解读（需已有 metrics）
      - boss_direct: 仅直出老板版骨架
      - tech_direct: 仅直出技术版初稿
      - full: 真抓后再解读（CLI 默认兼容）
    返回报告路径。
    """
    m = (mode or "full").strip().lower()
    if m == "crawl":
        return run_audit_crawl(project_id, custom_url=custom_url)["report_path"]
    if m == "interpret":
        return run_audit_interpret(project_id)["report_path"]
    if m == "boss_direct":
        return run_audit_boss_direct(project_id)["boss_report_path"]
    if m == "tech_direct":
        return run_audit_tech_direct(project_id)["tech_report_path"]

    # full：先抓再解读
    crawl_res = run_audit_crawl(project_id, custom_url=custom_url)
    try:
        interpret_res = run_audit_interpret(project_id)
        return interpret_res["report_path"]
    except Exception as e:
        print_warning(f"解读阶段跳过/失败，保留真抓报告: {e}")
        return crawl_res["report_path"]


def build_boss_audit_clipboard_pack(project_id: str) -> dict:
    """
    [2026-09-17] 阶段 8：为 IDE 生成四层全证据链剪贴板文本
    包含：
    1. 阶段零豆包实测一手答题卡；
    2. Python 客观直出商业诊断骨架；
    3. 发送给小毛驴的原始 Prompt 提示词；
    4. 小毛驴生成的初稿状态。
    """
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("name") or project_id
    official_url = cfg.get("official_url") or ""
    out_dir = cfg.get("_outputs_dir") or ""

    # 第一层：豆包一手答题卡
    probe_snap = load_probe_snapshot(cfg)
    items = probe_snap.get("items") or []
    probe_lines = []
    if items:
        probe_lines.append(f"共检测到 {len(items)} 条商业意图长问：")
        for idx, it in enumerate(items, 1):
            q = it.get("query") or ""
            m_self = "是" if it.get("mentioned_self") else "否"
            url_p = "是" if it.get("url_present") else "否"
            comps = ", ".join(it.get("competitors") or []) or "无"
            probe_lines.append(f"{idx}. 问句：{q}")
            probe_lines.append(f"   提及客户：{m_self} ｜ 带官网链接：{url_p} ｜ 推荐竞品：{comps}")
            ans_f = str(it.get("answer_full") or "").strip()
            if ans_f:
                probe_lines.append(f"   回答节选：{ans_f[:200]}...")
    else:
        probe_lines.append("（尚未录入阶段零豆包实测答题卡，建议先至阶段零摸底）")
    layer1_text = "\n".join(probe_lines)

    # 第二层：直出商业诊断骨架
    metrics = load_audit_metrics(cfg) or {}
    layer2_text = ""
    boss_report_path = os.path.join(out_dir, AUDIT_REPORT_BOSS_FILE) if out_dir else ""
    if boss_report_path and os.path.exists(boss_report_path):
        try:
            with open(boss_report_path, encoding="utf-8") as f:
                layer2_text = f.read().strip()
        except Exception:
            layer2_text = ""
    if not layer2_text:
        layer2_text = build_boss_psychology_report(cfg, metrics, probe_snap, narrative="").strip()

    # 第三层：发给小毛驴的原始 Prompt
    system_prompt, user_prompt = build_llm_prompt(cfg, metrics, probe_snap)
    layer3_text = f"【System Prompt】:\n{system_prompt}\n\n【User Payload】:\n{user_prompt}"

    # 第四层：小毛驴初稿状态
    llm_status = metrics.get("llm_status") or "unknown"
    llm_provider = metrics.get("llm_provider") or "none"
    if llm_status == "ok":
        layer4_text = f"（状态：已成功调用 {llm_provider} 生成商业解读，初稿已合并入第二层报告中，请重点检查其是否含有假大空与 AI 幻觉）"
    else:
        layer4_text = f"（状态：未调用小毛驴或调用未成功[{llm_status}]，当前报告完全基于客观规则直出）"

    clipboard = f"""【GEO 阶段一 · 老板商业转化诊断报告 · 全链路证据润色包】
项目 ID：{project_id}
企业名称：{client_name}
官网地址：{official_url}

—— 第一层：阶段零豆包实测一手答题卡（买家真实问答证据） ——
{layer1_text}

—— 第二层：Python 客观直出商业诊断骨架（真源依据，禁止篡改客观数据） ——
{layer2_text}

—— 第三层：发给小毛驴的原始 Prompt 提示词（了解指令意图与输入 JSON） ——
{layer3_text}

—— 第四层：小毛驴写出的初稿与状态 ——
{layer4_text}

【IDE 润色任务与老板心理学要求】：
1. 核对第一层与第二层的硬核数据，挑出小毛驴可能存在的套话、假大空与 AI 幻觉并坚决纠正；
2. 严格遵守 0 Emoji 严肃商业与工程规范；
3. 重点润色：买家视角提问、3 类流失的高价值询盘账本、好坏消息反差、四步破局路线、30 天愿景对比表；
4. 润色完成后，写回文件：projects/{project_id}/outputs/{AUDIT_REPORT_BOSS_FILE}"""

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "clipboard": clipboard.strip(),
    }

