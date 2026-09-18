# Proposal: 运营人员只读路由放行与管理入口隐藏修复

## Why (为什么做)
在刚刚上线的运营人员权限隔离与多租户协作版本中，给同事开通运营账号后，同事登录工作台遇到了三大严重体验问题，复审中又确认一处鉴权门前的站点越权面：
1. **首页一进来就报错 403**：仪表盘自动请求里，`GET /api/ops/check-ledger`、`GET /api/partners`、`GET /api/settings/notifications` 被误判成开发者专属。
2. **管理入口没藏住**：`#home-sidebar .sidebar-nav-item { display: flex }` 压过普通 `.hidden`，「系统设置」「成员管理」仍对运营可见。
3. **管理按钮缺乏权限感知**：「新建客户」「批量并发」对运营可见，点了只会 403。
4. **鉴权门前站点路由裸奔（复审新增）**：`GET …/site/preview|status|download` 写在 `do_GET` 鉴权门之前，未登录即可按 `project_id` 拉取整站 HTML、文件清单甚至源码 ZIP；真正的公开交付面是 `/sites/{id}/`，管理台预览不应裸奔。

## What Changes (改动了什么)
1. **后端只读路由放行（读写拆开）**：三条首页 GET 进 `ROUTE_AUTHENTICATED`；写操作仍开发者专属；台账按 `allowed_projects` 裁剪。
2. **站点预览收入鉴权门（方案 A）**：三处站点分支移到鉴权门后；`preview`/`status`/静态资源按项目级 `preview:view`；`site/download` 开发者专属；`/api/auth/status` 免登建会话时补发 `Set-Cookie`，保证 iframe 预览可用。公开面 `/sites/{id}/` 不动。
3. **前端 CSS 定点加强 + 高危按钮打标**：禁止全局 `.hidden !important`；新建客户、批量并发、合作方分组等 `data-geo-dev-only`。
4. **测试**：读放行、写拦截、台账裁剪、未登录站点 401、运营跨项目预览 403、运营 download 403。

## Capabilities (新增或修改的对外能力)
- 运营流畅使用工作台：首页不弹开发者专属 403；台账只看自己的客户。
- 使用者视角：设置/成员/合作方名册维护/新建客户/批量并发入口不可见。
- 管理台站点预览需登录且受项目白名单约束；未登录不可枚举客户站。

## Impact (受影响的部分)
- `tools/geo/rbac.py`、`tools/geo/server.py`、`web/geo-admin.css`、`web/index.html`、`tests/test_rbac.py`
