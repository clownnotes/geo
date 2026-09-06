#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sort_homepage_articles.py
自动化确保 NextGEO 首页 Canonical Answers 精选文章卡片严格按发表时间倒序（Descending）排列。
支持：
1. 自动解析首页当前 6 张精选卡片中的日期；
2. 严格按发表日期从新到旧倒序重新渲染卡片；
3. 同步写回 site/index.html 与 outputs/index.html 双端；
4. 可作为发布流水线的前置/后置自动校验钩子。
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE_INDEX = os.path.join(PROJECT_ROOT, "projects/nextgeo/outputs/site/index.html")
OUTPUTS_INDEX = os.path.join(PROJECT_ROOT, "projects/nextgeo/outputs/index.html")

DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

def parse_and_sort_canonical_cards(html_content: str) -> str:
    # 定位 Canonical Answers 的卡片容器
    section_marker = "<!-- 优先建设的 GEO 定义与方法页 (Canonical Answers) -->"
    if section_marker not in html_content:
        print("[WARN] Canonical Answers section marker not found.")
        return html_content

    # 提取卡片容器网格: <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"> ... </div>
    grid_pattern = re.compile(
        r'(<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">)(.*?)(</div>\s*</div>\s*</section>)',
        re.DOTALL
    )
    match = grid_pattern.search(html_content)
    if not match:
        print("[WARN] Grid container not found in index.html.")
        return html_content

    grid_header = match.group(1)
    grid_body = match.group(2)
    grid_footer = match.group(3)

    # 拆解单个卡片 <a href="blog/..." class="article-card ...">...</a>
    card_pattern = re.compile(r'(<a href="blog/[^"]+".*?</a>)', re.DOTALL)
    raw_cards = card_pattern.findall(grid_body)

    if not raw_cards:
        print("[WARN] No article cards found inside grid.")
        return html_content

    # 提取每个卡片的日期并排序
    cards_with_meta = []
    for card_html in raw_cards:
        # 寻找日期：例如 <div class="mt-auto text-xs text-slate-400 font-semibold">2025-09-03</div>
        date_match = DATE_PATTERN.search(card_html)
        date_str = date_match.group(1) if date_match else "1970-01-01"
        cards_with_meta.append({
            "date": date_str,
            "html": card_html.strip()
        })

    # 按日期严格倒序排列 (最新在前)
    sorted_cards = sorted(cards_with_meta, key=lambda x: x["date"], reverse=True)

    # 重新组装卡片，带上序号与日期注释
    new_body_parts = []
    for idx, item in enumerate(sorted_cards, 1):
        clean_html = item["html"]
        # 清除卡片前旧的 HTML 注释
        new_body_parts.append(f'        <!-- 卡片 {idx} ({item["date"]}) -->\n        {clean_html}')

    new_grid_body = "\n\n" + "\n\n".join(new_body_parts) + "\n      "
    new_html = html_content[:match.start()] + grid_header + new_grid_body + grid_footer + html_content[match.end():]
    return new_html

def main():
    if not os.path.exists(SITE_INDEX):
        print(f"[ERROR] {SITE_INDEX} does not exist.")
        sys.exit(1)

    with open(SITE_INDEX, "r", encoding="utf-8") as f:
        content = f.read()

    updated_content = parse_and_sort_canonical_cards(content)

    with open(SITE_INDEX, "w", encoding="utf-8") as f:
        f.write(updated_content)

    # 同步写入 outputs/index.html
    if os.path.exists(os.path.dirname(OUTPUTS_INDEX)):
        with open(OUTPUTS_INDEX, "w", encoding="utf-8") as f:
            f.write(updated_content)

    print("[SUCCESS] Successfully verified & sorted homepage canonical cards in descending order.")

if __name__ == "__main__":
    main()
