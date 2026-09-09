# Tasks: 管理端视觉对齐小毛驴组件令牌

- [ ] 1. 令牌与样式资产（抄小毛驴，不另起色板）
  - [ ] 1.1 在 `web/` 固化 `:root` 令牌表（见 design §2），注释标明对照 `App.vue` / `SidebarNav.vue` / `SettingsPanel.vue`。
  - [ ] 1.2 新增或内联 `geo-admin` 组件样式：`.geo-page-head`、`.geo-tabs`、`.geo-alert`、`.geo-btn*`、`.geo-row`、`.geo-tag`、`.geo-status-dot`、`.geo-help`（数值对齐小毛驴，禁止凭感觉改色）。
  - [ ] 1.3 （可选）抽出 `docs/specs/geo-admin-ui-tokens.md` 一页对照表，供后续面板复用。

- [ ] 2. 侧栏风琴对齐（抄 `SidebarNav.vue`）
  - [ ] 2.1 改造 `#app-sidebar`：品牌双行、一级 `accordion` 灰底卡片、▼/▶ 或统一 Lucide、二级选中整行 `#e0e7ff` + 左紫条。
  - [ ] 2.2 底部退出登录改为红字样式；保持现有 logout 逻辑。
  - [ ] 2.3 确认 `switchView` / 路由 hash / 分组展开行为不回归。

- [ ] 3. 壳层与高频页套用
  - [ ] 3.1 工作区 / 顶栏：页底 `#f8fafc`，主 CTA 实心紫、次要操作改 outline（全局抽样替换，避免整文件无差别改按钮）。
  - [ ] 3.2 P1 套用至少 2 处：`settings-llm`（或等价设置面板）页头+Tab 或按钮组；阶段四台账或阶段五列表改用 `.geo-row` / `.geo-tag` / `.geo-alert` 之一组。
  - [ ] 3.3 约定：本变更未覆盖的面板，后续改动必须优先用 `geo-*`（在 review-log 或 docs 写明）。

- [ ] 4. 验证
  - [ ] 4.1 DOM：`open_div == close_div`；无新增彩色 Emoji。
  - [ ] 4.2 本地 8088：侧栏 + P1 页面对照小毛驴截图验收；路由与展开无破坏。
  - [ ] 4.3 （若有）轻量静态检查脚本或手工清单写入 review-log。
