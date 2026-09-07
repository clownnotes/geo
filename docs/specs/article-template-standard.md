# NextGEO 企业级文章排版与组件工程规范

> 本文档是全站（包括博客知识库、行业案例、AI 搜索研究、GEO 方法论）所有文章页面在 HTML 结构、CSS 样式、双栏栅格、TOC 吸顶目录与多 IDE 协同开发时的**统一技术标准**。

---

## 1. 核心架构原则

1. **结构语义化与大模型友好**：
   - 文章正文严格按 `section id="block-X"` 分块，每个分块对应一个章节 `h2`；
   - 遵循普林斯顿 9 因子：结论先行（Executive Summary）、数据注入、结构化表格（`.content-table`）、专家引语（`.quote-box`）、标准 FAQ（`#faq`）；
   - 必须配置 Schema.org `TechArticle` 与 `BreadcrumbList` 结构化元数据；
   - 严禁使用任何客户端动态 JS 渲染正文（必须 SSR/SSG 服务端直出或静态纯 HTML）。
2. **0 Emoji 铁律**：
   - 严禁在标题、正文、列表、卡片、图表、目录或页脚中使用任何 Emoji 彩色表情符号（如 💡、⚡️、⚠️、🚀 等）；
   - 依靠文字对比、加粗、Tag 标签与微边框呈现严肃商业质感。
3. **黄金比例双栏栅格**：
   - 容器统一为 `width: min(1180px, calc(100% - 40px)); margin: 0 auto;`；
   - 栅格布局严格使用：`grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start`；
   - 左侧文章占用剩余全部空间（约 860px 宽度），右侧吸顶目录严格锁定为 **280px** 紧凑宽度。
4. **HTML 标签闭合与 DOM 平衡铁律**：
   - 表格必须规范包裹在 `<div class="overflow-x-auto my-6"><table class="content-table">...</table></div>` 中；
   - 严禁出现悬空未配对的 `</div>` 标签，否则会导致双栏栅格容器提前被闭合，致使右侧 `<aside>` 目录栏被挤出栅格下坠至页面底部；
   - 每次提交或生成文章后，必须执行 `scripts/check_article_styles.py` 自动化核验 `open_divs == close_divs`。

---

## 2. 标准 CSS 与组件类名规范

所有文章页面必须在 `<style>` 中引入以下基础样式表，禁止随意自定义私有样式类（严禁使用旧版的 `.prose-geo`）：

```css
html {
  scroll-behavior: smooth;
}
.site-shell {
  min-height: 100vh;
  background-color: #faf5ff;
  background-image: 
    radial-gradient(circle at 84% 4%, rgba(147, 51, 234, 0.12), transparent 28%),
    linear-gradient(90deg, rgba(147, 51, 234, 0.05) 1px, transparent 1px),
    linear-gradient(0deg, rgba(147, 51, 234, 0.05) 1px, transparent 1px);
  background-size: 100% 100%, 72px 72px, 72px 72px;
}
.geo-container {
  width: min(1180px, calc(100% - 40px));
  margin-left: auto;
  margin-right: auto;
}
.content-block {
  margin-bottom: 2.5rem;
  scroll-margin-top: 100px;
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
}
```

---

## 3. 标准 HTML 页面骨架模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{TITLE}}｜邻里GEO</title>
  <meta name="description" content="{{DESCRIPTION}}">
  <meta name="keywords" content="{{KEYWORDS}}">
  <link rel="canonical" href="https://nextgeo.baicl.cc/blog/{{FILENAME}}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="icon" href="../assets/logo.jpg" type="image/jpeg">

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "TechArticle",
        "@id": "https://nextgeo.baicl.cc/blog/{{FILENAME}}#article",
        "headline": "{{TITLE}}",
        "description": "{{DESCRIPTION}}",
        "inLanguage": "zh-CN",
        "datePublished": "{{DATE}}T08:00:00+08:00",
        "dateModified": "{{DATE}}T08:00:00+08:00",
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
          { "@type": "ListItem", "position": 3, "name": "{{CATEGORY_NAME}}", "item": "https://nextgeo.baicl.cc/blog/?cat={{CATEGORY_KEY}}" },
          { "@type": "ListItem", "position": 4, "name": "{{TITLE}}", "item": "https://nextgeo.baicl.cc/blog/{{FILENAME}}" }
        ]
      }
    ]
  }
  </script>

  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              50: "#faf5ff", 100: "#f3e8ff", 200: "#e9d5ff", 300: "#d8b4fe",
              400: "#c084fc", 500: "#a855f7", 600: "#9333ea", 700: "#7e22ce",
              800: "#6b21a8", 900: "#581c87"
            }
          },
          fontFamily: {
            sans: ['-apple-system', 'BlinkMacSystemFont', '"PingFang SC"', '"Hiragino Sans GB"', '"Microsoft YaHei"', 'sans-serif'],
          }
        }
      }
    }
  </script>
  <style>
    /* 引入上方第 2 节全部标准 CSS */
  </style>
</head>
<body class="site-shell text-slate-800 font-sans antialiased selection:bg-brand-200 selection:text-brand-900 min-h-screen flex flex-col">

  <!-- 顶部导航栏 (固定 80px 高度) -->
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
          <span class="text-brand-700">{{CATEGORY_BADGE}}</span>
        </div>

        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-6">
          {{TITLE}}
        </h1>

        <div class="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-slate-500 pb-6 border-b border-slate-200">
          <span class="font-semibold text-slate-700">作者: 老白（邻里GEO架构师）</span>
          <span>·</span>
          <time datetime="{{DATE}}">发布日期: {{DATE}}</time>
          <span>·</span>
          <span>阅读时长: {{READ_TIME}}</span>
        </div>

        <!-- 结论先行导读卡 (普林斯顿因子 1) -->
        <div class="mt-6 p-6 rounded-xl border border-brand-300/80 border-l-4 border-l-brand-600 bg-white shadow-xs">
          <strong class="text-slate-900 font-bold text-base block mb-2">结论先行 (Executive Summary)：</strong>
          <p class="text-slate-700 text-sm sm:text-base leading-relaxed m-0">
            {{DESCRIPTION}}
          </p>
        </div>
      </div>

      <!-- 双栏布局：正文 (左) + 页面结构目录 (右) -->
      <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start">
        
        <!-- 左侧文章内容 -->
        <article class="min-w-0">
          <section id="block-1" class="content-block">
            <h2>一、章节标题</h2>
            <p>段落内容...</p>
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
              <a href="#block-1" class="block py-2 text-slate-600 hover:text-brand-700 transition border-t border-slate-100 first:border-t-0 text-xs sm:text-[13.5px] leading-snug">一、章节标题</a>
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
```

---

## 4. 自动化与协同开发工作流

1. **新建文章**：
   ```bash
   python3 scripts/create_article.py --slug "my-new-article" --title "我的新文章标题" --cat "geo" --date "2026-09-07"
   ```
2. **重构索引与同步**：
   编写完文章正文后，只需运行：
   ```bash
   python3 scripts/build_blog_index.py
   ```
   脚本将：
   - 自动扫描全量文章并按 `datePublished` 绝对倒序排序；
   - 重新生成 `blog/index.html`，更新分类统计；
   - 更新 `llms.txt` 与 `sitemap.xml`；
   - 自动完成 `outputs/` 到 `outputs/site/` 的镜像同步。
3. **全站样式巡检**：
   ```bash
   python3 scripts/check_article_styles.py
   ```
   自动核验所有文章是否符合本规范。
