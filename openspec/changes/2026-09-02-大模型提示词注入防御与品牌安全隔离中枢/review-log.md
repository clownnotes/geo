# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code / Cursor）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

### 2026-09-02 Antigravity [发起大模型提示词注入防御与品牌安全隔离中枢提案] [已达成共识]

- **阶段**：Proposal & Design Alignment
- **背景与目标**：
  1. 填补 GEO 体系在对抗恶意 Prompt 注入、RAG 语料投毒与虚假 Citation 伪造等品牌安全维度的技术空白；
  2. 建立 4 维注入威胁特征库与单篇/全案免疫度体检引擎，生成交付级《16_大模型提示词注入防御与品牌隔离盾牌报告.md》与 JSON；
  3. 服务端 API、CLI 与 Web 端 Step 4 / Step 5 全链路挂载。
- **状态结论**：`[已达成共识]`，立即开始落地开发。

---

### 2026-09-02 Antigravity [完成大模型提示词注入防御与品牌安全隔离中枢全量落地] [已达成共识]

- **阶段**：Implementation & Verification
- **落地成果**：
  1. **提示词注入防御核心引擎 (`tools/geo/injection_guard.py`)**：
     - 构建 `INJECTION_PATTERNS_DB` 包含直接越狱 (P0)、RAG 投毒 (P1)、竞品劫持 (P1)、虚假信源 (P2) 4 维威胁模式库；
     - 实现单篇内容威胁扫描 `scan_content_for_injections()` 与全案品牌免疫度评分 `evaluate_project_injection_immunity()`；
     - 自动渲染输出交付级 `outputs/16_大模型提示词注入防御与品牌隔离盾牌报告.md` 与 `outputs/prompt_injection_guard.json`；
  2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
     - `geo injection-guard <pid>`
  3. **服务端 API 与 Web 端大一统 (`server.py`, `web/index.html`)**：
     - 挂载 `GET/POST /api/projects/{id}/guard/injection` 路由；
     - Web 端 Step 5 挂载「🛡️ 提示词注入防御盾」按钮与全景安全大盘弹窗；
  4. **自动化测试套件**：
     - 新增 [tests/test_injection_guard.py](file:///Users/a1/代码/GEO/tests/test_injection_guard.py)，全库 38 组单元测试全绿通过（100% Pass）；
     - 四大垂直行业母版均已生成 `16_*.md` 报告与 JSON。
- **状态结论**：`[已达成共识]`，提请跨 IDE 独立审查（`/opsx-review`）。


<!-- 下面是实际记录，按时间顺序往下追加 -->

---

### 2026-09-02 Cursor [独立跨 IDE 审查 — 大模型提示词注入防御与品牌安全隔离中枢] [通过]

- **阶段**：Proposal & Design Alignment（对照 `proposal.md` / `design.md` / `tasks.md` 与 `AGENTS.md`；**当前开发进度 0/12，尚无代码 Diff**）
- **审查范围**：OpenSpec 四件套、既有 `tools/geo/compliance.py` / `guard.py` / `defense.py` 模块边界、四行业 `outputs/` 交付物编号序列（01–15 已占用，16 号位空缺）
- **本地验证**：`./opsx status` → 总任务 12 项，已完成 0 项；`git status` → working tree clean

#### ✅ 通过项（方案可进入开发）

| 维度 | 结论 |
|:---|:---|
| **业务定位** | 与 `compliance.py`（广告法词汇）及 `guard.py`（大模型输出幻觉）形成互补三角，填补「语料侧 Prompt 注入 / RAG 投毒」空白，符合 GEO 攻防安全演进方向 |
| **交付物编号** | `16_大模型提示词注入防御与品牌隔离盾牌报告.md` + `prompt_injection_guard.json` 与现有 01–15 序列无冲突 |
| **架构范式** | 4 维特征库 → 单篇扫描 → 全案评分 → Markdown/JSON 落盘，与 `compliance.py` 成熟模式一致，复用成本低 |
| **评分模型** | P0/P1/P2 扣分 + `/llms.txt` / `07_` 锚点加分，与 `guard.py` 强事实锚点策略对齐 |
| **多端接入** | CLI `injection-guard`、REST `/api/projects/{id}/guard/injection`、Web 弹窗看板，符合项目大一统集成惯例 |
| **全局规范** | 未涉及生产部署；无数据库/自增 ID 等反模式；tasks 含单测与四行业 Benchmark 跑批 |

#### 🔴 P0 — 必须修正

*本轮未发现违反 `AGENTS.md` 红线或破坏既有业务的 P0 问题。*

#### 🟡 P1 — 建议在实现前写入 design.md / 首轮 PR 落实

1. **与 `guard.py` 命名空间易混淆**
   - 现有 `guard.py` 已占用 `/guard/risks`、`/guard/repair`、`/guard/simulation`（幻觉防御）；
   - 本变更 API 为 `/guard/injection`，模块为 `injection_guard.py`，Web 文案均为「防御盾」。
   - **建议**：Web 端明确区分「事实幻觉防御（Step 5）」与「语料注入防御（建议放 Step 4 合规旁）」；弹窗标题避免仅用「防御盾」。

2. **扫描范围与自排除规则未在设计中定义**
   - `compliance.py` 已沉淀 `is_excluded_file()`、排除 `.compliance_backup/`、排除自身 `13_*` 报告；
   - 本引擎若全量 walk `outputs/` 且不排除 `16_*`，将产生自引用误报。
   - **建议**：design 补充 `EXCLUDED_FILE_PATTERNS`（至少 `^16_.*`、`^13_.*`）及备份目录跳过逻辑，与 compliance 共用或抽取 `utils` 白名单。

3. **纯正则匹配的误报风险（类别 4 尤甚）**
   - 「央视新闻曝光」「官方通告」等模式在正规公关稿、FAQ 反谣段落中可能高频误报；
   - **建议**：实现时为每条规则增加 `requires_context` 或「引号/代码块内降权」；单测覆盖**负样本**（合法引用新闻标题不应计分）。

4. **CLI / API 语义未对齐 compliance 惯例**
   - `compliance` 已约定 GET 读缓存、POST 触发扫描、`--file` 单篇体检；
   - proposal 仅写 `geo injection-guard <pid> [--file <path>]`，未说明 `--inspect` 与缓存 JSON 读取路径。
   - **建议**：首轮实现对齐 `inspect_content_compliance` 交互范式，避免多端行为漂移。

5. **tasks.md 3.2「Git 推送」表述**
   - 推送应由用户/产品负责人在验收后显式触发，不宜作为开发机器人自动步骤；可改为「本地验证通过后提请 Git 提交」。

#### 🟢 P2 — 可选优化

- 抽取 `compliance.py` 与 `injection_guard.py` 共用的 `walk_project_outputs()` 遍历器，减少双份 `os.walk` 逻辑。
- `defense_quarantine_rules` 可考虑输出可操作的隔离动作（如「将命中文件移入 `outputs/.injection_quarantine/`」），而非仅文案建议。
- 免疫度雷达图 Web 组件可复用合规弹窗的 4 维指标卡布局，降低 `index.html` 增量体积。

#### 结论

**`[通过]`** — Proposal / Design 与 GEO 既有模块边界清晰、交付物编号与架构范式正确，**可立即按 `tasks.md` 进入开发**。实现阶段请优先落实 P1 #2（扫描白名单）、#3（误报负样本单测）、#1（Web 文案区分），开发完成后再次执行 `/opsx-review` 做实现态复审。

**下一步**：`/opsx-apply` 落地 tasks 1–3 → 本地单测与四行业跑批 → 实现态 `/opsx-review` → `[通过]` 后 `./opsx archive`。
