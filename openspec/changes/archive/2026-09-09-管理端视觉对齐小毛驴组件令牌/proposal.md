# Proposal: 管理端视觉对齐小毛驴组件令牌

## Why (为什么做)

1. **同一品牌两套脸**：GEO 管理端（`web/index.html`）与小毛驴 AI Admin（`http://…:3002/admin/`）已共用品牌紫 `#7c5bf5`，但侧栏与内容区的「形状语言」不同——GEO 仍是扁平列表 + 重色块 CTA，小毛驴是风琴卡片 + 线框工具钮 + 行列表。对外演示时像两个产品。
2. **小毛驴已经组件化过，不要再造轮子**：管理端源码在本机  
   `~/next核心项目/02_管理员操作端/XiuLan_IDE/src/admin/`  
   （`App.vue` 壳、`SidebarNav.vue` 风琴、`SettingsPanel.vue` 页头/Tab、仓库行/告警等）。样式与交互已线上验证；GEO 应**移植令牌与 class 约定**，而不是另起一套 Tailwind 花样。
3. **先壳后页，控制爆炸半径**：GEO 仍是单页大 HTML，不宜整仓迁 Vue；用「设计令牌 + 可复用 CSS 组件类」在现有壳上对齐，分批改高频页，避免一次重写业务面板。

---

## What Changes (改动了什么)

1. **建立 GEO Admin 设计令牌（对齐小毛驴，禁止另起色板）**  
   固化 CSS 变量：主色 `#7c5bf5`、选中底 `#e0e7ff`、选中字 `#4f46e5`、页底 `#f8fafc`、边框 `#e2e8f0`、危险红/成功绿语义。文档注明源码对照路径，后续改色只改 token。

2. **移植侧栏风琴形态（抄 `SidebarNav.vue`，不重发明）**  
   一级：灰底圆角卡片 `accordion-group` / `accordion-header` + ▼/▶。  
   二级：`job-item` 选中 `#e0e7ff` + 左边紫条。  
   品牌行对齐「NextClaw / 小毛驴 AI」双行结构；退出登录改为醒目红字。  
   **不改变**现有 viewId 路由与菜单信息架构。

3. **移植内容区通用组件类（抄 Settings 壳与列表套路）**  
   落地独立样式表 **`web/geo-admin.css`**（`index.html` 仅 link 引入）：  
   - 页头条 `geo-page-head`  
   - 底边 Tab `geo-tabs`（紫字 + 紫下划线）  
   - 告警条 `geo-alert`（浅红底 + 右侧动作）  
   - 线框按钮 `geo-btn` / `geo-btn-primary` / `geo-btn-danger`  
   - 行列表 `geo-row` + 状态点 + Tag `geo-tag`  
   - 折叠帮助 `geo-help`（对标 `PageHelpPanel` 交互，文案自写）

4. **分批套到高频壳与页面（本变更范围）**  
   - P0：侧栏（宽 220px、▼/▶、红退出 `#ef4444`）+ 顶栏/工作区灰底 + 全局按钮层级（主实心、次 outline）  
   - P1（两处都做）：设置/大模型中枢；阶段四台账 **或** 阶段五监测（行/Tag/告警）  
   - **明确不做**：结案 Pitch / 深色 ROI 大屏可保留商业分量；不迁 Vue；不改后端 API；不拷小毛驴业务菜单。

5. **防回归与复用文档**  
   0 新增彩色 Emoji；DOM 平衡；本地 8088 对照小毛驴截图验收；产出 `docs/specs/geo-admin-ui-tokens.md` 对照表。

---

## Capabilities (对外能力)

- 管理端与小毛驴 Admin **视觉同源**（侧栏 + 内容通用件）。  
- 后续新面板优先复用 `geo-*` 组件类，禁止再发明第三套按钮/Tab 样式。  
- 无新 REST API；纯前端壳与样式资产。

---

## Impact (影响范围)

| 区域 | 说明 |
|------|------|
| 参考源（只读） | `next核心项目/.../admin/App.vue`、`SidebarNav.vue`、`SettingsPanel.vue`、settings 子组件样式 |
| 改动主文件 | `web/geo-admin.css`（新建）、`web/index.html`（引入与 DOM 改造） |
| 文档 | **必做** `docs/specs/geo-admin-ui-tokens.md` + 本变更 design 对照表 |
| 不改 | `tools/geo/*` 业务逻辑、客户交付站点、生产部署（除非另令） |
