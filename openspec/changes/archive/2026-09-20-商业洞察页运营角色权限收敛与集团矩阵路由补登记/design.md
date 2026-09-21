# Design: 商业洞察页运营角色权限收敛与集团矩阵路由补登记

## Architecture (架构设计与对象关系)

### 1. 守卫模型：由「四档」扩为「五档」

现网 `guard_route()`（`tools/geo/rbac.py:787-850`）为四档判定，判定顺序严格，前一档命中即返回：

```
A 公开白名单 → B 开发者专属 → 已登录放行表 → 开发者全放行 → C 项目级 → D fail-closed
```

本期在 **开发者全放行之后、项目级之前** 插入「集团级」一档，形成五档：

```
A 公开白名单
B 开发者专属
已登录放行表（ROUTE_AUTHENTICATED，精确 (path, method) 匹配）
开发者全放行
C 集团级（本期新增）      ← /api/(v1/)?groups/{id}/...
D 项目级（原 C 档）        ← /api/(v1/)?projects/{id}/...
E 兜底 fail-closed（原 D 档）
```

**插入位置的理由**：集团级路径形如 `/api/groups/{id}/matrix`，既不会被项目级正则 `^/api/(?:v1/)?projects/([^/]+)(/.*)?$` 匹配，也不在精确匹配的 `ROUTE_AUTHENTICATED` 中，因此当前必然落入兜底档。放在项目级之前，可保证两者互不干扰。

### 2. 涉及对象与依赖

| 对象 | 位置 | 角色 |
|---|---|---|
| `Identity` | `rbac.py:134` | 身份快照，含 `is_developer` / `allowed_projects` / `permissions` |
| `ROUTE_AUTHENTICATED` | `rbac.py:503-520` | 精确匹配的「已登录即可访问」集合 |
| `ROUTE_PERMISSION_SUFFIXES` | `rbac.py:559-697` | 项目级「动作后缀 → 原子权限」映射 |
| `ROUTE_DEVELOPER` | `rbac.py:523-532` | 开发者专属集合 |
| `guard_route()` | `rbac.py:787` | 统一守卫，签名不变 |
| `filter_groups()` | `rbac.py:853` | 既有集团裁剪逻辑，本期**复用其判定语义** |
| `load_groups_config()` | `group.py` | 读取 `data/groups.json` |
| `applyRbacUi()` | `web/index.html:5365` | 前端角色裁剪，基于 `[data-geo-dev-only]` |
| `switchHomeView()` | `web/index.html:6183` | 视图切换入口 |

**依赖方向**：`rbac.py` 不得在模块顶层 import `group.py`（`group.py` 依赖 `utils.py` / `monitor.py`，顶层互引有循环风险）。集团配置读取采用**函数内延迟导入**，与 `server.py:4383` 既有写法保持一致。

### 3. 前端裁剪机制的关键约束

`applyRbacUi()` 对 `[data-geo-dev-only]` 元素的处理是 **`classList.remove('hidden')`（开发者）/ `add('hidden')`（运营）**。

由此产生一条硬约束：

> **`data-geo-dev-only` 严禁直接加在 `.home-panel` 容器上。**
> 因为 `.home-panel` 的显隐由 `switchHomeView()` 通过 `hidden` 类统一管理；若开发者身份触发 `remove('hidden')`，该面板将脱离 `switchHomeView` 控制而**常驻显示**，导致仪表盘视图被覆盖。

正确做法：导航入口用 `data-geo-dev-only`，面板本身改由 `switchHomeView()` 内部守卫拦截。

---

## Interface (接口/API/前端组件设计)

### 1. 后端新增（`tools/geo/rbac.py`）

```python
# 集团级路由：/api/groups/{id}/... 或 /api/v1/groups/{id}/...
_GROUP_ROUTE_RE = re.compile(r"^/api/(?:v1/)?groups/([^/]+)(/.*)?$")


def _can_access_group(group_id, identity):
    """集团可见性判定：开发者全放行；运营须母公司或任一子项目在 allowed_projects 内。

    判定语义与 filter_groups() 保持一致，避免同一份 groups.json 出现两套可见性口径。
    配置读取延迟导入 + 进程内缓存，避免每条请求读盘。
    """
```

`guard_route()` 中新增分支（伪代码，插入点见架构第 1 节）：

```python
    # 集团级。不要调用 _match_permission()：
    # 它对 GET 有 ROUTE_READONLY_SUFFIXES 兜底（/data、/print 等），
    # 未登记的集团路径会被误放行。
    g = _GROUP_ROUTE_RE.match(path)
    if g:
        group_id = g.group(1)
        if not _can_access_group(group_id, identity):
            return False, 403, "无权访问该集团"
        if method == "GET" and path.endswith("/matrix"):
            if not identity.has_permission("report:view"):
                return False, 403, "缺少相应操作权限（需要 report:view）"
            return True, 200, ""
        logger.warning("[RBAC] 未登记集团级路由被拦截(fail-closed): %s %s user=%s",
                       method, path, identity.user_id or identity.phone)
        return False, 403, "该操作尚未开放给运营人员，请联系管理员开通"
```

**签名与返回值**：`guard_route(path, method, identity) -> (ok: bool, status: int, msg: str)` **保持不变**。四个 `do_*` 入口的调用方式不变。`GET /api/groups/{id}/matrix` 的处理函数在 `send_json` 前多调一次裁剪，见第 7 节。

### 2. 路由归类变更（前后对照）

| 路由 | 变更前档位 | 变更前权限 | 变更后 | 变更后效果（运营身份） |
|---|---|---|---|---|
| `GET /api/portfolio/summary` | 已登录放行 (`rbac.py:515`) | 登录即 200 | 移入 `ROUTE_DEVELOPER` | 403 开发者专属 |
| `GET /api/portfolio/report` | 已登录放行 (`:516`) | 登录即 200 | 移入 `ROUTE_DEVELOPER` | 403 开发者专属 |
| `POST /api/portfolio/patrol` | 已登录放行 (`:517`) | 登录即 200 | 移入 `ROUTE_DEVELOPER` | 403 开发者专属 |
| `GET /api/benchmark/industries` | 已登录放行 (`:519`) | 登录即 200 | 移入 `ROUTE_DEVELOPER` | 403 开发者专属 |
| `GET /api/projects/{id}/pitch/data` | 项目级 (`:649`) | `report:view` | 移入 `ROUTE_DEVELOPER_SUFFIXES`，并从权限后缀表删除 | 403 开发者专属。只删表会被只读兜底 `/data` 重新放行 |
| `GET /api/projects/{id}/pitch/slides` | 项目级 (`:650`) | `report:view` | 同上 | 403 开发者专属 |
| `GET /api/projects/{id}/pitch/print` | 项目级 (`:651`) | `report:view` | 同上 | 403 开发者专属。只删表会被只读兜底 `/print` 重新放行 |
| `POST /api/projects/{id}/roi/settings` | 项目级 (`:589`) | `article:edit` | 移入 `ROUTE_DEVELOPER_SUFFIXES`，并从权限后缀表删除 | 403 开发者专属 |
| `GET /api/projects/{id}/roi/calculate` | 项目级 (`:590`) | `report:view` | **不变** | 200（运营交付动线保留） |
| `POST /api/projects/{id}/playground/simulate` | 项目级 (`:602`) | `preview:view` | **不变** | 200 |
| `POST /api/projects/{id}/playground/batch` | 项目级 (`:603`) | `preview:view` | **不变** | 200 |
| `GET /api/projects/{id}/intent/matrix` | 项目级 (`:599` `/intent/matrix`) | `report:view` | **不变** | 200。与 `:691` 的短后缀 `/matrix` 不是同一条 |
| `GET /api/groups/{id}/matrix` | 兜底 fail-closed | — | 集团级，仅 `GET` 且以 `/matrix` 结尾 | 看得见该集团则放行，响应再裁剪；看不见则 403「无权访问该集团」 |
| `GET /api/share/{token}/pitch/*` | 公开前缀 `/api/share/` | 无需登录 | **不变** | 公开白名单在开发者后缀之前命中，报价收紧不得误伤分享链接 |
| `GET /api/groups` | 已登录放行 (`:509`) | 登录即 200 | **不变**（精确匹配，先于集团级分支命中） | 200，响应按 `filter_groups` 裁剪 |
| `POST /api/groups` | 兜底 fail-closed | — | **不变**（集团分支只放行 `GET .../matrix`） | 403（符合预期：运营不建集团） |

**`/intent/matrix`（`:599`）才是项目意图矩阵，必须保留。**  
**`/matrix`（`:691`）源码注释已经写明是 `/api/groups/{id}/matrix`。** 删掉它不会弄坏意图矩阵。本期仍保留该行并改注释，避免短后缀的用途被再次写错；集团分支不靠 `_match_permission()` 去认它。

### 3. 前端改动

| 位置 | 改动 | 说明 |
|---|---|---|
| `web/index.html:87` | `#nav-home-insights` 增加 `data-geo-dev-only` | 侧栏入口对运营隐藏 |
| `web/index.html:157` | 仪表盘「全域商业总价值」 | **不加** `data-geo-dev-only`。该卡片已在 `#dashboard-dev-section`（`:135`，已有该属性）内部，运营看不见 |
| `web/index.html:6183` | `switchHomeView()` 顶部增加守卫 | 见下 |
| `web/index.html:10804` | `openGroupMatrixModal()` 默认参数修正 | 见第 4 条 |
| `web/index.html:303` | 面板 `#panel-home-insights` | **不加** `data-geo-dev-only`（见架构第 3 节硬约束） |
| `web/index.html:315-322` | 卡片文案 | 去黑话，见第 5 条 |

`switchHomeView()` 守卫：

```javascript
    async function switchHomeView(viewId, skipRoute) {
      // [2026-09-20] 商业洞察为开发者专属视图，前端拦一道体验层，安全边界在服务端守卫
      if (viewId === 'home-insights' && !isDeveloper()) {
        showToast('该功能仅开发者可用', 'error');
        return;
      }
      currentHomeView = viewId || 'home-dashboard';
      ...
```

### 4. 集团矩阵入口参数修正

```javascript
    // 变更前：两处都写死 xuanyuan_group
    async function openGroupMatrixModal(groupId = 'xuanyuan_group') { ... }
    async function loadGroupMatrixData(groupId = 'xuanyuan_group') { ... }

    // 变更后：无参时按当前项目反查，查不到就停
    async function openGroupMatrixModal(groupId) {
      const gid = groupId || resolveGroupIdByProject(currentProjectId);
      if (!gid) { showToast('当前企业不属于任何集团', 'warning'); return; }
      ...
      await loadGroupMatrixData(gid);
    }
```

`loadGroupMatrixData(groupId)` 去掉默认参数。没传 `groupId` 就提示并返回，不再请求。

`resolveGroupIdByProject(projectId)` 复用前端既有 `groupMapCache`（由 `/api/groups` 构建，只登记 `children[].project_id`）。现有母公司 `xuzhou_xuanyuan` 也在 children 里，所以能反查到。不新增接口。

### 5. 卡片文案

| 现文案 | 建议文案 |
|---|---|
| 适合客群 (EDI) | 适合什么样的客户 |
| 工业化对标透视 | 流水线和手工代运营差在哪 |
| 全域大盘驾驶舱 | 全部客户的经营数字 |

### 6. 错误响应规范（保持既有文案风格）

| 场景 | HTTP | 文案 |
|---|---|---|
| 集团不可见 | 403 | 无权访问该集团 |
| 集团级未登记动作 | 403 | 该操作尚未开放给运营人员，请联系管理员开通 |
| 集团级动作缺权限 | 403 | 缺少相应操作权限（需要 report:view） |
| 商业洞察专属接口 | 403 | 无此操作权限（开发者专属） |

### 7. 集团矩阵响应裁剪（`tools/geo/rbac.py` + `server.py` 一处调用）

`calculate_group_matrix()` 不改。开发者仍拿它的全量返回。

非开发者在 `server.py` 的 `GET /api/groups/{id}/matrix` 里，`send_json` 之前调用 `redact_group_matrix(payload, identity)`：

1. `children_matrix` 只留 `project_id` 在 `allowed_projects` 里的行。
2. `shared_citations` 里的品牌名只留授权品牌；一条里不足 2 个授权品牌则整条删除。
3. 若删掉了任何子品牌：禁止把原来的 `group_sov`、`synergy_index`、`synergy_multiplier`、`tier`、`summary`、`total_brands`、`total_prompts`、`total_unique_citation_domains`、`shared_citations_count` 原样返回。`total_brands` / `total_prompts` 按留下来的行重数；`shared_citations_count` 按裁剪后的共享列表重数。`group_sov` 只用留下来的行、按各行已有的 `weight` 与 `sov_pct` 做加权平均（权重和为 0 时记 0）。`tier` 与 `summary` 用纯文字「只统计你负责的品牌」，**禁止**复制 `group.py` 里带表情符号的段位文案。
4. `parent_project_id` 不在授权名单里就清空，与 `filter_groups()` 一致。
5. 一个子品牌都没留下：不当成 200 成功页，按无权访问处理（正常路径下守卫已拦住，这是兜底）。

分享链接不走这条裁剪。报价后缀收进 `ROUTE_DEVELOPER_SUFFIXES` 后，`/api/share/` 仍由公开前缀先放行。

---

## Database Schema / Data Structure (数据模型变更)

### 结论：无数据结构变更

| 数据 | 路径 | 本期是否改动 |
|---|---|---|
| 集团层级配置 | `data/groups.json` | 不改（结构、字段、内容均不变） |
| 成员花名册 | `data/rbac_members.json` | 不改（运营的 5 个原子权限与 `allowed_projects` 均不变） |
| 操作审计日志 | `data/operator_audit.jsonl` | 不改（403 事件由既有审计链路记录） |

### 新增的进程内缓存（非持久化）

`_can_access_group()` 需要读取 `data/groups.json`。为避免每条集团级请求读盘，采用与 `rbac.py` 既有风格一致的模块级缓存：

```python
_GROUPS_CACHE = {"mtime": 0.0, "data": {}}

def _load_groups_cached():
    """按文件 mtime 失效的进程内缓存；文件缺失或解析失败时返回空 dict，绝不抛异常。"""
```

缓存策略要点：

1. 以 `os.path.getmtime()` 为失效键，配置变更后下次请求自动重载，无需重启服务；
2. 解析失败回退空 `dict` 并打 `WARNING`，**fail-closed**（查不到集团即视为不可见）；
3. 不引入外部依赖，不使用 `functools.lru_cache`（无法感知文件变更）。

---

## 方案取舍记录

| 方案 | 内容 | 结论 |
|---|---|---|
| **A（本期采用）** | 商业洞察整页收敛为开发者专属；服务端同步重分类；补集团级守卫 | 与 RBAC 铁律一致，改动最小，运营动线零变化 |
| B | 拆分页面：开发者看「经营大盘」，运营看新建的「内容参谋」页（仅留 EDI 与工业化对标两项静态物料） | **本期不采用**。运营 0 使用，新增页面属无依据扩张；且 EDI / 工业化对标均为纯静态销售话术，与写文章无关。若后续确有需求另开变更 |
| C | 仅改前端隐藏，不动服务端 | **禁止**。违反既有「前端过滤不是安全边界」原则，curl 即可绕过 |

## 风险与回归边界

| 风险 | 缓解 |
|---|---|
| 只从权限表删掉 `/pitch/data`、`/pitch/print`，GET 仍被只读兜底放行 | 改为进入 `ROUTE_DEVELOPER_SUFFIXES`（B 档在权限匹配之前拦截），并用运营身份断言这两条 403 |
| 把 `/matrix` 当成意图矩阵的登记而删掉 `/intent/matrix` | 意图矩阵是 `:599` 的 `/intent/matrix`。回归断言这条仍在，且运营访问项目意图矩阵仍放行 |
| `data-geo-dev-only` 误加到 `.home-panel` 导致面板常驻 | 面板禁止加该属性，回归用例扫描 HTML |
| 集团分支调用 `_match_permission()`，未登记 GET 被只读兜底放行 | 集团分支只认 `GET .../matrix`，其它路径 fail-closed |
| 只放行矩阵、不裁响应，运营看到兄弟品牌数字 | `redact_group_matrix` 在返回前裁剪；单品牌授权用例断言响应里没有另一个 `project_id` |
| 报价后缀收紧误伤 `/api/share/{token}/pitch/print` | 公开前缀先于 B 档命中；回归断言未登录访问分享路径仍放行 |
| 集团缓存与 `filter_groups` 口径不一致 | `_can_access_group` 与 `filter_groups` 同一判定：母公司或任一子项目命中 |
| 运营侧仪表盘出现 403 弹窗刷屏 | 运营不调用 `/api/portfolio/summary`；大盘卡片已在开发者板块内 |

**回归范围：**
1. `tests/test_rbac.py` 既有 61 项全绿；
2. 新增：运营身份对 8 条商业洞察路由断言 403（含 `/pitch/data`、`/pitch/print`）；
3. 新增：集团级守卫——分到任一品牌可打开矩阵；没分到返回 403；未登记集团动作 403；
4. 新增：只分到 `demo_corp` 时，矩阵响应不含 `xuzhou_xuanyuan`，且汇总数不是全集团原值；
5. 新增：开发者对上述路由仍放行，矩阵响应仍是全量；
6. 新增：`/api/projects/{id}/intent/matrix` 对运营仍放行；`/api/share/` 下报价路径仍公开；
7. 新增：静态断言 `data-geo-dev-only` 未出现在任何 `home-panel` 上；
8. 本地 `http://127.0.0.1:8088` 双身份走查；**严禁私自推生产**。
