# Design: 独立页面导航对标与GEO博客知识库建设

## Architecture (架构设计与对象关系)

### 1. 站点拓扑结构与路由层级
对标 `https://deep-geo.cn/` 构建清晰的静态层级：
```text
projects/nextgeo/outputs/site/
├── index.html                           # 战略总览门户（Hero + Core Value + Workflow + Canonical Articles）
├── blog/
│   ├── index.html                       # 博客与知识库索引页（对标 /blog/，分类筛选与精选网格）
│   ├── geo-vs-seo-differences.html      # 核心方法篇 1: SEO、GEO、AIO、LLMO 区别
│   ├── geo-execution-roadmap.html       # 核心方法篇 2: 企业级 GEO 0 到 1 实战路线图
│   ├── content-ai-citations.html        # 核心方法篇 3: 普林斯顿内容同时适合人类与 AI 引用
│   ├── entity-brand-modeling.html       # 核心方法篇 4: 实体建模与大模型精准理解品牌
│   ├── schema-clean-markdown.html       # 核心方法篇 5: Schema 与 Clean Markdown AI 易读网页
│   └── b2b-decision-geo-strategy.html   # 核心方法篇 6: 解释型决策客群首轮拦截法则
├── services/
│   └── index.html                       # 全案服务页（交付物、流程、底端 #contact 咨询）
├── about/
│   └── index.html                       # 关于我们（团队履历、Bento 决策客群、实战案例、8大 FAQ）
├── llms.txt                             # 大模型极简知识库索引
└── sitemap.xml                          # 搜索引擎与爬虫统一站点地图
```

### 2. 导航组件规范 (100% 独立页面跳转契约)
- **严禁**在导航栏（`<header>`）注入任何以 `#` 开头的单页滚动锚点；
- 全站所有页面导航统一为四个标准连接：
  - 首页：`../` 或 `./`
  - 博客：`../blog/` 或 `blog/`
  - 服务：`../services/` 或 `services/`
  - 关于：`../about/` 或 `about/`
- 当前活动页项高亮展示，其余项保持深灰 hover 渐变，无任何右侧外挂突兀按钮。

---

## Content & Layout Architecture (内容与排版规范)

### 1. 首页去重与精简化
- **消除与关于页的重叠**：
  - 首页移除团队成员列表、移除 8 大 FAQ 折叠卡（此类深度履约与信任材料完全交给 `/about/`）；
  - 首页聚焦于：
    - 首屏决策者痛点提问与大模型拦截卡片；
    - 3 大核心价值卡片；
    - 4 步战略闭环（01 锚定、02 监测、03 洞察、04 塑造）；
    - 优先建设的 6 篇 GEO 答案源精选卡片（点击直达对应博客）；
    - 素雅页脚。

### 2. 博客与实战知识库规范（Princeton 9 因子 + Schema.org Article）
- 单篇文章采用标准 Princeton 9 因子：
  - 标题即用户核心提问词（Answer-First）；
  - 首段给出精准定义与定性结论；
  - 注入量化对照表（Markdown Table）；
  - 注入 Schema.org `Article` / `TechArticle` JSON-LD 实体元数据；
  - 严禁 Emoji 表情，使用微边框与数据对比卡片构建严肃商业质感。

