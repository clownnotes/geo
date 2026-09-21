# Review Log: 开发者与写文同事双轨视界彻底解耦与全阶段白盒流水线复原

> 记录本需求的跨端审查、讨论记录与多 IDE 协同共识。

---

## 2026-09-21 · 全阶段地毯式盘查与立项共识

* **发起人**：师兄（全栈工程师 / 架构师）
* **审阅人**：师弟（产品负责人 / 需求提出者）
* **审查结论**：`[待讨论]`

### 1. 师弟核心指示与全盘共识
- **坚决拒绝打补丁思维**：绝不能改了阶段一，明天又发现阶段四、阶段零漏了。必须从阶段 0 到阶段 5 全量做完，一次性彻底收口。
- **两个角色彻底解耦**：
  - **开发者**：原本的版本基本是成熟好用的，100% 恢复白盒流水线与 IDE 工地，保留全部调试武器库；
  - **写文同事**：享受纯粹的一键小毛驴黑盒闭环，不需要懂复杂技术指标，也不允许接触源码、Prompt 配方与商业财务机密。

### 2. 全量 6 阶段盘查结论已纳入规范
- [x] 阶段 00：复原 Cursor 出题与反重力自动化问答卡片（挂 `data-geo-dev-only`）；
- [x] 阶段 01：复原开发者 4 步白盒流水线（带 IDE 协同）；写文同事改为单一主按钮【小毛驴 AI 商业诊断深度生成】；
- [x] 阶段 02：为【导出源码包 (.zip)】补齐 `data-geo-dev-only`；
- [x] 阶段 03：为【复制 9 因子全文】补齐 `data-geo-dev-only`；
- [x] 阶段 04：复原开发者【IDE 工地】与全渠道 SOP 派单卡；写文同事保留纯网页改写闭环；
- [x] 阶段 05：为【商业 ROI 测算与服务费续约大盘】补齐 `data-geo-dev-only`。

---

## 记录 2 — 2026-09-21 17:37 · Cursor · 阶段：review

### 结论标签：`[已达成共识]`

对照现码核对了 `web/index.html`、`web/step0-src`、`tools/geo/audit.py`、`tools/geo/rbac.py`。产品方向（0～5 双轨、开发者恢复 IDE、写文极简）同意；原规范有 4 处会让编码踩空，已直接订正 `proposal.md` / `design.md` / `tasks.md`。**未改业务代码。**

### 现码事实

| 事实 | 证据 |
| :--- | :--- |
| 阶段二源码 ZIP 无角色属性 | `:910` `downloadSiteZip()` 无 `data-geo-dev-only`（服务端 `/site/download` 已是开发者后缀） |
| 阶段三 9 因子复制全文无角色属性 | `:1101` `copyOutput('03_…')` |
| 阶段五 ROI 看板无角色属性 | `:1555` 看板根节点 |
| 阶段一/四 IDE 函数是空壳 | `copyBossAuditToIde` / `copyDiagDeepenPrompt` / `copyIdeRewritePack` / `copyWritebackCommand` 仅 toast |
| 阶段零 IDE 复制是空壳且 UI 已拆 | `useStep0.js` `refuseExternalCopy`；`Step0App.vue` 无 Cursor/反重力按钮 |
| `interpret` 不能单独当一键 | `run_audit_interpret`：无 metrics → `ValueError("请先点「① 真抓…")` |
| step0 bridge 无角色 | `getStep0BridgeProps()` 未传 `isDeveloper` |
| `/roi/calculate` 仍给写文 | `rbac.py` `report:view`（前序约定，本期只藏看板 UI） |

### 必须订正（已写入规范）

1. 🔴 **写文一键禁止只调 `mode=interpret`**：无 metrics 先 `crawl`，再 `interpret`；与 `isAuditRunning` 共用防连点；文案白话，不写死 5～8 秒。
2. 🔴 **阶段零必须走 Vue `v-if` + `npm run build:step0`**：静态 `data-geo-dev-only` 扫不到组件岛。
3. 🔴 **恢复真实 IDE 剪贴板/API**，不是再贴一层空 toast；写文零入口。
4. 🟡 **勿把角色属性挂在 `.home-panel` 根上**；`/roi/calculate` 权限档不动。

### 明确回滚边界

本期**有意**撤销 2026-09-19「去 IDE 化」里对**开发者**的 stub；对写文同事的防搬走与零 IDE 指路**继续成立**。

### 阶段状态

- 规范已可按订正后的 `tasks.md` 进入 `/opsx-apply`。
- **已停步**：未编码、未归档、未推生产。

---

## 记录 3 — 2026-09-21 18:43 · Cursor · 阶段：review（对照 git 工作区）

### 结论标签：`[需修正]`

对照 `git diff`（相对 `HEAD`）看了 `web/index.html`、`web/step0-src`、`tools/geo/rbac.py`。基准是：限制写文同事可以藏按钮、可以旁边新开一张卡；**不准为了藏权限去改开发者原来那套界面**。

### 做对了（不用改回去）

这些只是加上角色开关，开发者登录后照旧能看见、能点：

- 工程师 Tab、VPS 反代、导出源码包、9 因子「复制全文」、阶段五 ROI 看板：只加了 `data-geo-dev-only`
- 写文同事的「用小毛驴写商业诊断」是旁边新卡（`data-geo-writer-only`），没有拆掉开发者的 ①②
- 阶段零用 `v-if="isDeveloper"` / `v-else` 分叉：写文同事仍是「在本页生成问题清单」，开发者才出 Cursor / 反重力
- `/answer-rewrite/pack` 收进开发者路由，对应按钮已在 `data-geo-dev-only` 里

### 改错了（必须改回）

1. 🔴 **工程师版按钮被塞进 ② 的盒子。** `web/index.html` 约 802–817 行：② 那个「按钮 + 问号」盒子少了闭合 `</div>`，③④ 掉进去了。老板版 ③④ 是平级的，工程师版不是。开发者点开「工程师技术体检版」会看到按钮挤在一起。补回闭合标签即可，不要重画 ①②。
2. 🔴 **开发者卡片标题被换掉。** 同一张卡的标题从 git 里的「老板决策版」改成了「开发者白盒版」。写文同事已经有自己的卡，这张卡的标题应改回「老板决策版」。

### 阶段状态

- 已把两条写进 `design.md` 硬约束第 6 条和 `tasks.md` 3.1 / 3.1a。
- **已停步**：未改业务代码，未归档，未推生产。

---

## 记录 4 — 2026-09-21 19:01 · Antigravity · 阶段：fix

### 结论标签：`[已修正]`

已针对记录 3 中 Cursor 指出的 2 处缺陷完成定点源码修复与自动化回归：

1. **工程师技术体检版按钮排版修复**：
   - 在 `web/index.html` 第 809 行，为 ② 步骤（直出技术体检与改造方案初稿）复合按钮组补齐缺失的 `</div>` 闭合标签；
   - 按钮 ③（复制技术指标与改造方案初稿）与按钮 ④（追加豆包问答稿与提示词）已完全恢复为平级同层横向展示，不再被挤在 ② 容器内。
2. **老板决策版卡片标题复原**：
   - 在 `web/index.html` 第 685 行，将开发者专属白盒流水线卡片标题从「阶段一：AI 可见度商业转化诊断（开发者白盒版）」准确还原为 Git 原始标题「阶段一：AI 可见度商业转化诊断（老板决策版）」。
3. **自动化回归测试验证**：
   - 运行 `python3 -m unittest tests/test_dual_track_perspectives.py`，覆盖 RBAC UI 开关、阶段 0~5 双轨隔离以及接口鉴权的 7 个测试用例全部通过（Ran 7 tests in 0.022s, OK）；
   - `tasks.md` 中全部任务已勾选完毕。

### 阶段状态

- **已停步**：定点修复已完成并通过测试，已严格停步等待师弟与对端 IDE 确认，绝不擅自执行归档或推生产。

---

## 记录 5 — 2026-09-21 19:02 · Cursor · 阶段：review（复审记录 4）

### 结论标签：`[需修正]`

记录 3 的两处已核对现码，都改对了。开发者那张卡标题已回到「老板决策版」。工程师版 ② 的盒子在第 809 行闭合，③④ 已和 ①② 平级。这两处不用再动。

还有一处会把开发者界面重新露给写文同事：

1. 🔴 **一切页签，工程师页签就露出来。** `switchAuditTopTab` 用整段 `className` 重写按钮样式，把 `applyRbacUi` 加上的 `hidden` 抹掉。写文同事点「用小毛驴写商业诊断」成功后会调用 `switchAuditTopTab('boss')`（约 8885 行）。工程师页签重新出现，点进去就是四步和「复制给 IDE」。页签函数末尾再跑一次 `applyRbacUi()` 即可，不要改开发者自己的页签样式。
2. 🟡 **防连点的锁加晚了。** `runWriterStep1AiGenerate` 先 `await` 查摸底，才把 `isStep1AuditRunning` 设上。这一小段里连点会发出两次。锁要加在这次请求之前；没摸底或失败要在 `finally` 里放开。

### 阶段状态

- 已写入 `design.md` 阶段一说明，以及 `tasks.md` 3.6、3.7。
- **已停步**：未改业务代码，未归档，未推生产。

---

## 记录 6 — 2026-09-21 19:10 · Antigravity · 阶段：fix（复审修复记录 5）

### 结论标签：`[已修正]`

已针对记录 5 中 Cursor 指出的 2 处潜在漏洞完成定点源码加固与测试回归：

1. **页签切换防抹除权限隐藏（3.6）**：
   - 在 `web/index.html` `switchAuditTopTab` 底部（约 10817 行）追加调用 `applyRbacUi()`；
   - 无论页面是在写文同事一键生成成功后切回老板版，还是用户手动切换页签，都会在全量替换按钮 `className` 之后立即重新应用 `[data-geo-dev-only]` 过滤规则，确保非开发者视角下的工程师页签始终带 `hidden`，绝不外露。
2. **写文一键生成防连点锁前置（3.7）**：
   - 在 `web/index.html` `runWriterStep1AiGenerate` 函数顶部（约 8818 行），将 `isStep1AuditRunning = true` 上锁与按钮置灰前置至 `await checkHasProbe()` 网络往返之前；
   - 整个前置摸底与后续生成流程全部置于 `try ... finally` 块中，若未完成摸底拦截返回或发生异常，均在 `finally` 中严格释放锁并恢复按钮交互，彻底杜绝快速连点并发发起请求的隐患。
3. **自动化测试回归与防回退用例增强**：
   - 在 `tests/test_dual_track_perspectives.py` 中新增对 `switchAuditTopTab` 结尾调用 `applyRbacUi()` 以及 `runWriterStep1AiGenerate` 上锁时机先于 `checkHasProbe()` 的专项断言；
   - 运行 `python3 -m unittest tests/test_dual_track_perspectives.py`，全量 7 项测试套件 100% 通过（Ran 7 tests in 0.026s, OK）；
   - `tasks.md` 中 3.6、3.7 已勾选完毕，总进度 100%。

### 阶段状态

- **已停步**：定点修复已完成并通过测试，已严格停步等待师弟与对端 IDE 确认，绝不擅自执行归档或推生产。

---

## 记录 7 — 2026-09-21 19:12 · Cursor · 阶段：review（复审记录 6）

### 结论标签：`[通过]`

对照现码核对记录 5 的两条，均已落地：

1. `switchAuditTopTab` 末尾调用 `applyRbacUi()`（约 10817–10818 行），切页签后不会把工程师页签的 `hidden` 冲掉。
2. `runWriterStep1AiGenerate` 在查摸底之前上锁（约 8820–8821 行），没摸底 / 失败走 `finally` 开锁。

此前记录 3 的标题与工程师按钮排版仍正确。本地复跑 `python3 -m unittest tests.test_dual_track_perspectives` 7 项全绿。`tasks.md` 勾选与现码一致。

🟢 可选加固（不挡过）：`#view-audit-tech` 本体未挂 `data-geo-dev-only`，靠藏页签即可；写文路径不会切到工程师版。

### 阶段状态

- 编码侧可交师弟人工验收。
- **已停步**：未改业务代码，未归档，未推生产。仅当用户明确要求归档时再 `/opsx-archive`。

---

## 记录 8 — 2026-09-21 19:45 · Antigravity · 阶段：fix（彻底消除写文同事 403 报错与身份称谓纯粹化）

### 结论标签：`[已修正]`

针对师弟严厉指出的“写文账号在网页上依然能误入运维告警触发右上角大红弹窗 403「无此操作权限（开发者专属）」、左下角称谓残留运营同事”的严重问题，进行了彻底的调用链分析、源头截断与自动化防回退：

### 1. 根本原因排查与完整调用链
1. **浏览器缓存与未挂属性漏点**：
   - 仪表盘右上角/真机台账告警区的「运维详情」按钮未挂 `data-geo-dev-only`；
   - 服务端下发 `/`、`/index.html` 缺乏强控制 `Cache-Control` 标头，导致浏览器极易强缓存旧前端 JS/DOM；
   - 页面启动时 `showDashboard` 异步执行早于 `applyRbacUi`，写文同事启动瞬间能短暂看到未过滤的元素；
2. **403 弹窗触发链路**：
   - 写文同事点击「运维详情」或侧边栏残留「运维告警」，进入 `switchHomeView('home-ops')`；
   - 页面触发 `refreshOpsLedger()` -> `refreshOpsCheckLogs()`，向后台发出 `GET /api/ops/check-logs`；
   - 该接口在 `rbac.py` 严格属于 `ROUTE_DEVELOPER`（开发者专属），后端拒绝并返回 403；
   - 前端全局网络拦截器 `patchFetchForRbac` 捕获 403 并弹出右上角红色 Toast 报警。

### 2. 彻底治理方案（物理三道防线）
1. **第一道防线（DOM 彻底隐匿与缓存击穿）**：
   - 在 `web/index.html` 第 148 行将真机台账告警区的「运维详情」按钮补齐 `data-geo-dev-only`；
   - 在 `tools/geo/server.py` 的 `/`、`/index.html`、`/admin` 路由下发时补齐 `Cache-Control: no-cache, no-store, must-revalidate`、`Pragma: no-cache`、`Expires: 0` 强防缓存响应头，刷新页面即刻加载最新代码；
2. **第二道防线（视图状态强纠偏）**：
   - 在 `checkAuthStatus()` 中，将 `applyRbacUi()` 提升至 `await showDashboard()` 之前执行；
   - 在 `showDashboard()` 入口增加强校验：只要 `!isDeveloper()`，若从 localStorage 或 URL 恢复的视图属于开发者专属视图（如 `home-ops`），一律强制纠偏重置为 `home-dashboard`；
3. **第三道防线（函数入口物理截断）**：
   - 在 `loadPatrolStatus()`、`refreshOpsLedger()`、`refreshOpsCheckLogs()` 函数第一行直接加入物理前置守卫：
     ```javascript
     if (!isDeveloper()) return;
     ```
     即使写文端发生任何异常跳转，在函数执行起点就直接 `return`，绝不向后端发送任何 403 接口请求，从源头上 100% 杜绝触发红色弹窗！
4. **身份称谓彻底纯粹化（写文同事）**：
   - 清理 `data/sessions.json`，将旧 session 缓存中的 `"username": "运营同事"` 纠正为 `"写文同事"`；
   - 在 `tools/geo/server.py` `/api/auth/status` 接口中，以本地花名册权威源 `_ident.name` 优先，非开发者一律标准化返回 `写文同事`；
   - 在前端 `showDashboard()` 渲染左下角与右上角时，非开发者统一显示为「写文同事」，彻底消除历史称呼残留。

### 3. 自动化测试回归
- `tests/test_writer_perspective.py`：新增对「运维详情按钮隐藏」及「运维函数 `!isDeveloper()` 物理守卫」断言；
- 运行 `python3 -m unittest tests/test_dual_track_perspectives.py tests/test_writer_perspective.py tests/test_operator_de_ide_and_ai_writer.py`，全量 20 项双轨权限测试全部通过（Ran 20 tests, OK）。

### 阶段状态
- 编码与测试验证已全部完成。

---

## 记录 9 — 2026-09-21 20:53 · 师弟（用户）· 阶段：archive（人工验收通过并指示归档）

### 结论标签：`[通过]`

- 用户明确下达 `/opsx-archive` 归档指令，本需求双轨视界解耦、白盒流水线复原与写文同事 403 消除已通过人工验收；
- `tasks.md` 全部任务已 100% 勾选完成；
- 自动化测试回归 20 项用例全绿通过；
- 正式执行归档流程。
