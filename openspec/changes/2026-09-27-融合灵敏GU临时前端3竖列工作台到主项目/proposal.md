# Proposal: 融合灵敏GU临时前端3竖列工作台到主项目

## Why (为什么做)
- **痛点背景**：原有的线上前端页面以长表单、平铺和弹窗为主，视觉体验与交互层级不够清晰，代运营操作繁琐。更重要的是，现有交付体系缺少专门针对 AI 向量搜索召回的“GEO 答题卡与向量问答库”独立交付物环节。
- **验证成果**：师弟在临时前端工作区（`/Volumes/联想120/临时前端/邻里GEO 的临时前端`）中，完成了全阶段（00 到 06 及周期复测）的「3 竖列专业工作台」样式与交互打磨，**全新插入了「04 GEO 答题卡与向量库」阶段**，并将原分发排版升位为阶段 05、商业验收升位为阶段 06。
- **本轮目标**：采用稳健的「方案 A（先前端样式与产物合流，再逐步对接真实 API）」，把临时前端的高颜值样式与 Vue 3 组件岛整体迁移并融合到当前的主项目 `GEO` 中，确保在真实工程（端口 `:8088`）下流畅运行、零报错。

---

## What Changes (改动了什么)
1. **交付阶段拓扑结构升级（新增阶段四 + 阶段编号位移）**：
   - 主工程原本只有阶段 0~5。本轮升级在阶段 3 与原阶段 4 之间**全新插入「阶段四：GEO 答题卡与向量问答库 (`step-4-qacard`)」**。
   - 原阶段四（草稿改写发布）升位为 **阶段五（GEO 文章选题撰写与矩阵分发）**，宿主容器沿用历史 ID `#panel-step-4-distribute`。
   - 原阶段五（首轮监测验收）升位为 **阶段六（首次交付与资产交接单）**，宿主容器沿用历史 ID `#panel-step-5-acceptance`。
   - 全新增加 **周期复测与商业运营月报** 独立工作台，宿主容器 ID 为 `#panel-mon-recurring`。
2. **组件岛源码全量合流**：
   - 将临时前端 `step0-src` 迁移至主项目 `web/step0-src/`。
   - 涵盖全部阶段主入口：`Step0App.vue` ~ `Step6App.vue`。
   - 涵盖全部阶段状态逻辑：`useStep1.js` ~ `useStep6.js`、`stage1Config.js` ~ `stage6Config.js`（主工程已有 `useStep0.js`）。
   - 涵盖通用与业务组件子目录：`components/studio/`、`components/qacard/`、`components/distribute/`、`components/acceptance/`、`components/daily/` 等。
3. **主壳层页面与侧边栏映射升级**：
   - 同步升级 `web/index.html`，更新左侧导航栏（00 现状摸底、01 商业诊断、02 普林斯顿母盘、03 交钥匙官网、04 GEO答题卡、05 矩阵分发、06 商业验收、周期复测）。
   - **在宿主页面全新创建 `#panel-step-4-qacard` 面板容器**，并挂载各阶段的根节点容器（`#step0-app-root` ~ `#step6-app-root` 及 `#mon-recurring-app-root`），在切换标签时触发对应 Bridge 实例的挂载与数据刷新。
   - 阶段 1~3 保留 `legacy-stepX-container` 作为安全兜底容器；阶段 0/4/5/6 与运营老 DOM 随 3 竖列改造整体替换，确保老脚本回调不报错。
4. **构建流水线与防缓存版本戳**：
   - 新建 `web/scripts/` 目录并引入 `stamp-build.mjs` 脚本，在 `npm run build:step0` 完成后自动在 `index.html` 的产物链接追加构建时间戳（如 `?v=20260927...`），防止浏览器（尤其是 Safari）强缓存导致样式不刷新。
   - 同步更新预构建产物 `web/assets/step0/step0.js` 与 `web/assets/step0/geo-step0-island.css`。
5. **数据绑定策略（融合双轨模式）**：
   - 优先通过 Bridge 接收后端 `/api/projects/:id` 注入的真实项目上下文（项目名称、行业、定位客群等）。
   - 针对阶段 1~6 尚未接通真实后端 API 的写操作（如打磨保存、前进步骤、备注记录等），采用 `localStorage` 进行优雅降级本地持久化，保证交互闭环流畅、零报错。

---

## 阶段编号位移与路由兼容性设计 (Routing Compatibility)
1. **阶段演进对照表**：
   - `00`：现状摸底 (`step-0-probe`) —— 保持不变
   - `01`：商业诊断 (`step-1-diag`) —— 保持不变
   - `02`：普林斯顿母盘 (`step-2-scaffold`) —— 保持不变
   - `03`：交钥匙官网 (`step-3-princeton`) —— 保持不变
   - **`04`【全新插入】**：GEO 答题卡与向量库 (`step-4-qacard`) —— **主工程需新建容器 `#panel-step-4-qacard`**
   - **`05`【原 04 升位】**：矩阵分发与链接检查 (`step-4-distribute`) —— 沿用历史面板 ID，根节点为 `#step5-app-root`
   - **`06`【原 05 升位】**：首次交付与资产交接 (`step-5-acceptance`) —— 沿用历史面板 ID，根节点为 `#step6-app-root`
   - **`运营`【全新独立】**：周期复测与商业月报 (`mon-recurring`) —— 新建面板容器 `#panel-mon-recurring`
2. **Hash 路由与既有深链兼容策略**：
   - 宿主 `web/index.html` 采用基于 hash 的单页视图路由（`window.location.hash` 与 `VIEW_META`）。
   - 既有深链中访问 `#step-4-distribute` 依然无缝打开分发排版工作台，访问 `#step-5-acceptance` 依然打开商业验收工作台，历史书签完全不失效、不产生 404 断链。
   - 宿主主流程正文引导中 3 处硬编码 `switchView('step-4-distribute')` 全量排查核对，按业务动线顺序正确导向新阶段。

---

## 规范豁免声明 (Exemption for AGENTS.md §8.2)
- **豁免条款**：暂时豁免 `AGENTS.md` §8.2「本地 JSON 真实物理落盘（严禁纯内存假交互）」中关于写操作必须立即物理落盘到后端 JSON 的要求。
- **豁免范围与理由**：本变更核心目标为**过渡期 3 竖列工作台前端样式与交互规范合流**。阶段 1~6 的前端内部打磨草稿、步骤进度与备注保存采用 `localStorage` 进行本地持久化降级，属于过渡期手段，**后续将在真实后端对应 API 就绪后逐阶段替换为真实物理落盘**。
- **产品负责人确认状态**：[已由师弟（产品经理）在方案探讨中选定融合双轨模式，特此确认豁免]

---

## Capabilities (对外能力)
1. **统一的 3 竖列工业级工作台体验**：
   - **左列**：交付物文件树与素材资产导航；
   - **中列**：高保真 Markdown 预览与实时打磨编辑器；
   - **右列**：麦肯锡商业思考模型抽屉、标准化 SOP 指引、质量门禁与放行按钮。
2. **全流程血统溯源与版本合流**：
   - 支持阶段零采纳标注血统印章（`[溯源血统]`），下游报告与母盘自动继承底牌版本。
   - 阶段二母盘版本（v1.0 -> v1.1）差异对比卡与一键合流交互。
3. **周期复测与日常运营独立看板**：
   - 具备专属的周期复测与商业运营月报工作台，直观展示多轮复测趋势与战果统计。

---

## Impact (受影响的部分)
- `web/step0-src/`：全面覆盖升级为最新的多阶段 Vue 3 组件工程，包含 `web/step0-src/package.json`（build 追加 stamp 脚本）与 `web/step0-src/vite.config.js`。
- `web/assets/step0/`：产物刷新，包含 `step0.js` 与 `geo-step0-island.css`，提供全阶段 Bridge 导出（`GeoStep0Bridge` ~ `GeoStep6Bridge` 与 `GeoRecurringMonitorBridge`）。
- `web/index.html`：侧边栏标题、容器结构与 Bridge 挂载监听函数更新。
- `web/scripts/stamp-build.mjs`：新建目录并增加构建加戳 Node 工具脚本。
- `openspec/changes/archive/`：新增同步 8 份临时前端阶段归档规范。
- **后端服务**：无需修改 Python 后端代码，现存接口完全兼容。
