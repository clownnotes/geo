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

- [ ] 4.1 新建共享配置模块 (`GEO/web/step0-src/config/studioArtifactConfig.js` · 解决 🔴2, A1, A3)：
  - 集中定义 8 大核心工序槽位字典 `CANONICAL_SLOT_DICT`；
  - 导出按阶段收窄器 `getSlotsByStage` 与 `getCoreFilesByStage`，彻底杜绝跨阶段污染；
  - 集中封装动态版本正则构造器 `buildSlotRegex`、版本提取防重名算法 `computeNextVersion`、双重锁删除判定 `canDeleteFile`、正交只读判定 `isReadOnlyFile`、版本号规整 `normalizeVersionTag`；
  - 供 Step0App、useStep1 与 StudioEditor 共同引用，彻底杜绝重复代码。
- [ ] 4.2 改造左栏废纸篓抽屉交互与删除死按钮消除 (`GEO/web/step0-src/components/studio/StudioFileTree.vue` · 解决 Y3, C4)：
  - 抽屉受 `v-if="showStatusBadge && trashFiles.length > 0"` 严格约束，彻底杜绝污染阶段二至六；
  - 草稿删除垃圾桶图标仅在 `canDeleteFile(files[fn], stage)` 为 `true` 时 hover 渲染，根除死按钮；
  - 废纸篓条目绑定整行点击事件 `@click="$emit('openFile', fn)"`，并在右侧保留【恢复】按钮 `@click.stop="$emit('restoreFile', fn)"`。
- [ ] 4.3 重构中栏编辑器顶栏为双行独立架构 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 🔴2, A4)：
  - 第一行（状态与操作工具栏）：左侧展示当前文件状态徽章（文字说明 + 主题色，无彩色 Emoji）、字数与时间戳；右侧偏右对齐排布快捷功能按钮；
  - 恢复按钮严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色；
  - `validAdoptSlots` 由父组件按阶段显式传入（Step0App 传 `getSlotsByStage('step0')`，Step1App 传 `getSlotsByStage('step1')`），默认空数组，杜绝跨阶段槽位污染与内部硬编码；
  - 第二行（Tab 标签栏）：独立一行平铺 `openTabs`，废纸篓文件标注 `[废纸篓]` 浅色标识，解决多文件拥挤。
- [ ] 4.4 实施正交只读与候选工作草稿自由编辑打磨机制 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 🔴1, C1)：
  - 严格依据 `isReadOnlyFile(file, files, stage)` 判定只读：仅废纸篓文件、已淘汰历史旧版、以及同槽位已有更新 active 时的规范主干自动镜像强制只读；
  - 当前生效底牌、最新候选工作草稿与新建文件均完全允许打字编辑，并展示【保存文件】按钮；
  - 在只读态下拦截 `Ctrl+S / Cmd+S` 保存快捷键并弹出对应原因提示。
- [ ] 4.5 改造状态胶水层与活动文件保存单向镜像主干 (`Step0App.vue` & `useStep1.js` · 解决 🔴1, 🔴3, C2, C3)：
  - 采纳时统一调用 `normalizeVersionTag` 剥离 `-Draft` 标签，初次采纳新版本时原骨干自动另存为 `_第1版` 留档；
  - 活动文件（`isActive === true`）保存或采纳时，自动将最新内容单向镜像更新至同槽位规范骨干文件对象，并更新快照 `updatedAt`；
  - 规范骨干退级后徽章明确显示为【规范主干 · 自动镜像】，隐藏保存按钮，仅由程序单向镜像写入；
  - 落实一键恢复确定性生命周期：移出废纸篓时，若槽位无 active 则恢复为 active，若已有 active 则严格保持草稿，绝对守住单槽单一 active 不变量；
  - `Step0App.vue` 显式传入 `:show-status-badge="true"`，保证废纸篓抽屉正常启用。
- [ ] 4.6 跨端构建与全量自动化断言冒烟验证（NE1 服务器执行 · 解决 🔴1, 🔴3, C5）：
  - 严格在 NE1 服务器执行 `npm run build:step0` 与 `npm run smoke:step0`（确保 4/4 项全部 PASS）；
  - 针对以下关键断言进行全量回归自检：
    - 断言 1（正则防误读）：文件名 `01_网络底座指标_待对照.md` 的前缀 `01_` 不被误读为版本 1；
    - 断言 2（废纸篓参与计数）：生成 `第2版` 删入废纸篓后，再次生成新文件确定递增为 `第3版`；
    - 断言 3（标签规整）：采纳后文件 `versionTag` 确定无 `-Draft` 后缀；
    - 断言 4（双重锁防误删与无死按钮）：规范骨干无论是否生效均不可删、无垃圾桶；
    - 断言 5（单槽单一 active）：采纳后同 slotKey 其他文件 `isActive` 严格为 `false`；
    - 断言 6（骨干单向自动镜像等价）：采纳新版或编辑保存生效文件后，规范骨干 content 与生效版本 content 100% 一致；
    - 断言 7（工作草稿打磨自由）：新抓取派生的候选草稿与新建文件 `:readonly` 严格为 `false`，完全可编辑保存；
    - 断言 8（规范骨干存在更新 active 时强制只读 · 🔴1 固化）：同槽采纳第 2 版后，规范骨干 `isReadOnlyFile === true`，徽章为镜像主干；
    - 断言 9（恢复后单槽 active 严格唯一 · 🔴3 固化）：从废纸篓恢复任何文件后，同 slotKey 下 active 文件数始终严格为 1。
- [ ] 4.7 浏览器真机验收（NE1 8088 端口 · 人工验收项，AI 不得代勾）：
  - 验证废纸篓文件在中栏成功打开只读预览，第二行 Tab 出现 `[废纸篓]` 标识；
  - 验证第一行右侧展示紫色【一键恢复此文件】按钮，且编辑器不可打字、Cmd+S 会提示拦截；
  - 验证新抓取的 `第2版` 草稿可以正常打字编辑、修改并点击【保存文件】保存；
  - 验证点击【设为客户采纳】后，规范骨干自动同步最新内容，状态显示为自动镜像且只读不可直接覆盖保存；
  - 验证阶段零与阶段一均只展示各自阶段槽位，无跨阶段污染，双行顶栏展示清爽。
