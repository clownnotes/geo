## 1. 准备工作
- [x] 1.1 确认要修改的生成脚本 `scripts/sync_deepgeo_blog.py` 与 7 篇独立博文列表。
- [x] 1.2 核对全局规则（0 Emoji、严禁私自推生产服务器、保持 outputs 与 site 双端镜像一致）。

## 2. 脚本与文章模板改造
- [x] 2.1 重构 `scripts/sync_deepgeo_blog.py` 的 HTML 渲染模板（`lg:grid-cols-[minmax(0,1fr)_280px]`，280px 吸顶 `.toc-card`）。
- [x] 2.2 运行脚本重新生成全部 77 篇行业与案例文章（覆盖 `/case-studies/`, `/ai-search/`, `/geo/`, `/blog/`）。

## 3. 独立博文排版与目录重构
- [x] 3.1 为 6 篇早期博文（`geo-vs-seo-differences.html` 等）补充段落锚点与 280px 吸顶目录栏。
- [x] 3.2 为 `princeton-nine-factors-and-real-geo-for-buyers.html` 更新为统一的 280px 双栏布局。
- [x] 3.3 镜像同步至 `projects/nextgeo/outputs/site/blog/`。

## 4. 验证与审查
- [x] 4.1 本地 8088 端口排版验证（对比 deep-geo.cn 案例页）。
- [x] 4.2 0 Emoji 违规检测与双端一致性校验。
- [x] 4.3 完成 OpenSpec 归档并推送到 git origin/github main。
