# Review Log: 阶段三企业母盘与统一口径卡需求与设计对齐记录

## 2026-09-30 轮次一：动线重构与母盘定位对齐

- **核心背景**：
  此前讨论中有人误将“统一口径卡”建议放在第 2 步素材库，师弟明确指出这是严重的逻辑错位——素材库是生料收集阶段，材料未齐、充满增量碎片，绝不能在此时定稿全企业的统一口径。
- **关键裁决**：
  1. 首次交付从 6 步扩充为 7 步，新增第 3 步【企业母盘与统一口径卡】；
  2. 第 2 步素材库收集齐备后，进入第 3 步加工提炼熟料；
  3. 母盘包含两大核心资产：基于老赵哥事实标准的《主体信息统一口径卡》与《普林斯顿企业事实母盘》。
  4. **[2026-09-30 师弟拍板]** 确立**【双轮驱动结构】**：
     - `01_主体信息统一口径卡.md`：专职全平台人机消歧与三级业务文本（50字/120字/完整版）及客观瑕疵对冲；
     - `02_普林斯顿企业事实母盘.md`：专职 9 因子核心事实高权威熟料，直供下游交钥匙官网与大模型问答底座。
     - 拒绝合二为一大文件，职责彻底分清！
  5. **[2026-09-30 师弟认知定音 · 定位与九因子本质]**：
     - **主体口径卡** = 企业的**“全网消歧身份证 + 精准定位名片”**（解决全网各平台信息打架、让 AI 认得准、不认错）；
     - **九因子母盘** = **“更丰满立体的企业事实大百科全书”**（长出价格、痛点、对比、案例、资质等血肉，支撑深度问答与官网）。
  6. **[2026-09-30 师弟拍板]** 三级业务描述采用**【智能首稿 + 实时字数合规指示灯】**：
     - 系统自动基于建档与素材库生成短版(50字)、标准版(120字)、完整版建议稿；
     - 界面带红绿字数指示灯，并强校验「消歧四要素」与「GEO 中文全称首现标注」，省时严密。
  7. **[2026-09-30 师弟拍板 · 母盘精炼合流法则]**：
     - **母盘仅消费 S1~S6 规范主版本**，绝不无脑合并增补分片！
     - 保持母盘短小精炼、权威克制（杜绝母盘臃肿爆炸）；
     - 增补素材（1.x）留在素材库中专供 RAG 细颗粒度检索调用，人机边界彻底分明！
  8. **[2026-09-30 师弟拍板 · 客观瑕疵对冲与平台指南]**：
     - 采用**【口径卡内置对冲章节 + 右侧动线交互式排查器】**；
     - 右侧提供“0 参保、跨城经营、历史业务过渡”等交互式排查勾选项；
     - 勾选后自动在口径卡正文生成合规对冲指引话术与逐平台（征信/招聘/地图/官网）修改卡；
     - 交付人员手持这份口径卡，即可直接指导客户在各大外部平台认领改口径！


---

### [2026-09-30 11:37] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# WorkBuddy 独立审查报告（stage=code）

审查对象：`阶段三企业母盘与统一口径卡构建（6步升级为7步）` 的 proposal / design / tasks 与业务源码 Diff（28 文件，+8110 / -4489）。

结论先行：本次实现体量巨大、方向大体正确，但**存在实现严重超出 Spec 范围、架构复用破坏与若干数据不变式隐患**，不满足 AGENTS「严格按 tasks.md 编码、拒绝打补丁与面条代码」的要求，需修正后再复审。

---

## 一、Spec 对照审查（完整性）

| 维度 | Spec 要求 | 代码实现 | 结论 |
| :--- | :--- | :--- | :--- |
| 槽位字典 | 3 槽位 `identity_card / master / hedge_list` | 断言 25 已注册三槽位，名称规范一致 | 达标 |
| 口径卡生成/校验 | 四要素+三级字数红绿灯 | 断言 26 覆盖，`normalizeOfficialUrl` 断言 24 额外补齐 | 达标（有外溢，见下） |
| 母盘合流 | 仅消费 S1~S6 主版本、隔离 1.x | 断言 27 覆盖，`filterMasterSourceFiles` 契约成立 | 达标 |
| 界面三栏 + 4 步 SOP | 左树 / 中编辑 / 右 4 步 SOP | Step3App 改造 | 部分达标（复用问题见 🔴2） |
| 导航 6→7 步顺延 | 后续 04~07 全保留 | index.html 已顺延且加历史 viewId 兼容映射 | 达标 |
| **实现边界** | tasks.md 仅列上述条目 | **代码额外实现大量未列功能** | **严重不达标（🔴1）** |

---

## 二、必须改（🔴）

**🔴1. 实现严重超出 Spec 范围（scope creep），违背规范驱动铁律**
Diff 中新增的以下能力在 `proposal.md / design.md / tasks.md` 中**均无任何描述**：
- `DistillSheet.vue` 网页/文案「盖板蒸馏工作台」（`openDistillSheet / handleAdoptDistillChunk / distillMode`）；
- `semanticChunkRawMaterial` 语义切块、`computeTextSimilarity / findSemanticDuplicates` RAG 去重、`checkDraftTextLimit` 8500 字硬限；
- Stage2 的 S1~S6 六大结构化表单卡片（`s1Form~s6Form / s4Competitors / s5Cases`）；
- `activateTabInStack` 智能 Tab 栈、`normalizeOfficialUrl / extractDomain` 归一化、`computeBranchVersion / computeStage2ChunkVersion` 等。

Spec 是唯一编码依据（AGENTS §1.3）。上述功能未进 Spec 即落地，导致审查**无法对照 tasks.md 验证**。必须二选一：补齐 design/tasks，或拆分为独立变更。

**🔴2. 架构复用破坏：SOP 面板出现两套实现**
`Step2App.vue` 采用共享组件 `<StudioSop :stage-meta=... :expand-all>`；而 `Step3App.vue` 改造后**放弃 StudioSop，改为手写 `<aside>` SOP 面板**（内联 `stage2Readiness / cardAudit` 渲染逻辑）。同一交付工作台出现两份 SOP 渲染代码，正是评审关注点中的「打补丁与重复面条代码」。应统一收敛到 `StudioSop`，差异通过 `STAGE_3_META.sopSteps` 数据驱动。

**🔴3. 配对文件版本标签存在污染风险（破坏 Q/A 配对不变式）**
`Step0App.vue handleAdoptFile`：
```js
if (currentAdopted.category === 'answers' || isV1) {
    files.value[pairFileName].versionTag = res.versionTag;
}
```
当采纳的是**回答**（`category==='answers'`）且其题目仍处低版本时，会把题目文件的 `versionTag` 覆写为回答版本号，造成「题目 V1 / 回答 V2」错配，破坏同槽 `QA-Vn` 配对一致性。应仅同步同名配套件（同 `n`）标签，绝不跨版本覆写。

**🔴4. 门禁 fail-open：`isProbeUnready` 读本地存储绕过服务端真相源**
`index.html` 中 `isProbeUnready` 新增逻辑：只要 `localStorage` 存在任一 active 文件即判定 ready、跳过拦截。这使**客户端本地脏数据可绕过服务端 `probe_status` 门禁**，与项目「SSOT + 服务端为准」的架构原则冲突，且属 fail-open。建议改为服务端状态与本地状态**同时满足**，或明确降级为提示而非放行。

---

## 三、建议改（🟡）

**🟡5. Spec 内部自相矛盾，文档一致性不达标**
- `proposal.md` 标题/Impact 写「6 步扩为 7 步」，What 又写「8 步流水线 00~07」；
- `tests/smoke_studio_artifacts.mjs` 头部注释写「23 项」，脚本内 `console` 与 `smoke_step0.sh` 却写「28 项」。
两处数字需对齐（交付步 01~07=7，含 00 共 8 个视图；断言数固定为 28），否则评审依据不可信。

**🟡6. `smoke_step0.sh` 步骤编号混编**
仅将 `1/4→1/5`、`2/4→2/5`、`3/4→3/5` 三处改写，末步仍为 `5/5`。若中间原 `4/4` 未同步改名，将出现 `1/5,2/5,3/5,4/4,5/5` 的混编，需统一。

**🟡7. `get_active_change` 的 git 状态判定过粗**
`[l for l in lines if "M" in l[:2]]` 对 ` M / MM / M ` 一律视为修改，无法区分重命名与顺序；且"优先取 modified"在用户实际改的是未跟踪新变更目录时会选错。建议显式按状态码字符集匹配。

**🟡8. 迁移「零 active 不激活母版」未评估下游**
断言 10/20 固化「无 active 时禁止激活母版或镜像」。需确认下游读取 active 的消费端（阶段四官网等）在**某槽位仅存留档/镜像**时不会取空导致空白，否则属逻辑漏洞。

---

## 四、优化建议（🟢）

- **🟢9.** `args.test` 失败分支（`resp` 为空）未显式 `sys.exit(1)`，测试失败会继续走主审查流程，退出码语义不清，建议补齐。
- **🟢10.** Emoji 一致性：同一提交在 smoke 测试中删除了 `🎉`，但 `workbuddy_reviewer.py` 仍保留 `🔴`。前者属企业交付脚本、后者属 CLI 工具，虽不在 AGENTS §3.3 严格范围内，仍建议统一去除以保证仓库口径一致。
- **🟢11.** 审查桥会把未跟踪文件全文（最多 30k 字/文件）喂给模型，建议增加体积上限与敏感文件名过滤。
- **🟢12.** Diff 未展示 `main.js` 新增注册与 `__GEO_STEP3__~__GEO_STEP7__` mount key。请确认四个新组件岛都已注册，否则 `mount('#stepN-app-root')` 会静默 no-op，页面空白。
- **🟢13.** `renderStep5QaCardPanel / renderStep6DistributePanel` 等函数名与"阶段序号"强耦合，本次已因调序产生大量别名（`renderStep3PrincetonPanel = renderStep4WebsitePanel`）。建议改以 viewId 命名，避免下次调序再次连锁改名。

---

## 五、值得肯定

- `workbuddy_reviewer.py` 改用 **stdin 管道传递 prompt**，彻底规避 `ARG_MAX` 溢出；diff 提取改为 `--stat + 业务目录 + 排除产物 + 未跟踪源码`，且**只读不 `git add/reset`**，消除了改写用户索引的隐患。
- 阶段零文案将「底牌 / 基线」替换为「生效版本 / 初测推荐」，**契合 AGENTS §3.5 禁自造词**条款。
- `formatReason` 集中化错误文案、`activateTabInStack` 收敛 Tab 逻辑，方向正确。
- 历史 viewId 兼容映射 + 隐藏留档 DOM，降级回滚意识良好。

---

[需修正]


---

### [2026-09-30 11:42] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# GEO 阶段二/阶段三改造 — 代码审查报告

**审查范围**：proposal.md / design.md / tasks.md 对照下方源码 Diff（`git diff --stat` 28 文件 + 业务源码变更）。
**总体判断**：方向正确、分层清晰（生熟两分、人机两分、8 道工序、SSOT 收敛），但存在若干**阻断级交付缺口**与契约不一致，当前状态不具备合并/归档条件。

---

## 🔴 必须改（阻断级）

**🔴1　关键新增文件未纳入本次改动，存在构建中断风险**
`web/step0-src/Step2App.vue` 新增引入 `./components/studio/DistillSheet.vue` 与 `./components/studio/StudioHeader.vue`；`web/index.html` 新增 `<div id="step7-app-root">` 且 `renderStep7AcceptancePanel` 依赖 `window.__GEO_STEP7__`。但 `git diff --stat` 中**既无 `DistillSheet.vue`、`StudioHeader.vue`，也无 `Step7App.vue`**。
- 影响：这些若为未跟踪（untracked）文件，提交遗漏或对端 IDE 拉取后 `npm run build:step0` 将因模块解析失败直接中断；阶段二"盖板蒸馏"与阶段七"资产交接"整块不可用（`if (window.__GEO_STEP7__)` 静默 no-op → 空白面板）。
- 要求：提交前 `git add` 全部新组件与入口文件并纳入 diff，补全 tasks.md 4.2 的"打包验证"证据。

**🔴2　StudioSop `prop` 契约不一致，右侧 SOP 面板可能整体空白**
`Step2App.vue` / 新 `Step3App.vue` 传的是 `:stage-meta="STAGE_2_META"`（右栏），而原 `Step2App` 传 `:sop-steps="STAGE_2_META.sopSteps"`；而本次 `StudioSop.vue` 仅 **+10 行（新增插槽）**，未见 prop 改名/兼容逻辑。
- 风险：若组件仍只读 `props.sopSteps`，则 `stageMeta` 被忽略，`idx` 不成立，插槽 `#step-1/#step-2`（消歧四要素指示灯、一键合流按钮）**永不渲染**——design.md §4.1 的核心复用契约落空。
- 要求：确认 `StudioSop` 已声明 `stageMeta`（或保留 `sopSteps`），全阶段（Step0~Step7）调用方 prop 名统一。

**🔴3　历史 viewId 别名"面板错位"，宣称的别名容错不成立**
`VIEW_META` / `isDeliveryStepView` 保留 `step-3-princeton→step4`、`step-4-qacard→step5`、`step-4-distribute→step6`、`step-5-acceptance→step7` 别名，且 `initForView` 显式分支渲染（`if (viewId === 'step-4-website' || viewId === 'step-3-princeton') renderStep4WebsitePanel()`）。
- 但对应 DOM `panel-step-3-princeton` / `panel-step-4-qacard` / `panel-step-4-distribute` / `panel-step-5-acceptance` 内的 Vue 根节点（`step3/4/5/6-app-root`）**已被删除**，Vue 只挂到新面板 `panel-step-4-website` 等的根节点上。
- 结果：走别名进入时显示的是无挂载点的遗留面板（`legacy-*` 又是 `hidden`）→ **空白工作区**。
- 要求：要么在 `switchView` 中将别名规范化为新 viewId 并显示对应新 panel；要么彻底删除别名与 meta 历史项。二者取一，不能"半兼容"。

---

## 🟡 建议改（显著缺陷 / 任务与代码不符）

**🟡1　`isProbeUnready` 未实质重构，tasks 3.4 与代码不符**
`web/index.html` 中该函数仅新增两行注释，判定逻辑 `String((p && p.probe_status) || 'unprobed') === 'unprobed'` **未变**。若 `p` 仍可能来自本地缓存，则"杜绝 localStorage 脏数据绕过"未落地。需指出真正的真相源收敛动作，否则应把 tasks 3.4 改为"补充注释/已满足"。

**🟡2　`geo:project-updated` 事件疑似空转**
建档联动块 `window.dispatchEvent(new CustomEvent('geo:project-updated', ...))` 已派发，但本次 diff 中 Step0~Step7 组件**均未见 `addEventListener('geo:project-updated')`**。若实际靠重置 `__GEO_STEPx_MOUNTED__` + 强制 remount 生效，则事件是死代码；若依赖事件刷新，则监听缺失，建档后各阶段数据不实时刷新。

**🟡3　`buildPairedAnswerTemplate` 题目解析正则易误匹配**
`web/step0-src/Step0App.vue`（约 397 行）`/(?:\[第\s*(\d+)\s*题\][：:]|\b(\d+)[\.、])\s*([^\n]+)/`：第二分支会把正文任意 `N.`（如"3000.00""1.5 万"）当题号，生成错误的配对实测模板。建议加行首锚点 `^\s*\d+[\.、]`，或仅认 `[第N题]`。

**🟡4　交付文本零 Emoji 合规存疑**
AGENTS §3.3 严禁交付物出现 Emoji。但 `tests/smoke_studio_artifacts.mjs` 断言 26 的标准版标题出现 `⭐ 主力`。需确认 `generateUnifiedIdentityCard` / `synthesizePrincetonMaster` / `generateHedgeList` 的输出模板**均 0 emoji**，并增补一条"生成内容无 Emoji"的断言固化。

**🟡5　`workbuddy_reviewer.py` 改 stdin 传 prompt，需确认 CLI 兼容**
新实现 `cmd=[CODEBUDDY_BIN,"-p","--model",model]` + `subprocess.run(input=prompt)`。若 `codebuddy -p` 要求 prompt 作为参数，则会阻塞/空跑。另需确认文件顶部已 `import re`（新代码用 `re.search`，且被 `except Exception: pass` 吞掉，出问题会静默退化难排查）。

**🟡6　纯函数/状态导出与模板引用需全量核对**
`Step3App` 模板引用 `isExtracting / stage2Readiness / handleExtractFromStage2 / cardAudit / handleCopyActiveContent / isMasterLocked`；`Step2App` 引用 `assetsHealth / viewMode / crawlingUrl / isScraping / sortingText / isSorting / showSorterCard / s1~s6Form / syncFormToMarkdown / openDistillSheet` 等。diff 未展示 `useStep2.js / useStep3.js` 导出，任一漏导出即为运行期 `undefined`（预览空白、按钮无响应）。

**🟡7　StudioEditor 事件名去重需确认**
Step0/Step1 删除了 camelCase 重复监听（`@adopt-file` 与 `@adoptFile` 并存），这是正确的去重；但需确认 `StudioEditor.vue` 实际 `emit` 的是 kebab-case，否则"采纳/恢复"按钮会失联。

---

## 🟢 优化建议

- **🟢1 渲染函数面条化**：`renderStep7AcceptancePanel` 与各阶段渲染函数逐行重复（fetch→mount→createIcons）。建议抽 `renderStagePanel(rootId, globalKey, mountedKey)` 工厂，契合"拒绝重复面条代码"。
- **🟢2 文档签名漂移**：proposal 中 `generateUnifiedIdentityCard(pData, s1, hedgeOpts)`、`generateHedgeList(pData, hedgeOpts)` 为多参，测试与实现均为单参；design §3.1 称口径卡来源含 S1，实现仅消费 pData。请回写文档对齐。
- **🟢3 测试与文案强耦合**：断言 26 通过正则替换 `### ① 短版` 标题来构造超标场景，文案一改测试即雪崩。建议把口径卡骨架抽为共享常量后再断言。
- **🟢4 死代码清理**：Step2 中 `handleScrapeWebsite`、`showSorterCard` 等在被新盖板流程接管后可能已无引用，建议清理以免误读。
- **🟢5 字数口径**：`checkDraftTextLimit` 建议统一为 `Array.from(text).length`（兼容代理对/emoji），并与 UI `draftCharCount` 同源，避免 8500 护栏两侧判定不一致。
- **🟢6 脚本编号**：`smoke_step0.sh` 已改 `x/5`，请确认中间"清单份数"步骤号同步为 `4/5`，避免跳号（diff 截断未能确认）。

---

## 方案文档一致性小结
- ✅ 8 道工序（00~07）、三槽位字典、人机两分过滤、1.x 单调派生、9 因子合流、消歧红绿灯——design 与 tasks 描述完整，且测试断言 13~28 覆盖到位。
- ⚠️ 上述 🔴1~🔴3 属"任务标记 [x] 但交付物不完整/契约不一致"，与 tasks.md 第 3、4 节的完成声明冲突，需在复审中作为必改项追踪。

---

[需修正]


---

### [2026-09-30 11:46] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# GEO 项目代码审查报告（stage=code）

审查对象：《阶段二素材资产库日常循环与阶段三企业母盘统一口径卡》变更（33 files / +9331 −4496）。以下为纯文本审查结论，未调用任何工具。

---

## 一、总体判断

方案的**业务分层（生料 02 / 熟料 03）与工序顺延（00~07）设计清晰**，槽位字典、SSOT 收敛、门禁 Fail-Closed、版本标签隔离等方向均与 proposal/design 自洽，测试覆盖度显著提升。但**代码层存在一处必然抛错的运行时缺陷**，以及若干“文档声称已做、但凭当前 diff 无法证实、且失败后会静默丢功能”的高风险点。当前不具备直接归档条件。

---

## 二、🔴 必须改（Must Fix）

### 🔴1. `buildPairedAnswerTemplate` 使用未声明变量 `questions`，必然抛 `ReferenceError`

`web/step0-src/Step0App.vue` 新增函数：

```js
function buildPairedAnswerTemplate(questionText, {...}) {
  const lines = (questionText || '').split('\n');
  const qRegex = /^\s*(?:\[第\s*(\d+)\s*题\][：:]|(\d+)[\.、])\s*([^\n]+)/;
  for (const line of lines) {
    const m = line.match(qRegex);
    if (m && m[3]) {
      questions.push(m[3].trim());   // ← questions 从未声明
    }
  }
  ...
  const targetQuestions = questions.length > 0 ? questions : defaultQuestions; // ← ReferenceError
```

Vue SFC 经 ESM 编译后为严格模式，读取未声明的 `questions` 会直接抛异常。触发路径非常核心：
- 采纳 **N≥2** 版本的提问（`isV1=false`，`files.value[pairCandidateName]` 不存在）→ 必走该函数 → 抛错；
- V1 首发但 `02_豆包实测回答记录_初测.txt` 无内容时同样会走该分支。

后果：阶段零“问答成对生成”这一本次重点新增能力在真机上会直接报错、中断采纳流程。**必须补 `const questions = [];`**，并建议在测试中新增一条针对 `buildPairedAnswerTemplate`（可从 Step0App 抽出为纯函数）的断言。

> 提示：该函数被设计为“纯文本模板生成”，却内联在组件内，导致 28 项断言无法覆盖它。这正是 🔴2 之外它得以漏网的原因——建议下沉到 `stage0Config.js` 之类的纯模块。

### 🔴2. 岛屿注册与渲染函数“错位改名”必须核对（否则面板张冠李戴或空白）

`web/index.html` 中函数是**只改名字、不改函数体**的方式顺延的：

| 旧函数（旧语义 / 挂载点） | 新函数（新语义） | 函数体挂载点（未改） |
| :--- | :--- | :--- |
| `renderStep3PrincetonPanel`（旧=官网） | `renderStep3MasterPanel`（新=母盘） | `__GEO_STEP3__` / `#step3-app-root` |
| `renderStep4QaCardPanel`（旧=答题卡） | `renderStep4WebsitePanel`（新=官网） | `__GEO_STEP4__` / `#step4-app-root` |
| `renderStep5DistributePanel`（旧=分发） | `renderStep5QaCardPanel`（新=答题卡） | `__GEO_STEP5__` / `#step5-app-root` |
| `renderStep6AcceptancePanel`（旧=交接） | `renderStep6DistributePanel`（新=分发） | `__GEO_STEP6__` / `#step6-app-root` |

该方案**只有 `web/step0-src/main.js` 把 `window.__GEO_STEP3__~__GEO_STEP7__` 全部按“新语义”重挂**时才成立（即 `__GEO_STEP3__=母盘`、`__GEO_STEP4__=官网`…）。若 main.js 未同步位移，就会出现“点 03 母盘却渲染官网 / 点 04 官网渲染答题卡”的串台。

当前 diff **看不到 main.js 的改动内容**（仅 stat）。请务必核对并给出证据（NE1 上逐一点击 03~07 验证渲染对象正确）。这是一处**依赖隐式约定、极易回归**的改名手法，建议改为显式的 `ISLAND_BY_VIEW` 映射表，而非函数别名链。

### 🔴3. `StudioSop` 槽位注入需证实——否则阶段三关键动作按钮会“静默消失”

design 4.1 明确要求 `StudioSop.vue` 提供 `<slot :name="'step-' + (idx+1)">`，Step3App 依赖 `#step-1`（“一键合流提取母盘初稿”）、`#step-2`（消歧四要素红绿灯）驱动推进（且各步 `hideProceed: true`）。

但 `git diff --stat` 显示 `StudioSop.vue` 仅 `10 +` 行改动。Vue 对**未定义的具名插槽内容会静默丢弃**——若槽位未真正渲染，用户将看不到合流按钮与质检指示灯，且因 SOP 步骤已 `hideProceed`，**阶段三将无法推进且无任何报错**。

请核对：StudioSop 是否真正 `v-for` 渲染了 `step-N` 插槽；`stage-meta` / `expand-all` 两个 prop 是否均已支持（Step2App 由旧 `:sop-steps` 改为 `:stage-meta`）。

### 🔴4. 新增模板绑定是否全部来自 composable，需逐项核对

以下标识符在模板中被引用，但均**未出现在可见的 `useStepN()` 解构片段**中，若缺失即为“点击无响应 / 控制台报错”：

- Step2App：`handleSaveActiveFile`、`handleUpdateContent`（以及 `StudioHeader` 的 `@select-tab/@close-tab` 回调）。
- Step3App：`isMasterLocked`、`cardAudit`、`stage2Readiness`、`isExtracting`、`handleExtractFromStage2`、`handleCopyActiveContent`（注意旧名为 `handleCopyContent`）、`activeFile?.updatedAt`。

请以“在 NE1 8088 真机打开 02/03 页面并触发每个按钮”为验收口径，逐项确认，不接受仅凭编译通过判断。

---

## 三、🟡 建议改（Should Fix）

1. **新回答文件目录疑似写错**：`handleAdoptFile` 中新建 `category:'answers'` 的文件却写 `dir: '豆包出的题目'`。若文件树按 `dir` 分组，回答会挂到“题目”节点下。请核对并统一。
2. **`scripts/workbuddy_reviewer.py` 可能缺 `import re`**：`get_active_change` 新增 `re.search(r"openspec/changes/([^/]+)/", ...)`，但 diff 未新增 `import re`。该段位于 `try/except Exception: pass` 内，即便 `NameError` 也会被吞掉 → “用 git status 探测活跃变更”这一新能力**静默失效并回退**。请确认 `re` 已导入，且不建议用裸 `except: pass` 掩盖此类错误。
3. **僵尸面板残留**：`panel-step-4-qacard`、`panel-step-4-distribute`、`panel-step-5-acceptance` 的挂载子节点已被移除，但空壳 div 与 `data-page-node-id`（`panelStep4QaCard` 等）仍保留。既属死 DOM，也可能与可视化页面框架的 node-id 选择器冲突，建议清理或明确标注为留档。
4. **`data-page-node-id` 复用/重复**：新导航项复用了旧节点 id（如 `nav-step-4-website` 用 `vl4ZnI8rm5D8NKDz3aELPJ`、`nav-step-5-qacard` 用 `navStep4QaCard`）。若框架按该属性查询，存在多节点命中风险，建议为新增项生成唯一 id。
5. **`currentViewId` 引用存疑**：建档保存回调中 `if (typeof currentViewId==='string' && currentViewId==='step-2-scaffold')` —— 代码库通行变量名为 `currentView` / `savedView`。若该变量不存在，分支恒不成立（因 `typeof` 保护不报错），导致“建档后阶段二不立即刷新”，与注释承诺不符。
6. **tasks.md 全量 `[x]` 过早**：含 `4.3 浏览器真机体验验收与 WorkBuddy 审查闭环` 亦已勾选，而本次审查尚在进行。按 AGENTS §1.3/§2，在用户或对端确认前不应把评审闭环标记为完成。
7. **文档与代码范围不一致**：proposal 的 Impact 未列出 `scripts/workbuddy_reviewer.py`、`scripts/smoke_step0.sh` 及新增 `StudioHeader.vue`，需补齐，避免“影响分析”失真。
8. **N≥2 采纳时的配对语义 wart**：新提问版本采纳后，其 `pairFile` 指向的是**旧回答**（`currentActiveAnswer`），同时会回写旧回答的 `pairFile` 指向新提问，形成短暂的“错配引用”。虽不致命，但建议在 UI 上明确标注“配对回答待实测回填”。

---

## 四、🟢 优化建议（Nice to Have）

1. **红/黄语义边界需明确**：design/tasks 写“超标**红色**拦截”，而 Step2 超限实现用 `amber`、Step3 质检失败用 `red`。AGENTS §3.5 对红色有强保护，请明确“阻断性校验失败”是否属允许用红的“运行报错”范畴，并让文档与实现口径一致。
2. **纯函数纯净度**：`buildPairedAnswerTemplate` 内 `new Date().toLocaleDateString()` 使输出不可复现，建议将时间作为入参注入，便于断言。
3. **口径统一**：文案“8500 汉字 (8K Token)”中“汉字 ≠ Token”，建议统一为“字符数”，避免误导。
4. **断言计数**：当前以 28 个散落的 `console.log('[PASS]')` 计数，注释与总数易漂移，建议改为断言数组 + 统一渲染。
5. **别名收敛**：现同时存在“函数别名（`renderStep4QaCardPanel = renderStep5QaCardPanel`）”与“视图别名（`LEGACY_VIEW_REDIRECT_MAP`）”两套兼容层，建议合并为单一映射表，降低认知负担。
6. **Step2 双录入面**：中间区同时保留内联 textarea（`handleUpdateRawDraft`）与 DistillSheet 盖板两套入口，建议明确主入口、次入口收敛，减少状态面。

---

## 五、规范符合性核对（结论）

| 核对项 | 结论 |
| :--- | :--- |
| 生熟两分 / 母盘仅消费 S1~S6 主版本（人机两分） | ✅ 设计自洽，测试断言 15/21/22/27 覆盖到位 |
| 门禁 Fail-Closed（以服务端 `probe_status` 为真相源） | ✅ 方向正确（`isProbeUnready` 已收敛） |
| 版本标签隔离（仅 V1 首发同步） | ✅ 代码与 proposal 一致，修复了旧覆写 |
| 零 Emoji 交付约束 | ✅ 已移除 `🎉`，新增断言 26/27/28 固化为 0 Emoji（CLI 打印 🔴 属开发工具，不违规） |
| 双栏布局 / DOM 标签闭合铁律（§6.4） | ⚠️ Step2/Step3 模板大手改，`<template #actions>` 内是否残留悬空 `</div>`（会导致栅格塌陷）需以 `check_article_styles.py` 同口径做一次 DOM 平衡核验 |
| 阶段隔离与单步停步（§1.3） | ⚠️ tasks 全量勾选并将“审查闭环”置为完成，违反“评审未结束不得标记闭环” |
| 编译/验证机器口径（§4.5） | ✅ 声明在 NE1 编译；请确保无本地重型编译`

---

## 六、最终结论

**存在 1 处必然抛错的运行时缺陷（🔴1），并叠加 3 处“失败即静默丢功能/串台”的隐式依赖（🔴2~🔴4）**，均属 P0 阻塞项，须修复并在 NE1 8088 真机逐面板复验后方可复审。

[需修正]
