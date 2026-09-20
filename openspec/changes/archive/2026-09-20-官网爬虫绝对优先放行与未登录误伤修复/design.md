# Design: 官网爬虫绝对优先放行与未登录误伤修复

## Architecture (架构设计与网关拦截模型)

```
                            终端访客 / 大模型检索爬虫 (Bytespider / DeepSeek / 百度)
                                                  │
                                                  ▼
                                       HTTP 请求到 8088 端口
                                                  │
                                                  ▼
                                 ┌─────────────────────────────────┐
                                 │     tools/geo/server.py         │
                                 │   网关总门拦截 (console_gate)    │
                                 └────────────────┬────────────────┘
                                                  │
                  ┌───────────────────────────────┴───────────────────────────────┐
                  ▼                                                               ▼
        【未登录公开白名单 (放行)】                                       【未登录私有资源 (阻断)】
   - 公开官网: /sites/{project_id}/*                                - 内部敏感代码: /.env, server.py 等
   - 爬虫协议: /robots.txt, /llms.txt, /sitemap.xml                - 内部后台 API: /api/projects/* 等
   - 登录页面: /, /login.html                                      - 管理台源码: /web/index.html (完整包)
                  │                                                               │
                  ▼                                                               ▼
       静态文件直接读取响应 (200 OK)                                       标准静默 404 轰出 (404 Not Found)
    (绝不带 X-Robots-Tag 阻断头)                                          (防探测，绝不泄露仓库内容)
```

### 1. 识别核心对象与边界 (面向对象三问)

| 实体对象 | 属性 / 类别 | 行为与安全约束 |
| :--- | :--- | :--- |
| **`PublicSiteAsset`（公开官网资源）** | 路径以 `/sites/` 开头，或属于根目录爬虫文件（`robots.txt`, `llms.txt`, `sitemap.xml`） | **无条件放行**：对任何公网 IP、免密访客和搜索引擎爬虫 100% 开放，返回规范 MIME 与内容，严禁附加 `noindex` 响应头。 |
| **`PrivateBackend`（内部管理接口）** | `/api/projects/`、`/api/ops/`、`/api/monitor/` 等业务接口 | **严格验权**：必须持有有效 `geo_token` Cookie 且通过花名册鉴权，未登录直接 404。 |
| **`SensitiveSource`（敏感文件与代码）** | `/.env`、`server.py`、`AGENTS.md`、`docs/`、`tools/` | **物理隔离**：无论是否登录，一律严禁通过 HTTP 静态直接下载，未登录直接 404。 |

---

## Interface (接口/路由与响应规范)

### 1. 公开官网静态服务路由 (`/sites/{project_id}/...`)
- **请求方式**：`GET` / `HEAD`
- **放行条件**：只要 `project_id` 格式合法且项目存在编译产物 `outputs/site`，无论是公网访客还是爬虫，一律放行读取；
- **防穿越与路径规整**：
  - 目录缺少尾部 `/`：继续严格执行 HTTP 301 重定向补充尾部斜杠，杜绝相对路径 CSS/图片错位；
  - 路径中禁止出现 `..`，严格局限在 `outputs/site/` 物理目录内；
  - 响应头：正常返回 `Content-Type` 与 `Cache-Control`，**严禁添加 `X-Robots-Tag: noindex, nofollow, noarchive`**。

### 2. AI 爬虫探针路由 (`/robots.txt`, `/llms.txt`, `/sitemap.xml`)
- **请求方式**：`GET` / `HEAD`
- **放行条件**：未登录直接放行，返回根目录或默认官方站（`nextgeo`）的爬虫协议文件；
- **响应头**：`Content-Type: text/plain; charset=utf-8`，确保各大模型 AI 抓取器毫秒级解析。

### 3. 拦截门核心判定逻辑变更 (`console_gate`)

```python
# 1. 已登录用户：走 RBAC 与防刷护栏
authed = self.check_auth()
if authed:
    ...
    return True

# 2. 未登录公开官网与大模型爬虫放行白名单（最高优先级）
is_public_site = (
    path.startswith("/sites/") or
    path in ("/robots.txt", "/llms.txt", "/sitemap.xml")
)
if is_public_site and method in ("GET", "HEAD"):
    return True

# 3. 登录页与认证接口
is_page_req = path in ("/", "/index.html", "/admin", "/login.html") or path.startswith("/web/")
if is_page_req and method in ("GET", "HEAD"):
    self._serve_login_page()
    return False

# 4. 其余任何内部请求（敏感文件、内部 API）：一律 404
self._serve_404_not_found()
return False
```

---

## Database Schema / Data Structure (数据模型)

- 无需新增数据库表或持久化模型结构。
- 遵循现行 `project.yaml` 与静态产物物理目录对齐原则。
