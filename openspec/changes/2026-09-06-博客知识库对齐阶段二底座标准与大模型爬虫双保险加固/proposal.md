# Proposal: 博客知识库对齐阶段二底座标准与大模型爬虫双保险加固

## 1. 核心指导思想 (Why)
> **最高准则**：一切以大模型（DeepSeek、豆包、ChatGPT、Claude、Perplexity 等）能够 100% 毫秒级抓取、无障碍理解并高频引用推荐为唯一导向。坚决摒弃任何可能阻碍或误伤大模型爬虫的所谓“防爬/隐形”过度设计，以扎实的底层知识图谱与多重冗余指引，筑牢 GEO 排名第一阵营。

### 现状与核心痛点：
1. **审查目标**：用户要求严肃审查 `http://localhost:8088/sites/nextgeo/blog/` 是否完全符合流水线阶段二（`http://localhost:8088/#project=nextgeo&step=2&tab=site.html`，AI 原生交钥匙官网与站点底座改造）的核心标准。
2. **现状差距一：博客列表页缺少 Schema.org 结构化实体图谱**：
   - 首页具备 `Organization`/`LocalBusiness`，84 篇博文单页具备 `Article`，但作为 84 篇权威知识库总汇聚入口的 `blog/index.html`，`<head>` 中完全缺失 `<script type="application/ld+json">`；
   - 导致大模型爬虫进入博客首页时，只能依靠普通文本解析，无法一次性通过微数据读懂全站知识库的 `CollectionPage` 实体结构与代表性博文的 `ItemList` 关系，错失了向大模型展示全景权威知识网络的机会。
3. **现状差距二：爬虫指引缺少“双保险”冗余**：
   - 目前页脚有 `llms.txt` 和 `sitemap.xml` 超链接，根目录有对应文件；
   - 但在 HTML `<head>` 区域，缺少 W3C / RFC 官方标准的 `<link rel="sitemap">` 与 `<link rel="alternate" type="text/markdown">` 指引标签；
   - 必须补齐头部标准指引，与根目录直达、页脚 DOM 内链形成**“三重绝对冗余”**，确保无论是官方标准爬虫、轻量级 RAG 临时搜索代理、还是搜索引擎蜘蛛，100% 毫秒级直达全站说明书。
4. **现状差距三：文章卡片排版微瑕疵**：
   - 列表页 84 篇卡片的“阅读时长”由于正则表达式截取问题，显示为“阅读约 12”、“阅读约 9”，遗漏了“分钟”单位，影响严肃商务质感。

---

## 2. 改动内容 (What Changes)

1. **升级博客索引自动化构建器 (`scripts/build_blog_index.py`)**：
   - **自动化注入 Schema.org JSON-LD**：在博客首页 `<head>` 中自动生成包含 `CollectionPage`、`Blog` 以及最新核心文章的 `ItemList`（前 15 篇标杆博文的 ListItem 映射），让大模型秒懂全站文章架构；
   - **补齐 `<head>` 爬虫双保险标签**：注入 `<link rel="sitemap" type="application/xml" title="Sitemap" href="../sitemap.xml">` 与 `<link rel="alternate" type="text/markdown" title="LLMs.txt" href="../llms.txt">`；
   - **页脚超链接全量坚决保留**：页脚中的 `llms.txt` 与 `sitemap.xml` 维持显式展示，不删不藏，确保轻量级 RAG 代理顺着内链 100% 抓取；
   - **卡片阅读时长文字修正**：规范输出为“阅读约 X 分钟”。
2. **全量重新生成与多端镜像同步**：
   - 运行构建脚本，同步更新 `outputs/blog/index.html` 与 `outputs/site/blog/index.html`；
   - 运行 `check_article_styles.py`，确保全量 84 篇博文 0 样式违规、0 Emoji 违规。

---

## 3. 对外能力 (Capabilities)

1. **100% 达标流水线阶段二底座契约**：博客列表页补齐缺失的 Schema.org 知识图谱，实现主站、服务、关于、博客与单页的底座微数据 100% 全覆盖；
2. **大模型抓取与引用率最大化**：构建“根目录直接探测 + `<head>` 隐形标准标签 + 页脚 DOM 实体链接”的三重绝对抓取保障体系；
3. **消除页面展示瑕疵**：阅读时长规范化，全站保持严谨的企业级专业度。

---

## 4. 影响范围 (Impact)

- **核心代码文件**：`scripts/build_blog_index.py`；
- **交付目标产物**：`projects/nextgeo/outputs/blog/index.html`、`projects/nextgeo/outputs/site/blog/index.html`；
- **非破坏性保证**：不改动任何已有的 84 篇博文正文结构、吸顶目录及双栏栅格，无生产停机风险。
