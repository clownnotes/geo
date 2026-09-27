# 开发任务清单 · 首次交付验收与日常运营复测工作台

> **变更ID**：`2026-09-27-首次交付验收与日常运营复测工作台`  
> **开发模式**：遵循 OpenSpec 标准多模型对抗开发流程。**已完成全流程编码与跨端实测验证**。

---

## 任务拆解与验收清单

- [x] **1. 配置字典与验收标准定义 (`step0-src/stage6Config.js`)**
  - [x] 1.1 依据老赵哥 SOP S11.1 定义七项验收合格指标字典（底座、40问、40答题卡、官网、发布外链、承接入口、交接归档）；
  - [x] 1.2 依据《主体信息统一口径卡》第 6 节预置核心 3 问（公司是做什么的、产品怎么样、官网与联系方式）与标准预期定位；
  - [x] 1.3 定义交付结项单模板文案与双方签字声明规范；
  - [x] 1.4 定义阶段六 SOP 动线说明与麦肯锡交付手册字典。

- [x] **2. 状态驱动与本地持久化 Hook (`step0-src/useStep6.js`)**
  - [x] 2.1 封装前序阶段（01~05）产出资产的自动统计与状态聚合逻辑；
  - [x] 2.2 封装首轮 3 问真机回填录入、改口比对判定与印章打标逻辑；
  - [x] 2.3 封装结项单签署人、日期、备注的本地保存与重置逻辑；
  - [x] 2.4 封装一键导出/打印结案单、生成资产移交清单 Markdown 的工具函数。

- [x] **3. 左栏 · 七项验收资产盘点组件 (`step0-src/components/acceptance/AssetChecklist.vue`)**
  - [x] 3.1 渲染七项指标对照卡片列表（包含合格标准、达标指示、产出物数量）；
  - [x] 3.2 渲染外链存活率小结（联动阶段五台账数据）；
  - [x] 3.3 提供快速跳转查看前序产出物的动作入口。

- [x] **4. 中栏 · 首轮 3 问改口真机抽测组件 (`step0-src/components/acceptance/FirstProbeVerifier.vue`)**
  - [x] 4.1 头部渲染轻量抽测指引（解释为什么刚做完只需要测 3 问）；
  - [x] 4.2 渲染 3 问卡片：一键复制问句、S0 摸底错误回答回顾、真机最新回答输入框；
  - [x] 4.3 贴入回答后自动高亮关键词并展示「已纠偏改口」绿色印章徽章；
  - [x] 4.4 底部展示 3 问全部达标状态统计。

- [x] **5. 右栏 · 首期工程移交与结项验收单组件 (`step0-src/components/acceptance/SignoffDocket.vue`)**
  - [x] 5.1 渲染高质感公文凭证式验收单（项目基本信息、移交资产清单摘要、抽测达标结论）；
  - [x] 5.2 渲染双方交接确认区（交付负责人、客户接收人、签署时间）；
  - [x] 5.3 【一键出具大屏版 HTML】与【打印/导出纸质签字单】主操作按钮。

- [x] **6. 页面总装集成与挂载 (`Step6App.vue` & `main.js` & `index.html`)**
  - [x] 6.1 编写 `Step6App.vue` 总装三竖列交付组件与顶部 `StageHeader` / `MckinseyDrawer`；
  - [x] 6.2 在 `step0-src/main.js` 中封装并导出 `GeoStep6Bridge`（提供 mount, unmount, refresh 等标准接口）；
  - [x] 6.3 在 `index.html` 的 `panel-step-5-acceptance` 容器中接入 Vue 3 组件岛（重命名标题为「06 首次交付与资产交接单」，内建 `#step6-app-root` 挂载点，替代原有混杂 DOM）；
  - [x] 6.4 更新 `VIEW_META['step-5-acceptance']` 的 label 为「06 首次交付与资产交接单」，并在 `hydrateView` 中注入 `renderStep6AcceptancePanel()`。

- [x] **7. 日常运维 · 周期复测与商业运营月报工作台 (`RecurringMonitorStudio.vue`)**
  - [x] 7.1 在 `index.html` 的 `VIEW_META` 字典中显式注册 `'mon-recurring': { group: 'daily', groupLabel: '日常运维', label: '周期复测与商业运营月报' }`，防止被 `switchView` 首行兜底回 `overview`；
  - [x] 7.2 在 `index.html` 的 `sidebar-group-daily` 中新增导航按钮 `<button id="nav-mon-recurring" onclick="switchView('mon-recurring')">`；
  - [x] 7.3 新增主面板容器 `<div id="panel-mon-recurring" class="workspace-panel hidden space-y-6">`，并在 `hydrateView` 中添加 `renderMonRecurringPanel()` 水合分支；
  - [x] 7.4 将原阶段六的老板商业 ROI 看板、年化财务价值折算、续约预测看板迁移至日常运维专属组件；
  - [x] 7.5 增加 40 问高意图尺子轮巡回贴区与 SOP S9 五级信号判定逻辑。

- [x] **8. 跨端验证与交付检查**
  - [x] 8.1 在 2019 PRO Safari（端口 5188）上验证首次交付 3 竖列自适应响应；
  - [x] 8.2 验证点击侧边栏「日常运维 -> 周期复测与商业运营月报」能够平滑切换到 `panel-mon-recurring`，且不会被 `switchView` 兜底回 `overview`；
  - [x] 8.3 验证首轮 3 问提问复制、回答粘贴、改口比对与打印凭单功能；
  - [x] 8.4 验证日常运维周期复测工作台的数据展示与周报导出；
  - [x] 8.5 检查是否 100% 遵守 0 Emoji 与五年级小学生易懂文案规范。
