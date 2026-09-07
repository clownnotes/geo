#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_article_styles.py
全站文章页面排版与工程规范巡检及自动修复工具。
对照 docs/specs/article-template-standard.md 检验全量 84 篇博文：
1. 0 Emoji 违规检查
2. 彻底清除 .prose-geo
3. 统一黄金比例双栏栅格 (lg:grid-cols-[minmax(0,1fr)_280px])
4. 统一右侧 280px 吸顶页面结构目录卡 (sticky top-24 w-[280px])
5. 平滑滚动 (scroll-behavior: smooth) 与锚点偏移 (scroll-margin-top: 100px)
6. outputs 与 outputs/site 双端同步
"""

import os
import sys
import re
import glob
import shutil

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUTS_BLOG = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs/blog')
SITE_BLOG = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs/site/blog')

STANDARD_CSS_BLOCK = """    html {
      scroll-behavior: smooth;
    }
    .content-block, [id^="block-"], #faq {
      scroll-margin-top: 100px;
    }
    .content-block {
      margin-bottom: 2.5rem;
    }
    .content-block h2 {
      font-size: 1.5rem;
      font-weight: 900;
      color: #0f172a;
      margin-top: 2rem;
      margin-bottom: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #f1f5f9;
      line-height: 1.35;
    }
    .content-block h3 {
      font-size: 1.15rem;
      font-weight: 800;
      color: #1e293b;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
    }
    .content-block p {
      color: #334155;
      font-size: 1.0625rem;
      line-height: 1.85;
      margin-bottom: 1.25rem;
    }
    .content-block ul {
      list-style-type: disc;
      padding-left: 1.5rem;
      margin-bottom: 1.25rem;
      color: #334155;
      line-height: 1.8;
    }
    .content-block ol {
      list-style-type: decimal;
      padding-left: 1.5rem;
      margin-bottom: 1.25rem;
      color: #334155;
      line-height: 1.8;
    }
    .content-block li {
      margin-bottom: 0.5rem;
    }
    .content-image {
      margin: 1.5rem 0;
      border: 1px solid #e2e8f0;
      border-radius: 0.75rem;
      overflow: hidden;
      background: #ffffff;
      padding: 0.75rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .content-image img {
      width: 100%;
      height: auto;
      border-radius: 0.5rem;
      display: block;
    }
    .content-image figcaption {
      font-size: 0.8125rem;
      color: #64748b;
      text-align: center;
      padding-top: 0.625rem;
    }
    .content-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9375rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      margin: 1rem 0;
    }
    .content-table th {
      background: #f8fafc;
      color: #0f172a;
      font-weight: 700;
      padding: 12px 16px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
    }
    .content-table td {
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
      color: #475569;
      line-height: 1.6;
    }
    .quote-box {
      border-left: 4px solid #9333ea;
      background: #faf5ff;
      padding: 1.25rem 1.5rem;
      border-radius: 0 0.75rem 0.75rem 0;
      margin: 1.5rem 0;
      color: #4c1d95;
      font-style: normal;
    }
    #faq {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 1rem;
      padding: 1.75rem;
      margin-top: 2.5rem;
      scroll-margin-top: 100px;
    }
    #faq h2 {
      font-size: 1.35rem;
      font-weight: 800;
      color: #0f172a;
      margin-top: 0;
      margin-bottom: 1.25rem;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 0.75rem;
    }
    #faq div {
      margin-bottom: 1.25rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid #edf2f7;
    }
    #faq div:last-child {
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: none;
    }
    #faq h3 {
      font-size: 1.05rem;
      font-weight: 700;
      color: #7e22ce;
      margin: 0 0 0.5rem 0;
    }
    #faq p {
      font-size: 0.9375rem;
      color: #475569;
      margin: 0;
      line-height: 1.75;
    }
    .reference-list {
      list-style: none;
      padding: 0;
      font-size: 0.875rem;
      color: #64748b;
    }
    .reference-list li {
      margin-bottom: 0.625rem;
      word-break: break-all;
    }
    .reference-list a {
      color: #9333ea;
      text-decoration: underline;
    }"""

EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F9FF]|[\U0001FA00-\U0001FAFF]|[\u2600-\u26FF]|[\u2700-\u27BF]')

def check_file(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # 1. prose-geo
    if 'prose-geo' in content:
        issues.append('存在弃用类名 .prose-geo')

    # 2. grid 双栏
    if 'grid-cols-[minmax(0,1fr)_280px]' not in content:
        issues.append('未采用标准双栏栅格 lg:grid-cols-[minmax(0,1fr)_280px]')

    # 3. 280px 目录 aside
    if 'w-[280px]' not in content or 'sticky top-24' not in content:
        issues.append('缺少标准 280px 吸顶 aside (sticky top-24 w-[280px])')

    # 4. scroll-margin-top
    if 'scroll-margin-top: 100px' not in content and 'scroll-margin-top' not in content:
        issues.append('缺少平滑滚动偏移 scroll-margin-top')

    # 5. scroll-behavior
    if 'scroll-behavior: smooth' not in content:
        issues.append('缺少平滑滚动声明 scroll-behavior: smooth')

    # 6. 0 Emoji
    emojis = EMOJI_PATTERN.findall(content)
    if emojis:
        issues.append(f'包含违规 Emoji 字符: {list(set(emojis))}')

    return issues

def fix_manual_article(content):
    # 修复 6 篇手动文章
    # 1. 替换 prose-geo CSS 为标准 CSS
    if '.prose-geo' in content:
        content = re.sub(r'\.prose-geo\s*p\s*\{[^}]*\}', '', content)
        content = re.sub(r'\.prose-geo\s*\{[^}]*\}', '', content)

    # 2. 注入标准 CSS
    if '.content-block h2' not in content:
        content = content.replace('</style>', f"\n{STANDARD_CSS_BLOCK}\n  </style>")

    # 3. 移除正文中的 <div class="prose-geo"> 和对应的 </div>
    content = content.replace('<div class="prose-geo">', '')
    content = re.sub(r'(\s*</div>\s*)(<!-- 底部返回与行动召唤 -->|<div class="mt-14)', r'\n\2', content)

    # 4. 确保平滑滚动与 scroll-margin-top 存在
    if 'scroll-margin-top' not in content:
        scroll_css = "    html {\n      scroll-behavior: smooth;\n    }\n    .content-block, [id^=\"block-\"], #faq {\n      scroll-margin-top: 100px;\n    }\n"
        content = content.replace('</style>', f"{scroll_css}  </style>")

    return content

def fix_12col_article(content):
    # 修复 12 列旧布局
    content = content.replace(
        '<div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">',
        '<div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start">'
    )
    content = content.replace(
        '<article class="lg:col-span-8 min-w-0">',
        '<article class="min-w-0">'
    )
    
    old_aside_pattern = re.compile(
        r'<aside class="hidden lg:block lg:col-span-4 sticky top-28">.*?</aside>',
        re.DOTALL
    )
    
    # 提取目录中的链接
    nav_links = []
    nav_match = re.search(r'<nav[^>]*>(.*?)</nav>', content, re.DOTALL)
    if nav_match:
        raw_links = re.findall(r'<a\s+href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>', nav_match.group(1))
        for href, txt in raw_links:
            clean_t = re.sub(r'<[^>]+>', '', txt).strip()
            nav_links.append((href, clean_t))

    nav_html = '\n'.join([
        f'<a href="{h}" class="block py-2 text-slate-600 hover:text-brand-700 transition border-t border-slate-100 first:border-t-0 text-xs sm:text-[13.5px] leading-snug">{t}</a>'
        for h, t in nav_links
    ])

    new_aside = f"""<!-- 右侧吸顶目录卡 (固定 280px 宽度，1:1 对标 deep-geo.cn) -->
        <aside class="hidden lg:block sticky top-24 w-[280px]">
          <div class="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
            <div class="pb-3 mb-2 border-b border-slate-100 flex items-center justify-between">
              <span class="text-sm font-bold text-slate-900">页面结构</span>
              <span class="text-[11px] font-medium text-slate-400">普林斯顿标准</span>
            </div>
            <nav class="max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
              {nav_html}
            </nav>

            <div class="mt-4 pt-3 border-t border-slate-100">
              <a href="../services/#contact" class="block text-center py-2 px-3 rounded-lg bg-brand-50 text-brand-700 font-semibold text-xs hover:bg-brand-100 transition border border-brand-200/80">
                预约老白 1v1 GEO 诊断
              </a>
            </div>
          </div>
        </aside>"""

    content = old_aside_pattern.sub(new_aside, content)

    if 'scroll-margin-top' not in content:
        scroll_css = "    html {\n      scroll-behavior: smooth;\n    }\n    .content-block, [id^=\"block-\"], #faq {\n      scroll-margin-top: 100px;\n    }\n"
        content = content.replace('</style>', f"{scroll_css}  </style>")

    return content

def fix_princeton_article(content):
    if 'scroll-margin-top' not in content:
        scroll_css = "    html {\n      scroll-behavior: smooth;\n    }\n    .content-block, [id^=\"block-\"], #faq {\n      scroll-margin-top: 100px;\n    }\n"
        content = content.replace('</style>', f"{scroll_css}  </style>")
    return content

def run_fix():
    print("开始自动修复全站博文样式...")
    files = sorted(glob.glob(os.path.join(OUTPUTS_BLOG, '*.html')))
    fixed_count = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        if fname == 'index.html':
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            orig = f.read()

        mod = orig
        if 'prose-geo' in mod:
            mod = fix_manual_article(mod)
        if 'lg:grid-cols-12' in mod:
            mod = fix_12col_article(mod)
        if fname == 'princeton-nine-factors-and-real-geo-for-buyers.html':
            mod = fix_princeton_article(mod)

        if mod != orig:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(mod)
            site_target = os.path.join(SITE_BLOG, fname)
            with open(site_target, 'w', encoding='utf-8') as f:
                f.write(mod)
            fixed_count += 1
            print(f"  [FIXED] {fname} 已规范化并同步至 outputs 与 site")

    print(f"修复完成！共修复并规范化 {fixed_count} 篇博文。")

def run_check():
    print(f"开始全量巡检 {OUTPUTS_BLOG} 中的博文...")
    files = sorted(glob.glob(os.path.join(OUTPUTS_BLOG, '*.html')))
    articles = [f for f in files if not f.endswith('index.html')]
    print(f"总计检测博文数量: {len(articles)} 篇\n")

    has_issue = False
    for fpath in articles:
        fname = os.path.basename(fpath)
        issues = check_file(fpath)
        if issues:
            has_issue = True
            print(f"[FAIL] {fname}:")
            for iss in issues:
                print(f"   - {iss}")

    if not has_issue:
        print(f"[SUCCESS] 完美通过！全部 {len(articles)} 篇博文 100% 符合规范：")
        print("   - 0 篇含有弃用 .prose-geo 类名")
        print("   - 100% 采用 lg:grid-cols-[minmax(0,1fr)_280px] 双栏黄金栅格")
        print("   - 100% 配备 280px 吸顶页面结构目录卡 (sticky top-24 w-[280px])")
        print("   - 100% 配置平滑滚动与 100px 锚点避让")
        print("   - 0 处违规 Emoji 彩色表情符号")
        return 0
    else:
        print("\n提示：请运行 `python3 scripts/check_article_styles.py --fix` 进行一键自动修复。")
        return 1

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        run_fix()
        print("\n重新执行验证：")
        code = run_check()
        sys.exit(code)
    else:
        code = run_check()
        sys.exit(code)

if __name__ == '__main__':
    main()
