# Tasks: 站点底座路由修复与阶段二GEO标准对齐加固

- [x] 1. 服务端路由与沙箱防御加固 (`tools/geo/server.py`)
  - [x] 1.1 增加 `/sites/{project_id}` 与子目录无斜杠时的 HTTP 301 自动重定向机制
  - [x] 1.2 扩展 `/api/projects/{id}/site/` 静态资源处理，支持预览 iframe 顺畅加载 assets 图片
  - [x] 1.3 重启本地服务或热加载验证重定向与预览资源
- [x] 2. 阶段二控制台修复 (`web/index.html`)
  - [x] 2.1 修复 `loadScaffoldTab` 与 `copyCurrentScaffold` 中的 DOM 元素 ID（修正为 `code-scaffold`）
  - [x] 2.2 验证各 Tab 切换（llms.txt / schema.jsonld / robots.txt）与复制代码功能正常
- [x] 3. 首页大模型爬虫双保险与知识图谱加固 (`projects/nextgeo/outputs/site/index.html`)
  - [x] 3.1 注入 `<link rel="alternate">` 与 `<link rel="sitemap">` 爬虫双保险标签
  - [x] 3.2 注入完整的 Schema.org JSON-LD 实体网络（LocalBusiness + FAQPage 8 组问答对）
  - [x] 3.3 注入排版防御基础兜底样式（防 CDN 波动白屏或飞散）
  - [x] 3.4 修正 `schema.jsonld` 中的 `logo.png` 为 `logo.jpg`
  - [x] 3.5 双向同步更新 `outputs/index.html` 与 `outputs/schema.jsonld`
- [x] 4. 自动化回归核验
  - [x] 4.1 测试 curl 重定向状态码（301）与目标地址
  - [x] 4.2 验证图片与静态资源 200 返回
  - [x] 4.3 校验 HTML 标签平衡性与大模型 Clean 抓取质量
