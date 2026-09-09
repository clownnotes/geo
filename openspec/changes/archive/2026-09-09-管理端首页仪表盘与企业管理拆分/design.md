# Design: 管理端首页仪表盘与企业管理拆分

## Architecture (架构设计与对象关系)

```
[登录]
   └─ AdminShell（全局侧栏 + 顶栏）
         ├─ 仪表盘          ← 默认
         ├─ 企业管理        ← Project 列表 / 搜索筛选 / 归属
         ├─ 商业洞察        ← 入口聚合 → 既有 Modal
         ├─ 运维告警
         └─ 系统设置
                │
                └─ 进入客户 → WizardShell（现有项目风琴）
                              └─ 返回 → 企业管理
```

### 核心实体

| 实体 | 含义 | 约束 |
|------|------|------|
| **Partner（合作方/业务员）** | 拓客归属分类，不是登录账号 | `id` 稳定；`name` 可改；`status`: active / archived |
| **Project（客户项目）** | 现有 `projects/{client_id}` | 可选 `partner_id` → Partner；空=未分配/直营 |
| **DashboardSnapshot** | 前端聚合已有 stats + 巡检状态 | 只读，不新建业务库 |

面向对象三问：

1. **谁拥有项目？** 运营主账号拥有全部；Partner 仅是分类标签（本期）。
2. **归属能否改？** 能；改挂只改 `partner_id`，不搬目录。
3. **删 Partner？** 仅允许 `archived`；已挂项目自动变「未分配」或要求先改挂（推荐：归档时批量清空 `partner_id` 并提示）。

## Interface (接口 / 前端)

### 前端视图（`web/index.html`）

| viewId | 侧栏文案 | 内容 |
|--------|----------|------|
| `home-dashboard` | 仪表盘 | `geo-page-head` + 健康条 + 3～4 指标卡 + 「需关注」可选列表 |
| `home-enterprises` | 企业管理 | 工具条（搜索框、筛选项、新建/批量）+ 表格 |
| `home-insights` | 商业洞察 | 入口卡片：EDI / Pitch / 全域大盘 / 对标 / 集团矩阵 / ROI / 沙箱 |
| `home-ops` | 运维告警 | 巡检状态详情 + 全量巡检 + 通知设置入口 |
| `home-settings` | 系统设置 | 复用/嵌入 settings-llm、settings-export；合作方名册管理可放此 Tab |

进入项目：`enterWizard(clientId)` 保持；`backToDashboard` 重命名语义为 `backToEnterprises()`。

### 企业管理筛选条

- **搜索**：对 `client_name` / `client_id` / `official_url` / `brand_name` 做前端或后端包含匹配（项目量级小时前端过滤即可；接口预留 `q`）。
- **筛选**：
  - `industry`（下拉，来自当前列表去重）
  - `sop_status`：全部 / 未完成 / 已完成（基于现有进度字段）
  - `partner_id`：全部 / 未分配 / 具体合作方
- 表格新增列：**合作方**；行内可「改归属」下拉或弹层。

### API（`tools/geo/server.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/partners` | 名册列表（`include_archived=1` 可选 query） |
| POST | `/api/partners` | `{ id?, name }` 创建 |
| POST | `/api/partners/{id}` | 改名 / `status`（实现落在 `do_POST`，非 PATCH） |
| GET | `/api/projects` 或现有列表接口 | 每项增加 `partner_id`, `partner_name`；支持 `q`, `partner_id`, `industry`, `sop_status`（能接则接，否则前端滤） |
| POST | `/api/projects/{id}/meta` | 至少支持 `{ partner_id }`（可空）；新建项目 POST body 增加 `partner_id`（实现落在 `do_POST`，非 PATCH） |

> 注：合作方改名/归档与项目改挂均通过 **POST** 实现（`server.py` `do_POST`），前端调用方式一致；本表已按真实契约由 PATCH 订正为 POST。

不破坏现有创建项目响应形状；仅扩展字段。

## Database Schema / Data Structure

### `config/geo_partners.yaml`

```yaml
partners:
  - id: agent_zhang
    name: 张三（渠道）
    status: active
    created_at: "2026-09-09"
  - id: agent_li
    name: 李四（合资）
    status: active
    created_at: "2026-09-09"
```

落盘由 `tools/geo/partners.py` 负责：字符串经 `_escape_yaml_str` 转义（仓库未引入 PyYAML）；纯中文名 ID 为 `agent_{unix}_{hex}`，并避开已有 ID。

### `projects/{id}/project.yaml` 增量

```yaml
# 代理合作归属（可选；缺省=未分配）
partner_id: "agent_zhang"   # 或 "" / 省略
```

存量项目不强制回填；UI 显示「未分配」。

### 二期预留（本变更只写进 design，不实现）

- Partner 绑定登录手机号 / 只读权限。
- 仪表盘按合作方分成多栏 ROI。
- 合作方自助建客（需审批）。

## UI 规范

- 复用 `geo-page-head` / `geo-btn*` / `geo-alert` / `geo-tabs`；侧栏宽度 220px、▼/▶。
- 禁止 Emoji；健康条用 `geo-alert` / status-dot，不用时钟表情。
- 顶栏胶囊按钮从「登录后首页」移除，迁入商业洞察 / 运维对应页。

## 风险与迁移

- `dashboard-view` DOM 大搬家：注意 JS 里 `getElementById` 与 `showDashboard`/`enterProject` 调用链，需回归登录→列表→进项目→返回。
- 合作方文件损坏时 API 返回空列表 + 明确错误，不阻断企业管理。
