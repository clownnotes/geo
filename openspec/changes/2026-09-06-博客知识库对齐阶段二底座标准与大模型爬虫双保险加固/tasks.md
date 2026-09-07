# Tasks: 博客知识库对齐阶段二底座标准与大模型爬虫双保险加固

## 1. 自动化构建器脚本升级 (`scripts/build_blog_index.py`)
- [x] 1.1 修复阅读时长提取逻辑，统一规范输出为“阅读约 X 分钟”；
- [x] 1.2 在博客列表 HTML 模板 `<head>` 中新增 Schema.org JSON-LD 结构化数据生成（包含 `CollectionPage`、`Blog` 和前序文章 `ItemList`）；
- [x] 1.3 在博客列表 HTML 模板 `<head>` 中新增爬虫标准指引标签：`<link rel="sitemap">` 与 `<link rel="alternate">`；
- [x] 1.4 确保页脚中的 `llms.txt` 与 `sitemap.xml` 显式超链接完整保留，实现三重冗余抓取保障。

## 2. 全量自动化编译与镜像同步
- [x] 2.1 运行 `python3 scripts/build_blog_index.py`，全量重新生成 `outputs/blog/index.html` 与 `outputs/site/blog/index.html`；
- [x] 2.2 运行 `python3 scripts/check_article_styles.py`，确保全量博文与列表页 0 样式违规、0 Emoji 违规；
- [x] 2.3 检查并确认 `outputs/` 与 `outputs/site/` 的双向镜像对齐与一致性。

## 3. 本地端验证与交付核验
- [x] 3.1 本地 8088 端口验证 `http://localhost:8088/sites/nextgeo/blog/`：
  - 检查页面源码，验证包含合规的 Schema.org JSON-LD；
  - 检查页面源码，验证包含 `<link rel="sitemap">` 与 `<link rel="alternate">`；
  - 检查页面视觉，验证每张文章卡片显示正确的“阅读约 X 分钟”；
  - 检查页脚，验证超链接正常直达，多重冗余全部就绪。
- [x] 3.2 验证阶段二后台（`http://localhost:8088/#project=nextgeo&step=2&tab=site.html`）各项标准已 100% 对齐就绪。
