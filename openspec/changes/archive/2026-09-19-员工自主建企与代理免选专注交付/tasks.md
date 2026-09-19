# 细分任务清单：员工自主建企与代理免选专注交付

- [x] 1. 后端 RBAC 路由与花名册自动绑定 (`tools/geo/rbac.py` & `tools/geo/server.py`)
  - [x] 1.1 从 `ROUTE_DEVELOPER_VERBS` 移除 `("/api/projects", "POST")` 与 `("/api/v1/projects", "POST")`
  - [x] 1.2 **同时**把上述两条加入 `ROUTE_AUTHENTICATED`（只删开发者名单不够，否则 fail-closed 仍 403）
  - [x] 1.3 新增 `append_member_allowed_project`（锁内原子追加）；找不到成员返回 False
  - [x] 1.4 `POST /api/projects`：运营强制 `partner_id=""`；落盘后追加管辖；追加失败须明确报错（勿假装可进项目）
- [x] 2. 前端专注型界面与 Client ID 自动生成 (`web/index.html`)
  - [x] 2.1 【新建客户】去掉 `data-geo-dev-only`
  - [x] 2.2 `#np-partner` 外层加 `data-geo-dev-only`
  - [x] 2.3 确认列表筛选/表头 `data-geo-dev-only` + `renderEnterprisesTable` 的 `isDeveloper()` 已隐藏合作方列（勿弄乱 colspan）
  - [x] 2.4 Client ID 自动预填（零新依赖；手改后停止覆盖）
  - [x] 2.5 建企成功后先刷新 `/api/auth/status` 再进阶段零
- [x] 3. 自动化测试与验证
  - [x] 3.1 `tests/test_employee_creation_and_partner_isolation.py`：路由放行、`partner_id` 置空、追加管辖、追加失败语义、0 Emoji
  - [x] 3.2 相关单测全部通过（OK）
  - [x] 3.3 本地 `:8088` 用 `13805206070` 验收：能建企、看不见合作方、建完能进阶段零
