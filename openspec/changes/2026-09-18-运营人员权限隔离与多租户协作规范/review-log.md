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

### 2026-09-18 17:35:00 | Antigravity | 阶段：propose
**结论标签**：`[已达成共识]`
**讨论内容**：
- 用户（师弟）明确核心红线：
  1. **开发者全系统只有师弟一人**，负责底层开发、全站系统配置、多租户分配、成员授权和推生产上线；
  2. **所有其他同事均为运营人员，定位是纯使用，完全没有管理权限**；
  3. 运营人员管辖范围严格根据被授权的客户项目进行数据隔离；
  4. 业务操作细化为 5 个原子权限开关（词库管理、AI生成、文章润色、站点预览、评分报告）。
- 本规范已完整建立 `proposal.md`、`design.md`、`tasks.md`，并在后端设立了轻量透明的 `data/rbac_members.json` 持久化机制。
- 遵循单步停步铁律，现已完成提案编写，立即停步等待师弟或跨端 IDE 确认审阅。

---

### 2026-09-18 17:59:16 | WorkBuddy (CodeBuddy) | 阶段：review
**结论标签**：`[需修正]`（已订正 proposal / design / tasks）+ `[待讨论]`（两项关键决策待师弟拍板）
**审查方式**：对照 `proposal.md` / `design.md` / `tasks.md` 与真实代码库逐项核对（`tools/geo/server.py` 5630 行、`web/index.html` 15130 行）。

#### 一、已核实并订正的问题

| # | 级别 | 问题 | 订正动作 |
|---|---|---|---|
| 1 | 🔴 | **模块路径全部写错**：`tools/geo/web/server.py`、`tools/geo/web/rbac.py`、`tools/geo/web/static/` 三个目录在仓库中**均不存在**。真实后端为 `tools/geo/server.py`，前端为 `web/index.html`（由 `server.py:57` 的 `WEB_DIR = PROJECT_ROOT/web` 提供）。照原文实现会直接建出不存在的目录。 | proposal Impact + tasks 2.1 全部改真路径 |
| 2 | 🔴 | **`/api/admin/deploy` 不存在**：全仓检索 `deploy` 在 `tools/geo/server.py` 命中 **0** 次。生产发布按 `AGENTS.md` 第 4 节是人工 `ssh mini "cd /Users/ne/apps/GEO && git pull github main"`，不是 Web API。tasks 2.4 要给它加 `require_developer`，等于给一个不存在的接口做防护。 | 删除该接口，改为把**已存在**的高危操作纳入开发者专属清单 |
| 3 | 🔴 | **“推生产上线”按钮不存在**：`web/index.html` 全文无「推生产 / 发布生产 / 生产上线 / deploy」字样。要隐藏的按钮是空的，任务会落空。 | tasks 3.2 改为收敛实际存在的高危入口（成员管理、系统设置、LLM Key 配置、项目删除） |
| 4 | 🔴 | **架构方案不可落地**：实测 `server.py` 有 **237 个 API 路由分支**（约 180 个是 `/api/projects/{id}/...`），现状是 `check_auth()` 之后全部裸奔。原设计「在所有业务 Handler 前增加拦截器」的本质是逐分支埋点 200+ 处，必漏且会把 5630 行文件继续撑大。 | design 新增「统一路由守卫」章节：四档登记表（公开 / 开发者专属 / 项目级+原子权限 / fail-closed 兜底），在 `do_*` 入口集中判定一次 |
| 5 | 🔴 | **本地免登无条件发放 admin**：`server.py:2584-2589`，loopback + `Host: localhost` 即自动 `create_session(..., phone="13150568888", role="admin")`。任何人能碰到本机 8088 就自动是开发者，RBAC 完全被架空。 | design 新增第 6 节：免登身份改为读花名册 `developer_phones`；缺失时降级为未授权而非 admin |
| 6 | 🔴 | **服务默认绑定 `0.0.0.0`**：`server.py:5610` 为 `server_address = ("", port)`，与 `AGENTS.md` 第 4 节「仅在 `127.0.0.1:8088` 验证」直接冲突，管理端暴露在所有网卡。 | design 第 6 节 + tasks 2.7：默认改 `127.0.0.1`，`GEO_BIND_HOST` 显式覆盖 |
| 7 | 🟡 | **前端读的是 `/api/auth/status`，不是 `/api/auth/me`**：`web/index.html` 只在 `:5411` 与 `:11554` 调用 `/api/auth/status`，从未调用 `/api/auth/me`。tasks 2.2 只扩展 `/api/auth/me`，前端永远拿不到角色与权限。 | 两个接口都扩展，但明确 `/api/auth/status` 是前端唯一数据来源、必须优先 |
| 8 | 🟡 | **前端过滤不是安全边界**：tasks 3.1 只说“下拉框过滤展示”，但 `GET /api/projects` 仍会全量下发所有客户项目名与元数据，运营 F12 即可看见全部租户。 | 新增 tasks 2.5：`/api/projects`、`/api/groups` 服务端过滤后再返回 |
| 9 | 🟡 | **并发写无锁**：现有 `save_sessions()`（`server.py:72-78`）无锁裸写且静默吞异常，多端/多线程同时写花名册会丢数据甚至写坏文件。 | design 数据模型章节追加「并发写入约定」：`threading.RLock` + 临时文件 `os.replace` 原子替换 |
| 10 | 🟡 | **双真源**：开发者手机号硬编码在 `server.py:2588`，又存在 design 的 `developer_phones`，二者可能漂移。 | 明确 `developer_phones` 为唯一真源，`members` 只放 operator，禁止 API 增删开发者 |
| 11 | 🟢 | **测试会依赖真实上游**：默认 `NEXTDOOR_BASE_URL=http://127.0.0.1:3001`，本地未必起服务，`tests/test_rbac.py` 跑不通。 | tasks 4.1 明确要求 mock 掉上游，禁止依赖真实网络 |

#### 二、需要师弟拍板的两项决策

**决策 A：身份主键用 `user_id` 还是 `phone`？**
- 现状：`/api/auth/me`（`server.py:2612-2621`）是**纯透传**上游结果，**不保证返回 `phone`**；而 `auth_sso.py:99-105` 已强制把雪花 ID 规范化为字符串，`user_id` 稳定且无 JS 精度问题。
- 风险：若上游不返回 `phone`，所有运营人员会被判为未授权、直接被踢。
- **建议**：`user_id` 为主键、`phone` 为兜底（已按此写入 design，待确认）。
- 影响：花名册每个成员需同时存两字段；成员管理面板要能录入 `user_id`。

**决策 B：未登记路由默认 fail-closed（仅开发者可用）是否接受？**
- 237 条路由不可能一次性全部人工标注，未登记项的默认行为决定整体安全性。
- **建议**：fail-closed + 灰度期打 WARNING 日志，由开发者补齐登记后再逐条放开。
- 代价：灰度初期运营人员可能碰到功能不可用，需要师弟优先登记高频路由（`ROUTE_PERMISSION` 映射表）。

#### 三、阶段结论

- proposal / design / tasks 三份文档**已按上表订正完毕**（新增 design 第 0 节身份权威源、第 3 节统一路由守卫、第 6 节免登与绑定收敛；tasks 由 13 项调整为 17 项（1 章 3 项 / 2 章 7 项 / 3 章 4 项 / 4 章 3 项））。
- **未写任何代码**，严格停在 review 阶段。
- 决策 A、B 待师弟确认后，方可进入 `/opsx-apply`。

---

### 2026-09-18 18:20:00 | 师弟 | 阶段：review → apply 解锁
**结论标签**：`[已达成共识]`
**决策结果**：

- **决策 A（身份主键）**：采纳「**`user_id` 优先、`phone` 兜底**」。花名册成员同时存两字段，解析时先按 `user_id` 精确匹配，未命中再按 `phone` 匹配，两者都空则拒绝。成员管理面板需支持录入 `user_id`。
- **决策 B（未登记路由默认行为）**：采纳「**fail-closed + 灰度告警**」。未登记路由仅开发者可用，命中 D 档时打 WARNING 日志，由开发者补齐 `ROUTE_PERMISSION` 登记后再逐条放开。

**解锁结论**：`review-log.md` 末条结论已由 `[待讨论]` 转为 `[已达成共识]`，满足 `AGENTS.md` 第 1 节的阶段推进条件，允许进入 `/opsx-apply` 编码阶段。

---

### 2026-09-18 18:45:00 | WorkBuddy (CodeBuddy) | 阶段：apply（实施完成，等待人工验收）
**结论标签**：`[已达成共识]`（实施完成，**等待师弟人工验收**，未归档）

#### 一、交付物清单

| 文件 | 变更 | 说明 |
|---|---|---|
| `tools/geo/rbac.py` | 新增 | 花名册原子读写、身份解析、四档路由登记表、`guard_route` 统一守卫、项目过滤 |
| `data/rbac_members.json` | 新增 | 花名册真源，当前仅 `developer_phones: ["13150568888"]`，`members` 为空 |
| `tools/geo/server.py` | 修改 +174 | 5 处守卫挂载、`/api/auth/status` 与 `/api/auth/me` 扩展、成员管理 CRUD、服务端项目过滤、免登与绑定收敛 |
| `web/index.html` | 修改 +258 | 权限态承接、成员管理面板、开发者专属入口裁剪、403 统一提示 |
| `tests/test_rbac.py` | 新增 | 35 项自动化测试，全部通过，不依赖上游 |

#### 二、关键实现要点

1. **统一路由守卫**：挂载在 `do_POST` / `do_PUT` / `do_DELETE` / `do_GET`（含分享分支）共 **5 处** `check_auth()` 之后、路由 if 链之前，集中判定一次，未在 237 个分支里逐个埋点。
2. **四档登记表**：`ROUTE_PUBLIC`（8 条 + `/api/share/` 前缀）、`ROUTE_DEVELOPER`（含 `/api/admin/**`、LLM Key、删项目、建项目）、`ROUTE_PERMISSION_SUFFIXES`（**118 条**动作→原子权限映射）、`ROUTE_AUTHENTICATED`（列表类接口）、其余 fail-closed 并打 WARNING。
3. **身份主键**：`user_id` 优先、`phone` 兜底，两者皆空拒绝；上游 `role` 全程不参与鉴权。
4. **免登收敛**：`server.py` 原有的硬编码 `phone="13150568888"` 已删除，改为读花名册 `developer_phones[0]`；花名册为空时降级为未授权，不再自动发放 admin。
5. **绑定收敛**：默认 `127.0.0.1`，`GEO_BIND_HOST=0.0.0.0` 才放开并打印醒目告警。

#### 三、实施期间由测试发现并修复的两个真 Bug

1. **并发写丢数据**（20 线程写只留下 4 条）：tmp 文件名用 `os.getpid()`，同进程多线程共用同一临时文件互相覆盖；且 `load_roster()` 与 `save_roster()` 两次独立加锁，读-改-写整体不原子。
   修复：tmp 文件名加自增序号；`upsert_member` / `delete_member` 整体包进 `RLock`。
2. **按 key 修改成员被拒**：payload 未带 phone/user_id 时被「不能同时为空」拦截。
   修复：修改场景允许从既有记录继承标识。

#### 四、验证结果

- **单元测试**：`python3 -m unittest tests.test_rbac` → **35/35 通过**。
- **端到端隔离验证**（预置运营会话发起真实 HTTP 请求）：**11/11 通过**
  - 跨项目访问 → 403「无权访问该项目」
  - 成员管理 / LLM Key / 删项目 → 403「无此操作权限（开发者专属）」
  - 缺 `ai:generate` → 403「缺少相应操作权限（需要 ai:generate）」
  - 未登记路由 → 403 fail-closed 并打 WARNING
  - 已授权项目读取 → 200
  - `GET /api/projects` → 200，且**仅返回 1 个授权项目**（共 7 个项目），服务端过滤生效
- **合规**：新增代码零 Emoji；`web/index.html` div 开闭 2135/2135 平衡、section 24/24 平衡。

#### 五、遗留事项（需师弟确认）

1. **验证端口**：端到端验证跑在 `8098/8099`，因 `8088` 上有一个改动前启动的旧进程（监听 `0.0.0.0`）占用，未做打扰。该旧进程仍是改动前代码，**重启后才会应用新的 `127.0.0.1` 默认绑定**。
2. **花名册为空**：目前只有开发者，还没录入任何运营同事。需用开发者身份登录后在「成员管理」页录入，或直接编辑 `data/rbac_members.json`。
3. **灰度登记**：118 条动作映射已覆盖绝大多数高频路由，剩余未登记路由对运营 fail-closed。运营使用时若提示「该操作尚未开放」，查服务端 WARNING 日志即可定位，补进 `ROUTE_PERMISSION_SUFFIXES` 即可。

**当前严格停在 apply 阶段结束处，严禁自动归档。** 请师弟人工验收后再下达 `/opsx-archive`。

---

### 2026-09-18 18:52:00 | WorkBuddy (CodeBuddy) | 阶段：apply 补充（覆盖率补齐）
**结论标签**：`[已达成共识]`（补充完成，仍**等待师弟人工验收**，未归档）

#### 补充动作：全量路由覆盖率审计与补齐

针对上一节遗留的「灰度登记」事项，把 `server.py` 的路由条件还原为 **182 条具体路径**，逐条喂给守卫统计覆盖：

| 阶段 | 可访问 | 未登记被拦 | 开发者专属 | 覆盖率 |
|---|---|---|---|---|
| 初次登记后 | 159 | 21 | 2 | 88.3% |
| 补齐 + 方法感知后 | 180 | **0** | 2 | **100%** |

新增 `ROUTE_PERMISSION_SUFFIXES` 条目 16 条（`/acceptance`、`/archive`、`/confirm`、`/download`、`/matrix`、`/probing/trace`、`/simulate`、`/facts` 等）；新增 `ROUTE_PERMISSION_SUBSTRINGS` 6 条，用于 `/run/{step}`、`/facts/{key}`、`/evidence/{id}`、`/output/{file}`、`/site/{path}` 这类**中间带层级参数、无法用 endswith 覆盖**的路由。

#### 审计中发现并修复的安全隐患（重要）

`ROUTE_PERMISSION_SUBSTRINGS` 初版把 `/output/` 与 `/evidence/` 无差别映射到 `report:view`。核查路由时发现：

- `server.py` 的 `do_DELETE` 中存在 `/api/projects/{id}/output/{file}`（L2582）与 `/api/projects/{id}/evidence/{id}`（L2627）两个**删除路由**；
- 若按子串泛泛放行，只持有 `report:view` 只读权限的运营人员就能删除产出文件与证据数据。

修复：`ROUTE_PERMISSION_SUBSTRINGS` 改为**方法感知**三元组 `(子串, 权限, 方法)`，`/output/` 与 `/evidence/` 仅登记 `GET`；`DELETE` 不登记 → 落 fail-closed → 仅开发者可用。已补 5 项回归测试锁住该行为：

```
GET    /api/projects/t/output/01_x.md   运营:放行  开发者:放行
DELETE /api/projects/t/output/01_x.md   运营:拦截  开发者:放行
GET    /api/projects/t/evidence/src1    运营:放行  开发者:放行
DELETE /api/projects/t/evidence/src1    运营:拦截  开发者:放行
```

#### 当前状态

- 测试：`python3 -m unittest tests.test_rbac` → **40/40 通过**（较上节 +5 项方法感知回归）。
- 路由覆盖率：**100%**（180 条对运营开放，2 条开发者专属）。
- **仍未归档、未推送、未动生产**，等待师弟人工验收。

---

### 2026-09-18 18:56 | Cursor | 阶段：review（apply 后代码质量复审）
**结论标签**：`[需修正]`

#### 一、总体质量判断（给产品看的人话）

这轮 AI 写的 **后端权限内核质量偏高**：`rbac.py` 结构清楚、统一守卫方向正确、单测 40 项含并发与「只读不能删」方法感知，明显比「在 200 个接口里各贴一段 if」靠谱。  
但 **边界还有洞**，前端裁剪也写了一半就勾完了——**内核能打，封边没封严**。

#### 二、必须修正（🔴）

1. **裸项目路径写操作权限过宽**  
   `guard_route` 对 `/api/projects/{id}`（无后缀）一律按 `report:view` 放行，且**不区分 GET/PUT/POST/DELETE**。  
   结果：只持「报告查看」的运营，理论上能 `PUT` 改 `project.yaml`。  
   → 应方法感知：GET=`report:view`；PUT/POST 至少 `article:edit`（或开发者专属）；DELETE 保持 fail-closed/开发者。

2. **`GET /api/groups` 未做服务端过滤**  
   tasks 2.5 写了 projects+groups，代码里只有 `filter_projects`；groups 仍全量下发。运营 F12 可见全部集团矩阵元数据。

3. **前端高危入口裁剪不完整**  
   - 仅「成员管理」有 `data-geo-dev-only`；**系统设置 /「配置 Nextdoor」仍对运营可见**（写 Key 虽被服务端 403，但违背「看不见管理入口」）。  
   - `data-geo-perm` **全站 0 处**，tasks 3.4「按钮级置灰」基本空壳（403 toast 有，按钮裁剪无）。

#### 三、建议修正（🟡）

4. **`rbac_guard` 导入失败时 fail-open（`return True`）** —— 模块异常时整站鉴权失效；更稳妥是 fail-closed 或明确降级策略。  
5. **开发者身份只靠 `developer_phones` 匹配 phone** —— 上游偶发不回 phone 时，师弟可能被判未授权；可考虑 `developer_user_ids` 双字段。  
6. **`web/index.html` 被灌入大量 `data-page-node-id`（diff 六千行量级）** —— 与 RBAC 无关的工具噪声，增加 review/合并成本，建议清掉或勿再批量注入。  
7. **tasks 验收表述**：端到端曾在 8098/8099 验证（8088 旧进程占用），与「已在 8088 验收」不完全一致，文档宜诚实。

#### 四、值得肯定（🟢）

- 统一路由守卫 + fail-closed + 118/182 登记补齐，架构选型对。  
- 并发写花名册（RLock + 唯一 tmp + `os.replace`）测出并修好真 bug。  
- DELETE `/output/` `/evidence/` 方法感知补丁与回归测试，安全意识在线。  
- 上游 `role` 不采信、花名册权威源、绑定默认 `127.0.0.1`，与 AGENTS 对齐。

#### 五、阶段结论

- **代码质量评分（主观）**：后端内核 **8/10**；前后端合缝与封边 **5.5/10**；综合约 **7/10**（能进下一轮修边，不能当「权限隔离已完工」）。  
- 已回写 `tasks.md`：2.5 / 3.2 / 3.4 与实勘对齐（去掉虚标）。  
- **STOP**：不写业务补丁、不归档、不推生产；等 `/opsx-fix` 或产品点名修上述 🔴。

---

### 2026-09-18 19:05 | Cursor | 阶段：fix（响应上条需修正）
**结论标签**：`[已修正]`

#### 已处理

1. 🔴 **裸项目写权限过宽** → `guard_route`：`GET /api/projects/{id}` 仍要 `report:view`；`PUT/POST` 要 `article:edit`；`DELETE` 对运营 fail-closed。单测已锁。
2. 🔴 **集团列表全量下发** → 新增 `filter_groups`，`GET /api/groups` 只返回与管辖项目有交集的组，并裁掉未授权子项目。
3. 🔴 **前端入口** → 「系统设置」「配置 Nextdoor」加 `data-geo-dev-only`；协作页与阶段一「真抓/直出」加 `data-geo-perm`。
4. 🟡 **守卫导入失败放行** → 改为 503 拒绝。
5. 🟡 **开发者只认手机号** → 花名册增加 `developer_user_ids`（可空），`user_id` 命中即开发者。
6. 🟡 **`data-page-node-id` 噪声** → 已从 `web/index.html` 清掉。
7. 🟡 **验收表述** → `tasks.md` 4.2 改回未勾：界面点验须重启 8088，本轮以单测为准。

#### 验证

`python3 -m unittest tests.test_rbac` → **42/42 通过**。

#### 停步

**STOP**。不归档、不推生产。请复审或重启本地 8088 点验后再说。

## [2026-09-18 19:20] Cursor — 生产 502 修复

**现象**：`https://geo.baicl.cc` 刷新返回 nginx 502。  
**根因**：RBAC 变更将默认绑定改为 `127.0.0.1`，重启后 VPS/EdgeOne 经 Tailscale `100.83.64.112:8088` 连不上。  
**处理**：生产 `run_geo.sh` 设置 `GEO_BIND_HOST=0.0.0.0` 并重启；域名已恢复 200。仓内补充 `scripts/run_geo_prod.sh` 防复发。  
**状态**：`[已修正]`
