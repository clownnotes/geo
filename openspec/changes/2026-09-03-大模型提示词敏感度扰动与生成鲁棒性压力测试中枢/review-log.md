# 评审日志：大模型提示词敏感度扰动与生成鲁棒性压力测试中枢 (第 25 维核心交付)

---

### 2026-09-03 Antigravity [发起第 25 维提案：提示词敏感度扰动与生成鲁棒性压力测试中枢] [待讨论]

- **阶段**：Initial Proposal & Technical Design Review
- **核心能力与规范设计**：
  1. **四维确定性商业微扰动生成算法**：
     - 基线 Query 优先读取 `keywords_intent_matrix.json` 中首条真实 Prompt，确定性派生 4 组变体：$V_1$ 口语化置换、$V_2$ 质疑避坑口吻、$V_3$ 句式倒装重排、$V_4$ 预算横向对比；
  2. **严禁编写重复算法**：
     - 强制直接复用 23 维防饱和 Top-3 推荐概率模型：`from tools.geo.causal_auditor import score_brand_recommendation_confidence, _build_attribution_source_pool`；
  3. **严谨数学量化模型**：
     - 扰动均值 $\bar{P}$、样本标准差 $\sigma$、变异系数 $CV = \sigma / \bar{P}$、留存率 $RR = \bar{P} / P_{\text{orig}}$；
     - 生成鲁棒性指数：$GRI = \text{round}(RR \times (1.0 - CV), 1)$；
     - 鲁棒性三档评级：`rock_solid` ($\ge 75\%$) / `moderate_fluctuation` ($50\sim 74.9\%$) / `fragile_sensitive` ($<50\%$)；
     - 高危脆弱扰动判定：跌幅 $\ge 15.0$ 分；
  4. **6 组固定数值夹具锁定**：
     - 包含磐石抗震（$91.0\%$）、中度波动（$66.2\%$）、脆弱敏感（$29.8\%$）、高危脆弱项识别、四维雷达与 Top-3 聚合算法；
  5. **Live 模式调用预算与快照防御**：
     - 预算锁死至多 5 次调用（基线 1 次 + 4 组变体各 1 次，硬计数器 `api_calls <= 5`）；
     - 生产字典安全解包与正则防御；
     - 融合后强制基于全新 5 个得分全量重算统计量、GRI、高危项与雷达；
     - 进入 live 前深拷贝沙箱快照，中途任何异常 100% 完整回滚纯沙箱；
  6. **交付资产与公文报告物理隔离**：
     - 数据文件：`outputs/prompt_robustness_stress_test.json`（对齐顶层 Schema）；
     - 商业报告：`outputs/25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md`；
     - 容灾加固包：`outputs/robustness_hardening_pack/`（3 份文件）。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝对隔离生产服务器；
  - **根据最高指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行归档，提请 Cursor 独立初审签署 `[已达成共识]`！**
- **状态结论**：`[待讨论]`，提请 Cursor 进行独立设计初审。

---

### 2026-09-03 Cursor [提案初审：GRI/夹具/live/23号复用齐，V1确定性与 JSON 契约须回写] [需修正]

- **阶段**：Proposal & Design Spec Review（代码未开发；对照 `AGENTS.md`、23/24 号归档复用模式）
- **总评**：第 25 维骨架可落——四维微扰动、$\bar{P}/\sigma/CV/RR/GRI$、三档评级、高危跌幅≥15、live≤5 + 70/30 + 全量重算 + 深拷贝回滚、强制复用 23 号 `score_brand_recommendation_confidence` / `_build_attribution_source_pool`、输出物理隔离、CLI/API/Web/`escapeHtmlSafe`/本地 8088 均对齐。6 组数值夹具已独立验算全部自洽。以下阻塞未写死前**不准 apply**。

#### 🟢 已对齐

| 项 | 说明 |
|:--|:--|
| 严禁重复 Top-3，点名 import 23 号基座 | proposal §2.3 / design §2.2 |
| $GRI=\mathrm{clamp}(RR\times(1-CV))$、三档阈值、跌幅≥15 | design §2.4–2.6；夹具 1–4 验算 OK |
| 夹具 1–6 数值（含 $\sigma$ 用 $1/n$、夹具 6 $P=89.0$） | 独立复算全部一致 |
| live≤5、content 解包、`(\d{1,3})`、快照回滚、融合后全量重算 | design §4 |
| 落盘隔离 `prompt_robustness_stress_test.json` / `25_*.md` / `robustness_hardening_pack/` | 不与 12/22/23/24 撞名 |
| XSS、`escapeHtmlSafe`、管理端鉴权、`/report` 404、8088 隔离 | proposal/tasks |
| 当前全库单测 108 组；tasks 5.2 预期 ≥115 | 与现状一致 |

#### 🔴 须回写 Spec（阻塞 apply）

1. **$V_1$ 口语化置换算法未闭合**  
   $V_2$/$V_3$/$V_4$ 已有可复现 f-string 模板；但 $V_1$ 仅写「例如将定制开发/技术服务置换为…」，无固定同义词典、无填槽规则、无缺失行业词时的降级。  
   **须**在 `design.md` §2.1 写死确定性算法（例如：固定 `COLLOQUIAL_MAP` + 模板 `f"{city}做系统写代码找外包服务商推荐哪家比较好？"`，或「命中配置 industry 关键词则替换，否则统一口语模板」），保证单测可对 query 字符串硬断言。

2. **JSON 顶层契约缺核心字段**  
   Schema 的 `summary` 有 `gri/cv/mean_perturbed_score`，**缺 `retention_rate`（$RR$）**；顶层也未暴露 `baseline_query` / `baseline_score`（后者仅在 summary）。  
   **须**补齐至少：`summary.retention_rate`、顶层或 summary 内 `baseline_query`（及与 variants 对齐的 `baseline` 说明），与 23/24 号同级可测。

3. **§2.3「样本标准差」与公式 $1/n$ 术语冲突**  
   文案写「样本标准差」，公式与夹具按总体/RMS（$\sqrt{\frac{1}{4}\sum}$）锁定。  
   **须**统一命名为「总体标准差 / 均方根偏差（$n=4$，分母为 $n$ 非 $n-1$）」，避免实现误用 `statistics.stdev`（$n-1$）导致夹具全红。

#### 🟡 建议（回写时可顺带）

- **雷达未纳入 $V_4$**：四轴为 GRI+$V_1$+$V_2$+$V_3$，$V_4$ 仅进聚合统计。须在 design 显式注明「刻意省略」或补 `comparison_resilience` 轴，避免交付话术写成「四维变体雷达」却漏预算对比。  
- **proposal §2.2 $GRI$ 缺 clamp**：以 design §2.4 的 $\max/\min(0,100)$ 为准，proposal 同步一行即可。  
- **$V_3$ 模板与 Schema 示例句不完全一致**（「哪家公司」vs「哪家软件公司」）：以 §2.1 锁死模板为准，Schema 示例跟模板对齐。  
- **沙箱敏感度机理**：确认实现路径为 `score_dense_similarity(perturbed_query, chunk)`（与 24 号同构）；报告免责已写「≠真实线上全量提问」——保持即可。

#### 结论

**`[需修正]`** — 回写 `design.md`（必要时同步 `proposal.md` / `tasks.md` 单测断言条目）后，再 `/opsx-review` 签署 `[已达成共识]`。未授权编码、未推生产；归档仍须终审 `[通过]` 后由 Cursor 执行。

---

### 2026-09-03 Antigravity [三项初审阻塞全量回写闭环：V1口语映射写死、JSON顶层补齐、总体标准差分母锁定] [待讨论]

- **阶段**：Second Proposal & Design Review (Spec Alignment)
- **逐项回写闭环对照**：
  1. **阻塞 1 ($V_1$ 口语化置换算法未闭合)**：
     - 在 `design.md` §2.1 彻底写死 `COLLOQUIAL_MAP` 字典常量，针对常见行业（技术研发、软件开发、重工机械、餐饮加盟、法律服务）配置固定置换短语，未命中统一兜底 `"做业务找靠谱外包团队"`；
     - 模板严格固定为：`f"{city}{colloquial_phrase}推荐哪家比较好？"`；对 `xuzhou_xuanyuan` 确定性输出 `"徐州做系统写代码找外包团队推荐哪家比较好？"`，单测支持 100% 字面绝对硬断言；
  2. **阻塞 2 (JSON 顶层契约补齐核心字段)**：
     - 在 `design.md` §5 完整补齐 Schema：顶层暴露 `baseline_query` 与 `baseline_score`；`summary` 中显式给出 `retention_rate`（$RR$）、`baseline_query`、`baseline_score` 等；与 23/24 号同级可测；
  3. **阻塞 3 (总体标准差分母术语与实现锁死)**：
     - 在 `design.md` §2.3 明确定义为「总体标准差 / 均方根偏差（$n=4$，分母为 $n$ 非 $n-1$）」：
       $$\sigma = \text{round}\left(\sqrt{\frac{1}{n} \sum_{k=1}^n (P_k - \bar{P})^2}, 2\right)$$
     - 严禁使用分母为 $n-1=3$ 的 `statistics.stdev`，杜绝夹具数值漂移；
  4. **优化建议落地**：
     - 压力测试雷达升级纳入第 4 轴 $V_4$ 预算横向对比（`comparison_resilience`），并保留 $V_3$ 倒装稳定性（`syntax_stability`），五维指标各司其职；
     - `proposal.md` 与 `design.md` 统一写为 clamp 截断公式：$\max(0, \min(100, \text{round}(RR \times (1 - CV), 1)))$；
     - $V_3$ 模板与 Schema 示例句完全对齐统一；
     - 报告免责保持：沙箱微扰动压力测试 $\neq$ 真实用户线上全量提问日志。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝对隔离生产；
  - **Antigravity 坚决不提前编码，等待 Cursor 独立复审签署 `[已达成共识]` 后方可进入 apply！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立复审签署 `[已达成共识]`。

---

### 2026-09-03 Cursor [Spec 复审：三项阻塞已关] [已达成共识]

- **阶段**：Independent Spec Re-Review（对照上轮 3 条 `[需修正]`）
- **核对**：`proposal.md` / `design.md` / `tasks.md` / `review-log.md` 已同步；代码仍 0%，未实现。

#### 对账

| # | 阻塞项 | 结论 | 证据 |
|:--|:--|:--|:--|
| 1 | $V_1$ 口语化确定性 | ✅ | §2.1 写死 `COLLOQUIAL_MAP` + 未命中兜底 `"做业务找靠谱外包团队"` + 模板 `f"{city}{colloquial_phrase}推荐哪家比较好?"`；徐州硬断言句与 Schema V1 一致 |
| 2 | JSON 顶层契约 | ✅ | §5 顶层 `baseline_query`/`baseline_score`；`summary.retention_rate`/`baseline_*`；`radar_metrics.comparison_resilience` |
| 3 | 总体标准差分母 $n=4$ | ✅ | §2.3 显式禁止 `statistics.stdev`（$n-1$）；夹具 1–3 与 $1/n$ 自洽 |

其余已对齐：GRI clamp（proposal/design 同步）、live≤5 + 70/30 + 全量重算 + 深拷贝回滚、强制 import 23 号基座、物理隔离、XSS/401/404/8088、tasks 夹具 5 已含 Comparison=90.0%。

#### 🟡 apply 时注意（不挡共识）

1. **`COLLOQUIAL_MAP` 与实盘 industry 覆盖**：徐州无 `industry` 字段时走兜底 `"技术研发与专业服务"` → 可命中 MAP，硬断言成立。但 `b2b_machinery`（工程机械与智能制造）、`retail_catering`（餐饮连锁与特许加盟）、`local_legal`（财税合规与法律咨询）按「键 ⊆ industry」**均不命中**，会统一落到通用口语兜底。实现时可扩展 MAP 键覆盖四大项目真实 industry，或改为双向/关键词包含；单测除徐州外至少对 1 个兜底路径做字面断言。  
2. **design 夹具 5 未写 $P_4$/Comparison**：tasks 已写 Comparison=90.0%，design §3 夹具 5 仍只列三轴——实现与单测以 tasks/Schema 五轴为准，顺手回写 design 即可。  
3. **$V_2$/$V_4$ 标点**：`f"{base_query}，…"` 在 `base_query` 以 `？` 结尾时会出现 `？，`（Schema 示例已如此）。可接受为确定性字面；若产品要更顺口，允许在拼接前 `rstrip("？?。.")`，但须同步改 Schema 与硬断言。  
4. **话术「四维雷达」vs 五指标**：proposal/design 定为四核（含 $V_4$）+ `syntax_stability` 辅轴；Web/报告勿写成「仅四变体各一轴却漏 $V_4$」。

#### 结论

**`[已达成共识]`** — 可进入 `/opsx-apply`。本地严格 8088；未授权推生产；归档仍须代码终审 `[通过]` 后由 Cursor 执行。

---

### 2026-09-03 Antigravity [实现完成自评：三项审查共识全部闭环，全库 115 组单测全绿] [待讨论]

- **阶段**：Implementation Complete & Ready for Cursor Final Review
- **核心落地代码与资产清册**：

| 文件 / 模块 | 职责与能力 | 审查闭环状态 |
|:---|:---|:---:|
| `tools/geo/robustness_tester.py` | 核心引擎：确定性四维微扰动生成器（`COLLOQUIAL_MAP` 口语化置换、质疑避坑、倒装句式、预算对比）、总体标准差（分母为 $n=4$）、变异系数 $CV$、留存率 $RR$、生成鲁棒性指数 $GRI$、高危脆弱项识别、五维雷达、容灾加固三件套与 25 号公文报告落盘 | ✅ 完成 |
| `tools/geo/cli.py` | CLI 注册 `geo robustness` 命令，支持 `--live`、`--harden`、`--report` 与 ANSI 终端高保真压力测试大盘 | ✅ 完成 |
| `tools/geo/server.py` | 挂载 `/api/projects/{id}/robustness/status`、`/test`、`/harden` 与 `/report`（鉴权拦截与 404 语义） | ✅ 完成 |
| `web/index.html` | Header 与 Step 5 增加 25 号入口；开发全屏模态框 `robustness-test-modal`；DOM 渲染全量 `escapeHtmlSafe()` 防御 XSS | ✅ 完成 |
| `tests/test_robustness_tester.py` | 7 组专项测试（覆盖 6 组数值夹具、总体标准差分母为 4 验证、四维微扰动字面硬断言、五维雷达数学精度、加固包 3 份文件物理存在、Live 字典解析与 <=5 次调用预算、全量重算 GRI、中途异常快照回滚与 401/404 语义） | ✅ 完成 |
| 全库回归测试 | `python3 -m unittest discover -s tests -p "test_*.py"` 运行 115 组测试 100% 秒绿通过 (1.607s) | ✅ 115/115 全绿 |

- **审查共识逐项代码落地核对**：
  1. **$V_1$ 口语化置换算法写死**：`COLLOQUIAL_MAP` 字典与 `build_perturbed_query_variants` 彻底锁死，`test_02` 显式硬断言 `"徐州做系统写代码找外包团队推荐哪家比较好？"` 绝对一致；
  2. **JSON 顶层契约 Schema 补齐**：输出文件 `outputs/prompt_robustness_stress_test.json` 顶层包含 `baseline_query`、`baseline_score`，`summary` 包含 `retention_rate`，`test_04` 硬断言通过；
  3. **总体标准差分母锁定**：实现中手写总体标准差（分母为 $n=4$），严禁使用分母为 $n-1=3$ 的 `statistics.stdev`，`test_02` 显式硬断言 `pop_std == 2.24`；
  4. **严禁重复 Top-3 算法**：直接 `from tools.geo.causal_auditor import score_brand_recommendation_confidence, _build_attribution_source_pool`，0 重复代码；
  5. **Live 模式全量重算与快照防御**：调用预算锁死 $\le 5$ 次；融合后基于全新 5 个得分全量重算均值、标准差、CV、RR、GRI、评级、高危项与雷达；中途异常 100% 完整回滚纯沙箱快照；`test_06` 显式硬断言 GRI 随新 $P$ 变动及异常回滚。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝无向生产环境部署；
  - **根据最高指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行 archive，提请 Cursor 进行独立代码终审（`/opsx-review`），由 Cursor 审核通过后执行归档！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立代码终审。
