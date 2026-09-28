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

> **迭代阶段说明**：第 1~3 节代码与冒烟已在上一轮完成并验证入库（commit `f2e1daf`）；第 4 节为本次 Grill-Me 迭代新需求，当前处于纯方案设计阶段（stage=design），本节任务全部保持 `[ ]` 未勾选，严格遵循立定停步铁律，未经 `/opsx-team-apply`（或 `/opsx-apply`）绝不提前编码。

- [ ] 4.1 新建共享配置与算法模块 (`GEO/web/step0-src/config/studioArtifactConfig.js` · 解决 🔴1-🔴4, 🟡2-🟡8, 🟢1-🟢3):
  - 集中定义 8 大核心工序槽位字典 `CANONICAL_SLOT_DICT` 与别名容错字典 `ALIAS_SLOT_MAP`，导出 `resolveSlotKey` 未匹配项统一兜底常量 `slot_misc`（解决 🔴3 & 🟡8）；
  - 导出 `safeStorageGet / safeStorageSet` 薄封装（带环境安全探测，保障纯函数与存储解耦 · 解决 🟢1）；
  - 导出按阶段收窄器 `getSlotsByStage` 与 `getCoreFilesByStage`（未传 stage 时安全降级为空集合并报警，坚决不抛错，彻底杜绝白屏崩溃 · 解决 🟡6, 🟡7）；
  - 集中封装动态版本正则构造器 `buildSlotRegex`（带 `escapeRegExp` 字符转义）、版本提取防重名算法 `computeNextVersion`（过滤手建文件 · 解决 🔴3）；
  - 导出双重锁删除判定 `canDeleteFile`（Fail-Closed 关闸保护：无论 stage 是否传入，规范镜像与母版留档终身不可删 · 解决 🟡3）；
  - 导出正交只读判定 `isReadOnlyFile`（优先依据 `isRetired === true` 判定淘汰只读，新生成候选草稿不带 isRetired 绝对不只读；已淘汰历史版本只读但支持回滚采纳 · 解决 🔴1 & 🟡7）；
  - 导出采纳互斥纯函数 `computeAdoptResult`：入口实施阶段合法性守卫（解决 🟡4），实施**非空内容有效性守卫**，被退级旧版写入 `isRetired: true`，采纳目标写入 `isRetired: false`，统一返回 `{ success: true, ... }`（彻底解决 🔴1, 🟡5, 🟡6）；
  - 导出活动文件保存纯函数 `computeSaveResult`：入口自证只读守卫（解决 🟡4），规范主干镜像实施非空内容守卫，统一返回 `{ success: true, ... }`（彻底解决 🔴1 & 🟡5）；
  - 导出恢复纯函数 `computeRestoreResult`：统一返回 `{ success: true, ... }`，无 active 恢复为 active，有 active 保持草稿，手建草稿保持草稿，写回 `isDeleted: false` 并确保 `name` 属性（解决 🔴2, 🔴3, 🟡5）；
  - 导出存量数据迁移函数 `migrateAndNormalizeFiles`：第一行保障 `item.name = fn`（解决 🔴2），`versionTag` 缺失优先从文件名反推（解决 🟡6），末尾按【规范骨干 > 最高版本数值 > 其余】显式排序严格单槽收敛，零 active 激活跳过镜像与母版（保证幂等性 · 解决 🟡2, 🟢2）；
  - 供 Step0App、useStep1 与 StudioEditor 共同引用，彻底杜绝重复代码。
- [ ] 4.2 改造左栏废纸篓抽屉交互与组件事件规范 (`GEO/web/step0-src/components/studio/StudioFileTree.vue` · 解决 🔴2, 🔴3, 🟡7, 🟡11):
  - 显式声明 `stage: { type: String, default: '' }` prop，未传时警告并降级，杜绝崩溃（解决 🟡7）；
  - 锁定组件标准事件契约：`@openFile(filename)`、`@deleteFile(filename)`、`@restoreFile(filename)`（解决 🟡11）；
  - 抽屉受 `v-if="showStatusBadge && trashFiles.length > 0"` 严格约束，彻底杜绝污染阶段二至六；
  - 草稿删除垃圾桶图标仅在 `canDeleteFile(files[fn], props.stage)` 为 `true` 时 hover 渲染（手建非 active 草稿允许删除），根除死按钮；
  - 废纸篓条目绑定整行点击事件 `@click="$emit('openFile', fn)"`，并在右侧保留【恢复】按钮 `@click.stop="$emit('restoreFile', fn)"`。
- [ ] 4.3 重构中栏编辑器顶栏为双行架构与 Tab 预览机制 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 🔴3, 🟡7, 🟡8, 🟡11):
  - 显式声明 `stage: { type: String, default: '' }` 与 `validAdoptSlots: { type: Array, default: () => [] }` props，未传 stage 时安全降级不白屏；
  - 锁定组件标准事件契约：`@adoptFile(filename)`、`@saveFile({ filename, content })`、`@restoreFile(filename)`（解决 🟡11）；
  - 第一行（状态与操作工具栏）：左侧展示当前文件状态徽章（文字说明 + 主题色，无彩色 Emoji）、字数与时间戳（缺失时显示 `生成时间: 未知`）；右侧偏右对齐排布快捷功能按钮；
  - 恢复按钮严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色；
  - 采纳守卫 `canAdoptCurrentFile` 显式排除手建文件（`isManual`），手建草稿不可作为核心工序底牌被采纳；允许已淘汰历史版本被点采纳实现版本回滚（解决 🔴3 & 🟡7）；
  - 第二行（Tab 标签栏）：独立一行平铺 `openTabs`，废纸篓文件标注 `[废纸篓]` 浅色标识，允许用户中栏只读预览查验（解决 🟡8）。
- [ ] 4.4 实施正交只读与保存分流联动 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 🔴1, 🔴3, 🔴4):
  - 严格依据 `isReadOnlyFile(file, files, props.stage)` 判定只读：仅废纸篓文件、已淘汰历史旧版（`isRetired: true`）、以及具备 `isCanonicalMirror: true` 的规范主干自动镜像强制只读；
  - 当前生效底牌、最新候选工作草稿与手建草稿均完全允许打字编辑，展示【保存文件】按钮（手建文件永不只读 · 解决 🔴1 & 🔴3）；
  - 点击保存时根据当前文件状态分流派发 `@saveFile`（对生效底牌联动调用 `computeSaveResult`，受非空内容守卫保护；对普通草稿仅更新正文，不触发主干镜像 · 解决 🔴1）；
  - 在只读态下拦截 `Ctrl+S / Cmd+S` 保存快捷键并弹出对应原因提示。
- [ ] 4.5 改造状态胶水层与全仓 SSOT 统一 (`Step0App.vue` & `useStep1.js` · 解决 🔴1-🔴3, 🟡9, 🟡10, 🟢3):
  - 编码前重跑全仓 grep 复核消费方，确认仅 Step0App 与 Step1App 加载 Studio 组件（解决 🟢3）；
  - 运行前全仓核对阶段零（2个）与阶段一（6个）真实生成文件名与 `CANONICAL_SLOT_DICT` 严格全等，且生成新草稿时直接使用 `slotItem.baseSlotName` 拼装文件名，消除重复拼装（解决 🟡10）；
  - 新写入代码（`handleDeleteFile`、`handleRestoreFile` 等）彻底统一写入 camelCase `isDeleted`，显式 `delete item.is_deleted`，彻底消除 snake_case 回潮（解决 🟡9）；
  - 初始化加载 localStorage 数据时统一接入 `migrateAndNormalizeFiles`，实现存量数据无感迁移与单槽 active 收敛；
  - 采纳统一调用 `computeAdoptResult`，由共享算法完成降级、升级、留档与非空单向镜像，同步更新活跃快照；
  - 保存文件统一调用 `computeSaveResult`，生效版本保存时自动单向同步镜像规范主干，同步更新活跃快照；
  - 恢复统一调用 `computeRestoreResult`，守住单槽单一 active 并同步快照；
  - `Step0App.vue` 与 `Step1App.vue` 向子组件显式传入 `:stage` 与 `:valid-adopt-slots`，且 Step0App 显式传入 `:show-status-badge="true"`。
- [ ] 4.6 跨端构建与全量自动化断言冒烟验证（NE1 服务器执行 · 解决 🔴1-🔴4, 🟡1, 🟡2, 🟡6, 🟡7）:
  - 严格在 NE1 服务器执行 `npm run build:step0` 与 `npm run smoke:step0`（确保 4/4 项全部 PASS）；
  - 测试装载方式采用独立 node 脚本直接 import `studioArtifactConfig.js` 纯函数，支持注入确定性 `now` 时间戳参数（保证冒烟可复现 · 解决 🟡6, 🟡7）；
  - 针对以下 10 项关键断言进行全量回归自检：
    - 断言 1（正则防误读）：文件名 `01_网络底座指标_待对照.md` 的前缀 `01_` 不被误读为版本 1；
    - 断言 2（废纸篓参与计数）：生成 `第2版` 删入废纸篓后，再次生成新文件确定递增为 `第3版`；
    - 断言 3（标签规整）：采纳后文件 `versionTag` 确定无 `-Draft` 后缀；
    - 断言 4（双重锁防误删与无死按钮）：规范骨干无论是否生效均不可删、无垃圾桶；首版留档 `_第1版` 同样不可删；
    - 断言 5（单槽单一 active）：采纳后同 slotKey 其他文件 `isActive` 严格为 `false`，并被打上 `isRetired: true`；
    - 断言 6（骨干单向自动镜像等价与内容守卫 · 🔴1 固化）：采纳有效新版或通过 `computeSaveResult` 编辑保存生效底牌后，规范骨干 content 100% 一致；空内容采纳被拦截，空内容保存严格不洗白规范骨干；
    - 断言 7（工作草稿打磨自由与手建隔离 · 🔴1 固化）：同槽存在 active 时，未采纳候选草稿（如第2版，`isRetired === undefined`）以及手建草稿（`isManual: true`）的 `:readonly` 严格为 `false`，完全可编辑打磨保存，且手建文件不参与工序版本计数；
    - 断言 8（规范骨干持久化标记与正交只读科学验证 · 🔴4 固化）：① 采纳第 2 版后，规范骨干打上 `isCanonicalMirror: true` 标记且强制只读；② 采纳第 3 版使第 2 版退级为历史旧版（`isRetired: true`）；③ 将退级后的第 2 版删入废纸篓，断言此时镜像骨干与首版母版依旧强制只读，状态绝不漂移；
    - 断言 9（恢复后单槽 active 严格唯一 · 🔴2 固化）：从废纸篓恢复任何文件后，同 slotKey 下 active 文件数始终严格为 1（无 active 恢复为 active，有 active 恢复为草稿）；
    - 断言 10（存量旧数据迁移收敛、不变式与幂等性 · 🔴2 固化）：老数据迁移后，所有对象严格具备 `item.name === fn` 硬约束不变式；多 active 脏数据按最高版本严格收敛为 1 个；手建草稿不被篡改；连续多次迁移完全幂等。
- [ ] 4.7 管理端文案与操作反馈合规自检（按 AGENTS §3.3 / §3.5 执行 · 解决 🟡8, 🟢5, 🟢6）:
  - 检查所有新增 UI 文案与徽章：严格 0 彩色 Emoji 表情；
  - 检查操作颜色语义：恢复按钮使用系统主色紫，禁止使用危险红色；提示信息四色语义准确；
  - 核查文案符合 V-W-W-H 简洁易懂标准（五年级小学生可懂）。
- [ ] 4.8 浏览器真机验收（NE1 8088 端口 · 人工验收留白项，AI 不得代勾）：
  - 验证废纸篓文件在中栏成功打开只读预览，第二行 Tab 出现 `[废纸篓]` 标识；
  - 验证第一行右侧展示紫色【一键恢复此文件】按钮，且编辑器不可打字、Cmd+S 会提示拦截；
  - 验证新抓取的 `第2版` 草稿可以正常打字编辑、修改并点击【保存文件】保存；
  - 验证点击【设为客户采纳】后，规范骨干自动同步最新内容，状态显示为自动镜像且只读不可直接覆盖保存；
  - 验证阶段零与阶段一均只展示各自阶段槽位，无跨阶段污染，双行顶栏展示清爽。


