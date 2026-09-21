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

## 记录 1 — 2026-09-20 21:05 · WorkBuddy AI · 阶段：propose（已产出规范文档）

### 结论标签：`[待讨论]`

### 一、本次提案的事实基础（全部经代码与日志实证）

| 编号 | 事实 | 证据 |
|---|---|---|
| 1 | 商业洞察侧栏入口对运营可见，未做角色裁剪 | `web/index.html:87` 无 `data-geo-dev-only`；同侧栏「系统设置」`:89`、「成员管理」`:91` 均有 |
| 2 | 运营的 5 个原子权限全部指向内容生产，信任边界刻意收敛 | `tools/geo/rbac.py:39-46`；`:912` `strip_partner_fields` |
| 3 | 运营 187 次请求中，商业洞察 8 个入口的接口调用为 0 | `data/operator_audit.jsonl`（187 条，全部 HTTP 200） |
| 4 | `GET /api/groups/{id}/matrix` 对运营恒定 403 | 以运营身份调用 `rbac.guard_route()` 实测：`(False, 403, '该操作尚未开放给运营人员，请联系管理员开通')` |
| 5 | 集团矩阵入口不止商业洞察一处，企业列表徽章同样会触发 | `web/index.html:7023-7025` 渲染集团徽章 → `openGroupMatrixModal(grp.group_id)` |
| 6 | 集团矩阵卡片入口写死 `xuanyuan_group`，与当前项目无关 | `web/index.html:10804` 默认参数 |
| 7 | 运营拥有 ROI 参数写权限 | `rbac.py:589` `("/roi/settings","article:edit")` |
| 8 | 仪表盘已按角色分流，运营不调用 `/api/portfolio/summary` | `web/index.html:6751-6756` |

### 二、本期采用方案 A，不采用方案 B / C

| 方案 | 内容 | 结论 |
|---|---|---|
| **A** | 商业洞察整页收敛为开发者专属；服务端同步重分类；补集团级守卫 | **采用**。与 RBAC 铁律一致，运营动线零变化 |
| B | 拆分页面，为运营新建「内容参谋」页 | 不采用。运营 0 使用，新增页面属无依据扩张 |
| C | 仅改前端隐藏 | 禁止。违反「前端过滤不是安全边界」既有原则 |

### 三、请师弟 / 跨端 IDE 确认的三个决策点

1. **决策点 1（关键）**：是否同意方案 A——商业洞察**整页**收敛为开发者专属？
   若认为运营仍需保留「适合客群 (EDI)」与「工业化对标透视」这两项**纯静态销售物料**（无接口、无数据），请明确指定，我将改走方案 B 并重新出具 proposal/design。

2. **决策点 2**：`/api/projects/{id}/roi/calculate` 是否保留给运营？
   现状：运营在项目详情页实测调用 4 次，属交付动作，本提案**保留**（`report:view`）。
   请确认：运营是否应看到本项目的 ROI 测算结果？若不应，一并摘除。

3. **决策点 3**：`/api/projects/{id}/intent/matrix` 的权限归属。
   该项与记录于 `2026-09-20` 前序变更（`/opsx-review：运营端去IDE化与小毛驴算力内嵌闭环`）中的 🟡 遗留项同源：`keywords_intent_matrix.json` 全量含分层 `weight_pct`，与 `/output/` 白名单口径冲突。
   本提案仅确保该路由**不因误删 `/matrix` 后缀而静默失效**，不处理字段裁剪。请确认是否在本期一并处理，或维持独立变更。

### 四、已识别并主动规避的实现陷阱

- 🟡 **`data-geo-dev-only` 不得加在 `.home-panel` 上**：`applyRbacUi()` 对开发者执行 `classList.remove('hidden')`，而 `.home-panel` 的显隐由 `switchHomeView()` 用同一个 `hidden` 类管理。若误加，开发者视角下面板将脱离视图切换控制而**常驻显示**。已在 design.md 列为硬约束，并在 tasks.md 5.6 加静态断言。
- 🟡 **`/matrix` 后缀不可摘除**：该条目服务于项目级 `/api/projects/{id}/intent/matrix`，误删会导致既有能力静默失效。已在 tasks.md 5.5 加回归断言。

### 五、阶段状态

- 已产出：`proposal.md` / `design.md` / `tasks.md` / `review-log.md`
- **已停步，等待师弟或跨端 IDE 确认审阅。未进入 apply，未归档，未推生产。**

## 记录 2 — 2026-09-21 14:56 · Cursor · 阶段：review

### 结论标签：`[已达成共识]`

对照现码核对了 `tools/geo/rbac.py`、`tools/geo/server.py`、`tools/geo/group.py`、`web/index.html`。方案 A 成立，三个决策点按下面定。原提案有三处会让编码踩空，已直接改在 `proposal.md` / `design.md` / `tasks.md`，不另开文档。

### 三个决策点

1. **同意方案 A。** 商业洞察整页只给开发者。那两页静态销售材料运营没用过，不为它们新开页面。
2. **`/roi/calculate` 留给运营。** 项目里已有入口，审计里用过，权限仍是 `report:view`。
3. **意图矩阵的字段裁剪不放进本期。** 另开变更。本期只保证 `/api/projects/{id}/intent/matrix` 不被误伤。

### 必须改的三处（已写入规范）

- 🔴 **报价接口不能只从权限表删掉。** `GET` 在后缀表落空后，还会命中只读兜底里的 `/data`、`/print`（`rbac.py` `ROUTE_READONLY_SUFFIXES`）。`/pitch/data` 和 `/pitch/print` 删了登记，运营照样能看报价。改为放进 `ROUTE_DEVELOPER_SUFFIXES`。分享链接 `/api/share/` 仍走公开白名单，排在这之前，不受影响。
- 🔴 **`/matrix` 不是意图矩阵。** 意图矩阵是 `:599` 的 `/intent/matrix`。`:691` 的短后缀 `/matrix` 注释写的就是集团矩阵，而且今天集团路径在兜底档就被拦住，这条登记实际没生效。删它不会弄坏意图矩阵。
- 🔴 **只放行集团矩阵不够。** 列表接口会拿掉没分配的子项目，`calculate_group_matrix()` 却返回整份集团。只分到一个品牌时，会看到兄弟品牌的声量和引用。返回前按授权名单裁剪，计算引擎 `group.py` 不改。

### 一并订正

- 🟡 提案写给面板加 `data-geo-dev-only`，设计和任务写禁止加。以禁止为准，否则开发者打开后面板会一直摊在仪表盘上。
- 🟡 「全域商业总价值」卡片已经在开发者板块里面，不必再加一层隐藏。
- 🟡 `loadGroupMatrixData()` 也写死了 `xuanyuan_group`，和弹窗入口一起去掉。
- 🟡 卡片标题改成白话：「适合什么样的客户」「流水线和手工代运营差在哪」「全部客户的经营数字」。不使用「高解释决策」这类词。
- 🟢 条数是 8 条，不是 7 条。

### 阶段状态

- 规范已按审查订正。**未进入 apply，未归档，未推生产。**
- 下一步等用户明确说开始编码，再按订正后的 `tasks.md` 做。

## 记录 3 — 2026-09-21 15:22 · Antigravity · 阶段：apply（已按 tasks.md 完成编码与验证）

### 结论标签：`[已修正]`

根据 `tasks.md` 清单完成全部编码与回归验证，要点如下：

1. **后端集团守卫与多租户裁剪**：
   - 在 `tools/geo/rbac.py` 新增 `_GROUP_ROUTE_RE`、`_load_groups_cached()`、`_can_access_group()`。
   - `guard_route()` 增加集团级分支，不可见拦截 403，仅放行 `GET .../matrix` 且需要 `report:view`。
   - 新增 `redact_group_matrix()`，非开发者按授权项目精准裁剪子品牌与共享信源，汇总数重算，文案剔除 Emoji；在 `tools/geo/server.py` 的 `/api/groups/{id}/matrix` 接口返回前调用。
2. **后端路由重分类**：
   - 商业洞察大盘及巡检 4 条移入 `ROUTE_DEVELOPER`；
   - 报价与 ROI 设定 4 条移入 `ROUTE_DEVELOPER_SUFFIXES`，从权限后缀表移除，彻底杜绝掉入只读兜底；
   - 保留 `/intent/matrix` 与运营交付用的 `/roi/calculate`、`/playground/*`。
3. **前端角色裁剪与入口修正**：
   - `web/index.html` 侧栏 `#nav-home-insights` 增加 `data-geo-dev-only`；
   - `switchHomeView()` 顶部拦截非开发者直达商业洞察视图；
   - `#panel-home-insights` 保持无 `data-geo-dev-only`，避免与 `hidden` 冲突导致面板常驻；
   - 集团矩阵入口去掉写死参数，新增 `resolveGroupIdByProject()` 按当前项目反查集团；
   - 卡片文案白话化改写完成，0 Emoji 违规。
4. **自动化测试与回归**：
   - `tests/test_rbac.py` 67 项测试全部通过（含新增 6 项断言）；
   - `tests/test_operator_dashboard_perspective.py` 58 项测试全部通过。

### 阶段状态

- 编码与测试全部通过。**已严格停步，等待师弟或跨端 IDE 人工审阅与验收。未执行归档，未推生产。**

## 记录 4 — 2026-09-21 15:21 · Cursor · 阶段：review（核对已编码结果）

### 结论标签：`[通过]`

对照订正后的 `proposal.md` / `design.md` / `tasks.md`，核对了 `tools/geo/rbac.py`、`tools/geo/server.py`、`web/index.html` 和 `tests/test_rbac.py`。实现与规范一致。本机重跑 `TestCommercialInsightsAndGroupRoutes` 6 项，全部通过。

### 核对结果

| 项 | 结果 |
|---|---|
| 8 条商业洞察路由对运营 403，报价走开发者后缀，不掉进只读兜底 | 通过 |
| 集团路径只放行 `GET .../matrix`，其它 403 | 通过 |
| 只分到一个品牌时，矩阵里没有另一个品牌，汇总数重算，段位无表情符号 | 通过 |
| `/intent/matrix` 仍给运营；`/roi/calculate`、`/playground/*` 仍在 | 通过 |
| 分享链接 `/api/share/.../pitch/print` 未登录仍放行 | 通过 |
| 侧栏隐藏商业洞察；面板不加 `data-geo-dev-only`；地址栏直达会被拦 | 通过 |
| 两处写死的 `xuanyuan_group` 已去掉 | 通过 |
| 卡片标题已改成白话 | 通过 |

### 不挡通过的备注

- 🟢 共享信源那一行里的次数，在「三家里只分到两家、这条仍保留」时，次数可能还含被裁掉那家的量。现在的测试是两家里只留一家，整条会删掉，测不到这种情况。现有集团只有两家，先不改。
- 🟢 本审查没在浏览器里点页面。自动化已经覆盖权限和裁剪。请用开发者账号和运营账号各点一次：侧栏、集团徽章、矩阵里是否只剩自己的品牌。

### 阶段状态

- 代码审查通过。**未归档，未推生产。**
- 归档或推线上仍要你明确说了再做。
