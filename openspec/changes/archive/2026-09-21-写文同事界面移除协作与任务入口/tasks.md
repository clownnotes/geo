# Tasks: 写文同事界面移除协作与任务入口

- [x] 1. 前端侧边栏与视图守卫修改
  - [x] 1.1 在 `web/index.html` 的 `#nav-home-collab` 上添加 `data-geo-dev-only` 标记
  - [x] 1.2 在 `web/index.html` 的 `switchHomeView` 与 `showDashboard` 守卫中，将 `'home-collab'` 加入 `devOnlyViews`
- [x] 2. 自动化测试与验证
  - [x] 2.1 编写测试验证写文同事无法在侧边栏看到「协作与任务」，且路由强制跳转被回退到仪表盘（`test_writer_perspective.py`）
  - [x] 2.2 执行全套自动化测试回归（67 项 RBAC 测试 + 7 项写文视界测试全绿）
- [x] 3. 结果汇报与人工验收
  - [x] 3.1 向用户汇报改动并通过人工验收（用户显式执行 /opsx-archive）
