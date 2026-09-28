# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

### 2026-09-28 17:15 - 师兄 (Antigravity) 针对 Grill 深度盘问对齐
- **探讨阶段**：Grill 需求对齐与架构推演
- **结论标签**：`[已达成共识]`
- **背景与分歧梳理**：
  师弟在体验阶段一（01 诊断现状并出具报告）时，点击“真抓网络底座指标”后虽收到了成功 Toast，但右侧交付动线面板没有明确的后续状态指引，导致不清楚下一步该往哪走、该点哪个按钮。
- **方案决策裁决**：
  通过 `ask_question` 交互式对齐，双方达成最优解共识：
  1. 采用“动作完成态 + 主按钮视线引导”方案：抓取后按钮动态变更为“已抓取真实指标 (点击重新抓取)”，并呈现浅绿就绪态；
  2. 主推进按钮【确认完成，前往出具初稿 ->】增加柔和呼吸动效与小标签引导，直接拉取引导视线；
  3. Toast 提示文案显式指引“请核对中栏数据，核验后点击下方【前往出具初稿】”。
- **下一步行动**：
  OpenSpec 规范已全量落盘。根据 `/grill-me` 铁律，立刻立定停步，严禁偷跑修改业务代码。等待进入 `/opsx-review` 或 `/opsx-apply` 阶段。

---

## 2026-09-28 17:18 · 审查方（单 IDE 自审）· 第一轮：阶段一底座抓取动线引导优化

> **审查对象**：`proposal.md` / `design.md` / `tasks.md` / `review-log.md`（新变更，5 文件，全部**尚未纳入 git 跟踪**）
> **比对基准**：`AGENTS.md`（§3.3 / §3.5 / §4.5）、`openspec/config.yaml`、`web/step0-src/` 真实源码
> **动作边界**：本轮**未修改任何业务代码与规范文档**，仅追加本记录（另见 P2-2 的 git 固化建议）。

### 一、🔴 P0

#### 🔴 P0-1｜用户可见文案含**彩色 Emoji**，违反 `AGENTS.md` §3.3（严禁）
- **实测**（三处，且**全部是最终用户可见文案**，非文档措辞）：

| 位置 | 文案 |
| :--- | :--- |
| `proposal.md:10` | 「**✅** 真实底座指标已抓取！请核对中栏数据，确认无误后点击下方【前往出具初稿】」（Toast） |
| `design.md:13` | 「**👉** 指标已就绪，请核验后点击进入出初稿」（引导标签） |
| `design.md:39` | 「**👇** 数据已抓取就绪，请核对中栏并点击下方继续」（引导文案） |

- **冲突点**：`AGENTS.md` §3.3 原文 —— 「**严禁在企业级页面、交付打样站点、商业白皮书与报告中使用 Emoji 彩色表情符号**（如 ⚡️、💡、⚠️、⚙️、💻、🤝、💎、⚖️、🎓、💬 等）」；「视觉冲击力与层次感必须依靠高质感的排版层级、严谨的文字对比、微渐变/发光线框、数据加粗与专业 Tag 标签呈现，**坚决杜绝任何低幼玩具感**」。
- **加重项**：`design.md:39` 同时给了 `animate-bounce`（上下弹跳）——**弹跳 Emoji 标签正是 §3.3 点名的「低幼玩具感」**。§3.5 亦规定视觉须走「浅底（`-50`）+ `border-l-4` 侧彩条」这类克制手法。
- **影响**：交付端（对客打样页面）出现低幼感 Emoji，属**对客形象事故**，且违反项目最高协议。
- **订正建议**：
  1. 三处彩色 Emoji **全部删除**；Toast 若要强调成功，用文字前缀（如「已完成：」）或 Lucide 图标（组件已统一用 `data-lucide`）；
  2. 引导标签改为**静态文案**，保留 `design` 已提的 `animate-pulse`（柔和呼吸）即可，**去掉 `animate-bounce`**；
  3. 建议对端在落笔文案前跑一次 Emoji 自检：`grep -nE "✅|👉|👇|⚡|💡|⚠️|🚀|🎯" <变更目录>/*.md`。

#### 🔴 P0-2｜`design.md` 指定的持久化键**在代码中不存在**，照字面实现即静默失效
- **实测**：
  - `design.md:62` 写「在 `localStorage.getItem('nextgeo_step1_state_v1')` 的 JSON 中增加持久化字段 `crawledMetrics: boolean`」；
  - 真实键为 `web/step0-src/useStep1.js:12`：`` const storageKey = `geo_step1_state_${clientId}`; ``（读 `:18`、写 `:90` 均用它）；
  - 全仓检索 `nextgeo_step1_state_v1` → **仅命中 `design.md` 自身**（`grep -rn "nextgeo_step1_state_v1" --exclude-dir=node_modules .` 1 处）。
- **冲突点**：`nextgeo_` 前缀在整个仓库不存在；本变更能力 #4「**状态持久化与状态恢复**」的唯一技术锚点就是这个键名。
- **影响**：若实现者照字面写 `localStorage.getItem('nextgeo_step1_state_v1')`，`getItem` 恒返回 `null` → **新增字段永不落盘、刷新后回到未抓取态**，且**不报错**（极难定位）。与上一变更 P0-1（构建命令与产物名双错）属**同一类缺陷（文档写死了一个不存在的事实锚点）**。
- **订正建议**：改为「在 `useStep1.js:76 saveState()` 的 `stateToSave` 中增加字段 `crawledMetrics`（该函数已写入真实键 `` `geo_step1_state_${clientId}` ``）」——**描述"在哪个函数加字段"，而不是写死键名**，这样即使键名演化也不会再次失配。

### 二、🟡 P1

#### 🟡 P1-1｜「状态从 `useStep1` 传到 `StudioSop`」的**最后一跳无任何任务覆盖**（覆盖缺口）
- **实测**：`design.md` §1 给 `StudioSop` 新增 prop `actionCompletedMap`；§3 让 `useStep1` 产出 `crawledMetrics`；但**全篇没有任何一处说明由谁把两者接起来**。
- `Step1App.vue:49-58` 当前绑定为 `:stage-meta` / `:current-step` / `:gate` + 5 个事件，**没有 `:action-completed-map`**；而 `proposal.md` 的 Impact 清单只列了 `stage1Config.js` / `useStep1.js` / `StudioSop.vue`，**未列 `Step1App.vue`**。
- **影响**：照现文档施工，`actionCompletedMap` 恒为默认 `{}` → **动作完成态与主按钮呼吸高亮两个核心能力都不会出现**（本变更全部 What Changes 落空）。
- **订正建议**：① Impact 补 `GEO/web/step0-src/Step1App.vue`；② `tasks.md` 在 2.3 后增加一条「在 `Step1App.vue` 的 `<StudioSop>` 上绑定 `:action-completed-map="{ crawlMetrics: crawledMetrics }"`，并把 `crawledMetrics` 从 `useStep1()` 解构出来」。

#### 🟡 P1-2｜`tasks.md:14` 引用了**不存在的构建脚本**
- **实测**：`tasks.md:14` 写「在 NE1 服务器执行前端打包构建（**`sync_dev_mini.sh`** / Vite 构建）」；全仓检索 `sync_dev_mini` → **仅命中 `tasks.md` 自身**；`ls scripts/sync_dev_mini.sh` → **不存在**。
- **正确口径**（上一变更已订正过）：**仓库根**执行 `npm run build:step0`（= `npm --prefix web/step0-src run build`，产物 `web/assets/step0/step0.js` + `geo-step0-island.css`，由 `stamp-build.mjs` 打版本戳）。
- **另两点**：
  1. `tasks.md:4` 的「核对全局规则（编译上 NE1）」建议**直接引用 `AGENTS.md §4.5`**（本日新增、仓库内可 `grep`），不要再写"全局规则"这类无出处表述；
  2. 「确保无任何 TS/Vue 编译报错」需注意：**Vite/esbuild 只剥离类型、不做类型检查**，`npm run build:step0` 全绿**不能证明**类型安全。若确要类型保障，应显式补跑 `typecheck`（若项目有该脚本）。
- **订正建议**：`tasks.md:14` 改为「在 **NE1** 执行仓库根 `npm run build:step0`（见 `AGENTS.md §4.5`）」。

#### 🟡 P1-3｜**共享组件第三次被改**，缺「防污染边界」实现声明
- **实测**：`StudioSop.vue` 被 **`Step0App.vue:48` / `Step1App.vue:49` / `Step2App.vue:188` / `Step3App.vue:235` 四阶段共用**（本会话中它已是第三次被改动）。
- `design.md` 只给了新 prop 的声明（`actionCompletedMap: { type: Object, default: () => ({}) }` ✓ 默认值正确），但**未给出 `isActionDone()` 与 `shouldHighlightProceed()` 的实现**。
- **风险**：`shouldHighlightProceed(step)` 若只判断"该 step 的 action 是否已完成"、而不校验"是否为当前步骤 / 当前阶段"，会让**其它阶段的主推进按钮一并呼吸高亮**；`isActionDone()` 若不做空值安全（`step.action?.type` 可能为空），阶段 0/2/3 的部分卡片（无 `action`）会抛错。
- **订正建议**：`design.md` 补两个函数的实现，并明确：
  1. `isActionDone(type)` 必须 `if (!type) return false;` 且 `actionCompletedMap` 为空时恒 `false`；
  2. `shouldHighlightProceed(step)` 必须**同时**满足「该 step 的 `action.type` 在 map 中为 `true`」**且**「`step` 是当前步骤」；
  3. 补一句边界声明：「阶段 0/2/3 因不传 `actionCompletedMap`（取默认 `{}`）而保持**零变化**」。

### 三、🟢 P2

#### 🟢 P2-1｜归档遗留：上一变更**带着未勾任务**被归档
- **实测**：归档副本 `openspec/changes/archive/2026-09-28-出题草稿采纳流与动线操作白盒化/tasks.md:28` 仍为 `- [ ] 4.2 同步产物至 NE1 服务器并在 8088 端口端到端真机验收（**人工浏览器验收项…AI 不得代勾**）`，而提交 `e2c5467 chore(openspec): 归档…` 已把它移入 `archive/`。
- `ops-archive` 前置条件之一为「`tasks.md` 全部 `[x]`」→ **本次归档未满足该前置**。（4.2 未完成是**事实**，故归档内容本身诚实；但"归档 = 已完成"的语义被破坏。）
- **订正建议**：① 归档已冻结，**不得回改**；② 真机验收完成后，以**新变更**形式补做；③ 建议在下一变更的 `review-log.md` 里显式登记该承接项（"上一变更 4.2 真机验收待补"），避免随归档沉没。

#### 🟢 P2-2｜新变更目录**未纳入 git 跟踪**（高危，建议立即固化）
- **实测**：`git status --short` → `?? openspec/changes/2026-09-28-阶段一底座抓取动线视线引导优化/`，**5 个文件全部未跟踪**。
- **风险**：按 2026-09-27 事故教训（多 IDE 同开时未跟踪文件被删除后 git 无法找回），本目录随时可能丢失。
- **订正建议**：**立即 `git add` + `git commit` 固化基线**（不改内容，仅纳管）。

#### 🟢 P2-3｜新变更文档格式与项目既有惯例不符（三处小项）
1. `review-log.md` **没有任何 `## ` 二级标题**（现有记录用的是 `### `），而文件自身三条规则要求"每条写明时间 / 谁写的 / 针对哪个阶段"；实测 `grep -cE "^## " review-log.md` = **0** —— 这会让"章节行号严格递增"这类自检失效。
2. `tasks.md` 缺 `# Tasks: …` 标题（上一变更的 `tasks.md` 有）。
3. `proposal.md` 标题写作 `# Proposal: 2026-09-28-阶段一底座抓取动线视线引导优化`（含日期前缀），与上一变更 `# Proposal: 出题草稿采纳流与动线操作白盒化`（不含日期）风格不一致。
- **订正建议**：统一为 `## 时间 · 作者 · 阶段` 二级标题；`tasks.md` 补 `# Tasks: …` 标题。

### 四、已核对**无问题**的事项（避免下一轮误报）

| 核对项 | 实测 | 结论 |
| :--- | :--- | :--- |
| `proposal` 引述的现状 Toast 文案 | `useStep1.js:196` `showStudioToast('网络底座指标抓取完毕，请与客户对照核实')` | ✅ **逐字一致** |
| `stage1Config.js` 第 1 步 action | `:283` `{ label: '真抓网络底座指标', icon: 'activity', type: 'crawlMetrics' }` | ✅ 与 design 一致 |
| `useStep1` 相关符号 | `:193 handleAction(actionType)`、`:194 crawlMetrics` 分支、`:76 saveState()`、`:15 savedState` | ✅ 均存在 |
| `nextLabel` 文案 | `:291` `'确认完成，前往出具初稿'`（proposal 写作「…出具初稿 ->」，箭头实为 Lucide `arrow-right` 图标） | ✅ 实质一致，仅描述性差异 |
| design 用翠绿表达"动作已完成" | `bg-emerald-50 text-emerald-700 border-emerald-200` 与 `StudioSop.vue:46` 既有「**已完成**」徽章**逐字相同** | ✅ **属沿用组件既有语义，不是 §3.5 四色令牌违规**（上一变更"已采纳徽章改绿"才是违规，那次已回退主色紫）。**本轮不重复提该问题。** |

### 五、本轮结论

- **审查标签**：`[需修正]` —— **2 项 🔴**（Emoji 违规 / 持久化键不存在）+ **3 项 🟡**（事件最后一跳缺覆盖 / 构建脚本不存在 / 共享组件缺边界声明）+ **3 项 🟢**（归档遗留 / 目录未纳管 / 文档格式）。
- **最要紧的一条**：P1-1 是"功能根本不会生效"的缺口 —— 现文档没有任何任务把 `crawledMetrics` 接到 `StudioSop`，照做会得到"改了三个文件但界面毫无变化"。
- **本轮动作边界**：仅追加本记录，**未改动任何业务代码与规范文档**，未执行构建、未向 NE1 部署。
- **下一步**：等待师兄裁决，不擅自进入 apply。

### 附：本轮实测证据索引

| 核对项 | 命令 / 路径 | 结果 |
| :--- | :--- | :--- |
| 彩色 Emoji | `grep -rnoE "✅\|👉\|👇" <变更目录>`（实际用 `-E`） | `design.md:13 👉` / `design.md:39 👇` / `proposal.md:10 ✅` |
| 持久化键真伪 | `grep -rn "nextgeo_step1_state_v1" --exclude-dir=node_modules .` | **仅 design.md 自身**（真实键见 `useStep1.js:12`） |
| 真实存储键 | `useStep1.js:12` | `` `geo_step1_state_${clientId}` `` |
| 构建脚本真伪 | `grep -rn "sync_dev_mini" --exclude-dir=node_modules .` / `ls scripts/sync_dev_mini.sh` | 仅 tasks.md 自身 / **不存在** |
| `StudioSop` 共用方 | Grep `StudioSop` `*.vue` | Step0App:48 / Step1App:49 / Step2App:188 / Step3App:235（**4 处**） |
| `Step1App` 现有绑定 | `Step1App.vue:49-58` | 无 `:action-completed-map` |
| 既有翠绿语义 | `StudioSop.vue:46` | `'text-emerald-700 bg-emerald-50 border border-emerald-200'`（已完成徽章） |
| 现状 Toast 文案 | `useStep1.js:196` | 与 proposal 引述逐字一致 |
| 归档是否带未勾任务 | `archive/…/tasks.md:28` | 仍 `- [ ] 4.2 …` |
| 新目录 git 跟踪状态 | `git status --short` | `??`（**未跟踪**） |
| `review-log` 二级标题数 | `grep -cE "^## " review-log.md` | **0** |
| 未推送提交 | `git rev-list --count origin/main..main` | **27** |
| NE1 现场 | `ssh mini` | `f1db08a` / 脏 **62** |

结论：`[需修正]`
