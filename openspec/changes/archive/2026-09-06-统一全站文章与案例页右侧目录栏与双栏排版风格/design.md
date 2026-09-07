# Design: 统一全站文章与案例页右侧目录栏与双栏排版风格

## Architecture & Layout Standards (架构与排版规范)

### 1. 容器与双栏栅格
- 容器宽度统一：`width: min(1180px, calc(100% - 40px)); margin: 0 auto;`
- 双栏网格：
  ```html
  <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start">
    <article class="min-w-0">
      <!-- 正文内容 (约 860px 宽度) -->
    </article>
    <aside class="hidden lg:block sticky top-24">
      <!-- 280px 吸顶目录卡片 -->
    </aside>
  </div>
  ```

### 2. 吸顶目录栏组件规范 (.toc-card)
- 吸顶定位：`sticky top-24` (96px)，完美对齐顶部 80px 导航条下方留白；
- 卡片容器：
  - 背景：`bg-white`
  - 边框：`border border-slate-200/90`
  - 圆角：`rounded-2xl`
  - 内边距：`p-5`
  - 阴影：`shadow-xs`
- 头部标题：
  - 文字：`页面结构` (15px 粗体 slate-900)
  - 分割线：`pb-3 border-b border-slate-100`
- 目录项导航：
  - 容器：`space-y-0.5 text-xs sm:text-[13.5px] text-slate-600 max-h-[calc(100vh-180px)] overflow-y-auto pr-1`
  - 单条链接：`block py-2 border-b border-slate-50 last:border-b-0 hover:text-brand-700 transition leading-snug truncate`
- 极简行动召唤 (CTA)：
  - 底部保留轻量 12px 诊断入口，保持视觉纯净，去除笨重彩色大卡片。

### 3. 数据与脚本生成流
- 由 `scripts/sync_deepgeo_blog.py` 统一定义 `render_article_html(data)` 渲染函数；
- 正文中所有的 `<section id="block-X">` 与 `<h2>` 标题自动提取成 `(href, text)` 元组，渲染为右侧 `.toc-card` 导航链。

