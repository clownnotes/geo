# Proposal: 文章体系标准化与全站博客自动同步索引规范

## Why (为什么做)
用户反馈了两个核心开发协同痛点：
1. **文章丢失与割裂**：首页精选展示了新撰写的《大模型是信息压缩机，不是垃圾桶》（2026-09-06），但在博客频道首页（`/blog/`）该文章完全缺失，分类停留在 75 篇。根本原因是博客索引由爬虫脚本基于固定爬虫列表覆盖写死，未动态扫描本地新增文章，导致本地独立创作被冲刷。
2. **样式不一与无法复用**：全站 84 篇文章中，早期手动编写的文章使用了老旧的 `.prose-geo` 类和内联样式，与批量生成的文章在排版层级、行高、标题边距存在差异。缺乏统一规范使得其他 IDE（Windsurf、Claude Code、Cursor、Antigravity）协作时无法复用模板。

## What Changes (改动了什么)
1. **建立全量动态博客索引器 (`scripts/build_blog_index.py`)**：动态遍历 `blog/*.html` 中的全部 84+ 篇文章，解析元数据，严格按 `publish_date` 倒序重构 `blog/index.html`，更新分类统计，并同步更新 `llms.txt` 与 `sitemap.xml`。
2. **制定文章排版与组件工程规范**：创建 `docs/specs/article-template-standard.md`，并在 `AGENTS.md` 中追加协同约束。
3. **逐篇巡检与样式归一化**：开发 `scripts/check_article_styles.py` 逐一巡检全站 84 篇博文，彻底清除 `.prose-geo`，保证 100% 结构一致。
4. **多 IDE 协同脚手架工具 (`scripts/create_article.py`)**：提供一键标准化新建文章工具，自动注册至索引流。

## Capabilities (新增或修改的对外能力)
- 任何 IDE 新增文章后，执行自动化脚本即可一键完成：页面生成 -> 样式合规校验 -> 博客列表自动索引 -> 首页/llms/sitemap 自动更新。
- 全站文章在任何屏幕尺寸与任何页面下呈现结构与组件级高度一致的视觉与交互体验。

## Impact (受影响的部分)
- `AGENTS.md`
- `docs/specs/article-template-standard.md`
- `scripts/build_blog_index.py` (新增)
- `scripts/check_article_styles.py` (新增)
- `scripts/create_article.py` (新增)
- `scripts/sync_deepgeo_blog.py`
- `projects/nextgeo/outputs/blog/index.html`
- `projects/nextgeo/outputs/site/blog/index.html`
- `projects/nextgeo/outputs/llms.txt`, `sitemap.xml`
- `projects/nextgeo/outputs/blog/*.html` (84 篇样式归一)
