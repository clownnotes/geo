# -*- coding: utf-8 -*-
"""
大模型爬虫抓取仿真与 Clean Markdown 提纯引擎 (tools/geo/crawler.py)
支持模拟 Bytespider (豆包)、Baiduspider (百度文心)、DeepSeek-Crawler 发起 HTTP 抓取，
并自动提取元数据与 Clean Markdown。
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


def simulate_crawler_fetch(url: str, spider_type: str = "bytespider", timeout: int = 10) -> dict:
    """模拟大模型爬虫抓取网页并提取 Clean Markdown 与技术元数据"""
    spider_key = spider_type.lower()
    ua = SPIDER_USER_AGENTS.get(spider_key, SPIDER_USER_AGENTS["bytespider"])
    clean_url = (url or "").strip()

    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

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
            "clean_markdown": ""
        }
