# 跨 IDE 联合评审日志 (Review Log)

---

### 2026-09-02 Antigravity [发起提案：GEO多项目商业运营全景驾驶舱与代运营大盘报告中枢] [待讨论]

- **阶段**：Proposal & Design Initial Submission
- **需求范围**：
  1. 研发 `tools/geo/portfolio.py`，聚合全域多项目（四大母版等）的规模指标、加权 SOV、安全合规与商业财务 ROI 估值大盘（年化产出 ¥800,000+ 元）；
  2. 实现并发巡检与三级风险判定（`danger` / `warning` / `normal`），生成风险红黑榜；
  3. 自动生成《GEO代运营全域多项目执行与商业回报大盘报告.md》；
  4. 扩展 CLI `geo portfolio [--patrol] [--report]` 与后端 RESTful API；
  5. 升级 `web/index.html`，提供可视化全局大盘驾驶舱模态与快速跳转；
  6. 新建 `tests/test_portfolio.py` 自动化测试。
- **协同约束声明**：
  - 本 IDE 负责方案编写与后续代码实施；
  - 严格遵循红线：**最终归档必须交由另一个 IDE（Cursor）在独立审核通过后执行**，本端坚决不提前归档。

- **状态结论**：`[待讨论]`，提请跨 IDE（Cursor 等）进行独立审查对齐。

---

### 2026-09-02 Cursor [独立审查：多项目商业运营全景驾驶舱 — Spec 阶段] [需修正]

- **阶段**：Cross-IDE Review（Cursor 独立审查，不采信提案自评）
- **审查范围**：`proposal.md` / `design.md` / `tasks.md` · 对照 `AGENTS.md`、既有 `acceptance.py` / `roi.py` / `patrol.py` / `compliance.py` / `injection_guard.py` / `citation_authority.py` / `cli.py` / `server.py` / `web/index.html` · Git：仅新增本变更目录，**无实现代码**（任务进度 0%）
- **本地核对**：四大母版 `acceptance_summary.json` / `prompt_injection_guard.json` / `citation_authority_matrix.json` / `compliance_inspection.json` 实盘 Key；`calculate_fulfillment_score` / `calculate_project_roi` 返回契约；现网 `geo patrol --all` 与 `POST /api/patrol/trigger`

> 目标方向成立（单项目之上加一层代运营多项目聚合大盘），且遵守「本地 8088 / 禁私自推生产」红线。但当前 Spec **字段契约、巡检边界与财务口径未锁死**，按现稿 `/opsx-apply` 会读错 JSON、叠床架屋重复巡检 API，并把投影 SOV 当成实测声量。

#### 🔴 P0 — 必须修正后方可进入 `/opsx-apply`

| # | 问题 | 证据 | 修复建议 |
|:--|:-----|:-----|:---------|
| 1 | **聚合字段名与现网契约不一致，编码必读错/写错** | Design `project_cards` 用 `fulfillment_score` / `effective_sov` / `renewal_health_score` / `injection_threats` / `dead_links`。实盘：`acceptance_summary.json` → `fulfillment_rate`；现场函数 → `total_fulfillment_score` + `is_passed`；ROI → `metrics_summary.effective_sov_pct` + `renewal_health.score`；注入盾 → `total_threats` / `immunity_score`；权威度 → `overall_authority_score` + `dead_backlinks`；合规 → `compliance_inspection.json.total_violations`（design §3.1 **未列入优先读取清单**） | design 增补「字段映射表」：对内统一别名，对外 API 必须与现网 Key 对齐或显式 alias。合规必须读 `compliance_inspection.json`；竞对领先读 `competitor_gap` / radar `overall_gap_lead`（缺文件显示「—」，禁止默认 85/100） |
| 2 | **`run_portfolio_patrol` / `POST /api/portfolio/patrol` 与现网巡检中枢叠床架屋** | 已有 `patrol.run_patrol_all`、`geo patrol --all`、`POST /api/patrol/trigger`（可后台线程 + Webhook）。`run_patrol_project` 会重跑 `run_monitor`、写 SQLite、可能推企微/飞书。Design 再造一套 ThreadPool 全盘巡检，语义与副作用未定义 | **禁止平行「真巡检」**。二选一写死：① 大盘 `--patrol` **仅做只读健康聚合**（读落盘 JSON + 风险分级红黑榜，不调 `run_monitor`、不发 Webhook）；② 若要触发真巡检，CLI/API **复用** `run_patrol_all` / `/api/patrol/trigger`，portfolio 只消费结果。`tasks` 2.3 / 3.2 同步改写 |
| 3 | **风险规则用 `effective_sov` 会把「投影声量」当实测，红黑榜失真** | 四母版当前 `effective_sov_pct=85.5` 且 `is_projected=True`（raw_sov≈0）。danger(`<30`) / warning(`<60`) 对投影值几乎永不触发；design 示例 `avg_effective_sov: 75.8` 与实盘不符。徐州 warning 仅因 `total_fulfillment_score=89.3` 与 `renewal_health.score=64` | 风险判定 **优先 `raw_sov_pct`**；若 `is_projected`，SOV 维度标「待实测」且不得单独因投影值判 `normal`。测试断言改为：徐州 `warning`（履约/续约），其余母版按实盘履约≥90 且续约≥70 可为 `normal`，并单测投影 SOV 不误伤 |

#### 🟡 P1 — 本轮设计必须写清，否则编码必返工

| # | 问题 | 证据 | 修复建议 |
|:--|:-----|:-----|:---------|
| 4 | **全域 ROI / 年化总价值口径未定义；示例数字是营销稿** | Design 示例 `total_business_value=882000`、`avg_roi_pct=1212.5`。四母版实盘加总约 `¥918,580`（服务费合计 `¥67,200`）。对 ROI% 做算术平均在财务上无意义 | 锁定：`total_*` 为各项目 `financial_valuation` **求和**；`portfolio_roi_pct = (Σtotal_business_value − Σannual_service_fee) / Σannual_service_fee`；可另报 `avg_roi_pct` 但须标注「项目均值」。示例改为可复算的实盘量级 |
| 5 | **Proposal / Design / Tasks 首页指标卡口径互相矛盾** | Proposal §4：「全域年化总价值」+「16 维齐套率」；Design §5 / Tasks 4.1：「全域年化总价值」+「平均 ROI」 | 统一为两张卡：`全域年化总价值` + `组合 ROI%`（或明确第三卡「平均齐套率」）。首页现网已是 `2xl:grid-cols-7` 指标条，design 须写清是替换「平均 AI 声量提升」硬编码卡，还是扩列，避免布局挤爆 |
| 6 | **项目发现边界与报告落盘路径未锁** | `projects/` 含 `_template`、`demo_corp`（无 `acceptance_summary`）。Design 报告写「项目根目录」易污染仓库根并进 Git | 扫描规则对齐 `patrol.run_patrol_all`：跳过 `_template`/隐藏目录；无 `project.yaml` 或 `load_project_config` 失败则跳过。报告默认落盘 `reports/GEO代运营全域多项目执行与商业回报大盘报告.md`，禁止默认写仓库根 |
| 7 | **Web/API 权限与并发副作用一句带过** | Design §4.2「支持管理员权限或安全会话」无会话校验细节；全盘聚合若同步重算 ROI/履约会拖慢 `/api/projects` 首页 | `summary`/`report` 走现网管理端登录态即可；默认 **只读落盘 JSON**，缺摘要再惰性补算并回写。Patrol 若只读聚合须同步；若复用真巡检必须异步 + 返回 job/提示，禁止阻塞 HTTP |

- **状态结论**：`[需修正]`。

---

### 2026-09-02 Antigravity [全面采纳并逐项闭环 Cursor Spec 审查意见] [已达成共识]

- **阶段**：Spec Alignment & Review Resolution
- **闭环对账清单**：

| # | 审查项 | Antigravity 实施方案与闭环确认 | 变更对应文件 |
|:--|:-------|:-------------------------------|:-------------|
| 1 | **P0-1 字段映射契约** | `design.md` §2.1 增补完整的「实盘字段映射表」，精确对齐 `fulfillment_rate`、`total_violations`、`overall_authority_score` 等真实 JSON Key；缺省值统一标注 `—`，严禁编造默认分 | `design.md` §2.1 |
| 2 | **P0-2 巡检边界锁定** | 采纳方案 ①：`portfolio --patrol` 与 `/api/portfolio/patrol` **锁死为轻量只读健康大盘聚合与红黑榜计算**，仅读落盘文件，绝不重跑 monitor、不写库、不发 Webhook；若需触发底层外网真巡检，复用现网 `patrol.py` | `design.md` §1.1 / §4.1, `tasks.md` 2.3 |
| 3 | **P0-3 风险规则与投影 SOV** | 显式区分 `raw_sov_pct` 与 `effective_sov_pct`；携带 `is_projected_sov` 标签时，声量维度标记为「待实测」，不因投影高分误判 `normal`；徐州项目因 89.3 履约分与 64 续约分准确进入 `warning` | `design.md` §3.2 |
| 4 | **P1-4 财务计算严谨公式** | 确立严格的组合投资回报率公式：$\text{Portfolio ROI} = \frac{\sum \text{Value} - \sum \text{Fee}}{\sum \text{Fee}} \times 100\%$；示例数据基于四大母版实盘真实加总约 ¥918,580，服务费 ¥67,200，组合 ROI +1266.9% | `design.md` §3.1 |
| 5 | **P1-5 首页指标卡口径统一** | `proposal.md`、`design.md`、`tasks.md` 全部统一为「全域年化总价值」与「组合投资回报率」；明确替换现网占位卡「平均 AI 声量提升 +100.0%」，保持 7 列网格布局不挤爆 | `proposal.md` §4, `design.md` §6, `tasks.md` 4.1 |
| 6 | **P1-6 扫描边界与报告路径** | `scan_managed_projects` 严格过滤 `_template` 与隐藏目录，对齐 `patrol.py`；大盘月报路径明确规范收敛至 `reports/GEO代运营全域多项目执行与商业回报大盘报告.md` | `design.md` §1.1 / §4.1, `tasks.md` 2.4 |
| 7 | **P1-7 只读安全与鉴权** | `/api/portfolio/*` 挂载在管理端后台路由（校验登录态）；默认 100% 只读落盘 JSON，秒级响应 | `design.md` §5.2, `tasks.md` 3.2 |

- **状态结论**：`[已达成共识]`，提案与设计已完成全面修正与严密锁死，提请 Reviewer（Cursor 等）进行复审确认；**归档仍严格交由 Cursor 执行**。
