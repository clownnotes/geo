#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_blog_index.py
动态全量扫描 projects/nextgeo/outputs/blog/*.html 中的所有博文，
提取标题、发布日期、分类、导读与封面图，严格按照 datePublished 倒序排列，
重新生成 blog/index.html、llms.txt、sitemap.xml，并完成 outputs 与 site 双向同步。
"""

import os
import re
import glob
import json
import shutil

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUTS_DIR = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs')
SITE_DIR = os.path.join(OUTPUTS_DIR, 'site')
BLOG_DIR = os.path.join(OUTPUTS_DIR, 'blog')

CATEGORY_INFO = {
    'geo': {'name': 'GEO 实战', 'badge': 'GEO实战'},
    'ai-search': {'name': 'AI 搜索认知', 'badge': 'AI搜索认知'},
    'case-studies': {'name': '行业落地案例', 'badge': '行业案例'}
}

def clean_text(html_str):
    if not html_str:
        return ''
    t = re.sub(r'<[^>]+>', '', html_str)
    return t.strip().replace('DeepGEO', '邻里GEO').replace('余果', '老白')

def parse_article_metadata(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(fpath)
    slug = filename.replace('.html', '')

    # 1. 标题
    h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    if h1_m:
        title = clean_text(h1_m.group(1))
    else:
        title_m = re.search(r'<title>(.*?)</title>', content)
        raw_t = title_m.group(1) if title_m else slug
        title = clean_text(raw_t.split('｜')[0].split('|')[0])

    # 2. 发布日期
    date = '2026-01-01'
    date_m = re.search(r'datePublished[\"\']:\s*[\"\'](\d{4}-\d{2}-\d{2})', content)
    if date_m:
        date = date_m.group(1)
    else:
        date_m2 = re.search(r'<time[^>]*datetime=[\"\'](\d{4}-\d{2}-\d{2})[\"\']', content)
        if date_m2:
            date = date_m2.group(1)
        else:
            date_m3 = re.search(r'(\d{4}-\d{2}-\d{2})', content)
            if date_m3:
                date = date_m3.group(1)

    # 3. 描述 / 导读 (Executive Summary)
    desc = ''
    summary_m = re.search(r'结论先行\s*\(Executive Summary\)：</strong>\s*<p[^>]*>(.*?)</p>', content, re.DOTALL)
    if summary_m:
        desc = clean_text(summary_m.group(1))
    else:
        desc_m = re.search(r'<meta\s+name=[\"\']description[\"\']\s+content=[\"\'](.*?)[\"\']', content)
        if desc_m:
            desc = clean_text(desc_m.group(1))
        else:
            p_m = re.search(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
            desc = clean_text(p_m.group(1)) if p_m else title

    # 4. 阅读时长
    read_m = re.search(r'阅读(?:时长|约)?[:\s]*([0-9]+)\s*(?:分钟)?', content)
    if read_m:
        calc_min = read_m.group(1).strip()
        read_time = f"{calc_min} 分钟"
    else:
        word_count = len(re.sub(r'<[^>]+>|\s+', '', content))
        calc_min = max(3, word_count // 450)
        read_time = f"{calc_min} 分钟"

    # 5. 分类判断
    cat_key = 'geo'
    badge_m = re.search(r'<span class=[\"\']text-brand-700[\"\']>(.*?)</span>', content)
    if badge_m and badge_m.group(1).strip():
        badge_text = badge_m.group(1).strip()
        if '案例' in badge_text:
            cat_key = 'case-studies'
        elif '搜索' in badge_text or 'AI' in badge_text:
            cat_key = 'ai-search'
        else:
            cat_key = 'geo'
    else:
        if 'case-studies' in content or '行业案例' in content:
            cat_key = 'case-studies'
        elif 'ai-search' in content or 'AI搜索' in content:
            cat_key = 'ai-search'
        else:
            cat_key = 'geo'

    cat_badge = CATEGORY_INFO[cat_key]['badge']

    # 6. 封面图
    cover_rel = None
    possible_covers = [
        f"../assets/article-covers/{slug}.png",
        f"../assets/article-covers/{slug}.jpg",
        f"../assets/article-covers/{slug}.webp",
    ]
    # 仅普林斯顿专文才匹配其专属插图目录
    if slug == 'princeton-nine-factors-and-real-geo-for-buyers':
        possible_covers.append("../assets/article-images/princeton-nine-factors/cover.jpg")

    for cov in possible_covers:
        disk_path = os.path.join(OUTPUTS_DIR, cov.replace('../', ''))
        if os.path.exists(disk_path):
            cover_rel = cov
            break

    if not cover_rel:
        # 检查正文中是否有本地首图（排除 logo 图）
        imgs = re.findall(r'<img[^>]+src=[\"\'](\.\./assets/[^\"\']+)[\"\']', content)
        for img in imgs:
            if 'logo' not in img and 'covers' not in img and os.path.exists(os.path.join(OUTPUTS_DIR, img.replace('../', ''))):
                cover_rel = img
                break

    return {
        'filename': filename,
        'slug': slug,
        'title': title,
        'publish_date': date,
        'hero_desc': desc,
        'read_time': read_time,
        'cat_key': cat_key,
        'cat_badge': cat_badge,
        'cover_rel': cover_rel
    }

def generate_blog_index_html(sorted_articles):
    total_cnt = len(sorted_articles)
    geo_cnt = sum(1 for a in sorted_articles if a['cat_key'] == 'geo')
    ai_cnt = sum(1 for a in sorted_articles if a['cat_key'] == 'ai-search')
    case_cnt = sum(1 for a in sorted_articles if a['cat_key'] == 'case-studies')

    # 构建 Schema.org JSON-LD 高权威知识库实体图谱 (CollectionPage + Blog + ItemList)
    item_list_elements = []
    for idx, art in enumerate(sorted_articles[:15]):
        item_list_elements.append({
            "@type": "ListItem",
            "position": idx + 1,
            "url": f"https://nextgeo.baicl.cc/blog/{art['filename']}",
            "name": art['title']
        })

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": "https://nextgeo.baicl.cc/blog/#collection",
                "url": "https://nextgeo.baicl.cc/blog/",
                "name": "GEO实战知识库与博客｜NextGEO 邻里GEO",
                "description": "NextGEO 邻里GEO 官方知识库：系统解构生成式引擎优化（GEO）、AI 搜索排名机制、模型引用底层逻辑与 B2B 行业落地案例，让企业知识在大模型时代被准确理解与首选推荐。",
                "isPartOf": {
                    "@type": "WebSite",
                    "@id": "https://nextgeo.baicl.cc/#website",
                    "name": "NextGEO 邻里GEO",
                    "url": "https://nextgeo.baicl.cc/"
                },
                "about": [
                    "生成式引擎优化",
                    "GEO",
                    "AI搜索优化",
                    "普林斯顿9因子",
                    "大模型引用机制"
                ]
            },
            {
                "@type": "Blog",
                "@id": "https://nextgeo.baicl.cc/blog/#blog",
                "name": "NextGEO 邻里GEO 实战知识库",
                "publisher": {
                    "@type": "Organization",
                    "name": "NextGEO 邻里GEO",
                    "url": "https://nextgeo.baicl.cc"
                },
                "mainEntity": {
                    "@type": "ItemList",
                    "name": "精选 GEO 实战与前沿文章",
                    "numberOfItems": total_cnt,
                    "itemListElement": item_list_elements
                }
            }
        ]
    }
    json_ld_str = json.dumps(schema_graph, ensure_ascii=False, indent=2)

    cards_html = ''
    for a in sorted_articles:
        if a['cover_rel']:
            cover_tag = f'<div class="aspect-16/10 bg-slate-100 overflow-hidden border-b border-slate-100"><img src="{a["cover_rel"]}" alt="{a["title"]}" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition duration-300"></div>'
        else:
            cover_tag = f'<div class="aspect-16/10 bg-gradient-to-br from-brand-50 to-purple-100 border-b border-slate-100 flex items-center justify-center p-6 text-center"><span class="font-extrabold text-slate-400 text-sm">{a["cat_badge"]}</span></div>'

        cards_html += f"""
        <article class="article-item group bg-white rounded-2xl border border-slate-200/80 overflow-hidden hover:shadow-lg hover:border-brand-300 transition duration-200 flex flex-col" data-category="{a['cat_key']}">
          <a href="./{a['filename']}" class="block overflow-hidden">
            {cover_tag}
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

    html = f"""<!DOCTYPE html>
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
  <link rel="sitemap" type="application/xml" title="Sitemap" href="../sitemap.xml">
  <link rel="alternate" type="text/markdown" title="LLMs.txt" href="../llms.txt">

  <!-- Schema.org JSON-LD 高权威知识库实体元数据 (供豆包/DeepSeek/百度等爬虫直接抓取归因) -->
  <script type="application/ld+json">
{json_ld_str}
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

  <!-- 主体内容 -->
  <main class="flex-grow py-12">
    <div class="geo-container">
      
      <!-- 博客 Hero 介绍 -->
      <div class="max-w-3xl mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-100 text-brand-700 text-xs font-bold uppercase tracking-wider mb-4 border border-brand-200">
          Knowledge Base & Research
        </div>
        <h1 class="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-4">
          GEO 实战知识库与深度博客
        </h1>
        <p class="text-slate-600 text-base sm:text-lg leading-relaxed">
          解构大模型搜索的召回、推理与生成逻辑。从普林斯顿 9 因子、实体建模、RAG 切片到真实行业落地打法，助企业赢得 AI 搜索时代的推荐权。
        </p>
      </div>

      <!-- 分类筛选切换卡 -->
      <div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-10 pb-4 border-b border-slate-200">
        <button onclick="filterCategory('all')" id="btn-all" class="cat-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-slate-900 text-white shadow-xs transition">
          全部 ({total_cnt})
        </button>
        <button onclick="filterCategory('geo')" id="btn-geo" class="cat-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition">
          GEO实战 ({geo_cnt})
        </button>
        <button onclick="filterCategory('ai-search')" id="btn-ai-search" class="cat-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition">
          AI搜索认知 ({ai_cnt})
        </button>
        <button onclick="filterCategory('case-studies')" id="btn-case-studies" class="cat-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition">
          行业案例 ({case_cnt})
        </button>
      </div>

      <!-- 文章卡片网格列表 (严格倒序排列) -->
      <div id="article-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
        {cards_html}
      </div>

    </div>
  </main>

  <!-- 页脚 -->
  <footer class="border-t border-slate-200/90 py-12 text-slate-500 text-xs sm:text-sm bg-white/90 mt-20">
    <div class="geo-container flex flex-col sm:flex-row items-center justify-between gap-6">
      <div>
        <strong class="text-slate-900 font-bold text-base">邻里GEO (NextGEO)</strong>
        <div class="text-slate-400 text-xs mt-1">中文企业级GEO方法研究与实战 · 淮海经济区</div>
      </div>
      <div class="flex items-center gap-6 text-slate-600 font-medium">
        <a href="../services/#contact" class="hover:text-brand-600 transition">联系老白</a>
        <span>·</span>
        <a href="../llms.txt" class="hover:text-brand-600 transition font-mono">llms.txt</a>
        <span>·</span>
        <a href="../sitemap.xml" class="hover:text-brand-600 transition font-mono">sitemap.xml</a>
      </div>
    </div>
  </footer>

  <!-- 分类筛选客户端逻辑 -->
  <script>
    function filterCategory(cat) {{
      const cards = document.querySelectorAll('.article-item');
      cards.forEach(card => {{
        if (cat === 'all' || card.getAttribute('data-category') === cat) {{
          card.style.display = 'flex';
        }} else {{
          card.style.display = 'none';
        }}
      }});

      // 切换按钮高亮
      document.querySelectorAll('.cat-btn').forEach(btn => {{
        btn.classList.remove('bg-slate-900', 'text-white');
        btn.classList.add('bg-white', 'text-slate-600');
      }});
      const activeBtn = document.getElementById('btn-' + cat);
      if (activeBtn) {{
        activeBtn.classList.remove('bg-white', 'text-slate-600');
        activeBtn.classList.add('bg-slate-900', 'text-white');
      }}
    }}

    // 支持通过 URL Query ?cat=xxx 自动筛选
    window.addEventListener('DOMContentLoaded', () => {{
      const params = new URLSearchParams(window.location.search);
      const cat = params.get('cat');
      if (cat && ['geo', 'ai-search', 'case-studies'].includes(cat)) {{
        filterCategory(cat);
      }}
    }});
  </script>

</body>
</html>
"""
    return html

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
    for p in [os.path.join(OUTPUTS_DIR, 'llms.txt'), os.path.join(SITE_DIR, 'llms.txt')]:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(llms_content.strip() + '\n')

    # sitemap.xml
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
    sitemap_str = '\n'.join(sitemap_xml) + '\n'

    for p in [os.path.join(OUTPUTS_DIR, 'sitemap.xml'), os.path.join(SITE_DIR, 'sitemap.xml')]:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(sitemap_str)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="NextGEO 博客全量动态索引构建系统")
    parser.add_argument('--dry-run', action='store_true', help="预演模式：只执行扫描与统计，不写入磁盘")
    args = parser.parse_args()

    print("Scanning all blog articles in projects/nextgeo/outputs/blog/*.html...")
    article_files = sorted(glob.glob(os.path.join(BLOG_DIR, '*.html')))
    articles = []

    for f in article_files:
        if f.endswith('index.html'):
            continue
        try:
            meta = parse_article_metadata(f)
            articles.append(meta)
        except Exception as e:
            print(f"[WARN] Error parsing {f}: {e}")

    print(f"Discovered {len(articles)} articles dynamically.")

    # 按 publish_date 严格倒序排序
    sorted_articles = sorted(articles, key=lambda x: (x['publish_date'], x['title']), reverse=True)

    geo_cnt = sum(1 for a in sorted_articles if a['cat_key'] == 'geo')
    ai_cnt = sum(1 for a in sorted_articles if a['cat_key'] == 'ai-search')
    case_cnt = sum(1 for a in sorted_articles if a['cat_key'] == 'case-studies')

    print(f"Stats: 全部={len(sorted_articles)}, GEO={geo_cnt}, AI搜索={ai_cnt}, 案例={case_cnt}")
    print(f"Top 3 Articles:")
    for i, a in enumerate(sorted_articles[:3]):
        print(f"  {i+1}. [{a['publish_date']}] {a['title']} (cover: {a['cover_rel']})")

    if args.dry_run:
        print("\n[DRY-RUN] 预演完成，未修改任何磁盘文件。")
        return

    # 生成 blog/index.html
    index_html = generate_blog_index_html(sorted_articles)

    out_index_path = os.path.join(BLOG_DIR, 'index.html')
    site_index_path = os.path.join(SITE_DIR, 'blog/index.html')

    with open(out_index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    with open(site_index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"[OK] Generated {out_index_path} and {site_index_path} with {len(sorted_articles)} articles.")
    print(f"   - Top Article: {sorted_articles[0]['publish_date']} | {sorted_articles[0]['title']}")

    # 更新 llms.txt & sitemap.xml
    update_llms_and_sitemap(sorted_articles)
    print("[OK] Updated llms.txt and sitemap.xml across outputs and site.")

    # 镜像双端同步
    for cat in ['geo', 'ai-search', 'case-studies']:
        s_dir = os.path.join(SITE_DIR, cat)
        o_dir = os.path.join(OUTPUTS_DIR, cat)
        if os.path.exists(s_dir):
            shutil.copytree(s_dir, o_dir, dirs_exist_ok=True)
            shutil.copytree(o_dir, s_dir, dirs_exist_ok=True)

    print("[SUCCESS] All blog indexing tasks completed.")

if __name__ == '__main__':
    main()
