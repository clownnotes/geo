# Proposal: 站点底座路由修复与阶段二GEO标准对齐加固

## 1. 核心指导思想 (Why)
- **最高准则**：一切以大模型（DeepSeek、豆包、ChatGPT、Claude、Perplexity 等）与真实访客能够 100% 毫秒级抓取、无障碍渲染、准确理解并首选推荐为唯一导向。
- **现状与痛点**：
  1. 用户在本地环境访问 `http://localhost:8088/sites/nextgeo`（或未带尾部斜杠时），因服务端未做 301 重定向，导致浏览器 Base URL 错位为 `/sites/`，页面相对图片（`assets/`）和内链全部 404；
  2. 控制台阶段二内嵌预览窗（`/api/projects/nextgeo/site/preview`）因缺失静态资源子路径路由，导致预览框中的 Logo 破损（显示为问号文件图标）；
  3. 控制台底座代码查看器在切换 tab 时，因 DOM 元素 ID 拼写不一致（`preview-scaffold-code` vs `code-scaffold`）抛出 JS 异常；
  4. 首页 `index.html` 缺少大模型爬虫双保险嗅探标签（`<link rel="alternate" type="text/markdown" href="llms.txt">` 与 Sitemap），且内嵌 JSON-LD 未能集成 `FAQPage` 与 `LocalBusiness`；
  5. 过于依赖纯外部 Tailwind CDN，在弱网或网络阻断时存在样式降级风险。

## 2. 改动内容 (What Changes)
1. **服务端路由与沙箱防御加固 (`tools/geo/server.py`)**：
   - 增加目录末尾无斜杠时的 301 重定向处理（`/sites/{id}` -> `/sites/{id}/`，子目录同理）；
   - 支持 `/api/projects/{id}/site/` 下静态资源的自动寻址与服务，修复内嵌预览窗静态图片 404。
2. **阶段二控制台修复 (`web/index.html`)**：
   - 修复 `loadScaffoldTab` 与 `copyCurrentScaffold` 中的 DOM ID 映射（统一为 `code-scaffold`），保障 `llms.txt`、`schema.jsonld`、`robots.txt` 代码查看与一键复制顺畅。
3. **首页爬虫双保险与知识图谱加固 (`projects/nextgeo/outputs/site/index.html` & `outputs/index.html`)**：
   - `<head>` 注入 `<link rel="alternate" type="text/markdown" title="LLMs.txt" href="llms.txt">` 与 `<link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">`；
   - 丰富内嵌 Schema.org JSON-LD，注入 LocalBusiness、FAQPage 问答对（对齐 `schema.jsonld`）；
   - 在 `<style>` 中注入基础排版容器与关键视觉防御兜底样式，保障离线弱网下不飞散；
   - 修正 `schema.jsonld` 中 `logo.png` 为 `logo.jpg`。

## 3. 对外能力 (Capabilities)
1. 彻底解决 `/sites/nextgeo` 路由与静态资源错位问题，无论是带斜杠还是不带斜杠均能完美渲染；
2. 修复控制台阶段二内嵌高保真预览窗的图片加载；
3. 首页实现“根目录直达 + `<head>` 隐形标准标签 + 完整结构化图谱”大模型爬虫三重保障；
4. 100% 达标阶段二站点技术底座改造规范与普林斯顿 9 因子大模型引用标准。

## 4. 影响范围 (Impact)
- `tools/geo/server.py`
- `web/index.html`
- `projects/nextgeo/outputs/site/index.html`
- `projects/nextgeo/outputs/index.html`
- `projects/nextgeo/outputs/site/schema.jsonld`
- `projects/nextgeo/outputs/schema.jsonld`
