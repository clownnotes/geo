# Tasks: 运营端仪表盘角色视角改造与待办台账

## 1. 方案评审与决策对齐 (Review & Decision)
- [x] 1.1 产品拍板实施 **方案 A**（方案 B 本轮不采用），已写入 `proposal.md` / `design.md` / `review-log.md`；
- [x] 1.2 确认运营端指标：四宫格为「我的管辖企业 / 待真机实测 / 未完成交付 / **声量异常数**」；彻底排除估值与 ROI；界面禁用「SOP」主文案与 Emoji；
- [x] 1.3 确认待办行必须展示豆包位次、声量、异动标记；易混淆按钮必须有白话帮助；

## 2. 前端骨架与样式适配 (UI Scaffolding)
- [x] 2.1 修改 `web/index.html`：在 `panel-home-dashboard` 注入运营端专属四宫格 + `ops-action-list`（方案 A）；开发者区继续 `data-geo-dev-only`；
- [x] 2.2 弱化/隐藏运营视图中的「机器全量巡检」误导文案；明确「真机实测回填」动作引导；
- [x] 2.3 按 `design.md` §2.5 为四宫格、灯色徽章、「去真机回填」「进入流水线」「声量异常」等控件补齐 `title` / 问号气泡白话帮助；

## 3. 权限逻辑与数据装配 (Frontend Logic)
- [x] 3.1 改造 `applyRbacUi()`：开发者 ↔ 运营容器互斥显示；运营端不调用财务大盘接口；
- [x] 3.2 实现 `renderOpsDashboard()`：聚合管辖企业的真机台账（`never`/`overdue`）、阶段未完、声量异常数；
- [x] 3.3 待办行按 `design.md` §2.3 渲染：灯色、豆包位次、SOV、异动原因、优先排序与主按钮；
- [x] 3.4 运营登录/刷新后默认进入仪表盘（方案 A 落地页）；
- [x] 3.5 **[opsx-fix]** 「去真机回填」改为 `openManualCheckForProject` → 打开粘贴框，禁止 `enterWizard(..., 5)`；

## 4. 自动化回归测试与验收 (Testing & Verification)
- [x] 4.1 编写/更新 `tests/test_operator_dashboard_perspective.py`：断言运营 DOM 无金额/ROI、含声量异常四宫格与待办行关键字段、含帮助属性；并断言真机按钮不进阶段五；
- [x] 4.2 本地双账号目测（http://127.0.0.1:8088，Safari）：运营点「去真机回填」应弹出粘贴框；开发者看财务大盘；
- [x] 4.3 自动化确认 0 Emoji、无「SOP」主文案、第四格为「声量异常数」。
