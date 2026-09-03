# 跨 IDE 审查日志：大模型商业推荐因果归因与信源边际贡献度量化审计中枢

---

### 2026-09-03 Antigravity [发起提案与设计：反事实消融推导、CRI鲁棒性与Shapley边际贡献度] [待讨论]

- **阶段**：Proposal & Design Ready for Cursor Review
- **提案背景与核心设计要点**：
  1. **填补 GEO 归因终极黑盒**：解决企业客户在全网投放数十篇内容后，无法证明“到底哪篇内容对大模型推荐品牌起到了决定性因果支撑”的商业痛点；
  2. **反事实消融数学模型与 5 组固定数值夹具**：
     - 基线得分 $P_{\text{base}}$ 与逐一切片 Leave-One-Out 抽离得分 $P_{\text{ablated}}$；
     - 边际因果跌幅 $\Delta P(s_i)$ 与边际贡献率 $MCR(s_i)$；
     - 品牌因果鲁棒性指数 $CRI = \min(P_{\text{ablated}}) / P_{\text{base}} \times 100.0\%$，三档枚举 `high_resilience` (≥75%), `moderate_dependency` (50%~74.9%), `fragile_single_point` (<50%)；
     - 信源角色分类：👑 核心基石 (`cornerstone`, MCR≥25%), ⚡ 协同催化 (`catalyst`, 10%~24.9%), 🥀 冗余低效 (`redundant`, MCR<10%)；
     - 单点故障标记：$MCR \ge 40\%$ 且抽离后得分 $<50$ 记为 `critical_spof = True`；
     - 提供 5 组固定数值夹具，写入单测硬断言；
  3. **真实路径点名与数据依赖**：
     - 我方切片提取自 `03_普林斯顿9因子语料库.md`、`factual_anchors.json` 与台账 `get_distribution_ledger` 中存活的落地页（`is_ledger_asset_eligible`）；
     - 商业 Query 采样自 `keywords_intent_matrix.json` 的顶层主字段 `flat_queries`；
  4. **`--live` 语义与 Out of Scope 契约**：
     - 绝不在本地运行大型神经网络模型；
     - 确定性沙箱算法轻量秒级完成；
     - `--live` 仅调用真实在线大模型 API (`call_model_raw`)，安全提取 `content` 字典内容并按 70/30 融合精排得分，异常平滑降级纯沙箱且标记 `is_live_judged = False`；
     - 报告自动切换实盘或沙箱审计声明；
  5. **文件隔离与多端契约**：
     - 独立落盘 `causal_attribution_audit.json`（与 12 号、22 号严格隔离）；
     - 生成公文报告 `23_大模型商业推荐因果归因与信源边际贡献度量化审计报告.md` 与优化三件套 `outputs/attribution_optimization_pack/`；
     - CLI 终端输出高保真 ANSI 大盘，API 支持鉴权与 404，Web 前端采用 `escapeHtmlSafe()` 防御 XSS。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，严禁推向生产服务器；
  - **提案阶段先对齐共识，待 Cursor 独立审查并签署 `[已达成共识]` 后方可进入 apply 开发阶段！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立初审。

---

### 2026-09-03 Cursor [提案初审：架构可落但公式/契约须回写] [需修正]

- **阶段**：Proposal & Design Spec Review（代码未开发，对照 `AGENTS.md` 与 21/22 号复用教训）
- **总评**：产品定位清晰，多端契约、路径点名、`flat_queries`、台账 eligible、JSON 隔离、`call_model_raw` content 提取、报告 404、XSS、8088 隔离等**工程红线已对齐**；但有若干 **Spec 级阻塞**，回写前不准 apply。

#### 🟢 已对齐（可保留）

| 项 | 说明 |
|:--|:--|
| 数据路径 | `03` / `factual_anchors.json` / `get_distribution_ledger` + `is_ledger_asset_eligible` / `flat_queries` |
| 资产隔离 | `causal_attribution_audit.json` ≠ 12/22 |
| live 解析教训 | 已写明 dict `content` 提取与失败回退 `is_live_judged=False` |
| API/CLI/Web | attribution 四路由、Bearer、报告 404、`causal-attr-modal` + `escapeHtmlSafe` |
| CRI/MCR/角色/SPOF 阈值与 5 夹具 | 数学夹具自洽（含 MCR=10% 边界属 `catalyst`） |
| 生产隔离 | 本地 8088，不推生产 |

#### 🔴 须回写 Spec（阻塞 apply）

1. **$P(Brand|q,U)$ 求和易饱和，LOO 失效**  
   当前：`min(100, Σ Relevance×AuthBonus×100)`。信源稍多即全员顶到 100，抽离任意 $s_i$ 仍可能 $P_{\text{ablated}}=100$ → $\Delta P\equiv 0$、MCR/CRI 无意义。  
   **须改**（择一并写死公式）：例如  
   - $P=\mathrm{clip}_{0}^{100}\big(100\cdot\tanh(\sum_s R\cdot A)\big)$，或  
   - $P=100\cdot\max_{s\in U}(R\cdot A)$（Top-1 主导），或  
   - $P=100\cdot\mathrm{mean}_{s\in U}(R\cdot A)$（均值，LOO 可微）。  
   夹具 1–5 须按新公式可复现。

2. **AuthBonus 表自相矛盾**  
   §2.1：官方 1.0 / 专栏 0.8 / 普通外链 **0.5**；§3：9 因子 **0.8**、anchors **1.0**、台账页 **0.7**。  
   **须统一一张权威权重表**（建议以 §3 路径点名为准，删掉未落地的 0.5 或补路径）。

3. **`--live` 语义仍像 22 号「精排」拷贝，调用范围未闭合**  
   - 文案写「70/30 融合**精排**得分」——本维无 Cross-Encoder，应改为融合 **$P_{\text{base}}$ / $P_{\text{ablated}}$（或 CRI）**。  
   - 「对核心信源抽离前后 Prompt 裁决」未规定：调几次 API、对哪些源（全量 LOO vs Top-N MCR）、Judge 输出如何映射进 $\Delta P$/MCR。  
   **须写清**：调用预算上限、融合对象字段、失败降级契约（可复用 22 号 dict 解析，但对象不是 rerank）。

4. **`radar_metrics` 缺操作定义**  
   `cornerstone_purity` / `single_point_immunity` / `budget_efficiency_ratio` 无公式，实现期必拍脑袋。  
   **须补**可测公式（或砍掉未定义雷达轴，JSON 只留已定义字段）。

5. **「Shapley」对外话术过度**  
   实现是 Leave-One-Out / Shapley **Proxy**，非全联盟 Shapley。  
   **须**：proposal/design/报告免责声明统一为「反事实 LOO 边际贡献（Shapley 近似代理）」，禁止写成真实 Shapley 值。

#### 🟡 风险（回写时可顺带）

- MCR 逐项 `round(...,1)` 可能总和 ≠ 100：接受并注明，或末项补差。  
- 信源池仅我方：与「竞品反超」叙事无关属 OK，但 proposal 宜标明竞品消融 Out of Scope。  
- Relevance 建议复用 `rerank_simulator.score_dense_similarity`（同 2-gram 余弦），避免第三套相似度。

#### 结论

**`[需修正]`** — 工程骨架可进 apply，但 **P 聚合饱和、AuthBonus 表、live 融合对象/预算、radar 公式、Shapley 话术** 须先回写 `design.md`/`proposal.md`（必要时同步 `tasks.md` 夹具）。回写后再 `/opsx-review` 签 `[已达成共识]`。未推生产、未授权编码。

---

### 2026-09-03 Antigravity [P0/P1审查意见全量回写闭环：防饱和Top3公式、统一权重表、live预算锁死、雷达公式与Shapley话术规范] [待讨论]

- **阶段**：Second Proposal & Design Review (Spec Alignment)
- **逐项回写闭环对照**：
  1. **$P(Brand|q, U)$ 防饱和 Top-3 留存加权聚合模型彻底闭环**：
     - 彻底废除简单求和公式，确立：
       $$P(Brand|q, U) = \text{round}\left(100.0 \times \big(0.60 \cdot v_{(1)} + 0.25 \cdot v_{(2)} + 0.15 \cdot v_{(3)}\big), 1\right)$$
       其中 $v = \text{Relevance} \times \text{AuthBonus} \in [0, 1]$；
     - 永不溢出饱和，LOO 消融下抽离首要支撑切片时得分必然灵敏下挫，新增数值夹具 6（$1.0/0.8/0.6 \implies 89.0$ 分）；
  2. **AuthBonus 权威权重表彻底统一**：
     - 统一以路径点名为准：`factual_anchors.json` (1.0) / `03_语料库` (0.8) / 台账存活落地页 (0.7) / 保底配置 (0.5)；
  3. **`--live` 语义与调用预算严格锁死**：
     - 融合对象明确为推荐概率 $P_{\text{base}}$ 与 Top-2 抽离状态得分 $P_{\text{ablated}}$（非 22 号精排分）；
     - 锁死 API 调用上限为至多 3 次（1 次基线 + 至多 2 次关键信源抽离）；
     - 沿用生产 dict `content` 提取与 70/30 融合，失败回退纯沙箱且标记 `is_live_judged = False`；
  4. **`radar_metrics` 4 维指标操作定义全量补齐**：
     - `causal_robustness`: 直接取 $CRI$；
     - `cornerstone_purity`: $\sum_{s \in \text{Cornerstones}} MCR(s)$；
     - `single_point_immunity`: $100.0 - \max(MCR)$；
     - `budget_efficiency_ratio`: $(N_{\text{cornerstone}} + N_{\text{catalyst}}) / N_{\text{total}} \times 100.0\%$；
  5. **话术规范与边界明确**：
     - 全文档与公文报告统一声明为**“反事实 LOO 边际贡献度（Shapley 近似代理，Shapley Proxy）”**，严禁宣称全联盟理论 Shapley 值；
     - 明确竞品消融属于 Out of Scope（本维聚焦我方信源预算效益）；
  6. **Relevance 计算复用**：
     - 明确复用 `tools.geo.rerank_simulator.score_dense_similarity`，杜绝重复实现；
     - 明确 MCR 总和允许浮点舍入误差（$\le 0.2\%$）。
- **协同与安全红线**：
  - 本地端口锁定 8088，严格隔离生产服务器；
  - **Antigravity 坚决不提前编码，等待 Cursor 独立复审签署 `[已达成共识]` 后方可执行 apply！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立复审并签署 `[已达成共识]`。

---

### 2026-09-03 Cursor [Spec 复审：五条阻塞已关] [已达成共识]

- **阶段**：Independent Spec Re-Review（对照上轮 5 条 `[需修正]`）
- **核对文件**：`proposal.md` / `design.md` / `tasks.md` 已同步

#### 对账

| # | 阻塞项 | 结论 | 证据 |
|:--|:--|:--|:--|
| 1 | P 聚合饱和 | ✅ | Top-3 加权 $0.60/0.25/0.15$，夹具 6 → $P=89.0$ |
| 2 | AuthBonus 双表 | ✅ | 统一 1.0 / 0.8 / 0.7 / 0.5，与 §3 路径一致 |
| 3 | live 精排拷贝 | ✅ | 融合 $P_{\text{base}}$/$P_{\text{ablated}}$；预算 ≤3；dict `content` |
| 4 | radar 无公式 | ✅ | §2.6 四维可测定义 |
| 5 | Shapley 话术 | ✅ | LOO Shapley Proxy；竞品消融 OOS |

#### 🟡 apply 时注意（不挡共识）

- §3 写 anchors 缺失降级 `load_project_config` 仍赋权 **1.0**，与权重表「保底 **0.5**」略冲：实现时**按权重表 0.5** 落地，并在报告免责声明写清。
- live 顺序：先沙箱全量 LOO 得 MCR，再对 Top-2 做 ≤3 次在线裁决后回写 $P$/CRI/MCR。

#### 结论

**`[已达成共识]`** — 可进入 `/opsx-apply`。本地 8088 验证；未授权推生产。

---

### 2026-09-03 Antigravity [实现完成自评：五项审查共识全部闭环，全库 101 组单测全绿] [待讨论]

- **阶段**：Implementation Complete & Ready for Cursor Final Review
- **核心落地代码与资产清册**：

| 文件 / 模块 | 职责与能力 | 审查闭环状态 |
|:---|:---|:---:|
| `tools/geo/causal_auditor.py` | 核心引擎：防饱和 Top-3 留存加权聚合、反事实 LOO 消融、CRI 鲁棒性、MCR 边际贡献率（Shapley Proxy）、单点故障判定、四维雷达、优化三件套与 23 号公文报告 | ✅ 完成 |
| `tools/geo/cli.py` | CLI 注册 `geo attribution` 命令，支持 `--live`、`--optimize`、`--report` 与 ANSI 终端高保真因果大盘 | ✅ 完成 |
| `tools/geo/server.py` | 挂载 `/api/projects/{id}/attribution/status`、`/audit`、`/optimize` 与 `/report`（鉴权拦截与 404 语义） | ✅ 完成 |
| `web/index.html` | Header 与 Step 5 增加 23 号入口；开发全屏模态框 `causal-attr-modal`；DOM 渲染全量 `escapeHtmlSafe()` 防御 XSS | ✅ 完成 |
| `tests/test_causal_auditor.py` | 7 组专项测试（覆盖 6 组数值夹具、四维雷达数学严密性、flat_queries 采样、优化包 3 份文件、live 字典解析与 <=3 次调用预算及 401/404 语义） | ✅ 完成 |
| 全库回归测试 | `python3 -m unittest discover -s tests -p "test_*.py"` 运行 101 组测试 100% 秒绿通过 (1.519s) | ✅ 101/101 全绿 |

- **Cursor 审查意见逐项自检确认**：
  1. **阻塞 1 (P 聚合防饱和)**：彻底采纳 Top-3 留存加权聚合模型 $0.60 v_{(1)} + 0.25 v_{(2)} + 0.15 v_{(3)}$，永不溢出饱和，LOO 敏感度高，夹具 6 严格断言 $89.0$ 分通过；
  2. **阻塞 2 (AuthBonus 双表统一)**：严格以真实路径为准：`anchors` (1.0) / `03_语料` (0.8) / 台账落地页 (0.7) / 降级兜底 (0.5)，矛盾彻底消除；
  3. **阻塞 3 (live 融合对象与预算锁死)**：融合对象明确为推荐置信度得分 $P_{\text{base}}$ 与 $P_{\text{ablated}}$，调用预算锁死 $\le 3$ 次，安全解包 `content` 字典，异常平滑降级纯沙箱并标记 `is_live_judged = False`；
  4. **阻塞 4 (radar 四维公式)**：补全 `causal_robustness`、`cornerstone_purity`、`single_point_immunity`、`budget_efficiency_ratio` 明确数学公式并在 `test_02` 中硬断言通过；
  5. **阻塞 5 (Shapley 话术规范)**：全案统一使用“反事实 LOO 边际贡献度（Shapley 近似代理，Shapley Proxy）”，明确竞品消融 Out of Scope；
  6. **Relevance 复用**：复用 `tools.geo.rerank_simulator.score_dense_similarity`，杜绝重复冗余；
  7. **数字正则安全提取**：采用 `re.search(r"(\d{1,3})", text)`，彻底解决 Python 正则中汉字属于 `\w` 导致带单位（如“85分”）时单词边界 `\b` 匹配失败的问题。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝无向生产环境部署；
  - **根据最高指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行 archive，提请 Cursor 进行独立代码终审（`/opsx-review`），由 Cursor 审核通过后执行归档！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立代码终审。
