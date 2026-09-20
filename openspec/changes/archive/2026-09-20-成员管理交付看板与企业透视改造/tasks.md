# 细分任务清单：成员管理交付看板与企业透视改造

- [x] 1. 后端 RBAC 与成员透视服务升级 (`tools/geo/rbac.py` & `tools/geo/server.py`)
  - [x] 1.1 在 `tools/geo/rbac.py` 新增 `assign_member_project` / `unassign_member_project`（`_ROSTER_LOCK` 内原子操作；分配优先复用或包一层 `append_member_allowed_project`，禁止第三套读写）
  - [x] 1.2 调整 `upsert_member`：开通默认赋予全部 `PERMISSION_CODES`；仅凭手机号可开通（`user_id` 可空）
  - [x] 1.3 **新增首次登录回写**：手机号命中运营成员且会话带 `user_id`、花名册该行 `user_id` 为空时，加锁写回落盘（自建标签前置条件）
  - [x] 1.4 `GET /api/admin/members` 在现有 `members` 数组上富化透视（保留 `developer_phones` / `permission_codes`）：名称 / `creator_user_id` 自建判定 / `probe_status`（仅 `unprobed|baseline_ready|awaiting_retest`）；进度与 `GET /api/projects` 同算法扫 `outputs/`；`updated_at` 用文件 mtime
  - [x] 1.5 实现 `POST .../members/{key}/projects` 与 `DELETE .../members/{key}/projects/{project_id}`；**路由顺序**先收回项目、再删成员
- [x] 2. 前端成员交付看板重构 (`web/index.html`)
  - [x] 2.1 清掉顶部大表单、多选框和 5 权限复选框
  - [x] 2.2 右上角【+ 新增成员】弹窗（姓名 + 手机号）
  - [x] 2.3 成员卡片流（负责 X 家、自建 Y 家、分配 Z 家）
  - [x] 2.4 企业透视条：`[自建]` / `[老板分配]`；进度用白话（禁止主文案「SOP」）；活动时间
  - [x] 2.5 【+ 分配企业】下拉速选与【× 收回】
- [x] 3. 自动化测试与验收
  - [x] 3.1 `tests/test_member_dashboard_and_perspective.py`：透视聚合、自建只认 `creator_user_id`、分配/收回、极简开通、登录回写 `user_id`、进度算法、0 Emoji、界面无「SOP」主文案
  - [x] 3.2 相关回归（含 `test_rbac.py`）全绿
  - [x] 3.3 本地 `:8088` 实机验收
