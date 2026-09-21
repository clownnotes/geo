## 1. 准备与梳理
- [x] 1.1 确认现有前端 `web/index.html` 中所有导航项与仪表盘按钮的 `data-geo-dev-only` 标记状态。
- [x] 1.2 核对当前测试用例中与「运营」/「写文」相关的断言，准备回归脚本。

## 2. 界面与导航纯粹化（前端改造）
- [x] 2.1 修改 `web/index.html`：在侧边栏「运维告警」(`nav-home-ops`) 按钮上添加 `data-geo-dev-only` 标记，对写文同事彻底隐藏。
- [x] 2.2 修改 `web/index.html`：在侧边栏「合作方名册」(`nav-home-partners`) 按钮上添加 `data-geo-dev-only` 标记，对写文同事彻底隐藏。
- [x] 2.3 修改 `web/index.html`：在仪表盘上方真机作业引导卡片的「检测台账详情」按钮上添加 `data-geo-dev-only` 标记，对写文同事隐藏。
- [x] 2.4 修改 `web/index.html`：修改左下角身份展示文案与成员管理相关文案，将「运营同事」统一更名为「写文同事」。
- [x] 2.5 修改 `web/index.html`：在 `switchHomeView` 路由跳转中对 `home-ops` 与 `home-partners` 增加非开发者拦截与兜底重定向，防止 URL Hash 强跳。
- [x] 2.6 修改 `web/index.html`：对阶段五验收页及辅助抽屉中的「下载全套成果 ZIP」和「归档 ZIP」按钮添加 `data-geo-dev-only`，避免写文同事在验收阶段误触开发者专属接口。

## 3. 花名册与后端配置兼容性
- [x] 3.1 检查并更新 `data/rbac_members.json`，确保成员示例和文案统一为「写文同事」。
- [x] 3.2 检查 `tools/geo/rbac.py` 中的日志文案与默认配置，确保语义清晰一致。

## 4. 自动化测试与验证
- [x] 4.1 新增/更新单测 `tests/test_writer_perspective.py`：
  - 模拟「写文同事」登录，断言进入仪表盘时不会触发任何开发者专属接口（403 为 0 次）；
  - 断言「运维告警」、「合作方名册」、「商业洞察」等非写文入口在 DOM 中带有 `data-geo-dev-only` 并正确隐藏；
  - 断言「下载全套成果 ZIP」按钮在写文同事视角下正确隐藏；
  - 断言写文同事能正常读取管辖企业列表、触发真机实测回填以及进行文章生成编辑。
- [x] 4.2 运行全量测试套件（`test_rbac.py`、`test_operator_dashboard_perspective.py` 等），确保无回归破坏。
