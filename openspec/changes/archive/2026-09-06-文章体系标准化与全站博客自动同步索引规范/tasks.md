## 1. 规范文档与协同约束建设
- [x] 1.1 编写 `docs/specs/article-template-standard.md` 文章页面标准排版与组件规范。
- [x] 1.2 在 `AGENTS.md` 中追加第 6 节《文章排版与博客索引工程规范》。

## 2. 自动化索引构建系统
- [x] 2.1 编写 `scripts/build_blog_index.py`，动态扫描 `outputs/blog/*.html` 全部文章并按发表时间倒序排列。
- [x] 2.2 自动生成 `outputs/blog/index.html`（修正分类计数与最新文章呈现）。
- [x] 2.3 自动更新 `outputs/llms.txt` 与 `outputs/sitemap.xml`。
- [x] 2.4 改造 `scripts/sync_deepgeo_blog.py`，爬虫结束时直接调用动态构建器，杜绝冲刷本地文章。
- [x] 2.5 修复 `build_blog_index.py` 封面全局兜底串图缺陷，补齐 `--dry-run` 预演支持。

## 3. 逐篇样式巡检与归一化
- [x] 3.1 编写 `scripts/check_article_styles.py` 样式巡检与修复工具。
- [x] 3.2 运行巡检工具，逐篇核对全站 84 篇博文，彻底清除 `.prose-geo` 并规范化样式。
- [x] 3.3 编写 `scripts/create_article.py` 多 IDE 标准新建文章脚手架。
- [x] 3.4 修复全量博文表格悬空 `</div>` 导致双栏栅格提前闭合与目录栏下坠问题，确保 84 篇博文 `open_divs == close_divs` 100% 平衡。

## 4. 验证与归档
- [x] 4.1 本地 8088 端口核验 `http://localhost:8088/sites/nextgeo/blog/`，确认第一篇为 2026-09-06 最新文章，分类数字精准匹配。
- [x] 4.2 0 Emoji 违规核查与双端镜像（outputs 与 outputs/site）一致性核查。
- [x] 4.3 待用户确认后执行 OpenSpec 归档并推送到 git origin/github main。
