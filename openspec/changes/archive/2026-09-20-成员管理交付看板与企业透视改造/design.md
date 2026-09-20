# OpenSpec 技术架构设计：成员管理交付看板与企业透视改造

> 对应变更目录：`openspec/changes/2026-09-20-成员管理交付看板与企业透视改造`

---

## 1. 面向对象抽象设计

### 1.1 对象、属性与行为 (面向对象三问)

#### 对象 1：`MemberDeliveryCard`（成员交付看板卡片）
- **对象是什么**：代表一个运营人员及其在 GEO 系统内承载的全部业务资产与交付大盘。
- **属性**：
  - `user_id`: 字符串（小毛驴唯一用户标识）
  - `phone`: 字符串（手机号，登录与匹配的核心标识）
  - `name`: 字符串（姓名/备注名）
  - `status`: 字符串（`active` 启用 / `disabled` 停用）
  - `projects`: `List[ProjectPerspectiveItem]`（名下管辖企业的详细透视图）
  - `total_count`: 整数（名下企业总数）
  - `self_created_count`: 整数（该员工自建企业数）
  - `assigned_count`: 整数（老板分配企业数）
- **行为**：
  - `assign_project(project_id)`：追加一家企业管辖权
  - `remove_project(project_id)`：收回一家企业管辖权

#### 对象 2：`ProjectPerspectiveItem`（企业透视条目）
- **对象是什么**：代表某员工名下负责的一家具体企业，带来源、进度与活动状态。
- **属性**：
  - `client_id`: 字符串（项目唯一代号，如 `xuzhou_tech`）
  - `client_name`: 字符串（企业全称/产品名，如 `示例科技（徐州）有限公司`）
  - `is_self_created`: 布尔值（是否由该员工本人创建）
  - `origin_label`: 字符串（"自建" 或 "老板分配"）
  - `probe_status`: 字符串（摸底状态，与现网一致：`unprobed` / `baseline_ready` / `awaiting_retest`）
  - `steps_done`: 整数（交付已完成步数，0~5；由 `outputs/` 的 `01_`～`05_` 计数得出，不读 yaml）
  - `progress_pct`: 整数（交付进度百分比，0~100）
  - `updated_at`: 字符串（该企业最近处理时间，取 yaml 或 `outputs/` 目录 mtime）

#### 对象 3：`RosterProjectAssignment`（管辖项目原子分配器）
- **对象是什么**：负责在 `_ROSTER_LOCK` 加锁保护下，对花名册 `allowed_projects` 进行原子读改写，杜绝并发覆盖。
- **行为**：
  - `assign_member_project(key, project_id) -> (bool, str)`
  - `unassign_member_project(key, project_id) -> (bool, str)`

---

## 2. 后端接口设计

所有成员管理写接口均锁死在 `ROUTE_DEVELOPER`，仅开发者总账号（师弟）享有操作权。

### 2.1 获取带企业透视的成员列表
- **路由**：`GET /api/admin/members`
- **处理逻辑**：
  1. 读取花名册 `load_roster()["members"]`；
  2. 预读各项目 `project.yaml`（抽 `client_id` / `client_name` / `creator_user_id` / `creator_name` / `probe_status`）并扫 `outputs/`；
  3. **进度不得读 yaml 里不存在的字段**：`steps_done` / `progress_pct` 必须与现有 `GET /api/projects` 同一套算法（看 `01_`～`05_` 产出文件计数，满 5 步即 100%）；`updated_at` 取 `project.yaml` 或 `outputs/` 目录最近修改时间，yaml 无该字段时不要空造；
  4. 遍历成员的 `allowed_projects`，组装 `projects: [ProjectPerspectiveItem]`：
     - **自建判定只认 `creator_user_id`**：`p.creator_user_id` 非空且等于该成员花名册 `user_id` → `is_self_created = True`；
     - **禁止**用 `creator_name == m.name` 当主规则（同名会串标）；姓名仅可作界面辅助展示，不作归属真源；
     - 其余一律 `is_self_created = False`（展示「老板分配」）；老项目无 `creator_user_id` 时也归「老板分配」，不猜；
  5. 响应 JSON：**在现有字段上富化，不另起新壳**：
     ```json
     {
       "success": true,
       "developer_phones": ["..."],
       "permission_codes": ["..."],
       "members": [MemberDeliveryCard, ...]
     }
     ```
     - 继续用 `members` 键（现前端 `d.members`）；每个成员在原有花名册字段之上增加 `projects` / `total_count` / `self_created_count` / `assigned_count`；
     - **禁止**改成只有 `data` 而丢掉 `members`，避免半改半留时读空表。

### 2.2 极简开通新成员
- **路由**：`POST /api/admin/members`
- **请求体**：
  ```json
  {
    "name": "李四",
    "phone": "13805206070",
    "allowed_projects": []
  }
  ```
- **处理逻辑**：
  - 开通时 `user_id` 允许留空，仅凭手机号入库（现有 `upsert_member` 已支持「手机号与 user_id 不能同时为空」）；
  - **必须补「首次登录回写 user_id」**（当前代码没有）：登录成功且按手机号命中运营成员、会话里带有小毛驴 `user_id`、花名册该行 `user_id` 仍为空时，在 `_ROSTER_LOCK` 内写回并落盘。否则建企写入的 `creator_user_id`（来自会话）永远对不上花名册，自建标签全废；
  - `permissions` 默认赋予 `PERMISSION_CODES` 全部五项交付原子权限；成员管理写接口仍锁 `ROUTE_DEVELOPER`，运营拿不到管理端；
  - `status` 默认 `active`。

### 2.3 快速追加分配企业
- **路由**：`POST /api/admin/members/{key}/projects`
- **请求体**：`{"project_id": "xuzhou_tech"}`
- **处理逻辑**：
  - 检查项目是否存在；
  - **优先复用**已有 `append_member_allowed_project`（或抽成其加锁兄弟函数 `assign_member_project`），禁止再写第三套读改写；
  - 在 `_ROSTER_LOCK` 内幂等追加 `allowed_projects`；
  - 落盘后返回最新透视条目。

### 2.4 快速收回企业管辖权
- **路由**：`DELETE /api/admin/members/{key}/projects/{project_id}`
- **处理逻辑**：
  - 在 `_ROSTER_LOCK` 内将 `project_id` 从该成员的 `allowed_projects` 剔除；
  - 落盘后返回成功状态；
  - **路由匹配顺序**：必须先匹配带 `/projects/` 的收回路径，再匹配现有 `DELETE /api/admin/members/{key}`（删整人），避免把 `.../projects/xxx` 误当成成员 key。

---

## 3. 前端交互与交付看板设计 (`web/index.html`)

### 3.1 废旧元素清理
- 彻底移除顶部的“新增 / 修改运营人员”表单卡片；
- 移除多选框 `<select multiple>`、18 位 user_id 必填项以及 5 个原子权限复选框。

### 3.2 全新看板结构
1. **顶部操作栏**：
   - 标题：“成员管理”
   - 说明：“查看员工交付大盘、透视自建与分配客户、一键增减客户管辖权。”
   - 右上角操作：【+ 新增成员】按钮（点击唤起弹窗）。
2. **新增成员模态框 (`#add-member-modal`)**：
   - 纯净双字段：姓名输入框 + 手机号输入框；
   - 底部操作：【取消】与【立即开通】；
3. **员工看板卡片流 (`#members-cards-container`)**：
   - 每个成员为一个独立卡片：
     - **卡片头部**：
       - 成员姓名（大号字体加粗） + 手机号（灰字） + 状态徽章（绿色“正常”/灰色“停用”）；
       - 右侧操作：【停用/启用】切换按钮、【删除成员】按钮；
     - **卡片统计栏**：
       - “负责客户 X 家（自建 Y 家 · 分配 Z 家）”
       - 右侧：【+ 分配企业】下拉速选（点击展开浮层，列出全部可选项目，支持实时搜索过滤，选中即添加）；
     - **客户透视网格**：
       - 每家企业展示为整洁的横条或微卡片：
         - 企业中文名 + 英文 slug；
         - 来源徽章：`[自建]` 或 `[老板分配]`（沿用现有管理台色板，不用新开紫色主题）；
         - 进度徽章（五年级白话，禁止主文案写「SOP」；`probe_status` 文案与首页企业列表对齐）：
           - `unprobed` → `还在豆包摸底`；
           - `baseline_ready` → `豆包答案已存进项目`；
           - `awaiting_retest` → `待复测`；
           - 交付中：`交付第 N 步 / 共 5 步 · 已完成 XX%`；
           - 满 5 步：`已结案`；
         - 最近活动时间（如 `10分钟前` 或真实日期）；
         - 右侧：【× 收回】小按钮，点击收回该项目管辖；
         - 点击企业行可直接跳转进入流水线查看其真实交付成果。
