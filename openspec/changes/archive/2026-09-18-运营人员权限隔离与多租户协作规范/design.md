# Design: 运营人员权限隔离与多租户协作规范

## Architecture (架构设计与对象关系)

### 1. 面向对象三问

#### 【对象一：开发者 (Developer)】
- **定位**：系统唯一的超级管理员与底层架构维护者（师弟）。
- **属性**：
  - `phone`: 固定管理员手机号（如 `13150568888`）
  - `role`: `"developer"`
  - `allowed_projects`: `["*"]`（可查看与操作所有客户站点）
  - `permissions`: `["*"]`（拥有全量开发、部署、配置、成员管理权限）
- **行为**：
  - 添加/删除/停用运营人员；
  - 为运营人员分配负责的客户项目和具体业务功能；
  - 触发线上生产环境部署（Deploy to mini/production）；
  - 查看并操作所有租户的所有数据。

#### 【对象二：运营人员 (Operator)】
- **定位**：业务使用者（同事们），**纯使用，无管理权限**。
- **属性**：
  - `phone`: 同事手机号（必须先在小毛驴统一体系注册）
  - `name`: 同事姓名（如“张三”）
  - `role`: `"operator"`
  - `status`: `"active"` | `"disabled"`
  - `allowed_projects`: `["nextgeo", "client_a"]`（管辖项目白名单）
  - `permissions`: 细分业务权限数组（如 `["keyword:manage", "article:edit"]`）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间
- **行为**：
  - 在授权的项目范围内录入关键词、校对文章、触发 AI 流水线、预览页面；
  - **禁止行为**：禁止进入成员管理面板、禁止修改全局系统配置、禁止触发线上生产发布、禁止跨项目访问未授权客户数据。

#### 【对象三：权限点 (Permission)】
细粒度原子权限枚举：
- `keyword:manage`：关键词词库导入、新增、修改与导出。
- `ai:generate`：触发语料提纯、大模型文章生成与 FAQ 生成。
- `article:edit`：编辑保存文章、更新元数据。
- `preview:view`：查看本地项目站点预览。
- `report:view`：查看 GEO 分析评测报告。

---

## Interface (接口/API/前端组件设计)

### 0. 身份解析与权威源（Authority of Truth）

**铁律：本地花名册 `data/rbac_members.json` 是权限的唯一权威源，上游小毛驴返回的 `role` 一律不采信。**

现状风险：`server.py` 在多处直接把上游字段写进会话——`server.py:126/309/363` 均为 `role = data.get("role", "user")`。若上游某天返回 `admin`，越权即刻成立。因此：

1. 上游只提供「这个人是谁」（`user_id` / `phone` / `name`），**不提供「这个人能干什么」**；
2. 每次请求以身份主键查花名册，命中 `developer_phones` → 开发者；命中 `members` 且 `status == "active"` → 运营人员；都未命中 → 401 并提示联系管理员；
3. 会话里仍可保留上游 `role` 字段用于展示，但**不得参与任何鉴权判定**。

**身份主键：以 `user_id` 为首选，`phone` 为兜底。**

- 理由一：`/api/auth/me` 目前是纯透传（`server.py:2612-2621`），直接返回上游原始字段，**不保证有 `phone`**；而 `auth_sso.py:99-105` 已强制把雪花 ID 规范化为字符串，`user_id` 天然稳定且无 JS 精度问题。
- 理由二：手机号存在换号/换绑场景，换号即失权，运营不可接受。
- 实现：花名册成员同时存 `user_id` 与 `phone`；解析时先按 `user_id` 精确匹配，未命中再按 `phone` 匹配，两者都空则拒绝。

### 1. 认证与状态同步接口

> **订正**：前端实际只调用 `/api/auth/status`（`web/index.html:5411`、`:11554`），从未调用 `/api/auth/me`。两者都要扩展，但**`/api/auth/status` 是前端唯一数据来源，必须优先**。

#### `GET /api/auth/status`（前端唯一依赖，必须扩展）
在现有返回（`authenticated` / `username` / `user_id` / `role` / `credits` / `token` / `repo_root` / `cd_cmd`）基础上追加：

```json
{
  "authenticated": true,
  "user_id": "1829384756102938475",
  "is_developer": false,
  "allowed_projects": ["nextgeo"],
  "permissions": ["keyword:manage", "article:edit", "preview:view"]
}
```

#### `GET /api/auth/me`（同步扩展，字段保持一致）
返回当前登录用户的身份、管辖项目与权限：
```json
{
  "code": 0,
  "data": {
    "is_logged_in": true,
    "user": {
      "user_id": "1829384756102938475",
      "phone": "13912345678",
      "name": "李四",
      "role": "operator",
      "is_developer": false,
      "allowed_projects": ["nextgeo"],
      "permissions": ["keyword:manage", "article:edit", "preview:view"]
    }
  }
}
```

### 2. 开发者专属成员管理接口 (需要 `require_developer` 鉴权)

- `GET /api/admin/members`：获取所有协作人员列表。
- `POST /api/admin/members`：新增协作人员。
  - 请求体：`{ "phone": "13912345678", "name": "李四", "allowed_projects": ["nextgeo"], "permissions": ["keyword:manage", "article:edit"] }`
- `PUT /api/admin/members/<phone>`：修改协作人员信息（修改姓名、项目、权限、启停状态）。
- `DELETE /api/admin/members/<phone>`：删除协作人员。

### 3. 统一路由守卫（Route Guard）—— 本期核心架构决策

> **为什么不能用「逐接口埋点」**：`tools/geo/server.py` 实测有 **237 个 API 路由分支**，其中约 180 个形如 `/api/projects/{id}/xxx`。逐分支补 `if` 必然漏改、且把 5630 行文件继续撑大。必须在分发层做集中拦截。

守卫挂载点：`do_GET` / `do_POST` / `do_PUT` / `do_DELETE` 各自的 **`check_auth()` 通过之后、进入路由 if 链之前**，统一调用一次 `guard_route(path, method) -> (ok, http_status, msg)`。

判定顺序（前一档命中即返回，不再下探）：

| 档位 | 匹配规则 | 判定 | 示例 |
|---|---|---|---|
| A 公开白名单 | `ROUTE_PUBLIC` 集合 | 直接放行 | `/api/auth/login`、`/api/auth/wechat-qr`、`/api/v1/community/auth/wx-login`、`/api/share/**`、`/api/llm/status` |
| B 开发者专属 | `ROUTE_DEVELOPER` 集合 | `require_developer`，非开发者 403 | `/api/admin/**`（成员管理）、`/api/llm/config`（写 API Key）、`/api/projects/{id}/delete`（`shutil.rmtree` 删库）、`POST /api/projects`（建项目）、`/api/settings/notifications`、`/api/patrol/trigger`、`/api/batch/trigger` |
| C 项目级 | 正则 `^/api/(v1/)?projects/([^/]+)/` | 提取 `project_id` → `require_project_access`；再按 `ROUTE_PERMISSION` 表查该动作所需原子权限 → `require_permission` | `/api/projects/{id}/facts/confirm-all` → `article:edit` |
| D 兜底 | 未登记且非项目级 | **fail-closed：仅开发者可用** | — |

**未登记路由的默认行为 = fail-closed（仅开发者）**。这是安全默认值；灰度期可用日志 `WARNING` 记录命中 D 档的路由，由开发者补齐登记后再放开。

### 4. 业务拦截与权限卡点

在 `tools/geo/rbac.py` 中实现，供上一节守卫调用：
- `verify_project_access(current_user, project_id)`：
  - 若 `current_user.is_developer == True`，放行。
  - 若 `project_id in current_user.allowed_projects`，放行。
  - 否则抛出 `403 Forbidden: 无权访问该项目`。
- `verify_permission(current_user, permission_code)`：
  - 若 `current_user.is_developer == True`，放行。
  - 若 `permission_code in current_user.permissions`，放行。
  - 否则抛出 `403 Forbidden: 缺少相应操作权限`。
- `verify_developer_only(current_user)`：
  - 仅允许 `role == "developer"`，用于生产发布（`/api/admin/deploy`）、配置修改与人员管理。

### 5. 前端组件与视图裁剪设计

1. **项目切换下拉框 (Project Selector)**：
   - 开发者：展示系统中全部项目（`outputs/` 扫描到的所有项目）。
   - 运营人员：根据 `allowed_projects` 过滤，仅渲染其被授权的项目；默认选中首个有权项目；禁止通过 URL 参数篡改访问未授权项目。
2. **顶部导航栏 (Navbar)**：
   - 运营人员隐藏：“成员管理”按钮、“系统设置”按钮、“发布生产”按钮。
   - 仅保留自身有权访问的 Tab（如词库、文章、报告）。
3. **按钮级权限置灰/隐藏 (Button Policy)**：
   - 针对未授权的操作按钮（如未被授权 `ai:generate` 则将“开始提纯生成”按钮隐藏或置灰提示）。
4. **开发者成员管理面板 (Modal / Page)**：
   - 表格呈现当前所有成员；
   - 支持快捷添加、编辑、启用/停用、删除；
   - 项目选择支持多选；权限选项提供全选/单选勾选框。

---

### 6. 本地免登通道与网络绑定收敛（安全前提）

当前实现存在两处会把 RBAC 整体架空的现状，必须先收敛，否则上层鉴权形同虚设：

1. **本地免登无条件发放 admin**（`server.py:2584-2589`）：
   `/api/auth/status` 在 `is_local_dev_request()` 为真时，任何无 token 请求都会被自动 `create_session("本地开发者", phone="13150568888", role="admin")`。任何人只要能访问到本机的 loopback + `Host: localhost`，就自动是开发者。
   收敛方案：免登通道保留，但身份改为从 `data/rbac_members.json` 的 `developer_phones[0]` 解析；若花名册不存在或为空，**降级为「未授权运营」而非开发者**，并打 WARNING。
2. **服务默认绑定 `0.0.0.0`**（`server.py:5610` 的 `server_address = ("", port)`）：
   与 `AGENTS.md` 第 4 节「开发一律仅在 `127.0.0.1:8088` 验证」不符，管理端实际暴露在所有网卡。
   收敛方案：默认改为 `127.0.0.1`，通过环境变量 `GEO_BIND_HOST` 显式覆盖（生产反代场景时才设为 `0.0.0.0`），且覆盖时在启动横幅打印醒目提示。

---

## Database Schema / Data Structure (数据模型变更)

使用轻量级 JSON 持久化存储于本地文件：`data/rbac_members.json`。
无需引入外部复杂数据库，保证离线与极简可维护性。

**结构约束（消除双真源）：**
- 开发者**只**存在于 `developer_phones`，**不写入 `members`**；`members` 只放运营人员。开发者身份禁止通过任何 API 增删改，只能手工改文件。
- `role` 字段在 `members` 中恒为 `"operator"`，保留仅为可读性，不参与判定。
- `developer_phones` 与 `server.py:2588` 的本地免登硬编码 `13150568888` **必须统一到本文件**，禁止再出现第二处硬编码。

```json
{
  "schema_version": 1,
  "developer_phones": [
    "13150568888"
  ],
  "members": [
    {
      "user_id": "1829384756102938475",
      "phone": "13900000001",
      "name": "运营同事小张",
      "role": "operator",
      "status": "active",
      "allowed_projects": ["nextgeo"],
      "permissions": [
        "keyword:manage",
        "ai:generate",
        "article:edit",
        "preview:view",
        "report:view"
      ],
      "created_at": "2026-09-18 17:30:00",
      "updated_at": "2026-09-18 17:30:00"
    }
  ]
}
```

### 并发写入约定（必须实现）

现有 `save_sessions()`（`server.py:72-78`）是**无锁裸写且静默吞异常**，多端/多线程同时写会丢数据，`rbac_members.json` 不得照抄。要求：

1. 模块级 `threading.RLock()` 包住读-改-写全过程；
2. 写入采用「临时文件 + `os.replace`」原子替换，杜绝写一半崩溃导致花名册损坏；
3. 文件缺失或 JSON 解析失败时，回退到内置默认结构（`developer_phones` 取既有值，`members` 为空）并打 WARNING，**不得抛异常导致整个管理端 500**。

