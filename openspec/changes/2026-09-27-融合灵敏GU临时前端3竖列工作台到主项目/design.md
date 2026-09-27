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
| **01** | 商业诊断与转化 | `#panel-step-1-diag` | `#step1-app-root` | `window.__GEO_STEP1__` (`GeoStep1Bridge`) |
| **02** | 普林斯顿母盘与素材 | `#panel-step-2-scaffold` | `#step2-app-root` | `window.__GEO_STEP2__` (`GeoStep2Bridge`) |
| **03** | 交钥匙官网与三件套 | `#panel-step-3-princeton`| `#step3-app-root` | `window.__GEO_STEP3__` (`GeoStep3Bridge`) |
| **04** | GEO 答题卡与向量库 | `#panel-step-4-qacard` *(注0)* | `#step4-app-root` | `window.__GEO_STEP4__` (`GeoStep4Bridge`) |
| **05** | 矩阵分发与链接检查 | `#panel-step-4-distribute` *(注1)* | `#step5-app-root` | `window.__GEO_STEP5__` (`GeoStep5Bridge`) |
| **06** | 首次交付与资产交接 | `#panel-step-5-acceptance` *(注1)* | `#step6-app-root` | `window.__GEO_STEP6__` (`GeoStep6Bridge`) |
| **运营** | 周期复测与商业月报 | `#panel-mon-recurring` | `#mon-recurring-app-root` *(注2)* | `window.__GEO_RECURRING__` (`GeoRecurringMonitorBridge`) |

> **注0（主工程需新建容器与路由元数据重写规范）**：  
> 1. **新建容器**：宿主面板容器 `#panel-step-4-qacard`（对应全新 04 GEO 答题卡与向量库）在主工程基线中**不存在**，必须在 `web/index.html` 中新建该容器，内部放置 `<div id="step4-app-root"></div>`；  
> 2. **`VIEW_META` 升位重构**：  
>    - 注册新视图：`'step-4-qacard': { step: 4, label: '04 GEO 答题卡与向量问答库', group: 'delivery', groupLabel: '首次交付' }` *(注：必须包含 groupLabel 防止面包屑 undefined)*；  
>    - 升位分发视图：`'step-4-distribute': { step: 5, label: '05 矩阵分发与链接检查', group: 'delivery', groupLabel: '首次交付' }`（`step: 4 -> 5`）；  
>    - 升位验收视图：`'step-5-acceptance': { step: 6, label: '06 首次交付与资产交接单', group: 'delivery', groupLabel: '首次交付' }`（`step: 5 -> 6`）；  
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
> 4. **引用点与白名单全量对齐**：  
>    - 核对并确保主工程内依赖 `STEP_TO_VIEW` 的全部 8 处引用（`:7173`、`:7269` 深链解析、`:7281` 缓存回退、`:7297` / `:7299` 路由落盘、`:9232` `enterWizard`、`:9949` / `:9954` 上下一步导航）以及 `currentStep = meta.step` 的门禁 UI（`updatePipelineGateUI`）步进完全统一；  
>    - 加固 `isDeliveryStepView(viewId)` 函数为显式交付白名单数组判定（`['step-1-diag', 'step-2-scaffold', 'step-3-princeton', 'step-4-qacard', 'step-4-distribute', 'step-5-acceptance'].includes(viewId)`），杜绝正则隐式匹配带来的遗漏隐患。  
> **注1（历史编号保留铁律）**：宿主容器 `#panel-step-4-distribute`（对应 05 矩阵分发）与 `#panel-step-5-acceptance`（对应 06 商业验收）系主工程历史遗留命名，其内部根节点已准确对齐为 `#step5-app-root` 与 `#step6-app-root`。此为既有规范事实，**严禁在 apply 阶段擅自修改宿主面板 ID**。  
> **注2（根节点与类名修正）**：周期运营挂载根节点规范订正为实测值 `#mon-recurring-app-root`，Bridge 导出类名规范订正为 `GeoRecurringMonitorBridge`。

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

3. **项目切换刷新双保险机制（彻底杜绝上下文滞后）**：
   - **Bridge 侧全量落地 `refresh(projectData)`**：在 `main.js` 中为全部 Bridge（`GeoStep0`~`GeoStep6` 及 `GeoRecurringMonitorBridge`）统一实现 `refresh(opts)`，并在对应 Vue 组件根实例上暴露 `refresh` 方法；
   - **宿主侧重置守卫标志位**：宿主 `index.html` 在 `enterWizard` 切换项目时，统一将所有 `window.__GEO_STEPX_MOUNTED__` 标志位重置为 `false`，并对当前已呈现的活跃视图执行带 `forceRemount=true` 的渲染调用；用户后续切换到其他阶段面板时，会因为守卫为 `false` 而自动以最新项目数据执行 `mount()`，彻底根除项目切换后的数据串流问题。

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
   └── geo-step0-island.css (全局 3 竖列与组件岛样式)
           │
           ▼ (stamp-build.mjs)
web/index.html              (自动重写产物引用链接: ./assets/step0/step0.js?v=20260927XXXXXX)
```

- **兼容性保障**：`web/scripts/stamp-build.mjs` 自动更新 `web/index.html` 中的引用链接，彻底杜绝浏览器强缓存带来的“代码修改后界面不刷新”假象。
