## 1. 总门

- [x] 1.1 在 `tools/geo/server.py` 增加 `console_gate`：白名单见 `design.md` 第 2 节；其余必须已登录且花名册能对上人。
- [x] 1.2 `do_GET` / `do_POST` / `do_PUT` / `do_DELETE` 开头先调用总门；未过门的网页只回 `web/login.html`，其它 404。
- [x] 1.3 删除 `super().do_GET()` 兜底，以及 `/docs`、`/llms.txt`、`/api/benchmark` 的未登录放行。
- [x] 1.4 关掉本机自动发登录票（`/api/auth/status` 不再因 127.0.0.1 创建会话）；未登录的 status 不返回仓库路径和管辖项目。

## 2. 登录页

- [x] 2.1 新建 `web/login.html`：只有手机号、密码、扫码。样式写在页面里。不含工作台、提示词、内部接口清单。
- [x] 2.2 登录成功写 Cookie 后刷新 `/`，总门才下发 `web/index.html`。退出清 Cookie，回到登录页。

## 3. 验收（无 Cookie）

- [x] 3.1 下列全部 404 或登录页，响应里不得出现工作台标记、密钥、花名册、源码：`/`、`/web/index.html`、`/.env`、`/tools/geo/server.py`、`/AGENTS.md`、`/data/rbac_members.json`、`/sites/nextgeo/`、`/docs/`、`/llms.txt`、`/api/projects`、`/api/benchmark/industries`。
- [x] 3.2 用账号登录后，`/` 能进工作台；员工仍只能看自己的客户。
- [x] 3.3 退出后上述地址再次打不开。
