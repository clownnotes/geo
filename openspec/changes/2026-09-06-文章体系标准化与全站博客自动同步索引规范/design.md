# Design: 文章体系标准化与全站博客自动同步索引规范

## Architecture & Data Flow (架构与数据流)

```
[Markdown / HTML 创作] 
       │
       ▼ (遵循 docs/specs/article-template-standard.md)
[projects/nextgeo/outputs/blog/*.html]
       │
       ▼ (执行 scripts/build_blog_index.py)
┌───────────────────────────────────────────────────────────┐
│ 1. 动态全量扫描 outputs/blog/*.html (84+ 篇)               │
│ 2. 正则提取 Schema/Meta: Title, Date, Desc, Category, Cover│
│ 3. 按 Date 倒序排序 (最新篇居首位)                          │
│ 4. 统计分类计数 (全部/GEO实战/AI搜索认知/行业案例)            │
│ 5. 生成 outputs/blog/index.html & outputs/site/blog/index │
│ 6. 生成 outputs/llms.txt & sitemap.xml                    │
│ 7. 执行 outputs -> outputs/site 双端同步                  │
└───────────────────────────────────────────────────────────┘
```

## Component Standards (文章统一 DOM 与 CSS 组件模型)

1. **容器**：`width: min(1180px, calc(100% - 40px)); margin: 0 auto;`
2. **栅格**：`grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start`
3. **正文**：`<article class="min-w-0">` 下使用标准 `.content-block`（废除 `.prose-geo`）：
   - `h2`: 1.5rem, font-black, text-slate-900, mt-10 mb-4, pt-4, border-t border-slate-100
   - `h3`: 1.15rem, font-bold, text-slate-800, mt-6 mb-3
   - `p`: 1.0625rem, text-slate-700, leading-relaxed mb-5
   - `table`: 统一使用 `<table class="content-table">`（包含在 overflow-x-auto 容器中）
   - `#faq`: `<section id="faq" class="content-block mt-12 p-6 sm:p-8 rounded-2xl bg-slate-50 border border-slate-200/90 shadow-2xs">`
4. **侧边栏**：`<aside class="hidden lg:block sticky top-24 w-[280px]">`
   - `.toc-card` 纯白圆角边框卡片，带“页面结构”标题与 13.5px 文字导航链，悬停品牌紫。
5. **滚动规范**：`html { scroll-behavior: smooth; }`，`.content-block, [id^="block-"], #faq { scroll-margin-top: 100px; }`。
6. **DOM 闭合平衡铁律**：表格必须标准包裹为 `<div class="overflow-x-auto my-6"><table class="content-table">...</table></div>`，严禁悬空 `</div>` 导致双栏栅格提前闭合与 `<aside>` 目录栏坠底。
7. **封面提取防串图**：仅根据当前文章 slug 匹配 `article-covers/{slug}.*` 或正文首图，无专属封面时展示分类渐变徽章，严禁全局硬编码特定文章封面。

## Tools & CLI (配套自动化工具设计)

- `scripts/build_blog_index.py`：独立执行，支持 `--dry-run` 预演模式与全量索引重建，内含精准 slug 封面绑定。
- `scripts/check_article_styles.py`：全站样式巡检脚本，带 `--fix` 自动修复模式，内置 `open_divs == close_divs` 标签平衡检测与封面一致性断言。
- `scripts/create_article.py`：一键新建标准文章脚手架并自动注册入库。
- `scripts/sync_deepgeo_blog.py`：爬虫抓取后自动调用动态索引器，表格处理使用正则避免标签失衡。

