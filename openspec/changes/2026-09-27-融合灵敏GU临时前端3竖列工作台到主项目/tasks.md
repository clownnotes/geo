# Tasks: 融合灵敏GU临时前端3竖列工作台到主项目

## 0. 规范与历史归档固化 <!-- id: 0 -->
- [x] 0.1 同步临时前端 8 份阶段归档规范至 `openspec/changes/archive/`，确保历史血统有据可查 <!-- id: 0.1 -->

## 1. 基础脚本与环境准备 <!-- id: 1 -->
- [ ] 1.1 在 `web/` 下新建 `scripts/` 目录并放置 `stamp-build.mjs` 版本戳脚本，支持为产物引用自动追加构建时间戳 <!-- id: 1.1 -->
- [ ] 1.2 确认主工程根目录 `package.json` 中的 `dev:step0` 和 `build:step0` 脚本可正常调用 <!-- id: 1.2 -->

## 2. 同步 Vue 组件岛源码与配置文件 <!-- id: 2 -->
- [ ] 2.1 同步 `step0-src/` 下全量阶段主页面（`Step0App.vue` ~ `Step6App.vue`） <!-- id: 2.1 -->
- [ ] 2.2 同步 `step0-src/` 下各阶段 Composable 状态逻辑与配置（`useStep1.js` ~ `useStep6.js`、`stage1Config.js` ~ `stage6Config.js`） <!-- id: 2.2 -->
- [ ] 2.3 同步 `step0-src/components/` 下所有子组件目录（`studio/`、`qacard/`、`distribute/`、`acceptance/`、`daily/` 等） <!-- id: 2.3 -->
- [ ] 2.4 同步并完善 `step0-src/main.js`，导出 `GeoStep0Bridge` ~ `GeoStep6Bridge` 与 `GeoRecurringMonitorBridge`，为全部 Bridge 补齐标准 `refresh(opts)` 响应接口，并确保各 `StepXApp.vue` 均通过 `defineExpose({ refresh })` 暴露刷新入口 <!-- id: 2.4 -->
- [ ] 2.5 同步 `step0-src/vite.config.js` 与 `step0-src/package.json`（确认 build 包含 stamp-build 脚本调用） <!-- id: 2.5 -->

## 3. 同步预构建产物与主壳层更新 <!-- id: 3 -->
- [ ] 3.1 同步预构建产物 `web/assets/step0/step0.js` 与 `web/assets/step0/geo-step0-island.css` <!-- id: 3.1 -->
- [ ] 3.2 同步更新 `web/index.html`：
  - 在宿主页面新建 `#panel-step-4-qacard` 面板容器（含 `<div id="step4-app-root"></div>`）并在 `VIEW_META` 注册 `step-4-qacard` 视图；
  - 更新左侧侧边栏 00~06 阶段与周期复测导航按钮；
  - 挂载各阶段 Vue 根节点 `#step0-app-root` ~ `#step6-app-root` 以及 `#mon-recurring-app-root`；
  - 保留阶段 1~3 的 `legacy-stepX-container` 隐藏兜底容器；
  - 全量排查并更新主工程硬编码 `switchView('step-4-distribute')`（实测 3 处），确保正文引导跳转到正确的目标阶段；
  - 接入全量阶段 Bridge 挂载管理；在 `enterWizard` 切换项目时，重置所有 `__GEO_STEPX_MOUNTED__ = false` 并对活跃面板调用 `renderStepXPanel(true)`，彻底杜绝项目切换数据滞后 <!-- id: 3.2 -->

## 4. 真实工程联调与构建验收 <!-- id: 4 -->
- [ ] 4.1 在 `web/step0-src` 运行 `npm run build`，验证打包流程无报错且时间戳正常打入 `index.html` <!-- id: 4.1 -->
- [ ] 4.2 启动本地服务 `./geo serve --port 8088`，浏览器访问 `http://127.0.0.1:8088` <!-- id: 4.2 -->
- [ ] 4.3 验证阶段 00~06 各工作台标签页点击切换顺畅，3 竖列布局渲染无白屏 <!-- id: 4.3 -->
- [ ] 4.4 验证切换不同项目时，各阶段能否正确获取项目上下文（客户ID、项目名称等）并平稳展示，无数据滞后或串流 <!-- id: 4.4 -->
- [ ] 4.5 确认浏览器控制台零报错（无 404、无 undefined 引用异常） <!-- id: 4.5 -->
