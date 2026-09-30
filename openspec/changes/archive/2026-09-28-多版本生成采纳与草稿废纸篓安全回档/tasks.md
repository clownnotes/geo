# Tasks: 多版本生成采纳与草稿废纸篓安全回档

## 1. 准备与规范核对

- [x] 1.1 核对 `AGENTS.md §3.3`（视觉设计规范与主色紫红线）、`§3.5`（管理端文案与操作反馈规范）、`§4.5`（本地零编译，打包构建必须在 NE1 服务器）。
- [x] 1.2 确认修改涉及的核心文件：`StudioFileTree.vue`、`stage1Config.js`、`useStep1.js`、`Step1App.vue`、`StudioEditor.vue`、`Step0App.vue`。

## 2. 前端组件与业务逻辑编码 (第一阶段已完成入库)

- [x] 2.1 改造左栏资源管理器组件 `GEO/web/step0-src/components/studio/StudioFileTree.vue`：
  - 完善草稿（未采纳）文件的删除触发按钮（Lucide `trash-2` 图标，hover 时浮现），派发 `deleteFile` 事件；
  - 保护已采纳文件，不展示删除按钮；
  - 保持 `showStatusBadge` 默认值为 `false`，杜绝污染阶段二/三；
  - 底部新增【已归档 / 废纸篓】折叠抽屉，汇总展示所有 `is_deleted` 文件并提供【恢复】按钮（使用已有先例的 Lucide `rotate-cw` 图标），派发 `restoreFile` 事件。
- [x] 2.2 扩展阶段一配置字典 `GEO/web/step0-src/stage1Config.js`：
  - 为初始生成的 6 个核心文件注入默认属性：`isActive: true`、`versionTag: 'V1'`、`is_deleted: false` 以及格式化生成时间戳。
- [x] 2.3 升级阶段一业务逻辑 `GEO/web/step0-src/useStep1.js`：
  - 实现 `handleDeleteFile(filename)`：对未采纳草稿标记 `is_deleted = true`，平滑切换选中文件并调用 `saveState()`；
  - 实现 `handleRestoreFile(filename)`：将废纸篓文件标记 `is_deleted = false`，恢复至主列表并调用 `saveState()`；
  - 实现 `handleAdoptFile(filename)`：将候选版本升格为 `isActive = true`，同类旧底牌退回为草稿；
  - 重新抓取时注入最新生成时间戳；
  - 在 `return` 对象中导出新方法供外部调用。
- [x] 2.4 改造胶水层与中栏组件 (`Step1App.vue` & `StudioEditor.vue`)：
  - 改造 `StudioEditor.vue:191-196`：放宽 `canAdoptCurrentFile` 白名单判定，兼容阶段一各分类；
  - `Step1App.vue` 显式为 `<StudioFileTree>` 传入 `:show-status-badge="true"`，并绑定 `@delete-file="handleDeleteFile"` 与 `@restore-file="handleRestoreFile"`；
  - `Step1App.vue` 补齐 `<StudioEditor>` 的 `@adopt-file="handleAdoptFile"` 绑定；
  - 中栏编辑器展示文件生成时间戳与版本号，针对草稿文件展示【设为客户采纳】动作按钮。
- [x] 2.5 文案与代码 Emoji 规整自检：检索改动文件，确保不引入任何彩色 Emoji 表情。
- [x] 2.6 为阶段零主应用 `GEO/web/step0-src/Step0App.vue` 补齐草稿删除与废纸篓恢复能力：
  - 实现 `handleDeleteFile(filename)` 与 `handleRestoreFile(filename)`；
  - 在 `<StudioFileTree>` 上绑定 `@delete-file="handleDeleteFile"` 与 `@restore-file="handleRestoreFile"`；
  - 联动持久化 `localStorage` 中的阶段零文件草稿与废纸篓状态，杜绝点击垃圾桶无反应。
- [x] 2.7 完善阶段一底座重新抓取多版本生成与工序槽位隔离 (`GEO/web/step0-src/useStep1.js`)：
  - 扫描全量历史（包含废纸篓 `is_deleted: true`）计算 `slot_metrics` 最大版本序号，生成递增新版草稿 `01_网络底座指标_第${maxVersion + 1}版.md`，设置 `slotKey: 'slot_metrics'`、`isActive: false`、`versionTag: 'V${maxVersion + 1}-Draft'`、最新生成时间戳，自动在中栏打开；
  - 采纳逻辑升级：仅将同 `slotKey` 旧版本退回草稿，新版本 `versionTag` 规整为正式版（去掉 `-Draft`），绝不误伤同分类下的其他独立报告；不满意则随时点垃圾桶删入废纸篓。

## 3. 构建与端到端真机验收 (第一阶段已完成入库)

- [x] 3.1 跨端构建（严格遵守 `AGENTS.md §4.5`）：在 NE1 服务器执行仓库根构建命令 `npm run build:step0`，产物写入 `web/assets/step0/` 并由 `stamp-build.mjs` 打版本戳。
- [x] 3.2 运行端到端冒烟测试（`npm run smoke:step0`），确保 4/4 项全部 PASS。
- [ ] 3.3 浏览器真机验证（NE1 开发环境 8088 端口 · 第一阶段人工浏览器验收留白项，AI 不得代勾）。

## 4. 废纸篓只读查验与顶栏双行解耦改造 (Grill-Me 迭代增量 · 待执行)

> **迭代阶段说明**：第 1~3 节代码与冒烟已在上一轮完成并验证入库（commit `f2e1daf`）；第 4 节为本次 Grill-Me 迭代新需求，当前处于代码实现与真代码审查对审阶段（stage=code），4.1~4.7 任务已实现并通过全量断言冒烟与构建验证，留待 4.8 供人工真机体验验收。

- [x] 4.1 新建共享配置与算法模块 (`GEO/web/step0-src/config/studioArtifactConfig.js` · 解决 🔴1-🔴4, 🟡2-🟡8, 🟢1-🟢3):
  - 集中定义 8 大核心工序槽位字典 `CANONICAL_SLOT_DICT` 与别名容错字典 `ALIAS_SLOT_MAP`，导出 `resolveSlotKey` 未匹配项统一兜底常量 `slot_misc`（解决 🔴3 & 🟡8）；
  - 导出 `safeStorageGet / safeStorageSet` 薄封装（带环境安全探测，保障纯函数与存储解耦 · 解决 🟢1）；
  - 导出按阶段收窄器 `getSlotsByStage` 与 `getCoreFilesByStage`（未传 stage 时安全降级为空集合并报警，坚决不抛错，彻底杜绝白屏崩溃 · 解决 🟡6, 🟡7）；
  - 集中封装动态版本正则构造器 `buildSlotRegex`（带 `escapeRegExp` 字符转义）、版本提取防重名算法 `computeNextVersion`（过滤手建文件 · 解决 🔴3）；
  - 导出双重锁删除判定 `canDeleteFile`（Fail-Closed 关闸保护：无论 stage 是否传入，规范镜像与母版留档终身不可删 · 解决 🟡3）；
  - 导出正交只读判定 `isReadOnlyFile`（优先依据 `isRetired === true` 判定淘汰只读，新生成候选草稿不带 isRetired 绝对不只读；已淘汰历史版本只读但支持回滚采纳 · 解决 🔴1 & 🟡7）；
  - 导出采纳互斥纯函数 `computeAdoptResult`：入口实施阶段合法性守卫（解决 🟡4），实施**非空内容有效性守卫**，被退级旧版写入 `isRetired: true`，采纳目标写入 `isRetired: false`，统一返回 `{ success: true, ... }`（彻底解决 🔴1, 🟡5, 🟡6）；
  - 导出活动文件保存纯函数 `computeSaveResult`：入口自证只读守卫（解决 🟡4），规范主干镜像实施非空内容守卫，统一返回 `{ success: true, ... }`（彻底解决 🔴1 & 🟡5）；
  - 导出恢复纯函数 `computeRestoreResult`：统一返回 `{ success: true, ... }`，无 active 恢复为 active，有 active 保持草稿，手建草稿保持草稿，写回 `isDeleted: false` 并确保 `name` 属性（解决 🔴2, 🔴3, 🟡5）；
  - 导出存量数据迁移函数 `migrateAndNormalizeFiles`：第一行保障 `item.name = fn`（解决 🔴2），`versionTag` 缺失优先从文件名反推（解决 🟡6），末尾按【最高版本数值 > 规范骨干 > 其余】显式排序严格单槽收敛，零 active 激活跳过镜像与母版（保证幂等性 · 解决 🟡2, 🟢2）；
  - 供 Step0App、useStep1 与 StudioEditor 共同引用，彻底杜绝重复代码。
- [x] 4.2 改造左栏废纸篓抽屉交互与组件事件规范 (`GEO/web/step0-src/components/studio/StudioFileTree.vue` · 解决 🔴2, 🔴3, 🟡7, 🟡11):
  - 显式声明 `stage: { type: String, default: '' }` prop，未传时警告并降级，杜绝崩溃（解决 🟡7）；
  - 锁定组件标准事件契约：`@openFile(filename)`、`@deleteFile(filename)`、`@restoreFile(filename)`（解决 🟡11）；
  - 抽屉受 `v-if="showStatusBadge && trashFiles.length > 0"` 严格约束，彻底杜绝污染阶段二至六；
  - 草稿删除垃圾桶图标仅在 `canDeleteFile(files[fn], props.stage)` 为 `true` 时 hover 渲染（手建非 active 草稿允许删除），根除死按钮；
  - 废纸篓条目绑定整行点击事件 `@click="$emit('openFile', fn)"`，并在右侧保留【恢复】按钮 `@click.stop="$emit('restoreFile', fn)"`。
- [x] 4.3 重构中栏编辑器顶栏为双行架构与 Tab 预览机制 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 🔴3, 🟡7, 🟡8, 🟡11):
  - 显式声明 `stage: { type: String, default: '' }` 与 `validAdoptSlots: { type: Array, default: () => [] }` props，未传 stage 时安全降级不白屏；
  - 锁定组件标准事件契约：`@adoptFile(filename)`、`@saveFile({ filename, content })`、`@restoreFile(filename)`（解决 🟡11）；
  - 第一行（状态与操作工具栏）：左侧展示当前文件状态徽章（文字说明 + 主题色，无彩色 Emoji）、字数与时间戳（缺失时显示 `生成时间: 未知`）；右侧偏右对齐排布快捷功能按钮；
  - 恢复按钮严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色；
  - 采纳守卫 `canAdoptCurrentFile` 显式排除手建文件（`isManual`），手建草稿不可作为核心工序底牌被采纳；允许已淘汰历史版本被点采纳实现版本回滚（解决 🔴3 & 🟡7）；
  - 第二行（Tab 标签栏）：独立一行平铺 `openTabs`，废纸篓文件标注 `[废纸篓]` 浅色标识，允许用户中栏只读预览查验（解决 🟡8）。
- [x] 4.4 实施正交只读与保存分流联动 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 🔴1, 🔴3, 🔴4):
  - 严格依据 `isReadOnlyFile(file, files, props.stage)` 判定只读：仅废纸篓文件、已淘汰历史旧版（`isRetired: true`）、以及具备 `isCanonicalMirror: true` 的规范主干自动镜像强制只读；
  - 当前生效底牌、最新候选工作草稿与手建草稿均完全允许打字编辑，展示【保存文件】按钮（手建文件永不只读 · 解决 🔴1 & 🔴3）；
  - 点击保存时根据当前文件状态分流派发 `@saveFile`（对生效底牌联动调用 `computeSaveResult`，受非空内容守卫保护；对普通草稿仅更新正文，不触发主干镜像 · 解决 🔴1）；
  - 在只读态下拦截 `Ctrl+S / Cmd+S` 保存快捷键并弹出对应原因提示。
- [x] 4.5 改造状态胶水层与全仓 SSOT 统一 (`Step0App.vue` & `useStep1.js` · 解决 🔴1-🔴3, 🟡9, 🟡10, 🟢3):
  - 编码前重跑全仓 grep 复核消费方，确认仅 Step0App 与 Step1App 加载 Studio 组件（解决 🟢3）；
  - 运行前全仓核对阶段零（2个）与阶段一（6个）真实生成文件名与 `CANONICAL_SLOT_DICT` 严格全等，且生成新草稿时直接使用 `slotItem.baseSlotName` 拼装文件名，消除重复拼装（解决 🟡10）；
  - 新写入代码（`handleDeleteFile`、`handleRestoreFile` 等）彻底统一写入 camelCase `isDeleted`，显式 `delete item.is_deleted`，彻底消除 snake_case 回潮（解决 🟡9）；
  - 初始化加载 localStorage 数据时统一接入 `migrateAndNormalizeFiles`，实现存量数据无感迁移与单槽 active 收敛；
  - 采纳统一调用 `computeAdoptResult`，由共享算法完成降级、升级、留档与非空单向镜像，同步更新活跃快照；
  - 保存文件统一调用 `computeSaveResult`，生效版本保存时自动单向同步镜像规范主干，同步更新活跃快照；
  - 恢复统一调用 `computeRestoreResult`，守住单槽单一 active 并同步快照；
  - 删除统一调用 `computeDeleteResult`，前置 Fail-Closed 校验 `canDeleteFile`，安全处理 openTabs 移除与平滑选中回退（解决 🟡1）；
  - `Step0App.vue` 与 `Step1App.vue` 向子组件显式传入 `:stage` 与 `:valid-adopt-slots`，且 Step0App 显式传入 `:show-status-badge="true"`。
- [x] 4.6 跨端构建与全量自动化断言冒烟验证（NE1 服务器执行 · 解决 🔴1-🔴4, 🟡1, 🟡2, 🟡6, 🟡7）:
  - 严格在 NE1 服务器执行 `npm run build:step0` 与 `npm run smoke:step0`（确保 5/5 项全部 PASS，16 项核心断言 100% 验证）；
  - 测试装载方式采用独立 node 脚本直接 import `studioArtifactConfig.js` 纯函数，支持注入确定性 `now` 时间戳参数（保证冒烟可复现 · 解决 🟡6, 🟡7）；
    - 针对以下 16 项关键断言进行全量回归自检：
    - 断言 1（正则防误读）：文件名 `01_网络底座指标_待对照.md` 的前缀 `01_` 不被误读为版本 1；
    - 断言 2（废纸篓参与计数）：生成 `第2版` 删入废纸篓后，再次生成新文件确定递增为 `第3版`；
    - 断言 3（标签规整）：采纳后文件 `versionTag` 确定无 `-Draft` 后缀；
    - 断言 4（双重锁防误删与无死按钮）：规范骨干无论是否生效均不可删、无垃圾桶；首版留档 `_第1版` 同样不可删；
    - 断言 5（单槽单一 active）：采纳后同 slotKey 其他文件 `isActive` 严格为 `false`，并被打上 `isRetired: true`；
    - 断言 6（骨干单向自动镜像等价与内容守卫 · 🔴1/🔴2 固化）：采纳有效新版或通过 `computeSaveResult` 编辑保存生效底牌后，规范骨干 content 100% 一致；空内容采纳被拦截，空内容保存严格拦截返回 `EMPTY_CONTENT`，骨干与生效底牌双向防洗白与分叉；
    - 断言 7（工作草稿打磨自由与手建隔离 · 🔴1 固化）：同槽存在 active 时，未采纳候选草稿（如第2版，`isRetired === undefined`）以及手建草稿（`isManual: true`）的 `:readonly` 严格为 `false`，完全可编辑打磨保存，且手建文件不参与工序版本计数；
    - 断言 8（规范骨干持久化标记与正交只读科学验证 · 🔴4 固化）：① 采纳第 2 版后，规范骨干打上 `isCanonicalMirror: true` 标记且强制只读；② 采纳第 3 版使第 2 版退级为历史旧版（`isRetired: true`）；③ 将退级后的第 2 版删入废纸篓，断言此时镜像骨干与首版母版依旧强制只读，状态绝不漂移；
    - 断言 9（恢复后单槽 active 严格唯一 · 🔴2 固化）：从废纸篓恢复任何文件后，同 slotKey 下 active 文件数始终严格为 1（无 active 恢复为 active，有 active 恢复为草稿）；
    - 断言 10（存量旧数据迁移收敛、不变式与幂等性 · 🔴2 固化）：老数据迁移后，所有对象严格具备 `item.name === fn` 硬约束不变式；多 active 脏数据按最高版本严格收敛为 1 个；手建草稿不被篡改；连续多次迁移完全幂等；
    - 断言 11（重载收敛不改写候选 · 🔴1 固化）：生成第 3 版草稿 → 执行 `migrateAndNormalizeFiles` → 断言该草稿 `isRetired === undefined` 且 `isReadOnlyFile === false`，绝不因刷新被误判淘汰（解决 🔴1 & 🟡3）；
    - 断言 12（缺失 stage 无害 Fail-Closed · 🔴2 固化）：`migrateAndNormalizeFiles(files, '')` → 断言 `slotKey` 未被破坏性改写为 `slot_misc`、文件对象不被篡改、无白屏异常（解决 🔴2 & 🟡3）；
    - 断言 13（阶段零 QA 槽位版本命名、镜像流转与留档防删全覆盖 · 🔴1/🔴2/🔴3 固化）：`computeNextVersion` 根据 `canonicalName` 准确提取扩展名（.txt），采纳后 `versionTag` 规范收敛为 `QA-V2`，规范骨干（`01_豆包提问清单_推荐版.txt`）同步镜像，首版母版（`01_豆包提问清单_第1版.txt`）自动留档且终身不可删；
    - 断言 14（母版解除采纳死锁与无损回滚 · 🔴2/🔴4 固化）：放开 `isProtectedArchive` 限制，第 1 版历史母版自由采纳生效，自动退级旧生效底牌，规范骨干精准镜像回母版内容，单槽活跃文件严格唯一，且采纳后解除只读死锁、允许打磨编辑与保存；
    - 断言 15（分支草稿生成与素材库 S 体系人机两分契约 · 🔴2 固化）：`computeBranchVersion` 精准生成 V3.1 分支，`filterMasterSourceFiles` 严格基于正则过滤剔除小数点分支草稿，仅向系统组装和外部 AI 提供标准 S 主版本；
    - 断言 16（智能 Tab 栈管理算法 · 师弟立规）：新打开 Tab 首置于第 0 位；上限 6 个时自动关闭最右侧（最老）未修改的干净 Tab；全脏时警告保护。
- [x] 4.7 管理端文案与操作反馈合规自检（按 AGENTS §3.3 / §3.5 执行 · 解决 🟡4, 🟡8, 🟢5, 🟢6）:
  - 严格落实 AGENTS §3.5 阶段零禁混谈条款：阶段零 UI 徽章、提示与文案中只使用『提问清单』与『豆包实测回答』等标准文案，严禁出现『底牌报告』等自造词混用（解决 🟡4）；
  - 检查所有新增 UI 文案与徽章：严格 0 彩色 Emoji 表情；
  - 检查操作颜色语义：恢复按钮使用系统主色紫，禁止使用危险红色；提示信息四色语义准确；
  - 核查文案符合 V-W-W-H 简洁易懂标准（五年级小学生可懂）。
- [ ] 4.8 浏览器真机验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）：
  - 验证废纸篓文件在中栏成功打开只读预览，第二行 Tab 出现 `[废纸篓]` 标识；
  - 验证第一行右侧展示紫色【一键恢复此文件】按钮，且编辑器不可打字、Cmd+S 会提示拦截；
  - 验证新抓取的 `第2版` 草稿可以正常打字编辑、修改并点击【保存文件】保存；
  - 验证点击【设为客户采纳】后，规范骨干自动同步最新内容，状态显示为自动镜像且只读不可直接覆盖保存；
  - 验证阶段零与阶段一均只展示各自阶段槽位，无跨阶段污染，双行顶栏展示清爽。

## 5. 成套版本套餐、回滚采纳、视觉瘦身与素材库S体系 (Grill-Me 迭代落地实施 · 已完成)

- [x] 5.1 解除第 1 版历史母版采纳死锁与无损回滚机制 (`GEO/web/step0-src/config/studioArtifactConfig.js` & `GEO/web/step0-src/components/studio/StudioEditor.vue`):
  - 修改 `canAdoptCurrentFile`：放开 `isProtectedArchive` 限制，允许第 1 版原始母版被点击【设为客户采纳】；
  - 优化母版徽章文案：由“终身留档”改为更亲切的“第 1 版 (原始母版)”；
  - 实现采纳母版后的单向镜像与跨阶段缓存同步，误点采纳后一键回滚。
- [x] 5.2 支持分支灵感草稿微调优化流转 (`GEO/web/step0-src/config/studioArtifactConfig.js`):
  - 在版本生成逻辑中增加分支生成能力（保留主版本 V3，派生灵感分支 V3.1，打上 `isBranchDraft: true`）；
  - 支持分支草稿自由打字编辑、保存与移入废纸篓。
- [x] 5.3 阶段 0.2 实测回答文件跟随提问清单多版本成套生成与问答成对排版 (`GEO/web/step0-src/Step0App.vue` & `GEO/web/step0-src/useStep0.js`):
  - 实测回答生成文件名跟随提问清单版本：`02_豆包实测回答记录_第${N}版.txt`，杜绝单一文件覆盖；
  - 正文严格按照【测试题目 + 对应回答】结构化排版，支持地域与核心业务参数化。
- [x] 5.4 阶段一初稿与最终报告多版本成套生成与出具入口 (`GEO/web/step0-src/useStep1.js`):
  - 出具初稿生成跟随阶段零版本的成套版本（初稿第 N 版、大屏第 N 版、文字版第 N 版），互不覆盖；
  - 骨干镜像终身豁免淘汰标记，退级逻辑保持干净。
- [x] 5.5 左侧文件树视觉瘦身与极简小绿勾规范 (`GEO/web/step0-src/components/studio/StudioFileTree.vue`):
  - 彻底干掉 `01_`、`02_` 冗余前缀；
  - 采纳徽章瘦身为极简小绿勾与版本标 `✓ V1`；
  - 人性化报告显示与状态呈现。
- [x] 5.6 阶段二素材库独立 S 体系与 6 大 RAG 黄金分类及全新动线 (`GEO/web/step0-src/stage2Config.js` & `GEO/web/step0-src/useStep2.js`):
  - 素材库独立抽离，使用 S 编号体系（主版本 S1，分支草稿 S1.1）；
  - 落实人机两分硬契约：系统组装母盘与外部喂 AI 时，只读取消费 S 主版本，严格过滤 `.x` 分支；
  - 梳理 6 大黄金检索分类（主体边界 S1、产品价格 S2、客户场景 S3、同行对比 S4_竞品、故事化案例库 S5_案例、权威凭据背书 S6）；
  - 故事化案例提取模型落地（标题 + 案例故事 + 量化结果）；
  - 动线重构：先分类录入与 9 因子提纯，再成套出具普林斯顿母盘（V1/V2）。
- [x] 5.7 跨端构建与全量自动化断言冒烟测试（NE1 服务器执行）:
  - 针对断言 14（母版解除采纳死锁）与断言 15（分支草稿生成与素材库 S 体系人机两分契约）进行完整验证；
  - 严格在 NE1 服务器执行 `npm run build:step0` 和 `npm run smoke:step0`，确保 15/15 项断言全部 PASS。
- [ ] 5.8 浏览器真机体验验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）:
  - 验证误点采纳后可一键切回第 1 版母版；
  - 验证实测回答生成对应版本且按 Q&A 排版；
  - 验证阶段一初稿生成对应版本且不覆盖旧版；
  - 验证文件树无冗余前缀且打上极简 `✓ V1` 小绿勾；
  - 验证阶段二素材库按 6 大分类提炼且系统只认 S 主版本。

## 6. 智能 Tab 栈管理、初稿微调分支与素材 8K 降噪分拣台 (Grill-Me 迭代任务 · 已完成代码与 16 项自动化自检)

- [x] 6.1 智能 Tab 栈管理重构 (`openTabs` 首置插入与超量 6 个智能淘汰):
  - 将激活/打开 Tab 的插入逻辑由 `push` 改为首置 `unshift`，新打开文件排在第 1 个；
  - 限制最大打开 6 个 Tab，超量时优先自动关闭最右侧（最老）且 `!isDirty` 的干净 Tab；
  - 若所有 6 个 Tab 均被修改，弹窗提示确认是否保存后再关闭。
- [x] 6.2 阶段一商业初稿出具分支派生 (`GEO/web/step0-src/useStep1.js`):
  - 出具初稿时检测已有主版本（基于 `isGenerated` 判定），派生生成 `01_商业诊断与转化初稿_第1.1版.md`，打上 `isBranchDraft: true`；
  - 保持原生 Markdown 高保真结构，无需去语法。
- [x] 6.3 阶段二动线错位纠偏与素材分拣台落地 (`GEO/web/step0-src/Step2App.vue` & `stage2Config.js`):
  - 修正 `Step2App.vue` 的 `StudioSop` 传参为 `:stage-meta="STAGE_2_META"`，彻底消除阶段零动线兜底，恢复阶段二 5 步真实动线；
  - 在第 1 步【素材分类归集与萃取】落地【智能素材分拣台】卡片；
  - 接入一键抓取官网（后端探测与 3000 字事实骨架）与手工粘贴框，保证文字输入在 8K Token (约 8500 汉字) 以内；
  - 提供【AI 智能分发到 6 大素材库】动作，自动分拣填入 S1~S6。
- [x] 6.4 跨端构建与全量自动化断言冒烟测试（NE1 服务器执行）:
  - 运行 `npm run build:step0 && npm run smoke:step0`，确保 16/16 项断言全部 PASS。
- [ ] 6.5 浏览器真机体验验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）:
  - 验证打开文件始终排在第 1 个，超量 6 个自动关掉干净 Tab；
  - 验证阶段一出具初稿派生 V1.1 分支；
  - 验证阶段二展示真实 5 步动线，素材分拣台抓取与粘贴分发正常。

## 7. 【02 客户素材资产管理库】独立整页化、6分类结构化资产台与时序拨乱反正（Grill-Me 迭代任务清单 · 已完成代码与构建）

- [x] 7.1 左侧全局大导航重组为 8 个独立大阶段 (`web/index.html`):
  - 侧栏菜单与 `VIEW_META` 明确确立 `02 客户素材资产管理库` 专属大阶段；
  - 保持阶段二独立路由与持久化状态，与阶段三交钥匙官网及母盘链路顺畅对接。
- [x] 7.2 阶段 02 全新构建为纯粹的【客户素材资产管理工作台】 (`web/step0-src/Step2App.vue` & `stage2Config.js` & `useStep2.js`):
  - 顶栏：实现【一键抓取官网骨架】（3000 字事实降噪）与【资料自由粘贴 AI 分流】抽屉入口；
  - 主区域：实现 6 大分类结构化资产卡片面板（S1主体、S2价格、S3画像痛点、S4竞品对标、S5真实案例故事、S6权威凭据背书）；
  - 实现每个分类的专属结构化面板（S4 支持点选新增对标竞品、S5 瀑布流管理三段式客户故事卡片、S2 价格标准维护、S1 核心工商主体维护）；
  - 右侧栏：素材资产健康度自检看板与【核验并前往阶段三母盘 ➔】推进按钮；
  - 数据层：自动将 6 大分类的结构化数据双向编译并同步更新至底层标准 `S1~S6.md` 文件，满足人机两分契约；
  - 母盘保护：持久化维护 `geo_step2_master_text_`，保障阶段三及下游消费不中断。
- [x] 7.3 阶段 02 与 03 彻底解耦，时序拨乱反正 (`web/step0-src/stage2Config.js` & `web/step0-src/Step2App.vue`):
  - 阶段二彻底剔除博文库（`article_*.md`）及博文派生逻辑，博文时序拨乱反正至阶段六；
  - 彻底移除旧版混杂的母盘与博文文件，聚焦纯粹的客户素材资产库。
- [x] 7.4 自动化冒烟测试与断言扩展 (`tests/smoke_studio_artifacts.mjs` & `scripts/smoke_step0.sh`):
  - 验证 S1~S6 编译同步与人机两分契约；
  - 严格在 NE1 服务器执行 `npm run build:step0 && npm run smoke:step0`，19/19 项断言 100% PASS。
- [ ] 7.5 浏览器真机体验验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）:
  - 验证左侧大导航清晰展现 02 客户素材资产管理库；
  - 验证素材管理台 6 大分类卡片操作流畅、新增案例/竞品正常，双模切换平滑；
  - 验证阶段二恢复纯粹清爽，无博文与旧版母盘冲突卡片干扰。

## 8. 【02 客户素材资产工作台】真实双场景、人工审核与 RAG 语义去重落实清单 (师弟立规 · 严防遗漏铁律)

- [x] 8.1 中间大文字书写稿与真实双场景进场 (`web/step0-src/Step2App.vue` & `useStep2.js`):
  - [x] 搭建中间可自由打字编辑的【大文字书写稿】工作草稿主区域；
  - [x] 场景一（单一网址抓取）：实现输入网址 ➔ 点击抓取 ➔ 提纯正文 ➔ 自动回填至中间文字稿；
  - [x] 场景二（人工自由粘贴）：支持操作员从本地文件、微信聊天记录复制文字粘贴到中间文字稿；
  - [x] 8500 字上限监控与变色预警：实时统计汉字字数，`<= 8500` 显示绿色，`> 8500` 实时变红并拦截 AI 分拣，提示用户人工删减修饰。
- [x] 8.2 AI 语义切块协议与 6 大黄金分类输出 (`web/step0-src/stage2Config.js` & 后端 API):
  - [x] 构造轻量大模型分类 Prompt，将不超过 8500 字的长文按 S1~S6（主体、价格、场景、竞品、案例、资质）切分为 3~4 个独立素材片段；
  - [x] 输出结构化切片数组，包含 `chunkId`、`targetCategory`、`suggestedTitle`、`content`。
- [x] 8.3 人工终审工作台与四项绝对权力 (`web/step0-src/Step2App.vue`):
  - [x] 弹层/抽屉渲染切片审核流水席，坚决不搞暗箱操作私自落库；
  - [x] 实现权能一【预览】：点击展开完整文字正文与字数；
  - [x] 实现权能二【修改】：切片卡片内支持直接打字修改文字，标记 `isEdited: true`；
  - [x] 实现权能三【纠偏】：下拉框支持一键切换所属分类（如从 S2 切换到 S3）；
  - [x] 实现权能四【废弃】：卡片右上角垃圾桶一键丢弃无用片段；
  - [x] 实现权能五【采纳】：点击【确认采纳入库】，触发 RAG 语义去重流程。
- [x] 8.4 RAG 语义聚类去重机制（师弟立规 · 彻底杜绝死板标题匹配）(`web/step0-src/useStep2.js` & `stage2Config.js`):
  - [x] 严禁使用“标题是否一模一样”作为判重标准，全面接入正文语义向量相似度（RAG）；
  - [x] 切片入库前，与当前客户已存素材库进行语义比对；
  - [x] 相似度高（≥ 0.50 黄金阈值）的素材，自动聚类归入【去重对比组 / 二级子目录】集中呈现。
- [x] 8.5 左右双栏对比与人工文案合并器 (`web/step0-src/Step2App.vue`):
  - [x] 左栏展示存量老素材，右栏展示新提取素材，直观对比差异；
  - [x] 提供【人工文案合并】编辑器，操作员将有效信息整合为终稿；
  - [x] 点击【完成合并并更新库】，以合并终稿替换老版本，保证知识库唯一性与干净度。
- [x] 8.6 存储唯一性与母盘下游消费闭环 (`useStep2.js`):
  - [x] 严格绑定当前项目 `client_id`，自然归入当前客户的项目知识库，彻底消除“存哪个库”的歧义；
  - [x] 素材定稿推进时自动调用 `generateMasterCorpusMarkdown` 生成母盘，并持久化写入 `geo_step2_master_text_${clientId}` / `geo_step3_master_text_${clientId}`，确保阶段三交钥匙官网能够无缝直接消费。
- [x] 8.7 跨端构建与全量自动化断言验证（NE1 服务器执行）:
  - [x] 扩展断言 17（8500 字上限拦截与场景切换校验，真实函数级测试）；
  - [x] 扩展断言 18（AI 语义切块输出契约与人工修改状态保持）；
  - [x] 扩展断言 19（RAG 语义去重聚类与文案合并终态）；
  - [x] 严格在 NE1 服务器执行 `npm run build:step0 && npm run smoke:step0`，确保 19/19 项断言全部 PASS。
- [ ] 8.8 浏览器真机体验验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）:
  - [ ] 验证输入网址能抓取文字并填入中间写字板；
  - [ ] 验证粘贴文字超过 8500 字会变红并拦截提醒；
  - [ ] 验证 AI 切块后弹出审核席，可改文字、可改分类、可删、可入库；
  - [ ] 验证相似素材能被 RAG 聚类到去重组，人工合并文案后正常更新。

## 9. 【中栏双行标准头部组件 (StudioHeader) 抽象与第二页复用】开发任务清单 (师弟立规 · 严禁偷跑)

- [x] 9.1 新建公共头部组件 (`web/step0-src/components/studio/StudioHeader.vue`):
  - [x] 封装第一行：状态元数据展示（自适应解析文件状态徽章、字符数统计、生成时间戳）；
  - [x] 封装第一行快捷操作插槽 `<slot name="actions">`，支持外部定制按钮组；
  - [x] 封装第二行：独立文件 Tab 标签栏，支持当前选中高亮、`[废纸篓]` 标识、未保存黄点以及关闭按钮；
  - [x] 集成顶部浮动轻量通知（`noticeMessage`，防原生 alert 红线）。
- [x] 9.2 重构第一页编辑器 (`web/step0-src/components/studio/StudioEditor.vue`):
  - [x] 剥离现有的内联双行头部，统一引入 `<StudioHeader>`；
  - [x] 将原有【源码/预览/全屏/复制/保存】按钮通过 `<template #actions>` 优雅注入；
  - [x] 验证第一页视觉、快捷键（Ctrl+S）、视图切换等功能 100% 保持一致无退化。
- [x] 9.3 改造第二页素材库工作台 (`web/step0-src/Step2App.vue`):
  - [x] 彻底剔除内联挤在第一排的 Tab 栏与操作按钮；
  - [x] 引入 `<StudioHeader>`，第二排独立展开文件 Tabs（`openTabs`），第一排插槽注入【素材采集与蒸馏工作台 / Markdown源码】模式切换 + 【一键复制】 + 【保存修改】；
  - [x] 彻底消灭第一排挤扁变形问题，第二页视觉层次与第一页 100% 统一。
- [x] 9.4 跨端构建与全量自动化断言验证（NE1 服务器执行）:
  - [x] 严格在 NE1 服务器执行 `npm run build:step0 && npm run smoke:step0`；
  - [x] 确保 19/19 项自动化断言 100% PASS，产物打包无错误。
- [ ] 9.5 浏览器真机体验验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）:
  - [ ] 刷新 `http://100.83.64.112:8088/` 页面；
  - [ ] 验证第一页（阶段一）双行头部正常，各项操作不退化；
  - [ ] 验证第二页（阶段二）第一排清爽展示操作按钮，第二排整齐独立展示 Tab 标签栏，彻底告别拥挤。

