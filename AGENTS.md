# AGENTS.md — GEO 项目开发与协同规范

> 本文件是所有 AI 助手（Antigravity、Windsurf、Claude Code、Cursor 等）在本项目中进行需求开发、代码编写与代码审查时的**最高指导协议**。

---

## 1. 核心工作流：OpenSpec 规范驱动开发

本项目严格遵循开源 **OpenSpec 1.16.0** 规范与官方生成的工作流/技能进行任务拆解与开发（官方生成物位于 `.agents/workflows/`、`.agents/skills/openspec-*` 及各 IDE 对应目录，禁止手改，升级 CLI 后运行 `openspec update` 同步）：

1. **日常交互入口（官方工作流与技能）**：
   - **探讨**：`/opsx-explore`（`openspec-explore`）— 只排查和讨论，严禁写业务代码；
   - **发起需求**：`/opsx-propose`（`openspec-propose`）或 `openspec new change <change-name>` — 生成 `proposal.md`、`specs/`、`design.md`、`tasks.md`，产出后**必须立即停步**等待用户审阅；
   - **开发实施**：`/opsx-apply`（`openspec-apply-change`）— 按 `tasks.md` 逐项编码并验证，完成后**必须立即停步**汇报，等待用户人工验收；
   - **订正方案**：`/opsx-update`（`openspec-update-change`）— 仅修正规划文档，不写业务代码；
   - **同步规格**：`/opsx-sync`（`openspec-sync-specs`）— 将变更中的 delta specs 合并到 `openspec/specs/`；
   - **验收归档**：`/opsx-archive`（`openspec-archive-change`）— 仅在用户明确下达归档指令时执行。
2. **命名与规格文件约束**：
   - **历史存量与新变更口径**：历史 145 个中文归档与当前正在进行的变更保持原名继续推进；**今后所有新建变更目录一律使用纯英文小写短横线 `kebab-case`**（如 `2026-11-20-align-openspec-official`），中文需求标题写进 `proposal.md`；
   - **规范文件**：包含 `proposal.md`（Why / What / Capabilities / Impact）、`specs/<能力名>/spec.md`（delta 规格）、`design.md`（架构与推导链条）、`tasks.md`（`- [ ]` / `- [x]` 任务清单）；
   - **行为契约与豁免**：涉及业务行为或接口契约改动时，**必须编写 delta `specs/`，且每个场景须成对包含 `WHEN`（或 `GIVEN`）与 `THEN` 步骤**；纯工具、重构或纯文档类变更可在 `.openspec.yaml` 中设置 `skip_specs: true` 豁免。
3. **严格阶段隔离与归档硬约束 (Strict Stage Boundary)**：
   - **探讨/提案/订正阶段**：只动规范文档，不写业务代码，完成后**必须立即停步（STOP）**等待用户确认；
   - **实施阶段**：严格按 `tasks.md` 编码与自测，完成后**必须立即停步（STOP）**向用户汇报进展，**严禁擅自归档**；
   - **归档硬约束**：归档权完全归用户。**只有当用户明确下达归档指令（显式输入 `/opsx-archive` 或明确说“归档”）时**，才可执行 `openspec validate <change-name> --strict` 与 `openspec archive <change-name> -y`（无 delta specs 变更可加 `--skip-specs`）。任何自动串联归档均为严重违规！
4. **常用官方原生 CLI 命令**：
   - 查看进行中变更：`openspec list --json`；
   - 查看变更完成度：`openspec status --change <change-name>`（或 `openspec status --all`）；
   - 严格校验格式：`openspec validate <change-name> --strict`（或 `openspec validate --changes --strict`）；
   - 非交互归档：`openspec archive <change-name> -y`。
5. **可选本地独立审查工具**：
   - 本项目保留 `scripts/workbuddy_reviewer.py` 与 `scripts/qoder_reviewer.py` 作为可选的独立本地审查工具；
   - 审查结果统一输出到 `docs/reviews/<变更名>.md`（仓库已预置 `docs/reviews/` 目录，首次运行审查脚本时自动写入对应报告；不再向变更目录写入 `review-log.md`），仅供跨端核对与人工复核参考。

---

## 2. 角色定义与协作沟通

* **用户角色**：产品负责人 / 需求提出者（使用直白中文沟通，直奔主题）。
* **AI 角色**：全栈工程师 / GEO 架构师。
* **审查与协作协议**：
  - 跨端或独立本地审查（`docs/reviews/<变更名>.md`、PR 评论或对话核对）可使用 `[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]` 标注结论；
  - 只要核心分歧仍处于 `[待讨论]`，不可擅自进入编码或归档阶段。

---

## 3. 工程与 GEO 编码约束

1. **结构化与大模型友好**：
   - 编写 Markdown 内容与技术文档时，严格遵循**普林斯顿 9 因子**（结论先行、数据量化、Markdown 表格、FAQ 问答对）。
2. **多端与爬虫支持**：
   - 网站建设需确保服务端渲染（SSR）或静态预渲染（SSG），确保 `Crawl4AI` / `Firecrawl` 可完整提取 Clean Markdown。
   - 必须配置 `/llms.txt` 与 Schema.org (JSON-LD) 实体元数据。
3. **视觉与设计规范（严禁滥用 Emoji 表情）**：
   - **严禁在企业级页面、交付打样站点、商业白皮书与报告中使用任何彩色表情符号（Emoji）**；
   - Emoji 在严肃商业决策与 B2B 语境下极度突兀、廉价且不专业；
   - 视觉冲击力与层次感必须依靠高质感的排版层级、严谨的文字对比、微渐变/发光线框、数据加粗与专业 Tag 标签呈现，坚决杜绝任何低幼玩具感。
4. **内容流与发布时序规范（严格时间倒序）**：
   - 凡是在首页（`Canonical Answers` 精选板块）或博客知识库列表展示的文章，**一律严格按照发表时间（`datePublished`）由新到旧倒序（Descending）排列**；
   - 新增、修改或同步博文后，必须执行自动排序校验（如运行 `./scripts/sort_homepage_articles.py`），杜绝任何时序错乱。
5. **管理端功能文字解答与引导说明规范（麦肯锡 V-W-W-H 标准）**：
   - 详细规范见：[`docs/specs/ui-feature-explanation-standard.md`](docs/specs/ui-feature-explanation-standard.md) 与 [`.cursor/rules/plain-speak.mdc`](.cursor/rules/plain-speak.mdc)；
   - **V-W-W-H 四层金字塔（结论先行）**：管理端所有功能页面的顶部说明，严格按 Value（核心交付成果与价值）、What（本质比喻与边界）、Why（不做的严重后果与避坑）、How（极简 1-2-3 动线与人机分工）四层组织；
   - **四色语义与令牌**：主色紫严格引用 [`docs/specs/geo-admin-ui-tokens.md`](docs/specs/geo-admin-ui-tokens.md) 的 `--geo-primary: #7c5bf5`（Value），搭配冷调蓝灰（What）、暖调琥珀黄（Why）、通路翡翠绿（How）；采用浅底（`-50`）+ `border-l-4` 侧彩条；
   - **红色 100% 绝对保护**：红色保留给运行报错与危险删除，功能说明中 100% 严禁出现红色；0 处 Emoji 表情；
   - **阶段零两件真东西禁混谈条款**：文案只谈「问题清单」与「豆包答案存档」，严禁自造「底牌报告 / 基线 / 剧本 / 探活」充当主文案；How 三步必须对应页内 1/2/3 步（出题 -> 真问 -> 写入），严禁把落盘与写入混谈；保留动态 `modeBanner`（首轮/再测）与状态芯片。
   - **适用范围收口声明（2026-11-22 师弟立规）**：本条 V-W-W-H 文案标准自即日起迁移至小毛驴 `02_管理员操作端/XiuLan_IDE/RULES.md` 第六节，GEO 仓内 `docs/specs/ui-feature-explanation-standard.md` 与 `docs/specs/geo-admin-ui-tokens.md` 降级为只读历史参考；绝对禁止在 GEO 仓新增任何管理端页面文案、状态芯片或引导浮层；存量文案随旧管理台下线一并归档，不维护双份文案真相源。

---

## 4. 生产部署与 Git 协同约束

1. **生产发布触发协议（最高优先级约束）**：
   - **严禁私自/自动向生产服务器（`mini` / `geo.baicl.cc`）部署或重启生产进程**；
   - 开发与审查阶段的所有代码与功能**一律在 NE1 验证端测试与验证**（见 §4 第 5 条）：旧 `:8088` 管理台（`scripts/run_geo_prod.sh` 与 `deploy/nginx_geo.conf` 的 8088 反代块）退役后，验证入口统一切换至小毛驴 `:3002`（前店开发）与同机旁挂 `:18092`（后厂 Worker 直连自检）；`:8088` 退役仅针对旧管理台进程与其反代块，不影响 NE1 作为编译中心与验证中心的定位；
   - **只有当用户明确指示推生产（如“部署到生产”、“推到线上网站”）时**，方可执行生产发布。
2. **Git 协同推送规范**：
   - 开发端阶段性测试通过后，Git 仓库必须正常执行提交并推送到远端（`git push origin main` 与 `git push github main`），确保多端代码同步。
3. **双仓资料分工（Agent 必读）**：
   - **GEO（本仓）**：代码 + OpenSpec + SOP + `project.yaml` + 词库/报告等轻量真源；双推自建 `origin` 与 `github`。
   - **GEOZiLiao（并列目录 `/Users/a1/代码/GEOZiLiao`）**：客户整站 `site/`、大图 `assets/`、结案大 ZIP；**仅**推自建 `https://git.baicl.cc/admin/GEOZiLiao.git`，**严禁**加 GitHub remote。
   - GEO 后厂运行时只读写本仓 `projects/{id}/outputs/`（成品文件落盘）；业务状态真相源不在本仓，GEO 仓内旧管理台（`src/web/index.html` 与 `:8088` 常驻进程）属于退场对象，客户档案、SOP 0~7 步进度、代采记账、后厂异步任务、已发布博文这五类业务状态，严格一事一表，一律由小毛驴 Go 后端与 `geo_projects` / `geo_sop_steps` / `geo_ad_orders` / `geo_baseline_posts` / `geo_worker_jobs` 五表承接，严禁跨实体借用 payload 字段塞入无关数据；资料仓是备份镜像，不是运行入口。
   - 备份：`./scripts/sync_delivery_to_ziliao.sh [client_id]` → 进入 GEOZiLiao commit + `git push origin main`。
   - 恢复：`./scripts/restore_delivery_from_ziliao.sh [client_id]`。
   - 生产机首次切换 / pull 后补站：`scripts/cutover_ziliao_on_mini.sh`（克隆资料仓 → pull 主仓 → 立刻 restore）。
   - 完整约定见：[`docs/strategy/customer-materials-repo.md`](docs/strategy/customer-materials-repo.md)。
4. **极简标准推生产流程（两步直达，严禁繁琐探查）**：
   - **第 1 步：本地双推**：
     ```bash
     git push origin main && git push github main
     ```
   - **第 2 步：生产物理机单行拉取**：
     ```bash
     ssh mini "cd /Users/ne/apps/GEO && git pull github main"
     ```
   - 若生产依赖的 `outputs/site|assets` 已从主仓 gitignore、仅存资料仓：推生产前须在 mini 并列拉 GEOZiLiao 并执行 restore（见资料仓文档），避免线上站点被 pull 清空。
   - **铁律**：严禁在推生产时擅自登录多台机器扫描端口、查杀进程或修改 Nginx；生产机 Web 服务直接挂载静态文件，`git pull` 完成后秒级生效。
5. **编译与验证机器口径（2026-09-28 师弟立规最高标准）**：
   - **本地笔记本定位（打字机与遥控器）**：无论是 2019 PRO 还是 M1 等开发笔记本，一律仅作为纯源码编辑与 Git 提交端，**绝对严禁在本地执行重型编译（如大型 build、本地常驻测试服务等）**，杜绝小内存发烫与环境漂移；
   - **NE1 服务器定位（唯一编译中心与测试真相源）**：NE1（Mac mini M4）拥有充足空闲内存，Tailscale 静态内网 IP 为 `100.83.64.112`（SSH 用户 `ne`，端口 `22`）。所有构建打包、接口测试与端到端功能验证**一律且只在 NE1 服务器上就地完成**：旧 `:8088` 退役前在 8088 验证，退役后统一切换至小毛驴 `:3002`（前店）与同机 `:18092`（后厂 Worker）验证；NE1 作为编译中心与验证中心的定位不变；

---

## 5. 服务端拓扑与交付架构战略（物理机 + VPS 转发 + 边缘 CDN）

> 详细规范与参数见：[`docs/strategy/server-architecture.md`](docs/strategy/server-architecture.md)  
> 客户重资料与主仓分工见：[`docs/strategy/customer-materials-repo.md`](docs/strategy/customer-materials-repo.md)

1. **三层交付拓扑**：
   - **第三层：家用物理机 (Mac mini)**：自备物理服务器，中国联通动态公网 IP（50 Mbps 上行），作为总控母体、语料提纯、建站编译中心；
   - **第二层：公网商用 VPS (3~5 Mbps)**：具备固定商用 IP，承载客户域名直接解析（A/CNAME）与 Nginx 反向代理；
   - **第一层：腾讯云边缘 CDN**：全国/全球边缘加速，承载大模型爬虫并发抓取与静态缓存。
2. **静态缓存时机策略**：
   - **开发预览态**：强制 `no-cache` 与动态时间戳，修改素材与重新编译秒级显现；
   - **生产发布态**：经定稿确认后交由 CDN 强缓存；CDN 缓存刷新（Purge Cache）一律由小毛驴 Vue 工作台调用 Go 后端接口 `POST /api/v1/geo/projects/:project_id/cdn-purges` 触发，GEO 后厂 Python 进程不得持有 Purge 凭证、不得自行调用 CDN API，绝不在开发阶段死锁缓存。
3. **客户全托管交付**：
   - 客户无需了解底层服务器与代码，全权由我方交付与运维；同时保留整站源码包一键导出功能，作为客户离线资产兜底。
4. **开发测试与防幻觉红线（严禁绕道 VPS）**：
   - **开发端与验证中心直连**：代码编辑在本地，构建与端到端测试统一对接 NE1 验证中心，统一走 **Tailscale 虚拟内网直连（`100.83.64.112`）**；旧 `:8088` 退役前在 8088 验证，退役后统一切换至小毛驴 `:3002`（前店）与同机 `:18092`（后厂 Worker）验证；
   - **严禁在 SSH 配置中注入 `ProxyJump vps`**，严禁把开发者内网直连流量塞进 VPS 跳板；
   - **生产环境全套部署在家里 mini（NE）**，VPS 仅作为公网 Nginx 域名反代，**VPS 上绝对不部署业务代码或测试环境**；
   - 详细拓扑与三机分工标准见 [`docs/strategy/server-architecture.md`](docs/strategy/server-architecture.md) 第五节。


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

---

## 8. 极速前端原型沙盒与物理持久化规范（新项目起手最高效路径）

> 详细技术规范与克隆流程见：[`docs/specs/prototype-frontend-workflow-for-agents.md`](docs/specs/prototype-frontend-workflow-for-agents.md)  
> 外挂盘总规则手册见：`/Volumes/联想120/临时前端/README_给Agent看的极速前端规范.md`

1. **先原型后大后端（拒绝闭门造车）**：
   - 新项目或复杂交付动线探索期，**严禁一上来就写复杂的 Go/Python 大后端或直接建数据库表**；
   - 必须先通过“外挂盘极速前端沙盒”打磨高保真原型，待产品经理在浏览器里亲手操作、顺畅跑通、拍板确认后，再回迁主工程并补全后端。
2. **本地 JSON 真实物理落盘（严禁纯内存假交互）**：
   - 严禁仅靠 `localStorage` 或前端内存变量存数据（刷新就丢无法连贯测试）；
   - 必须依托标准库 `server.py` 将增删改查物理写入 `data/projects.json`（或项目 JSON），确保 Safari 刷新或关闭后数据永不丢失。
3. **新项目 1 分钟快速克隆拉起**：
   - 复制 `/Volumes/联想120/临时前端/邻里GEO 的临时前端/` 成为新目录；
   - 改写 `server.py` 与启动脚本的端口（如 `5189`、`5190`）；
   - 清空并初始化 `data/projects.json` 骨架数据，启动后台服务即可对客/对内交付体验。
4. **原型沙盒退场边界（2026-11-22 师弟立规）**：外挂盘原型沙盒只用于需求探索期的高保真演示，其 `data/projects.json` 是临时演示数据，绝对禁止升格为业务真相源；原型确认后必须回迁小毛驴 `02_管理员操作端/XiuLan_IDE/src/admin/views/geo/`（本变更新建，待建）并由 Go 后端 `geo_*` 五表承接数据；沙盒目录只保留静态素材，不保留常驻服务。

---

## 9. 前店后厂分工与后厂异步计算车间定位（2026-11-22 师弟立规 · GEO 仓最高定位条款）

> 详细契约见：[geo-worker-contract](openspec/changes/2026-11-22-geo-nextdoor-architecture-split/specs/geo-worker-contract/spec.md) 与 [dual-workspace-governance](openspec/changes/2026-11-22-geo-nextdoor-architecture-split/specs/dual-workspace-governance/spec.md)

1. **一句话定位**：GEO 仓（`/Users/a1/代码/GEO`）是无状态后厂计算车间 + 客户静态成品输出仓；小毛驴（`/Users/a1/next核心项目`）是前店 + 数据大管家。管理台界面、业务接口、权限鉴权、关系型数据库全部归小毛驴，GEO 仓只负责计算与落盘成品。
2. **后厂三条绝对禁令（违反即架构红线）**：
   - **禁止连接任何 MySQL 实例**：GEO 后厂 Python 进程禁止连接 `Leishen-DB:3306` 业务 MySQL（实测为 MySQL 8.0.46）及任何 MySQL 实例，禁止读取 `/Users/ne/nextMysql` 冷备目录（Standby Replica），禁止执行任何 DDL/DML，禁止自建平行业务状态表；后厂只读输入参数、只写磁盘成品文件；
   - **不得保留平行真相源，且严禁跨实体借用字段**：后厂不得保留任何平行业务状态库或状态 JSON。5 张核心表严格一事一表（客户档案→`geo_projects`、SOP 0~7 步进度→`geo_sop_steps`、`ad_orders.json` 代采记账→`geo_ad_orders`、已发布博文→`geo_baseline_posts`、后厂异步任务→`geo_worker_jobs`），**严禁跨实体借用 payload 字段塞入无关数据**；除上述五表外本变更不建任何业务表，散装 YAML/JSON 只能作为任务中间产物与静态素材；退场对象必须点名：存量 `projects/{id}/history.db`（磁盘已实测存在；实测 `xuzhou_xuanyuan` 为自增 ID 的 `monitor_history` 表，含 `id INTEGER PRIMARY KEY AUTOINCREMENT`；实测 `demo_corp` 为无主键的 `sightings` 表，无 `id` 列）属旧巡检平行库，随旧管理台退役直接停写归档，不跨表塞入 `geo_worker_jobs`；随旧管理台退役必须同时停巡检（上一轮按 DeepSeek #67-3 / 千问 #69-C 收口：停巡检 = 停止 `src/tools/geo/server.py` 的 `:8088` 进程，实测其 `/api/portfolio/patrol` 位于 L952-L953、`/api/patrol/trigger` 位于 L1787-L1788，巡检由这两个路由触发；实测两仓 15 个 `*.plist` grep `patrol` 零命中，不存在独立 cron/launchd 登记可注销，因此同时必须停止任何外部定时任务对 `/api/portfolio/patrol` 的调用；实测 `src/tools/geo/patrol.py` L105-L119 建 `monitor_history` 表、L138 连接 `history.db`、L141 写 `monitor_history`，L366 调 `check_ledger.append_check_log` 写 `data/ops_check_logs.jsonl`（实测 `src/tools/geo/check_ledger.py` L18-L19 定义 `DATA_DIR` 与 `LOG_FILE`，磁盘 `data/ops_check_logs.jsonl` 已实测存在）；`history.db` 与 `data/ops_check_logs.jsonl` 一并列入退场平行源清单，随旧管理台停写归档，确保 `history.db` 彻底停写归档；若后续要持久化巡检历史，必须另立变更新增 `geo_patrol_records` 表并成对写 `migrations/YYYY-MM-DD_name.up.sql` 与 `.down.sql`；`projects/{id}/raw_materials/ledger/facts.jsonl`（磁盘已实测存在；实测核心字段为 `fact_key`/`category`/`statement`/`value`/`unit`/`status`/`sources`/`candidates`/`confirmed_snapshot`/`updated_at`）仅作为后厂建站磁盘输入素材，不作为业务状态落库，亦不借道塞入 `geo_sop_steps` 或 `geo_baseline_posts`；迁移完成后后厂停写 `raw_materials/`，存量 `facts.jsonl` 仅作只读磁盘历史素材保留（不再新增写入），`build_site` 所需新事实由 Go 后端在调用参数中显式传入（若未来持久化则另立变更建表，新增 `geo_facts` 表并成对上/下迁移脚本）；`projects/{id}/ad_orders.json`（代码路径存在，磁盘当前无实例）代采记账唯一落库为 `geo_ad_orders`，按表契约逐列写入，不得整块塞进其他表的 payload；
   - **禁止新建管理台**：绝对禁止在 GEO 仓新增任何管理端页面、表单、仪表盘或业务状态 JSON。`src/web/index.html`（1.18 MB 单文件旧管理台）与 `:8088` 常驻进程属于退场对象，提纯完成后一次性下线，不保留双轨过渡期。
3. **后厂异步任务接口契约（唯一对外入口，仅小毛驴 Go 后端调用，不带 `/api/v1` 前缀）**：
   | 接口 | 方法 | 行为 | 返回 |
   | :--- | :--- | :--- | :--- |
   | `/worker/jobs` | `POST` | 提交任务（`job_type` + 客户标识 + 参数） | HTTP 202 + 全局唯一后厂内部 `job_id`（该后厂内部 `job_id` 对应小毛驴 `geo_worker_jobs.worker_job_id`，**不是** Go 对外返回的雪花主键 `job_id`；前端只读 Go 的雪花 `job_id`），后台异步执行 |
   | `/worker/jobs/{job_id}` | `GET` | 查询任务状态 | `queued` / `running` / `succeeded` / `failed`；成功附带结果 JSON 与成品路径，失败附带底层报错原文 |
   - **后厂 `job_id` 与前店雪花 `id` 绝对区分（写死口径）**：后厂 `/worker/jobs` 返回的全局唯一 `job_id` 在小毛驴数据库中对应 `geo_worker_jobs.worker_job_id` 字段，**不是** Go 雪花主键 `id`（`geo_worker_jobs.id`），两者绝对不得混称；前店对外 URL 只接受雪花主键 `id`，后厂内部 `job_id` 仅供 `GeoWorkerClient` 向后厂轮询使用，不暴露在对外 URL；
   - 完整 9 类任务（基础 4 类 + 交付与对客 5 类）：基础 4 类为 `diagnose`（官网诊断）、`probe`（大模型问答采样）、`build_site`（静态建站）、`build_blog`（博客保活构建）；交付与对客 5 类为 `boss_report`（老板诊断单文件报告）、`share_portal`（7~30 天免密分享大屏生成）、`distribute_pack`（公众号/知乎/头条多平台排版分发包）、`acceptance_report`（07 交接确认单与 A4 证书，含无大 ZIP 约束）、`pitch_roi`（售前商业建议书与 ROI 测算）；
   - `/api/v1` 前缀只属于小毛驴 Go 后端对外接口，后厂接口一律不带该前缀；绝对禁止长连接同步阻塞等待结果，长耗时抓取与采样必须走异步提交 + 轮询；
   - 内部服务凭证强制校验（本轮按 DeepSeek #85-3 写死请求头名）：调用后厂时 MUST 携带请求头 `X-Geo-Internal-Token: <token>`，其值取自环境变量 `GEO_WORKER_INTERNAL_TOKEN`；小毛驴 Go `GeoWorkerClient` 与后厂 Python Worker 双方必须严格按该 Header 传输与校验；该 Header 为 GEO 后厂 Worker 专用，与现有蜂群后厂微服务 `:8091` 专用的 `X-Swarm-Api-Key` / `Authorization: Bearer` 彻底分开，两者不得混用，GEO 后厂接口严禁使用 `Authorization: Bearer`；请求缺少该 Header 或其值与环境变量不一致，后厂 MUST 返回 HTTP 401；非法 `job_type` 返回 400；查不到的 `job_id` 返回 404。
4. **同机旁挂与网络安全（写死口径）**：后厂 Worker 实现落点为 `src/tools/worker/`（本变更新建，尚无现存目录；实测 `src/tools/` 现有只有 `__init__.py`、`__pycache__` 与 `geo`，无 `worker`，新建 `src/tools/worker/` 后才有该目录），现有 `src/tools/geo` 顶层实测 74 个 `.py` 文件待提纯剥离；MUST 仅绑定 `127.0.0.1:18092`（本机实测空闲，部署到 NE1/mini 时需再验），launchd 常驻旁挂，plist 命名为 `com.xiulan.geo-worker-18092`，存放在小毛驴 `05_独立微服务集群/`；绝对禁止绑定 `0.0.0.0`，绝对禁止对外暴露端口，绝对禁止与 `:8091`（蜂群后厂）混用。`:8088` 现为 GEO 旧管理台与过渡期验证端口（NE1 与 mini 已实锤确认为同一台物理机 Mac mini M4，写死部署在 NE1 即 mini，严禁部署到 NE2）；现存 `scripts/run_geo_prod.sh` 第 7 行的 `GEO_BIND_HOST=0.0.0.0` 仅随旧管理台退役一并废止，不构成新绑定口径，新 Worker `:18092` 严禁绑定 `0.0.0.0`；`:8088` 退役仅针对旧管理台进程（`scripts/run_geo_prod.sh`）与 `deploy/nginx_geo.conf` 中指向 `127.0.0.1:8088` 的反代 `location`，不影响 NE1 作为编译中心与验证中心的定位；待小毛驴 GEO 工作台全量验收通过后，停止 `run_geo_prod.sh` 结束旧管理台服务，不保留双轨；退役后开发与测试验证统一改走小毛驴 `:3002`（前店）与同机旁挂 `:18092`（后厂 Worker）。端口登记唯一真相源是小毛驴根目录 `AGENTS.md` 第四节端口表。
5. **客户静态官网由 `mini` 本机 Nginx 直接挂载磁盘目录（写死口径）**：站点真源存放在 `mini` 本机磁盘目录 `projects/{id}/outputs/site/`；每个客户独立域名或二级域名经公网 `VPS` 反代回源、再经边缘 CDN 回源至 `VPS`，最终由 **`mini` 本机 Nginx** 的独立 `server_name` 块直接挂载该磁盘目录；公网 `VPS` 仅做反代回源，不挂业务代码、不直接挂载磁盘；静态访问完全不经过 Go 也不经过 Python。磁盘目录与对外 URL 必须成对写清，且映射来源写死（上一轮按 DeepSeek #67-1 / #67-2 收口）：客户独立域名的 Nginx 配置MUST 由小毛驴仓库 Go 工具命令 `cmd/gen_geo_nginx/main.go`（待建，本变更新建，实测不存在；上一轮按 DeepSeek #85-4 收口落点，本轮按 DeepSeek #92-5 收口实现语言）从小毛驴 MySQL 读取未删除的 **`geo_projects.domain`**（查询 MUST 显式带 `deleted_at IS NULL`，且 MUST 通过该 Go 工具复用 `pkg/constant` 常量（导入路径 `xxl-baicl-cc/pkg/constant`，引用前缀 MUST 写 `vioconstant.Xxx`，实测 `constant.go` 第 1 行为 `package vioconstant`，严禁写 `constant.Xxx`）与环境变量 `XIULAN_MYSQL_DATABASE` 建立 GORM 连接、以 GORM 模型查询完成，严禁 shell 裸拼 SQL，严禁硬编码数据库密码，严禁调用 `mysql` CLI 明文传密码）作为 `server_name`、未删除的 **`geo_projects.output_dir`** 作为 `root`（实测 `design.md` L73 已定义 `domain` 与 `output_dir` 两字段），绝对禁止手工写死域名或目录，绝对禁止 GEO 后厂连库生成；客户独立域名配置单独放在新建文件 `deploy/nginx_customer.conf`（本变更新建，待建，实测不存在），每个客户独立域名配置一个独立 `server_name` 块，不写入 `deploy/nginx_geo.conf`；**`geo.baicl.cc`** 只做 `/sites/{project_id}/` 多租户兼容路径（保留缺尾斜杠 301，见 §7 第 1 条），绝对不把 `nextgeo` 根路径 `/` 挂到 `geo.baicl.cc`（实测 `projects/nextgeo/outputs/site/index.html` 的 canonical 为 `https://www.baicl.cc/`）；**`nextgeo` 官网根路径 `/`** 由 **`www.baicl.cc`** 独立 `server_name` 块挂载，该块同样由数据库真源生成；两套 URL 绝对不得混写；该 `server_name` 块与小毛驴主站公网白名单网关（小毛驴 `AGENTS.md` 核心架构铁律 6）完全隔离，不走主站 `location /` 透传；后厂进程不承担任何站点流量。本变更的 Nginx 处置写死为：仅下线 `deploy/nginx_geo.conf` 中指向 `127.0.0.1:8088` 的反代 `location`，保留 `geo.baicl.cc` 域名并改为由 `mini` 本机 Nginx 直接挂载 `projects/{id}/outputs/site/` 静态目录；其他客户独立域名新建独立 `server_name` 配置块；实测现有 `deploy/nginx_geo.conf` 为一个 `server_name geo.baicl.cc` 块，内含两处生效的指向 `127.0.0.1:8088` 的反代 `location`，绝对禁止整块删除该文件导致 `geo.baicl.cc` 官网失联。注记：NE1 与 `mini` 已通过 `~/.ssh/config` 与节点备案实锤确认为同一台物理机（Mac mini M4，Tailscale `100.83.64.112`，主服务器），与算力机 NE2（`192.168.0.153`）严格区分，所谓 `mini` 本机 Nginx 就是 NE1 本机 Nginx，写死部署在 NE1（即 mini），严禁部署到 NE2。
6. **后厂落盘与时序硬约束**：后厂 Worker 只允许写入 `projects/{id}/outputs/`，绝对禁止写该目录之外的任何路径；迁移过渡前 `raw_materials/` 仅作临时中间产物，不得作真相源；迁移完成后后厂停写 `raw_materials/`，只写 `projects/{id}/outputs/`；存量 `raw_materials/ledger/facts.jsonl` 仅作只读磁盘历史素材保留（不再新增写入），`build_site` 所需新事实由 Go 后端在调用参数中显式传入（若未来持久化则另立变更建表）；新增或修改博文后必须执行 `datePublished` 倒序校验（`./scripts/sort_homepage_articles.py` 与 `python3 scripts/build_blog_index.py`），杜绝时序错乱；客户重资料的备份与恢复唯一入口是 `./scripts/sync_delivery_to_ziliao.sh` 与 `./scripts/restore_delivery_from_ziliao.sh`，绝对禁止手工拷贝或自建同步脚本。
7. **AI 开发动线**：日常 90% 的前端与后端开发在小毛驴单工作区完成；只有改爬虫规则、诊断算法、大模型采样脚本、静态模板生成时才进 GEO 仓。
8. **AI 协作门禁**：本仓任何涉及后厂接口形态、任务类型增删、端口变更的改动，必须先在本文件与小毛驴 `AGENTS.md` 同步登记，再写代码。

