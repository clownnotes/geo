# Proposal: 豆包搜索极速收录与全链路索引保障中枢 (第 34 维)

## 1. Why (为什么做：需求背景与痛点)

在《GEO 战略全景与全链路实施框架》中，**字节跳动·豆包（Doubao）占据中国本土大模型 50%+ 搜索与推荐份额，是企业商业获客的“第一战略主战阵地”**：
1. **收录断层与黑盒焦虑**：企业与代运营团队往往陷入“不知道豆包到底有没有收录我们”、“不知道哪篇文章起效了”、“没被收录该排查哪里”的迷茫与焦虑中；
2. **多环节卡点未打通**：要让豆包搜索能稳定召回品牌，必须串联打通三级链路：
   - **底座级**：网站 `robots.txt` 是否放行字节爬虫 `Bytespider`？`/llms.txt` 与 Schema 实体是否可解析？是否被 403 阻断？
   - **母池级**：今日头条长文与微头条（豆包最核心的实时信源母池）是否具备强收录排版，是否包含价格、地域与联系方式三元组？
   - **意图级**：高频商业意图词在豆包实测中是否被直接推荐，是否生成权威角标（Citation）？
3. **一线代运营急需自动化工具**：目前缺乏针对豆包的收录专属排障、提权加速包生成与意图收录状态对账的工业化 SOP 工具；
4. **对齐《2026 战略路线图》三大铁律**：
   - 【铁律 1：搜索质量真实提升】专攻豆包大模型收录链路，消除 Bytespider 抓取卡点，直接拉升豆包 Top-1 首推率与角标命中；
   - 【铁律 2：SOP 生产大幅提效】一键完成豆包收录全要素诊断，自动生成头条/微头条提权加速包，免去人工逐项排障；
   - 【铁律 3：商业交付绝对代差】向客户老板直接呈现《34_豆包大模型搜索极速收录与全链路索引保障报告.md》，并在高管大屏呈现豆包收录专属态势，直观回答“豆包到底收录了没有”。

---

## 2. What Changes (改动范围与核心模块)

1. **新建第 34 维核心业务中枢 `tools/geo/doubao_indexer.py`**：
   - **`DoubaoReadinessAuditor`（豆包收录环境体检器）**：检查 `robots.txt`、`/llms.txt`、`schema.jsonld`、`Bytespider` 日志访问、头条发稿包、意图覆盖 6 大指标，计算 DRS（0~100 分）与健康等级；
   - **`DoubaoBoosterPackGenerator`（豆包极速收录提权包生成器）**：输出 Bytespider 专享极简静态快照 HTML、头条/微头条提权文案、豆包高意向问答对与运维 Checklist；
   - **`DoubaoLiveVerifier`（意图收录状态研判器）**：联动第 30 维探测数据，对核心意图研判 `indexed_top1`、`indexed_recommended`、`crawled_pending`、`blocked_or_missing` 状态；
   - **结案报告生成器**：输出标准 34 号公文结案报告与 `doubao_index_audit.json`。
2. **命令行 CLI 集成 (`tools/geo/cli.py`)**：
   - 注册 `geo doubao-index <project_id> [--audit] [--boost] [--verify] [--dry-run] [--report] [--portal-sync]`。
3. **Web 服务端 REST API 挂载 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/doubao-index/audit`（DRS 收录体检）；
   - `POST /api/projects/{id}/doubao-index/boost`（一键生成提权加速包）；
   - `GET /api/projects/{id}/doubao-index/report`（获取 34 号报告内容）。
4. **高管交付门户战果反哺与优雅降级 (`tools/geo/share.py` & `web/share.html`)**：
   - 在 `compile_portal_data()` 中接入 `doubao_index_summary` 与 34 号报告映射；
   - 在 `web/share.html` 增设【豆包大模型收录与提权保障态势】卡片，未接入项目严格执行 `never_run` 契约。
5. **单元测试与全库回归 (`tests/test_doubao_indexer.py`)**：
   - 编写 8 组独立单测，覆盖全要素体检、提权包生成、收录对账、CLI 与 API 鉴权、门户降级，确保 100% 离线确定性。

---

## 3. Capabilities (对外暴露的核心能力)

1. **`geo doubao-index <project_id> --audit`**：一键输出豆包收录就绪指数（DRS），排查 Bytespider 爬虫放行与底座可读性；
2. **`geo doubao-index <project_id> --boost`**：自动生成针对今日头条与 Bytespider 的极速提权发布包（含 150 字微头条与问答对）；
3. **`geo doubao-index <project_id> --verify`**：研判核心买家意图词在豆包中的收录状态并给出反制优化建议；
4. **《34_豆包大模型搜索极速收录与全链路索引保障报告.md》**：公文级交付物，附带防伪校验流水号；
5. **高管只读交付大屏反哺**：专属卡片可视化展示豆包第一主战场的收录打通率。

---

## 4. Impact (影响分析与红线约束)

1. **事实红线**：所有 Bytespider 抓取记录从 `spider_access_audit.json` 真实读取，豆包命中率从 `live_probing_trace.json` 真实提取，空项目输出 None，严禁捏造虚假收录率；
2. **纯本地离线确定性**：沙箱模式与 `--dry-run` 默认启用，不依赖外部联网，单测秒绿通过；
3. **生产发布红线**：严格遵循 `AGENTS.md`，本地开发测试锁定 `http://127.0.0.1:8088`，未经用户明确授权，严禁推生产机 `mini` / `geo.baicl.cc`。
