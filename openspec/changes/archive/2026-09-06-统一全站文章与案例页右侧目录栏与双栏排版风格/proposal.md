# Proposal: 统一全站文章与案例页右侧目录栏与双栏排版风格

## Why (为什么做)
用户反馈在浏览文章与案例页面时，排版和目录栏存在明显不一致性：
1. 部分文章目录栏位于右侧，但采用 Tailwind col-span-4，宽度高达 ~380px，过于宽泛且挤压左侧正文阅读空间；
2. 早期手动编写的 6 篇博客文章没有右侧目录栏，内容单栏居中，大纲位于正中；
3. 部分断点下目录栏流式排布到文章最底端，造成“有的在中间、有的在右边、有的在最下面”的割裂体验。
对标竞品 deep-geo.cn (如 /case-studies/professional-services-geo-clinics.html) 具备高度统一的排版：左侧正文自由舒展，右侧固定 280px 吸顶卡片，包含规范平滑跳转的“页面结构”目录。

## What Changes (改动了什么)
1. **重构文章双栏栅格**：建立统一的网格标准，采用 `lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10`，将右侧目录栏固定为 280px 黄金阅读宽度。
2. **统一吸顶目录栏组件 (.toc-card)**：
   - 标题规范为“页面结构”；
   - 目录项 13.5px，色值 `#475569`，细线分割，悬停品牌紫；
   - 吸顶位置锁定为 top-24 (96px)，支持长列表自适应纵向滚动；
   - 去除原先侧边栏过于繁杂臃肿的底色和宣传大卡片，保持极致素雅克制。
3. **自动化脚本模板升级**：改造 `scripts/sync_deepgeo_blog.py`，并全量重新同步渲染 77 篇行业案例与分类文章。
4. **统一 7 篇独立博客页面**：为全部独立博客补充段落锚点与右侧固定目录栏，消除居中单栏页面。
5. **镜像双端同步**：严格保持 outputs/ 与 outputs/site/ 字节对齐，严格遵循 0 Emoji 与本地测试准则。

## Capabilities (新增或修改的对外能力)
- 全站所有文章（涵盖行业案例、AI搜索洞察、GEO方法论与实战博客）均具备统一像素级视觉水准。
- 用户可随时通过右侧 280px 吸顶卡片平滑跳转到任何章节。

## Impact (受影响的部分)
- `scripts/sync_deepgeo_blog.py`
- `projects/nextgeo/outputs/case-studies/*.html`
- `projects/nextgeo/outputs/ai-search/*.html`
- `projects/nextgeo/outputs/geo/*.html`
- `projects/nextgeo/outputs/blog/*.html`
- `projects/nextgeo/outputs/site/**`
