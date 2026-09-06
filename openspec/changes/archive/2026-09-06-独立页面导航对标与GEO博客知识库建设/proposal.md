# Proposal: 独立页面导航对标与GEO博客知识库建设

## Why (为什么做)
1. **导航混杂与跳转体验混乱**：当前页面存在“有的是点击跳锚点，有的是点击跳进页面”的混乱现象，顶部导航夹杂了 `#core-value` 等页面内锚点，破坏了严肃企业级站点的浏览体验；对标站点 `https://deep-geo.cn` 采用极其清晰的 4 大独立一级页面（首页、博客、服务、关于）。
2. **首页与“关于页”定位重复**：关于页已具备完整的团队履历、客群 Bento 矩阵与 8 大 FAQ；首页应回归战略级总览门户，去除重复的团队列表与冗余锚点，避免信息冲突。
3. **博客（知识库）是 GEO 核心答案源基础设施**：大模型（DeepSeek、豆包、Kimi）联网搜索 RAG 召回依赖具有独立 Permalink URL 的 Clean Markdown / HTML 文章单元。建设 GEO 博客实战知识库，能直接提升企业品牌在行业核心搜索词与方法论问法中的 Citation 引用率。

## What Changes (改动了什么)
1. **统一全站 4 大独立页面导航**：`首页` (`/`)、`博客` (`/blog/`)、`服务` (`/services/`)、`关于` (`/about/`)，彻底移除导航栏内锚点跳转。
2. **首页精简化对标重构**：首页定位为“战略总览 + 答案源入口”，保留 Hero、3 大核心价值、4 步闭环，以及 6 篇优先建设的 GEO 博客方法卡片，直链点击进入博客详情。
3. **上线 GEO 实战博客知识库体系**：
   - 建立 `/blog/` 列表页，对标 DeepGEO 质感；
   - 输出首批 6 篇普林斯顿标准 GEO 权威深度实战文章；
   - 更新 `/llms.txt` 与 `/sitemap.xml`，实现大模型收录对齐。

## Capabilities (新增或修改的对外能力)
- 新增 `/blog/` 独立路由与博客列表展示能力；
- 新增 6 篇具有独立 URL 与 Schema.org Article 元数据的 GEO 深度实战知识单元；
- 全站统一采用独立页面跳转模式。

## Impact (受影响的部分)
- `projects/nextgeo/outputs/site/index.html`（与 `outputs/index.html`）
- `projects/nextgeo/outputs/site/about/index.html`（与 `outputs/about/index.html`）
- `projects/nextgeo/outputs/site/services/index.html`（与 `outputs/services/index.html`）
- `projects/nextgeo/outputs/site/blog/` 新增目录与页面
- `projects/nextgeo/outputs/site/llms.txt` 与 `sitemap.xml`
