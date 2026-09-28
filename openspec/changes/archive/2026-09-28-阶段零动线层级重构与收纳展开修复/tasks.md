# Tasks: 阶段零动线层级重构与收纳展开交互修复

## 任务拆解与执行清单

- [x] **Task 1: 修复顶栏“收纳概览/展开概览”按钮 JS 报错及双向切换失效 Bug**
  - 文件：`GEO/web/index.html` (约 7041 行 `applyStepOverviewState`)
  - 内容：
    1. 补齐 `btn`、`icon`、`text` 的 `document.getElementById` 获取，彻底解决 `ReferenceError: btn is not defined` 报错；
    2. 收敛约 7084 行 `STEP0_SUB_LABELS` 中的历史三步残留，仅保留 0.1 与 0.2 两项；
  - 验证：在浏览器中连续点击“收纳概览”与“展开概览”，卡片平滑切换收纳与展开，按钮文字和图标正确切换，控制台零报错，切换阶段零/一后面板图标正常渲染为 SVG。

- [x] **Task 2: 改造 `StudioSop.vue` 推进按钮为条件渲染，保障阶段 1/2/3 共享完好**
  - 文件：`GEO/web/step0-src/components/studio/StudioSop.vue`
  - 内容：
    1. 主推进按钮改为 `v-if="!step.hideProceed"` 条件渲染（不判 nextLabel，保障阶段 2/3 默认按钮完好）；
    2. 新增 `expandAll` prop，支持阶段零三级微操作卡片平铺展开；
    3. 当 `step.hideProceed` 为真时，隐藏主推进按钮，在面板底部显示“提示：本小节工作完成后，可直接在左侧菜单切换至下一项”；
    4. 在 `onActionClick` 中处理 `type === 'finishStage0'` 时，触发 `emit('finish-stage0')`；
    5. 绝不修改或破坏阶段 1/2/3 的既有推进逻辑与前进事件；
  - 验证：阶段零 0.1 与 0.2 不再渲染大号跨页跳转按钮；阶段 1/2/3 依然正常显示推进按钮与前进功能。

- [x] **Task 3: 在 `Step0App.vue` 中为 0.1 与 0.2 分别挂载三级动线元数据**
  - 文件：`GEO/web/step0-src/Step0App.vue`
  - 内容：
    1. 定义 `STAGE0_SUB1_META`（AI 出题查看、中间区打磨、保存采纳）与 `STAGE0_SUB2_META`（一键复制、豆包实测提问、贴回回答并封版）；
    2. 根据响应式变量 `currentSubStep.value` 计算 `currentStageMeta`，下发给 `<StudioSop :stage-meta="currentStageMeta" :expand-all="true" ... />`；
    3. 清理已失效的死代码 `proceedToSub2` 与无参的 `handleProceedToNext`；确保 `@finish-stage0` 正确调用 `handleFinishStage0` 闭环封版；
  - 验证：0.1 页面右侧动线显示 3 个微操作（出题、打磨、保存采纳）；0.2 页面右侧动线显示 3 个微操作（复制、实测、贴回并封版），点击“重新出题”弹出新版草稿，点击封版正确持久化。

- [x] **Task 4: 前端编译打包与冒烟测试验证**
  - 内容：
    1. 执行 `npm run build:step0`（重新构建 Vue3 产物 `web/assets/step0/step0.js` 与 `geo-step0-island.css`，自动注入 `web/index.html` 资源版本号）；
    2. 执行 `bash scripts/smoke_step0.sh`，确保 4/4 步冒烟检查全部亮绿通过；
  - 验证：构建产物生成成功，无语法错误与打包异常。

- [x] **Task 5: 真机端口 8088 端到端全链路验收**
  - 访问地址：`http://127.0.0.1:8088/`（本地）或 `http://100.83.64.112:8088/`（NE1 服务器）；
  - 验收项目：
    1. 顶栏“收纳概览”点击后卡片收起，按钮变为“展开概览”；再次点击卡片展开，按钮恢复“收纳概览”；
    2. 0.1 准备题目页面，右侧动线呈现三级微操作，无多余跳转大按钮；点击“重新出题”生成新版；
    3. 左侧菜单点击切换到 0.2 网页提问，右侧动线平滑切换为 0.2 专属三级微操作；
    4. 0.2 页面可正常打开豆包外链，点击“保存并封版完成阶段零”后数据正常落盘；
    5. 回归检查阶段一、阶段二、阶段三，确认主推进按钮完好存在，业务流程未受任何负面影响。
