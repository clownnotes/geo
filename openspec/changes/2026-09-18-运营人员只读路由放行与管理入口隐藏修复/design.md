# Design: 运营人员只读路由放行与管理入口隐藏修复

## 1. 架构目标与设计原则
- **读写分离鉴权**：只读展示类接口对已登录运营开放；高危写操作严格开发者专属。
- **多租户裁剪优先于「已登录即可」**：台账等返回项目行的接口，运营侧必须按 `allowed_projects` 过滤。
- **鉴权门必须罩住管理台项目 API**：`/api/projects/{id}/site/*` 属工作台能力，不是公开交付面；公开交付面仅 `/sites/{id}/`（含尾斜杠 301）。
- **CSS 定点加固**：禁止全局 `.hidden { display: none !important }`。

---

## 2. 后端路由登记表重构 (`tools/geo/rbac.py`)

### 2.1 首页只读放行
| 路由 | 方法 | 新集合 | 说明 |
| :--- | :--- | :--- | :--- |
| `/api/ops/check-ledger` | `GET` | `ROUTE_AUTHENTICATED` | 响应须按身份裁剪 |
| `/api/partners` | `GET` | `ROUTE_AUTHENTICATED` | 企业管理下拉 |
| `/api/settings/notifications` | `GET` | `ROUTE_AUTHENTICATED` | `loadPatrolStatus` 只读 |
| `/api/settings/notifications` | `POST` | `ROUTE_DEVELOPER_VERBS` | 现码写配置为 POST |
| `/api/settings/notifications/test` | * | `ROUTE_DEVELOPER` | 试发 |
| `/api/partners` | `POST` | `ROUTE_DEVELOPER_VERBS` | 创建 |
| `/api/partners/{id}` | `POST` | 前缀开发者或 fail-closed+单测 | 改名/归档；无 PUT/DELETE |
| `/api/patrol/trigger`、`/api/batch/trigger`、`/api/ops/check-logs`、`/api/llm/config` | * | 仍开发者 | 不变 |

**判定顺序**：须先从 `ROUTE_DEVELOPER` 字符串集合删除已拆出的 GET 路径，否则 B 档仍会 403。

### 2.2 伪代码（只读 + 写）
```python
ROUTE_AUTHENTICATED = frozenset({
    ("/api/projects", "GET"),
    ("/api/v1/projects", "GET"),
    ("/api/groups", "GET"),
    ("/api/partners", "GET"),
    ("/api/ops/check-ledger", "GET"),
    ("/api/settings/notifications", "GET"),
})

ROUTE_DEVELOPER = frozenset({
    "/api/llm/config",
    "/api/settings/notifications/test",
    "/api/patrol/trigger",
    "/api/batch/trigger",
    "/api/ops/check-logs",
})

ROUTE_DEVELOPER_VERBS = frozenset({
    ("/api/projects", "POST"),
    ("/api/v1/projects", "POST"),
    ("/api/partners", "POST"),
    ("/api/settings/notifications", "POST"),
})

ROUTE_DEVELOPER_SUFFIXES = (..., "/site/download")  # 已有，保持

# 合作方改档：path.startswith("/api/partners/") 且非 GET -> 开发者
# 或依赖 D 档 fail-closed，单测锁死 POST /api/partners/{id}
```

### 2.3 台账多租户裁剪
`build_check_ledger` 之后按身份过滤：
1. 开发者：全量。
2. 运营：滤 `rows`，再重算 `summary`。
3. 单测：仅授权 `nextgeo` 时不得出现其他 `project_id`。

---

## 3. 站点预览收入鉴权门（方案 A，已定）

### 3.1 决策
采用 **方案 A**：把下列分支从 `do_GET` 鉴权门之前整体移到 `check_auth` + `rbac_guard` 之后：
- `/api/projects/{id}/site/preview` 与 `/site/{asset}`
- `/api/projects/{id}/site/status`
- `/api/projects/{id}/site/download`

公开面 `/sites/{id}/` **不改动**。

### 3.2 权限映射
| 路径 | 判定 |
| :--- | :--- |
| `…/site/preview`、`…/site/{asset}`、`…/site/status` | 项目级 + `preview:view`（现有子串/后缀已覆盖，守卫生效即可） |
| `…/site/download` | 开发者专属（已在 `ROUTE_DEVELOPER_SUFFIXES`） |

### 3.3 iframe 会话（风险 A1）
管理台用 `<iframe src="/api/projects/{id}/site/preview">`，只带 Cookie。  
`GET /api/auth/status` 在本地免登（或任意已发出 `token` 的成功会话）时，若响应体带 `token`，须同步 `Set-Cookie: geo_token=…; Path=/; HttpOnly`（与 login 一致），避免加鉴权后预览 401。

---

## 4. 前端样式与入口裁剪

```css
#app-sidebar .sidebar-nav-item.hidden,
#home-sidebar .sidebar-nav-item.hidden,
[data-geo-dev-only].hidden {
  display: none !important;
}
```

打标：`新建客户`、`批量并发`、合作方管理大分组；系统设置/成员管理保持现有 `data-geo-dev-only`。文案用「运维告警」。

---

## 5. 自动化测试
新增（不写死旧编号）：
1. 运营 GET 台账 / partners / notifications → 放行；台账无未授权项目。
2. 运营 POST partners（含带 id）、写通知、batch → 403。
3. 未登录 GET site/preview|status|download → 401。
4. 运营跨项目 site/preview → 403；运营 site/download → 403。
5. 全量 `test_rbac` 通过。
