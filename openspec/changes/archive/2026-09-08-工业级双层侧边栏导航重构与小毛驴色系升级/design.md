# Design: 工业级双层侧边栏导航重构与小毛驴色系升级

## Architecture (架构设计与对象关系)

### 1. 整体布局拓扑（双栏固定流）
```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       Window (100vh)                                         │
├──────────────────────┬───────────────────────────────────────────────────────────────────────┤
│ Sidebar (240px 固定) │ Right Container (flex-1 flex flex-col min-w-0 h-screen)              │
│                      ├───────────────────────────────────────────────────────────────────────┤
│ 1. 品牌与工作台徽标   │ Top Bar (52px 固定高度):                                              │
│ 2. 客户项目快速切换器 │   • 左侧: 动态面包屑 (客户名称 / 一级分类 / 二级功能)                 │
│ 3. 核心功能树 (5大组) │   • 右侧: 全局操作 (一键跑通 5 步流水线 / 打包导出 ZIP / 刷新)        │
│    • 二级菜单子项    ├───────────────────────────────────────────────────────────────────────┤
│ 4. 底部账号与版本信息 │ Workspace (flex-1 overflow-y-auto bg-slate-50 p-6 md:p-8):            │
│                      │   • 各功能 Panel 独立渲染 (原有 Step 1~5 与进阶工具无缝承接)          │
└──────────────────────┴───────────────────────────────────────────────────────────────────────┘
```

---

## Color Palette & Nextdoor AI Design System (色彩体系规范)

全面对齐 `http://100.83.64.112:3002/admin/` 小毛驴 AI 设计规范：

| 角色 | 色值 | 适用场景 |
| :--- | :--- | :--- |
| **主品牌色 (Primary)** | `#7c5bf5` (Nextdoor Violet) | 侧边栏激活文字、高亮光条、主按钮背景、活动 Tab |
| **悬浮主色 (Hover)** | `#6846e3` | 主按钮 Hover 态、可点击微交互 |
| **浅色主基底 (Tint)** | `#7c5bf514` / `rgba(124, 91, 245, 0.08)` | 侧边栏选中项胶囊底色、微徽章高亮背景 |
| **主文本色 (Text Primary)** | `#0f172a` (Slate-900) | 标题、核心数值、强调文本 |
| **次文本色 (Text Secondary)**| `#334155` (Slate-700) / `#64748b` (Slate-500) | 正文描述、二级文字 |
| **弱化文本色 (Muted)** | `#94a3b8` (Slate-400) | 占位说明、未激活图标、辅助属性 |
| **页面底色 (Page Bg)** | `#f8fafc` (Slate-50) | 整个工作台右侧背景色 |
| **卡片底色 (Card Bg)** | `#ffffff` | 工作区卡片、侧边栏容器底色 |
| **细腻边框 (Border)** | `#e2e8f0` (Slate-200) / `#f1f5f9` (Slate-100) | 卡片分割线、侧边栏右边界线 |
| **成功态 (Success)** | `#10b981` (Emerald-500) | 存活 200、校验通过、就绪徽章 |
| **警告态 (Warning)** | `#f59e0b` (Amber-500) | 待发布、需排查、软 404 提醒 |
| **危险态 (Danger)** | `#ef4444` (Red-500) | 死链、异常告警、阻断提醒 |

---

## Navigation Tree（管理台：一级分类 + 二级菜单）

> **产品共识**：采用 Admin 常见「左侧一级分组标题 + 二级可点菜单」样式，分类要一眼能懂；图标一律 Lucide，**禁止**彩色 Emoji。  
> **交互规则**：一级分组只负责折叠/展开分类，不单独占一个业务页；二级菜单点击后切换右侧 `workspace-panel` 并高亮。

```text
1. 项目概览                          (group=overview, Lucide: layout-dashboard)
   ├── 客户档案与总资产看板           (view=overview)
   └── 核心词库与三级意图矩阵         (view=keywords)

2. 交付流水线                        (group=delivery, Lucide: workflow)
   ├── 01 现状诊断与体检              (view=step-1-diag)
   ├── 02 站点底座与三件套            (view=step-2-scaffold)
   ├── 03 普林斯顿 9 因子语料         (view=step-3-princeton)
   ├── 04 矩阵分发与外链探活          (view=step-4-distribute)
   └── 05 商业验收与结案单            (view=step-5-acceptance)

3. 监测运维                          (group=monitoring, Lucide: activity)
   ├── 权威度与 SOV 周报              (view=mon-weekly)
   ├── 大模型问答探针                 (view=mon-probing)
   ├── 巡检告警与全网探活             (view=mon-patrol)
   ├── 客户交付物与专属链接           (view=mon-deliverables)  // 原 ops「给客户看的」
   ├── 知识半衰期与自愈               (view=mon-decay)
   ├── 品牌声誉与危机清洗             (view=mon-crisis)
   └── 普林斯顿复检                   (view=mon-princeton)

4. 进阶攻防                          (group=defense, Lucide: shield)
   ├── 竞品与护城河                   (view=def-rival)         // 差距/包抄/博弈/评测沙盘
   ├── 检索与内容增益                 (view=def-retrieval)     // 意图/图谱/RAG/重排/词库/视觉/合规
   ├── 信源与归因加深                 (view=def-attribution)   // Citation/因果/漏斗/心智
   └── 对抗与鲁棒                     (view=def-guard)         // 幻觉/注入/压测/沙箱/爬虫

5. 系统设置                          (group=settings, Lucide: settings)
   ├── 大模型中枢与密钥               (view=settings-llm)
   └── 离线资产打包导出               (view=settings-export)
```

### 侧边栏视觉规格（二级菜单样式）

| 元素 | 规格 |
| :--- | :--- |
| 一级分组标题 | `text-[11px] font-semibold uppercase tracking-wide text-slate-400 px-3 py-2`；左侧小 Lucide；点击仅折叠本组 |
| 二级菜单项 | 左缩进 + 16px 图标 + 文案；默认 `text-slate-600 hover:bg-slate-100 rounded-lg` |
| 二级激活态 | `bg-[#7c5bf5]/10 text-[#7c5bf5] font-semibold border-r-2 border-[#7c5bf5]` |
| 分组默认展开 | `delivery` / 当前 view 所在分组默认展开；其余可折叠以降低噪音 |

### 现有三场景 → 新导航映射（禁止删入口）

| 现有宿主 | 映射策略 |
| :--- | :--- |
| `scene-delivery` + `step-panel-1~5` | 升为 `view=step-*-*` 独立 Panel |
| `scene-ops`「给客户看的」 | → `view=mon-deliverables`（专属链接/周报打印/结案/证书/ZIP 按钮原样迁入） |
| `scene-ops`「每周巡检」等 | → `mon-weekly` / `mon-probing` / `mon-patrol` / `mon-decay` 等命名二级项 |
| `scene-boost` 四张主题卡 | → `def-rival` / `def-retrieval` / `def-attribution` / `def-guard` 四个二级 Panel，卡内按钮原样迁入 |
| `dashboard-view` 项目列表 | 未选项目时保留；侧边栏仅品牌 + 项目切换器 + 退出 |

---

## Router Model & State Transition (前端路由与状态流转)

### 1. Hash 路由规格
- 标准格式：`#project={projectId}&view={viewId}`（**无**前导 `/`）
  - 例如：`#project=xuzhou_xuanyuan&view=step-4-distribute`
  - Step 2 可选：`#project=...&view=step-2-scaffold&tab=site.html`
- 向后兼容映射表：
  - `step=1` → `view=step-1-diag`；`step=2` → `step-2-scaffold`；…；`step=5` → `step-5-acceptance`
  - 无 `view` 且无 `step` 时默认 `view=overview`
  - 检测到旧 Hash 后必须 `history.replaceState` 回写新格式，避免书签永久停留在旧参数
- 必须同步改造现有 `parseCurrentRoute()` / `updateRouteState()` / `localStorage`（`geo_active_step` 可保留作兼容，但以 `view` 为准）

### 2. 路由切换核心动线
```javascript
function switchView(viewId, pushHash = true) {
  // 1. 隐藏所有右侧面板，仅显式显示目标面板
  document.querySelectorAll('.workspace-panel').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`panel-${viewId}`);
  if (target) target.classList.remove('hidden');

  // 2. 更新左侧二级菜单高亮态 (Nextdoor Violet 胶囊风格)
  // 激活态统一：bg tint + text primary + font-semibold + 右侧 2px 品牌色条
  document.querySelectorAll('.sidebar-nav-item').forEach(btn => {
    btn.classList.remove('bg-[#7c5bf5]/10', 'text-[#7c5bf5]', 'font-semibold', 'border-r-2', 'border-[#7c5bf5]');
    btn.classList.add('text-slate-600', 'hover:bg-slate-100');
  });
  const activeNav = document.getElementById(`nav-${viewId}`);
  if (activeNav) {
    activeNav.classList.add('bg-[#7c5bf5]/10', 'text-[#7c5bf5]', 'font-semibold', 'border-r-2', 'border-[#7c5bf5]');
    activeNav.classList.remove('text-slate-600', 'hover:bg-slate-100');
  }

  // 3. 动态更新顶部面包屑
  updateBreadcrumb(viewId);

  // 4. 同步更新 URL Hash（禁止写成 #/project=...）
  if (pushHash && currentProjectId) {
    const tabSuffix = (viewId === 'step-2-scaffold' && currentScaffoldTab)
      ? `&tab=${encodeURIComponent(currentScaffoldTab)}`
      : '';
    history.replaceState(null, '', `#project=${encodeURIComponent(currentProjectId)}&view=${encodeURIComponent(viewId)}${tabSuffix}`);
  }

  // 5. 按 view 触发原有懒加载钩子（等价于原 switchStep 内的 load* 调用）
  hydrateView(viewId);
}
```

### 3. 响应式约束
- 桌面（`md+`）：侧边栏固定 240px。
- 窄屏：侧边栏改为抽屉（默认收起，Top Bar 提供打开按钮），避免 240px 挤死工作区。

---

## Anti-Coupling & Security Guarantee (解耦与安全性)

1. **业务逻辑与 API 100% 零修改**：
   - 所有的业务数据获取、生成触发、探活与审计完全沿用现有 API（`/api/projects/...`）；
   - 只是改变了 DOM 面板的挂载宿主容器，业务 JavaScript 函数调用不受任何影响；
2. **DOM 严格闭合**：
   - 重构前后必须执行 DOM 平衡校验，确保 `open_divs == close_divs`；
3. **0 彩色 Emoji 铁律**：
   - 菜单项全部采用精细 Lucide 矢量图标，杜绝任何彩色 Emoji 符号，保持企业级专业质感。

