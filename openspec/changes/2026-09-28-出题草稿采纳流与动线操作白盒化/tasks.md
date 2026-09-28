# Tasks: 出题草稿采纳流与动线操作白盒化

## 1. 资源管理器（左栏）跨阶段共用与状态透传升级
- [x] 1.1 拓宽四阶段侧栏容器宽度：在 `GEO/web/step0-src/components/studio/StudioFileTree.vue` 中将 `lg:w-60`（240px）拓宽为 `lg:w-72`（288px），保障所有阶段长文件名展示不被截断。
- [x] 1.2 新增防污染状态开关与主色紫二元徽章：
  - 在 `StudioFileTree.vue` 中新增 prop `showStatusBadge: { type: Boolean, default: false }`；
  - 仅在 `showStatusBadge === true` 时渲染徽章：草稿文件渲染灰色 `[草稿]`（`bg-slate-100 text-slate-400 border border-slate-200`），生效文件渲染高亮主色紫 `[已采纳 QA-V(N)]`（`bg-[#7c5bf5]/15 text-[#7c5bf5] border border-[#7c5bf5]/30`）；
  - 在 `Step0App.vue` 中引用 `<StudioFileTree>` 时显式传入 `:show-status-badge="true"`，确保阶段 1/2/3 零污染。

## 2. SOP 交付动线防误触与动作事件打通（【🔴 线上 P0 热修】优先排产）
- [x] 2.1 【🔴 现网 P0 热修】阻断平铺模式误触跨页跳页与崩溃，消除假可点手型：
  - 在 `GEO/web/step0-src/components/studio/StudioSop.vue` 的 `onGotoStep` 头部增加防护 `if (props.expandAll) return;`，彻底阻断用户点击卡片 2 静默跳往 0.2 以及点击卡片 3 导致 `subMetaMap[3]` 抛出 `TypeError` 崩溃；
  - 在卡片头部将手型样式根据 `props.expandAll` 进行条件化处理：`:class="expandAll ? 'cursor-default' : 'cursor-pointer'"`，避免视觉承诺可点但行为不可点的落差。
- [x] 2.2 扩展动作分发并彻底清理悬空事件：
  - 在 `StudioSop.vue` 的 `onActionClick` 中支持派发 `save-file`（对应 `saveCurrentFile`）和 `adopt-current-file`（对应 `adoptCurrentFile`）；
  - 在 `defineEmits` 中声明 `save-file` 和 `adopt-current-file`，彻底清理废弃悬空的 `proceed-to-next` 声明及其在 `onProceedClick` 中的发射点。

## 3. 阶段零出题打磨动线挂载动作按钮与事件绑定
- [x] 3.1 动线微步骤文案改写与动作按钮化（保持 0.2 动线不动）：
  - 在 `GEO/web/step0-src/Step0App.vue` 的 `STAGE0_SUB1_META` 中，为第 2 步增加【保存当前润色修改】实体按钮（`saveCurrentFile`）；
  - 同步改写第 3 步 `name` 为『3. 采纳为生效底牌』、`desc` 改写为『题目打磨满意后，点击下方转正为正式生效版本（自动生成 QA-V2），作为后续实测基线。』，并挂载【采纳为生效底牌 (转正为新版)】实体按钮（`adoptCurrentFile`）；
  - 保持 0.2 提问动线 `STAGE0_SUB2_META` 现状不动，完整保留第 3 步的【完成阶段零并封版】按钮（`finishStage0`）。
- [x] 3.2 页面级事件闭环绑定：在 `Step0App.vue` 的 `<StudioSop>` 组件上绑定 `@save-file="handleSaveActiveFile"` 与 `@adopt-current-file="() => handleAdoptFile(activeFileName)"`，打通存盘与采纳转正闭环。


## 4. 前端构建与 NE1 8088 真机环境验证
- [x] 4.1 编译打包阶段零前端产物：在仓库根目录 `GEO/` 执行 `npm run build:step0`，生成真实产物 `web/assets/step0/step0.js` 与 `web/assets/step0/geo-step0-island.css`，由 `stamp-build.mjs` 自动更新版本戳。
- [x] 4.2 同步产物至 NE1 服务器并在 8088 端口端到端真机验收：
  - 验证点击“重新出题”后，生成草稿文件，左侧显示灰色 `[草稿]` 标签；
  - 验证点击微步骤 2【保存当前润色修改】，成功存盘并弹出保存成功提示；
  - 验证点击微步骤 3【采纳为生效底牌】，草稿瞬间转正为 QA-V2，左侧高亮显示紫色 `[已采纳 QA-V2]` 徽章，原 QA-V1 自动让位变为草稿；
  - 验证阶段 1/2/3 文件列表干净纯粹，无任何多余草稿徽章污染；
  - 验证在平铺卡片上任意点击卡片头部，不再发生跨页乱跳或报错。
