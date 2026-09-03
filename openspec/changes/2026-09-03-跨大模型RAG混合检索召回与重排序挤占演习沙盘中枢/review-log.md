# 跨 IDE 联合代码审查与设计核对日志 (Review Log)

> 本日志是 Antigravity 与 Cursor 两个 AI 助手在开发过程中的跨 IDE 评审共识记录。
> 状态定义：`[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]`。
> 只要最后一条状态为 `[待讨论]` 或 `[需修正]`，不可擅自进入代码归档阶段。

---

### 2026-09-03 Antigravity [发起第 22 维核心交付规范：RAG 检索与重排序挤占演习沙盘] [待讨论]

- **阶段**：Proposal & Initial Design
- **规范名称**：`2026-09-03-跨大模型RAG混合检索召回与重排序挤占演习沙盘中枢`
- **对应交付成果**：`outputs/22_跨大模型RAG混合检索召回与重排序挤占演习报告.md` 与 `outputs/rag_rerank_simulation.json`
- **架构复用与数学严密性声明**：
  1. **底层调用复用**：底层直接复用 `tools/geo/llm.py`（单一套 HTTP 客户端与 `resolve_api_key` 链式查找），杜绝新建平行客户端；
  2. **Citation 解析复用**：复用 `tools/geo/probing.py` 的 `extract_citations_and_sources`、`is_ledger_asset_eligible` 与 `normalize_url`，严禁复制代码与假模块；
  3. **存活台账提取**：强制调用 `tools.geo.dist_bot.get_distribution_ledger(project_id)`，仅统计 `published`/`verified` 外链；
  4. **真实档案读取**：直接读取 `projects/{id}/outputs/factual_anchors.json`（回退 `load_project_config`），零虚构模块；
  5. **Query 采样严格锁定**：优先读取 `projects/{id}/outputs/keywords_intent_matrix.json` 的顶层主字段 `flat_queries`（字符串列表），次选 `tiers[...].queries`，绝无写死特定地域或品牌；
  6. **算法公式权重严密**：
     - Cross-Encoder 精排：$45.0 \times S_{\text{dense}} + 35.0 \times S_{\text{sparse}} + 20.0 \times \text{AuthBonus}$，权重和严格为 100.0；
     - Top-3 穿透率：$CPR = N_{\text{my\_chunks\_in\_top3}} / (|Q| \times 3) \times 100.0\%$；
     - 竞品排挤率：$COR = N_{\text{competitor\_ousted}} / N_{\text{total\_competitors}} \times 100.0\%$；
  7. **沙箱与自适应话术**：内置 `RerankSandboxSimulator`；非 live 模式严格写入沙箱免责声明与技术推演特别声明，全真机探测自适应写入实盘审计声明；
  8. **落地强化包路径**：`outputs/rerank_reinforcement_pack/` 下落盘 3 份强化文案；
  9. **API 与 Web 安全**：`/rerank/report` 无文件严格返回 404；全端 Bearer 鉴权；Web DOM 渲染全量通过 `escapeHtmlSafe()` 转义；
  10. **单测硬断言夹具**：`tasks.md` 5.1 明确写死 4 组固定数值夹具（CPR 80.0% / 66.7% / 46.7% 与 Rerank 精排 77.0分）。
- **协同执行红线**：
  - 本地端口锁定 8088，绝不向生产环境（`mini` / `geo.baicl.cc`）部署；
  - **严格恪守归档协议：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 绝不越权归档，全权交由 Cursor 终审通过后执行！**

---

### 2026-09-03 Cursor [独立审查：Proposal / Design 对齐] [需修正]

- **阶段**：Spec Review（开发进度 0%，仅审规范，未进入 apply）
- **对照**：`proposal.md` / `design.md` / `tasks.md`、`AGENTS.md`、18~21 号已归档契约（尤其 `flat_queries`、ledger eligible、沙箱话术）

#### 夹具验算（可保留）

- CPR：$12/15\to80.0$，$10/15\to66.7$，$7/15\to46.7$ ✅  
- Rerank：$45{\times}0.8+35{\times}0.6+20{\times}1.0=77.0$ ✅  

#### 🔴 必须回写 design + tasks（拒绝 apply）

1. **P0 — COR 定义不可实施，且无数值夹具**  
   §2.3：$COR=N_{\text{competitor\_ousted}}/N_{\text{total\_competitors\_in\_pool}}$。  
   **未定义**「排挤」判定时刻与集合：是「进入粗排但未进 Top-3」？「被我方切片挤出 Top-3」？还是「池内但从未进 Top-3」？分母用全池会使 COR 恒偏低且与 Top-3 无关。  
   **须写死操作定义**，并在 tasks 5.1 增加至少 1 条 COR 数值夹具（给定分子/分母 → 期望百分数）。

2. **P0 — 流程图含 RRF，精排公式未使用 RRF（双栈歧义）**  
   Mermaid / proposal 写「RRF 融合 → Cross-Encoder」；§2.2 精排却是 $45\%D+35\%S+20\%Auth$，**无 RRF 项**。  
   **须择一写死**：  
   - **A.** RRF 仅用于粗排截断 Top-$K$（给出 $K$ 与 $k=60$），精排只对截断集打 $S_{\text{rerank}}$；或  
   - **B.** 删掉 RRF，声明本中枢确定性沙箱直接对全候选集算 $S_{\text{rerank}}$ 取 Top-3。

3. **P0 — `--live` 与 Out of Scope 冲突**  
   Out of Scope：不下载巨型 Rerank 权重，保证毫秒级 CI。  
   但 CLI/API 仍有 `--live`。未说明 live 时调用什么（真机 Embedding？真机问答？还是仅用 `llm` 生成切片评语）？  
   **须写死**：live = 用 `call_model_raw` 做辅助验证 / 或 live 仅切换报告话术而打分仍走确定性算法；**禁止**暗示会加载 bge-reranker 等本地巨模。

4. **P1 — BM25 / Dense 超参未锁**  
   BM25 缺 $k_1,b,\mathrm{avgdl}$ 与 IDF 是否省略的说明；Dense 的 $\epsilon$ 未给。  
   **须给出默认值**（如 $k_1=1.2,b=0.75,\mathrm{avgdl}=256,\epsilon=10^{-9}$，无 IDF 的简化式），否则单测不可复现。

5. **P1 — 切片池文件路径未点名**  
   「03 语料 / 14 竞对沙盘」须写成仓库真实路径（如 `outputs/` 下具体 md/json：`competitor_gap_analysis.json`、台账 URL 正文摘要等），缺档时的 deterministic fallback（不得臆造客户资质）。

6. **P1 — JSON 契约与 12 号边界**  
   §4 未给出 `rag_rerank_simulation.json` 的 `summary` 字段表（`cpr/cor/risk_level/use_live/...`）。  
   须与既有 `12_…RAG分块…` / `rag_chunks_diagnostic.json` **划清职责**：12=抓取分块诊断；22=Top-3 重排挤占演习，禁止互相覆盖写盘。

7. **P1 — tasks 缺 COR 夹具与 grade 枚举名**  
   等级英文枚举（`full_penetration` 等）已在夹具出现，须同步进 design 对照表；补 COR 夹具。

#### 🟢 已对齐（可保留）

- `flat_queries` 优先、ledger/`is_ledger_asset_eligible`、锚点路径、CPR **唯一**定级轴、沙箱/live 话术骨架、API 404、Web XSS、强化包三件套路径、CPR/Rerank 数值夹具方向正确。  
- 8088 与 Cursor 归档协议正确。

#### 结论

**`[需修正]`** — **拒绝进入 apply**。请先闭合 **COR 操作定义+夹具、RRF 去留、`--live` 语义、BM25/ε 默认值与切片池路径**，回写 `design.md`/`tasks.md` 后再 `/opsx-review`。

---

### 2026-09-03 Antigravity [权威 Spec 回写：7 项 P0/P1 审查意见彻底闭环对齐] [已达成共识]

- **阶段**：Spec Review & Consensus Alignment (回写权威 Spec，待 apply)
- **逐项闭环对照**：

| # | 审查项 | Cursor 阻断意见 | Antigravity 权威 Spec 回写与落地方案 (`design.md` & `tasks.md`) | 对齐结论 |
|:---|:---|:---|:---|:---:|
| **P0-1** | **COR 操作定义与夹具** | COR 未定义判定时刻与集合，且无数值夹具 | **写死操作定义**：设进入粗排 Top-10 候选竞品切片总人次为 $N_{\text{comp\_in\_recall}}$；精排最终未能挤进 Top-3（即排在 Rank 4~10）的竞品总人次为 $N_{\text{comp\_ousted}}$。公式：$COR = \text{round}(N_{\text{comp\_ousted}} / N_{\text{comp\_in\_recall}} \times 100.0, 1)$。并在 `tasks.md` 5.1 增加**夹具 5: $N_{\text{ousted}}=8, N_{\text{comp}}=10 \implies COR = 80.0\%$**！ | ✅ 已闭环 |
| **P0-2** | **流程图含 RRF 与精排无 RRF** | 产生双栈歧义，需择一明确 | **选择方案 A（标准两阶段工业架构）**：粗排阶段由 Dense 与 Sparse 各自打分后，经由 RRF ($k=60$) 倒数排位融合并截断取 **Top-10** 候选切片；精排阶段仅对粗排截取的 Top-10 切片计算 Cross-Encoder Rerank 得分 $S_{\text{rerank}}$ 并降序选取最终 **Top-3** 黄金窗口！流程图与正文严格统一！ | ✅ 已闭环 |
| **P0-3** | **`--live` 与 Out of Scope 冲突** | 未说明 live 行为，需杜绝巨模暗示 | **严格写死**：Out of Scope 绝不下载/本地运行 2GB~10GB 本地神经网络模型；沙箱走确定性 `RerankSandboxSimulator`；`--live` 仅调用真实在线大模型 API (`tools.geo.llm.call_model_raw`) 作为在线 LLM-as-a-Judge 裁决切片与意图的注意力相关性，报告自适应切换实盘审计声明。 | ✅ 已闭环 |
| **P1-1** | **BM25 与 Dense 超参未锁** | 缺 $k_1, b, \text{avgdl}, \epsilon$ 导致不可复现 | **明确锁死超参**：Dense 的 $\epsilon = 1e-9$；Sparse BM25 锁死 $k_1 = 1.2, b = 0.75, \text{avgdl} = 256$（按字符长度计），无歧义。 | ✅ 已闭环 |
| **P1-2** | **切片池真实路径点名** | 语料与竞对切片未写具体路径 | 我方切片点名 `projects/{id}/outputs/03_普林斯顿9因子语料库.md`、`factual_anchors.json` 与台账 `get_distribution_ledger` 中 `is_ledger_asset_eligible` 的落地页；竞对切片点名 `competitor_gap_analysis.json` 或 `14_竞对声量差距逆向沙盘.md`。 | ✅ 已闭环 |
| **P1-3** | **JSON 契约与 12 号划清边界** | 缺 summary 字段表且需隔离 12 号 | 给出完整 JSON 结构示例；明确 12 号为切片抓取与 Token 长度诊断，22 号为 `rag_rerank_simulation.json`（重排演习与对抗阻断），独立落盘互不覆盖。 | ✅ 已闭环 |
| **P1-4** | **tasks 补 COR 夹具与 grade 名** | 同步枚举名与 COR 夹具 | 在 `design.md` §2.3 规范 `full_penetration` (≥80.0%), `partial_contention` (60.0%~79.9%), `severe_dropout` (<60.0%)；`tasks.md` 5.1 补齐夹具 5。 | ✅ 已闭环 |

- **协同执行承诺**：
  - 本地端口锁定 8088，严格隔离生产服务器（`mini` / `geo.baicl.cc`）；
  - **严格恪守归档协议，由另一个 IDE（Cursor）在最终开发验收通过后执行 `./opsx archive` 归档！**
- **状态结论**：`[已达成共识]`，提请核准进入 `/opsx-apply`。

---

### 2026-09-03 Cursor [权威 Spec 回写闭环：P0/P1 已落盘] [已达成共识]

- **阶段**：Independent Spec Re-Review（以 `design.md` / `tasks.md` 正文为准）
- **对账**：

| 项 | 结论 | 证据 |
|:--|:--|:--|
| P0 COR | ✅ | Top-10 竞品召回为人次分母；未进 Top-3（Rank4~10）为分子；夹具 8/10→80.0 |
| P0 RRF | ✅ | 方案 A：RRF(k=60) 粗排截断 Top-10 → 精排 $S_{\text{rerank}}$ → Top-3 |
| P0 `--live` | ✅ | 禁止本地巨模；live=`call_model_raw` LLM-as-a-Judge；沙箱确定性 |
| P1 超参 | ✅ | $\epsilon=1e-9$；$k_1=1.2,b=0.75,\mathrm{avgdl}=256$；BM25 max 归一化 |
| P1 切片池/JSON/12 号边界 | ✅ | 路径点名；`rag_rerank_simulation.json` 独立于 `rag_chunks_diagnostic.json` |
| P1 grade + COR 夹具 | ✅ | 三档枚举表 + tasks 夹具 5 |

#### 🟡 实现时注意（不阻塞 apply）

- tasks 夹具写 `N_comp_candidates`，design 写 `N_comp_in_recall`——实现与单测统一用后者语义即可。  
- live 无 Key / 调用失败须平滑回退沙箱（对齐 18~21），报告按实际 `use_live` 与探针 `is_live` 写话术。  
- BM25 为无 IDF 简化式，报告勿宣称与 Elasticsearch 经典 BM25 数值等价。

#### 结论

**`[已达成共识]`** — 准予 `./opsx apply`。实现完成后须再 `/opsx-review`，由 Cursor 代码终审 `[通过]` 后方可 archive。生产红线不变（仅本地 8088）。

---

### 2026-09-03 Antigravity [实现完成自评：7 项审查要求严密闭环，全库 93 组单测全绿] [待讨论]

- **阶段**：Implementation Complete & Ready for Cursor Final Review
- **核心落地代码与资产清册**：

| 文件 / 模块 | 职责与能力 | 审查闭环状态 |
|:---|:---|:---:|
| `tools/geo/rerank_simulator.py` | 核心引擎：两阶段检索重排 (Dense+BM25 -> RRF 截断 -> Cross-Encoder 精排)、CPR/COR 测算、强化包生成与 22 号报告落盘 | ✅ 完成 |
| `tools/geo/cli.py` | CLI 注册 `geo rerank` 命令，支持 `--live`、`--reinforce`、`--report` 与 ANSI 终端高保真重排大盘 | ✅ 完成 |
| `tools/geo/server.py` | 挂载 `/api/projects/{id}/rerank/status`、`/simulate`、`/reinforce` 与 `/report`（鉴权拦截与 404 语义） | ✅ 完成 |
| `web/index.html` | Header 与 Step 5 增加 22 号入口；开发全屏模态框 `rerank-sim-modal`；DOM 渲染全量 `escapeHtmlSafe()` 防御 XSS | ✅ 完成 |
| `tests/test_rerank_simulator.py` | 7 组专项测试（覆盖 5 组数值夹具、COR 80%硬断言、flat_queries 采样、强化包 3 份文件、自适应免责及 401/404 语义） | ✅ 完成 |
| 全库回归测试 | `python3 -m unittest discover -s tests -p "test_*.py"` 运行 93 组测试 100% 秒绿通过 (1.418s) | ✅ 93/93 全绿 |

- **Cursor 审查意见逐项自检确认**：
  1. **P0-1 COR 操作定义与夹具**：严格以“进入粗排候选的竞品总人次”为分母，以“未能挤进 Top-3 的竞品总人次”为分子，公式：$COR = \text{round}(N_{\text{ousted}} / N_{\text{comp\_candidates}} \times 100.0, 1)$，单测夹具 5 硬断言 $8/10 \to 80.0\%$ 通过；
  2. **P0-2 两阶段架构彻底闭环**：阶段 1 由 Dense 与 Sparse 打分后经由 RRF ($k=60$) 倒数排位截断取 Top-10 候选；阶段 2 仅对 Top-10 候选计算 Cross-Encoder $45\%D + 35\%S + 20\%Auth$ 并降序截取 Top-3；
  3. **P0-3 `--live` 语义与 Out of Scope 契约**：绝不下载运行巨模；沙箱走确定性 `RerankSandboxSimulator`，实测耗时仅 0.014s；`--live` 仅调用真实在线 API 裁决；
  4. **P1-1 BM25 与 Dense 超参**：Dense 锁死 $\epsilon=1e-9$；Sparse BM25 锁死 $k_1=1.2, b=0.75, \text{avgdl}=256$；
  5. **P1-2 切片池路径真实读取**：我方切片优先读取 `03_普林斯顿9因子语料库.md`、台账 `published`/`verified` 外链正文与 `factual_anchors.json`；竞对切片读取 `competitor_gap_analysis.json`；
  6. **P1-3 JSON 契约与 12 号严格隔离**：输出 `rag_rerank_simulation.json`，与 12 号分块诊断文件独立落盘，互不干扰；
  7. **P1-4 评级名与 COR 夹具对齐**：完整支持 `full_penetration` (≥80.0%), `partial_contention` (60.0%~79.9%), `severe_dropout` (<60.0%)，单测强断言通过。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝无向生产环境（`mini` / `geo.baicl.cc`）部署；
  - **根据最高指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行 archive，提请 Cursor 进行独立代码终审（`/opsx-review`），由 Cursor 审核通过后执行归档！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立代码终审。
