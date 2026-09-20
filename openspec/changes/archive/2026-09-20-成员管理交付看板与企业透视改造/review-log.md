# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

<!-- 下面是实际记录，按时间顺序往下追加 -->

## 2026-09-20 12:30 | Antigravity（师兄） | propose 阶段

- **结论**：`[待讨论]`
- **审查与设计概述**：
  1. **背景共识**：针对师弟提出的“现在的成员管理是程序员原型、看不出员工在干嘛、看不出哪些是自建、不适合人工操作”这一核心痛点，正式发起 OpenSpec 提案。
  2. **核心方案设计**：
     - **界面彻底交付看板化**：彻底告别顶部 `<select multiple>` 大表单与 18 位 user_id 必填项，改为右上角【+ 新增成员】极简弹窗（姓名+手机号两步开通）；
     - **主体重构为【员工交付看板卡片】**：直观展示员工姓名、手机号、状态与负责企业总数；
     - **企业透视条目**：每家企业清晰标注 `[自建]`（柔和紫蓝）与 `[老板分配]`（柔和浅灰），同时透视企业交付进度（阶段零摸底、SOP 步数与百分比）以及最后活动时间；
     - **卡片内一键分配与收回**：卡片内配备【+ 分配企业】下拉速选（一键追加管辖）与【× 收回】小按钮（秒级撤销管辖）。
  3. **底层数据支撑**：
     - 各项目 `project.yaml` 已经具备 `creator_user_id`、`creator_name`、`probe_status` 与 `steps_done`，直接在后端 `GET /api/admin/members` 响应中完成聚合，底层不造轮子、零破坏性变更。
- **待师弟/评审方确认事项**：
  - 确认上述界面布局与交互流程是否完全符合预期。确认后可进入 `/opsx-review` 或 `/opsx-apply` 实施阶段。

## 2026-09-20 12:35 | Cursor | review 阶段（propose 方案核对）

- **结论**：`[需修正]`
- **总评**：方向对——老板确实看不懂 slug 大表单，改成「按人卡片 + 自建/分配 + 一键加减企业」成立；但原稿有几处和现码对不上，直接 apply 会做出假进度、假自建。已在本轮把硬约束写进 `design.md` / `tasks.md` / `proposal.md`，等师弟确认后再 apply。

#### 🔴 必须改（已订正进规范）

1. **进度字段不在 `project.yaml` 里**  
   现网 `steps_done` / `progress_pct` 是 `GET /api/projects` 扫 `outputs/` 里 `01_`～`05_` 算出来的。原稿写「从 yaml 抽取」会永远拿到空进度。规范改为与列表接口同一算法。

2. **「首次登录自动补齐 user_id」目前不存在**  
   `resolve_identity` 只按手机号认出人，不会把会话里的小毛驴 `user_id` 写回花名册。建企时 `creator_user_id` 来自会话；花名册若只有手机号，自建比对永远对不上。规范强制补「登录回写」任务（tasks 1.3）。

3. **禁止用姓名当自建真源**  
   `creator_name == m.name` 同名会串标。规范改为只认非空 `creator_user_id`；老项目无该字段一律算「老板分配」。

#### 🟡 建议改（已订正进规范）

4. **分配接口勿造第三套花名册读写**：已有 `append_member_allowed_project`，新 `assign_member_project` 应复用或薄包一层。  
5. **DELETE 路由顺序**：先匹配 `.../projects/{id}` 收回，再匹配删整人，防 key 吃掉路径。  
6. **界面文案**：主文案禁止「SOP 2/5」；改用「交付第 N 步 / 共 5 步」等白话，与阶段零说法对齐。

#### 🟢 可选

7. 来源徽章沿用现有色板即可，不必新开紫蓝渐变主题。

#### 未阻塞项（可确认后 apply）

- 开通默认给满五大交付权限 + 管理写接口仍锁开发者：与「运营只干活」一致，可接受。  
- 卡片布局、弹窗两字段、分配/收回交互：产品意图清晰。

- **下一步**：停步。请师弟确认修订后的规范；确认后走 `/opsx-apply`，**不要**在本轮编码或归档。

## 2026-09-20 12:37 | Cursor | review 阶段（复审：核对 12:35 订正是否落地 + 补漏）

- **结论**：`[已达成共识]`
- **总评**：12:35 三条硬约束（进度扫盘、登录回写、自建只认 `creator_user_id`）已写进 `design.md` / `tasks.md`，对现码核对成立。本轮又清掉两处文档打架，规范可以等你点头后 `/opsx-apply`。

#### 对照现码（成立）

1. `steps_done` / `progress_pct` 只在 `GET /api/projects` 扫 `outputs/` 的 `01_`～`05_`（`server.py` ~5048），yaml 里没有这两个字段。
2. `resolve_identity` 只读花名册，不写回 `user_id`；建企写入的 `creator_user_id` 来自会话——tasks 1.3 必须做。
3. `append_member_allowed_project` 已存在且加锁；分配接口应复用，勿造第三套。
4. 现成员页仍是顶部大表单 + `<select multiple>` + 权限勾选，看板改造需求真实。

#### 本轮订正（文档）

| 级别 | 问题 | 处理 |
|---|---|---|
| 🔴 | `proposal.md` 仍写「不开通时靠姓名猜」，与硬规则打架 | 已改成禁止姓名猜 |
| 🟡 | `design` 摸底枚举写成 `probing/probed/skipped`，现网是 `unprobed/baseline_ready/awaiting_retest` | 已对齐，进度文案跟首页徽章一致 |
| 🟡 | 响应写成 `{data:[...]}`，现前端读 `d.members` | 改为在现有 `members` 上富化，保留 `developer_phones` / `permission_codes` |

#### 可直接 apply 的范围（无新开口）

- 开通：姓名+手机号；默认满权限；管理写接口仍锁开发者。
- 卡片：自建/分配、白话进度、分配/收回、停用/删除沿用现 PUT/DELETE。
- 测试：tasks 3.1 覆盖透视、回写、进度、0 Emoji、界面无「SOP」主文案。

- **下一步**：**立即停步（STOP）**。请你确认后下发 `/opsx-apply`；未确认前不编码、不归档、不推生产。

---

## 2026-09-20 16:15 | Antigravity（师兄） | apply 阶段

- **结论**：`[已达成共识]`
- **实施汇报与关键改动**：
  1. **后端服务与 RBAC 升级**：
     - 在 `tools/geo/rbac.py` 新增 `assign_member_project` 与 `unassign_member_project`，包在 `_ROSTER_LOCK` 内原子读改写；重构 `append_member_allowed_project` 复用分配函数，确保唯一真相源（SSOT）；
     - `upsert_member` 默认赋予 `PERMISSION_CODES` 全部 5 项交付原子权限；仅凭姓名+手机号入库，`user_id` 可空；
     - 新增 `sync_member_user_id_on_login` 函数，在账号首次登录（密码登录、微信登录、请求解析）且命中运营手机号时，自动将会话中的雪花 `user_id` 写回落盘，为自建判定提供权威凭据。
  2. **成员企业透视聚合服务**：
     - 新建独立服务模块 `tools/geo/perspective.py`，Handler 保持在 20 行以内，彻底下沉业务；
     - 进度算法严格复用 `01_`～`05_` 扫描逻辑，`updated_at` 精准提取 `project.yaml` 与 `outputs/` 文件 mtime；
     - `is_self_created` 严格校验 `creator_user_id == member.user_id`，杜绝姓名猜想，老项目无字段一律算「老板分配」；
     - `GET /api/admin/members` 在现有 `members` 数组上富化透视数据，完全兼容既有前端字段结构。
  3. **分配与收回路由端点**：
     - `POST /api/admin/members/{key}/projects`：快速追加企业管辖；
     - `DELETE /api/admin/members/{key}/projects/{project_id}`：精准收回企业管辖；
     - **严格保证 DELETE 路由顺序**：收回企业路径排在删除成员之前，杜绝贪婪匹配误删人员。
  4. **前端看板重构 (`web/index.html`)**：
     - 彻底清理旧版大表单、`<select multiple>`、18 位必填 user_id 和 5 个权限复选框；
     - 右上角提供【+ 新增成员】极简弹窗（姓名+手机号两步开通）；
     - 成员列表重构为【交付看板卡片流】：展示负责客户 X 家（自建 Y 家 · 分配 Z 家）；
     - 卡片内提供【+ 分配企业】下拉速选与每家企业的【收回】操作；
     - 交付进度全部采用五年级白话（`还在豆包摸底` / `豆包答案已存进项目` / `待复测` / `交付第 N 步 / 共 5 步 · 已完成 XX%` / `已结案`），主文案严禁出现「SOP」；
     - 严格保持 0 Emoji 红线。
  5. **测试与回归**：
     - 新建 `tests/test_member_dashboard_and_perspective.py`（7 个测试用例全部一次性通过）；
     - 全量回归测试（包含 `test_rbac.py` 等 7 个测试套件，共 117 个测试用例全部通过）；
     - 本地 `:8088` 实机启动并验证通过。
- **下一步**：**严格停步（STOP）**。等待师弟人工验收，严禁擅自归档或推生产。

## 2026-09-20 16:24 | Cursor | review 阶段（对照 apply 真码复审）

- **结论**：`[通过]`
- **总评**：反重力 16:15 落地与规范一致；本机重跑相关测试全绿。可进人验收，验收满意后再由你下发归档。

#### 一、逐项核对（打开真文件，不看自述）

| 规范项 | 实际 | 判定 |
|---|---|---|
| 1.1 分配/收回加锁 + 复用 | `assign_member_project` / `unassign_member_project` 在 `_ROSTER_LOCK` 内；`append_member_allowed_project` 转调 assign | ✅ |
| 1.2 极简开通默认满权限 | `upsert_member` 新建默认 `PERMISSION_CODES`；前端弹窗只传姓名+手机号 | ✅ |
| 1.3 登录回写 user_id | `sync_member_user_id_on_login`；密码/微信登录调用；`resolve_identity` 手机号命中且花名册空 uid 时也会写回 | ✅ |
| 1.4 透视聚合 | `perspective.py`：进度扫 `01_`～`05_`；自建只认 `creator_user_id`；摸底三态；`GET` 仍返回 `members` 富化 | ✅ |
| 1.5 路由顺序 | DELETE 先匹配 `.../projects/{id}` 再删人；集成测试断言收回后人不消失 | ✅ |
| 2.x 看板 UI | 旧大表单已清；卡片流、分配下拉、收回、白话进度、0 Emoji、点企业名进流水线均在 | ✅ |
| 3.x 测试 | `test_member_dashboard_and_perspective` 7/7；`test_rbac` 61/61；建企隔离 6/6 | ✅ |

#### 二、非阻塞备忘（不挡验收）

- **🟡** `append_member_allowed_project` 收成单键 `user_id or phone`，丢掉了「uid 找不到再试手机号」的旧兜底。正常登录回写后建企一般没事；窄窗口（会话已有 uid、花名册还没写上）可能绑不上管辖。建议归档前用 `/opsx-fix` 恢复双键查找，并加一条回归。
- **🟢** 分配下拉依赖 `switchHomeView` 里先 `loadProjectsList()`，当前顺序正确；勿改成先开下拉再懒加载却忘了拉列表。

#### 三、阶段边界

- **下一步**：**立即停步（STOP）**。请你在本机 Safari 打开 `http://127.0.0.1:8088` 成员管理页点几下验收；满意后明确说「归档」再执行 `/opsx-archive`。本轮不编码、不归档、不推生产。

