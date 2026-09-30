# 审查与讨论实录 · 阶段二素材库日常循环与盖板蒸馏重构

## 2026-09-30 09:10 · 师弟与师兄 (Grill 深度探讨与架构对齐启动)

- **探讨主题**：阶段二素材库从“线性死锁流水线”向“初始化 + 日常循环收集场景”演进；盖板页面交互定义；左侧单主文件 + 1.x 纯增量分片模型。
- **原始需求留档**：详见 `原始需求/2026-09-30-师弟关于素材库循环收集与盖板蒸馏的原始要求.md`。
- **结论标签**：`[探讨中]`

### 【已达成共识 1 · 增量切片落盘规则 (师弟定规)】
1. **纯新增内容**：盖板内每确认一条切片，就在所属分类下派生一个文件（第 1 条确认生成 `1.1`，第 2 条生成 `1.2`）；
2. **不带原文**：`1.1`、`1.2` 的正文内容只存本次新提取出来的纯新增文字，不需要每次带上原主文件的内容；
3. **结构极简**：每个分类只保留 1 个主文件，后续扩展均作为 `1.x` 独立增补卡片，方便后续 RAG 检索和大模型蒸馏。

### 【已达成共识 2 · 盖板工作台呈现形式 (师弟定规)】
1. **中间主区域盖板化**：点击“蒸馏素材”后，中间主区域直接盖上一层完整的蒸馏操作页（像一块画板盖在原来编辑器上面，保留左侧资源管理器便于对照）；
2. **沉浸式双栏流转**：
   - 左栏：输入网址并快速提取内容，支持人工在打字板上自由增删修改；
   - 右栏：点击【一键蒸馏与分类】后，展示拆分到 6 个分类中的切片卡片列表；
3. **闭环收工即退出**：审核修改一条切片就点【确认入库】一条，全部弄完后点击【完成并返回素材库】，盖板收起，立刻切回原主文件视图。

### 【已达成共识 3 · 右侧动线无锁解耦与日常两大蒸馏场景 (师弟定规)】
1. **彻底废除死板打勾与强行串行锁**：右侧展示步骤卡片，但**绝不强行串行绑定，不用打勾，没有锁**，用户日常可随时反复执行并修改；
2. **场景一：网页蒸馏**：
   - 用户在卡片内填入网页网址 ➔ 点击进行网页蒸馏 ➔ 中间跳出盖板 ➔ 系统自动提取该网页核心内容并填入写字板 ➔ 蒸馏拆分为 6 大分类 ➔ 逐条确认入库 ➔ 跳出盖板；
3. **场景二：文案蒸馏**：
   - 用户直接复制粘贴文案素材 ➔ 点击进行文案蒸馏 ➔ 中间跳出盖板 ➔ 蒸馏拆分为 6 大分类 ➔ 逐条确认入库 ➔ 跳出盖板。


---

### [2026-09-30 09:41] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# GEO 阶段二重构 · 严格对抗式代码审查报告

## 结论先行

本次变更在「阶段二素材库动线解锁 + 全屏盖板蒸馏」方向正确，纯函数抽取（`computeStage2ChunkVersion` / `activateTabInStack` / `formatReason`）与单测扩展值得肯定；但存在 **1 个直接击穿核心设计不变式的严重缺陷**（`isMasterSourceFile` 把人机两分契约反着做了），叠加 **两套并存的蒸馏/入库流水线（重复面条）** 与 **代码显著超出 proposal 声明的 Impact 范围**。**不予通过，需修正。**

---

## 🔴 必须改（Must Fix）

### 🔴1. `isMasterSourceFile` 会把 `1.x` 增补分片误判为主文件——核心「人机两分契约」被反向击穿
`studioArtifactConfig.js`：
```js
const base = filename.replace(/\.[^.]+$/, '');
return /^S\d+(_|$)/i.test(base) && !/^S\d+\.\d+/i.test(base);
```
设计 1.1 明确增补分片命名格式为 `S2_核心产品与价格承诺_增补_1.1.md`，**该名字以 `S2_` 开头**，因此：
- `^S\d+(_|$)` → `S2_` 命中 → true
- `^S\d+\.\d+` → 前缀是 `S2_` 而非 `S2.` → 负向判定不成立 → `!false = true`

结果 `isMasterSourceFile('S2_..._增补_1.1.md') === true`，`filterMasterSourceFiles` 会把所有增量分片当作主版本喂给母盘/AI。这与设计「人机两分，只消费 S 主版本」「1.x 独立沉淀供 RAG」的**核心不变式完全相反**。

**更严重的是测试给了假绿灯**：断言 15 仅用点号命名 `S1.1_草稿.md`、`S4.2_修改版.md` 验证，未覆盖真实的 `_增补_1.x` 命名，导致缺陷被放行。
**修正**：判定需排除 `/_增补_1\.\d+/` 与 `S\d+\.\d+`，并补充以真实命名 `S2_…_增补_1.1.md` 为输入的回归断言。

### 🔴2. 两套并存的蒸馏 + 入库流水线（重复面条代码，直接违反 proposal 与 AGENTS「拒绝打补丁与重复」）
- `Step2App.vue` 中 `DistillSheet`（`isDistillSheetOpen` → `handleAdoptDistillChunk`）是新盖板流水线；
- 同一文件底部仍保留 `isReviewModalOpen`（AI 语义切块审核席 → `handleStartChunking`/`handleAdoptChunk`/`handleAdoptAllChunks`）与 `isDuplicateModalOpen`（RAG 去重合并 → `handleMergeDuplicate`）两套**旧弹窗流水线**。

proposal What#3 与 design 3.1 白纸黑字要求「**彻底告别小弹窗**」「废除死锁」。现在等于新旧两条流水线同时存活，两套各自的切块状态（`chunks` vs `candidateChunks`）与版本派生各算各的，必然产生 `1.x` 版本号冲突与状态错乱。
**修正**：删除审核弹窗与去重弹窗流水线，统一收口到盖板；或明确说明为何保留（并同步改 design）。

### 🔴3. 变更范围显著超出 proposal 声明的 Impact（流程合规）
proposal Impact 仅列 `Step2App.vue / DistillSheet.vue / studioArtifactConfig.js / useStep2.js`，但实际 diff 还改动：
`Step0App.vue`、`Step1App.vue`、`StudioEditor.vue`、`StudioSop.vue`、`StudioHeader.vue`、`stage1Config.js`、`scripts/workbuddy_reviewer.py`、`scripts/smoke_step0.sh`、`web/index.html`（含 `isProbeUnready` 改读 localStorage、导航改名）。

AGENTS §1 要求 proposal 覆盖 Impact。上述阶段零/一与探活逻辑改动**未在 proposal/tasks 中立项**，属于隐性范围蔓延（尤其 `index.html` 用前端 localStorage 反推 readiness 覆盖服务端 `probe_status`，属功能语义变更）。需回补 proposal/tasks 或拆分独立变更。

### 🔴4. 双入口并发点击会造成 `1.x` 版本号竞争（数据一致性）
`DistillSheet.handleAdoptSingleChunk` 用 `computeStage2ChunkVersion(props.files, slotKey)` 读的是 `props.files`，而 `files` 实际由父组件拥有。同一 tick 内连续点击两条切片时，父组件 `files` 尚未回灌 props，两次都会算出同一个 `1.1` → 文件名/版本碰撞覆盖。
**修正**：切块入库版本号应由父级在实际写入时统一分配（single source of truth），或在 emit 前做本地递增占位。

---

## 🟡 建议改（Should Fix）

### 🟡1. design.md 1.1 分类表与 `CANONICAL_SLOT_DICT` 主文件名不一致
| 分类 | design.md | 代码 `CANONICAL_SLOT_DICT` |
| :-- | :-- | :-- |
| S4 | `S4_同行对比与差异化策略.md` | `S4_对标竞品参数对比表_优搜网络.md` |
| S5 | `S5_经典案例故事_本地实体.md` | `S5_经典案例故事_本地实体GEO突围.md` |
| S6 | `S6_权威资质与客户凭据.md` | `S6_权威背书与资质凭据.md` |

设计表已过期，且 `S4` 主文件名**硬编码了具体竞品品牌「优搜网络」**，污染多租户 SSOT 配置。需二者对齐并去除租户专属字样。

### 🟡2. `canDeleteFile` 阶段二一刀切禁删，与 design 的「含已入废纸篓历史」自相矛盾
```js
if (stage === 'step2' || /^S[1-6]_/i.test(file.name || '')) return false;
```
该规则使所有 `S*_…_增补_1.x.md` 永远不可删，而 `computeStage2ChunkVersion` 的注释/设计 1.2 明确「扫描包含已入废纸篓历史」——该分支成为**不可达死代码**。需二选一：要么允许废弃分片入废纸篓，要么删除设计中的废纸篓描述。

### 🟡3. 阶段二「双编辑器」数据不同步，存在丢失输入风险
- `Step2App` 中心 `textarea` 绑定 `rawMaterialDraft`；
- `DistillSheet` 内部 `draftText = ref(props.initialText)`，**无 `watch(props.initialText)`**，且退出盖板时不回写 `rawMaterialDraft`。

用户在盖板中润色的文本关闭后即丢失，且两处草稿互相不可见。建议盖板文案与父级 `rawMaterialDraft` 双向同步（或明确盖板为唯一编辑区）。

### 🟡4. proposal 对外 Capabilities 命名与实现不一致
proposal 声明 `fetchWebScraping(url)` / `distillAndCategorize(rawText)` / `adoptSingleChunk(chunk, category)`，实现为 `handleScrape` / `handleStartDistill` / `handleAdoptSingleChunk`。对外能力契约与代码脱节，需在 proposal 或代码注释中对齐。

### 🟡5. 断言计数三处不一致（19 / 20 / 21），tasks 4.2「100% PASS」缺少可信锚点
`tests/smoke_studio_artifacts.mjs` 头部注释写「19 项」，运行日志 `20 项自动化断言`，末尾 `21/21`，`smoke_step0.sh` 又写「21 项」。计数混乱削弱 CI 结果可信度，需统一。

### 🟡6. `normalizeVersionTag` 语义改变为「无条件从 tag/文件名抽取首个数字」
新实现 `(tag||'').match(/(\d+(?:\.\d+)?)/)` 对含数字的非版本标签（如历史脏数据里的 `推荐版02`）会强行生成 `V2`，属静默语义收敛。建议在迁移路径上加白名单/校验，避免误归一化。

### 🟡7. 盖板覆盖范围表述冲突
proposal What#3「覆盖度 90%+ 大盖板」vs design 2.1「遮盖原中间编辑器」vs 实现（`DistillSheet` 仅占中栏 `flex-1`，非 90% 全屏）。请以实现为准统一 proposal/design 措辞。

---

## 🟢 优化建议（Nice to Have）

- 🟢1. `getActiveBadgeText` 阶段二分支直接返回分类名，丢失 `isRetired/isDeleted` 状态语义，归档态文件在徽章上无法区分。
- 🟢2. `StudioHeader.vue` 已抽为通用组件，但 `Step2App` 中栏仍自研 tab/编辑区，未复用 `StudioEditor`，存在同类逻辑两处维护。
- 🟢3. `isMasterSourceFile` 的 `S\d+` 未限 1~6，未来若出现 `S10_` 会误判；建议收紧为 `S[1-6]`。
- 🟢4. 浏览器兼容性方面，`Object.fromEntries` / 可选链 / `?.` 在现代 Safari/Chrome 均可用，`activateTabInStack`、`computeStage2ChunkVersion`、`semanticChunkRawMaterial` 均为不依赖 DOM 的纯函数，本次未发现兼容性风险（符合 AGENTS 桌面端双内核要求）。
- 🟢5. tasks 4.3（NE1 8088 真机验收）正确留白未勾选，符合 AGENTS「AI 不得代勾人工验收」——此项执行规范。

---

## 审查局限说明
本次提供的 diff 中 `stage2Config.js` 与 `useStep2.js` 主体被截断，`semanticChunkRawMaterial` / `handleAdoptDistillChunk` / 去重算法内部实现**未能完整核验**；上述 🟡7 与落盘持久化是否真正闭环，建议补全后再复核。

---

[需修正]


---

### [2026-09-30 09:46] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# GEO 阶段二盖板蒸馏重构 · 代码审查报告

审查范围：proposal.md / design.md / tasks.md 与 web、scripts、tests 源码 Diff。以下为纯文本结论。

---

## 一、🔴 必须改（阻断项）

### 🔴1. `normalizeVersionTag` 对阶段二前缀发生「版本号膨胀」，迁移非幂等（数据完整性受损）
`studioArtifactConfig.js` 中 `CANONICAL_SLOT_DICT.slot_stage2_s2.prefix = 'S2.'`，而新版 `normalizeVersionTag` 用：
```js
const mNum = (tag||'').match(/(\d+(?:\.\d+)?)/) || ...
return `${prefix}${num}`;
```
- 输入 `S2.1` → 贪心匹配到 `2.1` → 输出 `S2.2.1`；输入 `S2.2` → `S2.2.2`。
- 再次迁移时 `S2.2.1` 又被匹配为 `2.2.1` → `S2.2.2.1`……**每次刷新/迁移持续膨胀，迁移不再幂等**。
- `migrateAndNormalizeFiles` 步骤 4 对「有 versionTag 且槽位有效」的文件无条件归一化，阶段二文件全部命中，必然触发。
- 断言 10 / 断言 20 的幂等性校验只覆盖 `step1`（prefix 为 `V`，无小数点，天然幂等），**断言 21/22 完全绕开了迁移路径**，因此测试全绿但缺陷潜伏。

### 🔴2. `computeStage2ChunkVersion` 的 tag 反查正则歧义，S1 首片会从 1.2 起跳
```js
const mTag = (f.versionTag || '').match(/1\.(\d+)/);
```
- `S1.1`（S1 主文件被归一化后的 tag）含子串 `1.1` → 被误计为已有分支 1 → `nextBranch=2`，**S1 首个增补分片直接生成 `_增补_1.2`**，违背 design「单调递增自 1.1 起」。
- 断言 21 只验证了 S2（tag `S2.1`，无 `1.` 子串）与 S5，恰好规避 S1；建议补 S1 槽位用例。
- 根因与 🔴1 同源：把「文件名前缀」当成「版本标签前缀」复用，字段语义被重载。

### 🔴3. `canDeleteFile` 删除了空值守卫，Fail-Closed 语义被削弱
```diff
-  if (!file) return false;
+  if (isMasterSourceFile(file.name)) return false;
```
- 原函数是明确的 Fail-Closed 关闸；现 `file` 为 `null/undefined` 时 `file.name` 直接抛 TypeError。
- 该函数在文件树渲染、迁移、后续母盘消费等多点调用，任何一处传入空引用即崩溃。

---

## 二、🟡 建议改

1. **规格与实现不一致（多点）**
   - proposal「What」写 `S2_核心产品与价格承诺_增补1.1.md`（缺下划线），design 与代码为 `_增补_1.1.md`；
   - proposal Capabilities 命名 `handleAdoptDistillChunk`，实现为 `handleAdoptSingleChunk`；
   - proposal 称「覆盖度 90%+ 全屏盖板」，实现仅覆盖中栏（design 2.1 才是中栏，proposal 需订正）。

2. **断言计数三处互相矛盾**
   - `smoke_studio_artifacts.mjs` 头部注释「19 项」、起始 log「20 项」、末尾「22/22 项」；
   - `smoke_step0.sh` 步骤号从 `3/5` 直跳 `5/5`（缺 `4/5`）。属自检可信度问题，须统一。

3. **proposal Impact 清单滞后**：实际改动还包含 `Step0App.vue`、`Stage1App/useStep1.js`、`StudioEditor/FileTree/Sop/Header.vue`、`web/index.html`、`workbuddy_reviewer.py`，均未列入 Impact，影响面评估缺失。

4. **迁移中的 active 选取未以「主版本」优先**：`migrateAndNormalizeFiles` 在零 active 兜底时按 `getVerNum` 降序取候选，主文件与 `_增补_1.x` 的 `getVerNum` 会相等（如都为 2.1），可能把 1.x 增补切片激活为槽位生效版，违背 design「每分类仅 1 主文件生效」。建议 tie-break 优先 `isMasterSourceFile`。

5. **`isProbeUnready` 放行逻辑弱化阶段零门禁**：仅凭 localStorage 存在 `activeQa` 或任一带 `isActive` 的文件即返回 ready。而 `initDefaultFiles` 默认即为 active，可能导致门禁形同虚设。需明确这是否为预期。

6. **`Stage2App.vue` 内联 6 套 S1~S6 表单卡片（约数百行重复结构）**，与审查基线「拒绝重复面条代码」相悖，建议抽 `SourceAssetCard` 泛型组件 + 字段配置驱动。

7. **未验证项（Diff 截断）**：`stage2Config.js` 的 `semanticChunkRawMaterial / computeTextSimilarity / findSemanticDuplicates / DEFAULT_SIMILARITY_THRESHOLD / checkDraftTextLimit`、`useStep2.js` 大量导出、以及父级 `handleAdoptDistillChunk` 的「同名二次单调递增派生校验」均未在可见 Diff 中出现；若缺任一导出，`smoke_studio_artifacts.mjs` 会直接 import 失败。请补证据。

8. **数据标记脆弱**：阶段零「第1版」回答被迁移规则 `fn.startsWith(baseSlotName+'_第1版')` 再次打上 `isProtectedArchive=true`，与其同时 `isActive` 状态并存（代码虽在创建时刻意置 false，但迁移会复写）。建议迁移条件排除 `isActive`。

9. **`dir` 字段不一致**：`DistillSheet` 写入 `dir: '分类 2'`，而 `CATEGORY_DIR_MAP` 为 `分类 2 · 产品与价格标准 (S2)`；`getActiveBadgeText` 直接取 `dir`，徽章文案将出现两套口径。

10. **事件名风格**：子组件 `defineEmits('update:draftText')`，父模板 `@update:draft-text`，依赖 Vue 归一化才成立；建议两端统一为 `draftText`。

11. **多租户污染风险**：`CANONICAL_SLOT_DICT` 将客户专属名（`S4_..._优搜网络.md`、`S5_..._本地实体GEO突围.md`）硬编码为全局规范槽位名，跨客户复用会串味。

---

## 三、🟢 优化建议

1. `web/index.html` 仍裸引 `cdn.tailwindcss.com`，与 AGENTS §7.4「严禁裸奔依赖外部 Play CDN」相悖（历史遗留，但本次已触碰该文件，宜同步收敛）。
2. `workbuddy_reviewer.py` 的 console 文案仍含 🔴 Emoji（非交付物，建议清理以统一「0 Emoji」口径）。
3. `competitor` 默认值不一致：`StudioHeader`/`DistillSheet` 为 `优搜网络`，`Stage2App` 传 `区域竞品同行`。
4. `computeStage2ChunkVersion` 未过滤 `isDeleted`（利于防版本复用，但需在注释中明示，避免误读）。
5. `formatDisplayName` 对 `S1.1_草稿.md` 不剥离 `S1.1_` 前缀（`S\d+` 后需 `_`），与主文件命名规则不统一。

---

## 四、值得肯定之处

- 抽出 `StudioHeader.vue` 实现跨阶段复用，`Step0/Step1/Step2` 共用，属正确的架构收敛；
- 清理了 `@adoptFile / @restoreFile` 重复事件绑定，消除面条式冗余；
- 将「底牌」等自造词统一改为「生效版本」，方向与 AGENTS §3.5 禁混谈条款一致；
- 冒烟脚本将 `🎉` 替换为 `[SUCCESS]`，符合 0 Emoji 硬约束；
- tasks.md 4.3「浏览器真机验收」正确留白未代勾，符合单步停步铁律。

---

## 结论

方案方向（无锁日常循环 + 盖板蒸馏 + 人机两分）与 tasks 拆解基本完整，架构复用有提升。但存在两处**数据完整性级缺陷（🔴1/🔴2，版本号膨胀且迁移非幂等）** 与一处**Fail-Closed 守卫回退（🔴3）**，且现有 22 项断言恰好绕开了这两类路径，测试绿灯不等于逻辑闭环。需先修复 🔴 项并补 `step2` 迁移幂等性 / S1 槽位断言，方可复审。

[需修正]


---

### [2026-09-30 09:51] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# 阶段二素材库日常循环与盖板蒸馏重构 — 代码审查报告

## 一、总体结论（结论先行）

本次变更在**纯函数化、SSOT 收敛、人机两分契约、Fail-Closed 守卫**这几条硬骨头上做得扎实：`computeStage2ChunkVersion` / `isMasterSourceFile` / `filterMasterSourceFiles` / `activateTabInStack` / `formatDisplayName` / `normalizeVersionTag` 全部为无 DOM 依赖的纯函数，断言 1~23 覆盖了幂等、单调递增、空引用防崩等关键边界，方向正确。

但作为**规范驱动开发（OpenSpec）**的审查，存在一个必须处理的结构性问题：**本次 Diff 的实际改动范围（3440 行，横跨阶段零 / 一 / 二、config、tests、scripts）远超 proposal / design / tasks 的声明范围**。proposal 只讲"阶段二盖板蒸馏"，diff 却同时重构了阶段零的采纳-回滚-配对、阶段一的槽位映射、`isReadOnlyFile`/`computeAdoptResult`/`migrateAndNormalizeFiles` 核心不变式、Tab 栈、错误文案映射等。这属于**方案与实现不一致（范围蔓延）**，按 AGENTS §1.3 / §2 应回到 `/opsx-review` 订正文档。

因此结论为 **`[需修正]`**（非阻断性崩溃，但治理与设计对齐不达标）。

---

## 二、对照 proposal / design / tasks 的符合性

| 检查项 | 结论 | 说明 |
| :--- | :--- | :--- |
| 左侧单主文件 + `1.x` 增量分片 | 符合 | `computeStage2ChunkVersion` 仅派生 `_增补_1.x`，主文件排除，单调递增 |
| 人机两分（母盘只消费主文件） | 符合 | `isMasterSourceFile` 排除 `_增补_` 与 `\d+\.\d+`，`filterMasterSourceFiles` 正交隔离 |
| 盖板内逐条确认即点即入 | 基本符合 | `DistillSheet.handleAdoptSingleChunk` 单条派生 + 防并发合并视界 |
| 右侧无锁日常循环 | 符合 | `STAGE_2_META` 三大卡片 + 底部推进，已去除串行锁 |
| **盖板形态（提案 vs 设计）** | **不一致** | 提案 What 称"覆盖度 90%+ 的大盖板 / 全屏 Overlay"；design 2.1 称"中间主区域切换…遮盖原中间编辑器"；实现是**中栏内嵌替换**（`<section>` 内 `v-if` 切换），非全屏浮层。三方口径不齐 |
| **测试断言范围** | **不一致** | proposal Impact 仅写"扩展断言 21 与 22"；tasks 4.1 仅写 S1~S6 契约；实际新增断言 13~23（11 项），且 13/14/20/23 大量针对**阶段零/一** |
| **tasks 与 diff 对齐** | **不完整** | diff 中的阶段零配对重构、阶段一 `SLOT_KEY_MAP` 派生、`activateTabInStack`、`formatReason`、`isProbeUnready` 等均无对应任务条目 |

> 结论：**能力实现大体达标，但"文档-实现"契约断裂**，这是本次最需要修正的地方。

---

## 三、🔴 必须改

### 🔴1 变更范围严重超出 OpenSpec 提案（范围蔓延）
diff 同时大改阶段零/阶段一的核心算法与不变式，但 proposal/design/tasks 均未覆盖：
- 阶段零采纳-回滚-成对版本联动（`Step0App.handleAdoptFile`、`buildPairedAnswerTemplate`、`stampActiveQaHeader` 文案）
- 只读判定重写（`isReadOnlyFile` 将 `isActive` 提到 `isProtectedArchive` 之前，解锁母版编辑死锁）
- 采纳候选白名单放开（`computeAdoptResult` 允许 `isProtectedArchive` 回滚）与同槽退级豁免逻辑
- 迁移算法零-active 兜底重写（`migrateAndNormalizeFiles`）
- 阶段一 `SLOT_KEY_MAP` 改为由 `CANONICAL_SLOT_DICT` 派生
- `activateTabInStack` / `formatReason` / `isProbeUnready` 等

**要求**：要么把这些改动补入 proposal/design/tasks 并标注对应的 🔴 来源，要么拆分为独立变更。当前状态违反 AGENTS §1 "规范文件必须覆盖改动范围" 与 §2 评审协议，**不得进入归档**。

### 🔴2 提案与设计对"盖板形态"定义冲突，实现只满足其一
- proposal What Changes §3：明确"全屏盖板页面（Sheet / Overlay）""覆盖度 90%+ 的大盖板工作台"。
- design 2.1：降级为"中间主区域切换为沉浸式盖板视图，遮盖原中间编辑器"。
- 实现（`Step2App.vue` 中栏 `<section>` 内 `DistillSheet v-if="isDistillSheetOpen"`）：是**中栏就地替换**，不覆盖左树与右 SOP，更谈不上 90% 覆盖。

三者必须收敛到一个口径（建议以 design 为准并回改 proposal 措辞，或在 design 中明确"不做全屏浮层"的理由），否则后续验收无唯一判定标准。

### 🔴3 tasks.md 测试条目与实际断言数量/范围不符
`smoke_step0.sh` 已改为"23 项"，但 `tasks.md` 4.1 只描述了 S1~S6 契约三条，未列 13/14/20/23（阶段零 QA 镜像、母版回滚、迁移收敛），导致"任务完成度"无法被客观核验。**必须补全 tasks 4.1 的断言清单**。

---

## 四、🟡 建议改

### 🟡1 `DistillSheet` 采纳空内容未拦截
`handleAdoptSingleChunk` 直接把 `chunk.content.trim()` 写入 `newFile.content`，未做空内容守卫。虽 `handleStartDistill` 有 `!draftText.trim()` 门槛，但用户可在切片卡片里把某一 `textarea` 编辑为空白后再点"确认加入"，会产生**空的 `1.x` 增补文件**。建议增加 `if (!chunk.content.trim()) { emit('toast', ...); return; }`。

### 🟡2 采纳失败无回滚，UI 与真实状态可能分叉
`handleAdoptSingleChunk` 先置 `chunk.isAdopted = true` 再 `emit('adopt-chunk')`。若父级 `handleAdoptDistillChunk` 因冲突/异常未落盘，卡片仍显示"已入库"。建议改为**父级确认成功后再置位**（回传 ack 或由 props 驱动 `isAdopted`）。

### 🟡3 8500 上限逻辑三重重复
`stage2Config.checkDraftTextLimit`（默认 8500）、`DistillSheet.isOverLimit`（硬编码 8500）、模板文案"8500 汉字"三处独立。且 `isOverLimit` 用 `draftText.length`（UTF-16 单元）却标注"汉字"，对英文/代理对不精确。建议统一引用同一常量与同一函数。

### 🟡4 `isProbeUnready` 用 localStorage 短路服务端门禁（index.html）
新增逻辑：只要本地存在 `geo_step0_active_qa_*` 或含 active 的 `geo_step0_files_*` 即判定 ready，绕过原本基于 `probe_status` 的拦截。这使**门禁真源从服务端退化为客户端可篡改的 localStorage**，且属于对超大内联脚本的"打补丁"。建议将"已完成阶段零"的状态落到服务端 `projectData`，或至少加注释说明这是临时豁免。

### 🟡5 `StudioFileTree` 新增 `:stage="'step2'"` 但 props 定义未同步可见
Step2App 传入 `stage` / `:show-status-badge="false"`，而 diff 中 `StudioFileTree.vue` 仅改了展示名与 import，未见 `props` 声明更新。若 `stage` 未在 `defineProps` 声明，`canDeleteFile(file, stage)` 将拿到 `undefined`，导致删除守卫第 ⑧ 条（阶段白名单校验）失效。**请核实 props 已声明**，否则属于"表面传参、实际失效"。

### 🟡6 父级 `handleAdoptDistillChunk` 无可见实现与断言
`DistillSheet` emit 的 `adopt-chunk` 由 `useStep2.js`（diff 被截断，912 行）承接，落盘、去重二次单调递增、持久化均未在断言中覆盖。断言 21 只测了纯函数 `computeStage2ChunkVersion`，**"即点即入库"的端到端链路无自动化证据**。建议补一条集成级断言或在 review-log 说明人工验收项。

### 🟡7 阶段一 `SLOT_KEY_MAP` 兜底改为 `slot_misc` 的连带影响
`stage1Config.buildStage1Files` 将未命中槽位的文件一律兜底为 `slot_misc`（原为动态 `slot_xxx`）。这依赖 `resolveSlotKey`/`canDeleteFile` 对 `slot_misc` 的后续纠偏正确，否则可能出现"阶段一文件被判定为不可删/不可采纳"。建议对阶段一四大交付物做一次迁移回归断言。

### 🟡8 AGENTS §3.5 V-W-W-H 说明规范
`DistillSheet` 顶栏仅有单句引导（"提取、删减与人工润色后…"），未按 Value/What/Why/How 四层金字塔组织。若该盖板视为"管理端功能页顶部说明"，则不符合 §3.5。建议补齐四层或明确其不适用。

---

## 五、🟢 优化建议

- 🟢1 `formatDisplayName` 正则 `^(?:\d+|S\d+)_` 无 `i` 标志，小写 `s1_` 不剥离；建议加 `i` 保持一致（虽然规范文件均为大写 S）。
- 🟢2 `isMasterSourceFile` 用 `/\d+\.\d+/` 排除，会误伤"主文件名内合法含小数"的场景（如未来出现 `S2_价格2.5万起.md`）。建议收紧为 `/_增补_/` + `/_第?\d+\.\d+/` 之类的显式分片模式。
- 🟢3 `activateTabInStack` 在全脏时返回 `maxTabs+1` 个标签（仅告警不裁剪），与"上限 6"语义略冲突，可在文档/注释中明确"超限保留待用户处理"。
- 🟢4 `StudioSop` 同时支持 `sopSteps` 与 `stageMeta`，但 Step2App 已改传 `stageMeta`，`sopSteps` 分支成为潜在死代码；建议二选一，避免双入口。
- 🟢5 `scripts/workbuddy_reviewer.py` 输出保留 🔴 等符号（命令行脚本，非企业页面，暂不违规）。但建议与断言输出风格统一为纯文本标签（本次已把测试里的 🎉 改为 `[SUCCESS]`，方向正确，可延续）。
- 🟢6 `DistillSheet.handleScrape` 使用 `/api/probe/single?url=`，前端仅 `encodeURIComponent`。若后端据此发起抓取，需确认服务端有 URL 白名单/内网地址拦截，防 SSRF（后端职责，提示知会）。
- 🟢7 文案脱敏基本到位（"底牌/基线"→"生效版本/推荐出题"），但 `getActiveBadgeText` 对非 step0 仍返回"客户生效底牌"、若干注释仍留"底牌"字样，建议统一收敛。

---

## 六、浏览器兼容性与纯函数审查

- **PC 桌面端（Safari / Chrome 双内核）**：使用到的 `optional chaining`、`Object.fromEntries`、`Object.entries`、模板字符串、`fetch`、`toLocaleDateString` 均在 Safari 13.1+ / Chrome 80+ 支持，**无兼容性阻断**。
- **纯函数不依赖 DOM**：`computeStage2ChunkVersion`、`isMasterSourceFile`、`filterMasterSourceFiles`、`activateTabInStack`、`formatDisplayName`、`normalizeVersionTag`、`formatReason` 均无 DOM/localStorage 依赖，可在 Node 直测（断言已证实），**符合 AGENTS §4.5 "测试真相源在 NE1" 的可测性要求**。
- **DOM 侧组件**（`DistillSheet`/`StudioHeader`）对 `window.lucide`、`fetch`、`window.showToast` 均做了 `typeof window !== 'undefined'` 守卫，较稳健。
- **未在本地执行重型编译**：tasks 4.2 明确在 NE1 执行 `npm run build:step0 && npm run smoke:step0`，符合 AGENTS §4.5 与 §5.4，合规。

---

## 七、唯一结论

需修正项集中在**治理与文档对齐**（🔴1/2/3），而非不可用的代码缺陷；纯函数与守卫设计质量高，方向正确。建议按 `/opsx-review` 先订正 proposal/design/tasks（收敛盖板形态口径、补全 13~23 断言与阶段零/一改动范围），并用 `/opsx-fix` 处理 🟡1~🟡6 的空内容守卫、状态回滚、真源口径等问题后复审。

[需修正]


---

### [2026-09-30 14:04] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# GEO 阶段二素材库日常循环与盖板蒸馏重构 — 对抗式审查意见

结论先行：本变更的**功能实现本身密度高、纯函数契约与 Fail-Closed 守卫做得扎实**，但**规范文档（proposal/design/tasks）与代码实现出现严重脱节与范围漂移**，且伴随若干真实缺陷与生命周期死代码。文档真实性不足，不能作为可追溯的交付依据。建议退回补正。

---

## 一、对照 Spec 的总体核查

| 审查维度 | 结论 | 说明 |
| :--- | :--- | :--- |
| proposal 能力项落地 | 大体落地，存在命名/契约漂移 | `handleScrape` vs 实际 `handleScrapeWebsite`；多项已实现能力未写入 spec |
| design 数据模型 | 部分自相矛盾 | 主文件命名基准与 `1.x` 分片基准不一致（见 🟡） |
| tasks 任务清单 | 与实现严重不符 | 断言数量三处打架；stage3~7 重构完全缺席任务清单 |
| AGENTS §1 规范驱动 | 不达标 | 实际改动范围远超 Impact 声明 |
| AGENTS §3.5 阶段零文案 | 达标 | 已由「底牌/基线」统一改为「问题清单 + 豆包答案存档」，`modeBanner`/状态芯片保留 |
| AGENTS §3.3 / §4.5 | 基本达标 | 交付文案 0 Emoji；tasks 4.3 未代勾，合规 |

---

## 二、🔴 必须改（阻断级）

**🔴-1 断言数量三处严重打架，规范不可追溯**
- `proposal.md` 影响范围：*扩展自动化断言至 23 项*；
- `tasks.md` 4.1：*扩展至 23 项*，且只枚举 **断言 1~18 / 19~20 / 21 / 22 / 23**；
- `tests/smoke_studio_artifacts.mjs` 文件头注释：*31 项核心断言*；
- 同文件末尾输出 + `scripts/smoke_step0.sh`：**32/32 项 / 32 项全部 PASS**。

实际脚本已实现断言 **1~32**（含阶段三母盘、口径卡、雪花 ID、5 点质检等），而 spec 只写到 23。规范与真相源脱节，违反「tasks.md 必须反映真实工作」。必须一次性对齐为 32 项并在 tasks/design 中重新分档说明。

**🔴-2 变更范围远超 Spec，属未申报的大规模范围漂移**
`git diff --stat` 显示改动覆盖 `Step3App~Step7App`、`stage3Config~stage7Config`、`useStep1~useStep7`、`stage1Config.js`、新增 `stage7Config.js / useStep7.js`、`main.js`、`index.html` 的 **3→7 全流水线重编号**。而 `proposal.md` 的 Impact 仅声明了 stage2/Step0/Step1/DistillSheet/studioArtifactConfig/useStep2 等。
其中「新增阶段三 企业母盘与统一口径卡、旧阶段整体后移一位」是**架构级重排**，直接违反 AGENTS 核心工作流（propose → design → tasks 先行）。必须由独立 OpenSpec 变更承载并补齐 design/tasks，否则本变更的评审边界无法成立。

**🔴-3 proposal 声明的能力签名与代码不一致**
- proposal：`handleScrape()`；代码：`handleScrapeWebsite()`（Step2App 解构）。
契约名不一致会误导下游与自动化对接，必须二选一严格统一（AGENTS 要求对外能力即契约）。

> 另：proposal/design 完全未覆盖已落地的 `DEFAULT_SIMILARITY_THRESHOLD` RAG 去重、8500 字上限、雪花 ID、参考候选件模型、5 点质检门禁、官网 URL 归一化、S4/S5 增删竞品与案例等契约，属**能力静默扩张**，须回填。

---

## 三、🟡 建议改

**🟡-1 `workbuddy_reviewer.py::get_active_change` 中文路径静默失效**
`git status --porcelain` 未加 `-c core.quotepath=false`。变更目录为中文时路径会被八进制转义（如 `"openspec/changes/\346..."`），随后执行的正则 `openspec/changes/([^/]+)/` 捕获到的是转义串，`os.path.isdir` 必失败 → **git 探测静默跳过**，退化为兜底取最新目录。注意：同文件后续提取 diff **已**加 `core.quotepath=false`，唯独此处遗漏，前后口径不一致。

**🟡-2 `smoke_step0.sh` 步骤序号疑似断档**
由 `1/4、2/4、3/4` 改为 `1/5、2/5、3/5`，但下游仍是 `5/5 studio artifacts`。若不存在 `4/5`，则冒烟步骤计数断裂（需人工确认是否存在 nextgeo 清单的 `4/5`）。

**🟡-3 旧 viewId 生命周期与门禁 UI 存在失效风险**
`index.html` 中 `panel-step-4-qacard`、`panel-step-4-distribute`、`panel-step-5-acceptance` 已变为**无挂载根的空壳面板**，且旧导航按钮 ID（`nav-step-3-princeton` 等）已被重命名。`updatePipelineGateUI()` 若仍按 `VIEW_META`（含 legacy id，见 `isDeliveryStepView`）拼接 `nav-${viewId}` 查询 DOM，将命中 null。请确认门禁置灰逻辑已切换为新 id，避免「按钮不禁用/错位」。

**🟡-4 兼容别名疑似死代码，且以「补丁」承载架构重排**
`const renderStep3PrincetonPanel = renderStep4WebsitePanel;` 等 4 处别名 + `LEGACY_VIEW_REDIRECT_MAP`，在 `switchView`/`renderActiveView` 中实际已改用新名。若别名无外部（`window.*`）引用，即为死代码。用别名垫片迁移阶段编号与 AGENTS「拒绝打补丁」精神相悖，建议一次性正规化。

**🟡-5 主文件命名基准与 `1.x` 分片基准不一致**
design 表格：S4 主文件 `S4_对标竞品参数对比表_优搜网络.md`、S5 `S5_经典案例故事_本地实体GEO突围.md`；而分片与断言产出为 `S4_对标竞品参数对比表_增补_1.1.md`、`S5_经典案例故事_增补_1.1.md`（**去掉了后缀描述词**）。主文件与分片基准名不统一，`computeStage2ChunkVersion` 若基于槽位固定基准而非真实主文件名，一旦用户改动主文件名将出现分片归槽/展示错位。须明确「基准名」唯一真相源。

**🟡-6 `isMasterSourceFile` 小数误伤风险**
以 `/\d+\.\d+/` 排除分片。若主文件中出现合法小数（如 `S2_价格_9.9元.md`）会被误判为非主文件，导致下游母盘过滤误丢 S 主版本。建议收敛为更严格的 `_增补_\d+\.\d+` 前缀锚定。

**🟡-7 缺 NE1 验证证据**
tasks 4.1/4.2 已勾选，但 diff 内无 `100.83.64.112:8088` 构建/冒烟实证。AGENTS §4.5 明确 NE1 为唯一编译与测试真相源，请附 `npm run build:step0 && bash scripts/smoke_step0.sh` 的 32 项全绿输出。

**🟡-8 `buildPairedAnswerTemplate` 疑似死代码 + 无用解构**
新函数定义后未见调用（`handleAdoptFile` 走的是 `stampActiveQaHeader`）；`Step2App` 解构的 `sortingText / isSorting / CATEGORY_DIR_MAP` 在模板未见消费。请清理或补全用途。

**🟡-9 `:is-ready="currentStep >= 5 && assetsHealth >= 80"` 阈值语义缺失**
`assetsHealth` 的计算口径与 80 分门槛未见于 design/AGENTS，属隐式业务规则，须写入规范，否则后续调整无依据。

---

## 四、🟢 优化建议

- **🟢-1** `workbuddy_reviewer.py` 的打印与代码注释含 🔴🟡🟢；虽属内部 CLI，但与项目「0 Emoji」严格基调及 §3.5 表述不统一，建议改用 `【必须改】/【建议改】`。
- **🟢-2** `smoke_studio_artifacts.mjs` 文件头仍写「31 项」，与最终 32 项不一致（同 🔴-1，注释层面）。
- **🟢-3** `stampActiveQaHeader` 的 `existingBlockRegex` 以 `^=== 阶段零` 强锚定行首；若正文前置空行或用户粘贴预留内容，旧头无法被替换，可能叠加重复元数据头。建议允许前导空白。
- **🟢-4** `handleAdoptFile` 中 `currentAdopted` 与 `adoptedInFiles` 指向同一对象，冗余且易误读，建议合并。
- **🟢-5** `checkDraftTextLimit` 以 `String.length` 计「汉字」，代理对/表情按 2 计，与「8500 汉字」口径存在偏差；建议按 code point 计数。

---

## 五、浏览器兼容性与纯函数专项（评审关注点 2）

- **兼容性：通过。** 使用 `Object.values`、`Set`、可选链 `?.`、正则 `u` 标志、`String.prototype.repeat`、`CustomEvent`、`dispatchEvent` 均为 Chrome/Safari 桌面端长期稳定能力，无 IE 依赖，无 `ProxyJump` 等网络侧旁路。
- **纯函数：通过。** `computeStage2ChunkVersion`、`normalizeVersionTag`、`normalizeOfficialUrl`、`extractDomain`、`computeTextSimilarity`、`computeReferenceVersion`、`isMasterSourceFile`、`formatDisplayName/Title` 均无 DOM 依赖，`generateSnowflakeId` 仅依赖时间/随机数，符合「纯函数不依赖 DOM」要求，可被 Node 冒烟直接 import 验证。
- **Fail-Closed：通过且值得肯定。** `canDeleteFile(null/undefined/{})` 恒 false、空内容保存阻断、`isProbeUnready` 以服务端 `probe_status` 为唯一真相源（杜绝 localStorage 脏数据绕过门禁），是本次改动中质量最高的部分。

---

## 六、结论

功能实现质量与守卫设计可圈可点，但**规范文档已明显落后于实现**（断言数三方不一致、阶段 3~7 重构未申报、能力契约命名不符/静默扩张），叠加中文路径探测失效、旧 viewId 生命周期风险与命名基准矛盾等真实缺陷。按 AGENTS §2「只要存在 `[待讨论]/[需修正]` 不可进入合并或归档」之规定，本变更不满足可合并条件。

`[需修正]`


---

### [2026-09-30 14:28] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# 代码审查报告：阶段二素材库日常循环与盖板蒸馏重构

## 一、总体判定

本轮 diff 声称实现「阶段二盖板蒸馏重构」，但实际改动范围（36 文件 / +9988 / -4605）**远超** proposal / design / tasks 的申报边界，且**所提供 diff 在 `Step2App.vue` 中部即被截断**，proposal 最核心的新增组件（`DistillSheet.vue`、`studioArtifactConfig.js`、`stage2Config.js`、`useStep2.js`、`main.js`）实现全部落在审查视野之外。因此**无法对方案核心能力的正确性给出通过判定**。

---

## 二、对照 proposal / design / tasks 的符合性

1. **断言数量三方打架（规范级硬伤）**
   - `proposal.md` 与 `tasks.md` 4.1/4.2 均写「23 项」；
   - 实际 `tests/smoke_studio_artifacts.mjs` 头部注释、`断言 13~32` 与结尾 `32/32` 全部为 **32 项**；
   - `scripts/smoke_step0.sh` 新输出也写「32 项自动化断言全部 PASS」。
   → 规范文档与实现严重脱节，违反 OpenSpec「tasks.md 必须反映真实进度」的约束。

2. **申报范围与实际改动严重不符**
   - proposal 的 Impact 仅列举 `Step2App.vue / DistillSheet.vue / studioArtifactConfig.js / useStep2.js / stage2Config.js / StudioHeader.vue / Step0App.vue / Step1App.vue / tests / smoke_step0.sh`；
   - 实际 diff 却包含 **`Step3App~Step7App`、`stage3Config~stage7Config`、`useStep3~useStep7`、`web/index.html` 全站阶段重编号、`tools/geo/server.py`、`tools/geo/utils.py`、`scripts/workbuddy_reviewer.py` 模型切换**。
   → 阶段三~阶段七的整体重构、后端建档写盘改造、审查器模型从 `hy3` 切到 `deepseek-v4.1-flash` 等能力，**在 proposal/design/tasks 中零描述**。属于未申报变更，无法被本轮 spec 驱动审查覆盖。

---

## 三、🔴 必须改（Must Fix）

**🔴1. 未申报的大范围重构，规范未同步（最高优先级）**
`web/index.html` 将交付流水线由 6 步整体重编号为 7 步（`step-3-princeton→step-4-website`、`step-4-qacard→step-5-qacard`、`step-4-distribute→step-6-distribute`、`step-5-acceptance→step-7-acceptance`），并新增 `Stage7App/useStep7/stage7Config`。这是影响全站导航、门禁、路由 hash 的**结构性变更**，却只字未写在 proposal/design/tasks 中。按规范必须先补 proposal/design/tasks 影响分析再评审。

**🔴2. 核心实现未被纳入审查视野，无法验证**
proposal 声称的对外能力 `openDistillSheet / closeDistillSheet / handleScrape / handleStartDistill / handleAdoptDistillChunk / computeStage2ChunkVersion` 全部实现于 `DistillSheet.vue`、`studioArtifactConfig.js`、`stage2Config.js`、`useStep2.js`，但这些文件的 diff 均被截断。只在测试文件里看到消费端断言，缺失生产端实现，**无法确认断言与实现一致**。

**🔴3. 阶段重编号后「挂载点 ↔ render 函数」对齐存在白屏风险**
- HTML 侧：`panel-step-3-master` 挂 `#step3-app-root`，`panel-step-4-website` 挂 `#step4-app-root`，`panel-step-5-qacard` 挂 `#step5-app-root`；
- JS 侧：`renderStep4WebsitePanel` 实为**由旧 `renderStep4QaCardPanel` 改名而来**（函数体未改，仍指向 `__GEO_STEP4__` / `#step4-app-root`），并用 `const renderStep3PrincetonPanel = renderStep4WebsitePanel;` 做别名；同理 `renderStep5QaCardPanel` 由旧 `renderStep5DistributePanel` 改名而来。
- 同时 `panel-step-4-qacard` 被清空为**空 div**，`panel-step-3-princeton` 的 `#step3-app-root` 被移除。
→ 改名后的函数体挂载目标（`__GEO_STEP3__…STEP7__` 全局与 app-root）必须依赖 `main.js` 的重新绑定才能成立，而 `main.js` 的 32 行 diff 未提供。**若绑定未同步，将出现「切到某阶段白屏/串台」**。此项必须逐一对照 `main.js` 的 `window.__GEO_STEPx__` 绑定与 DOM 挂载点给出证据。

**🔴4. `tools/geo/utils.py` 存在数据丢失与潜在 NameError**
- 新增标量键循环中：`elif isinstance(val, (dict, list)): continue` 会**静默丢弃** `nameplate`（若为对象）、`avatar` 等复杂结构字段，注释所称「走专门通道」并无对应实现分支；
- `_replace_yaml_string_list(content, "models", _normalize_profile_list(...))` 与 `member_user_ids` 依赖 `_normalize_profile_list`，该函数**未在 diff 中出现**，若不存在将直接 `NameError` 导致配置保存 500。请确认其定义存在且对 `None`/字符串/列表均有兜底。

---

## 四、🟡 建议改（Should Fix）

**🟡1. `smoke_step0.sh` 步骤编号仍错乱**
改动只把 `1/4,2/4,3/4` 改为 `1/5,2/5,3/5`，末尾却仍是 `5/5`，**缺 `4/5`**。沿用了旧文件的编号 bug，未随本次「4 步升 5 步」一起修正。

**🟡2. 派生基名与设计主文件名不一致（存在挂错主文件隐患）**
design.md 1.1 表声明 S5 主文件为 `S5_经典案例故事_本地实体GEO突围.md`、S4 为 `S4_对标竞品参数对比表_优搜网络.md`；但断言 21 期望 `computeStage2ChunkVersion` 对 S5 派生出的基名为 `S5_经典案例故事`。**派生增补文件（`..._增补_1.1`）所依附的主文件基名与设计规范化主文件名不同**，未来主文件改名或带描述后缀时，增补件极可能挂到错误节点。请统一「主文件 canonicalName ↔ 增补基名」的唯一真相源。

**🟡3. camelCase 事件监听被移除，需确认子组件只 emit kebab-case**
`Step0App.vue`/`Step1App.vue` 删除了 `@adoptFile`、`@restoreFile`（保留 `@adopt-file`、`@restore-file`）。若 `StudioEditor.vue` 内存在任何 `emit('adoptFile')`，将静默失效。请 grep 确认。

**🟡4. 阶段二就绪门槛引用了未在 diff 中定义的 `assetsHealth`**
`Step2App.vue` 新增 `:is-ready="currentStep >= 5 && assetsHealth >= 80"`，但 `assetsHealth` 的定义（应在 `useStep2.js`）未出现在 diff 中。若拼写/来源不符，会导致阶段二永远「未就绪」。

**🟡5. 可能存在的死代码**
`handleConfirmMaster`、`buildPairedAnswerTemplate` 已定义并 `defineExpose`，但模板中未见对应 `@confirm-master` 绑定或调用点；`getMaxQaVersionNumber` 被删除后是否有残留引用也需确认。

**🟡6. 空面板与重复 `data-page-node-id`**
`panel-step-4-qacard` 变为空 `<div>`，且 `data-page-node-id="navStep4QaCard"` 与导航按钮 `nav-step-5-qacard` 的 `data-page-node-id` 完全重复；`panel-step-3-princeton` 遗留大块 hidden 容器与新面板并存。运行时无害，但会干扰页面编排工具与后续维护。

**🟡7. `tools/geo/ingest.py` 新增 `content` 字段的负载风险**
`"content": clean_md ...` 会把整页清洗文本塞进结果对象，若该对象进入 API 响应/落盘 JSON，可能显著增大体积。请确认消费方按需裁剪。

**🟡8. `workbuddy_reviewer.py` 的两点需确认**
- `codebuddy -p --model ...` 改为纯 stdin 传参，需确认该 CLI 在无位置参数时确实读取 stdin（否则审查直接空响应）；
- 模型从免费 `hy3` 切到 `deepseek-v4.1-flash` 属计费变更，虽与 AGENTS §1.6 表述一致，但未在 proposal 中申报，涉及成本口径应显式确认。

---

## 五、🟢 优化建议（Nice to Have）

**🟢1. Emoji 检测正则不完整**
`/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u` 未覆盖 `\u{1F000}-\u{1F2FF}`（麻将/多米诺）、`\u{FE0F}`（变体选择符）等区段。建议改用更完备的 Unicode 属性检测（`\p{Extended_Pictographic}`）以免漏检。

**🟢2. render 函数别名缺少说明**
`const renderStep3PrincetonPanel = renderStep4WebsitePanel;` 一类「旧名指向新函数」的兼容别名，建议统一收敛到 `LEGACY_VIEW_REDIRECT_MAP` 一处处理，避免长期维护歧义。

**🟢3. proposal 与 design 的盖板步数表述不一**
proposal 列 5 步（含「收起盖板」），design 2.2 写「4 步」。属文案层面，建议对齐。

**🟢4. `probeWarnDismissedProjects` 仅在内存**
刷新后重复弹窗；且当 `currentProjectData` 为空时键为 `undefined`。可接受，建议加项目 id 兜底。

---

## 六、结论

优点：`migrateAndNormalizeFiles` 对无效/跨阶段槽位的失活与纠偏、`normalizeVersionTag` 幂等防膨胀、`canDeleteFile` Fail-Closed（null/undefined 不抛异常）、`isMasterSourceFile` 人机两分隔离等断言设计严谨；空内容保存守卫（断言 6）方向正确；Emoji 从 `🎉` 收敛为 `[SUCCESS]` 符合 §3.3。

但本轮存在**规范未申报的大范围重构**（阶段三~七 + index.html 全站重编号 + 后端写盘改造）、**规范断言数（23）与实现（32）脱节**、**关键新组件实现未纳入 diff 无法验证**、以及 `utils.py` 潜在数据丢失/NameError 等硬伤，且阶段重编号后的挂载点对齐缺乏 `main.js` 证据，存在白屏回归风险。据此本轮**不满足进入归档的条件**。

[需修正]


---

### [2026-09-30 15:20] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

# 审查报告：阶段二素材库日常循环与盖板蒸馏重构

## 〇、审查前提与重大限制（必读）

本次送审材料存在**结构性缺陷，导致无法做出完整判定**：

1. `git diff --stat` 显示 **36 个文件、+10214 / -4600 行**，但正文只提供了约 15 个文件的 Diff。以下**关键文件内容完全缺失**，无法验证其契约：
   - `web/step0-src/useStep2.js`（+980/-…，盖板入库落盘主逻辑）
   - `web/step0-src/stage2Config.js`（+724，`semanticChunkRawMaterial` / `CATEGORY_DIR_MAP` / `computeTextSimilarity` 供给方）
   - `web/step0-src/useStep4.js` / `useStep5.js` / `useStep6.js` / `useStep7.js`（大搬家的接收方）
   - `web/step0-src/stage7Config.js`（新建）
   - `config/studioArtifactConfig.js` 尾部被截断（`getMasterFileForSlot` 函数体未给全）

2. 这意味着**最关键的"入库落盘""母盘合流""阶段搬运"逻辑处于黑盒状态**。以下所有🔴判定中，凡涉及这些文件的，均为"依据 Diff 信号推断的高风险项"，需补全 Diff 后方可最终定性。**审查材料不完整本身即为需修正项（🔴0）。**

---

## 一、对照 proposal / design / tasks 的严谨性核查

### 🔴1 变更范围严重失控，违反 AGENTS §1 规范驱动铁律

proposal.md 的 `Impact` 明确列举了 **9 个文件**，全部围绕"阶段二"。而实际 Diff 覆盖了：

- **阶段三~阶段七全流水线重编号**：`web/index.html` 把 00~06 改为 00~07，`step-3-princeton`→`step-4-website`、`step-4-qacard`→`step-5-qacard`、`step-4-distribute`→`step-6-distribute`、`step-5-acceptance`→`step-7-acceptance`；
- **新建 `Step7App.vue` + `useStep7.js` + `stage7Config.js`**；
- **后端改动**：`tools/geo/server.py`（废弃建档十字段重写）、`tools/geo/utils.py`（扩展标量键 + models/member_user_ids 持久化）、`tools/geo/ingest.py`（新增 content 字段）；
- **阶段三/四工作台语义对调**：原 step3「交钥匙官网」搬至 step4，原 step4「答题卡」搬至 step5……

这些在 proposal / design / tasks **三份 Spec 中零描述**。按 AGENTS §1，任何超出 Spec 授权的实现均为违规。**这不是"重构顺带"，而是一次未立项的全产线架构漂移。** 必须回写 Spec 或拆分变更。

### 🔴2 文档与实现的断言数量直接矛盾，且断言 24~32 所测功能无 Spec 依据

- `tasks.md` 4.1 明确写"扩展至 **23 项**"，proposal.md 亦写"**23 项**"；
- 但 `tests/smoke_studio_artifacts.mjs` 实际输出 `32/32 项`，`smoke_step0.sh` 也被改为"**32 项**"。

更严重的是，**断言 24~32 所覆盖的功能**（官网网址归一化、阶段三槽位字典、统一口径卡生成/消歧/字数红绿灯、9 因子母盘合流、全平台对冲清单、雪花 ID、参考候选件、5 点质检）**在 proposal / design / tasks 中完全没有出现**。这是"代码先行、文档欠账"，与 OpenSpec 的 SSOT 原则（AGENTS §1.2）根本背离。

### 🔴3 `tests` 疑似引用未导入符号，可能导致整卷测试失败

断言 25 直接使用 `CANONICAL_SLOT_DICT.slot_stage3_identity_card`，断言 1 也使用了 `resolveSlotKey`。但 Diff 中新增的 import 列表**未包含 `CANONICAL_SLOT_DICT`**（仅列出 `resolveSlotKey`/`computeNextVersion`…）。若原文件顶部亦无该导入，则断言 25 会抛 `ReferenceError`，**导致 32 项全绿的说法不成立**。请确认 `CANONICAL_SLOT_DICT` 的导入来源（若原 import 已有请忽略，但送审材料未体现）。

### 🔴4 design 2.1 与实现不符：默认态定义冲突

- design 2.1 明确："**默认态（素材库管理态）**：中间为文本编辑器，可自由查看与打字修改主文件及分片"；
- 实现 Step2App 中：`<div v-if="viewMode !== 'source'">` 展示的是"素材采集与蒸馏工作台"（网址抓取 + 大文字稿），**Markdown 编辑器退化为需切到 `source` 才出现**。

即：**默认落地视图被静默改变**，与 Spec 描述相反。要么改代码，要么回写 design（并说明理由）。

---

## 二、核心关注点审查

### （一）架构复用与规范遵循

#### 🟡5 「裁决11 / 裁决12」为全局行为变更，未落入任何 Spec
- **裁决11**：`isReadOnlyFile` 被改为"除废纸篓外全域可编辑"，**推翻了原"镜像骨干终身只读、首版母版只读、淘汰历史只读"三重保护**，影响阶段零~七。
- **裁决12**：`isProbeUnready` 被弱化为读 `localStorage`，`switchView`/切页 `confirm` 门禁被**整体删除**。
- 二者均为项目级产品决策，却只在代码注释（`[2026-09-30 裁决11]`）中留痕，proposal/design 只字未提。**违反 AGENTS §1 与 §2 的评审留痕要求**。

#### 🟡6 镜像骨干可编辑 → 与"单向镜像同步"存在数据丢失风险
`isReadOnlyFile` 解绑后，`isCanonicalMirror` 骨干（如 `01_网络底座指标_待对照.md`）可被用户直接编辑保存；而 `handleAdoptFile`/`migrateAndNormalizeFiles` 又会把骨干内容**单向覆盖为最新生效版本内容**。用户对骨干的修改将在下一次采纳/迁移时被**静默冲毁**。design 1.2 第 4 条只字未提前者，建议显式在 UI 提示或恢复部分只读。

#### 🟡7 Step3App 残留"底牌"字样，与去"底牌"规范精神冲突
Step0App 已系统性把"底牌"改为"生效版本"，但 Step3App 抽屉标题仍为「**企业底牌信息核对与微调**」。AGENTS §3.5 的"严禁自造『底牌报告/基线/剧本』充当主文案"虽特指阶段零，但全项目正在统一口径，此处属遗漏。

#### 🟡8 smoke_step0.sh 新增 brew 探测，暗示本地执行重型编译，与 §4.5 冲突
脚本新增：
```bash
if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
```
并直接在脚本内 `npm run build:step0`。AGENTS §4.5 明确"本地笔记本**绝对严禁执行重型编译**，一律且只在 NE1（8088）就地完成"。脚本本身未做"非 NE1 环境拒绝执行"的防护，brew 探测更像是为了在本地 mac 跑通而加。**建议增加环境守门（非 NE1 直接 fail-fast）**，或明确该脚本仅供 NE1 使用。

### （二）浏览器兼容性与现有业务破坏

#### 🔴9 Step4App 复用旧 siteInfo 抽屉，依赖 useStep4 改造是否到位（无法验证）
Step4App 解构了 `siteInfo`、`drawerOpen`、`handleCompile`、`handleResetSiteInfo` 等，模板中完整渲染了旧的"企业底牌信息收集"抽屉（brandName/slogan/services/faqs）。这些能力原属 `useStep3`。**若 useStep4.js 未同步迁入这些导出，Step4App 将在运行时解构出 `undefined`，导致面板崩溃**。鉴于 useStep4 Diff 未给，此为一等处 🔴 风险，必须验证。

#### 🔴10 Step7App 与 Step6App 的 props 契约不一致
- 新 Step6App：`useStep6(props.bridge?.projectData || {})`；
- 新 Step7App：`useStep7(props.bridge)`（**传整个 bridge，无 `?.projectData`**）。

若 `useStep7.js` 是照抄新 `useStep6.js`（接收 projectData），则传 bridge 会导致 `projectData` 被当作 bridge 解构 → 数据全空。若照抄旧 useStep6 则勉强兼容。**两处调用签名必须统一**，请确认 useStep7 的内部解构约定。

#### 🟡11 index.html 资源版本号与构建产物一致性风险
`web/index.html` 引用 `?v=20260930021338`，但 Diff 中**未见 `web/assets/step0/step0.js` 的构建产物**（可能被 `.gitignore` 忽略）。若产物未提交或未在 NE1 重新构建，线上/验证端将出现 **HTML 引用新 hash、实际加载旧/缺失 bundle** 的错配。tasks 4.2 声称在 NE1 构建，但需确认产物入库或明确部署流程。

#### 🟡12 VIEW_META 与侧栏导航存在新旧双份映射
`VIEW_META` 同时保留新 viewId（`step-4-website`）与旧 viewId（`step-3-princeton`）两条记录，且 `STEP_TO_VIEW` 只登记新 id。若侧栏/面包屑或其它遍历 `VIEW_META` 的渲染路径未过滤旧键，可能出现**重复菜单项或标签错乱**。建议旧 id 仅保留在 `LEGACY_VIEW_REDIRECT_MAP`，不再进 `VIEW_META`。

#### 🟡13 旧面板根节点被掏空但未删除
`panel-step-4-qacard`、`panel-step-4-distribute`、`panel-step-5-acceptance` 变为**空壳 div**（子节点迁走后仅剩容器）。虽然 `hidden` 下通常无害，但 `switchView` 若对这些 id 仍有渲染分支，会命中空容器。建议清理死壳，避免误命中。

### （三）规则与设计的逻辑漏洞

#### 🟡14 `isMasterFile` 第三分支边界可疑
```js
if (allCanonicalNames.includes(file.name) && file.isActive !== false) return true;
```
`isActive !== false` 对 `undefined` 也为 `true`。若迁移未彻底、canonicalName 文件缺少 `isActive` 字段，则会被判为主文件 → 受"终身防删"保护，可能误锁用户想删的文件。建议收紧为 `file.isActive === true` 或显式 `isActive === undefined` 的受控白名单。

#### 🟡15 `computeStage2ChunkVersion` 依赖 `resolveSlotKey` 做跨槽归属，存在误归槽隐患
其对每个 slotFile 计算 `resolveSlotKey(f.name, 'step2', f.isManual) === targetSlotKey`。由于 `ALIAS_SLOT_MAP` 新增了 `'S1_'`、`'S2_'` 等**短前缀键**并采用 `startsWith` 匹配（`resolveSlotKey` 第 3 步新增了"别名前缀匹配"），理论上 `S1.1_草稿` 与 `S1_企业主体...` 都会命中 `S1_` → `slot_stage2_s1`。虽然 `isMasterSourceFile(f.name)` 已跳过带 `.1` 的文件，但**排序与边界仍较脆弱**，建议补一条断言覆盖"含小数点的别名前缀"。

#### 🟢16 `generateSnowflakeId` 使用 BigInt 字面量
`snowflakeSequence & 4095` 等逻辑正确，但 `BigInt` 在 Safari < 14 不支持。AGENTS 要求 Safari/Chrome 双内核，若需覆盖老 Safari 建议加 polyfill 或降级。当前主流版本无碍。

#### 🟢17 右键盘菜单/行内改名输入无 aria 语义
`contextmenu` 自定义菜单、内联 `<input>` 缺少 `role="menu"` / `aria-label`，键盘/无障碍体验欠缺。非阻断项。

#### 🟢18 无用 import 与常量
- Step2App 仍 `import { ref, ... }`（删除 `suggestedTopics` 后 `ref` 疑无使用）；
- Step2App 从 `useStep2` 解构了 `CATEGORY_DIR_MAP` 但模板未用。
建议清理以免 lint 噪音。

#### 🟡19 `handleAdoptFile` 的配对文件与"参考件"阻断逻辑需与应用层闭环
Step0App 新增"参考件禁止覆盖主文件"守卫（`versionTag?.startsWith('参考')`），并在 `StudioEditor` 用 `isReferenceFile` 复用同一判定——**判定逻辑重复实现于两个文件**，未抽为 `studioArtifactConfig.js` 的单一真相源，违反 SSOT。建议收敛为一个纯函数导出。

---

## 三、后端改动补充意见

`tools/geo/server.py` 废弃硬编码十字段重写、改调 `update_project_profile` 是**正确方向的复用**，且补了 `project_slug`/`id`/`client_name`/`official_url`/`updated_at` 向后兼容字段，值得肯定。但：

- 🟡 `update_project_profile(project_id, body or {})` 未防御 `body` 非 dict 的极端输入；`body` 为 JSON object 时通常安全，但建议显式 `isinstance` 校验。
- 🟡 `tools/geo/ingest.py` 新增返回 `content` 字段，需与 `DistillSheet` 期望的 `data.content` / `data.crawled_words` **逐字段核对**（`/api/projects/{pid}/ingest/url` 的实际响应包装层未在 Diff 体现）。

---

## 四、结论

本变更在**产品方向**上（去死锁、盖板蒸馏、1.x 纯增量、人机两分）逻辑自洽，`normalizeVersionTag` 幂等、`isMasterSourceFile` 过滤、`computeStage2ChunkVersion` 单调递增等核心纯函数设计合理，后端复用亦为正向改进。

但在**工程纪律**上存在系统性缺口：

1. 变更范围远超 Spec 授权（阶段三~七全产线顺延 + 后端 + 新阶段七），无立项；
2. 文档（23 项）与实现（32 项）及功能描述严重脱节；
3. 关键文件（useStep2/4/5/6/7、stage2Config）Diff 缺失，核心落盘/搬运逻辑无法验证，且已发现 Step4App/Step7App 的契约不一致高风险；
4. 裁决 11/12 等全局行为变更未入 Spec；
5. 疑似测试导入缺失，32/32 全绿存疑。

以上任一项都足以阻断合入。建议：**先补全 Diff 与回写 Spec，再由对端复评**，不得进入归档。

**审查意见：需修正（Reopen）**

[需修正]


---

### [2026-09-30 16:00] 审查意见（来自 WorkBuddy (deepseek-v4.1-flash)）

## GEO 阶段二盖板蒸馏重构 · 代码审查报告

**结论先行**：本次 Diff 的实现质量与自动化程度较高（纯函数、断言充分、术语去自造词），但**变更范围与已评审的 proposal/design/tasks 严重背离**，且存在 1 处功能行为回归、多处文档与代码数量不一致。**在补齐规范文档前不应进入归档。**

### 一、总体对照（proposal / design / tasks vs 实际 Diff）

| 维度 | 规范声明 | 实际 Diff | 判定 |
| :--- | :--- | :--- | :--- |
| 改动范围 | 仅阶段二（Step2App / DistillSheet / studioArtifactConfig / useStep2 / stage2Config 等 9 文件） | 36 文件、+10207/-4603，覆盖 Step0~Step7、tools/geo Python、web/index.html 全站路由 | 🔴 严重超范围 |
| 流水线编号 | proposal 仍写"推进至阶段三交钥匙官网" | 实际重排为 03 母盘 / 04 官网 / 05 答题卡 / 06 分发 / 07 验收 | 🔴 文档与实现两套口径 |
| 断言数量 | tasks 4.1/4.2 → 23 项 | 测试与脚本 → 32 项 | 🔴 数量矛盾 |
| 版本模型 | design 1.2 阶段二 `1.x` 增补分片 | 阶段零改用 `参考N`、阶段一用 `第N版`、阶段二用 `1.x` | 🔴 三套模型并行 |

### 二、🔴 必须改（阻塞归档）

1. **Impact 完整性与阶段隔离违规**。proposal/design/tasks 只立项阶段二，但 Diff 夹带了：全站步骤重编号、Step3 由"交钥匙官网"改为"企业母盘与统一口径卡"、新增 Step7、`tools/geo/server.py|utils.py|ingest.py` 三处后端改动、`web/index.html` 路由与视图大重构。按 AGENTS §1.1，Impact 必须完整；这些改动既无 proposal，也无 design，属**未经评审的夹带变更**。必须回填规范或拆分为独立变更后重审。

2. **断言数量三处不一致**。tasks.md 4.1/4.2 与 `scripts/smoke_step0.sh` 文案写 23 项，实际 `smoke_studio_artifacts.mjs` 为 32 项。tasks.md 4.1 描述亦仅列到断言 23，而代码已到 32。文档必须与代码对齐（且断言已覆盖阶段三，tasks 未记录）。

3. **`tools/geo/server.py` 功能行为回归（高危）**。旧实现对 YAML 是**无条件**写入 `site_pending: false`；新实现委托 `update_project_profile(project_id, body or {})`，而 `utils.py` 仅 `if "site_pending" in patch` 才更新。**调用方不带该字段时，站点"待发布"状态不会被复位**，可能使存量 `site_pending: true` 长期残留、破坏发布门禁。需显式保留旧语义或确认调用方始终传参。同时须验证：`update_project_profile`、`_replace_yaml_string_list`、`_normalize_profile_list` 均已在 `server.py` / `utils.py` 中就位（本次仅见调用，未见定义）。

4. **阶段零/阶段三机制被静默重设计**。`主文件预置建档 + isMaster + 参考件取代第N版 + 5点质检 + 企业母盘/统一口径卡/全平台对冲清单 + 废除切页 confirm 拦截`，全部无 proposal/design 记载。更关键：这引入了与 design 1.2 平行的**第二套版本模型**（阶段零 `参考N` vs 阶段二 `1.x`），存在"版本体系分裂"的 SSOT 风险。必须先补 design 统一说明。

### 三、🟡 建议改

5. **SSOT / 跨模块耦合**：`isProbeUnready` 直接 `localStorage.getItem('geo_step0_files_${pid}')` 并解析 Vue 岛私有数据结构。阶段零存储键或结构一旦调整，宿主判断将静默失效。建议由 Step0 通过 `geo:project-updated` 事件或 window 只读接口暴露"就绪态"。

6. **死代码/冗余**：`web/index.html` 新增 `probeWarnDismissedProjects` 未见使用；移除拦截后 `switchView` 的 `opts.skipProbeWarn` 成为死参；`panel-step-4-qacard`、`panel-step-5-acceptance` 等遗留面板已无子节点成为空壳 DOM。`Step0App.buildPairedAnswerTemplate` 新增但未见调用点，且其头部拼接与 `stampActiveQaHeader`、`initDefaultFiles` 三处重复，建议收敛为单函数。

7. **遗留 DOM 助手悬空风险**：`handleHashRoute` 中 `step-4-website` 分支仍调用 `restoreStep3GuideState / loadRawMaterialsEditor / loadCorpusStatus / handleCorpusDiff`，而新面板 `panel-step-4-website` 仅有 `#step4-app-root` 纯 Vue 根。需确认这些函数对 `null` 节点安全，否则切换页面会抛错。

8. **命名/兼容层可精简**：`const renderStep3PrincetonPanel = renderStep4WebsitePanel` 等 4 条别名 + `LEGACY_VIEW_REDIRECT_MAP` 构成双保险；既然 `switchView` 已完成重定向，别名链可裁撤。且 `data-page-node-id` 存在复用（如 `nav-step-5-qacard` 复用 `navStep4QaCard`），需确认可视化编辑器不受影响。

9. **审查器 prompt 体积失控**：`workbuddy_reviewer.py` 现拼接 RULES(30000) + AGENTS(30000) + diff(300000) + untracked(50000) ≈ 380KB，易超模型上下文被静默截断；且 AGENTS.md 截 30000 字符会切掉后段红线（§6~§8），审查可能漏判。建议按阶段节选、提高上限或做长度校验并告警。

10. **测试导入纯净性**：新增从 `stage2Config.js` / `stage3Config.js` 导入。必须保证这两个文件为**纯函数、零 Vue / 零 DOM / 零浏览器 API**，否则 Node 无 DOM 环境冒烟会崩溃；同时确认 `package.json` 支持 ESM 解析这些 `.js`。

11. **清理与一致性**：`utils.py` 新增 `import json` 未使用；`server.py` 中 `_yaml_escape`、`new_id`、`load_project_config` 可能变为死代码。`scripts/smoke_step0.sh` 步骤编号仍不连续（1/5、2/5、3/5、…、5/5，缺 4/5 标注）。

12. **前端可维护性**：`Step2App.vue` 内联了 6 张 S 分类卡与大量表单，单文件膨胀明显，建议拆分为 `S1Card…S6Card` 子组件，符合 AGENTS"拒绝重复面条代码"。

### 四、🟢 优化建议（正面确认）

- `getSlotsByStage` 取代硬编码槽位数组、移除重复的 `@adoptFile/@restoreFile` 监听、`formatReason` 统一错误文案，符合架构复用与 SSOT，予以肯定。
- 移除 `🎉` 改为 `[SUCCESS]`、去掉"底牌/基线"自造词改用"生效版本"，符合 AGENTS §3.3 / §3.5。
- `DistillSheet` 为**非全屏盖板**、保留左右栏，符合 design 2.1。
- tasks 4.3 人工验收留白未勾选，符合单步停步铁律。
- `ingest.py` 将完整 `clean_md` 写入 source 记录，建议关注返回体/落盘体积是否冗余。

### 五、审查边界说明

本次提供的 Diff 在 `Step2App.vue` 的 S6 文本域处**被截断**，`DistillSheet.vue`、`studioArtifactConfig.js`、`useStep2.js`、`stage2Config.js`、`StudioHeader/FileTree/Editor.vue`、`Step3~7App.vue`、`useStep1~7.js`、`stage3~7Config.js` 等核心实现**未在可见范围内**。上述判断仅基于可见片段；建议对上述文件补充完整 Diff 后再做一次 code 阶段复审，尤其核对 `computeStage2ChunkVersion` 的槽位独立性、`normalizeVersionTag` 幂等实现、以及 `__GEO_STEP7__` 的构建导出。

[需修正]
