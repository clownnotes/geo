# GEO Admin UI Tokens — 对齐小毛驴组件

> 实现源码：`web/geo-admin.css`  
> 只读参考：`~/next核心项目/02_管理员操作端/XiuLan_IDE/src/admin/`（`App.vue` / `SidebarNav.vue` / `SettingsPanel.vue`）  
> **禁止另起第三套色板或按钮样式。** 未在本变更中改到的面板，后续改动必须优先使用下方 `geo-*` 类。

## 令牌

| Token | 值 | 用途 |
|-------|-----|------|
| `--geo-primary` | `#7c5bf5` | 主色 / Tab / 左边条 |
| `--geo-primary-hover` | `#6846e3` | 主按钮 hover |
| `--geo-accent-text` | `#4f46e5` | 侧栏选中字 |
| `--geo-accent-bg` | `#e0e7ff` | 侧栏选中底 |
| `--geo-page-bg` | `#f8fafc` | 工作区底 |
| `--geo-group-bg` | `#f1f5f9` | 风琴一级头 |
| `--geo-border` | `#e2e8f0` | 边框 |
| `--geo-danger` | `#ef4444` | 退出登录 |
| `--geo-danger-tint` | `rgba(239,68,68,0.08)` | 退出 hover |
| `--geo-success` | `#16a34a` | 状态点 / 恢复 |
| `--geo-sidebar-width` | `220px` | 侧栏宽 |

## 组件类

| 类名 | 用途 |
|------|------|
| `.geo-page-head` / `.geo-page-title` | 页头条 |
| `.geo-tabs` | 底边紫下划线 Tab |
| `.geo-alert` / `.geo-alert-danger` | 告警条 |
| `.geo-btn` / `.geo-btn-primary` / `.geo-btn-danger` / `.geo-btn-success` | 线框 / 主 / 危险 / 成功 |
| `.geo-row` + `.geo-status-dot*` + `.geo-tag*` | 行列表 |
| `.geo-help` | 折叠说明 |
| `#app-sidebar .accordion-*` / `.sidebar-nav-item.active` | 侧栏风琴（▼/▶） |

## 非目标

- 不迁 Vue；不拷小毛驴业务菜单。  
- 深色 ROI / Pitch 可保留商业分量，外围按钮尽量用 `geo-btn*`。
