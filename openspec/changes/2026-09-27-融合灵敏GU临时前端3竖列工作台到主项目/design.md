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
> 1. **新建容器与旧标题移除口径（R6-6 / R7-2）**：  
>    - 宿主面板容器 `#panel-step-4-qacard`（对应全新 04 GEO 答题卡与向量库）在主工程基线中**不存在**，必须在 `web/index.html` 中新建该容器，内部放置 `<div id="step4-app-root"></div>`；  
>    - **阶段五（`#panel-step-4-distribute`）与阶段六（`#panel-step-5-acceptance`）**面板内原有的旧 DOM（含旧 `<h2>`）随整体替换为组件岛根容器 `<div id="stepX-app-root">` 而移除；  
>    - **阶段一~三的原有旧 DOM 与旧 `<h2>` 全部保留在 `legacy-step1~3-container` 隐藏兜底容器内，严禁删除**（内含 `preview-step-1-boss/tech` 等节点，供回调安全执行）；前台可见的阶段标题，统一由组件岛内部的 `StageHeader.vue` 规范渲染；  
> 2. **`VIEW_META` 全量重构与文案订正（R6-3 / R6-5 / R7-3 / R8-4）**：  
>    - 订正 01~03 标签文案并同步对齐侧边栏按钮（*注：演进对照表业务名称 ≠ `VIEW_META.label` 字段*）：  
>      - `'step-1-diag'`: label 改为 `'01 诊断现状并出具报告'`（主工程原为实测值 `'01 现状诊断与体检'`，`:7191`）；  
>      - `'step-2-scaffold'`: label 改为 `'02 普林斯顿母盘与素材库'`（主工程原为实测值 `'02 站点底座与三件套'`，`:7192`）；  
>      - `'step-3-princeton'`: label 改为 `'03 交钥匙官网与三件套'`（主工程原为实测值 `'03 普林斯顿 9 因子语料'`，`:7193`）；  
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
> 6. **兜底容器明确（R6-8 / R7-2）**：阶段 1~3 新建 `legacy-step1~3-container` 隐藏兜底容器包裹老 DOM（含旧 h2 与 `preview-step-*` 预览容器），确保所有既有 DOM、ID 与回调完好无损。  
> **注1（历史编号保留铁律）**：宿主容器 `#panel-step-4-distribute`（对应 05 矩阵分发）与 `#panel-step-5-acceptance`（对应 06 商业验收）系主工程历史遗留命名，其内部根节点已准确对齐为 `#step5-app-root` 与 `#step6-app-root`。此为既有规范事实，**严禁在 apply 阶段擅自修改宿主面板 ID**。  
> **注2（根节点与类名修正）**：周期运营挂载根节点规范订正为实测值 `#mon-recurring-app-root`，Bridge 导出类名规范订正为 `GeoRecurringMonitorBridge`。

### 2.1 宿主老脚本兼容与空节点安全守卫（乙案：彻底保证零报错，R6-2 / R7-1 / R7-4 / R7-5）
阶段五（原04分发）与阶段六（原05验收）老 DOM 全部替换为组件岛独立根容器（仅保留 `<div id="stepX-app-root">`），但主工程 `enterWizard()` 会调用 `loadStepPreviews()`。经穷举筛查，被替换区间内的 606 个缺失 ID 中，有 6 个函数存在直接获取 DOM 抛出 `TypeError` 并触发 `console.error` 的风险。
为兑现「控制台 0 报错」承诺，守卫节点一律取函数体内首个 DOM 访问节点，在 apply 阶段必须补齐空安全守卫：

1. **`loadMarkdownToElem`（通用文档渲染函数，R7-1 必报错核心）**：  
   函数体首行增加收敛式守卫：
   ```javascript
   const el = document.getElementById(elemId);
   if (!el) return; // 目标节点不存在时静默跳过，彻底解决 preview-step-5 缺失导致的 TypeError
   el.innerHTML = marked.parse(data.content);
   ```
2. **`loadProjectRoiEvaluation`**：首行增加 `if (!document.getElementById('roi-total-val')) return;`；
3. **`loadProjectBenchmarkEvaluation`**：首行增加 `if (!document.getElementById('bm-industry-name')) return;`；
4. **`loadMonitorDashboardMetrics`**：首行增加 `if (!document.getElementById('metric-sov')) return;`；
5. **`loadAcceptanceData`**：首行增加 `if (!document.getElementById('acceptance-status-badge')) return;`；
6. **`loadDistributionLedger`（R7-5 首个访问节点）**：首行增加 `if (!document.getElementById('dist-channels-ledger-list')) return;`。

#### 老脚本可达性筛查结论表（R7-4 守卫判定依据）
- **需补守卫（6个）**：上述 6 个函数（1 个通用渲染函数 + 5 个业务加载函数），补齐后彻底消除 `console.error`；
- **自带守卫（6个，无需改动）**：`loadProjectHistoryChart`、`loadAlertHistory`、`applyDistributeRunStatusBar`、`applyChannelPackStatuses`、`loadFidelityScoresForCards`、`onDistCanPublishChange`，体内已自带判空；
- **不可达或空 catch 静默（17个，无需改动）**：`loadDefensePreview`（`loadStepPreviews` 可达但被 `catch(e){}` 空捕获静默，阶段六已由组件岛资产与反向包抄工作台接管）、`buildToutiaoPack` 等 16 个入口按钮随老 DOM 移除的函数，无需改动。

### Bridge 标准接口定义与参数透传约定
```javascript
export const GeoStepXBridge = {
  // [必需] 挂载组件岛到宿主 DOM（内部将 bridge 参数原样注入 Vue 组件 Props: { bridge }）
  // 宿主侧调用传参形状: mount(containerEl, { projectData, subStep })
  mount(el, bridge) {},
  // [通用约定] 卸载组件岛并清理全局监听（供内部重挂载与未来扩展，宿主当前不直接调用）
  unmount() {},
  // [按需实现] 响应外部项目切换，更新响应式上下文（宿主仅阶段零实际调用 __GEO_STEP0__.refresh）
  refresh(projectData) {},
  // [按需实现] 切换阶段内部子步进（宿主仅阶段零实际调用 __GEO_STEP0__.setSubStep）
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

2. **本地降级持久化与键名契约规范（R8-1 / R8-2 / R8-3）**：
   - **命名空间隔离与分片规范**：
     * **聚合式单键**：阶段 1 与阶段 6 使用 `geo_step{N}_state_{clientId}` 存储整阶段状态；
     * **分片式语义键**：阶段 2~5 使用 `geo_step{N}_{语义描述}_{clientId}`（如 `geo_step2_step_index_`、`geo_step5_active_topic_` 等）；
   - **跨阶段键名契约对齐（R8-1 致命断裂修复）**：
     * 写入方（`useStep4.js:28, 278`）：`geo_step4_qa_cards_${clientId}`；
     * 读取方（`stage5Config.js:170`）：统一对齐为 **`geo_step4_qa_cards_${clientId}`**（修复原本读取缺少 `qa_` 导致读取恒为空的问题），并将空 catch 改为 `console.warn`；
   - **折叠态持久化补齐（R8-2）**：
     * 为 `useStep3.js`、`useStep4.js`、`useStep5.js` 补齐与 `useStep2.js:139` 统一的折叠态写入：`localStorage.setItem(STORAGE_KEY_HEADER, String(val))`，实现刷新后折叠态记忆；
   - 若本地无缓存，自动生成带有项目真实字段的基线模板文件。

3. **项目切换刷新与重挂载机制（彻底杜绝上下文滞后，R6-4 / R9-1 甲案）**：
   - **阶段零响应式刷新与其余阶段重挂载分工**：
     * **阶段零**：宿主实际调用 `window.__GEO_STEP0__.refresh(p)` 与 `setSubStep`，故 `GeoStep0Bridge` 及其内部 `Step0App.vue` 必须保持完整的 `refresh` 逻辑并暴露 `defineExpose({ refresh })`；
     * **阶段 1~6 与周期复测**：宿主无 `refresh` 调用点，其上下文更新依赖宿主在 `enterWizard` 切换项目时，统一将所有 `window.__GEO_STEP0..6_MOUNTED__` 以及 `window.__GEO_RECURRING_MOUNTED__` 标志位重置为 `false`；当前活跃视图与后续切换点击的阶段面板因为守卫为 `false` 而自动以最新项目数据执行 `mount()` 重挂载，彻底根除项目切换后的数据串流问题。各 Bridge 保留既有接口签名，不强求对无调用方的阶段编写冗余存根。

---

## 4. 构建与发布流水线架构

```
web/step0-src/
   ├── vite.config.js       (显式固定 assetFileNames: 'geo-step0-island.[ext]')
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
- **CSS 产物名解耦锁定（R8-8）**：在 `step0-src/vite.config.js` 的 `rollupOptions.output` 中通过 `assetFileNames` 显式固定 CSS 产物名为 `geo-step0-island.css`，彻底解除对 `package.json.name` 的隐式耦合。
- **构建版本戳防假成功断言机制（R8-5）**：`web/scripts/stamp-build.mjs` 自动更新 `web/index.html` 中的 JS 与 CSS 引用链接：
  - 仅当目标正则真实命中并替换成功时才自增 `changed` 计数；
  - 遍历检查全部目标，若 `web/index.html` 中缺少 CSS 或 JS 引用链接，脚本显式打印错误告警并设置 `process.exitCode = 1` 退出，彻底杜绝假成功掩盖资源缺失风险。
