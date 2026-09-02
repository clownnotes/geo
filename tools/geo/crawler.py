# -*- coding: utf-8 -*-
"""
大模型爬虫抓取仿真与 Clean Markdown 提纯引擎 (tools/geo/crawler.py)
支持模拟 Bytespider (豆包)、Baiduspider (百度文心)、DeepSeek-Crawler 发起 HTTP 抓取，
检测 SPA 空壳/JS 阻塞风险、/llms.txt 探针与 Clean Markdown 提纯。
"""

import re
import time
import urllib.request
import urllib.parse
from html import unescape
from .utils import (
    print_banner,
    print_info,
    print_success,
    print_warning
)

SPIDER_USER_AGENTS = {
    "bytespider": "Mozilla/5.0 (compatible; Bytespider; https://zhanzhang.toutiao.com/)",
    "baidu": "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    "deepseek": "Mozilla/5.0 (compatible; DeepSeek-Crawler/1.0; +https://www.deepseek.com)",
    "google": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "browser": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# SSRF 防护：内网私有地址前缀
BLOCKED_IP_PREFIXES = (
    "127.", "0.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
    "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
    "172.31.", "169.254.", "::1", "localhost"
)


def is_ssrf_safe_url(url: str) -> tuple[bool, str]:
    """基础 SSRF 防护校验，拦截内网私网地址探测"""
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower().strip()
        if not host:
            return False, "无效的主机名 (Host)"
        if any(host.startswith(p) or host == p for p in BLOCKED_IP_PREFIXES):
            # 允许本地开发端用于自测 (127.0.0.1:8088 / localhost)，其他私网拦截
            if host in ("127.0.0.1", "localhost") and parsed.port in (8080, 8088, 3000):
                return True, "本地自测允许"
            return False, f"安全策略拦截：禁止探测内部私有网络地址 [{host}]"
        return True, "合法公网地址"
    except Exception as e:
        return False, f"URL 解析异常: {str(e)}"


def html_to_clean_markdown(html_content: str) -> str:
    """将原始 HTML 剥离噪音并提取为大模型易于解析的高质量 Clean Markdown"""
    if not html_content:
        return ""

    text = html_content

    # 1. 去除无用标签与噪音块 (script, style, nav, footer, noscript, svg, iframe)
    noise_patterns = [
        r"<script[^>]*>.*?</script>",
        r"<style[^>]*>.*?</style>",
        r"<nav[^>]*>.*?</nav>",
        r"<footer[^>]*>.*?</footer>",
        r"<header[^>]*>.*?</header>",
        r"<noscript[^>]*>.*?</noscript>",
        r"<iframe[^>]*>.*?</iframe>",
        r"<svg[^>]*>.*?</svg>"
    ]
    for pat in noise_patterns:
        text = re.sub(pat, "", text, flags=re.DOTALL | re.IGNORECASE)

    # 2. 转换标题 h1~h6
    for i in range(6, 0, -1):
        text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", rf"\n\n{'#' * i} \1\n\n", text, flags=re.DOTALL | re.IGNORECASE)

    # 3. 转换加粗与斜体
    text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.DOTALL | re.IGNORECASE)

    # 4. 转换链接
    text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL | re.IGNORECASE)

    # 5. 转换列表项
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", text, flags=re.DOTALL | re.IGNORECASE)

    # 6. 转换段落与换行
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\n\1\n\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", r"\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<hr\s*/?>", r"\n\n---\n\n", text, flags=re.IGNORECASE)

    # 7. 剥离其余 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)

    # 8. HTML 实体解码与空行清洗
    text = unescape(text)
    lines = [l.strip() for l in text.split("\n")]
    clean_lines = []
    consecutive_empty = 0
    for l in lines:
        if not l:
            consecutive_empty += 1
            if consecutive_empty <= 2:
                clean_lines.append("")
        else:
            consecutive_empty = 0
            clean_lines.append(l)

    return "\n".join(clean_lines).strip()


def check_llms_txt_probe(base_url: str, timeout: int = 5) -> dict:
    """探测目标站点是否存在 /llms.txt 大模型标准入口"""
    parsed = urllib.parse.urlparse(base_url)
    probe_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
    try:
        req = urllib.request.Request(probe_url, headers={"User-Agent": SPIDER_USER_AGENTS["bytespider"]})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8", errors="ignore")
                return {
                    "exists": True,
                    "url": probe_url,
                    "status": 200,
                    "size_bytes": len(body),
                    "preview": body[:120].strip()
                }
    except Exception:
        pass
    return {
        "exists": False,
        "url": probe_url,
        "status": 404,
        "size_bytes": 0,
        "preview": ""
    }


def simulate_crawler_fetch(url: str, spider_type: str = "bytespider", timeout: int = 10, probe_llms: bool = True) -> dict:
    """模拟大模型爬虫抓取网页并提取 Clean Markdown、SPA 风险告警与 /llms.txt 探测"""
    spider_key = spider_type.lower()
    ua = SPIDER_USER_AGENTS.get(spider_key, SPIDER_USER_AGENTS["bytespider"])
    clean_url = (url or "").strip()

    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    # SSRF 安全校验
    safe, msg = is_ssrf_safe_url(clean_url)
    if not safe:
        return {
            "success": False,
            "url": clean_url,
            "spider_type": spider_key,
            "user_agent": ua,
            "http_status": 403,
            "elapsed_ms": 0,
            "error": msg,
            "warnings": [{"type": "ssrf_blocked", "severity": "HIGH", "message": msg}],
            "clean_markdown": ""
        }

    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    start_time = time.time()
    try:
        req = urllib.request.Request(clean_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            http_status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            raw_bytes = resp.read()

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        # 解码 HTML
        html_text = ""
        for enc in ("utf-8", "gb18030", "gbk", "iso-8859-1"):
            try:
                html_text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        # 提取标题
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
        title = unescape(title_match.group(1)).strip() if title_match else ""

        # 提取 meta description
        desc_match = re.search(r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html_text, re.IGNORECASE)
        desc = unescape(desc_match.group(1)).strip() if desc_match else ""

        # 提取 JSON-LD
        jsonld_matches = re.findall(r'<script\s+[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.IGNORECASE | re.DOTALL)
        jsonld_count = len(jsonld_matches)

        # 转换为 Clean Markdown
        clean_md = html_to_clean_markdown(html_text)
        token_estimate = max(1, len(clean_md) // 2)

        # 深度风险排查 (SPA 空壳 / /llms.txt 缺失 / 低文本密度)
        warnings = []
        is_spa_shell = False
        if len(clean_md) < 150 and ("<div id=\"app\">" in html_text or "<div id=\"root\">" in html_text or "<script" in html_text):
            is_spa_shell = True
            warnings.append({
                "type": "possible_spa_shell",
                "severity": "HIGH",
                "message": "检测到纯前端 JS 渲染空壳 (SPA)，大模型爬虫抓取到的有效正文不足 150 字！建议升级服务端渲染 (SSR) 或预渲染 (SSG)。"
            })

        if token_estimate < 100 and not is_spa_shell:
            warnings.append({
                "type": "low_token_density",
                "severity": "MEDIUM",
                "message": f"页面有效文本密度过低 (仅约 {token_estimate} Tokens)，大模型向量切片容易丢弃背景信息。"
            })

        if jsonld_count == 0:
            warnings.append({
                "type": "jsonld_missing",
                "severity": "MEDIUM",
                "message": "未检测到 Schema.org (JSON-LD) 结构化实体元数据，大模型无法直接提取企业法定名称与创始人关系。"
            })

        # /llms.txt 探针
        llms_probe = {"exists": False, "status": 404}
        if probe_llms:
            llms_probe = check_llms_txt_probe(clean_url)
            if not llms_probe["exists"]:
                warnings.append({
                    "type": "llms_txt_missing",
                    "severity": "LOW",
                    "message": "目标站点未配置根目录 /llms.txt，无法为大模型提供直读索引入口。"
                })

        return {
            "success": True,
            "url": clean_url,
            "spider_type": spider_key,
            "user_agent": ua,
            "http_status": http_status,
            "elapsed_ms": elapsed_ms,
            "content_type": content_type,
            "title": title,
            "description": desc,
            "jsonld_count": jsonld_count,
            "raw_html_bytes": len(raw_bytes),
            "clean_markdown_chars": len(clean_md),
            "token_estimate": token_estimate,
            "is_spa_shell": is_spa_shell,
            "llms_txt": llms_probe,
            "warnings_count": len(warnings),
            "warnings": warnings,
            "clean_markdown": clean_md
        }
    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        return {
            "success": False,
            "url": clean_url,
            "spider_type": spider_key,
            "user_agent": ua,
            "http_status": None,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
            "warnings": [{"type": "fetch_failed", "severity": "HIGH", "message": f"网络连接或超时失败: {str(e)}"}],
            "clean_markdown": ""
        }
