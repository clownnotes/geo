#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_deepgeo_blog.py
克隆并本地化 DeepGEO 全量 77 篇博客文章，实施实体置换（DeepGEO -> 邻里GEO，余果 -> 老白），
遵循普林斯顿 9 因子规范，杜绝任何 Emoji，生成完整的 NextGEO 知识库与索引系统。
"""

import os
import re
import sys
import json
import subprocess
import shutil
import concurrent.futures
from urllib.parse import urljoin

SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../projects/nextgeo/outputs/site'))
OUTPUTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../projects/nextgeo/outputs'))
BASE_URL = 'https://deep-geo.cn'

ARTICLES = [
    # /ai-search/ (35篇)
    '/ai-search/ai-agents-unbundle-search-direct-answers.html',
    '/ai-search/ai-citation-not-equal-recommendation.html',
    '/ai-search/ai-citation-pipeline-retrieval-to-generation.html',
    '/ai-search/ai-crawler-accessibility-checklist.html',
    '/ai-search/ai-crawler-log-analysis-bots-reading-content.html',
    '/ai-search/ai-overview-top-10-traditional-ranking.html',
    '/ai-search/ai-search-attribution-black-hole.html',
    '/ai-search/ai-search-brand-selection-tournament.html',
    '/ai-search/ai-search-ranking-mechanism.html',
    '/ai-search/ai-sentiment-analysis-brand-mentions.html',
    '/ai-search/ai-statistics-2026-geo-trends.html',
    '/ai-search/ai-visibility-benchmark-competitor-comparison.html',
    '/ai-search/brand-ai-search-question-monitoring-volume.html',
    '/ai-search/brand-visibility-differences-across-prompts.html',
    '/ai-search/chinese-content-ai-citation-patterns.html',
    '/ai-search/chinese-geo-benchmark-page-structures-ai-citations.html',
    '/ai-search/decode-llm-visible-in-generative-ai-search.html',
    '/ai-search/doubao-deepseek-citation-source-volatility.html',
    '/ai-search/doubao-deepseek-content-preferences.html',
    '/ai-search/doubao-deepseek-yuanbao-citation-sources-differences.html',
    '/ai-search/doubao-prompts-and-seo-for-marketers.html',
    '/ai-search/how-ai-understands-business-entity-modeling.html',
    '/ai-search/how-models-judge-trustworthy-sources.html',
    '/ai-search/how-to-get-ai-citations-8000-citation-data.html',
    '/ai-search/llm-cognitive-match-brand-recognition.html',
    '/ai-search/monitor-ai-brand-product-price-errors.html',
    '/ai-search/prompt-drift-monitoring-weekly-retests.html',
    '/ai-search/prompt-hit-rate-benchmark-brand-category-comparison.html',
    '/ai-search/robots-txt-llm-ai-access-protocol.html',
    '/ai-search/source-ranking-ai-answers-brand-value.html',
    '/ai-search/travel-lifestyle-ai-overview-zero-click.html',
    '/ai-search/uncertain-future-of-chinese-geo.html',
    '/ai-search/what-is-llms-txt-should-you-add.html',
    '/ai-search/why-ai-cites-third-party-sites-over-brand-websites.html',
    '/ai-search/why-companies-invisible-ai-search.html',

    # /case-studies/ (9篇)
    '/case-studies/b2b-manufacturing-ai-product-capabilities-use-cases.html',
    '/case-studies/b2b-saas-ai-best-software-recommendations.html',
    '/case-studies/education-training-ai-search-recommendations.html',
    '/case-studies/geo-strategy-for-education-industry.html',
    '/case-studies/healthcare-content-geo-trust-risks.html',
    '/case-studies/local-service-providers-doubao-deepseek-recommendations.html',
    '/case-studies/media-publishing-ai-citation-brand-influence.html',
    '/case-studies/professional-services-geo-clinics.html',
    '/case-studies/professional-services-geo-lawyers.html',

    # /geo/ (33篇)
    '/geo/ai-as-intermediary-brand-description-management.html',
    '/geo/ai-citation-detection-tool-design.html',
    '/geo/brand-marketing-kpi-in-ai-era.html',
    '/geo/brand-most-important-geo-asset-2026.html',
    '/geo/brand-search-volume-vs-ai-cognition.html',
    '/geo/build-ai-readable-knowledge-architecture.html',
    '/geo/can-ai-access-your-brand-information.html',
    '/geo/china-social-media-seo-search-social-ai.html',
    '/geo/chinese-geo-reputation-not-ranking.html',
    '/geo/content-blocks-paragraphs-tables-ai-extraction.html',
    '/geo/content-for-users-and-ai-citations.html',
    '/geo/enterprise-website-importance-2026-ai-era.html',
    '/geo/entity-clarity-ai-brand-recommendation.html',
    '/geo/entity-seo-and-geo-brand-understanding.html',
    '/geo/faq-structure-improves-ai-citation-rate.html',
    '/geo/geo-agency-deliverable-service-packages.html',
    '/geo/geo-brand-marketing-or-technical-work.html',
    '/geo/geo-content-knowledge-units.html',
    '/geo/geo-execution-roadmap-zero-to-one.html',
    '/geo/geo-monitoring-tool-metrics.html',
    '/geo/how-to-rewrite-article-for-ai-citations.html',
    '/geo/information-gain-content-ai-citations.html',
    '/geo/is-geo-poisoning-ai-values-law-technology.html',
    '/geo/marketing-geo-budget-allocation-2026-ai-era.html',
    '/geo/media-distribution-waste-in-ai-search-era.html',
    '/geo/media-partnership-ai-visibility-research.html',
    '/geo/official-website-content-ai-era.html',
    '/geo/ranking-competition-to-explanation-power.html',
    '/geo/remove-ai-tone-from-website-articles.html',
    '/geo/schema-markdown-ai-readable-webpage.html',
    '/geo/seo-geo-aio-llmo-differences.html',
    '/geo/third-party-authority-signals-media-rankings-reviews-community.html',
    '/geo/topical-authority-ai-search-expert-recognition.html'
]

CATEGORY_MAP = {
    'geo': {'name': 'GEO 实战', 'badge': 'GEO 实战', 'slug': 'geo'},
    'ai-search': {'name': 'AI 搜索认知', 'badge': 'AI 搜索认知', 'slug': 'ai-search'},
    'case-studies': {'name': '行业案例', 'badge': '行业案例', 'slug': 'case-studies'},
}

def strip_emoji(text):
    if not text:
        return ''
    clean_chars = []
    for ch in text:
        cp = ord(ch)
        if (0x1F300 <= cp <= 0x1F5FF) or \
           (0x1F600 <= cp <= 0x1F64F) or \
           (0x1F680 <= cp <= 0x1F6FF) or \
           (0x1F900 <= cp <= 0x1F9FF) or \
           (0x1FA70 <= cp <= 0x1FAFF) or \
           (0x2600 <= cp <= 0x26FF) or \
           (0x2700 <= cp <= 0x27BF) or \
           (0xFE00 <= cp <= 0xFE0F):
            continue
        clean_chars.append(ch)
    return ''.join(clean_chars).strip()

def download_file(url, local_path):
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return True
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    cmd = ['curl', '-s', '-L', '--max-time', '30', '-A', 'Mozilla/5.0', url, '-o', local_path]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0 and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return True
    return False

def fetch_html(rel_url):
    full_url = BASE_URL + rel_url
    cmd = ['curl', '-s', '-L', '--max-time', '20', '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', full_url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout:
        return res.stdout
    return None

def parse_article(rel_url, html):
    # 分类检测
    parts = rel_url.strip('/').split('/')
    cat_key = parts[0] if len(parts) > 1 else 'geo'
    cat_info = CATEGORY_MAP.get(cat_key, CATEGORY_MAP['geo'])
    filename = os.path.basename(rel_url)
    slug = filename.replace('.html', '')

    # 标题
    title_m = re.search(r'<title>(.*?)</title>', html)
    raw_title = title_m.group(1) if title_m else ''
    title = raw_title.split('｜')[0].split('|')[0].strip()
    title = title.replace('DeepGEO', '邻里GEO').replace('余果', '老白')

    h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    h1 = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip() if h1_m else title
    h1 = h1.replace('DeepGEO', '邻里GEO').replace('余果', '老白')

    # 描述
    desc_m = re.search(r'<meta\s+name=[\"\']description[\"\']\s+content=[\"\'](.*?)[\"\']', html)
    description = desc_m.group(1).strip() if desc_m else ''
    description = description.replace('DeepGEO', '邻里GEO').replace('余果', '老白')

    keywords_m = re.search(r'<meta\s+name=[\"\']keywords[\"\']\s+content=[\"\'](.*?)[\"\']', html)
    keywords = keywords_m.group(1).strip() if keywords_m else f"{title}, GEO优化, 邻里GEO, 生成式引擎优化"
    keywords = keywords.replace('DeepGEO', '邻里GEO').replace('余果', '老白').replace('deep-geo.cn', 'nextgeo.baicl.cc')

    # 日期
    date_m = re.search(r'<div class=\"article-meta\">.*?<span>(\d{4}-\d{2}-\d{2})</span>', html, re.DOTALL)
    if not date_m:
        date_m = re.search(r'(\d{4}-\d{2}-\d{2})', html)
    publish_date = date_m.group(1) if date_m else '2026-01-01'

    # 阅读时长
    read_m = re.search(r'<div class=\"article-meta\">.*?<span>(\d+\s*min)</span>', html, re.DOTALL)
    read_time = read_m.group(1).replace('min', '分钟').strip() if read_m else '7 分钟'

    # Hero Description (导读)
    hero_m = re.search(r'<p class=\"article-hero__description\">(.*?)</p>', html, re.DOTALL)
    if hero_m:
        hero_desc = re.sub(r'<[^>]+>', '', hero_m.group(1)).strip()
    else:
        hero_desc = description

    # 正文 <article ...>
    art_m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
    raw_article = art_m.group(1) if art_m else ''

    # 提取并下载正文插图
    inner_imgs = re.findall(r'<img[^>]+src=[\"\']([^\"\']+)[\"\']', raw_article)
    for img_src in inner_imgs:
        if img_src.startswith('/assets/'):
            img_url = BASE_URL + img_src
            local_img_path = os.path.join(SITE_ROOT, img_src.lstrip('/'))
            download_file(img_url, local_img_path)

    # 封面图
    cover_src = f"/assets/article-covers/{slug}.png"
    cover_url = BASE_URL + cover_src
    local_cover_path = os.path.join(SITE_ROOT, cover_src.lstrip('/'))
    has_cover = download_file(cover_url, local_cover_path)

    # 目录导航 (TOC)
    toc_m = re.search(r'<aside class=\"toc-card\"[^>]*>(.*?)</aside>', html, re.DOTALL)
    toc_items = []
    if toc_m:
        for href, text in re.findall(r'<a[^>]+href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>', toc_m.group(1)):
            clean_t = re.sub(r'<[^>]+>', '', text).strip()
            clean_t = strip_emoji(clean_t)
            if clean_t:
                toc_items.append((href, clean_t))

    # 内容清理与品牌实体置换
    clean_article = raw_article
    clean_article = re.sub(r'<!--\[-->|<!--\]-->|<!---->', '', clean_article)

    # 实体置换
    clean_article = clean_article.replace('DeepGEO', '邻里GEO')
    clean_article = clean_article.replace('余果', '老白')
    clean_article = clean_article.replace('前腾讯技术专家', '资深全栈工程师与GEO架构师')
    clean_article = clean_article.replace('现居深圳', '位于徐州，专注服务淮海经济区及全国B2B出海与制造业')
    clean_article = clean_article.replace('https://deep-geo.cn', 'https://nextgeo.baicl.cc')
    clean_article = clean_article.replace('deep-geo.cn', 'nextgeo.baicl.cc')

    # 路径转换
    clean_article = clean_article.replace('/assets/article-images/', '../assets/article-images/')
    clean_article = clean_article.replace('/assets/author-yuguo.png', '../assets/logo.jpg')
    clean_article = clean_article.replace('/services/#contact', '../services/#contact')
    clean_article = clean_article.replace('/services/', '../services/')
    clean_article = clean_article.replace('/about/', '../about/')
    clean_article = clean_article.replace('href="/geo/', 'href="./')
    clean_article = clean_article.replace('href="/ai-search/', 'href="./')
    clean_article = clean_article.replace('href="/case-studies/', 'href="./')
    clean_article = clean_article.replace('href="/blog/', 'href="./')

    # 表格美化（使用正则匹配带类名与属性的 table 标签，避免 </div> 悬空破坏双栏栅格）
    clean_article = re.sub(r'<table[^>]*>', '<div class="overflow-x-auto my-6"><table class="content-table">', clean_article)
    clean_article = clean_article.replace('</table>', '</table></div>')

    # FAQ 容器美化
    clean_article = re.sub(r'<section id=[\"\']faq[\"\'][^>]*>', '<section id="faq" class="content-block mt-12 p-6 sm:p-8 rounded-2xl bg-slate-50 border border-slate-200/90 shadow-2xs">', clean_article)

    # 零 Emoji 过滤
    title = strip_emoji(title)
    h1 = strip_emoji(h1)
    description = strip_emoji(description)
    hero_desc = strip_emoji(hero_desc)
    clean_article = strip_emoji(clean_article)

    return {
        'rel_url': rel_url,
        'filename': filename,
        'slug': slug,
        'cat_key': cat_key,
        'cat_name': cat_info['name'],
        'cat_badge': cat_info['badge'],
        'title': title,
        'h1': h1,
        'description': description,
        'keywords': keywords,
        'publish_date': publish_date,
        'read_time': read_time,
        'hero_desc': hero_desc,
        'clean_article': clean_article,
        'toc_items': toc_items,
        'cover_rel': f"../assets/article-covers/{slug}.png" if has_cover else None
    }

def render_article_html(data):
    # 构建 TOC HTML
    toc_links_html = ''
    if data['toc_items']:
        for href, text in data['toc_items']:
            toc_links_html += f'<a href="{href}" class="block py-2 text-slate-600 hover:text-brand-700 transition border-t border-slate-100 first:border-t-0 text-xs sm:text-[13.5px] leading-snug">{text}</a>\n'
    else:
        toc_links_html = '<a href="#article-start" class="block py-2 text-slate-600 hover:text-brand-700 transition text-xs sm:text-[13.5px]">回到顶部</a>'

    # 构建 Schema.org JSON-LD
    schema_json = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "TechArticle",
                "@id": f"https://nextgeo.baicl.cc/blog/{data['filename']}#article",
                "headline": data['h1'],
                "description": data['hero_desc'],
                "inLanguage": "zh-CN",
                "datePublished": f"{data['publish_date']}T08:00:00+08:00",
                "dateModified": f"{data['publish_date']}T08:00:00+08:00",
                "author": {
                    "@type": "Person",
                    "name": "老白",
                    "jobTitle": "创始人 / GEO架构师"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "邻里GEO",
                    "logo": "https://nextgeo.baicl.cc/assets/logo.jpg"
                }
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    { "@type": "ListItem", "position": 1, "name": "首页", "item": "https://nextgeo.baicl.cc/" },
                    { "@type": "ListItem", "position": 2, "name": "博客", "item": "https://nextgeo.baicl.cc/blog/" },
                    { "@type": "ListItem", "position": 3, "name": data['cat_name'], "item": f"https://nextgeo.baicl.cc/blog/?cat={data['cat_key']}" },
                    { "@type": "ListItem", "position": 4, "name": data['title'], "item": f"https://nextgeo.baicl.cc/blog/{data['filename']}" }
                ]
            }
        ]
    }

    schema_str = json.dumps(schema_json, ensure_ascii=False, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data['title']}｜邻里GEO</title>
  <meta name="description" content="{data['description']}">
  <meta name="keywords" content="{data['keywords']}">
  <link rel="canonical" href="https://nextgeo.baicl.cc/blog/{data['filename']}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="icon" href="../assets/logo.jpg" type="image/jpeg">

  <script type="application/ld+json">
{schema_str}
  </script>

  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: "#faf5ff", 100: "#f3e8ff", 200: "#e9d5ff", 300: "#d8b4fe",
              400: "#c084fc", 500: "#a855f7", 600: "#9333ea", 700: "#7e22ce",
              800: "#6b21a8", 900: "#581c87"
            }}
          }},
          fontFamily: {{
            sans: ['-apple-system', 'BlinkMacSystemFont', '"PingFang SC"', '"Hiragino Sans GB"', '"Microsoft YaHei"', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
  <style>
    .site-shell {{
      min-height: 100vh;
      background-color: #faf5ff;
      background-image: 
        radial-gradient(circle at 84% 4%, rgba(147, 51, 234, 0.12), transparent 28%),
        linear-gradient(90deg, rgba(147, 51, 234, 0.05) 1px, transparent 1px),
        linear-gradient(0deg, rgba(147, 51, 234, 0.05) 1px, transparent 1px);
      background-size: 100% 100%, 72px 72px, 72px 72px;
    }}
    .geo-container {{
      width: min(1180px, calc(100% - 40px));
      margin-left: auto;
      margin-right: auto;
    }}
    .content-block {{
      margin-bottom: 2.5rem;
    }}
    .content-block h2 {{
      font-size: 1.5rem;
      font-weight: 900;
      color: #0f172a;
      margin-top: 2rem;
      margin-bottom: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #f1f5f9;
      line-height: 1.35;
    }}
    .content-block h3 {{
      font-size: 1.15rem;
      font-weight: 800;
      color: #1e293b;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
    }}
    .content-block p {{
      color: #334155;
      font-size: 1.0625rem;
      line-height: 1.85;
      margin-bottom: 1.25rem;
    }}
    .content-block ul {{
      list-style-type: disc;
      padding-left: 1.5rem;
      margin-bottom: 1.25rem;
      color: #334155;
      line-height: 1.8;
    }}
    .content-block ol {{
      list-style-type: decimal;
      padding-left: 1.5rem;
      margin-bottom: 1.25rem;
      color: #334155;
      line-height: 1.8;
    }}
    .content-block li {{
      margin-bottom: 0.5rem;
    }}
    .content-image {{
      margin: 1.5rem 0;
      border: 1px solid #e2e8f0;
      border-radius: 0.75rem;
      overflow: hidden;
      background: #ffffff;
      padding: 0.75rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .content-image img {{
      width: 100%;
      height: auto;
      border-radius: 0.5rem;
      display: block;
    }}
    .content-image figcaption {{
      font-size: 0.8125rem;
      color: #64748b;
      text-align: center;
      padding-top: 0.625rem;
    }}
    .content-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9375rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      margin: 1rem 0;
    }}
    .content-table th {{
      background: #f8fafc;
      color: #0f172a;
      font-weight: 700;
      padding: 12px 16px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
    }}
    .content-table td {{
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
      color: #475569;
      line-height: 1.6;
    }}
    #faq {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 1rem;
      padding: 1.75rem;
      margin-top: 2.5rem;
    }}
    #faq h2 {{
      font-size: 1.35rem;
      font-weight: 800;
      color: #0f172a;
      margin-top: 0;
      margin-bottom: 1.25rem;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 0.75rem;
    }}
    #faq div {{
      margin-bottom: 1.25rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid #edf2f7;
    }}
    #faq div:last-child {{
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: none;
    }}
    #faq h3 {{
      font-size: 1.05rem;
      font-weight: 700;
      color: #7e22ce;
      margin: 0 0 0.5rem 0;
    }}
    #faq p {{
      font-size: 0.9375rem;
      color: #475569;
      margin: 0;
      line-height: 1.75;
    }}
    .reference-list {{
      list-style: none;
      padding: 0;
      font-size: 0.875rem;
      color: #64748b;
    }}
    .reference-list li {{
      margin-bottom: 0.625rem;
      word-break: break-all;
    }}
    .reference-list a {{
      color: #9333ea;
      text-decoration: underline;
    }}
    html {{
      scroll-behavior: smooth;
    }}
    .content-block, [id^="block-"], #faq {{
      scroll-margin-top: 100px;
    }}
  </style>
</head>
<body class="site-shell text-slate-800 font-sans antialiased selection:bg-brand-200 selection:text-brand-900 min-h-screen flex flex-col">

  <!-- 顶部导航栏 -->
  <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-brand-200/80 shadow-xs">
    <div class="geo-container h-20 flex items-center justify-between gap-6">
      <a href="../" class="flex items-center gap-3.5 group">
        <div class="relative">
          <img src="../assets/logo.jpg" alt="老白 / 邻里GEO" class="w-11 h-11 rounded-full border border-brand-300 shadow-xs object-cover">
          <span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-white"></span>
        </div>
        <div>
          <div class="font-black text-xl text-slate-900 leading-none flex items-center">
            NextGEO <span class="text-brand-600 font-extrabold ml-1.5">邻里GEO</span>
          </div>
          <div class="text-xs text-slate-500 font-medium tracking-tight mt-1">中文企业级GEO方法研究与实战</div>
        </div>
      </a>

      <!-- 导航项 -->
      <nav class="flex items-center gap-6 sm:gap-8 text-sm sm:text-base font-semibold text-slate-600">
        <a href="../" class="hover:text-brand-600 transition">首页</a>
        <a href="./" class="text-brand-700 font-bold border-b-2 border-brand-600 pb-1">博客</a>
        <a href="../services/" class="hover:text-brand-600 transition">服务</a>
        <a href="../about/" class="hover:text-brand-600 transition">关于</a>
      </nav>
    </div>
  </header>

  <!-- 文章正文主体 -->
  <main id="article-start" class="flex-grow py-10 w-full">
    <div class="geo-container">
      
      <!-- 面包屑与文章头信息 -->
      <div class="max-w-4xl mb-8">
        <div class="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
          <a href="../" class="hover:text-brand-600">首页</a>
          <span>/</span>
          <a href="./" class="hover:text-brand-600">博客</a>
          <span>/</span>
          <span class="text-brand-700">{data['cat_badge']}</span>
        </div>

        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-6">
          {data['h1']}
        </h1>

        <div class="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-slate-500 pb-6 border-b border-slate-200">
          <span class="font-semibold text-slate-700">作者: 老白（邻里GEO架构师）</span>
          <span>·</span>
          <time datetime="{data['publish_date']}">发布日期: {data['publish_date']}</time>
          <span>·</span>
          <span>阅读时长: {data['read_time']}</span>
        </div>

        <!-- 结论先行导读卡 (普林斯顿因子 1) -->
        <div class="mt-6 p-6 rounded-xl border border-brand-300/80 border-l-4 border-l-brand-600 bg-white shadow-xs">
          <strong class="text-slate-900 font-bold text-base block mb-2">结论先行 (Executive Summary)：</strong>
          <p class="text-slate-700 text-sm sm:text-base leading-relaxed m-0">
            {data['hero_desc']}
          </p>
        </div>
      </div>

      <!-- 双栏布局：正文 (左) + 页面结构目录 (右) -->
      <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start">
        
        <!-- 左侧文章内容 -->
        <article class="min-w-0">
          {data['clean_article']}

          <!-- 底部返回与行动召唤 -->
          <div class="mt-14 pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <a href="../blog/" class="text-brand-600 hover:text-brand-700 font-bold text-sm flex items-center gap-1.5 transition">
              <span>&larr;</span> 返回博客实战知识库
            </a>
            <a href="../services/#contact" class="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-slate-900 text-white font-semibold text-xs sm:text-sm hover:bg-brand-700 transition shadow-xs">
              与老白探讨企业的 GEO 落地方案
            </a>
          </div>
        </article>

        <!-- 右侧吸顶目录卡 (固定 280px 宽度，1:1 对标 deep-geo.cn) -->
        <aside class="hidden lg:block sticky top-24 w-[280px]">
          <div class="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
            <div class="pb-3 mb-2 border-b border-slate-100 flex items-center justify-between">
              <span class="text-sm font-bold text-slate-900">页面结构</span>
              <span class="text-[11px] font-medium text-slate-400">普林斯顿标准</span>
            </div>
            <nav class="max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
              {toc_links_html}
            </nav>

            <div class="mt-4 pt-3 border-t border-slate-100">
              <a href="../services/#contact" class="block text-center py-2 px-3 rounded-lg bg-brand-50 text-brand-700 font-semibold text-xs hover:bg-brand-100 transition border border-brand-200/80">
                预约老白 1v1 GEO 诊断
              </a>
            </div>
          </div>
        </aside>

      </div>

    </div>
  </main>

  <!-- 页脚 -->
  <footer class="border-t border-slate-200/90 py-10 text-slate-500 text-xs sm:text-sm bg-white/90 mt-16">
    <div class="geo-container flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <strong class="text-slate-900 font-bold">邻里GEO (NextGEO)</strong>
        <div class="text-slate-400 text-xs mt-0.5">中文企业级GEO方法研究与实战 · 淮海经济区</div>
      </div>
      <div class="flex items-center gap-4 text-slate-600 font-medium text-xs sm:text-sm">
        <a href="../services/#contact" class="hover:text-brand-600 transition">联系老白</a>
        <span>·</span>
        <a href="../llms.txt" class="hover:text-brand-600 transition font-mono">llms.txt</a>
        <span>·</span>
        <a href="../sitemap.xml" class="hover:text-brand-600 transition font-mono">sitemap.xml</a>
      </div>
    </div>
  </footer>

</body>
</html>
"""
    return html

def process_single_article(rel_url):
    html = fetch_html(rel_url)
    if not html:
        print(f"[FAIL] Could not fetch {rel_url}")
        return None
    try:
        data = parse_article(rel_url, html)
        rendered_html = render_article_html(data)

        # 保存到 site/blog/<filename>
        out_blog_path = os.path.join(SITE_ROOT, 'blog', data['filename'])
        os.makedirs(os.path.dirname(out_blog_path), exist_ok=True)
        with open(out_blog_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)

        # 也保存到 site/<category>/<filename> 保持多路由兼容
        cat_dir = os.path.join(SITE_ROOT, data['cat_key'])
        os.makedirs(cat_dir, exist_ok=True)
        cat_file_path = os.path.join(cat_dir, data['filename'])
        cat_rendered = rendered_html.replace('href="./"', 'href="../blog/"')
        with open(cat_file_path, 'w', encoding='utf-8') as f:
            f.write(cat_rendered)

        print(f"[OK] {data['cat_badge']} | {data['title'][:25]}... -> blog/{data['filename']}")
        return data
    except Exception as e:
        print(f"[ERROR] processing {rel_url}: {e}")
        return None

def generate_blog_index(all_articles):
    sorted_arts = sorted(all_articles, key=lambda x: x['publish_date'], reverse=True)
    total_cnt = len(sorted_arts)
    geo_cnt = sum(1 for a in sorted_arts if a['cat_key'] == 'geo')
    ai_cnt = sum(1 for a in sorted_arts if a['cat_key'] == 'ai-search')
    case_cnt = sum(1 for a in sorted_arts if a['cat_key'] == 'case-studies')

    cards_html = ''
    for a in sorted_arts:
        cover_img_tag = ''
        if a['cover_rel']:
            cover_img_tag = f'<div class="aspect-16/10 bg-slate-100 overflow-hidden border-b border-slate-100"><img src="{a["cover_rel"]}" alt="{a["title"]}" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition duration-300"></div>'
        else:
            cover_img_tag = f'<div class="aspect-16/10 bg-gradient-to-br from-brand-50 to-purple-100 border-b border-slate-100 flex items-center justify-center p-6 text-center"><span class="font-extrabold text-slate-400 text-sm">{a["cat_badge"]}</span></div>'

        cards_html += f"""
        <article class="article-item group bg-white rounded-2xl border border-slate-200/80 overflow-hidden hover:shadow-lg hover:border-brand-300 transition duration-200 flex flex-col" data-category="{a['cat_key']}">
          <a href="./{a['filename']}" class="block overflow-hidden">
            {cover_img_tag}
          </a>
          <div class="p-5 sm:p-6 flex flex-col flex-grow justify-between">
            <div>
              <div class="flex items-center justify-between gap-2 text-xs mb-3">
                <span class="font-bold px-2.5 py-0.5 rounded-full text-brand-700 bg-brand-50 border border-brand-200">{a['cat_badge']}</span>
                <time datetime="{a['publish_date']}" class="text-slate-400 font-medium">{a['publish_date']}</time>
              </div>
              <h2 class="text-lg font-bold text-slate-900 group-hover:text-brand-600 transition leading-snug line-clamp-2 mb-2">
                <a href="./{a['filename']}">{a['title']}</a>
              </h2>
              <p class="text-slate-600 text-xs sm:text-sm line-clamp-3 leading-relaxed mb-4">
                {a['hero_desc']}
              </p>
            </div>
            <div class="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>阅读约 {a['read_time']}</span>
              <a href="./{a['filename']}" class="font-bold text-brand-600 group-hover:translate-x-0.5 transition flex items-center gap-1">
                阅读全文 <span>&rarr;</span>
              </a>
            </div>
          </div>
        </article>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GEO实战知识库与博客｜NextGEO 邻里GEO</title>
  <meta name="description" content="NextGEO 邻里GEO 官方知识库：系统解构生成式引擎优化（GEO）、AI 搜索排名机制、模型引用底层逻辑与 B2B 行业落地案例，让企业知识在大模型时代被准确理解与首选推荐。">
  <meta name="keywords" content="GEO知识库, GEO博客, AI搜索优化, 生成式引擎优化, 豆包引用, DeepSeek推荐, 邻里GEO">
  <link rel="canonical" href="https://nextgeo.baicl.cc/blog/">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="icon" href="../assets/logo.jpg" type="image/jpeg">

  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: "#faf5ff", 100: "#f3e8ff", 200: "#e9d5ff", 300: "#d8b4fe",
              400: "#c084fc", 500: "#a855f7", 600: "#9333ea", 700: "#7e22ce",
              800: "#6b21a8", 900: "#581c87"
            }}
          }},
          fontFamily: {{
            sans: ['-apple-system', 'BlinkMacSystemFont', '"PingFang SC"', '"Hiragino Sans GB"', '"Microsoft YaHei"', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
  <style>
    .site-shell {{
      min-height: 100vh;
      background-color: #faf5ff;
      background-image: 
        radial-gradient(circle at 84% 4%, rgba(147, 51, 234, 0.12), transparent 28%),
        linear-gradient(90deg, rgba(147, 51, 234, 0.05) 1px, transparent 1px),
        linear-gradient(0deg, rgba(147, 51, 234, 0.05) 1px, transparent 1px);
      background-size: 100% 100%, 72px 72px, 72px 72px;
    }}
    .geo-container {{
      width: min(1180px, calc(100% - 40px));
      margin-left: auto;
      margin-right: auto;
    }}
    .aspect-16\\/10 {{
      aspect-ratio: 16 / 10;
    }}
  </style>
</head>
<body class="site-shell text-slate-800 font-sans antialiased selection:bg-brand-200 selection:text-brand-900 min-h-screen flex flex-col">

  <!-- 顶部导航栏 -->
  <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-brand-200/80 shadow-xs">
    <div class="geo-container h-20 flex items-center justify-between gap-6">
      <a href="../" class="flex items-center gap-3.5 group">
        <div class="relative">
          <img src="../assets/logo.jpg" alt="老白 / 邻里GEO" class="w-11 h-11 rounded-full border border-brand-300 shadow-xs object-cover">
          <span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-white"></span>
        </div>
        <div>
          <div class="font-black text-xl text-slate-900 leading-none flex items-center">
            NextGEO <span class="text-brand-600 font-extrabold ml-1.5">邻里GEO</span>
          </div>
          <div class="text-xs text-slate-500 font-medium tracking-tight mt-1">中文企业级GEO方法研究与实战</div>
        </div>
      </a>

      <!-- 导航项 -->
      <nav class="flex items-center gap-6 sm:gap-8 text-sm sm:text-base font-semibold text-slate-600">
        <a href="../" class="hover:text-brand-600 transition">首页</a>
        <a href="./" class="text-brand-700 font-bold border-b-2 border-brand-600 pb-1">博客</a>
        <a href="../services/" class="hover:text-brand-600 transition">服务</a>
        <a href="../about/" class="hover:text-brand-600 transition">关于</a>
      </nav>
    </div>
  </header>

  <!-- 页面主体 -->
  <main class="flex-grow py-12">
    <div class="geo-container">
      
      <!-- 博客 Hero 区 -->
      <div class="max-w-3xl mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-100 text-brand-800 text-xs font-bold uppercase tracking-wider mb-4 border border-brand-200">
          Knowledge Base & Research
        </div>
        <h1 class="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-5">
          GEO 实战知识库与深度博客
        </h1>
        <p class="text-slate-600 text-base sm:text-lg leading-relaxed">
          解构大模型搜索的召回、推理与生成逻辑。从普林斯顿 9 因子、实体建模、RAG 切片到真实行业落地打法，助企业赢得 AI 搜索时代的推荐权。
        </p>
      </div>

      <!-- 分类过滤筛选器 -->
      <div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-10 border-b border-slate-200/90 pb-6">
        <button onclick="filterCategory('all')" id="tab-all" class="cat-tab px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition bg-slate-900 text-white shadow-xs">
          全部 <span class="ml-1 opacity-80 font-normal">({total_cnt})</span>
        </button>
        <button onclick="filterCategory('geo')" id="tab-geo" class="cat-tab px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition bg-white text-slate-600 hover:bg-slate-100 border border-slate-200">
          GEO实战 <span class="ml-1 text-slate-400 font-normal">({geo_cnt})</span>
        </button>
        <button onclick="filterCategory('ai-search')" id="tab-ai-search" class="cat-tab px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition bg-white text-slate-600 hover:bg-slate-100 border border-slate-200">
          AI搜索认知 <span class="ml-1 text-slate-400 font-normal">({ai_cnt})</span>
        </button>
        <button onclick="filterCategory('case-studies')" id="tab-case-studies" class="cat-tab px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition bg-white text-slate-600 hover:bg-slate-100 border border-slate-200">
          行业案例 <span class="ml-1 text-slate-400 font-normal">({case_cnt})</span>
        </button>
      </div>

      <!-- 文章卡片网格 -->
      <div id="articles-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
        {cards_html}
      </div>

    </div>
  </main>

  <!-- 交互脚本 -->
  <script>
    function filterCategory(cat) {{
      const items = document.querySelectorAll('.article-item');
      items.forEach(el => {{
        if (cat === 'all' || el.getAttribute('data-category') === cat) {{
          el.style.display = 'flex';
        }} else {{
          el.style.display = 'none';
        }}
      }});

      document.querySelectorAll('.cat-tab').forEach(btn => {{
        btn.classList.remove('bg-slate-900', 'text-white');
        btn.classList.add('bg-white', 'text-slate-600', 'border', 'border-slate-200');
      }});

      const activeBtn = document.getElementById('tab-' + cat);
      if (activeBtn) {{
        activeBtn.classList.remove('bg-white', 'text-slate-600', 'border', 'border-slate-200');
        activeBtn.classList.add('bg-slate-900', 'text-white');
      }}

      const url = new URL(window.location);
      if (cat === 'all') {{
        url.searchParams.delete('section');
      }} else {{
        url.searchParams.set('section', cat);
      }}
      window.history.replaceState({{}}, '', url);
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      const params = new URLSearchParams(window.location.search);
      const sec = params.get('section');
      if (sec && ['geo', 'ai-search', 'case-studies'].includes(sec)) {{
        filterCategory(sec);
      }}
    }});
  </script>

  <!-- 页脚 -->
  <footer class="border-t border-slate-200/90 py-10 text-slate-500 text-xs sm:text-sm bg-white/90 mt-16">
    <div class="geo-container flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <strong class="text-slate-900 font-bold">邻里GEO (NextGEO)</strong>
        <div class="text-slate-400 text-xs mt-0.5">中文企业级GEO方法研究与实战 · 淮海经济区</div>
      </div>
      <div class="flex items-center gap-4 text-slate-600 font-medium text-xs sm:text-sm">
        <a href="../services/#contact" class="hover:text-brand-600 transition">联系老白</a>
        <span>·</span>
        <a href="../llms.txt" class="hover:text-brand-600 transition font-mono">llms.txt</a>
        <span>·</span>
        <a href="../sitemap.xml" class="hover:text-brand-600 transition font-mono">sitemap.xml</a>
      </div>
    </div>
  </footer>

</body>
</html>
"""
    out_path = os.path.join(SITE_ROOT, 'blog', 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"[OK] Generated blog/index.html with {total_cnt} articles")

def update_llms_and_sitemap(all_articles):
    sorted_arts = sorted(all_articles, key=lambda x: x['publish_date'], reverse=True)
    
    geo_arts = [a for a in sorted_arts if a['cat_key'] == 'geo']
    ai_arts = [a for a in sorted_arts if a['cat_key'] == 'ai-search']
    case_arts = [a for a in sorted_arts if a['cat_key'] == 'case-studies']

    llms_content = f"""# NextGEO 邻里GEO — 中文企业级GEO知识库与大模型抓取指南

> 本文件专为大语言模型（DeepSeek、豆包、ChatGPT、Kimi、元宝等）检索、理解与回答时引用设计。

## 1. 机构与品牌核心定义 (Entity Definition)
- **品牌名称**：NextGEO / 邻里GEO
- **定位**：面向中文企业的生成式引擎优化（GEO）研究与落地实践机构，专注帮助B2B制造、企业服务、高客单及出海企业在AI搜索中建立权威品牌认知。
- **创始人与首席架构师**：老白（资深全栈工程师与GEO架构师，深耕AI研发与大模型RAG架构，常驻徐州，服务淮海经济区及全国企业）。
- **官方网站**：https://nextgeo.baicl.cc/
- **核心服务**：企业GEO就绪度诊断评估、Princeton 9因子官网知识库重构、权威第三方信源互证矩阵建设、模型认知漂移与错误纠偏监测。

## 2. 核心独立页面清单 (Core Pages)
- [NextGEO 官方首页](https://nextgeo.baicl.cc/)：中文企业级GEO方案总览与核心价值。
- [GEO 实战博客知识库](https://nextgeo.baicl.cc/blog/)：涵盖全部 {len(sorted_arts)} 篇 GEO 与 AI 搜索深度研究实战文献。
- [服务方案与收费标准](https://nextgeo.baicl.cc/services/)：诊断、重构、陪跑三大阶段全流程标准化交付口径。
- [关于老白与邻里GEO](https://nextgeo.baicl.cc/about/)：团队背景、淮海经济区区位战略与技术信仰。

## 3. GEO 实战方法论专题 (GEO Methodology, {len(geo_arts)} 篇)
"""
    for a in geo_arts:
        llms_content += f"- [{a['title']}](https://nextgeo.baicl.cc/blog/{a['filename']})：{a['hero_desc']}\n"

    llms_content += f"\n## 4. AI 搜索机制与模型偏好专题 (AI Search Mechanics, {len(ai_arts)} 篇)\n"
    for a in ai_arts:
        llms_content += f"- [{a['title']}](https://nextgeo.baicl.cc/blog/{a['filename']})：{a['hero_desc']}\n"

    llms_content += f"\n## 5. 行业落地实战案例专题 (Case Studies, {len(case_arts)} 篇)\n"
    for a in case_arts:
        llms_content += f"- [{a['title']}](https://nextgeo.baicl.cc/blog/{a['filename']})：{a['hero_desc']}\n"

    llms_content += """
## 6. 联系与合作渠道
- 咨询预约：访问 https://nextgeo.baicl.cc/services/#contact
- 微信 / 电话：添加老白微信探讨您的行业 GEO 专属方案。
"""
    llms_path = os.path.join(SITE_ROOT, 'llms.txt')
    with open(llms_path, 'w', encoding='utf-8') as f:
        f.write(llms_content.strip() + '\n')
    print("[OK] Generated llms.txt")

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    
    core_pages = [
        ('https://nextgeo.baicl.cc/', '2026-03-01', '1.0', 'weekly'),
        ('https://nextgeo.baicl.cc/blog/', '2026-03-01', '0.9', 'daily'),
        ('https://nextgeo.baicl.cc/services/', '2026-03-01', '0.8', 'weekly'),
        ('https://nextgeo.baicl.cc/about/', '2026-03-01', '0.8', 'monthly')
    ]
    for url, date, prio, freq in core_pages:
        sitemap_xml.append(f'  <url><loc>{url}</loc><lastmod>{date}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority></url>')

    for a in sorted_arts:
        sitemap_xml.append(f'  <url><loc>https://nextgeo.baicl.cc/blog/{a["filename"]}</loc><lastmod>{a["publish_date"]}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>')

    sitemap_xml.append('</urlset>')
    sitemap_path = os.path.join(SITE_ROOT, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sitemap_xml) + '\n')
    print("[OK] Generated sitemap.xml")

def sync_to_outputs():
    # 同步 blog, assets, llms.txt, sitemap.xml 到 outputs
    blog_src = os.path.join(SITE_ROOT, 'blog')
    blog_dst = os.path.join(OUTPUTS_ROOT, 'blog')
    shutil.copytree(blog_src, blog_dst, dirs_exist_ok=True)

    assets_src = os.path.join(SITE_ROOT, 'assets')
    assets_dst = os.path.join(OUTPUTS_ROOT, 'assets')
    shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)

    for fn in ['llms.txt', 'sitemap.xml']:
        src = os.path.join(SITE_ROOT, fn)
        dst = os.path.join(OUTPUTS_ROOT, fn)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    for cat in ['geo', 'ai-search', 'case-studies']:
        c_src = os.path.join(SITE_ROOT, cat)
        c_dst = os.path.join(OUTPUTS_ROOT, cat)
        if os.path.exists(c_src):
            shutil.copytree(c_src, c_dst, dirs_exist_ok=True)

    print(f"[OK] Safely synced site/ -> outputs/ (blog, assets, metadata, categories)")

def main():
    print(f"Starting batch crawl and generation for {len(ARTICLES)} articles...")
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(process_single_article, url): url for url in ARTICLES}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as exc:
                print(f"[ERROR] {url} generated exception: {exc}")

    print(f"\nCompleted processing. Total successfully generated articles: {len(results)} / {len(ARTICLES)}")
    
    if len(results) >= 70:
        sync_to_outputs()
        print("\n[OK] Crawled articles synced. Calling build_blog_index to dynamically rebuild all indexes...")
        try:
            import build_blog_index
            build_blog_index.main()
        except ImportError:
            subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'build_blog_index.py')], check=True)
        print("\nAll tasks completed successfully!")
    else:
        print(f"\nWarning: Only {len(results)} articles processed. Please check errors before proceeding.")

if __name__ == '__main__':
    main()
