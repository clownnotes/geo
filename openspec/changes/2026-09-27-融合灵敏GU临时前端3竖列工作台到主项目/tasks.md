# Tasks: 融合灵敏GU临时前端3竖列工作台到主项目

## 0. 规范与历史归档固化 <!-- id: 0 -->
- [x] 0.1 同步临时前端 8 份阶段归档规范至 `openspec/changes/archive/`，确保历史血统有据可查 <!-- id: 0.1 -->

## 1. 基础脚本与环境准备 <!-- id: 1 -->
- [ ] 1.1 在 `web/` 下新建 `scripts/` 目录并放置 `stamp-build.mjs` 版本戳脚本，支持为产物引用自动追加构建时间戳，内置引用目标存在性断言（未命中时报错中断并 exit 1，杜绝假成功，R8-5） <!-- id: 1.1 -->
- [ ] 1.2 确认主工程根目录 `package.json` 中的 `dev:step0` 和 `build:step0` 脚本可正常调用 <!-- id: 1.2 -->

## 2. 同步 Vue 组件岛源码与配置文件 <!-- id: 2 -->
- [ ] 2.1 同步 `step0-src/` 下全量阶段主页面（`Step0App.vue` ~ `Step6App.vue`），并在 `Step0App.vue` 修正直写后端 API 失败时的 catch 处理，给出明确报错 Toast 提示（杜绝失败依然弹出成功提示，R8-7） <!-- id: 2.1 -->
- [ ] 2.2 同步 `step0-src/` 下各阶段 Composable 状态逻辑与配置（`useStep1.js` ~ `useStep6.js`、`stage1Config.js` ~ `stage6Config.js`）：
  - 修复 `stage5Config.js:170` 读取阶段四答题卡的键名为 `geo_step4_qa_cards_${clientId}`（与写入方严格一致），并将空 catch 改为 `console.warn`（R8-1）；
  - 为 `useStep3.js`、`useStep4.js`、`useStep5.js` 补齐与 `useStep2.js:138-142` 同形的 `watch(isHeaderCollapsed, val => localStorage.setItem(STORAGE_KEY_HEADER, String(val)))` 折叠态持久化写入（R8-2）；
  - 清理或注释 `useStep3.js:34` 中无写入方的 `geo_step2_site_info_` 历史死引用（R8-6） <!-- id: 2.2 -->
- [ ] 2.3 同步 `step0-src/components/` 下所有子组件目录（`studio/`、`qacard/`、`distribute/`、`acceptance/`、`daily/` 等） <!-- id: 2.3 -->
- [ ] 2.4 同步并完善 `step0-src/main.js`，导出全部 8 个 Bridge（`GeoStep0Bridge` ~ `GeoStep6Bridge` 与 `GeoRecurringMonitorBridge`），保留统一接口签名；为阶段零（宿主唯一调用 `refresh` 的阶段）确保 `refresh(opts)` 响应接口与 `Step0App.vue` 的 `defineExpose({ refresh })` 暴露，其余 7 个阶段统一依托宿主守卫重置与 `mount()` 重新挂载注入上下文，避免冗余死代码（R6-4 / R9-1 甲案） <!-- id: 2.4 -->
- [ ] 2.5 同步 `step0-src/vite.config.js` 与 `step0-src/package.json`（在 `rollupOptions.output.assetFileNames` 中显式固定 CSS 产物名为 `geo-step0-island.css`，解除对 `package.json.name` 的隐式耦合，确认 build 包含 stamp-build 脚本调用，R8-8） <!-- id: 2.5 -->

## 3. 同步预构建产物与主壳层更新 <!-- id: 3 -->
- [ ] 3.1 同步预构建产物 `web/assets/step0/step0.js` 与 `web/assets/step0/geo-step0-island.css` <!-- id: 3.1 -->
- [ ] 3.2 同步更新 `web/index.html`：
  - 在 `<head>` 区域 `./assets/step0/step0.js` 之前显式插入 `<link rel="stylesheet" href="./assets/step0/geo-step0-island.css">` 外链样式（R6-1）；
  - 在宿主页面新建 `#panel-step-4-qacard` 面板容器（含 `<div id="step4-app-root"></div>`）；
  - 移除阶段五（`#panel-step-4-distribute`）与阶段六（`#panel-step-5-acceptance`）宿主面板内的旧 DOM 与旧 `<h2>`（改由组件岛根容器渲染）；
  - 阶段 1~3 新建 `legacy-step1~3-container` 隐藏兜底容器包裹老 DOM（含宿主旧 `<h2>` 与 `preview-step-*` 预览容器，确保老 DOM、ID 与回调完好无损，严禁删除，R7-2）；
  - 为宿主 6 个老脚本函数增加空安全守卫，保证老回调执行时控制台零报错（R6-2 / R7-1 / R7-5）：
    * 通用文档渲染函数 `loadMarkdownToElem`：首行增加 `const el = document.getElementById(elemId); if (!el) return;`（彻底解决 `preview-step-5` 节点缺失抛错，R7-1）；
    * `loadProjectRoiEvaluation`：首行增加 `if (!document.getElementById('roi-total-val')) return;`；
    * `loadProjectBenchmarkEvaluation`：首行增加 `if (!document.getElementById('bm-industry-name')) return;`；
    * `loadMonitorDashboardMetrics`：首行增加 `if (!document.getElementById('metric-sov')) return;`；
    * `loadAcceptanceData`：首行增加 `if (!document.getElementById('acceptance-status-badge')) return;`；
    * `loadDistributionLedger`：首行增加首个访问节点守卫 `if (!document.getElementById('dist-channels-ledger-list')) return;`（R7-5）；
  - 注册与订正 `VIEW_META` 视图元数据（R6-3 / R6-5 / R7-3 / R8-4）：
    * 同步订正 01~03 标签文案（`'step-1-diag'`: 01 诊断现状并出具报告；`'step-2-scaffold'`: 02 普林斯顿母盘与素材库；`'step-3-princeton'`: 03 交钥匙官网与三件套）；
    * 注册新 04 视图 `'step-4-qacard'`（`step: 4`，含 `groupLabel: '首次交付'`）；
    * 升位 05 视图 `'step-4-distribute'` (`step: 5`) 与 06 视图 `'step-5-acceptance'` (`step: 6`) 及其标签文案；
    * 补充注册周期复测视图 `'mon-recurring': { group: 'daily', groupLabel: '日常运维', label: '周期复测与商业运营月报' }`，防止 `switchView` 回退到 `overview`；
  - 全量重写 `STEP_TO_VIEW` 映射表（包含 0~6 全阶段映射），核验全部 8 处引用点对齐；
  - 加固 `isDeliveryStepView(viewId)` 函数为显式白名单数组判定（`['step-1-diag', 'step-2-scaffold', 'step-3-princeton', 'step-4-qacard', 'step-4-distribute', 'step-5-acceptance'].includes(viewId)`），显式排除 `step-0-probe`（纠正临时前端正则 `[0-9]` 的过度匹配，R6-7）；
  - 清理 `switchView` 中对 `renderStepXPanel` 的重复调用，统一由 `hydrateView` 驱动（R6-9）；
  - `applyStepOverviewState` 收敛选择器范围为显式枚举 `step0~step6-header-card`，消除通配过度隐藏风险（R6-10）；
  - 更新左侧侧边栏 00~06 阶段与周期复测导航按钮文案与类名（含 01/02/03 文案同步，R6-5）；
  - 挂载各阶段 Vue 根节点 `#step0-app-root` ~ `#step6-app-root` 以及 `#mon-recurring-app-root`；
  - 全量排查并更新主工程硬编码 `switchView('step-4-distribute')`（实测 3 处），确保正文引导跳转到正确的目标阶段；
  - 接入全量阶段 Bridge 挂载管理；在 `enterWizard` 切换项目时，重置所有 `__GEO_STEP0..6_MOUNTED__ = false` 及 `__GEO_RECURRING_MOUNTED__ = false`，并对当前呈现的活跃面板调用对应具名渲染函数注入最新上下文：`renderStep1DiagPanel(true)` ~ `renderMonRecurringPanel(true)` 这 7 个面板传参 `forceRemount=true`，`renderStep0ProbePanel()` 无该参数、依托守卫重置为 `false` 触发重挂载与 `refresh`，彻底杜绝项目切换数据滞后与串流（R6-4 / R9-1 / R9-3） <!-- id: 3.2 -->

## 4. 真实工程联调与构建验收 <!-- id: 4 -->
- [ ] 4.1 在 `web/step0-src` 运行 `npm run build`，验证打包流程无报错且时间戳正常打入 `index.html`，确认未命中引用时脚本能正确告警中断 <!-- id: 4.1 -->
- [ ] 4.2 启动本地服务 `./geo serve --port 8088`，浏览器访问 `http://127.0.0.1:8088` <!-- id: 4.2 -->
- [ ] 4.3 验证阶段 00~06 各工作台标签页点击切换顺畅，3 竖列布局渲染无白屏，中列 Markdown 样式渲染正常（CSS 成功生效，R6-1） <!-- id: 4.3 -->
- [ ] 4.4 验证切换不同项目时，各阶段能否正确获取项目上下文（客户ID、项目名称等）并平稳展示，无数据滞后或串流；阶段五能正常读取阶段四答题卡缓存（R8-1） <!-- id: 4.4 -->
- [ ] 4.5 确认浏览器控制台零报错（无 404、无 undefined/null 引用异常、无 `loadMarkdownToElem` 及老 DOM 缺失导致的 TypeError，R6-2 / R7-1） <!-- id: 4.5 -->
- [ ] 4.6 确认已知预期行为：验证阶段四完成答题卡本地操作后，顶栏进度条与“共 5 步”文案保持不变（符合当前仅前端合流、后端 5 步进度解耦的已知预期，不误判为 Bug） <!-- id: 4.6 -->
