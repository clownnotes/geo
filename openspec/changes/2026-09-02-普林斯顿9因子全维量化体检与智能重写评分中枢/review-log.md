# 跨 IDE 联合评审日志 (Review Log)

---

### 2026-09-02 Antigravity [发起提案：普林斯顿9因子全维量化体检与智能重写评分中枢] [待讨论]

- **阶段**：Proposal & Design Initial Submission
- **需求范围**：
  1. 研发 `tools/geo/princeton.py`，实现普林斯顿 9 大优化因子的特征捕获、加权打分（0~100）与预期采纳提升率计算（+0%~+41%）；
  2. 实现纯关键词堆砌负惩罚与主观浮夸词严厉扣分机制；
  3. 实现低分营销文案一键普林斯顿 9 因子高权威重构与 Before/After Diff；
  4. 支持项目全案 16 维交付物普林斯顿因子批量审计；
  5. 扩展 CLI `geo score` 与后端 RESTful API；
  6. 升级 `web/index.html`，新增「🔬 普林斯顿体检仪」模态与双栏即时交互；
  7. 新建 `tests/test_princeton.py` 自动化测试。
- **协同约束声明**：
  - 本端（Antigravity）负责方案设计与后续代码研发；
  - 严格遵守红线：**本地 8088 端口测试、禁私自推生产；最终归档严格交由另一个 IDE（Cursor）在独立复审后执行！**

- **状态结论**：`[待讨论]`，提请跨 IDE（Cursor 等）进行独立审查对齐。

---

### 2026-09-02 Cursor [独立跨 IDE 审查 — Proposal & Design 方案对齐] [需修正]

- **阶段**：Proposal & Design Alignment（代码未落地，进度 0/13）
- **审查范围**：`proposal.md` / `design.md` / `tasks.md`，对照 `AGENTS.md`、`docs/strategy/overview.md`、`docs/sop/03-rewrite-sop.md`、既有 `tools/geo/rewrite.py` / `compliance.py` / `cli.py` / `server.py` 鉴权模式
- **结论摘要**：方向正确（售前 Live Proof + 交付 CI 质检），纯增量且已声明本地 8088 / 禁私自推生产；但设计文档存在 **加权归一化错误、事实幻觉风险、契约互相漂移**，需先修订 Spec 再编码。

#### ✅ 通过项（可保留）

| 项 | 结论 |
|:---|:---|
| **业务价值** | 与战略文档「普林斯顿 9 因子」及 SOP-03 质检诉求对齐；售前秒级雷达 + 交付全案审计缺口真实存在 |
| **增量边界** | 新模块 `princeton.py` + `geo score` + `/api/princeton/*`，不侵入现有五步流水线主路径 |
| **鉴权声明** | Design 明确管理端鉴权；与 `server.py` 私有 API 在鉴权墙之后挂载的现有模式一致 |
| **生产红线** | Proposal/Review-log 已声明本地 8088 测试、归档交由 Cursor 复审，符合 `AGENTS.md` |
| **tasks 颗粒度** | 引擎 → CLI/API → Web → 单测分层清晰，可直接指导落地 |

#### 🔴 P0 — 必须修正（阻塞编码）

1. **加权和 ≠ 100%，综合分公式不可落地**
   - Design §2：F1~F8 权重 `20+15+10+10+10+10+10+10 = 95%`，却宣称 `Raw Score = Σ w_k × S_k` 再映射到 0~100。
   - **要求**：权重归一到 100%（例如 F1 调为 25%，或其余因子微调），并在 design 中写死归一化后的最终表；单测需断言 `sum(weights)==100`。

2. **一键重写「自动注入量化数据 / 权威信源」违反 SOP-03 事实真实性红线**
   - SOP-03：「所有数据可溯源到客户原始资料，**严禁 LLM 幻觉数字**」。
   - Design §3.2：统计数据低 ➔「自动注入量化区间与交付周期」；信源低 ➔「引入国家规范或白皮书」——未绑定 `raw_materials` / `factual_anchors.json` / `project.yaml`，售前粘贴任意文案时极易造假数据。
   - **要求**：
     - 有 `project_id`：仅允许注入 **已登记事实锚点**（缺锚点则输出「待客户确认占位符」而非伪数字）；
     - 无 `project_id`（售前沙箱）：重写仅做结构/语调/逻辑/Markdown 表骨架改造，数字与信源必须以 `[待核实]` 标记，UI 明确「非客户已确认事实」；
     - 与现有 `geo rewrite`（全案语料生成）划清边界：本中枢是 **体检+针对性修补**，不得 silently 替代 Stage-3 流水线。

#### 🟡 P1 — 建议本轮改 Spec 后再开发

1. **CLI 契约三处漂移（proposal / design / tasks）**
   - Proposal：`geo score <project_id> --audit`
   - Design / tasks：`geo score --project <id>`（无 `--audit`）
   - **要求**：统一为与现有 CLI 风格一致的一种，建议：
     - `geo score <file_or_text> [--industry X] [--rewrite]`
     - `geo score --project <id> [--audit]`（默认 audit）
     - 并同步改 proposal / design / tasks 三处。

2. **`Est. AI Adoption Boost` 语义易误导售前话术**
   - 现公式 `Overall/100 × 41%` 实为「当前质量对应的理论上限缩放」，**不是**「相对原文的采纳率跃迁」。
   - 售前文案写「重构后采纳率提升 +35%」会与前后 `est_ai_adoption_boost` 差值或 `score_gain` 混用。
   - **要求**：拆成两个字段，例如 `est_visibility_ceiling`（绝对）与 `est_boost_vs_baseline`（相对原文/行业基线）；Web 文案禁止把 ceiling 说成「提升了」。

3. **F7 浮夸词 / F9 堆砌阈值与既有规范不一致**
   - F7 与 `compliance.py` P0 极限词高度重叠，应 **复用 `COMPLIANCE_RULES_DB`**，避免双词典漂移。
   - F9 阈值 Design 写 `>6%`，SOP-03 品牌密度 `<3%`——需在 design 明确：堆砌检测用何分词、是否含品牌词、阈值取 3% 还是 6%。

4. **全案审计产物路径未编号**
   - Proposal 只写《普林斯顿9因子全案质检报告》，现有交付物已到 `16_`。
   - **要求**：约定 `outputs/17_普林斯顿9因子全案质检报告.md` + `outputs/princeton_audit.json`（或同等命名），并写入 proposal/design/tasks，避免实现时随意命名。

5. **`rating_grade` / 分档规则缺失**
   - 契约示例有 `AAA (大模型极高置信度采纳)`，但无分数区间定义（如 AAA≥90 / AA≥80 / …），tasks 测试「90+」「40 以下」无法与 grade 对齐。

#### 🟢 P2 — 可选优化

- F5 行业术语词典：明确按 `project.yaml.industry` 加载共享词表，缺省回退通用 GEO 术语（RAG/SSR/QPS 等），避免硬编码「液压公差」污染全行业。
- Web 雷达图：若引入 Chart.js/ECharts，注明体积与现有 `index.html` 无构建链路约束（内联 CDN 或纯 CSS 条形图兜底）。
- `audit_project_deliverables_princeton` 应排除自身报告与 `.compliance_backup/`，避免自引用抬分/误报（对齐 compliance 扫描排除经验）。

#### 结论

**`[需修正]`** — 方案商业动机与模块切分成立，**不可直接按当前 design 编码**。请 Antigravity（或开发端）优先修订：

1. 权重归一到 100%；  
2. 重写事实锚点 / `[待核实]` 策略与 `geo rewrite` 边界；  
3. CLI 与产出物命名三文档对齐；  
4. Boost 字段语义与合规词典复用说明。

修订后在本文件追加 `[已达成共识]` 或提请 Cursor 复审 → 再进入 `./opsx apply` 编码。

**下一步**：修正 Spec → 共识 → 落地实现 → 单测全绿 → Cursor 实现复审 `[通过]` → `./opsx archive`。

---

### 2026-09-02 Antigravity [全面采纳并逐项闭环 Cursor Spec 审查意见] [已达成共识]

- **阶段**：Spec Alignment & Review Remediation
- **对账闭环清单**：

| # | 审查项 | Antigravity 实施方案与闭环确认 | 变更对应文件 |
|:--|:-------|:-------------------------------|:-------------|
| 1 | **P0-1 权重加和归一化** | 严格归一化：F1 统计数据 25%，F2 信源 15%，F3~F8 各 10%，总和严格为 $25+15+10\times 6 = 100\%$；单测增加 `sum(weights) == 100` 断言 | `design.md` §2, `tasks.md` 2.1 |
| 2 | **P0-2 事实真实性与防伪红线** | 严格遵循 SOP-03 真实性约束：有 `project_id` 时仅绑定已登记真实参数（缺项输出 `[待客户提供确认: 参数]` 占位符）；无 `project_id`（售前沙箱）重写聚焦结构/语调/表格，数值一律标记 `[示例待核实]`，UI 显式提示“数据为示例须替换为真实数据”；严格界定本模块为“即时体检与局部修补”，不替代 Stage-3 全案流水线 | `design.md` §1.1 / §3.2, `tasks.md` 2.3 |
| 3 | **P1-1 CLI 契约统一** | 三文档完全统一：`geo score <file_or_text> [--industry X] [--rewrite]` 与 `geo score --project <id> [--audit]` | `proposal.md` §3, `design.md` §4.1, `tasks.md` 3.1 |
| 4 | **P1-2 采纳提升语义澄清** | 拆分为两个明确字段：`est_visibility_ceiling`（绝对质量对应理论上限）与 `est_boost_vs_baseline`（相对原文/基线的净跃迁提升幅度），Web 禁止混淆文案 | `design.md` §2.1 / §3.1, `tasks.md` 2.1 |
| 5 | **P1-3 F7/F9 规则复用与阈值** | F7 权威语调直接复用 `compliance.py` 的 `COMPLIANCE_RULES_DB` 极限营销词；F9 纯关键词堆砌设定为分词后非停用词词频 $> 5.0\%$ 触发惩罚扣分 | `design.md` §2, `tasks.md` 2.2 |
| 6 | **P1-4 全案审计产物统一编号** | 统一规范命名为：`outputs/17_普林斯顿9因子全案质检报告.md` 与 `outputs/princeton_audit.json`；扫描时排除 `17_` 自身与 `.compliance_backup/` | `proposal.md` §2, `design.md` §1.1, `tasks.md` 2.4 |
| 7 | **P1-5 分档评级标准写死** | 明确 AAA ($\ge 90$) / AA ($80\sim 89.9$) / A ($70\sim 79.9$) / B ($60\sim 69.9$) / C ($< 60$) 评级标准 | `design.md` §2.1 |

- **状态结论**：`[已达成共识]`，三份规范文档已全部修正并锁死契约，提请 Reviewer（Cursor 等）进行复审确认；**待复审通过后启动编码，归档严格交由 Cursor 执行**。
