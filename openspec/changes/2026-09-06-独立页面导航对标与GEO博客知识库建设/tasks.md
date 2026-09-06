## 1. 全站 4 大一级独立页面导航统一对标
- [x] 1.1 更新 `about/index.html` 顶部导航，加入 `博客` 链接，统一为 `首页`、`博客`、`服务`、`关于`，无锚点跳转
- [x] 1.2 更新 `services/index.html` 顶部导航，加入 `博客` 链接，统一为 `首页`、`博客`、`服务`、`关于`，无锚点跳转
- [x] 1.3 更新 `index.html` 顶部导航，统一为 `首页`、`博客`、`服务`、`关于`，移除 `#core-value`、`#workflow`、`#faq` 等页面内锚点

## 2. 首页精简化对标重构与“关于页”去重
- [x] 2.1 移除首页中的重复团队成员展示、冗余 FAQ 锚点块，消除与 `/about/` 的内容冲突
- [x] 2.2 强化首页四大标准对标板块：Hero 提问痛点与双主干按钮、3 大核心价值、4 步闭环战略、6 篇优先建设的 GEO 定义与方法页卡片
- [x] 2.3 确保首页中所有卡片点击均直达对应独立页面（`/services/`、`/about/`、`/blog/...`）

## 3. GEO 博客与实战知识库体系建设
- [x] 3.1 创建 `blog/index.html` 博客列表页，1:1 对标 DeepGEO 视觉质感、分类筛选与卡片网格
- [x] 3.2 编写首批 6 篇普林斯顿标准 GEO 权威深度实战文章（Markdown/HTML + Schema.org Article + 零 Emoji）：
  - `blog/geo-vs-seo-differences.html`
  - `blog/geo-execution-roadmap.html`
  - `blog/content-ai-citations.html`
  - `blog/entity-brand-modeling.html`
  - `blog/schema-clean-markdown.html`
  - `blog/b2b-decision-geo-strategy.html`
- [x] 3.3 同步更新 `llms.txt` 与 `sitemap.xml`，将博客文章全部注册入大模型与搜索引擎索引
- [x] 3.4 同步双份静态资产（`outputs/site/` 与 `outputs/`）

## 4. 本地验证与 Git 协同同步
- [x] 4.1 本地 8088 端口全流程抽检（首页、博客列表、博客单篇、服务页、关于页）
- [x] 4.2 检查全站代码严格杜绝任何 Emoji 彩色表情符号
- [x] 4.3 Git 提交并推送至 `origin main` 与 `github main`（坚决遵守不擅自推生产服务器原则）
