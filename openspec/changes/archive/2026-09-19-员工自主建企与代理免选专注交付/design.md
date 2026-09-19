# OpenSpec 技术架构设计：员工自主建企与代理免选专注交付

> 对应变更目录：`openspec/changes/2026-09-19-员工自主建企与代理免选专注交付`

---

## 1. 面向对象抽象设计

### 1.1 对象与属性
- **`OperatorProjectCreator`（员工建企与自动授权器）**：
  - 属性：
    - `creator_ident`：当前登录人员身份快照（`is_developer`、`user_id`、`phone`）
    - `new_client_id`：新创建的项目唯一标识符
  - 核心行为：
    - `append_member_allowed_project(user_id, phone, client_id)`：原子级落盘追加管辖项目
- **`PartnerIsolationGate`（合作方权限与视图隔离门）**：
  - 属性：
    - `is_developer`：是否为师弟的总账号
  - 核心行为：
    - 员工新建强制 `partner_id = ""`（未分配）
    - 代理归属划转接口保持仅开发者专属
- **`CleanDeliveryUI`（专注型交付界面呈现器）**：
  - 属性：
    - 员工端完全隐藏所有商务合作方元素

---

## 2. 后端权限路由与花名册原子联动

### 2.1 路由放行与守卫调整 (`tools/geo/rbac.py`)（防踩坑）

现码 `guard_route` 判定顺序：开发者专属 → `ROUTE_AUTHENTICATED` → 项目级 → **未登记则 fail-closed 403**。

因此 **只从 `ROUTE_DEVELOPER_VERBS` 删掉 POST 不够**：`POST /api/projects` 不是项目级路径，会掉进 D 档，员工仍然 403。

正确做法（两步一起做）：
1. 从 `ROUTE_DEVELOPER_VERBS` 移除 `("/api/projects", "POST")` 与 `("/api/v1/projects", "POST")`；
2. **同时**把这两条加入 `ROUTE_AUTHENTICATED`（已登录且花名册命中的运营可调）；
3. 合作方写操作继续锁死：`POST /api/partners*`、`POST/PUT …/meta`（改挂 `partner_id`）保持开发者专属。

### 2.2 花名册管辖项目自动追加 (`tools/geo/rbac.py`)
在 `rbac.py` 新增原子写函数（须在 `_ROSTER_LOCK` 内读改写）：
```python
def append_member_allowed_project(user_id: str = None, phone: str = None, project_id: str = None) -> bool:
    """运营建企成功后，把 project_id 追加进该成员 allowed_projects。找不到成员则返回 False。"""
    ...
```

**失败语义（硬约束）**：
- 员工建企：目录已落盘后若 `append_member_allowed_project` 返回 False（花名册无此人），接口必须返回 **明确错误**（建议 500，文案人话：「建好了但还没写进你的管辖名单，请联系管理员」），并在响应里标 `bind_failed=true`，避免「建完立刻 403」静默死锁；
- 开发者建企：不强制改自己的 `allowed_projects`（开发者本就可看全量）。

### 2.3 建企接口逻辑增强 (`tools/geo/server.py`)
在 `POST /api/projects`（与 `/api/v1/projects` 同一分支）中：
```python
ident = self.rbac_identity()
if ident and not ident.is_developer:
    partner_id = ""   # 员工禁止指定合作方；忽略 body 里的 partner_id
else:
    partner_id = str(body.get("partner_id") or "").strip()

# 落盘成功后：
if ident and not ident.is_developer:
    ok = append_member_allowed_project(
        user_id=creator_user_id, phone=ident.phone, project_id=client_id
    )
    if not ok:
        # 返回 bind_failed，前端提示找管理员；勿假装成功后跳进项目
        ...
```

---

## 3. 前端界面重构与 Client ID 自动生成 (`web/index.html`)

### 3.1 开放【新建客户】按钮
- 将企业管理标题栏的【新建客户】按钮移除 `data-geo-dev-only`，使员工账号可正常点击。

### 3.2 Client ID 自动推导算法（零新依赖）
- 监听 `#np-name`；若 `#np-id` 仍属「自动填充态」（未人工改过），则预填：
  1. 从名称中抽出已有英文/数字片段，转小写，非 `[a-z0-9]` 换成 `_`；
  2. 若几乎没有英文（纯中文名），前缀固定用 `corp_` + 名称哈希或时间戳后 4 位（如 `corp_5206`）；
  3. **不引入** pypinyin 等新依赖；员工可随时手改 `#np-id`，手改后停止自动覆盖。

### 3.3 员工端合作方元素全面纯净化隐藏
- **新建弹窗**：`#np-partner` 外层容器加 `data-geo-dev-only`（员工看不见；开发者仍可选）。
- **企业列表筛选 / 表头**：继续用现有 `data-geo-dev-only`；表格行已由 `renderEnterprisesTable` 的 `isDeveloper()` 控制，**不要**再叠一套会弄乱 colspan 的半隐藏。
- **左侧导航**：`合作方管理` 保持仅开发者可见（现码已有）。
- **建企成功后**：前端必须再拉一次 `/api/auth/status`，刷新内存里的 `allowedProjects`，再进入阶段零；否则本地权限态还是旧名单，会误以为没权限。
