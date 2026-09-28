# Proposal: 阶段零动线层级重构与收纳展开交互修复

## Why (为什么做)
1. **动线层级混乱（二级与三级混淆）**：
   - 目前左侧导航栏是大阶段下的“二级小步骤”（第一步：0.1 准备题目；第二步：0.2 网页提问拿答案）；
   - 而右侧的“交付动线”却错误地把左边的两个二级小步骤原样照搬，变成了第 1/2 步和第 2/2 步，造成层级混乱与页面内容重复；
   - 按照面向对象层级：右侧“交付动线”应当下沉为**第三级动线引导**，只负责指引当前二级页面内部的 3 个微操作（出题润色保存），不跨页面。
2. **跨页跳转按钮冗余无效**：
   - 当前右侧动线底部设置了“保存并前往下一集”大按钮；实测由于 `emit('proceed-to-next')` 无参数，接收方条件 `target === 2` 永不成立，实为一个无效空转的冗余死按钮；
   - 实际上每个页面中央都有独立的“保存文件”功能，顶部有“保存备注”，用户保存完毕后若想进入下一个二级小步骤，直接在左侧菜单栏点击切换即可，跨页跳转按钮完全是多余的。
3. **顶栏“收纳概览”点击后无法再展开 Bug 及图标丢失**：
   - 用户点击顶部“收纳概览”按钮后，概览卡片被成功收纳，但再点击时毫无 JS 反馈，彻底无法再展开；
   - 代码排查确认：`web/index.html` 中的 `applyStepOverviewState` 函数（约 7041 行）直接引用未声明的 `btn`、`icon`、`text` 变量，抛出 `ReferenceError: btn is not defined`，导致 JS 中断，`localStorage` 未写入、状态未翻转、事件未分发；
   - 该函数还在 `renderStep0ProbePanel` 和 `renderStep1DiagPanel` 中被无 try/catch 调用，报错会直接吞掉后续的 `lucide.createIcons()`，导致切换阶段时顶栏或面板图标变为空白。

## What Changes (改动了什么)
1. **右侧“交付动线”降维为第三级动线引导卡（遵循共享契约）**：
   - 在 `Step0App.vue` 中，根据当前二级步骤 `currentSubStep`，通过 `stageMeta` 传入各自专属的 3 条 `sopSteps`：
     - **0.1 准备题目**：
       - ① 查看/生成初始题目（保留“重新出题（生成新版）”操作按钮）；
       - ② 在中间编辑区打磨润色（从 60 分打磨到 80 分）；
       - ③ 保存生效（指引用户在中间编辑器点击保存文件与设为采纳）。
     - **0.2 网页提问拿答案**：
       - ① 一键复制提问清单；
       - ② 前往豆包网页版逐题实测（保留“打开豆包网页版”外链按钮）；
       - ③ 贴回回答并保存封版（提供“保存并封版完成阶段零”动作按钮，触发 `handleFinishStage0` 闭环封版）。
2. **条件隐藏主推进按钮（坚决保障阶段 1/2/3 共享逻辑完好）**：
   - `StudioSop.vue` 为阶段 0/1/2/3 共享组件，绝不物理删除主推进按钮模板；
   - 改为在 `step.hideProceed` 或无 `nextLabel` 时**条件隐藏**推进按钮；阶段零 0.1/0.2 标记隐藏，阶段 1/2/3 推进逻辑与通关入口 100% 保持现状不动。
3. **彻底修复顶栏“收纳概览”展开交互 Bug 与渲染链路**：
   - 在 `applyStepOverviewState` 函数中，安全声明并获取 `btn-toggle-step-overview`、`icon-toggle-step-overview`、`text-toggle-step-overview` 三个 DOM 元素；
   - 确保收纳与展开状态正常翻转、按钮文案在“收纳概览”与“展开概览”间正确切换、`localStorage` 正确持久化、`geo-toggle-step-overview` 事件稳定分发，保证后续 `lucide.createIcons()` 顺畅执行。
4. **清理三步制历史残迹与收敛文案**：
   - 清理 `index.html` 中 `STEP0_SUB_LABELS` 的 0.3 残留键值，统一收敛为 0.1 与 0.2 两项；
   - 动线文案规范化，用“提问清单 / 采纳生效”替换历史遗留词汇。

## Capabilities (对外能力)
- 交付专家在操作具体二级步骤时，右侧交付动线纯粹充当本页步骤的作业指引与专属小工具箱，不再出现层级重复。
- 阶段零通关与封版链路（`handleFinishStage0`）清晰可靠，页面切换自由顺畅。
- 顶栏概览支持自由收纳与展开，无任何控制台报错，图标正常渲染。

## Impact (影响范围)
- 前端源码：
  - `GEO/web/step0-src/components/studio/StudioSop.vue`（支持 `hideProceed` 条件隐藏，保留共享主按钮给阶段 1/2/3）
  - `GEO/web/step0-src/Step0App.vue`（依 `currentSubStep` 下发 0.1/0.2 专属 `stageMeta`，0.2 提供封版动作挂载）
  - `GEO/web/index.html`（修复 `applyStepOverviewState` DOM 声明与收敛 `STEP0_SUB_LABELS`）
- 前端构建产物：
  - `GEO/web/assets/step0/step0.js` 与 `geo-step0-island.css`（需经 `npm run build:step0` 重新构建并提交，同步更新 index.html 引用时间戳）
- 验证服务：
  - 真实验证服务位于端口 **8088**（`http://127.0.0.1:8088/` 或 `http://100.83.64.112:8088/`），绝不混淆为 3002。
