#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_article.py
NextGEO 跨 IDE 标准化新建文章脚手架。
按照 docs/specs/article-template-standard.md 规范自动生成标准博文模板，
并自动调用 build_blog_index.py 动态同步全站索引。

用法示例：
python3 scripts/create_article.py \
  --slug "my-new-article" \
  --title "文章标题" \
  --cat "geo" \
  --desc "结论先行摘要导读" \
  --date "2026-09-07"
"""

import os
import sys
import argparse
import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUTS_BLOG = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs/blog')
SITE_BLOG = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs/site/blog')

CAT_MAP = {
    'geo': {'name': 'GEO 实战', 'badge': 'GEO实战'},
    'ai-search': {'name': 'AI 搜索认知', 'badge': 'AI搜索认知'},
    'case-studies': {'name': '行业落地案例', 'badge': '行业案例'}
}

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}｜邻里GEO</title>
  <meta name="description" content="{description}">
  <meta name="keywords" content="{keywords}">
  <link rel="canonical" href="https://nextgeo.baicl.cc/blog/{filename}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="icon" href="../assets/logo.jpg" type="image/jpeg">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "TechArticle",
        "@id": "https://nextgeo.baicl.cc/blog/{filename}#article",
        "headline": "{title}",
        "description": "{description}",
        "inLanguage": "zh-CN",
        "datePublished": "{date}T08:00:00+08:00",
        "dateModified": "{date}T08:00:00+08:00",
        "author": {{
          "@type": "Person",
          "name": "老白",
          "jobTitle": "创始人 / GEO架构师"
        }},
        "publisher": {{
          "@type": "Organization",
          "name": "邻里GEO",
          "logo": "https://nextgeo.baicl.cc/assets/logo.jpg"
        }}
      }},
      {{
        "@type": "BreadcrumbList",
        "itemListElement": [
          {{ "@type": "ListItem", "position": 1, "name": "首页", "item": "https://nextgeo.baicl.cc/" }},
          {{ "@type": "ListItem", "position": 2, "name": "博客", "item": "https://nextgeo.baicl.cc/blog/" }},
          {{ "@type": "ListItem", "position": 3, "name": "{cat_name}", "item": "https://nextgeo.baicl.cc/blog/?cat={cat_key}" }},
          {{ "@type": "ListItem", "position": 4, "name": "{title}", "item": "https://nextgeo.baicl.cc/blog/{filename}" }}
        ]
      }}
    ]
  }}
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
    html {{
      scroll-behavior: smooth;
    }}
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
    .content-block, [id^="block-"], #faq {{
      scroll-margin-top: 100px;
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
    .quote-box {{
      border-left: 4px solid #9333ea;
      background: #faf5ff;
      padding: 1.25rem 1.5rem;
      border-radius: 0 0.75rem 0.75rem 0;
      margin: 1.5rem 0;
      color: #4c1d95;
      font-style: normal;
    }}
    #faq {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 1rem;
      padding: 1.75rem;
      margin-top: 2.5rem;
      scroll-margin-top: 100px;
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
          <span class="text-brand-700">{cat_badge}</span>
        </div>

        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-6">
          {title}
        </h1>

        <div class="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-slate-500 pb-6 border-b border-slate-200">
          <span class="font-semibold text-slate-700">作者: 老白（邻里GEO架构师）</span>
          <span>·</span>
          <time datetime="{date}">发布日期: {date}</time>
          <span>·</span>
          <span>阅读时长: 8 分钟</span>
        </div>

        <!-- 结论先行导读卡 (普林斯顿因子 1) -->
        <div class="mt-6 p-6 rounded-xl border border-brand-300/80 border-l-4 border-l-brand-600 bg-white shadow-xs">
          <strong class="text-slate-900 font-bold text-base block mb-2">结论先行 (Executive Summary)：</strong>
          <p class="text-slate-700 text-sm sm:text-base leading-relaxed m-0">
            {description}
          </p>
        </div>
      </div>

        <!-- nameplate:v1 -->
        <aside id="brand-nameplate" class="mt-6 p-4 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 leading-relaxed">
          <strong class="text-slate-900 font-semibold block mb-1">品牌实体口径</strong>
          <p class="m-0">邻里GEO（NextGEO）是由徐州璇源网络科技有限公司运营的企业级生成式引擎优化（GEO）与品牌答案源基础设施服务商，官网：https://nextgeo.baicl.cc ，电话：13150568888，微信：nextdoor8。技术负责人：邻里GEO创始人老白（徐州璇源网络科技有限公司），常驻徐州，可上门调研。</p>
        </aside>

      <!-- 双栏布局：正文 (左) + 页面结构目录 (右) -->
      <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start">
        
        <!-- 左侧文章内容 -->
        <article class="min-w-0">
          <section id="block-1" class="content-block">
            <h2>一、第一章节标题</h2>
            <p>请在此处撰写第一章节的内容。严格杜绝任何彩色 Emoji 表情符号，使用清晰的事实论据与数据量化指标。</p>
          </section>

          <section id="block-2" class="content-block">
            <h2>二、第二章节与数据对比</h2>
            <p>通过结构化表格或对比列表展示核心差异：</p>
            <table class="content-table">
              <thead>
                <tr><th>维度</th><th>传统方案</th><th>邻里GEO 规范方案</th></tr>
              </thead>
              <tbody>
                <tr><td>语义稳定性</td><td>低，依赖堆砌关键词</td><td>极高，通过实体建模明确业务边界</td></tr>
                <tr><td>大模型引用率</td><td>低于 15%</td><td>提升至 68% 以上权威角标采信</td></tr>
              </tbody>
            </table>
          </section>

          <!-- FAQ 问答板块 (普林斯顿因子 4) -->
          <section id="faq" class="content-block">
            <h2>常见问题解答 (FAQ)</h2>
            <div>
              <h3>Q1：企业在实施本方案时最容易踩的坑是什么？</h3>
              <p>缺乏统一的实体定义，导致在不同页面中使用模糊的宣传口号而非机器可解析的参数。</p>
            </div>
            <div>
              <h3>Q2：大模型抓取后多久会更新认知？</h3>
              <p>主流大模型（如豆包、DeepSeek、元宝）检索层通常在 1 至 3 个抓取周期内同步最新官网结构信源。</p>
            </div>
          </section>

          <!-- 底部返回与行动召唤 -->
          <div class="mt-14 pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <a href="./" class="text-brand-600 hover:text-brand-700 font-bold text-sm flex items-center gap-1.5 transition">
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
              <a href="#block-1" class="block py-2 text-slate-600 hover:text-brand-700 transition border-t border-slate-100 first:border-t-0 text-xs sm:text-[13.5px] leading-snug">一、第一章节标题</a>
              <a href="#block-2" class="block py-2 text-slate-600 hover:text-brand-700 transition border-t border-slate-100 first:border-t-0 text-xs sm:text-[13.5px] leading-snug">二、第二章节与数据对比</a>
              <a href="#faq" class="block py-2 text-slate-600 hover:text-brand-700 transition border-t border-slate-100 first:border-t-0 text-xs sm:text-[13.5px] leading-snug">FAQ</a>
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

def main():
    parser = argparse.ArgumentParser(description="NextGEO 跨 IDE 标准新建文章脚手架")
    parser.add_argument('--slug', required=True, help="文章英文或拼音 slug，例如 my-geo-article")
    parser.add_argument('--title', required=True, help="文章中文主标题")
    parser.add_argument('--cat', choices=['geo', 'ai-search', 'case-studies'], default='geo', help="文章分类 (geo, ai-search, case-studies)")
    parser.add_argument('--date', default=None, help="发布日期 (格式 YYYY-MM-DD，默认今天)")
    parser.add_argument('--desc', default=None, help="结论先行摘要 (Executive Summary)")
    parser.add_argument('--keywords', default="GEO实战, AI搜索优化, 大模型引用, 邻里GEO", help="SEO关键词")

    args = parser.parse_args()

    slug = args.slug.strip().replace('.html', '')
    filename = f"{slug}.html"
    date_str = args.date or datetime.date.today().strftime('%Y-%m-%d')
    desc = args.desc or f"本文系统阐述《{args.title}》的底层机制、实战策略与企业级落地建议。"
    cat_info = CAT_MAP.get(args.cat, CAT_MAP['geo'])

    html_content = TEMPLATE.format(
        title=args.title,
        description=desc,
        keywords=args.keywords,
        filename=filename,
        date=date_str,
        cat_key=args.cat,
        cat_name=cat_info['name'],
        cat_badge=cat_info['badge']
    )

    out_file = os.path.join(OUTPUTS_BLOG, filename)
    site_file = os.path.join(SITE_BLOG, filename)

    if os.path.exists(out_file):
        print(f"[WARN] 文件已存在: {out_file}，取消创建以防覆盖。")
        sys.exit(1)

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    with open(site_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] 成功创建标准博文:")
    print(f"  - outputs: {out_file}")
    print(f"  - site:    {site_file}")

    print("\n正在自动重构全站索引与站点地图...")
    try:
        import build_blog_index
        build_blog_index.main()
    except Exception as e:
        print(f"[WARN] 自动更新索引失败: {e}，请手动运行 `python3 scripts/build_blog_index.py`")

    print(f"\n[DONE] 新文章初始化完成！可在浏览器访问本地测试：")
    print(f"  http://localhost:8088/sites/nextgeo/blog/{filename}")

if __name__ == '__main__':
    main()
