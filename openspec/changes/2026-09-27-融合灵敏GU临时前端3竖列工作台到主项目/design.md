# Design: 融合灵敏GU临时前端3竖列工作台到主项目

## 1. 架构总览：组件岛架构与双轨运行机制

本项目采用轻量级的 **Vue 3 组件岛 (Island Architecture)** 模式嵌入宿主页面 `index.html`。
宿主页面负责侧边栏路由切换与顶层状态（当前选中的项目上下文），各阶段核心工作区作为独立的 Vue 3 实例挂载到专用的 DOM 容器节点。

```
                    ┌─────────────────────────────────────────────────────┐
                    │            宿主页面 (web/index.html)                 │
                    │  • 侧边栏导航 (00~06 阶段与周期运营)                │
                    │  • 真实项目切换监听 (POST/GET /api/projects/:id)     │
                    └───────────┬─────────────────────────┬───────────────┘
                                │ 派发 projectData        │
                                ▼                         ▼
    ┌────────────────────────────────────────┐ ┌────────────────────────────────────────┐
    │     阶段 0 摸底探测工作台               │ │     阶段 1~6 业务阶段工作台            │
    │  • 挂载节点: #step0-app-root           │ │  • 挂载节点: #step1-app-root ~ #step6...│
    │  • 驱动: GeoStep0Bridge                │ │  • 驱动: GeoStep1Bridge ~ GeoStep6...  │
    │  • 数据链: 直连 /api/projects/:id/probe│ │  • 数据链: 融合双轨模式 (真上下文+本地持久化) │
    └────────────────────────────────────────┘ └────────────────────────────────────────┘
```

---

## 2. 容器挂载与 Bridge 接口契约

宿主页面通过全局变量 `window.__GEO_STEP{N}__` 调用各阶段 Bridge。每个 Bridge 必须实现统一的生命周期方法：

| 阶段编号 | 阶段名称 | 宿主面板容器 ID | Vue 挂载根节点 ID | 全局 Bridge 变量名 (导出类名) |
| :--- | :--- | :--- | :--- | :--- |
| **00** | 现状摸底 (探测) | `#panel-step-0-probe` | `#step0-app-root` | `window.__GEO_STEP0__` (`GeoStep0Bridge`) |
| **01** | 诊断现状并出具报告 | `#panel-step-1-diag` *(注0.2)* | `#step1-app-root` | `window.__GEO_STEP1__` (`GeoStep1Bridge`) |
| **02** | 普林斯顿母盘与素材库 | `#panel-step-2-scaffold` *(注0.2)* | `#step2-app-root` | `window.__GEO_STEP2__` (`GeoStep2Bridge`) |
| **03** | 交钥匙官网与三件套 | `#panel-step-3-princeton` *(注0.2)*| `#step3-app-root` | `window.__GEO_STEP3__` (`GeoStep3Bridge`) |
| **04** | GEO 答题卡与向量库 | `#panel-step-4-qacard` *(注0.1)* | `#step4-app-root` | `window.__GEO_STEP4__` (`GeoStep4Bridge`) |
| **05** | 矩阵分发与链接检查 | `#panel-step-4-distribute` *(注1)* | `#step5-app-root` | `window.__GEO_STEP5__` (`GeoStep5Bridge`) |
| **06** | 首次交付与资产交接 | `#panel-step-5-acceptance` *(注1)* | `#step6-app-root` | `window.__GEO_STEP6__` (`GeoStep6Bridge`) |
| **运营** | 周期复测与商业月报 | `#panel-mon-recurring` *(注0.2)* | `#mon-recurring-app-root` *(注2)* | `window.__GEO_RECURRING__` (`GeoRecurringMonitorBridge`) |

> **注0（主工程需新建容器与路由元数据重写规范）**：  
> 1. **新建容器与旧标题移除（R6-6）**：宿主面板容器 `#panel-step-4-qacard`（对应全新 04 GEO 答题卡与向量库）在主工程基线中**不存在**，必须在 `web/index.html` 中新建该容器，内部放置 `<div id="step4-app-root"></div>`；同时，各阶段宿主面板内原有的旧 `<h2>` 整体移除，统一由组件岛内部的 `StageHeader.vue` 规范渲染，宿主面板内仅保留 Vue 根节点容器，杜绝重复渲染双标题；  
> 2. **`VIEW_META` 全量重构与文案订正（R6-3 / R6-5）**：  
>    - 订正 01~03 标签文案并同步对齐侧边栏按钮：  
>      - `'step-1-diag'`: label 改为 `'01 诊断现状并出具报告'`（主工程原为 `'01 商业诊断与转化建议书'`）；  
>      - `'step-2-scaffold'`: label 改为 `'02 普林斯顿母盘与素材库'`（主工程原为 `'02 普林斯顿 9 因子素材博文库'`）；  
>      - `'step-3-princeton'`: label 改为 `'03 交钥匙官网与三件套'`（主工程原为 `'03 普林斯顿 9 因子语料'`）；  
>    - 注册新 04 视图：`'step-4-qacard': { step: 4, label: '04 GEO 答题卡与向量问答库', group: 'delivery', groupLabel: '首次交付' }`；  
>    - 升位 05 视图：`'step-4-distribute': { step: 5, label: '05 矩阵分发与链接检查', group: 'delivery', groupLabel: '首次交付' }`（`step: 4 -> 5`）；  
>    - 升位 06 视图：`'step-5-acceptance': { step: 6, label: '06 首次交付与资产交接单', group: 'delivery', groupLabel: '首次交付' }`（`step: 5 -> 6`）；  
>    - 补充注册周期复测视图（R6-3）：`'mon-recurring': { group: 'daily', groupLabel: '日常运维', label: '周期复测与商业运营月报' }`，防止 `switchView` 静默回退到 `overview`；  
> 3. **`STEP_TO_VIEW` 路由表全量重写**：  
>    ```javascript
>    const STEP_TO_VIEW = {
>      0: 'step-0-probe',
>      1: 'step-1-diag',
>      2: 'step-2-scaffold',
>      3: 'step-3-princeton',
>      4: 'step-4-qacard',
>      5: 'step-4-distribute',
>      6: 'step-5-acceptance',
>    };
>    ```  
> 4. **引用点与白名单全量对齐（R6-7 / R6-9 / R6-10）**：  
>    - 核对并确保主工程内依赖 `STEP_TO_VIEW` 的全部 8 处引用对齐；  
>    - 加固 `isDeliveryStepView(viewId)` 函数为显式白名单数组判定：`['step-1-diag', 'step-2-scaffold', 'step-3-princeton', 'step-4-qacard', 'step-4-distribute', 'step-5-acceptance'].includes(viewId)`。业务上显式**排除 `step-0-probe`**（阶段零本身是探针，无需探针拦截；主工程原正则排除正确，临时前端 `[0-9]` 属于过度匹配 Bug，本轮规范定为修正临时前端为白名单）；  
>    - 清理 `switchView` 中对 `renderStepXPanel` 的重复调用，统一由 `hydrateView` 驱动（R6-9）；  
>    - `applyStepOverviewState` 收敛选择器范围为显式枚举 `step0~step6-header-card`，消除通配过度隐藏风险（R6-10）；  
> 5. **产物落盘前缀防碰撞规范**：阶段四后续真实物理落盘前缀规范定为 `04a_qacard_`，后续后端演进必须采用精确前缀匹配（如 `f.startswith(prefix)` 且最长前缀优先），实测 `"04_" in "04a_qacard_..."` 为 `False`，绝不干扰既有 4 个项目的 `04_` 分发产物判定；  
> 6. **兜底容器明确（R6-8）**：阶段 1~3 新建 `legacy-step1~3-container` 隐藏兜底容器包裹老 DOM，以便在必要时降级回看。  
> **注1（历史编号保留铁律）**：宿主容器 `#panel-step-4-distribute`（对应 05 矩阵分发）与 `#panel-step-5-acceptance`（对应 06 商业验收）系主工程历史遗留命名，其内部根节点已准确对齐为 `#step5-app-root` 与 `#step6-app-root`。此为既有规范事实，**严禁在 apply 阶段擅自修改宿主面板 ID**。  
> **注2（根节点与类名修正）**：周期运营挂载根节点规范订正为实测值 `#mon-recurring-app-root`，Bridge 导出类名规范订正为 `GeoRecurringMonitorBridge`。

### 2.1 宿主老脚本兼容与空节点安全守卫（乙案：彻底保证零报错，R6-2）
阶段五（原04分发）与阶段六（原05验收）老 DOM 全部替换为组件岛独立根容器（仅保留 `<div id="stepX-app-root">`），但主工程 `enterWizard()` 会调用 `loadStepPreviews()`，其内部的 5 个老数据加载函数直接操作了被移除的老 DOM 节点。为兑现「控制台 0 报错」承诺，在 apply 阶段必须为宿主这 5 个老函数补齐空节点安全守卫：
- `loadProjectRoiEvaluation`：首行增加 `if (!document.getElementById('roi-total-val')) return;`；
- `loadProjectBenchmarkEvaluation`：首行增加 `if (!document.getElementById('bm-industry-name')) return;`；
- `loadMonitorDashboardMetrics`：首行增加 `if (!document.getElementById('metric-sov')) return;`；
- `loadAcceptanceData`：首行增加 `if (!document.getElementById('acceptance-status-badge')) return;`；
- `loadDistributionLedger`：首行增加 `if (!document.getElementById('toutiao-pack-status')) return;`。

### Bridge 标准接口定义与参数透传约定
```javascript
export const GeoStepXBridge = {
  // 挂载组件岛到宿主 DOM（内部将 bridge 参数原样注入 Vue 组件 Props: { bridge }）
  // 宿主侧调用传参形状: mount(containerEl, { projectData, subStep })
  mount(el, bridge) {},
  // 卸载组件岛并清理全局监听
  unmount() {},
  // 响应外部项目切换，更新响应式上下文
  refresh(projectData) {},
  // （可选）切换阶段内部子步进
  setSubStep(stepNum) {},
};
```

---

## 3. 数据层：融合双轨持久化与项目切换刷新保障规范

为确保迁移后真实工程立即可用且不报错，阶段 1~6 统一遵循**双轨融合模型与刷新双保险机制**：

1. **真实上下文解析 (Read-only)**：
   - 提取 `projectData.client_id || projectData.id` 获取当前客户 ID；
   - 提取 `projectData.name`、`projectData.category`、`projectData.target_audience` 获取品牌、行业与受众；
   - 模板自动将上述真实字段动态拼装进各阶段初始文件（如诊断报告、官网配置、问答卡、分发文案）。

2. **本地降级持久化 (Read/Write)**：
   - 本地状态键名统一采用客户端命名空间隔离：`geo_step{N}_state_{clientId}`；
   - 用户在工作台内部修改文件、勾选门禁、前进步骤或填写备注时，自动写入 `localStorage`；
   - 若本地无缓存，自动生成带有项目真实字段的基线模板文件。

3. **项目切换刷新双保险机制（彻底杜绝上下文滞后，R6-4）**：
   - **Bridge 侧全量补齐 `refresh(projectData)`（8/8 完整覆盖）**：实测临时前端基线中仅阶段 0 和阶段 5 实现了 `refresh`，组件侧缺乏 `defineExpose`（现状 2/8）。在 apply 阶段必须在 `main.js` 中为全部 Bridge（`GeoStep0`~`GeoStep6` 及 `GeoRecurringMonitorBridge`）统一实现 `refresh(opts)`，并在对应 8 个 Vue 组件根实例上通过 `defineExpose({ refresh })` 暴露方法；
   - **宿主侧重置守卫标志位**：宿主 `index.html` 在 `enterWizard` 切换项目时，统一将所有 `window.__GEO_STEP0..6_MOUNTED__` 以及 `window.__GEO_RECURRING_MOUNTED__` 标志位重置为 `false`，并对当前已呈现的活跃视图执行带 `forceRemount=true` 的渲染调用；用户后续切换到其他阶段面板时，会因为守卫为 `false` 而自动以最新项目数据执行 `mount()`，彻底根除项目切换后的数据串流问题。

---

## 4. 构建与发布流水线架构

```
web/step0-src/
   ├── vite.config.js       (配置 iife 格式打包为单个 step0.js)
   └── package.json         ("build": "vite build && node ../scripts/stamp-build.mjs")
           │
           ▼ (Vite Build)
web/assets/step0/
   ├── step0.js             (组件岛全量逻辑产物，含 Vue runtime + 全部 7 个 StepApp)
   └── geo-step0-island.css (全局 3 竖列与组件岛排版样式)
           │
           ▼ (stamp-build.mjs)
web/index.html              (头部引入 CSS 与 JS，自动重写时间戳链接防强缓存)
```

- **CSS 外链必须引入铁律（R6-1）**：Vite 在 lib 模式下抽取出的 `geo-step0-island.css`（含 `.geo-md` 预览排版规则）不会自动内联注入。宿主 `web/index.html` 的 `<head>` 区域中，**必须在 `./assets/step0/step0.js` 之前显式插入**：
  ```html
  <link rel="stylesheet" href="./assets/step0/geo-step0-island.css">
  ```
- **兼容性保障**：`web/scripts/stamp-build.mjs` 自动更新 `web/index.html` 中的 JS 与 CSS 引用链接，彻底杜绝浏览器（尤其是 Safari）强缓存带来的“代码修改后界面不刷新”假象。
