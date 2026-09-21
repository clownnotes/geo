# Proposal: 商业洞察页运营角色权限收敛与集团矩阵路由补登记

## Why (为什么做)

### 结论先行

**「商业洞察」是经营者/售前视角的商业变现工具集合，不是内容生产工具。当前它对运营角色完全敞开，但运营 0 使用、且其中 1 个入口对运营恒定报错、1 个入口构成越权面。**

### 一、角色定位与页面能力严重错配

RBAC 对运营的定位是明确的（`tools/geo/rbac.py:39-46`），运营只拥有 5 个原子权限，全部指向内容生产：

| 原子权限 | 语义 |
|---|---|
| `keyword:manage` | 词库导入、新增、修改、导出 |
| `ai:generate` | 语料提纯、文章生成、FAQ 生成 |
| `article:edit` | 编辑保存文章、更新元数据 |
| `preview:view` | 查看本地项目站点预览 |
| `report:view` | 查看 GEO 分析评测报告 |

同时 `rbac.py:912` 专门实现 `strip_partner_fields`，把「客户是谁的」从运营响应里抹掉——说明对运营的信任边界是**刻意收敛**的。

但「商业洞察」侧栏入口（`web/index.html:87`）**没有 `data-geo-dev-only` 属性**，角色裁剪机制（`applyRbacUi()`，`web/index.html:5365-5374`）对它不生效，8 个卡片（`web/index.html:315-322`）全部对运营可见。对照之下，同一侧栏的「系统设置」（`:89`）与「成员管理」（`:91`）都正确加了该属性。**权限模型与 UI 自相矛盾。**

### 二、实证：运营 0 使用（`data/operator_audit.jsonl`）

运营同事（`user_id=7d60e11b1f397703`，`allowed_projects=["nextgeo"]`）累计 **187 次请求，全部 HTTP 200，无一次报错**。按商业洞察 8 个卡片逐一核对接口调用：

| 卡片 | 后端接口 | 运营调用次数 | 判定 |
|---|---|---|---|
| 适合客群 (EDI) | 无（纯前端静态 + 两个下拉框算分） | 不适用 | 销售物料，与写文章无关 |
| 售前 Pitch | `GET /api/projects/{id}/pitch/data` | 0 | 含三档报价阶梯，越权面 |
| 全域大盘驾驶舱 | `GET /api/portfolio/summary` 等 | 0 | 老板视角，其仅 1 个客户无组合意义 |
| 工业化对标透视 | 无（纯静态对比表） | 不适用 | 销售话术页 |
| 行业大盘基准 | `GET /api/benchmark/industries` | 0 | 跨租户全库聚合 |
| 集团多品牌矩阵 | `GET /api/groups/{id}/matrix` | 0 | **恒定 403，坏入口** |
| AI 测序沙箱 | `POST /api/projects/{id}/playground/simulate` | 0 | 项目交付流程内已有入口，重复 |
| 商业 ROI 测算 | `GET /api/projects/{id}/roi/calculate` | 4（来自项目详情页，非本页） | 能力保留，本页入口冗余 |

运营的真实动线是：企业列表 → 项目报告 → 监测题/metrics → 站点预览 → 发帖 → 分发台账 → 验收，即标准的**内容交付流水线**，一个商业洞察入口都没碰过。

### 三、确证缺陷：集团矩阵对运营恒定 403

`GET /api/groups/{id}/matrix`（`tools/geo/server.py:4390-4399`）**未登记进 RBAC 路由表**：它不匹配项目级正则 `^/api/(?:v1/)?projects/([^/]+)(/.*)?$`，也不在 `ROUTE_AUTHENTICATED`（该集合是精确 `(path, method)` 匹配，无法覆盖动态路径），因此落入 D 档 fail-closed。以运营身份实测：

```
(False, 403, '该操作尚未开放给运营人员，请联系管理员开通')  GET /api/groups/xuanyuan_group/matrix
```

**这不是孤例，是随时会爆的地雷**：`web/index.html:7023-7025` 在企业列表里为「属于某集团」的项目渲染集团徽章，点击即调用 `openGroupMatrixModal(grp.group_id)`。运营当前管辖的 `nextgeo` 恰好不在任何集团内（`data/groups.json` 仅有 `xuanyuan_group` = `xuzhou_xuanyuan` + `demo_corp`），所以尚未暴露。**一旦把集团客户分配给运营，徽章立刻出现，点了就 403。**

此外该卡片入口写死默认参数 `openGroupMatrixModal(groupId = 'xuanyuan_group')`（`web/index.html:10804`），不带参数时永远打开「璇源控股集团」，与当前项目无关。

### 四、越权面：运营可改写 ROI 参数

`("/roi/settings", "article:edit")`（`rbac.py:589`）使运营**拥有 ROI 参数的写权限**。ROI 参数直接决定对外测算口径与 Pitch 报价基线，属商务数据，不应由纯使用角色改写。

### 五、附带问题：命名黑话

卡片描述使用内部术语「EDI」「Pitch」「工业化对标透视」「全域大盘驾驶舱」，运营无法从字面判断用途，第一反应是「这跟我有什么关系」。

---

## What Changes (改动了什么)

### 1. 商业洞察整页收敛为开发者专属（前端 + 服务端双收敛）

- 前端：只给侧栏入口 `#nav-home-insights` 加 `data-geo-dev-only`。面板 `#panel-home-insights` **禁止**加这个属性（`applyRbacUi()` 会给开发者去掉 `hidden`，面板会脱离视图切换、一直摊在仪表盘上）。运营若从地址栏直接进该页，由 `switchHomeView()` 拦住并提示。
- 仪表盘「全域商业总价值」卡片已经包在 `#dashboard-dev-section[data-geo-dev-only]` 里，运营本来就看不见，本期不再给内层卡片重复加属性。
- 服务端：**前端隐藏不是安全边界**（既有 design 原则），必须同步把商业洞察专属接口重新归类，详见第 2 条。

### 2. 服务端路由重分类（`tools/geo/rbac.py`）

| 路由 | 现档位 | 现权限 | 改为 | 理由 |
|---|---|---|---|---|
| `GET /api/portfolio/summary` | ROUTE_AUTHENTICATED (`:515`) | 登录即放行 | 开发者专属 | 组合 ROI / 服务费 / 净增收益 |
| `GET /api/portfolio/report` | ROUTE_AUTHENTICATED (`:516`) | 登录即放行 | 开发者专属 | 大盘执行报告 |
| `POST /api/portfolio/patrol` | ROUTE_AUTHENTICATED (`:517`) | 登录即放行 | 开发者专属 | 全域健康扫描 |
| `GET /api/benchmark/industries` | ROUTE_AUTHENTICATED (`:519`) | 登录即放行 | 开发者专属 | 跨租户全库行业聚合 |
| `/pitch/data` `/pitch/slides` `/pitch/print` | ROUTE_PERMISSION_SUFFIXES (`:649-651`) | `report:view` | 移入 `ROUTE_DEVELOPER_SUFFIXES`，并从权限后缀表删除 | 报价。只删后缀表不够：`GET` 还会掉进只读兜底 `/data`、`/print`，运营照样能看 |
| `/roi/settings` | 同上 (`:589`) | `article:edit` | 移入 `ROUTE_DEVELOPER_SUFFIXES`，并从权限后缀表删除 | 运营不得改写 ROI 口径 |
| `/roi/calculate` | 同上 (`:590`) | `report:view` | **保留** | 运营实测在项目内使用（4 次），属交付动作 |
| `/playground/simulate` `/playground/batch` | 同上 (`:602-603`) | `preview:view` | **保留** | 运营可用，项目内入口 |
| `/intent/matrix` | 同上 (`:599`) | `report:view` | **保留** | 这才是 `/api/projects/{id}/intent/matrix`，与集团 `/matrix` 不是同一条 |
| `/matrix` | 同上 (`:691`) | `report:view` | **保留并改注释** | 源码注释写的是集团矩阵，不是意图矩阵。删了它不会弄坏意图矩阵 |

### 3. 集团级路由守卫与矩阵路由补登记

新增「集团级」判定档，在项目级（C 档）之前插入：

- 新增 `_GROUP_ROUTE_RE = re.compile(r"^/api/(?:v1/)?groups/([^/]+)(/.*)?$")`；
- 解析 `group_id` 后，复用既有 `filter_groups()` 的可见性口径：母公司或任一子项目在 `allowed_projects` 内即可打开；
- 不可见 → 403「无权访问该集团」；
- 可见且路径是 `GET .../matrix` → 需要 `report:view` 后放行；
- **不要**把整段 `_match_permission()` 套到集团路径上。那个函数对 `GET` 有只读兜底（`/data`、`/print` 等），未登记的集团接口会被误放行。其它集团路径一律 fail-closed。

放行之后还要裁响应，不能只看「能不能打开」：

- `GET /api/groups` 已经用 `filter_groups()` 拿掉没分配的子项目；
- `calculate_group_matrix()` 却返回整份集团（兄弟品牌的声量、引用、汇总数字都在）；
- 只分到其中一个品牌的运营，若直接放行，会看到没分给他的品牌。

因此 `server.py` 里该接口在返回前按 `allowed_projects` 裁一刀（开发者仍看全量）。计算引擎 `group.py` 不改。细则见 `design.md`。

### 4. 集团矩阵卡片入口参数修正

`openGroupMatrixModal()` 与 `loadGroupMatrixData()` 的默认参数 `'xuanyuan_group'` 都去掉。无参时按当前项目反查所属集团（只查 `children[].project_id`，现有母公司也在 children 里），查不到就提示「当前企业不属于任何集团」，不要打开无关集团。

### 5. 卡片文案去黑话

| 现文案 | 建议文案 |
|---|---|
| 适合客群 (EDI) | 适合什么样的客户 |
| 工业化对标透视 | 流水线和手工代运营差在哪 |
| 全域大盘驾驶舱 | 全部客户的经营数字 |

---

## Capabilities (新增或修改的对外能力)

| 能力 | 类型 | 说明 |
|---|---|---|
| 商业洞察页角色裁剪 | 修改 | 运营登录后侧栏不再出现「商业洞察」，页面不可达 |
| 商业洞察接口开发者专属化 | 修改 | 8 条商业洞察专属路由对运营返回 403（4 条大盘/行业 + 3 条报价 + ROI 参数写入）。服务端强制，不是只藏按钮 |
| 集团级路由守卫 | 新增 | `/api/groups/{id}/...` 按 `allowed_projects` 判定能否打开；只放行 `GET .../matrix` |
| 集团矩阵响应裁剪 | 新增 | 运营只看到分给自己的品牌；兄弟品牌的行和全集团汇总数不返回 |
| 集团矩阵路由可用 | 修复 | 分到该集团任一企业的运营不再 403；没分到的仍是「无权访问该集团」 |
| 集团矩阵入口参数修正 | 修复 | 卡片按当前项目反查集团，不再写死 `xuanyuan_group` |
| 运营交付能力零损失 | 约束 | `/roi/calculate`、`/playground/*`、`/api/projects/{id}/intent/matrix` 均保留，运营动线不变 |

## FAQ

**Q1：隐藏整页会不会让运营失去必要能力？**
不会。8 个卡片中，运营唯一有真实使用痕迹的是 ROI 测算（4 次），而该能力在项目详情页有独立入口且本期保留；AI 测序沙箱在交付流程（04/05 步）同样有入口。整页隐藏后，运营动线零变化。

**Q2：为什么不只改前端，还要改服务端？**
既有 design 已确立「前端过滤只是体验优化，不是安全边界」。仅改前端，运营 F12 或直接 curl 仍可拿到组合 ROI 与报价数据。

**Q3：集团矩阵为什么不直接做成开发者专属，而要做集团级守卫？**
因为该接口的入口不止商业洞察一处：企业列表的集团徽章（`web/index.html:7025`）会为「属于某集团」的项目渲染按钮。做集团级守卫可同时修好两条路径。只分到其中一个品牌时，徽章仍在，但矩阵里只出现分给他的品牌，不把兄弟品牌的数字一并给出去。

**Q4：本期是否引入「内容参谋」新页？**
不引入。经评估运营当前无此需求（0 使用），新增页面属于无依据扩张。若后续确有需求，另开变更。

## Impact (受影响的部分)

| 文件 | 行数量级 | 改动 |
|---|---|---|
| `web/index.html` | 约 15965 行 | 侧栏 `:87` 加 `data-geo-dev-only`；面板 `:303` **不加**；`switchHomeView` 拦截运营进入；去掉两处 `xuanyuan_group` 默认值；卡片标题改白话 |
| `tools/geo/rbac.py` | 约 942 行 | 4 条大盘/行业移入 `ROUTE_DEVELOPER`；3 条报价 + `/roi/settings` 移入 `ROUTE_DEVELOPER_SUFFIXES`；新增集团级分支与矩阵响应裁剪函数 |
| `tools/geo/server.py` | 约 6197 行 | 不新增路由。`GET /api/groups/{id}/matrix` 返回前调用裁剪函数。分享链接 `/api/share/` 仍走公开白名单，不受报价后缀收紧影响 |
| `tests/` | — | 新增运营身份对 8 条商业洞察路由的 403 断言（含 `/pitch/data`、`/pitch/print` 不被只读兜底放行）、集团守卫与矩阵裁剪正反用例、分享链接仍公开 |

**明确不改：**
- 不改任何业务引擎（`pitch.py` / `portfolio.py` / `benchmark.py` / `group.py` / `roi.py` / `playground.py`）；
- 不改流水线阶段语义与运营交付动线；
- 不新增页面、不删任何能力；
- 不动 `data/groups.json` 与 `data/rbac_members.json` 结构。

**测试与协同：**
- 本地 `http://127.0.0.1:8088` 验证；**严禁私自推生产**；
- 视觉：严禁新增 Emoji，企业风靠 Tag / 字阶 / 分组卡片；
- 跨 IDE：需在 `review-log.md` 对齐后再进入 apply。
