## 1. 后端鉴权与多租户裁剪
- [x] 1.1 调整 `tools/geo/rbac.py`：将 `GET /api/ops/check-ledger`、`GET /api/partners`、`GET /api/settings/notifications` 移入 `ROUTE_AUTHENTICATED`；并从 `ROUTE_DEVELOPER` 字符串集合中删除这三条路径。
- [x] 1.2 合作方写：`POST /api/partners` 纳入 `ROUTE_DEVELOPER_VERBS`；`POST /api/partners/{id}` 明确为开发者专属（前缀或 fail-closed + 单测）。不登记不存在的 `PUT`/`DELETE`。
- [x] 1.3 通知写：`POST /api/settings/notifications` 进 `ROUTE_DEVELOPER_VERBS`；`/test` 仍 `ROUTE_DEVELOPER`。
- [x] 1.4 `check-ledger` 响应按 `identity` 过滤 `rows` 并重算 `summary`。
- [x] 1.5 `server.py`：将 `site/preview`（含 asset）、`site/status`、`site/download` 三处分支整体移到 `do_GET` 鉴权门（`check_auth` + `rbac_guard`）之后；公开面 `/sites/{id}/` 不动。
- [x] 1.6 确认 `site/preview|status|asset` 走项目级 `preview:view`；`site/download` 走 `ROUTE_DEVELOPER_SUFFIXES`（开发者专属）。
- [x] 1.7 `GET /api/auth/status` 在已发出 `token` 的成功响应上补发 `Set-Cookie: geo_token=…; Path=/; HttpOnly`，保证 iframe 预览带会话。

- [x] 1.5 `server.py`：把站点路由三个分支（L3366 `site/preview` 与 `site/{asset}`、L3405 `site/download`、L3444 `site/status`）整体移到鉴权门之后，交由统一守卫判定。
- [x] 1.6 `rbac.py`：`/site/preview` 与 `/site/{asset}` 归入项目级 `preview:view`；`site/download` 归入**开发者专属**（不给 `report:view`，因为是整站源码 ZIP）。
- [x] 1.7 `server.py`：`GET /api/auth/status` 自动建会话时补发 `Set-Cookie: geo_token=…; Path=/; HttpOnly`，保证免登场景 iframe 预览可用。

## 2. 前端样式与视觉入口收敛
- [x] 2.1 `web/geo-admin.css` 定点规则（禁止全局 `.hidden !important`）。
- [x] 2.2 `web/index.html`：「新建客户」「批量并发」加 `data-geo-dev-only`。
- [x] 2.3 `web/index.html`：侧边栏「合作方管理」大分组加 `data-geo-dev-only`。

## 3. 自动化测试与验证
- [x] 3.1 `tests/test_rbac.py`：台账/合作方/通知 GET 放行；写拦截；台账裁剪。
- [x] 3.2 补：未登录站点路由 → 401；运营跨项目 preview → 403；运营 download → 403。
- [x] 3.3 跑通 `python3 -m unittest tests.test_rbac`；确认无 Emoji 违规。
