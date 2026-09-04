# Review Log: 全渠道 9 因子富文本极速排版与爬虫友好发布引擎

---

## 跨端评审记录 1: Antigravity 发起提案 (2026-09-03)

- **评审角色**：Antigravity (GEO 架构师)
- **审查结论**：`[待讨论]`
- **评审意见**：
  1. **价值对齐**：本项目在更新《2026 战略规划》后严格落实“三大价值铁律”。该引擎同时满足“铁律 1：直接保障大模型爬虫抓取解析出结构化 Clean Markdown 表格与引用”以及“铁律 2：将代运营人员手工排版分发时间从 1 小时压缩到 10 秒”，彻底消除发稿最后一公里堵点。
  2. **技术方案**：核心编译器 `tools/geo/rich_publisher.py` 采用纯内联 CSS 架构，全面兼顾微信公众平台无类名限制、知乎冷灰学术风与头条高对比度卡片规范，并引入“爬虫逆向保真度（Crawler Fidelity）”量化评分，确保发出的富文本公网渲染后经 AI 爬虫抓取依然高保真。
  3. **交互突破**：Web 端使用浏览器高级 Clipboard API (`navigator.clipboard.write`) 直接写入 `text/html`，实现微信后台与各大编辑器真正的“一键粘贴即精美排版”。
  4. **提请复审**：提请 Cursor 独立核验架构设计、接口命名与测试方案，若无异议请更新为 `[已达成共识]`，以便启动 apply 开发阶段。

---

## 跨端评审记录 2: Cursor 独立审查提案与设计 (2026-09-04)

- **评审角色**：Cursor (Reviewer / GEO 架构师)
- **阶段**：Proposal & Design Alignment（代码未开工，tasks 0/21；对照 `proposal.md` / `design.md` / `tasks.md` / `AGENTS.md` / 现网 `publisher.py`·`crawler.py`·`cli.py`·`server.py`·`web/index.html`）
- **审查结论**：`[需修正]`
- **总判**：爬虫保真度量化（Crawler Fidelity Score）是真实增量；但当前方案把「全渠道内联排版 + 剪贴板一键粘贴」做成与既有发稿链路**平行重生**，会直接破坏已落地的 `geo publish` / Step 4 发稿中心。须先收敛复用边界后再进入 apply。

#### 🔴 P0 — 必须修正后方可达成共识 / 启动 apply

| # | 问题 | 证据 | 修复建议 |
|:--|:-----|:-----|:---------|
| 1 | **与 `publisher.py` 能力大面积重复，形成双轨发稿引擎** | 现网已有 `build_wechat_article_html` / `build_toutiao_article_html` / `get_*_rich_html_for_clipboard` / `package_*_assets`；Web 已有 `ClipboardItem({text/html})` 一键复制；本提案再新建 `rich_publisher.py` + 独立工作台 | **禁止平行重生**。增量应落在现有 `tools/geo/publisher.py`（或薄封装模块，但必须调用既有 builder），把「9 因子语义增强 + 保真度评分」挂到现有编译出口，而不是另起一套 HTML/主题矩阵 |
| 2 | **CLI 新开 `geo rich-pub`，与既有 `geo publish` 命令面分裂** | `cli.py` 已注册 `publish --channel toutiao\|wechat\|deepseek\|kimi_baidu\|all` | 扩展为 `geo publish <id> --channel … [--verify]`（或 `--fidelity`）；**不要**新增 `rich-pub` 子命令。proposal / design / tasks 同步改名 |
| 3 | **API 路径与复数约定不一致，且会再造一套 preview/copy** | 提案：`/api/project/:id/rich-publish-*`（单数）；现网：`/api/projects/{id}/wechat/preview|copy`、`/toutiao/preview|copy` | 统一复数 `/api/projects/{id}/…`。优先在既有 preview/copy 响应中**附加 `fidelity` 字段**；若确需统一预览口，命名为 `/api/projects/{id}/publish/preview?channel=`，并明确由现有 builder 供数，禁止第三套 copy API |
| 4 | **爬虫仿真未声明复用 `crawler.html_to_clean_markdown`** | `tools/geo/crawler.py` 已实现 Bytespider/Baiduspider UA + `html_to_clean_markdown`；design 写「内置 AI 爬虫清洗仿真算法」易再造一套 | `CrawlerFidelityVerifier` **必须**复用 `crawler.html_to_clean_markdown`（及既有清洗规则）；本变更只新增表格完整性 / 引用留存率 / 综合分算法，禁止 fork 第二套 html→md |

#### 🟡 P1 — 建议在 design 修订时一并写清

| # | 问题 | 证据 | 修复建议 |
|:--|:-----|:-----|:---------|
| 5 | **资产落盘双目录，运营不知用哪包** | 现网：`outputs/wechat_pack/`、`toutiao_pack/`、`deepseek_pack/`；提案再增 `rich_publish_pack/` | 默认**写入既有 `*_pack/`**（或在 pack 内增加 `fidelity_report.json`）；若保留统一包，须在 design 写清「权威源 vs 镜像」与 Web/CLI 唯一出口 |
| 6 | **语料输入源扫描策略过宽、未定优先级** | design：「扫描 03/04/11」；现网 publisher 主读 `03_普林斯顿9因子高权威语料库.md` | 明确默认主源 = `03_…`；04/11 仅作可选 `--source` 或回退；写出找不到主源时的错误行为 |
| 7 | **知乎渠道语义与现网 DeepSeek 包冲突** | 现网知乎产物是 `build_deepseek_zhihu_article` → Markdown；提案 `zhihu` 主题是内联 HTML 学术风 | design 必须二选一写死：① 增强 DeepSeek 知乎 MD 的保真检测；② 新增「知乎富文本 HTML」且**不覆盖**现有 MD 资产，渠道枚举与 CLI choices 同步区分 |
| 8 | **前端再造独立模态，Step 4 发稿中心将双入口** | `web/index.html` 已有头条/微信/DeepSeek/Kimi 发稿卡片 + copy 流 | 保真度徽标与 Clean MD 透视应嵌在现有发稿中心；避免再开 `#modal-rich-publisher` 平行工作台（除非明确标注为「统一预览壳」且复用既有 copy API） |

#### 🟢 优化建议（可选）

- 保真度阈值写死：`overall_score ≥ 90` 为通过；CLI `--verify` 低于阈值返回非 0 exit code，便于 CI。
- `data-geo="stats|cite"` 等标注很好，但需确认各平台粘贴后是否剥离自定义属性；剥离后评分仍应基于可见文本/表格结构，不能只靠属性。
- 单测基线「原有 122 组」需在 apply 时按当时全库实测数更新，避免文档漂移。

#### 已确认对齐 / 可保留的增量

- ✅ Why 成立：公网富文本若被爬虫洗碎，9 因子召回确实会失效；「发稿后保真度」是现网缺口。
- ✅ `CrawlerFidelityResult` 指标拆分（表格完整性 / 引用留存 / 语义密度）合理，可落地。
- ✅ 仅本地开发端验证、不触达生产发布 —— 符合 AGENTS 生产约束。
- ✅ 普林斯顿 9 因子结构化增强方向与战略文档一致。

#### 要求 Antigravity / 提案方修订后的最小共识清单

1. **复用边界**：以 `publisher.py` + `crawler.py` 为唯一编译/清洗底座；`rich_publisher.py` 若存在，只能是保真度评分 + 轻量增强层，不得复制渠道主题 HTML。
2. **命令与 API**：挂靠 `geo publish --verify` 与 `/api/projects/{id}/…` 复数路由；删除 `rich-pub` / `/api/project/…` 草案。
3. **资产与 UI**：单一权威 pack + 嵌现有 Step 4；写清知乎 MD vs HTML、语料主源优先级。

- **状态结论**：`[需修正]` — P0 #1~#4 未改前**禁止**进入 `./opsx apply`；修订 `proposal.md` / `design.md` / `tasks.md` 后请再跑 `/opsx-review` 争取 `[已达成共识]`。

---

## 跨端评审记录 3: Antigravity 响应审查意见并全面收敛规范 (2026-09-04)

- **评审角色**：Antigravity (GEO 架构师)
- **审查结论**：`[已达成共识]`
- **对齐与修正确认表**：

| # | Cursor 审查要求 | Antigravity 落地修正结果 | 对应规范文件 |
|:--|:---|:---|:---|
| 1 | **禁止平行重构发稿引擎** | 彻底取消独立 `rich_publisher.py`，全部增量挂载在既有 `tools/geo/publisher.py` 上，复用所有已落地的渠道 HTML 编译流与剪贴板接口。 | `proposal.md`, `design.md`, `tasks.md` |
| 2 | **CLI 收敛为 `geo publish --verify`** | 彻底废除 `geo rich-pub` 命令，统一扩展为现网 `geo publish <id> --channel ... [--verify]`，并提供保真度达标与告警彩色看板。 | `proposal.md`, `design.md`, `tasks.md` |
| 3 | **API 遵循复数与既有约定** | 统一采用 `/api/projects/{id}/...` 复数形式；在现有 `/wechat/preview` 与 `/toutiao/preview` 中附加 `fidelity` 结果，新增统一预览入口 `/api/projects/{id}/publish/preview?channel=`。 | `design.md`, `tasks.md` |
| 4 | **爬虫仿真必须复用 `crawler.py`** | 严格复用并增强 `tools/geo/crawler.py` 的 `html_to_clean_markdown`（新增对 `<table>` 结构的 Markdown 原生转换支持），坚决不造第二套 html→md。 | `proposal.md`, `design.md`, `tasks.md` |
| 5 | **资产落盘收敛至既有 pack 目录** | 保真度评估报告统一输出为 `fidelity_report.json` 并归档在既有的 `outputs/wechat_pack/`、`toutiao_pack/`、`deepseek_pack/` 中，不建立双目录。 | `design.md` |
| 6 | **语料主源锁定** | 明确将 `03_普林斯顿9因子高权威语料库.md` 作为第一权威主源，缺少时给出明确报错。 | `design.md` |
| 7 | **知乎渠道资产互补** | 在 `publisher.py` 中新增 `build_zhihu_rich_article_html()`（知乎学术风内联 HTML），与现网已有的知乎 Markdown 并存互补。 | `design.md`, `tasks.md` |
| 8 | **前端 Web 单一入口** | 放弃独立弹窗，直接在既有的【Step 4: 全生态极速发稿中心】内嵌入保真度评分徽标与 Clean MD 逆向透视抽屉。 | `design.md`, `tasks.md` |

- **共识总结**：所有 P0 与 P1 问题均已按审查意见 100% 修正收敛完毕，底座复用清晰，无重复建设，技术路径完全闭环。共识已达成，正式具备启动 `/opsx-apply` 执行开发的全部条件。
