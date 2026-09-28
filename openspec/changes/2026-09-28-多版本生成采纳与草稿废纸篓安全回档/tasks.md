# Tasks: 多版本生成采纳与草稿废纸篓安全回档

## 1. 准备与规范核对

- [x] 1.1 核对 `AGENTS.md §3.3`（视觉设计规范与主色紫红线）、`§3.5`（管理端文案与操作反馈规范）、`§4.5`（本地零编译，打包构建必须在 NE1 服务器）。
- [x] 1.2 确认修改涉及的核心文件：`StudioFileTree.vue`、`stage1Config.js`、`useStep1.js`、`Step1App.vue`、`StudioEditor.vue`、`Step0App.vue`。

## 2. 前端组件与业务逻辑编码

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

## 3. 构建与端到端真机验收

- [x] 3.1 跨端构建（严格遵守 `AGENTS.md §4.5`）：在 NE1 服务器执行仓库根构建命令 `npm run build:step0`，产物写入 `web/assets/step0/` 并由 `stamp-build.mjs` 打版本戳。
- [x] 3.2 运行端到端冒烟测试（`npm run smoke:step0`），确保 4/4 项全部 PASS。
- [ ] 3.3 浏览器真机验证（NE1 开发环境 8088 端口 · 人工浏览器验收项，AI 不得代勾）：
  - 观察阶段零与阶段一草稿文件 hover 均出现删除垃圾桶图标，点击成功移入废纸篓；
  - 观察已采纳文件受到强制保护，不出现删除按钮；
  - 观察左栏底部的【已归档 / 废纸篓】抽屉展开展示被删文件，点击【恢复】一键原位复原；
  - 观察阶段一点击【已抓取真实指标（点击重新抓取）】，成功在左栏生成 `01_网络底座指标_第2版.md` 草稿并自动打开；
  - 观察点击中栏【设为客户采纳】，新版获得已采纳徽章，原版本退回为普通草稿；
  - 观察刷新页面后，采纳标记、时间戳与废纸篓状态 100% 保持。

## 4. 废纸篓只读查验与顶栏双行解耦改造 (Grill-Me 迭代增量)

> **迭代阶段说明**：第 1~3 节代码与冒烟已在上一轮完成并验证入库（commit `f2e1daf`，真机浏览器人工验收待补）；第 4 节为本次 Grill-Me 迭代新需求，当前处于纯方案设计阶段（stage=design），本节任务全部保持 `[ ]` 未勾选，严格遵循立定停步铁律，未经 `/opsx-team-apply`（或 `/opsx-apply`）绝不提前编码。

- [ ] 4.1 改造左栏废纸篓抽屉交互 (`GEO/web/step0-src/components/studio/StudioFileTree.vue` · 解决 Y3)：
  - 约束渲染条件为 `v-if="showStatusBadge && trashFiles.length > 0"`，杜绝污染阶段二/三；
  - 为废纸篓条目绑定整行点击事件 `@click="$emit('openFile', fn)"`，允许点击废纸篓文件直接在中栏打开；
  - 保留右侧【恢复】按钮 `@click.stop="$emit('restoreFile', fn)"`，防止冒泡。
- [ ] 4.2 重构中栏编辑器顶栏为双行独立架构 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 Y1/Y3)：
  - 第一行（状态与操作工具栏）：左侧展示当前文件状态（废纸篓状态展示 `[废纸篓归档 · 只读状态]`，非活跃历史版本展示 `[历史版本 · 只读归档]`）；右侧偏右对齐排布快捷功能按钮；
  - 若为废纸篓文件，右侧提供醒目的【一键恢复此文件】高亮按钮（派发 `@restoreFile` 事件，严格遵循 AGENTS §3.3 使用系统主色紫 `--geo-primary` / `bg-[#7c5bf5]`，严禁使用红色），直接隐藏【设为采纳】与【保存文件】；
  - 若为历史非生效草稿，展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】，**直接隐藏【保存文件】**；
  - 若为正常生效底牌，展示【客户生效底牌】、【源码/预览】、【全屏】、【一键复制】、【保存文件】；
  - **回归收紧 tasks 2.4**：升级 `canAdoptCurrentFile` 判定，严格按 8 大核心槽位白名单校验，禁止杂项文件采纳为底牌；
  - 第二行（Tab 标签栏）：独立一行平铺 `openTabs`，废纸篓文件在 Tab 标签上标注 `[废纸篓]` 浅色标识，彻底解决多文件拥挤问题。
- [ ] 4.3 废纸篓与历史版本双重只读保护与快捷键守卫 (`GEO/web/step0-src/components/studio/StudioEditor.vue` · 解决 R2)：
  - 当 `currentFile?.is_deleted || !currentFile?.isActive` 为 `true` 时，文本编辑区 `<textarea>` 自动置为 `:readonly="true"` 并应用只读浅色背景，防止误操作；
  - 在编辑器容器/textarea 上拦截 `Ctrl+S / Cmd+S` 保存快捷键，只读态下提示“当前为历史非生效版本，禁止直接覆盖保存！如需以此为准修改，请先点击【设为客户采纳】或另存新版”。
- [ ] 4.4 完善采纳剥离 `-Draft`、骨干镜像与双重删除安全锁 (`Step0App.vue` & `useStep1.js` · 解决 R1/R2/R4/Y4/Y5)：
  - 阶段零规范骨干初始标签统一为 `QA-V1`，采纳时统一按 `slotKey` 精确隔离互斥，并自动剥离 `-Draft` 标签（如 `QA-V2-Draft` -> `QA-V2`，`V2-Draft` -> `V2`）；
  - 采纳时将新内容同步镜像写入槽位对应的规范骨干文件对象（更新其 `content` 与 `versionTag`）；
  - 实施双重不可删除保护锁：① 正在生效的文件（`isActive === true`）禁止删除；② 属于 8 大核心主干的初始规范文件（在 `CANONICAL_CORE_FILES` 白名单中），即使处于退级态也受系统终身保护禁止删除；
  - 仅允许对派生出来的草稿版本（`第2版` 等）且 `isActive === false` 时执行删除移入废纸篓。
- [ ] 4.5 写入阶段一生效槽位快照与主仓 outputs 双写同步 (`useStep1.js` · 解决 R1 & R3 · 解决 Y2)：
  - 采纳时同步写入 `geo_step1_active_slots_${clientId}` 快照（记录各 `slotKey` 的 `canonicalFileName` 与 `adoptedDraftName`）；
  - 采纳时复用 `PUT /api/projects/:id` 接口，将最新生效内容覆盖写回主仓 `projects/{id}/outputs/` 规范主干文件，彻底消除双头真相源。
- [ ] 4.6 跨端构建与端到端自动化冒烟验证（NE1 服务器执行 · 解决 Y6）：
  - 严格在 NE1 服务器执行 `npm run build:step0` 与 `npm run smoke:step0`（确保 4/4 项全部 PASS）；
  - 针对以下 5 项关键不变量进行自动化断言验证：
    - 断言 1：正则防误读：文件名 `01_网络底座指标_待对照.md` 的前缀 `01_` 不被误读为版本 1；
    - 断言 2：废纸篓参与计数：生成 `第2版` 删入废纸篓后，再次生成新文件确定递增为 `第3版`；
    - 断言 3：标签规整：采纳后文件 `versionTag` 确定无 `-Draft` 后缀；
    - 断言 4：双重锁防误删：规范骨干文件无论 `isActive` 为何值均不可删除；
    - 断言 5：单槽单一 active：采纳后同 slotKey 其他文件 `isActive` 严格为 `false`。
- [ ] 4.7 浏览器真机验收（NE1 8088 端口 · 人工验收项，AI 不得代勾）：
  - 点击左栏底部的废纸篓文件，验证在中栏成功打开只读预览，第二行 Tab 出现 `[废纸篓]` 标识；
  - 验证第一行右侧偏右对齐展示【一键恢复此文件】等按钮，且编辑器不可打字输入、按 Cmd+S 会提示拦截；
  - 点击【一键恢复此文件】，验证文件立即变回可编辑正常草稿，原位恢复；
  - 验证阶段零与阶段一在双行顶栏下均正常展示、无视觉截断或错位。


