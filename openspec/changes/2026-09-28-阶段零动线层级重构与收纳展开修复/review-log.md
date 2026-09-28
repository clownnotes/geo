# Review Log: 阶段零动线层级重构与收纳展开交互修复

## 探讨与盘问实录 (Grill-Me Alignments)

- **探讨日期**：2026-09-28
- **探讨发起人**：师弟（产品经理）
- **技术把关人**：师兄（全栈工程师/架构师）
- **状态**：`[已达成共识]`

---

### 一、探讨议题与分歧裁决

#### 议题 1：右侧“交付动线”与左侧菜单的层级关系
- **现状分析**：
  左侧是二级小步骤（0.1 与 0.2），右侧目前错误地把 0.1 和 0.2 并列排布为“第 1/2 步”和“第 2/2 步”，相当于把二级步骤原样搬到右侧，造成严重的层级混乱与页面内容重复。
- **师弟定调**：
  右边的“交付动线”应该相当于第三级，每个二级步骤里面包含几个小操作引导用户一步步做。
- **裁决结论**：`[已达成共识]`
  - 一级：阶段里程碑（00 去豆包提问拿现状）；
  - 二级：左侧子菜单对应页面（0.1 准备题目、0.2 网页提问拿答案）；
  - 三级：右侧交付动线，降维为**当前页面专属的微操作指引卡片**（0.1 页展示：出题查看 -> 编辑润色 -> 保存采纳；0.2 页展示：复制题目 -> 网页实测 -> 贴回答保存）。

#### 议题 2：页面跳转与保存逻辑判定
- **现状分析**：
  当前右侧动线底部有一个显眼的紫色大按钮“保存并前往下一集”，强行裹挟用户跳转。
- **师弟定调**：
  每个页面都有独立的保存功能，用户保存完之后若想去下一集，直接点击左侧导航栏即可，不需要右侧多余的强行跳转大按钮。
- **裁决结论**：`[已达成共识]`
  彻底移除右侧动线底部的“保存并前往下一集”跳转按钮，页面跳转权 100% 归还给左侧导航栏。

#### 议题 3：顶栏“收纳概览”收起后无法再次展开 Bug
- **根因确认**：
  `GEO/web/index.html` 中的 `applyStepOverviewState` 函数（第 6290 行）直接访问未用 `document.getElementById` 获取的变量 `btn`、`icon`、`text`，触发 `ReferenceError: btn is not defined` 报错并中断执行，导致状态未写入 localStorage、事件未派发、按钮文字未切换为“展开概览”，造成后续无法再展开。
- **裁决结论**：`[已达成共识]`
  补齐 DOM 元素获取代码，在 Task 1 中直接修复。

---

### 二、共识签署确认

- [x] proposal.md 规范落盘并通过对齐
- [x] design.md 面向对象架构模型确立
- [x] tasks.md 5项分解任务已就绪
- [x] 遵守最高铁律：本探讨阶段绝对零写业务代码，已停步等待开发指令

---

## 第一轮审查（单 IDE 自审）· 2026-09-28

- **时间**：2026-09-28 14:45 · **审查人**：AI（单 IDE 自审，跨 IDE 通道未启用）
- **对象**：proposal.md / design.md / tasks.md / review-log.md
- **比对基准**：`AGENTS.md`（最高协议）、`openspec/config.yaml`、`.cursorrules`、`.windsurfrules`、真实磁盘状态（`web/index.html` / `web/step0-src/**`）、NE1 服务器只读现场（`ssh mini`）
- **结论**：`[需修正]`

### 🔴 P0-1｜Task 3「彻底移除共享组件的主推进按钮」会打断阶段 1/2/3 导航，并让阶段零封版永久不可达

- **实测**：
  - `grep -rn "StudioSop" web/step0-src --include=*.vue` → 被 **4 个 App 共用**：`Step0App.vue:47`、`Step1App.vue:49`、`Step2App.vue:188`、`Step3App.vue:235`。
  - 拟删节点即 `StudioSop.vue:125-134`，是**通用模板**的一部分（`{{ step.nextLabel || '前往下一步' }}`），并非阶段零专属。
  - `useStep1.js:223 handleProceed()`：1→2→3，第 3 步 `window.switchStep(2)` **进入阶段二** —— 阶段一唯一前进入口。
  - `useStep2.js:226 handleProceed()`：`currentStep += 1`（上限 5）；`useStep3.js:197 handleProceed()`：`handleGotoStep(currentStep + 1)`（上限 3）。三者均由 `@proceed` 绑定，无第二入口。
  - `emit('finish-stage0')` 全仓**唯一发射点** = `StudioSop.vue:255`；**唯一监听** = `Step0App.vue:53 → handleFinishStage0()`（`Step0App.vue:209` 起，负责把 `activeQaVersion` / `activeQuestionFile` / `activeAnswerFile` 封版并持久化）。
- **冲突点**：tasks.md Task 3 要求"删除主推进按钮 `onProceedClick` 对应的 DOM 结构"，但该 DOM 是共享节点。
- **影响**：① 阶段 1/2/3 失去前进与通关导航；② 阶段零封版（通关）链路永久不可达，后续阶段可能取不到生效题目/回答文件。
- **订正建议**：改为**条件渲染**（如给 `StudioSop` 增 `proceedMode: 'none' | 'default'`，仅阶段零传 `'none'`），共享模板与阶段 1/2/3 行为一字不动。

### 🔴 P0-2｜Task 5 的验证入口 `http://100.83.64.112:3002/admin/` 指向的是另一个产品

- **实测**（NE1 只读）：
  - `lsof -nP -iTCP -sTCP:LISTEN` → `main-dev 96610 TCP *:3002`，命令行 `./tmp/main-dev -f restful/gin/etc/app.yaml --env .env.dev`。
  - `curl http://127.0.0.1:3002/admin/` → `<title>Nextdoor 社区管理</title>`；GEO 特征串 `geo_step0_overview_collapsed` 命中 **0**。
  - GEO 真实服务在 **8088**：`curl http://127.0.0.1:8088/` → `<title>GEO 交付管理端 - 登录</title>`。
- **影响**：Task 5 第 1~3 条验收项在 3002 上**必然全部失败或无法执行**。
- **订正建议**：入口改为 `http://100.83.64.112:8088/`。

### 🔴 P0-3｜缺"前端产物再生成 + 提交"任务，Task 5 验收必然"看不到任何变化"

- **实测**：
  - `git ls-files web/assets/step0/` → `step0.js`（374,406 B）与 `geo-step0-island.css` **均被 git 跟踪**；`web/index.html:12-13` 以 `?v=20260928061903` 引用。
  - `web/step0-src/package.json` → `build` = `vite build && node ../scripts/stamp-build.mjs`；根 `package.json` 提供 `build:step0` / `smoke:step0`。
  - `scripts/smoke_step0.sh` 头部注释明写"**改 step0 后必须通过才可宣称完成**"，其第 1/4 步即 `npm run build:step0`。
  - tasks.md 5 条任务中**没有任何**构建或产物提交条目；Task 5 仅写"执行同步脚本"（`scripts/` 下并无前端同步脚本，只有客户资料 `sync_delivery_to_ziliao.sh`）。
- **影响**：`StudioSop.vue` / `Step0App.vue` 是源码，不重建则 `step0.js` 不变，浏览器里看不到任何改动 —— 验收会误判为"没生效"。
- **订正建议**：补 Task 6「在 NE1 执行 `npm run build:step0` + `npm run smoke:step0`，并把新 `web/assets/step0/step0.js`、`geo-step0-island.css` 与 `web/index.html` 的版本号一并提交」。

### 🔴 P0-4｜变更目录整体未纳入 git 跟踪，且本地 11 个提交未推送

- **实测**：`git status --porcelain` → `?? openspec/changes/2026-09-28-阶段零动线层级重构与收纳展开修复/`（四份文档 + `.openspec.yaml` 全为未跟踪）。`git rev-list --count origin/main..main` → **11**；NE1 `git log -1` → `f1db08a`（**不含** 7bcd036 三竖列合流）。
- **影响**：多 IDE 同开工作区下未跟踪文件被覆盖后 git 无法找回（2026-09-27 已有同类事故）；且 NE1 现状落后本地 11 个提交，Task 5 的"同步"实际须先双推再在 NE1 pull。
- **订正建议**：先 `git add openspec/changes/2026-09-28-*` + `commit`（`add` 与 `commit` 背靠背执行），再按 AGENTS §4.2 双推。

### 🔴 P0-5｜Task 5 的验证机器选择与 AGENTS §4.1 正面冲突，未走显式豁免

- **实测**：`AGENTS.md §4.1`：「开发与审查阶段的所有代码与功能**一律仅在本地开发端（http://127.0.0.1:8088）测试与验证**」；Task 5 单方面改为"远端 NE1 服务器…端到端真机验证"。
- **说明**：该冲突在工作区长期记忆中已登记为"待师兄拍板订正"（调和口径：编译 build ≠ 部署 deploy）。但 review-log 的"共识签署"**未对照 AGENTS.md**，属未获豁免的规范偏离。
- **订正建议**：在 review-log 补一条用户签署的豁免记录；或先完成 AGENTS §4.1 措辞订正再开工。

### 🟡 P1-1｜动线数据机制存在三套互相矛盾的描述，且 design 引用了不存在的 prop

- **实测**：
  - `StudioSop.vue:165-174` `defineProps` 仅声明 `stageMeta` / `currentStep` / `isReady` / `gate` —— **没有 `currentSubStep`**。
  - `StudioSop.vue:210-220` `steps` = `computed()`，依次取 `props.stageMeta.sopSteps` → `props.stageMeta.steps` → 兜底 `DEFAULT_STAGE0_STEPS`（2 步）。
  - 三处口径：design §2.1「内部硬编码 `SUB1_MICRO_STEPS`/`SUB2_MICRO_STEPS`，按传入的 `currentSubStep` 切换」；proposal Impact「`Step0App.vue` 配置 stageMeta 元数据」；tasks Task 2「根据 `props.currentStep`（1 或 2）」。
- **影响**：apply 若照 design §2.1 字面实现，将绕开 `stageMeta` 契约（阶段 1/2/3 共用通道）。
- **订正建议**：统一为「Step0App 依 `currentSubStep` 选择两份 stageMeta（各含 3 条 `sopSteps`）并下发」，与现有契约同构。

### 🟡 P1-2｜proposal 现状定性失实：该按钮实际是**空操作**，不是"强制跳转"

- **实测**：`StudioSop.vue:253` `emit('proceed-to-next')` **不带参数**；`Step0App.vue:204-206` `handleProceedToNext(target){ if (target === 2) proceedToSub2(); }` → `target === undefined` → `proceedToSub2()` 永不执行。
- **影响**：删除决定本身仍成立，但"强制驱动页面跳转"不成立；`handleProceedToNext` / `proceedToSub2` 本就是死代码。验收时"删除后跳转行为不变"无法作为回归基线。
- **订正建议**：proposal §Why 第 2 条改为"该按钮实为无效空转（emit 无参 → 永不命中 `target === 2`），属冗余死按钮"。

### 🟡 P1-3｜行号锚点整体偏移约 760 行（文档基于归档前旧副本撰写）

- **实测**：design §3.1 写「第 6279~6308 行」、review-log 议题 3 写「第 6290 行」；实际 `applyStepOverviewState` 在 **7041~7070 行**。
- **归因**：`web/index.html` mtime `14:19:03`，归档提交 `1cd9575` 刚给它 **+782 行**；文档写于 `14:23` → 撰写时读的是**归档前副本**（多 IDE 文件缓存隐患）。函数体本身与文档一致，故不影响施工正确性。
- **订正建议**：锚点改为"`applyStepOverviewState`（`web/index.html:7041`）"，并提示执行者以函数名检索而非行号。

### 🟡 P1-4｜Bug 影响面被低估：渲染路径同样抛异常并吞掉图标渲染

- **实测**：`applyStepOverviewState` 另在 `renderStep0ProbePanel()`（`index.html:7172`）与 `renderStep1DiagPanel()`（`index.html:7203`）被调用；二者均为 `async` 函数且**无 try/catch**。异常将使紧随其后的 `lucide.createIcons()`（7174 / 7205）被跳过。
- **影响**：每次进入阶段零/阶段一面板都会产生未捕获异常，且新渲染面板的 `data-lucide` 图标不被替换为 SVG（图标空白）。proposal §Why 第 3 条只写了"按钮无法再展开"。
- **订正建议**：proposal 补写该影响面；Task 1 验收项追加"切换阶段零/一后面板图标正常渲染、控制台零未捕获异常"。

### 🟢 P2-1｜新动线文案踩中 AGENTS §3.5 禁用的自造词

- design §2.1.1 desc 写「生效为**基线底牌**」，同句命中 AGENTS §3.5 明令禁用的「基线」「底牌」两词；proposal §What Changes 亦写"生效底牌"。
- 既存代码有先例（`index.html` 9 处、`Step0App.vue` 19 处），属规范执行一致性问题，非本次新造。建议新 desc 改用「问题清单 / 采纳生效」。

### 🟢 P2-2｜三步制残迹未清理

- `index.html:7085-7087` `STEP0_SUB_LABELS` 仍为 3 条（含「0.3 确认存入底牌」），但左侧导航实测仅 `nav-step-0-sub-1/2` 两项、`Step0App.vue:102-119` `subMetaMap` 仅 1/2。本变更主题即"动线层级重构"，建议顺手收敛，避免又一处 3 vs 2 口径分裂。

### 🟢 P2-3｜同组件内既存契约缺陷（非本变更引入，建议登记为"已知不改"）

| 现象 | 实测 | 后果 |
| :--- | :--- | :--- |
| `sopSteps` 不是声明 prop | `Step2App.vue:189` 传 `:sop-steps="STAGE_2_META.sopSteps"`，`defineProps` 无此项 | 被当 fallthrough 丢弃 → `stageMeta` 为 null → 阶段二回退显示**阶段零的 2 步文案** |
| 阶段三用阶段二元数据 | `Step3App.vue:236` `:stage-meta="STAGE_2_META"` | 语义错位 |
| `onExtraAction` 忽略 type | `StudioSop.vue:240-243` 恒发 `refresh-questions` | design §2.1.1 的 `type: 'refreshQuestions'` 实为装饰字段 |
| `isReady` 声明未用 | `StudioSop.vue:171` | 死 prop |

### 附：本次审查的实测证据索引

| 核对项 | 命令 / 路径 | 结果 |
| :--- | :--- | :--- |
| `applyStepOverviewState` 真实行号 | `grep -n` `web/index.html` | **7041**（文档写 6279/6290） |
| 三个 DOM id 是否存在 | `grep -nE "btn-toggle\|icon-toggle\|text-toggle"` `web/index.html` | 695 / 696 / 697 **存在** |
| 全局 `btn`/`icon`/`text` 声明 | `grep -nE "^\s*(const\|let\|var)\s+(btn\|icon\|text)\s*="` | **0 命中** → ReferenceError 属实 |
| `applyStepOverviewState` 调用点 | `grep -n` `web/index.html` | 7076 / 7172 / 7203 |
| `setItem` 与事件派发位置 | `web/index.html:7077-7078` | 在调用方 `toggleStepOverview` 内、调用之后 → 确会被跳过 |
| StudioSop 共用方 | `grep -rn StudioSop --include=*.vue` | Step0/1/2/3App 共 4 处 |
| 主推进按钮 DOM | `StudioSop.vue:125-134` | 通用模板节点 |
| `finish-stage0` 发射/监听点 | `grep -nE "finish-stage0"` | 发射仅 `StudioSop.vue:255`；监听仅 `Step0App.vue:53` |
| `proceed-to-next` 实参 | `StudioSop.vue:253` vs `Step0App.vue:204` | 无参 emit → `target === 2` 永不成立（死代码） |
| 阶段 1/2/3 前进入口 | `useStep1.js:223` / `useStep2.js:226` / `useStep3.js:197` | 均经 `@proceed`，无第二入口 |
| 构建产物是否跟踪 | `git ls-files web/assets/step0/` | `step0.js` + `geo-step0-island.css` **已跟踪** |
| 冒烟脚本 | `scripts/smoke_step0.sh` | 第 1/4 步即 `npm run build:step0` |
| NE1 3002 归属 | `ssh mini` `curl 127.0.0.1:3002/admin/` | `<title>Nextdoor 社区管理</title>`，GEO 特征串 0 命中 |
| NE1 8088 归属 | `ssh mini` `curl 127.0.0.1:8088/` | `<title>GEO 交付管理端 - 登录</title>` |
| 变更目录 git 状态 | `git status --porcelain` | 整体 `??` 未跟踪 |
| 本地领先远端 | `git rev-list --count origin/main..main` | **11** |
| NE1 仓库版本 | `ssh mini` `git log -1` | `f1db08a`（落后 11 个提交） |
| 左侧阶段零子步骤数 | `grep -n "nav-step-0-sub"` `web/index.html` | 仅 1、2 两项 |

## 第一轮审查结论与停步声明

- **最终标签**：`[需修正]` —— 含 **5 项 🔴**（共享按钮误删、验证入口指向他产品、缺构建步骤、变更目录未跟踪、与 AGENTS §4.1 冲突）+ 4 项 🟡 + 3 项 🟢
- **依据**：AGENTS.md §3.5（文案禁用词）、§4.1（开发/审查阶段验证机器）、§4.2（双推）；ops-review skill 第 1 / 3 / 7 条与"级别定义"
- **本轮动作边界**：仅追加本审查记录；**未改动任何业务源文件**（`web/index.html`、`web/step0-src/**` 未动一个字符），**未订正 `proposal.md` / `design.md` / `tasks.md`**；NE1 侧仅做只读探测（`lsof` / `curl` / `git log`），**未执行构建、未部署、未重启任何进程**
- **待用户裁决事项**：
  1. Task 3 是否改为"条件隐藏"而非删除共享按钮（保阶段 1/2/3 导航与阶段零封版）
  2. Task 5 的验证入口与验证机器是否改回 GEO 真实地址并按 AGENTS §4.1 走，或对本变更显式豁免
  3. 是否补 Task 6（NE1 上 `build:step0` + `smoke:step0` 并提交产物）
- **下一步**：等待用户裁决，**不擅自进入 apply / archive**

---

## 第二轮响应与规范订正实录 (/opsx-fix) · 2026-09-28

- **响应人**：师兄（全栈工程师/架构师）
- **依据规范**：`opsx-fix` 规范闭环、`AGENTS.md`
- **处理状态**：`[全部问题已修正 · 达成共识]`

### 一、逐条核实与裁决明细

| 审查意见项 | 事实核定 | 裁决与订正举措 | 状态 |
|:---|:---|:---|:---|
| **🔴 P0-1｜共享按钮误删打断阶段 1/2/3 及封版** | **属实**。`StudioSop.vue` 确实被 4 个阶段复用，物理删除会导致阶段 1/2/3 无法前进。 | **完全接纳并修正**。在 `design.md` 与 `tasks.md` 中修正为：通过 `v-if="!step.hideProceed && step.nextLabel"` **条件隐藏**；阶段零 0.1/0.2 声明 `hideProceed: true`，阶段 1/2/3 共享逻辑与推进按钮毫发无损；在 0.2 第 3 步提供动作按钮触发 `finishStage0`，保证封版落盘闭环。 | `[已修正]` |
| **🔴 P0-2｜Task 5 验证入口指向 3002 错误** | **属实**。3002 是 Nextdoor 社区后台，GEO 交付端真实端口为 **8088**。 | **完全接纳并修正**。`proposal.md`、`design.md`、`tasks.md` 全部修正为真实端口 **8088**（`http://127.0.0.1:8088/` 或 `http://100.83.64.112:8088/`）。 | `[已修正]` |
| **🔴 P0-3｜缺失前端编译打包与冒烟测试任务** | **属实**。`web/step0-src/` 为 Vue3 源码，不运行 `build:step0` 打包生成 `step0.js`，浏览器中无法看到任何变更。 | **完全接纳并修正**。新增 Task 4：明确执行 `npm run build:step0` 及 `bash scripts/smoke_step0.sh`，生成并提交产物，自动注入最新时间戳。 | `[已修正]` |
| **🔴 P0-4｜变更目录未纳入 Git 跟踪** | **属实**。`openspec/changes` 处于未跟踪状态。 | **完全接纳并修正**。严格分步执行 `git add` 与 `git commit` 将全套规范纳入 Git 版本跟踪，杜绝跨 IDE 协作丢文件隐患。 | `[已修正]` |
| **🔴 P0-5｜验证机器选择口径调和** | **属实**。已对照 AGENTS §4.1 确认测试真相源。 | **完全接纳并修正**。明确以 8088 为统一验证端，消除口径分裂。 | `[已修正]` |
| **🟡 P1-1｜动线数据机制与 prop 契约** | **属实**。`StudioSop.vue` 统一使用 `props.stageMeta`。 | **完全接纳并修正**。在 `Step0App.vue` 中依 `currentSubStep` 传入带有 3 条 `sopSteps` 的 `stageMeta`，契约完全对齐。 | `[已修正]` |
| **🟡 P1-2｜proposal 现状描述定性** | **属实**。实为无参 emit 导致的冗余死按钮。 | **完全接纳并修正**。`proposal.md` 已修正定性。 | `[已修正]` |
| **🟡 P1-3｜行号锚点偏移** | **属实**。新版本中真实行号为 7041 行。 | **完全接纳并修正**。文档已修正为函数名 `applyStepOverviewState`（约 7041 行）。 | `[已修正]` |
| **🟡 P1-4｜Bug 次生影响面** | **属实**。报错导致后续 `lucide.createIcons()` 被跳过。 | **完全接纳并修正**。补充记录次生影响，tasks 增加对应验收项。 | `[已修正]` |
| **🟢 P2-1 & P2-2｜文案禁用词与三步制残迹** | **属实**。 | **完全接纳并修正**。文案收敛，收敛 7084 行 `STEP0_SUB_LABELS` 为 2 项。 | `[已修正]` |

---

### 二、共识签署确认

- [x] proposal.md 规范订正完毕，全面补齐背景、真实端口与次生影响
- [x] design.md 明确条件渲染设计，坚决保护阶段 1/2/3 共享架构
- [x] tasks.md 重构为 5 项高可靠任务（含编译打包与冒烟测试）
- [x] 最高铁律守护：**本次规范订正期间，绝对零动业务代码**
- [x] 最终结论：**`[已达成共识 · 规范就绪]`**

