# Design: 管理端企业管理按合作方侧栏与合作方一级菜单

## Architecture

```
AdminShell 侧栏
├─ 工作台
│    ├─ 仪表盘
│    ├─ 商业洞察
│    ├─ 运维告警
│    └─ 系统设置          ← 仅 LLM + 导出说明
├─ 企业管理               ← 一级风琴（常用）
│    ├─ 全部企业          → home-enterprises, partnerFilter=""
│    ├─ 未分配            → partnerFilter="__none__"
│    └─ {partner.name}×N  → partnerFilter=partner.id   （仅 active）
└─ 合作方管理             ← 一级风琴（常用）
     └─ 合作方名册        → home-partners（本期唯一二级；不放空占位）
```

> 产品拍板：企业管理二级 **固定含「未分配」**；合作方管理本期只做名册一页。

### 对象关系

- **Partner**：名册实体；侧栏二级只展示 `status=active`。
- **归档合作方**：从企业管理二级消失；其企业已清为未分配，出现在「未分配」。
- **企业管理页**：仍是一张表；侧栏点击 = 设置筛选状态，不新建多套表格 DOM。

## Interface

### 前端

| 符号 | 行为 |
|------|------|
| `renderHomeEnterpriseNav(partners)` | 清空并重绘 `#sidebar-group-enterprises` 内动态项 |
| `openEnterprisesByPartner(partnerId)` | `switchHomeView('home-enterprises')` + 设 `#filter-partner` + `applyEnterpriseFilters()` + 高亮对应 nav |
| `switchHomeView('home-partners')` | 展示名册面板（从 settings 迁出的 DOM/逻辑） |
| `refreshPartnersAndNav()` | CRUD 成功后：`loadPartners` → 刷新名册表 + 企业管理二级 + 筛选下拉 |

### Hash（建议）

- `#home=home-enterprises&partner=agent_xxx` / `partner=__none__`
- 刷新后恢复筛选与侧栏高亮。

### API

无强制变更；继续：

- `GET /api/partners?include_archived=0` 供侧栏（只要 active）
- 名册页可用 `include_archived=1` 看已归档（若 UI 需要）

## Data

不改 `geo_partners.yaml` / `project.yaml` 字段。

## UI 细节

- 「企业管理」「合作方管理」默认：**展开**（与「工作台」并列常用）。
- 二级过多时：企业管理 submenu 区域 `max-height` + 内部滚动，避免撑破侧栏。
- 选中态：沿用 `.sidebar-nav-item.active` 左边条。
- 系统设置 Tab：删除「合作方名册」；保留大模型、导出说明。

## 风险

- 动态 nav 的 `id`（如 `nav-home-ent-partner-{id}`）需对 `id` 做 CSS/HTML 安全字符（已有 partner id 规范 `agent_*`）。注意 `create_partner` 显式传入 `id` 的分支不强制 `agent_` 前缀，可能以数字开头；因 nav id 带固定前缀 `nav-home-ent-partner-`，最终选择器不会以数字开头，仍安全。
- 与表内「改挂」联动：改挂后若当前筛的是原合作方，该行应从表中消失（现有 filter 逻辑应已覆盖，回归点一下）。
- **带筛选入口**：统一用 `openEnterprisesByPartner(partnerId)`，**不得**复用 `switchHomeView` 的第二参（现网 `switchHomeView(viewId, skipRoute)` 的 `skipRoute` 为布尔，塞对象会破坏路由）。
- **归档当前正筛选的合作方**：若用户正筛某合作方时将其归档，侧栏该项消失后筛选会指向隐藏项 → 需自动把筛选切到「未分配」（或「全部企业」）并重绘，避免空表无提示。
- **父级风琴落点**：点击「企业管理」父级标题默认进入「全部企业」（清空合作方筛选）；「合作方管理」父级默认进入「合作方名册」。
