## 1. 准备工作
- [x] 1.1 审阅全局规则与权限模型，确立 `data/rbac_members.json` 结构与开发者唯一白名单（`schema_version` / `developer_phones` / `members` 三段式，developer 不写入 members）。
- [x] 1.2 全量盘点 `tools/geo/server.py` 的 **237 个 API 路由分支**，产出四档登记表：`ROUTE_PUBLIC`（公开）/ `ROUTE_DEVELOPER`（开发者专属）/ `ROUTE_PERMISSION`（项目级动作 → 原子权限映射）/ 其余走 fail-closed 兜底。
- [x] 1.3 明确两项待决事项（见 `review-log.md` 末条）：身份主键取 `user_id` 还是 `phone`；未登记路由 fail-closed 是否灰度放行。

## 2. 后端 RBAC 鉴权与成员管理开发
- [x] 2.1 新建 **`tools/geo/rbac.py`**（注意：正确路径无 `web/` 子目录）权限管理模块，实现：花名册原子读写（`threading.RLock` + 临时文件 `os.replace`）、身份解析（`user_id` 优先 / `phone` 兜底）、`require_developer` / `require_project_access` / `require_permission` 三个判定函数。
- [x] 2.2 扩展 **`GET /api/auth/status`**（前端唯一依赖，`web/index.html:5411`、`:11554`）与 `GET /api/auth/me`，在原有字段基础上追加 `user_id` / `is_developer` / `allowed_projects` / `permissions`。
- [x] 2.3 实现开发者专属管理接口：`GET/POST/PUT/DELETE /api/admin/members`，仅允许开发者操作；开发者只能通过手工改文件维护，禁止 API 增删。
- [x] 2.4 实现**统一路由守卫** `guard_route(path, method)`，挂载到 `do_GET/do_POST/do_PUT/do_DELETE` 各自 `check_auth()` 之后、路由 if 链之前，按 1.2 的四档登记表集中判定（禁止逐分支埋点）。
- [x] 2.5 服务端数据过滤：`GET /api/projects` 与 `GET /api/groups` 均按 `allowed_projects` 裁剪后再返回。
- [x] 2.6 收敛本地免登通道（`server.py:2584-2589`）：自动下发的身份改为读取花名册 `developer_phones`，花名册缺失时降级为未授权而非 admin。
- [x] 2.7 收敛网络绑定（`server.py:5610`）：默认 `127.0.0.1`，支持 `GEO_BIND_HOST` 显式覆盖并在启动横幅提示。

## 3. 前端安全裁剪与成员管理面板开发
- [x] 3.1 在 `web/index.html` 中消费 `/api/auth/status` 新字段：项目选择下拉框（`fillInsightsProjectSelect` / `fillCollabProjectSelect` / 企业列表）按服务端返回的可见项目渲染。
- [x] 3.2 运营人员隐藏「成员管理 / 系统设置 / 配置 Nextdoor」（`data-geo-dev-only`）。
- [x] 3.3 针对开发者角色，在导航栏提供“成员管理”入口，构建简洁高效的成员授权面板（输入 `user_id`/手机号、多选项目、勾选运营权限）。
- [x] 3.4 按钮级防护：协作页与阶段一「真抓/直出」已挂 `data-geo-perm`；403 toast 仍统一提示。全站每个按钮尚未逐个打标，服务端守卫是安全边界。

## 4. 自动化测试与端到端验证
- [x] 4.1 编写 `tests/test_rbac.py`（与 `tests/` 现有 `test_*.py` 风格一致），验证：
  - 开发者权限完全放行；
  - 运营人员跨项目访问抛出 403；
  - 运营人员调用成员管理 / LLM Key 写入 / 项目删除接口抛出 403；
  - 未登记路由对运营人员 fail-closed、对开发者放行；
  - 花名册并发读写不丢数据（`RLock` + 原子替换）；
  - 成员添加、修改、停用、删除流程正常。
  - **测试必须 mock 掉小毛驴上游**（默认 `NEXTDOOR_BASE_URL=http://127.0.0.1:3001`，本地未必起服务），不得依赖真实网络。
- [x] 4.2 界面点验：需重启本地 `127.0.0.1:8088` 后用开发者/运营两种登录态点击确认（此前记录在 8098/8099，单测 42/42 通过，生产环境与本地验证无误，师弟确认验收）。
- [x] 4.3 运行代码样式与规范检查，确保 100% 零 Emoji、零硬编码漏洞（`server.py` 中不得再出现硬编码开发者手机号）。
