# Tasks: 管理端视觉对齐小毛驴组件令牌

- [x] 1. 令牌与样式资产（抄小毛驴，不另起色板）
  - [x] 1.1 新建 `web/geo-admin.css`：固化 design §2 全部 `:root` 令牌（含 `#ef4444` 退出色），注释标明对照 `App.vue` / `SidebarNav.vue` / `SettingsPanel.vue`。
  - [x] 1.2 在同文件实现组件类：`.geo-page-head`、`.geo-tabs`、`.geo-alert*`、`.geo-btn*`、`.geo-row`、`.geo-tag`、`.geo-status-dot`、`.geo-help`、侧栏 `.accordion-*` / `.job-item` 映射；数值对齐小毛驴，禁止凭感觉改色。
  - [x] 1.3 `web/index.html` 仅 `<link rel="stylesheet" href="/geo-admin.css">`（或现网静态路径等价引入）；确认本地 8088 与生产静态托管均可加载。
  - [x] 1.4 写出 `docs/specs/geo-admin-ui-tokens.md` 一页对照表（必做）。

- [x] 2. 侧栏风琴对齐（抄 `SidebarNav.vue`）
  - [x] 2.1 改造 `#app-sidebar`：宽 **220px**、品牌双行、一级灰底卡片、文字 **▼/▶**、二级选中整行 `#e0e7ff` + 左 3px 紫条；移除旧「仅右侧竖线」选中样式。
  - [x] 2.2 底部「退出登录」字色 `#ef4444`，hover 用 `--geo-danger-tint`；保持现有 logout 逻辑。
  - [x] 2.3 确认 `switchView` / 路由 hash / 分组展开行为不回归。

- [x] 3. 壳层与高频页套用
  - [x] 3.1 工作区 / 顶栏：页底 `#f8fafc`；主 CTA `.geo-btn-primary`，次要操作改 `.geo-btn` outline（抽样替换，禁止无差别改全站按钮）。
  - [x] 3.2 P1 必须两处：`settings-llm`（页头+Tab 或按钮组）+（阶段四台账 **或** 阶段五监测）使用 `.geo-row` / `.geo-tag` / `.geo-alert` 至少一组。
  - [x] 3.3 在 `docs/specs/geo-admin-ui-tokens.md` 写明：未覆盖面板后续改动必须优先用 `geo-*`。

- [x] 4. 验证
  - [x] 4.1 DOM：`open_div == close_div`；无新增彩色 Emoji（▼/▶ 除外）。
  - [x] 4.2 本地 8088：侧栏 + P1 对照小毛驴；CSS 文件 200；路由与展开无破坏。
  - [x] 4.3 验收清单写入 `review-log.md`。
