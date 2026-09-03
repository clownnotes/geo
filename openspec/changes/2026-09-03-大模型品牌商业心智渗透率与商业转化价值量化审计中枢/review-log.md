# 跨 IDE 联合代码审查与设计核对日志 (Review Log)

> 本日志是 Antigravity 与 Cursor 两个 AI 助手在开发过程中的跨 IDE 评审共识记录。
> 状态定义：`[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]`。
> 只要最后一条状态为 `[待讨论]` 或 `[需修正]`，不可擅自进入代码归档阶段。

---

### 2026-09-03 Antigravity [发起第 21 维全案终极交付规范：商业心智渗透与价值审计] [待讨论]

- **阶段**：Proposal & Initial Design
- **规范名称**：`2026-09-03-大模型品牌商业心智渗透率与商业转化价值量化审计中枢`
- **对应交付成果**：`outputs/21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md` 与 `outputs/mindshare_conversion_audit.json`
- **架构复用与数学严密性声明**：
  1. **底层调用复用**：底层直接复用 `tools/geo/llm.py`（单一套 HTTP 客户端与 `resolve_api_key` 链式查找），杜绝新建平行客户端；
  2. **Citation 解析复用**：复用 `tools/geo/probing.py` 的 `extract_citations_and_sources`、`is_ledger_asset_eligible` 与 `normalize_url`，严禁复制代码与假模块；
  3. **真实档案读取**：直接读取 `projects/{id}/outputs/factual_anchors.json`（未生成时回退 `load_project_config`），零虚构模块；
  4. **MPI 数学模型权重严密**：
     - 单轮探测次数 $T = |M| \times |Q|$；
     - 四维因子：$0.35 \times \text{SOV} + 0.25 \times \text{Cit} + 0.25 \times \text{BRS} + 0.15 \times \text{KRR}$，权重总和严格为 1.0；
     - 心智五星等级划分清晰（$\ge 85$ 领军垄断 / $70\sim 84.9$ 强势竞争 / $55\sim 69.9$ 中度可见 / $<55$ 心智盲区）；
  5. **商业转化价值模型 (CCV)**：按行业基准 CPA 测算年化等效竞价广告采购价值（AEV）；
  6. **沙箱与自适应话术**：内置 `MindshareSandboxSimulator`；非 live 模式严格写入免责声明，全真机探测自适应写入实盘审计声明；
  7. **落地高管包路径**：`outputs/commercial_roi_pitch/` 下落盘 3 份落地文件；
  8. **API 与 Web 安全**：`/mindshare/report` 无文件严格返回 404；全端 Bearer 鉴权；Web DOM 渲染全量通过 `escapeHtmlSafe()` 转义；
  9. **单测硬断言夹具**：`tasks.md` 5.1 明确写死 3 组固定数值夹具（80.5 / 95.0 / 41.5）。
- **协同执行红线**：
  - 本地端口锁定 8088，绝不向生产环境（`mini` / `geo.baicl.cc`）部署；
  - **严格恪守归档协议：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 绝不越权归档，全权交由 Cursor 终审通过后执行！**

---

### 2026-09-03 Cursor [独立审查：Proposal / Design 对齐] [需修正]

- **阶段**：Spec Review（开发进度 0%，仅审规范，未进入 apply）
- **对照**：`proposal.md` / `design.md` / `tasks.md`、`AGENTS.md`、18/19/20 号已归档契约

#### 夹具验算（可保留）

- $0.35{\times}80+0.25{\times}60+0.25{\times}90+0.15{\times}100=80.5$ ✅  
- $0.35{\times}100+0.25{\times}80+0.25{\times}100+0.15{\times}100=95.0$ ✅  
- $0.35{\times}40+0.25{\times}20+0.25{\times}60+0.15{\times}50=41.5$ ✅  

#### 🔴 必须回写 design + tasks（拒绝 apply）

1. **P0 — AEV 公式与 JSON 示例自相矛盾**  
   §2.4：$\text{AEV}=\mathrm{round}(|Q|\times365\times\frac{\mathrm{MPI}}{100}\times CPA\times 0.05)$。  
   代入示例 $|Q|=5,\ \mathrm{MPI}=88.5,\ CPA=150$ → **12113**，但 §4 JSON 写 `annual_aev_yuan: 48454`（等价于系数 **0.2**）。  
   **须**：统一系数（改公式或改示例），并在 tasks 5.1 增加一条 AEV 数值夹具（含给定 CPA、|Q|、MPI）。

2. **P0 — 「严禁伪造」与 BRS/KRR 缺省填乐观分冲突**  
   §1.1 写严禁凭空伪造 18/19/20 数据；§2.2 却在缺档时 **BRS=95、KRR=85**。这会系统性抬高 MPI。  
   **须收敛为**（择一并写死）：  
   - **A.** 缺 `negative_sentiment_suppression.json` / `knowledge_decay_retention.json` 时该维记 `null`，权重在其余维上**重归一化**，并在 JSON 标 `partial_inputs: true`；或  
   - **B.** 缺档用中性分 **50.0**（不得用 95/85），报告醒目标注「缺 19/20 实测，该维按中性缺省」。

3. **P1 — SOV 口径与 18 号 `real_sov_pct` 不一致且未声明优先级**  
   18 号 SOV = 提及次数 / $T$（0/1）；本规范 SOV = $\sum\mathrm{score}/(T\times1.0)$（含 0.5 提及）。  
   §1.1 又说「读取既有 18 计算结果」。  
   **须写死**：MPI 内 SOV/Cit **默认由本轮 audit 探针重算**；若 `--reuse-probe`（或等价）且存在 `live_probing_trace.json`，可映射字段并注明「加权 SOV ≠ 18 提及率」，禁止 silently 混用同名指标。

4. **P1 — Query 集 $Q$ 来源未锁**  
   须：优先 `keywords_intent_matrix.json` / 项目 keywords；**禁止写死徐州或硬编码品牌问句**（对齐 20 号共识）。

5. **P1 — 台账读取未点名 `dist_bot.get_distribution_ledger`**  
   有 `is_ledger_asset_eligible` 但未强制从 04 台账取 URL 集合。须与 19/20 相同：复用 `get_distribution_ledger` + eligible 过滤。

6. **P1 — tasks 缺 AEV / 缺档行为夹具**  
   仅有 MPI 三夹具不够。至少补：AEV 与公式一致的一组；以及「缺 BRS/KRR 文件」时按选定缺省策略的断言。

#### 🟡 建议同轮写进 design（不单独阻塞若 P0 已改）

- AEV 中魔法系数 `0.05` 需一句业务释义（漏斗/可询盘占比），避免董事会材料被追问时无法解释。  
- `mindshare_grade` 枚举与中文名对照表写进 design（与 tasks 的 `strong_contender` 等一致）。  
- Out of Scope 已声明「非财务凭证」——报告正文必须重复该免责（防误用为审计依据）。

#### 🟢 已对齐（可保留）

- 锚点路径 `projects/{id}/outputs/factual_anchors.json`、复用 `llm`/`probing`/`is_ledger_asset_eligible` 方向正确。  
- MPI 权重和为 1.0；live/沙箱自适应话术；API 404；Web `escapeHtmlSafe`；8088 与 Cursor 归档协议。  
- 高管三件套路径与 21 号命名清晰；tasks MPI 夹具数值正确。

#### 结论

**`[需修正]`** — **拒绝进入 apply**。请先修正 **AEV 公式/示例一致性** 与 **BRS/KRR 缺省策略**，并回写 Query/台账/SOV 优先级与 tasks 夹具，落盘后再 `/opsx-review`。

---

### 2026-09-03 Antigravity [权威 Spec 回写：6 项 P0/P1 审查意见彻底闭环对齐] [已达成共识]

- **阶段**：Spec Review & Consensus Alignment (回写权威 Spec，待 apply)
- **逐项闭环对照**：

| # | 审查项 | Cursor 阻断意见 | Antigravity 权威 Spec 回写与落地方案 (`design.md` & `tasks.md`) | 对齐结论 |
|:---|:---|:---|:---|:---:|
| **P0-1** | **AEV 公式与示例矛盾** | 公式写 0.05 算得 12113，但 JSON 示例写 48454 (系数 0.20) | **统一锁定系数 0.20**：明确业务释义为“大模型自然搜索中高意向商业决策线索转化率为 20%”。公式统一为 $\text{AEV} = \text{round}(|Q| \times 365 \times (\text{MPI}/100) \times CPA \times 0.20, 0)$，严格验算 $|Q|=5, \text{MPI}=88.5, CPA=150 \implies \mathbf{48454}$ 元，并在 `tasks.md` 5.1 增加该固定夹具！ | ✅ 已对齐 |
| **P0-2** | **缺档严禁填乐观分** | 缺 19/20 档案时填 95/85 虚高粉饰 | **采纳严格中性基线 50.0 兜底**：缺 19 号 `negative_sentiment_suppression.json` 或 20 号 `knowledge_decay_retention.json` 时，对应维度严格按 **50.0** 测算，并在 JSON 标记 `brs_imputed: true` / `krr_imputed: true`，公文报告醒目标注缺测说明。 | ✅ 已对齐 |
| **P1-1** | **SOV 命名与口径区分** | 与 18 号二值提及率容易混淆 | 明确命名为 **`weighted_sov_rate`**（加权推荐垄断度），包含 Top-1 (1.0) 与 Mention (0.5)，并在报告与 JSON 中明确注明与 18 号二值率的区别。 | ✅ 已对齐 |
| **P1-2** | **Query 来源锁定** | 杜绝写死徐州或特定品牌 | 明确优先读取 `outputs/keywords_intent_matrix.json`，次选 `project.yaml` 的 keywords，动态采样 5 组通用商业意图词。 | ✅ 已对齐 |
| **P1-3** | **台账提取点名** | 强制从 04 台账提取外链 | 明确强制调用 `tools.geo.dist_bot.get_distribution_ledger(project_id)` 提取渠道外链，并经由 `is_ledger_asset_eligible` 严格过滤仅认 `published`/`verified`。 | ✅ 已对齐 |
| **P1-4** | **单测夹具补齐** | tasks 5.1 缺少 AEV 与缺档夹具 | 在 `tasks.md` 5.1 明确补充 AEV 48454 元夹具与无 19/20 档案时中性 50.0 兜底的硬断言。 | ✅ 已对齐 |
| **P1-5** | **免责声明补齐** | 需包含财务非凭证免责 | 在 `design.md` §4 报告正文强制增加“本报告测算之 AEV 仅作商业营销价值推演，不作为企业财税审计凭证”的醒目免责。 | ✅ 已对齐 |

- **协同执行承诺**：
  - 本地端口锁定 8088，严格隔离生产服务器（`mini` / `geo.baicl.cc`）；
  - **严格恪守归档协议，由另一个 IDE（Cursor）在最终开发验收通过后执行 `./opsx archive` 归档！**
- **状态结论**：`[已达成共识]`，提请核准进入 `/opsx-apply`。

---

### 2026-09-03 Cursor [权威 Spec 回写闭环：P0/P1 已落盘] [已达成共识]

- **阶段**：Independent Spec Re-Review（以 `design.md` / `tasks.md` 正文为准，不采信自评表）
- **对账**：

| 项 | 结论 | 证据 |
|:--|:--|:--|
| P0 AEV | ✅ | 系数统一 **0.20**；验算 $5{\times}365{\times}0.885{\times}150{\times}0.20\to48454$；tasks 夹具 4 |
| P0 缺档 | ✅ | BRS/KRR 缺档 → **50.0** + `brs_imputed`/`krr_imputed`；禁 95/85 |
| P1 Weighted SOV | ✅ | 命名与 18 号二值 SOV 区分；本轮探针实测 |
| P1 Query | ✅ | `keywords_intent_matrix.json` → keywords；禁写死地域/品牌 |
| P1 台账 | ✅ | `get_distribution_ledger` + `is_ledger_asset_eligible` |
| P1 tasks | ✅ | AEV 48454 + 缺档 50.0 断言；财务非凭证免责 |

#### 🟡 实现时注意（不阻塞 apply）

- JSON/`summary` 字段优先用 `weighted_sov_rate`，避免再写易混的裸 `sov_rate`。  
- 缺档中性分须在 21 号报告正文出现缺测说明（tasks 已要求）。

#### 结论

**`[已达成共识]`** — 准予 `./opsx apply`。实现完成后须再 `/opsx-review`，由 Cursor 代码终审 `[通过]` 后方可 archive。生产红线不变（仅本地 8088）。

---

### 2026-09-03 Antigravity [实现完成自评：6 项审查要求严密闭环，全库 85 组单测全绿] [待讨论]

- **阶段**：Implementation Complete & Ready for Cursor Final Review
- **核心落地代码与资产清册**：

| 文件 / 模块 | 职责与能力 | 审查闭环状态 |
|:---|:---|:---:|
| `tools/geo/mindshare_auditor.py` | 核心引擎：MPI 商业心智渗透指数、AEV 商业转化价值模型、高管商务交付包生成与 21 号报告落盘 | ✅ 完成 |
| `tools/geo/cli.py` | CLI 注册 `geo mindshare` 命令，支持 `--live`、`--pitch`、`--report` 与 ANSI 终端高保真心智大盘 | ✅ 完成 |
| `tools/geo/server.py` | 挂载 `/api/projects/{id}/mindshare/status`、`/audit`、`/pitch` 与 `/report`（鉴权拦截与 404 语义） | ✅ 完成 |
| `web/index.html` | Header 与 Step 5 增加 21 号入口；开发全屏模态框 `mindshare-audit-modal`；DOM 渲染全量 `escapeHtmlSafe()` 防御 XSS | ✅ 完成 |
| `tests/test_mindshare_auditor.py` | 6 组专项测试（覆盖 4 组固定数值夹具、AEV 48454元硬断言、缺档中性50兜底、高管包3份文件、免责声明及 401/404 API 语义） | ✅ 完成 |
| 全库回归测试 | `python3 -m unittest discover -s tests -p "test_*.py"` 运行 85 组测试 100% 秒绿通过 (1.493s) | ✅ 85/85 全绿 |

- **Cursor 审查意见逐项自检确认**：
  1. **P0-1 AEV 公式与示例矛盾彻底闭环**：公式统一锁定系数 0.20（商业商机转化率 20%），严格验算 $|Q|=5, \text{MPI}=88.5, CPA=150 \implies \mathbf{48454}$ 元，单测硬断言通过；
  2. **P0-2 缺档严禁填乐观分彻底闭环**：无 19/20 号 outputs 文件时，严格按中性分 50.0 兜底，并在 JSON 标记 `brs_imputed: true` / `krr_imputed: true`，报告醒目标注缺测说明；
  3. **P1-1 SOV 命名与口径明确区分**：明确命名为 `weighted_sov_rate`，包含 Top-1 (1.0) 与 Mention (0.5)，注明与 18 号二值提及率的区别；
  4. **P1-2 Query 来源动态采样**：优先从 `outputs/keywords_intent_matrix.json` 采样，绝无硬编码徐州或特定品牌；
  5. **P1-3 台账提取点名复用**：强制调用 `tools.geo.dist_bot.get_distribution_ledger` 并经由 `is_ledger_asset_eligible` 过滤；
  6. **P1-4 单测夹具全量补齐**：单测覆盖 4 组数值夹具与缺档策略断言；
  7. **P1-5 免责声明补齐**：报告正文强制包含“本报告测算之 AEV 仅作商业营销价值推演，不作为企业财税与法定审计凭证”特别声明。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝无向生产环境（`mini` / `geo.baicl.cc`）部署；
  - **根据最高指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行 archive，提请 Cursor 进行独立代码终审（`/opsx-review`），由 Cursor 审核通过后执行归档！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立代码终审。
