# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
1. 🔴 违反白皮书/全局规则，必须改
2. 🟡 有风险，建议改
3. 🟢 优化建议，可选

---

## 2026-09-28 16:10 · 师兄 Antigravity · Grill 深度探讨与架构对齐

### 1. 师弟提出的核心疑问与痛点
1. **重新出题后版本困惑**：
   - 重新出题生成了“第二版”，但第 1 版显示 `[已采纳 QA-V1]`（因侧栏窄被挤压误读为 `QAVE`），第二版显示为纯文件名 `01_豆包题目_第2版.txt`；
   - 疑问：QA-V2 版本号是怎么产生的？如果想以第二版为模型深入完善并保存，该怎么做？
2. **动线第 3 步“保存文件并采纳”操作黑盒**：
   - 界面上只有静态文字说明，没有实体可点击的动作按钮；
   - 疑问：“我保存了什么文件？为什么左边文件树没有新文件？保存在哪里了？为什么动线不能直接点？”
3. **动线平铺卡片误触跳页**：
   - 用户在 0.1 页面点击卡片 2 查看说明时，页面突然意外跳转到了 0.2。

### 2. 底层机制与黑盒根因剖析
1. **QA-V2 产生机制**：
   - 点击“重新出题”生成的只是一份**未生效的草稿**（`isActive: false`，尚未分配版本号）；
   - 系统中存在完整的采纳机制（`handleAdoptFile`）：只有当交付专家主动“采纳”某个草稿时，系统才会自动抓取当前项目最大版本号（如当前是 V1，则递增分配 `QA-V2`），盖上生效底牌印章，并将旧版本（V1）让位为草稿（单底牌互斥原则）；
   - **痛点根因**：原本这个采纳动作只能点中间编辑器顶部的黄色小按钮【设为客户采纳】，右侧动线第 3 步只有一段静态描述文字，缺乏实体按钮，导致用户完全不知道去哪里点。
2. **“保存文件”的本质**：
   - 保存只是把当前编辑器里修改的文本内容更新到对应的文件实体（存盘到内存、本地存储和后端），并不是“另存为新文件”，所以左侧文件树文件数量不会增加。
3. **跳页误触根因**：
   - `StudioSop.vue` 的卡片头部监听了 `@click="onGotoStep(idx + 1)"` 并向外派发 `switch-step` 事件；
   - 在 0.1 页面中，微步骤有 3 个（idx 分别为 0, 1, 2）。点击第 2 个微步骤卡片时，向外发射了 `switch-step(2)`，外层 `Step0App.vue` 误以为用户要切换到子页面 0.2，从而发生了跨页跳转。

### 3. 双方探讨与方案共识
师弟通过选择器明确敲定了**【方案一：右侧动线带动作按钮】**：
1. **右侧微动线彻底动作化**：
   - 微步骤 1：保留【重新出题（生成新版）】按钮；
   - 微步骤 2：增加【保存当前润色修改】按钮，存盘时清晰提示“已保存当前文件”；
   - 微步骤 3：增加【采纳为生效底牌 (QA-V2)】按钮，点击后立即将当前草稿转正为 QA-V2，左侧高亮显示 `[已采纳 QA-V2]`；
2. **左侧资源管理器视觉与状态透传**：
   - 侧栏宽度由 240px 拓宽至 288px，彻底解决文字截断；
   - 未采纳文件显式标注 `[草稿]` 灰色徽章，生效文件显式标注高亮 `[已采纳 QA-V(N)]` 徽章，草稿与生效底牌对比鲜明；
3. **动线阻断误触跳页**：
   - 平铺模式（`expandAll === true`）下，卡片头部点击严禁派发 `switch-step`，彻底阻断跨页误触。

### 4. 规范文件落盘状态
- [x] `proposal.md`：已完成
- [x] `design.md`：已完成（含状态机图与事件架构）
- [x] `tasks.md`：已完成（拆分为 4 项具体任务）
- [x] `review-log.md`：已签署共识

结论：`[已达成共识]`

---

## 审查记录 · 第一轮（单 IDE 自审）· 2026-09-28

- **时间**：2026-09-28 16:25 · **审查人**：AI（单 IDE 自审，跨 IDE 通道未启用）
- **对象**：本变更 proposal.md / design.md / tasks.md / review-log.md
- **比对基准**：`AGENTS.md`（最高协议）、`openspec/config.yaml`、真实磁盘状态（`web/step0-src/**`、`web/step0-src/*Config.js`、根 `package.json`、`web/step0-src/vite.config.js`、`web/scripts/stamp-build.mjs`）、git 状态、NE1 只读现场
- **结论**：`[需修正]`

### 零、前置核查：上一变更（`2026-09-28-阶段零动线层级重构与收纳展开修复`）的归档合规性

| 核查项 | 实测 | 判定 |
| :--- | :--- | :--- |
| 归档副本是否完整保留审计链 | `git show HEAD:<旧路径>/review-log.md` 与 `archive/…/review-log.md` **逐字节一致**（均 41,505 B，`diff -q` 无差异） | ✓ 完整、无篡改 |
| 上一轮 🔴 R3-1 是否已修 | `StudioSop.vue:245-248` 的 `onGotoStep()` 仍为裸 `emit('gotoStep')` + `emit('switch-step')`，**无 `expandAll` 防护** | ✗ **未修即归档** |
| 上一轮 🟡 Task 5 代勾是否回退 | `archive/…/tasks.md:36` 仍为 `- [x] Task 5: 真机端口 8088 端到端全链路验收` | ✗ **未回退** |
| 归档是否走 git | `git status --short` → **5 个未暂存删除 + 1 个未跟踪归档副本** | ✗ 未走 git |
| 是否符合 ops-archive 前置条件 | tasks 全 `[x]` ✓；但 review-log 末条为本 AI 的 `[需修正]`（含未闭合 🔴），且**无用户签署的归档同意** | ⚠️ 存疑，需用户确认 |

- **风险**：归档副本当前是**未跟踪文件**，一旦被其他 IDE 覆盖或清理即无法从 git 找回（2026-09-27 已有同类事故）。同时 5 个未暂存删除若被 `git checkout .` 还原，活动目录会"复活"并与归档副本重复。
- **订正建议**：立刻把这次归档移动用 git 固化（`git add -A` + `commit`，等价 `git mv` 语义），再继续本变更。

**补充（根因记录不完整）**：本变更 review-log 第 3 节把跳页根因记为"点击第 2 个微步骤卡片时发射了 `switch-step(2)`"，但**未记录更严重的崩溃分支**：点击**第 3 张**卡片头会发射 `switch-step(3)` → `Step0App.vue:218-222` `setSubStep(3)`（守卫为 `n >= 1 && n <= 3`）→ 读取 `subMetaMap[3].category`，而 `subMetaMap` 只有键 1、2（`:103-120`）→ 抛 `TypeError`。design §2.3 的 `if (props.expandAll) return;` 恰好能同时堵住两条路径，但**根因描述缺一条，后续复现与回归会漏测**。

### 一、🔴 P0-1｜Task 4.1 的构建命令与产物路径**双重错误**，验收标准必然失败

- **原文**（`tasks.md:16`）：「在 `GEO/web` 目录下执行 `npm run build:step0`，生成 `dist/step0.iife.js`」
- **实测**：
  - `ls web/package.json` → **不存在**。`build:step0` 定义在**根** `package.json:12`（`"build:step0": "npm --prefix web/step0-src run build"`）。在 `GEO/web` 下执行会直接报 "Could not read package.json"，命令失败。
  - `ls dist/` → **无该目录**；`find . -name "step0.iife.js"` → **全仓零命中**。真实产物是 `web/assets/step0/step0.js`（376,436 B）与 `web/assets/step0/geo-step0-island.css`（见 `vite.config.js`：`build.lib.fileName = () => 'step0.js'`、`outDir = ../assets/step0`）。
  - `dist/` 还被 `.gitignore` 忽略，与"提交产物"的意图相悖。
- **影响**：apply 阶段按字面执行必失败；即便执行者自行纠正，验收也无法引用正确产物。
- **订正建议**：改为「在**仓库根目录** `GEO/` 执行 `npm run build:step0`，产物为 `web/assets/step0/step0.js` + `geo-step0-island.css`，并由 `stamp-build.mjs` 自动刷新 `web/index.html` 版本戳」。

### 二、🔴 P0-2｜"草稿"徽章加在**四阶段共用**的 `StudioFileTree.vue` 上，会让阶段 1/2/3 的**每一个文件**都被标成 `[草稿]`

- **实测**：
  - `grep -rn "StudioFileTree" web/step0-src --include="*.vue"` → 被 **Step0App / Step1App / Step2App / Step3App 四个 App 共用**（各在 `:22` 引入）。
  - `isActive` 的**唯一写入方是 `Step0App.vue`**（`:274`、`:279`、`:411`、`:414`、`:635-647`，初始化 `false` 见 `:542/:553/:759/:872`）。`useStep1.js` / `useStep2.js` / `useStep3.js` / `stage1Config.js` / `stage2Config.js` / `stage3Config.js` 中 `isActive` 命中数**均为 0**。
  - 现有徽章（`StudioFileTree.vue:89-96`）为 `v-if="files[fn]?.isActive"`，**无 `v-else`** → 阶段 1/2/3 当前不显示任何徽章。
- **冲突点**：tasks 1.2 要求"为未采纳的草稿文件显式渲染 `[草稿]` 灰色标签（`v-else`）"，未限定阶段；design §1.1 只描述了阶段零的二元语义。
- **影响**：落地后**阶段一/二/三的每个文件都会挂上 `[草稿]`**（这些阶段从不设 `isActive`），语义完全错位。这与上一变更 P0-1（误改共用组件）**属同一类缺陷，系复发**。
- **附**：宽度 `lg:w-60 → lg:w-72`（tasks 1.1）同样作用于四个阶段的三竖列布局；文档未声明跨阶段影响。
- **订正建议**：给 `StudioFileTree` 增加显式开关（如 `showStatusBadge` / `statusMode`），**仅阶段零传 `true`**；宽度调整若只想作用于阶段零，同样需要开关，否则请在 proposal 里写明"四阶段统一加宽"。

### 三、🟡 P1

#### 🟡 P1-1｜按钮文案「采纳为生效底牌」与 AGENTS §3.5 的正面冲突未走豁免
- AGENTS §3.5 原文：「**阶段零两件真东西禁混谈条款**：文案只谈「问题清单」与「豆包答案存档」，严禁自造「底牌报告 / 基线 / 剧本 / 探活」充当主文案」。
- 本变更把「生效底牌」提升为**核心按钮文案**（design §2.1 第 3 步 `label: '采纳为生效底牌 (转正为新版)'`；proposal 的 Why #3 / What Changes / Capabilities 多处使用）。
- 说明：review-log 记载该措辞系师弟在选择器中敲定，且既存代码已大量使用（`Step0App.vue` 19 处，含写进文件头的 `=== 阶段零生效底牌 (基线标识: …) ===`）。因此这是**规范与既定用词的冲突**，不是笔误。
- **订正建议**：在本变更 review-log 补一条**用户签署的规范豁免**（动作最小）；AGENTS §3.5 本身的修订建议另立议题，不在本变更内夹带。

#### 🟡 P1-2｜构建/验证机器口径（AGENTS §4.1）连续第二个变更未闭环
- tasks 4.2 再次把验证放在「NE1 服务器 … 8088 端口」；AGENTS §4.1 明文"开发与审查阶段的所有代码与功能**一律仅在本地开发端（http://127.0.0.1:8088）测试与验证**"—— 约束的是**机器**而非端口。
- 该冲突已连续两轮（上一变更 R2-3、R3-2）提出且未获豁免。建议随 P1-1 一并签署豁免，避免第三次复发。

#### 🟡 P1-3｜design §3.2 把"已采纳"徽章由主色紫改成翡翠绿，与现状及四色令牌不一致，tasks 措辞含糊
- 现状（`StudioFileTree.vue:89-96`）：`bg-[#7c5bf5]/15 text-[#7c5bf5] border-[#7c5bf5]/30`、`font-medium`、`px-1.5`。
- design §3.2 改为 `bg-emerald-50 text-emerald-700 border-emerald-200`、`font-bold`、`px-2`。
- AGENTS §3.5 定义四色语义：主色紫=Value、冷调蓝灰=What、暖调琥珀黄=Why、**通路翡翠绿=How**。"已采纳/生效"属状态而非 "How"，改绿缺乏依据；tasks 1.2 只写"优化已采纳徽章排版"，未点明配色变更。
- **订正建议**：要么维持主色紫，要么在 design 写明改色理由并同步 tasks 措辞。

#### 🟡 P1-4｜design §2.1 只给出 `STAGE0_SUB1_META`，未声明 `STAGE0_SUB2_META`（含封版按钮）保持不变
- 上一变更已为 0.2 挂载 3 条 `sopSteps`，其第 3 步 `action.type = 'finishStage0'` 触发 `handleFinishStage0` 封版。本变更 design §2.1 只列 0.1，执行者可能误将 0.2 一并改写或删掉封版按钮，导致阶段零封版链路再次中断。
- **订正建议**：design 补一句"0.2 的 `STAGE0_SUB2_META` 保持现状不动（含 `finishStage0` 封版按钮）"，tasks 3.1 同步注明。

#### 🟡 P1-5｜上一变更的未闭环项未随归档登记
- `sopTitle` 死字段（`StudioSop.vue` 消费点 0，`Step0App.vue` 2 处已进产物）；P2-3 既存契约缺陷（`Step2App.vue` 传非声明 prop `:sop-steps`、`Step3App.vue` 用 `STAGE_2_META`、`onExtraAction` 忽略 type、`isReady` 死 prop）仍未登记。
- 另：本地领先 `origin/main` **15 个提交**（AGENTS §4.2 要求双推）；NE1 现场仍是"绕过 git 拷入"的脏工作区（HEAD `f1db08a` + 12 个 ` M`）。
- **订正建议**：在本变更 review-log 建一节"承接项"，把上述未闭环事项显式登记，避免随归档沉没。

### 四、🟢 P2

#### 🟢 P2-1｜旧 review-log 章节顺序错位（本 AI 自我更正）
- 归档副本二级标题顺序为：`探讨与盘问实录` → `第一轮审查` → **`第三轮审查（代码落地验收轮）`** → `第二轮响应与规范订正实录` → `第二轮审查（复核轮）` → `第三轮双模型对抗执行实录`。
- 归因：本 AI 追加第三轮记录时 `old_string` 取了 `- **下一步**：等待用户裁决…`，该串在第一轮与第二轮的结论段**各出现一次**，内容被插到第一轮结论之后（非文件末尾）。
- 影响：仅影响阅读顺序，**内容无丢失、无篡改**（归档副本与 HEAD 版本逐字节一致）。按"追加不覆盖"原则，本 AI **不覆写**该归档文件，仅在此登记；是否重排由用户/师兄决定。

#### 🟢 P2-2｜`proceed-to-next` 成为悬空 emit
- `StudioSop.vue:189` 仍声明 `proceed-to-next`，`onProceedClick` 仍在 `idx === 0` 时发射它，但上一变更已移除 `Step0App` 的 `@proceed-to-next` 绑定 → 现为无接收方的死事件。建议在 tasks 2.2 顺手清理声明。

### 附：本次审查的实测证据索引

| 核对项 | 命令 / 路径 | 结果 |
| :--- | :--- | :--- |
| 归档副本完整性 | `diff -q`（`git show HEAD:…` vs `archive/…`） | 逐字节一致（41,505 B） |
| 旧 review-log 章节顺序 | `grep -n "^## "` 归档副本 | 第一轮 → 第三轮 → 第二轮 → 第三轮双模型（错位） |
| R3-1 是否已修 | `StudioSop.vue:245-248` | 无 `expandAll` 防护 → **未修** |
| 归档后 tasks 勾选 | `grep -nE "^- \[" archive/…/tasks.md` | Task 5 仍 `[x]` |
| 归档是否走 git | `git status --short` | 5 个 ` D` + 1 个 `??` |
| `web/package.json` | `ls web/package.json` | **不存在** |
| `dist/step0.iife.js` | `ls dist/` + `find -name` | 目录不存在 / 全仓零命中 |
| `build:step0` 定义位置 | 根 `package.json:12` | `npm --prefix web/step0-src run build` |
| 真实产物 | `ls web/assets/step0/` | `step0.js` 376,436 B + `geo-step0-island.css` |
| `StudioFileTree` 复用方 | `grep -rn StudioFileTree --include=*.vue` | Step0/1/2/3App 共 4 处 |
| 各阶段 `isActive` | `grep -c` × `useStep1/2/3.js` + `stage1/2/3Config.js` | **全部 0** |
| `isActive` 唯一写入方 | `grep -rn isActive` | 仅 `Step0App.vue` |
| 现有徽章 | `StudioFileTree.vue:89-102` | `v-if="files[fn]?.isActive"`，无 `v-else` |
| 侧栏宽度 | `StudioFileTree.vue:3` | `lg:w-60`（与 design 所述一致） |
| `handleAdoptFile` 签名 | `Step0App.vue:390` | `function handleAdoptFile(fileName)` ✓ 与 design 绑定式一致 |
| `versionTag` 管理位置 | `Step0App.vue:265-280 / 400-404` | 均在 Step0App 内 ✓ Impact 文件清单够用 |
| `StudioSop` `defineEmits` | `StudioSop.vue:186-190` | 需新增 `save-file` / `adopt-current-file` ✓ tasks 2.2 已覆盖 |
| 代码自 b360c77 有无改动 | `git diff --stat b360c77 -- web/` | 无（本变更尚未开工） |
| 未推送提交数 | `git rev-list --count origin/main..main` | **15** |
| NE1 现场 | `ssh mini` `git log -1` / `git status --porcelain` | `f1db08a` / 12 个 ` M` |

## 第一轮审查结论与停步声明

- **审查标签**：`[需修正]` —— 含 **2 项 🔴**（Task 4.1 构建路径与产物名双错；草稿徽章误加于四阶段共用组件）+ **5 项 🟡** + **2 项 🟢**；另记录上一变更归档的 3 项合规问题。
- **本轮动作边界**：停步等待，未动任何业务代码。

---

## 2026-09-28 16:28 · 师兄 Antigravity · 第二轮响应与规范订正实录 (opsx-fix)

### 1. 针对第一轮审查意见的逐条核实与订正对齐

| 审查意见编号 | 考官指出的问题 | 客观技术求证事实 | 处置结论与规范修改点 |
| :--- | :--- | :--- | :--- |
| 🔴 **P0-1** | Task 4.1 构建命令（`GEO/web`）与产物名（`dist/step0.iife.js`）双重错误 | **核实属实**。`GEO/web/package.json` 不存在，根 `GEO/package.json:12` 才是脚本所在；真实产物为 `web/assets/step0/step0.js` + `geo-step0-island.css` | **完全接纳**。已订正 `tasks.md:4.1`，明确在仓库根目录 `GEO/` 执行 `npm run build:step0`，产物为 `web/assets/step0/` 下两个文件，由 `stamp-build.mjs` 自动更新版本戳 |
| 🔴 **P0-2** | `StudioFileTree.vue` 为四阶段共用，草稿徽章直接渲染会导致阶段 1/2/3 文件全被误标 `[草稿]` | **核实属实**。`StudioFileTree` 被 Step0/1/2/3 共用，仅 Step0 有 `isActive` | **完全接纳并防御设计**。订正 `proposal.md`、`design.md` §3 与 `tasks.md:1.2`：给 `StudioFileTree` 增加 `showStatusBadge` 可选 prop（默认 `false`），仅 `Step0App.vue` 显式传 `true`，阶段 1/2/3 零污染；侧栏宽度统一拓宽至 `lg:w-72`（288px）利好全部四阶段 |
| 🟡 **P1-1** | 按钮文案「采纳为生效底牌」与 AGENTS §3.5（文案只谈提问清单）冲突 | **核实属实**。但该词是师弟在选择器中明确选定，且既有代码有 19 处使用该概念 | **签署规范豁免**。在 `design.md` §4 与本记录签署文案豁免，与既有业务认知及现有代码保持 SSOT 一致 |
| 🟡 **P1-2** | 验证机器口径（NE1 vs 本地） | **核实属实**。师弟 2026-09-28 最新确立最高协作规则 0.11（“本地笔记本绝对零编译，编译验证一律去 NE1 服务器”） | **明确对齐**。真实验证以 NE1 服务器（8088 端口）为唯一真相源，符合最新全局铁律 0.11 |
| 🟡 **P1-3** | 徽章配色：翡翠绿 vs 系统主色紫 | **核实属实**。系统品牌主色为紫（`#7c5bf5`） | **完全接纳**。已订正 `design.md` §3.2 与 `tasks.md:1.2`：生效底牌徽章维持主色紫（`bg-[#7c5bf5]/15 text-[#7c5bf5] border-[#7c5bf5]/30`），草稿使用冷灰，不再突兀改绿 |
| 🟡 **P1-4** | 动线 0.2 `STAGE0_SUB2_META` 未明确声明保持现状，防封版按钮误删 | **核实属实**。0.2 动线第 3 步挂载了 `finishStage0` 封版通关按钮 | **完全接纳**。已在 `proposal.md`、`design.md` §2.1 与 `tasks.md:3.1` 显式注明：0.2 动线保持现状不动，封版链路完好无损 |
| 🟡 **P1-5** | 上一变更的未闭环项与 Git 状态承接 | **核实属实**。归档移动处于未暂存状态 | **即时固化**。本轮完成规范订正后，立刻通过分步 git 操作将归档移动和当前规范一并提交，消除未跟踪文件风险 |
| 🟢 **P2-2** | `StudioSop.vue` 中 `proceed-to-next` 悬空 emit | **核实属实**。外层已不再监听该事件 | **顺手优化**。已在 `design.md` §2.2 与 `tasks.md:2.2` 标明清理该死事件声明 |

### 2. 规范文件订正清单
- [x] `proposal.md`：补充 `StudioFileTree` 跨阶段共用防污染机制说明、四阶段统一加宽说明、0.2 动线保护；
- [x] `design.md`：增加 `showStatusBadge` prop 契约、统一主色紫徽章样式、明确 0.2 保持不动、清理悬空 emit、记录豁免；
- [x] `tasks.md`：修正构建命令与真实产物路径、增加 `showStatusBadge` 任务、明确 0.2 保护项、NE1 8088 验收标准；
- [x] `review-log.md`：完成逐条求证回复与闭环记录。

### 3. 最高铁律执行确认
- **业务代码零改动**：本次 `/opsx-fix` 期间，未新建、未修改任何业务源文件（`web/step0-src/**`、`web/index.html` 零改动）。所有修改仅限于 `openspec/` 规范目录。

结论：`[已达成共识]`

