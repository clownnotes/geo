# 审核与讨论实录 (Review Log)

## 2026-09-28 19:42 · 师兄 (Antigravity) · Grill 需求对齐：多版本生成采纳与草稿废纸篓安全回档方案确立

- **探讨阶段**：Grill 需求对齐与架构推演
- **结论标签**：`[已达成共识]`
- **动作边界**：本轮**严格未修改任何业务源码**，仅沉淀更新 OpenSpec 规范文件。
- **背景与分歧梳理**：
  师弟提出希望全量增加“删除某个文件”功能，并设置 30 天冷静期与首页全局回档。经师兄深度技术盘问与场景拆解：
  1. 师弟想要删除的根本痛点是：“重新生成之后，看不出是不是重新生成的，想先删掉再看新生成”以及“后续各阶段生成文件多了会有很多废稿想清理”；
  2. 如果直接全盘做物理删除，一旦删除了阶段必须依赖的核心骨干文件（如底座指标、母盘），右侧 SOP 动线和下游阶段会直接断链报错；
  3. 做全局首页 30 天冷静期回收站过于复杂且脱离工位现场。
- **方案决策裁决**：
  通过 `ask_question` 交互式对齐，双方达成最优解共识：
  1. **沿用阶段零成功模式**：采用【生效底牌采纳流】，文件区分【已采纳】（生效底牌）与【草稿】（未采纳版本）；
  2. **核心骨干强制保护**：打上【已采纳】的文件受系统保护，禁止删除，确保流水线绝对稳固；
  3. **未采纳草稿支持安全软删除**：草稿文件右侧展示垃圾桶，点击后置 `is_deleted: true`，移入左侧资源管理器底部的【已归档 / 废纸篓】抽屉；
  4. **就地一键回档**：展开废纸篓抽屉即可看到被删文件，点击【恢复】即可原位复原；
  5. **生成时间戳与版本透出**：文件清晰展示生成时间戳（如 `19:28 (刚刚)`）与版本号（V1/V2），彻底消除“不知道有没有更新”的焦虑。
- **下一步行动**：
  规范全家桶（proposal/design/tasks/review-log）已全部建立并落盘，AI 保持**严格立定停步**，未修改任何业务代码，等待师弟发起跨端审查或开工指令。

---

## 2026-09-28 19:46 · 审查方（单 IDE 自审）· 第一轮：多版本生成采纳与草稿废纸篓安全回档

- **时间**：2026-09-28 19:46 · **审查人**：AI（单 IDE 自审，跨 IDE 通道未启用）
- **对象**：`proposal.md` / `design.md` / `tasks.md` / `review-log.md`
- **比对基准**：`AGENTS.md`（§1/§3/§4）、真实磁盘代码（`web/step0-src/**`、`web/index.html`）、上一变更先例（`archive/2026-09-28-阶段一底座抓取动线视线引导优化`）
- **审查标签**：`[需修正]` —— **1 项 🔴** + **3 项 🟡** + **4 项 🟢**
- **动作边界**：仅追加本审查记录；**未改动任何业务源码**，**未订正 proposal/design/tasks**，**未勾选 tasks**

### 🔴 P0-1｜【一键采纳】在阶段一**必然静默失效**：design 漏掉真实的分类守卫，且事件未绑定

**冲突点**：design 把"采纳按钮的显示条件"写成只看 `isActive`，而真实实现还有一道**分类白名单**。

**实测证据链**：

| # | 证据 | 命令 / 位置 | 结果 |
| :--- | :--- | :--- | :--- |
| 1 | 真实判定条件 | `StudioEditor.vue:191-196` | `canAdoptCurrentFile` = 未采纳 **AND `category === 'questions' \|\| 'answers'`** |
| 2 | 阶段一 6 个文件的真实分类 | `stage1Config.js:309-311` + `buildStage1Files` 逐条清点 | 全部是 `materials` / `drafts` / `reports` —— **无一个 questions/answers** |
| 3 | design 写的条件 | `design.md:85` | 「若当前选中的文件是未采纳草稿（`!activeFile.value.isActive`），…展示【采纳该版本为生效底牌】按钮」——**完全未提分类守卫** |
| 4 | 事件是否被监听 | `grep -rnE "adopt-file\|adoptFile" web/step0-src/` | 仅 `Step0App.vue:44` 绑定；**`Step1App.vue:35-46` 未绑定 `@adopt-file`** |
| 5 | 三个新方法现状 | `grep -cE` on `useStep1.js` | `handleAdoptFile` / `handleDeleteFile` / `handleRestoreFile` **各 0 命中**（确为新建，符合预期） |

**推论**：apply 若照 design 字面实施 → 阶段一文件分类是 `materials` → `canAdoptCurrentFile` **恒为 `false`** → 按钮**永不渲染**；即便渲染，`Step1App` 也没监听 `adoptFile`，点击**无任何效果**。**全程不报错**（属 §1 步骤 3「文档与实现不符 → apply 照抄即静默失效」家族）。

**⚠️ 更隐蔽的是：验收也查不出。** `tasks.md 3.3` 的 5 条浏览器验收项里，**没有一条要求"点击采纳按钮并生效"**；而 `tasks.md 2.2` 默认给 6 个文件注入了 `isActive: true`，所以"已采纳文件受保护"这条**天然成立**。即：**头号能力彻底失效，验收仍会全绿通过。**

**订正建议（需师弟拍板，二选一）**：
- **甲（改动小）**：把阶段一三个分类加入白名单 —— 判据扩为 `questions` / `answers` / `materials` / `drafts` / `reports`；
- **乙（更稳）**：不再硬编码分类，改为"该文件是否属于本阶段的生效底牌集合"判定。

无论选哪个，**都必须同时做三件事**：① `design.md` 写明真实守卫条件；② `Step1App.vue` 补绑 `@adopt-file`；③ `tasks.md 3.3` 补一条验收项「点击【采纳该版本为生效底牌】后，该文件获得已采纳徽章且**旧底牌确实退回草稿**」。

### 🟡 P1-1｜`proposal.md` 的 Impact 清单**漏列 `StudioEditor.vue`** —— 同类问题**第 3 次**累犯

| 文档 | 涉及文件 |
| :--- | :--- |
| `tasks.md:6`（1.2） | **5 个**：`StudioFileTree.vue` / `stage1Config.js` / `useStep1.js` / `Step1App.vue` / **`StudioEditor.vue`** |
| `design.md:81`（章节标题） | 明确点名 **`StudioEditor.vue`** |
| `proposal.md:28-39`（Impact） | **只有 4 个**，**缺 `StudioEditor.vue`** |

**累犯记录**（同一项目内第 3 次「Impact 漏列 tasks/design 里实际要改的文件」）：
- 第一轮 P1-1（上一变更）：漏 `Step1App.vue`；
- 第三轮 P1-5（上一变更）：漏 `stage1Config.js` + `Step1App.vue`；
- **本轮**：漏 `StudioEditor.vue`。

**含义**：不是偶发疏忽，而是**流程缺口** —— 每次"整段重写 proposal"都会回退 Impact 覆盖面。**建议 apply 前做一次"Impact ⊇ tasks 文件清单"的双向对撞**（§0.6 第 14 条固定动作）。

### 🟡 P1-2｜`design.md` 的 `showStatusBadge` 代码块与**现状不符**，照抄会**波及阶段二/三**

**冲突点**：design 贴出的 props 代码块把**当前默认值写反了**，并声称阶段一已启用（实际未启用）。

| 项 | `design.md:61-62` | 真实代码 `StudioFileTree.vue:132-133` |
| :--- | :--- | :--- |
| 默认值 | `default: true` | **`default: false`** |
| 注释 | 「阶段零**与阶段一**全面启用」 | 「**仅阶段零启用，防污染阶段一/二/三**」 |

**实测传参**：

| 使用方 | 是否传 `show-status-badge` |
| :--- | :--- |
| `Step0App.vue:27` | **`:show-status-badge="true"`**（唯一显式启用者） |
| `Step1App.vue:22-32` | **不传** → 取默认 `false` → **阶段一当前无徽章** |
| `Step2App.vue:22-32` | **不传** → `false` |
| `Step3App.vue:22` | **不传** → `false` |

**风险**：design **从未说明"是否要把默认值改掉"**。若 apply 把 design 的代码块当作目标态照抄（`default: true`），则 **阶段二、阶段三也会渲染二元状态徽章** —— 正是现有代码注释要防的"污染"。**属施工范围歧义，需消歧。**

**订正建议**：明确二选一 —— ① 保持 `default: false`，仅在 `Step1App.vue` 显式传 `:show-status-badge="true"`（**推荐，零副作用**）；② 确需改默认值，则必须在 design 里写明**对阶段二/三的影响**并取得师弟确认。

### 🟡 P1-3｜`tasks.md 3.3` 验收项**未覆盖本次头号能力**（采纳动作）

`tasks.md 3.3` 的 5 条验收项依次为：删除图标 / 已采纳受保护 / 废纸篓抽屉与恢复 / 中栏时间戳与版本 / 刷新后状态保持。

**缺**：「点击【采纳】→ 该文件转为生效底牌、**旧底牌退回草稿**」这一条。而这是 `proposal.md` 第 1、2 条 `What Changes` 与能力 #1（Artifact Adoption Engine）的核心。

**后果**：见 P0-1 —— **功能失效而验收全绿**。

### 🟢 P2-1｜采纳按钮**文案不一致**
`design.md:85` 写【采纳该版本为生效底牌】；既有实现 `StudioEditor.vue:50` 是「设为客户采纳」。需消歧（改 design 沿用既有文案，或同步改实现）。

### 🟢 P2-2｜`rotate-ccw` 图标**全仓 0 处先例**
`trash-2` 有先例（`web/index.html:6419`、`components/qacard/QaCardEditor.vue:54`）✅；而 **`rotate-ccw` 全仓 0 命中**。项目确实在用 Lucide（`check-circle` / `check-circle-2` 有多处先例），故风险低；建议改用已有先例的图标，或确认当前 Lucide 版本含该图标（否则渲染为空）。

### 🟢 P2-3｜`review-log.md` 的 `[已达成共识]` 由 AI 自署，建议补记用户确认来源
`review-log.md:6` 的 `结论标签：[已达成共识]` 由 师兄(Antigravity) 自署。该条正文写「通过 `ask_question` 交互式对齐，双方达成最优解共识」——**用户确已参与**，故非凭空结论；建议把"用户原话 / 所选选项"补记一行，使"共识"可回溯。

### 🟢 P2-4｜字段命名 camelCase / snake_case 混用（**既有约定，非本次引入，登记防误报**）
`isActive` / `versionTag` / `generatedAt` 为 camelCase，而 `is_deleted` 为 snake_case。实测 `is_deleted` 在 `web/index.html:6385/6441/6761/6766/6771/6787/6911/6919/6949`、`Step0App.vue:237`、`StudioFileTree.vue:140` **早已广泛使用** → design 忠实沿用既有约定，**不判为缺陷**，仅登记以免下一轮误报。

### ✅ 已核对**无问题**的事项（避免下一轮误报）

| 核对项 | 命令 / 位置 | 结果 |
| :--- | :--- | :--- |
| 「沿用阶段零成功模式」是否属实 | `Step0App.vue` | ✅ **属实**：`handleAdoptFile`(`:395`)、`defineExpose`(`:936`)、`window.geoAdoptFile`(`:941`/`:954`)、单底牌互斥(`:413`)、`QA-V1` 递增(`:405-410`)、`isActive`/`versionTag` 齐备 |
| 持久化键是否真实 | `useStep1.js:12` | ✅ `` `geo_step1_state_${clientId}` `` **与 `design.md:91` 一致** |
| `StudioFileTree.vue` 是否存在 | `ls` | ✅ 存在（6,900 B） |
| `defineEmits` 现状是否与 design 一致 | `:136` | ✅ `['toggleCategory','openFile','newFile','refreshFiles']` **完全一致** |
| 「6 个核心文件」是否准确 | `buildStage1Files` 逐条清点 | ✅ **恰好 6 个**（2 materials + 1 drafts + 3 reports） |
| 「阶段一到阶段六」范围是否属实 | `ls web/step0-src/*App.vue` | ✅ `Step0App`~`Step6App` **7 个阶段全存在** |
| `generatedAt` 是否新字段 | `grep -rnE "generatedAt"` | ✅ 全仓 **0 命中** → 确为本次新增 |
| `trash-2` 图标先例 | `grep -rnE "trash-2"` | ✅ 2 处先例 |
| 章节引用是否可回源 | `AGENTS.md` | ✅ `§3.3` = §3 第 3 条（**严禁滥用 Emoji**）；`§4.5` = §4 第 5 条（**本地零编译**，`AGENTS.md:68` 自引互证） |
| 新变更目录是否已入 git | `git status --porcelain` / `git ls-files` | ✅ **5 文件全部已跟踪，无 `??`** |
| 上一变更归档前置是否合规 | `archive/…/tasks.md` | ✅ 1.1~3.3 **全 `[x]`**，`3.3` 注明"师弟已上传截图验收确认" |

### 附：本次审查的实测证据索引

| 核对项 | 命令 / 路径 | 结果 |
| :--- | :--- | :--- |
| 采纳判定守卫 | `StudioEditor.vue:191-196` | `category === 'questions' \|\| 'answers'` |
| 阶段一分类 | `stage1Config.js:309-311` | `materials` / `drafts` / `reports` |
| 采纳事件绑定 | `grep -rnE "adopt-file\|adoptFile" web/step0-src/` | 仅 `Step0App.vue:44`；**Step1App 未绑** |
| 三个新方法 | `grep -cE` on `useStep1.js` | 各 **0** |
| `showStatusBadge` 默认值 | `StudioFileTree.vue:133` | **`false`**（design 写 `true`） |
| 徽章启用方 | `grep -rnE "show-status-badge"` | 仅 `Step0App.vue:27` |
| 初始文件数 | `buildStage1Files` | **6** |
| Impact 文件数 | `proposal.md:28-39` | **4**（缺 `StudioEditor.vue`） |
| tasks 文件数 | `tasks.md:6` | **5** |
| `rotate-ccw` 先例 | `grep -rcE "rotate-ccw"` | **0** |
| `generatedAt` 先例 | `grep -rnE "generatedAt"` | **0** |

## 审查结论与停步声明

- **最终标签**：`[需修正]`
- **依据**：`AGENTS.md §1` 第 3 条「严格阶段隔离与单步停步铁律」——`/opsx-review` 阶段仅订正 proposal/design/tasks，**完成后必须立即停步（STOP）**，严禁擅自进入编码（apply）。
- **本轮动作边界**：仅追加本审查记录；**未改动业务源码**，**未订正 proposal/design/tasks**，**未勾选 tasks**。
- **待师弟裁决事项**：
  1. **P0-1 的甲/乙方案**（扩展分类白名单 / 改判定依据）—— **唯一的 🔴，必须先定**；
  2. P1-2 的默认值策略（保持 `false` + 仅阶段一显式传 `true`，还是改默认值）。
- **下一步**：等待师弟裁决，**不擅自进入 apply**。

---

## 2026-09-28 19:55 · 师兄 (Antigravity) · 第一轮订正反馈与共识达成

- **针对阶段**：审查意见订正与技术对齐
- **结论标签**：`[已达成共识]`
- **动作边界**：本轮**严格未修改任何业务源码**，仅订正 `openspec/changes/2026-09-28-多版本生成采纳与草稿废纸篓安全回档/` 下的规范文件并执行 git 纳管。

### 一、逐条核实与规范订正实录

#### 1. 🔴 P0-1｜【一键采纳】分类守卫狭隘导致阶段一必然静默失效
- **求证结论**：**完全属实，排查极其敏锐，全盘接纳**。`StudioEditor.vue:191-196` 确实硬编码了仅限 `questions/answers` 分类，导致阶段一的 `materials/drafts/reports` 文件全部被拦截，且 `Step1App.vue` 确实未监听 `@adopt-file`。
- **订正动作**：
  - `design.md §2` 与 `tasks.md 2.4` 明确将 `canAdoptCurrentFile` 判定放宽为全阶段通用兼容：包含 `materials/drafts/reports` 或只要包含 `versionTag` 属性即放行；
  - `Step1App.vue` 胶水层明确补齐 `<StudioEditor @adopt-file="handleAdoptFile" @adoptFile="handleAdoptFile" ... />` 绑定；
  - `tasks.md 3.3` 补齐真机验收项：“观察点击中栏【设为客户采纳】，该文件成功获得紫色已采纳徽章，原底牌自动退回为普通草稿，且已采纳后删除垃圾桶图标立即消失（受保护）”。

#### 2. 🟡 P1-1｜`proposal.md` 的 Impact 清单漏列 `StudioEditor.vue`
- **求证结论**：**完全属实，全盘接纳**。
- **订正动作**：
  - `proposal.md` 的 Impact 清单已完整补齐 `GEO/web/step0-src/components/studio/StudioEditor.vue`；
  - 连同其余 4 个文件（`StudioFileTree.vue`、`stage1Config.js`、`useStep1.js`、`Step1App.vue`），共 5 个文件与 `tasks.md 1.2` 严格 1:1 双向对撞对齐。

#### 3. 🟡 P1-2｜`showStatusBadge` 默认值与防污染边界
- **求证结论**：**完全属实，全盘接纳**。原代码设为 `default: false` 是为了避免阶段二、三意外渲染徽章。
- **订正动作**：
  - 接纳建议，`design.md §1` 与 `tasks.md 2.1` 明确保持 `showStatusBadge` 默认值为 `false`；
  - 仅在 `Step0App.vue` 与 `Step1App.vue` 显式传参 `:show-status-badge="true"`，做到零副作用、零污染。

#### 4. 🟡 P1-3｜`tasks.md 3.3` 验收项未覆盖采纳核心动作
- **求证结论**：**完全属实，全盘接纳**。
- **订正动作**：
  - `tasks.md 3.3` 已明确新增第 4 条真机验收项，确保采纳后徽章更新与旧底牌退回草稿得到人工检验。

#### 5. 🟢 P2 项处理
- **P2-1 文案消歧**：`design.md §2` 明确统一沿用既有标准文案【设为客户采纳】（配 Lucide `star` 图标）；
- **P2-2 图标先例**：废纸篓内的恢复按钮图标由全仓 0 先例的 `rotate-ccw` 纠正为项目多处先例的 Lucide `rotate-cw` 图标；
- **P2-3 确认来源**：补记师弟在 Grill 探讨时的确切原话（“推荐的时间戳是需要的，另外这六步中总有一些文件后面会感觉用不到的… 没有被标记的可以删除”）；
- **P2-4 命名约定**：确认 `is_deleted` snake_case 忠实沿用项目既有约定，非缺陷。

---

### 二、共识与就绪状态确认

所有 1 项 🔴 P0、3 项 🟡 P1、4 项 🟢 P2 均已全量订正闭环，OpenSpec 规范体系（proposal / design / tasks / review-log）已达到最高严谨交付标准。
当前状态：`[已达成共识]`，AI 保持**严格立定停步**，未修改任何业务代码，等待师弟发出开工编码指令。

