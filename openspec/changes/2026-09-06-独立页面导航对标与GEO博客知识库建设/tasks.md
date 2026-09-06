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

## 5. 对标 DeepGEO 博客知识库全量 77 篇文章克隆与品牌实体置换
- [x] 5.1 批量拉取 DeepGEO 77 篇权威博文原文与结构数据
- [x] 5.2 实施品牌实体与口径深度置换（DeepGEO -> 邻里GEO NextGEO，余果 -> 老白，深圳 -> 徐州/淮海经济区，deep-geo.cn -> nextgeo.baicl.cc）
- [x] 5.3 严格遵循普林斯顿 9 因子与零 Emoji 规范生成 77 篇独立静态 HTML（含 Schema.org TechArticle、右侧目录导航、FAQ 模块）
- [x] 5.4 升级 `blog/index.html`，支持“全部(77)”、“GEO(33)”、“AI搜索(35)”、“案例(9)”分类筛选与 77 篇卡片网格
- [x] 5.5 全量更新 `llms.txt` 与 `sitemap.xml`，同步双份目录（`outputs/site/` 与 `outputs/`）
- [x] 5.6 本地 8088 端口全量验证、零 Emoji 自动化核验与 Git 双端推送

## 6. 首页底部 Canonical Answers 板块 1:1 对标视觉卡片与封面图
- [x] 6.1 下载并持久化 6 篇优先展示文章封面图至 `assets/article-covers/`
- [x] 6.2 重构首页底部 Canonical Answers 为 6 张带 16:9 封面图、标题与发布日期的标准卡片
- [x] 6.3 卡片精准直达对应深度博客单篇，移除旧版纯文字排版
- [x] 6.4 本地 8088 端口验证、同步双份目录并完成 Git 双端推送

