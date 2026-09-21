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

## 2026-09-21 21:02 Antigravity 针对 propose 阶段
- 标签：`[已达成共识]`
- 评估说明：
  - 师弟明确指示：“既然是鸡肋，那就不要留在这个写文同事的操作页面里了.从写文同事里面去掉吧.”
  - 方案设计：
    1. 给侧边栏「协作与任务」（`#nav-home-collab`）添加 `data-geo-dev-only` 标记，写文同事侧栏隐藏。
    2. 在 `switchHomeView` 守卫中将 `'home-collab'` 放入 `devOnlyViews`，如果写文同事强制跳转则自动回退到仪表盘。
    3. 保留开发者的访问与使用能力，不破坏系统底层调度与打包功能。
  - 规范文档 `proposal.md`、`design.md`、`tasks.md` 已编排完毕，等待用户审阅确认。

## 记录 2 — 2026-09-21 21:03 · Cursor · 阶段：review

### 结论标签：`[已达成共识]`

对照现码核对了侧栏 `#nav-home-collab`、`#panel-home-collab`、`showDashboard` 与 `switchHomeView`。方向对：只藏写文同事的入口，开发者照旧能进。规范有两处会让编码踩空，已写入 `proposal.md` / `design.md` / `tasks.md`。**未改业务代码。**

### 现码事实

| 事实 | 证据 |
| :--- | :--- |
| 侧栏按钮还没有角色标记 | `#nav-home-collab` 约第 91 行，无 `data-geo-dev-only` |
| 拦截名单有两份，都没有协作页 | `showDashboard` 约 6235 行；`switchHomeView` 约 6356 行 |
| 协作面板是 `home-panel` | `#panel-home-collab` 约 423 行 |
| 进协作页才会拉任务 | `switchHomeView` 里 `home-collab` 才调 `collabRefreshTasks` |

### 必须订正（已写入规范）

1. 🟡 **两份 `devOnlyViews` 都要加 `home-collab`。** 只改 `switchHomeView` 时，从旧地址恢复页面的那份名单仍会把人送进协作页，再靠第二道拦。两处一起改，和运维告警同一套。
2. 🔴 **不要给 `#panel-home-collab` 加 `data-geo-dev-only`。** 开发者登录时，`applyRbacUi` 会去掉所有该标记上的 `hidden`。面板若带上，人在仪表盘时协作页会一起露出来。只标记侧栏按钮。
3. 🟢 隐藏用现成的 `hidden` class，不要另写 `display:none`。

### 阶段状态

- 可按订正后的 `tasks.md` 进入 `/opsx-apply`。
- **已停步**：未编码、未归档、未推生产。

---

## 记录 3 — 2026-09-21 21:10 · Cursor · 阶段：apply

### 结论标签：`[已修正]`

按记录 2 的订正完成编码，未改开发者界面行为，未给协作面板加标记。

1. `#nav-home-collab` 已加 `data-geo-dev-only`。`#panel-home-collab` 仍是普通 `home-panel`，没有该标记。
2. `showDashboard`（约 6235 行）与 `switchHomeView`（约 6356 行）的 `devOnlyViews` 都加入了 `'home-collab'`。写文同事从旧地址进来会回到仪表盘。
3. `tests/test_writer_perspective.py` 增加侧栏按钮、面板禁标、两份名单的断言。
4. `python3 -m unittest tests.test_writer_perspective tests.test_dual_track_perspectives`：14 项全绿。

### 阶段状态

- 请用写文同事账号刷新工作台，确认侧栏没有「协作与任务」；再用开发者账号确认该项还在、点进去能看任务。
- **已停步**：未归档，未推生产。

---

## 记录 4 — 2026-09-21 21:28 · Antigravity · 阶段：review (跨端终审)

### 结论标签：`[通过]`

Antigravity 作为对端 Reviewer，对 Cursor 提交的改动与回归测试进行了全量实测与代码审查：

1. **DOM 与样式审查**：
   - 侧栏导航项 `#nav-home-collab` 正确挂载 `data-geo-dev-only`。
   - 协作面板 `#panel-home-collab` 保持干净，未误挂 `data-geo-dev-only`，杜绝了开发者登录后因 `hidden` 类被冲刷导致的多面板重叠 Bug。
2. **守卫双重覆盖审查**：
   - `showDashboard`（页面初次载入/刷新路由恢复）与 `switchHomeView`（运行时切页）两处的 `devOnlyViews` 均已严密包含 `'home-collab'`，写文同事无法绕过。
3. **自动化回归核验**：
   - 执行 `python3 -m unittest tests/test_writer_perspective.py`：7 项测试全部通过（含侧栏按钮、面板禁标、双重守卫断言）。
   - 执行 `python3 -m unittest tests/test_rbac.py`：67 项权限守卫测试全量通过。
4. **铁律与阶段约束核验**：
   - 无违规代码、无破坏性变更、无绕过逻辑。
   - 严格停步：未擅自归档、未向生产机部署。
