# Tasks: 商业洞察页运营角色权限收敛与集团矩阵路由补登记

> 约定：方括号勾选框未勾选表示未完成，已勾选表示已完成。严格按本清单编码，测试通过后**立即停步**向用户汇报，严禁擅自归档或推生产。

## 1. 准备工作

- [x] 1.1 核对全局规则：重读 `AGENTS.md` 第 3/4 节（GEO 编码约束、生产发布协议）与 `.workbuddy/skills/opsx/SKILL.md` 阶段铁律。
- [x] 1.2 基线采集：运行 `python3 -m unittest tests/test_rbac.py`，记录变更前通过数（当前基线 61 项），作为回归对照。
- [x] 1.3 复核事实：确认 `web/index.html:87` 侧栏入口当前**无** `data-geo-dev-only`；确认 `tools/geo/rbac.py:515-519`、`:589`、`:649-651` 四条目行号与 `proposal.md` 一致（文件会随改动漂移，动手前重新定位）。
- [x] 1.4 复核 `switchHomeView()`（`web/index.html:6183`）与 `applyRbacUi()`（`:5365`）现状，确认 `.home-panel` 的显隐仍由 `hidden` 类统一管理。

## 2. 后端：集团级守卫（先做，独立可测）

- [x] 2.1 在 `tools/geo/rbac.py` 新增 `_GROUP_ROUTE_RE = re.compile(r"^/api/(?:v1/)?groups/([^/]+)(/.*)?$")`，置于 `_PROJECT_ROUTE_RE`（`:730`）旁并加注释说明两档关系。
- [x] 2.2 新增模块级缓存 `_GROUPS_CACHE = {"mtime": 0.0, "data": {}}` 与 `_load_groups_cached()`：按 `os.path.getmtime()` 失效，解析失败回退空 `dict` 并打 `WARNING`（fail-closed），不抛异常。
- [x] 2.3 新增 `_can_access_group(group_id, identity)`：开发者放行；`identity` 为空返回 `False`；否则母公司 `parent_project_id` 或任一 `children[].project_id` 命中 `allowed_projects` 即放行。判定语义必须与 `filter_groups()`（`:853`）一致。
- [x] 2.4 在 `guard_route()` 中，于「开发者全放行」之后、项目级分支之前插入集团级分支。不可见 → `403 无权访问该集团`。只放行 `GET` 且路径以 `/matrix` 结尾、并具备 `report:view` 的请求；缺权限 → `403 缺少相应操作权限（需要 report:view）`。其它集团路径打 WARNING 并 `403 该操作尚未开放给运营人员，请联系管理员开通`。**禁止**在此分支调用 `_match_permission()`。
- [x] 2.5 新增 `redact_group_matrix(payload, identity)`：开发者原样返回；非开发者按 design.md 第 7 节裁 `children_matrix`、`shared_citations` 与汇总字段；`parent_project_id` 未授权则清空；段位文案禁止表情符号。
- [x] 2.6 `server.py` 的 `GET /api/groups/{id}/matrix` 在 `send_json` 前调用 `redact_group_matrix`。不改 `group.py` 的计算函数。`guard_route()` 签名仍是三元组。

## 3. 后端：路由重分类

- [x] 3.1 `ROUTE_AUTHENTICATED`（`rbac.py:503-520`）删除 4 条：`("/api/portfolio/summary","GET")`、`("/api/portfolio/report","GET")`、`("/api/portfolio/patrol","POST")`、`("/api/benchmark/industries","GET")`。
- [x] 3.2 上述 4 条移入 `ROUTE_DEVELOPER`（`:523-532`），并按既有注释风格补充归属说明（组合 ROI / 服务费 / 跨租户行业聚合）。
- [x] 3.3 从 `ROUTE_PERMISSION_SUFFIXES` 删除 4 条：`("/pitch/data","report:view")`、`("/pitch/slides","report:view")`、`("/pitch/print","report:view")`、`("/roi/settings","article:edit")`。
- [x] 3.4 把这 4 条后缀放进 `ROUTE_DEVELOPER_SUFFIXES`（B 档，先于权限匹配和只读兜底）。只删权限表不够：`GET` 的 `/pitch/data`、`/pitch/print` 会掉进 `ROUTE_READONLY_SUFFIXES` 的 `/data`、`/print`。
- [x] 3.5 **保留** `("/intent/matrix","report:view")`（`:599`，这才是项目意图矩阵）。**保留** `("/matrix","report:view")`（`:691`）并把注释改成「集团矩阵短后缀，不是意图矩阵；集团分支不靠它放行」。
- [x] 3.6 **保留** `("/roi/calculate","report:view")` 与 `("/playground/simulate","preview:view")`、`("/playground/batch","preview:view")`，并补注释说明「运营交付动线在用，勿动」。
- [x] 3.7 确认 `GET /api/groups` 仍命中 `ROUTE_AUTHENTICATED`，`POST /api/groups` 仍拒绝，`/api/share/` 仍走公开前缀、不受报价后缀收紧影响。

## 4. 前端：角色裁剪与入口修正

- [x] 4.1 `web/index.html:87` 侧栏 `#nav-home-insights` 增加 `data-geo-dev-only`。
- [x] 4.2 确认仪表盘「全域商业总价值」卡片（`:157`）已在 `#dashboard-dev-section[data-geo-dev-only]`（`:135`）内部。不要再给内层卡片加 `data-geo-dev-only`。
- [x] 4.3 `switchHomeView()`（`:6183`）顶部插入守卫：`viewId === 'home-insights' && !isDeveloper()` → `showToast('该功能仅开发者可用','error')` 并 `return`。
- [x] 4.4 **不得**在 `#panel-home-insights`（`:303`）上加 `data-geo-dev-only`；在 `:303` 处补一行 HTML 注释说明该约束。
- [x] 4.5 修正 `openGroupMatrixModal()`（`:10804`）和 `loadGroupMatrixData()`（`:10814`）：去掉默认参数 `'xuanyuan_group'`。无参时用 `resolveGroupIdByProject(currentProjectId)` 反查；查不到 → `showToast('当前企业不属于任何集团','warning')` 并 `return`。`loadGroupMatrixData` 没拿到集团编号也不发请求。
- [x] 4.6 新增 `resolveGroupIdByProject(projectId)`，复用既有 `groupMapCache`（只含 `children[].project_id`），不新增接口调用。
- [x] 4.7 卡片标题改白话：`适合客群 (EDI)` → `适合什么样的客户`；`工业化对标透视` → `流水线和手工代运营差在哪`；`全域大盘驾驶舱` → `全部客户的经营数字`。
- [x] 4.8 全量自检：确认本次未新增任何 Emoji；确认所有新增注释与文案为中文。

## 5. 测试与验证

- [x] 5.1 回归基线：`python3 -m unittest tests/test_rbac.py` 全绿（67 项通过，高于基线 61 项）。
- [x] 5.2 新增测试：运营身份（`allowed_projects=["nextgeo"]`）对 8 条商业洞察路由断言 `403`——`/api/portfolio/summary`、`/api/portfolio/report`、`/api/portfolio/patrol`、`/api/benchmark/industries`、`/api/projects/nextgeo/pitch/data`、`/pitch/slides`、`/pitch/print`、`/roi/settings`。其中 `/pitch/data` 与 `/pitch/print` 必须是 403，用来证明没有掉进只读兜底。
- [x] 5.3 新增测试：集团级守卫——`allowed_projects=["xuzhou_xuanyuan"]` 访问 `GET /api/groups/xuanyuan_group/matrix` 守卫放行；`allowed_projects=["nextgeo"]` 返回 `403 无权访问该集团`；同集团的非 matrix 路径返回 `403`。
- [x] 5.4 新增测试：`redact_group_matrix`——只授权 `demo_corp` 时，响应 `children_matrix` 不含 `xuzhou_xuanyuan`，且 `group_sov` 不是全集团原值。开发者身份返回不裁剪。
- [x] 5.5 新增测试：开发者身份对 5.2 涉及的路由断言放行。`/api/share/demo-token/pitch/print` 在未登录时仍放行。
- [x] 5.6 新增测试：`("/intent/matrix","report:view")` 仍在，运营访问 `/api/projects/nextgeo/intent/matrix` 放行。`("/matrix","report:view")` 仍在，但注释不得再写成意图矩阵。
- [x] 5.7 新增静态测试：扫描 `web/index.html`，断言 `data-geo-dev-only` **未出现在任何** `class` 含 `home-panel` 的元素上。
- [x] 5.8 本地人工走查（`http://127.0.0.1:8088`）：开发者——商业洞察侧栏可见、卡片可点、集团矩阵按当前项目打开且是全量；运营——侧栏无商业洞察、地址栏直达该页会被拦下、企业列表里分到的集团徽章能打开且只看到自己的品牌、无 403 弹窗刷屏。
- [x] 5.9 合规自检：本次不改文章模板则不必跑样式脚本；若改了 HTML 文案，确认没有新增 Emoji。

## 6. 收尾（严格停步）

- [x] 6.1 汇总变更清单（文件 + 行号 + 一句话说明）与测试结论，在对话中向用户汇报。
- [x] 6.2 用户已确认验收，下发 /opsx-archive 归档指令。
- [x] 6.3 执行归档与推送。
