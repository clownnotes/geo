# AGENTS.md — GEO 项目开发与协同规范

> 本文件是所有 AI 助手（Antigravity、Windsurf、Claude Code、Cursor 等）在本项目中进行需求开发、代码编写与代码审查时的**最高指导协议**。

---

## 1. 核心工作流：OpenSpec 规范驱动开发

本项目严格遵循 **OpenSpec 规范** 进行任务拆解与多 IDE 协同开发：

1. **发起需求 (propose)**：通过 `./opsx propose <需求名称>` 创建中文命名变更目录；产出规范文档后**必须立即停步**等待用户或评审方审阅。
2. **规范文件**：
   - `proposal.md`：需求背景（Why）、改动范围（What）、对外能力（Capabilities）、影响分析（Impact）。
   - `design.md`：架构设计、接口规范、数据模型与组件划分。
   - `tasks.md`：细化任务清单（使用 `- [ ]` 与 `- [x]` 标记）。
   - `review-log.md`：跨 IDE 评审日志与共识记录。
3. **严格阶段隔离与单步停步铁律 (Strict Stage Boundary)**：
   - **`/opsx-review` 阶段**：仅负责跨端审查、对照 Spec 核对、在 `review-log.md` 中记录结论或按讨论订正 proposal/design/tasks。**完成后必须立即停步（STOP）等待用户或对端 IDE 确认，严禁擅自进入编码（apply）或归档（archive）！**
   - **`/opsx-apply` 阶段**：严格按 `tasks.md` 编码并验证，测试通过后**必须立即停步（STOP）向用户汇报进展**，等待用户人工验收。**严禁擅自执行归档！**
   - **`/opsx-archive` 归档硬约束**：**只有当用户明确下达归档指令（显式输入 `/opsx-archive` 或文字明确要求“归档”）时，方可执行 `./opsx archive` 归档与推送。任何自动串联归档均为严重违规！**
4. **对端 IDE 审查意见的直接修复工作流 (Review-to-Fix Flow)**：
   - **方案/设计类问题**（如合规矩阵、字段定义、架构分歧）：使用 `/opsx-review`，仅订正 `proposal.md` / `design.md` / `tasks.md`，并在 `review-log.md` 标记 `[已达成共识]`，然后**立即停步**；
   - **代码/功能/Bug/测试缺陷**：使用专属快捷指令 **`/opsx-fix`**（或 `/opsx-apply`），直接定位源码与测试脚本进行修复，通过自动化回归后在 `review-log.md` 标记 `[已修正]`，然后**立即停步**等待复审，严禁擅自归档。
5. **任务跟踪**：
   - 使用 `./opsx status` 查看当前进度。

---

## 2. 角色定义与协作沟通

* **用户角色**：产品负责人 / 需求提出者（使用直白中文沟通，直奔主题）。
* **AI 角色**：全栈工程师 / GEO 架构师。
* **跨 IDE 评审协议**：
  - 评审者（Reviewer）需在 `review-log.md` 中以 `[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]` 标注结论。
  - 只要最后一条状态为 `[待讨论]`，不可擅自进入代码合并或归档阶段。

---

## 3. 工程与 GEO 编码约束

1. **结构化与大模型友好**：
   - 编写 Markdown 内容与技术文档时，严格遵循**普林斯顿 9 因子**（结论先行、数据量化、Markdown 表格、FAQ 问答对）。
2. **多端与爬虫支持**：
   - 网站建设需确保服务端渲染（SSR）或静态预渲染（SSG），确保 `Crawl4AI` / `Firecrawl` 可完整提取 Clean Markdown。
   - 必须配置 `/llms.txt` 与 Schema.org (JSON-LD) 实体元数据。
3. **视觉与设计规范（严禁滥用 Emoji 表情）**：
   - **严禁在企业级页面、交付打样站点、商业白皮书与报告中使用 Emoji 彩色表情符号**（如 ⚡️、💡、⚠️、⚙️、💻、🤝、💎、⚖️、🎓、💬 等）；
   - Emoji 在严肃商业决策与 B2B 语境下极度突兀、廉价且不专业；
   - 视觉冲击力与层次感必须依靠高质感的排版层级、严谨的文字对比、微渐变/发光线框、数据加粗与专业 Tag 标签呈现，坚决杜绝任何低幼玩具感。
4. **内容流与发布时序规范（严格时间倒序）**：
   - 凡是在首页（`Canonical Answers` 精选板块）或博客知识库列表展示的文章，**一律严格按照发表时间（`datePublished`）由新到旧倒序（Descending）排列**；
   - 新增、修改或同步博文后，必须执行自动排序校验（如运行 `./scripts/sort_homepage_articles.py`），杜绝任何时序错乱。

---

## 4. 生产部署与 Git 协同约束

1. **生产发布触发协议（最高优先级约束）**：
   - **严禁私自/自动向生产服务器（`mini` / `geo.baicl.cc`）部署或重启生产进程**；
   - 开发与审查阶段的所有代码与功能**一律仅在本地开发端（http://127.0.0.1:8088）测试与验证**；
   - **只有当用户明确指示推生产（如“部署到生产”、“推到线上网站”）时**，方可执行生产发布。
2. **Git 协同推送规范**：
   - 开发端阶段性测试通过后，Git 仓库必须正常执行提交并推送到远端（`git push origin main` 与 `git push github main`），确保多端代码同步。

---

## 5. 服务端拓扑与交付架构战略（物理机 + VPS 转发 + 边缘 CDN）

> 详细规范与参数见：[`docs/strategy/server-architecture.md`](docs/strategy/server-architecture.md)

1. **三层交付拓扑**：
   - **第三层：家用物理机 (Mac mini)**：自备物理服务器，中国联通动态公网 IP（50 Mbps 上行），作为总控母体、语料提纯、建站编译中心；
   - **第二层：公网商用 VPS (3~5 Mbps)**：具备固定商用 IP，承载客户域名直接解析（A/CNAME）与 Nginx 反向代理；
   - **第一层：腾讯云边缘 CDN**：全国/全球边缘加速，承载大模型爬虫并发抓取与静态缓存。
2. **静态缓存时机策略**：
   - **开发预览态**：强制 `no-cache` 与动态时间戳，修改素材与重新编译秒级显现；
   - **生产发布态**：经定稿确认后交由 CDN 强缓存；变更时通过管理台触发 CDN 缓存刷新（Purge Cache），绝不在开发阶段死锁缓存。
3. **客户全托管交付**：
   - 客户无需了解底层服务器与代码，全权由我方交付与运维；同时保留整站源码包一键导出功能，作为客户离线资产兜底。

---

## 6. 文章排版与博客自动同步工程规范（多 IDE 协同最高执行标准）

> 详细技术规范与 DOM 模板见：[`docs/specs/article-template-standard.md`](docs/specs/article-template-standard.md)

1. **统一双栏栅格与吸顶目录（对标 DeepGEO 280px 标准）**：
   - 全站所有博文与案例页面严格遵循 `grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_280px] gap-8 xl:gap-10 items-start`；
   - 正文使用标准的 `.content-block` 语义化样式，**严禁使用任何 `.prose-geo` 等老旧类名**；
   - 右侧目录统一为固定 **280px** 宽度的 `.toc-card`，吸顶于 `top-24`，包含“页面结构”标题与平滑滚动锚点；
   - 页面严格注入 `html { scroll-behavior: smooth; }` 与 `.content-block, [id^="block-"], #faq { scroll-margin-top: 100px; }`。
2. **博客索引动态自动扫描（杜绝新文章丢失）**：
   - 新增或编辑文章后，**严禁依赖写死的爬虫数组**；
   - 必须统一通过 `python3 scripts/build_blog_index.py` 动态扫描 `projects/nextgeo/outputs/blog/*.html` 全量文章；
   - 必须严格按照发表时间（`datePublished`）由新到旧绝对倒序排列，自动同步更新 `blog/index.html`、`llms.txt` 与 `sitemap.xml`；
   - 必须严格执行 `outputs/` 到 `outputs/site/` 的双向镜像对齐。
3. **多 IDE 协同脚手架支持**：
   - 无论在 Antigravity、Windsurf、Claude Code 或 Cursor 中新建文章，推荐使用 `python3 scripts/create_article.py` 生成标准骨架；
   - 提交前必须执行 `python3 scripts/check_article_styles.py` 确保 100% 样式合规与 0 Emoji 违规。
4. **HTML 标签闭合与 DOM 平衡铁律（杜绝目录栏坠底）**：
   - 正文中的所有数据表格必须成对包裹在 `<div class="overflow-x-auto my-6"><table class="content-table">...</table></div>` 中；
   - **严禁出现悬空未配对的 `</div>` 闭合标签**，否则会导致双栏栅格容器提前闭合，将右侧 `<aside>` 目录栏挤出栅格下坠至页面最底部；
   - 提交前必须执行 `python3 scripts/check_article_styles.py`，确保全站文章 `open_divs == close_divs` 100% 绝对平衡。
5. **文章封面图绑定与防串图规范**：
   - 博客索引构建器仅允许精准读取与文章 slug 对应的 `article-covers/{slug}.*` 或正文首图，**严禁将任何特定文章的插图作为全局兜底**；
   - 无封面时必须统一展示标准分类微渐变徽章，坚决杜绝封面张冠李戴。

---

## 7. 站点技术底座与大模型爬虫工程规范（多租户托管与协议最高约束）

> 详细技术规范与页面类型合规矩阵见：[`docs/specs/site-scaffold-standard.md`](docs/specs/site-scaffold-standard.md)

1. **静态多租户托管严格 301 尾部重定向 (Strict Trailing Slash Rule)**：
   - 访问 `/sites/{project_id}` 或站内任意静态子目录若末尾缺少 `/`，服务端**必须强制执行 HTTP 301 永久重定向补齐末尾 `/`**；
   - 严禁直接 200 返回页面，杜绝浏览器 Base URL 错位导致 `assets/` 相对图片与内链大面积 404。
2. **大模型爬虫三重绝对冗余 (Triple Redundancy)**：
   - **根目录探测**：必须保障 `/llms.txt`、`/robots.txt`（明确放行国产 5 大 AI 爬虫）与 `/sitemap.xml` 可访问；
   - **`<head>` 隐形嗅探**：全站所有 HTML 页面必须成对注入 `<link rel="alternate" type="text/markdown" href="...">` 与 `<link rel="sitemap" type="application/xml" href="...">`；
   - **DOM 显式内链**：页脚必须保留直接指向 `llms.txt` 与 `sitemap.xml` 的可点击超链接。
3. **页面类型差异化 Schema.org 实体图谱矩阵**：
   - **首页**：必须聚合 `Organization` + `LocalBusiness` + `WebSite` + `Service` + `FAQPage`（8~15 组高频问答对）；
   - **博客知识库列表**：必须配备 `CollectionPage` + `Blog` (+ `ItemList`)；
   - **博文/案例单页**：必须配备 `Article`/`TechArticle`（FAQPage 非强制）；
   - 实体声明的所有图片资源（如 `logo.jpg`）必须在本地磁盘真实存在且后缀一致。
4. **前端排版防御性 CSS 兜底 (CSS Resilience Standard)**：
   - 严禁纯裸奔依赖外部 Play CDN（如 `cdn.tailwindcss.com`）；
   - 页面 `<style>` 必须内联盒模型 `border-box`、自适应图片、字阶与 `.geo-container` 容器约束，防范离线弱网排版飞散。
5. **脚手架编译防覆盖锁定机制 (Scaffold Override Protection)**：
   - 当 `project.yaml` 声明 `custom_site: true` 时，阶段二脚手架（`scaffold.py`）**严禁重新生成并覆盖 `index.html`**，严禁覆盖存量定制子站目录（about/services/blog 等）；
   - `/llms.txt` 与 `/schema.jsonld` 若已存在定制版本则严格保留，仅允许刷新 `/robots.txt` 放行规则。
