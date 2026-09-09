# Design: 管理端视觉对齐小毛驴组件令牌

## 1. 原则：抄组件，不造轮子

```text
小毛驴 Admin (Vue 已组件化)          GEO Admin (单页 HTML)
─────────────────────────          ─────────────────────
App.vue 壳 / token                  :root --geo-* 对齐同色
SidebarNav 风琴                     同一套 class 名或 geo- 前缀映射
SettingsPanel 页头/Tab              .geo-page-head / .geo-tabs
仓库行 / 告警 / outline 钮          .geo-row / .geo-alert / .geo-btn
PageHelpPanel                       .geo-help（可选，交互抄、文案自写）
```

**禁止**：为 GEO 单独发明第二套主色、第二套 Tab 下划线逻辑、第二套侧栏选中态。  
**允许**：class 加 `geo-` 前缀以免与页面内旧 utility 冲突；语义与数值必须与小毛驴一致。

**参考根路径（本机只读）**：  
`/Users/a1/next核心项目/02_管理员操作端/XiuLan_IDE/src/admin/`

---

## 2. 设计令牌（必须与小毛驴一致）

| Token | 值 | 小毛驴出处 |
|-------|-----|------------|
| `--geo-primary` | `#7c5bf5` | 品牌紫 / Tab active / 左边条 |
| `--geo-primary-hover` | `#6846e3` | 主按钮 hover |
| `--geo-accent-text` | `#4f46e5` | `.job-item.active` 文字 |
| `--geo-accent-bg` | `#e0e7ff` | 选中底 |
| `--geo-page-bg` | `#f8fafc` | `.super-layout` / `.sm-body` |
| `--geo-sidebar-bg` | `#ffffff` | `.global-sidebar` |
| `--geo-group-bg` | `#f1f5f9` | `.accordion-header` |
| `--geo-border` | `#e2e8f0` | 通用边框 |
| `--geo-text` | `#0f172a` | 主文字 |
| `--geo-muted` | `#64748b` | 次要文字 |
| `--geo-danger` | `#ef4444` | 退出登录字色（SidebarNav 内联） |
| `--geo-danger-tint` | `rgba(239, 68, 68, 0.08)` | `.logout-nav:hover` |
| `--geo-alert-bg` | `#fef2f2` | 告警条浅红底（对齐运维告警观感） |
| `--geo-alert-border` | `#fecaca` | 告警条边框 |
| `--geo-success` | `#16a34a` | 状态点、恢复类动作 |

侧栏宽度：**本变更统一为 `220px`**（小毛驴约 190px；GEO 中文菜单略宽，取 220 兼顾形态与可读性，禁止再保留 240 旧宽）。

退出登录字色：**精确使用 `#ef4444`**（对齐 `SidebarNav.vue` 内联色），hover 浅红底 `rgba(239, 68, 68, 0.08)`。

一级箭头：**统一使用文字 `▼` / `▶`**（与小毛驴一致，禁止本变更内混用 Lucide chevron）。几何三角不算彩色 Emoji。

---

## 3. 侧栏结构映射

| 小毛驴 | GEO 目标 |
|--------|----------|
| `.brand-logo` + `.brand-sub` | 「GEO」+「邻里交付 / Nextdoor」双行 |
| `.accordion-group` | 现有 `sidebar-group` 改为同视觉卡片 |
| `.accordion-header` + ▼/▶ | 一级分类点击展开；**固定文字 ▼/▶**（禁止混用 Lucide） |
| `.submenu-list` + `.job-item.active` | 二级 `sidebar-nav-item`；去掉「仅右侧竖线」旧样式，改为整行淡紫底 + 左 3px 紫条 |
| 红色退出 `#ef4444` | 侧栏底部「退出登录」红字，对标小毛驴 |

路由：`switchView(viewId)` / `#project=&view=` **不变**。

---

## 4. 内容区组件契约（HTML 约定）

### 4.1 页头
```html
<header class="geo-page-head">
  <h1 class="geo-page-title">页面标题</h1>
  <!-- 可选右侧动作 -->
</header>
```

### 4.2 Tab
```html
<nav class="geo-tabs">
  <button type="button" class="active">模型管理</button>
  <button type="button">套餐配置</button>
</nav>
```
行为：灰字 / active 紫字 + `::after` 紫下划线（抄 `SettingsPanel` `.settings-tabs`）。

### 4.3 告警条
```html
<div class="geo-alert geo-alert-danger" role="alert">
  <div class="geo-alert-body">…</div>
  <button type="button" class="geo-btn geo-btn-success">体验恢复</button>
</div>
```

### 4.4 按钮
- `.geo-btn`：线框默认  
- `.geo-btn-primary`：实心紫（仅主 CTA）  
- `.geo-btn-danger`：红字或红线框  
- `.geo-btn-success`：绿系次要正向动作  

### 4.5 行列表
```html
<div class="geo-row">
  <span class="geo-status-dot geo-status-ok"></span>
  <div class="geo-row-main">
    <div class="geo-row-title">标题</div>
    <div class="geo-row-meta"><span class="geo-tag">Tag</span></div>
  </div>
  <div class="geo-row-actions">…文字链…</div>
</div>
```

### 4.6 帮助折叠（可选）
`.geo-help` 默认收起；文案「忘了这页怎么用？点击展开」——交互抄小毛驴，不引入 Vue 组件依赖。

---

## 5. 落地策略与非目标

**落地顺序**  
1. 新增独立样式表 **`web/geo-admin.css`**（禁止把整套组件样式只堆在 `index.html` 巨型 `<style>` 里）；`index.html` 仅 `<link>` 引入并保留最少覆盖。  
2. Token + 侧栏 DOM/class 改造（宽 220px、▼/▶、选中态、红退出）。  
3. 工作区背景与顶栏弱化（少渐变、少重阴影）；主 CTA 实心紫、次要 outline。  
4. 套 P1 页面（必须两处都做，不可只做一处）：  
   - `settings-llm`（或系统设置大模型面板）：页头 + Tab 或按钮组  
   - 阶段四台账 **或** 阶段五监测区：至少一组 `.geo-row` / `.geo-tag` / `.geo-alert`  
5. 写出 `docs/specs/geo-admin-ui-tokens.md` 对照表（**必做**，非可选），供后续面板复用。  
6. 其余面板：本变更未改到的，后续改动必须优先用 `geo-*`。  

**非目标**  
- 不把 GEO 迁入 XiuLan_IDE / Vue  
- 不改菜单信息架构与 viewId  
- 不擅自推生产  
- 深色 ROI / Pitch 可保留，仅统一外围按钮与告警组件  
- 不把小毛驴业务菜单（客服/知识库等）拷进 GEO  

**无后端 / 无 DB Schema。**

---

## 6. 验收对照

- 侧栏截图对照小毛驴：一级灰卡片、二级淡紫选中、红退出。  
- 设置或阶段四/五之一：页头 + Tab 或行列表 + Tag 肉眼同源。  
- `open_div == close_div`；页面无新增彩色 Emoji。  
- 本地 `http://127.0.0.1:8088` 验证。
