# 接入小毛驴统一API与GEO协作网站搭建 (Design)

## 1. 总体拓扑（同机 `ne@mini`）

**部署锚点（硬约束）**

| 项 | 值 |
| :--- | :--- |
| 物理机 | SSH `mini` / Tailscale `100.83.64.112`，用户 **`ne`** |
| 小毛驴代码 | `/Users/ne/apps/xiulan` |
| GEO 代码 | `/Users/ne/apps/GEO` |
| 开放 API（同机互调） | `http://127.0.0.1:3001` |
| 管理台 / 能力目录 | `http://100.83.64.112:3002/community/admin/api-management?tab=capabilities` |
| 外部公网 API（非同机） | `https://nextdoor.baicl.cc`（仅异地客户端；**同机禁止**） |
| GEO Web（现状/目标） | 本机监听 `:8088`（与现网一致） |

```
+--------------------------------------------------------------------------+
|              多电脑浏览器（同事本机，仅 UI，不存生产项目文件）              |
|         Tailscale / 局域网 → http://100.83.64.112:8088 （或绑定域名）       |
+------------------------------------+-------------------------------------+
                                     | JWT + vio-source-client: geo
                                     v
+--------------------------------------------------------------------------+
|                    同一台宿主机 ne@mini (100.83.64.112)                    |
|  +---------------------------+    +------------------------------------+ |
|  | GEO 业务壳 (:8088)        |    | 小毛驴统一后端                      | |
|  | 现网：Python server.py    |--->| - :3001 开放 API（账号/对话/KB/上传）| |
|  | （可选）Go gateway 透传   |    | - :3002 社区管理台 / 能力目录       | |
|  | - 验 JWT / 项目 / GeoTask |    | - 雪花 ID / 算力 / LLM Proxy        | |
|  | - 报告 / ZIP / KB 代理    |    +------------------------------------+ |
|  +-------------+-------------+                                           |
|                | 同进程线程调度（TaskManager）                            |
|                v                                                         |
|  +---------------------------+    +------------------------------------+ |
|  | Python GEO 工兵模块       |    | 集中磁盘                             | |
|  | audit/rewrite/… import 调用|--->| /Users/ne/apps/GEO/projects/{slug} | |
|  +---------------------------+    +------------------------------------+ |
+--------------------------------------------------------------------------+
```

**原则**：小毛驴已有的能力 **禁止在 GEO 再实现一份**；GEO 只补「项目 + SOP Job + 行业算法」。

---

## 2. 小毛驴 7 大能力包 × GEO 复用矩阵

契约真源：`XiuLan_IDE/src/community/config/api-capabilities.ts`（与能力中心页一致）。

### 2.1 必复用

| 功能 | 方法与路径 | 鉴权 | GEO 用法 |
| :--- | :--- | :--- | :--- |
| 手机号密码登录 | `POST /api/v1/xiulan/login` | Public | 换 JWT；`device_id` 可选 |
| 当前用户画像 | `GET /api/v1/xiulan/me` | JWT | 右上角姓名/角色/credits；字段 `name` 非 nickname；**id 为雪花字符串** |
| 微信扫码二维码 | `GET /api/auth/wechat-qr` | Public | Web 扫码登录 |
| 微信快捷登录 | `POST /api/v1/community/auth/wx-login` | Public | 有 App/内嵌微信时用 |
| 流式对话 | `SSE /api/v1/xiulan/chat` | JWT | 解读/改写/润色；与现 `tools/geo/llm.py` 对齐 |
| 社区图片上传 | `POST /api/v1/community/uploads` | JWT | Logo、封面、客户资料图 |

### 2.2 优先复用（首期或紧随）

| 功能 | 方法与路径 | GEO 用法 |
| :--- | :--- | :--- |
| 文档入库 | `POST /api/kb/documents` | 客户 PDF/DOCX/MD 进统一 KB |
| KB 问答 | `POST /api/kb/chat` | 品牌事实问答、交付辅助 |
| 意图路由 | `POST /api/v1/xiulan/intent/match` | 管理台快捷工具入口（可选） |
| 视觉上传 | `POST /api/v1/xiulan/vision/upload` | 截图/对照图给多模态 |

### 2.3 明确不做 / 首期不做

- `voice` TTS/ASR、数字人视频、`sub` 充值提现、社区笔记瀑布流：与 GEO 交付主路径无关，**不写进首期任务**。
- **禁止** GEO 自建：用户表+密码哈希、JWT 签发、LLM Key 池、第二套通用 RAG 服务。

### 2.4 同机调用规范

1. Base URL = `http://127.0.0.1:3001`（写进环境变量 `NEXTDOOR_BASE_URL`，已有约定）。  
2. Header：`vio-source-client: geo` +（用户态）`Authorization: Bearer <token>`。  
3. 响应：`{ "code": 0, "msg", "data" }`，以 **`code === 0`** 判成功。  
4. 雪花 ID：**JSON 一律 string**；Go 内存可用 uint64，出网 DTO 必须字符串，禁止 JS Number。

---

## 3. GEO 自有对象（仅行业域）

全系统主键雪花 ID；**禁止自增主键**。用户主数据在小毛驴，GEO **只存引用**。

### 3.1 UserSnapshot（只读缓存，非账号主表）

- `user_id` (string 雪花) / `phone` / `name` / `role` / `credits`（来自 `/me`）  
- 行为：`VerifyJWT`（本地验签或回调小毛驴）、`CheckProjectAccess`

### 3.2 GeoProject

- `id` (雪花) / `project_slug`（磁盘名）/ `brand_name` / `industry` / `target_domain`  
- `creator_user_id`（雪花字符串）/ `member_user_ids` / `config_yaml` 镜像 / `status`  
- 磁盘真源：`/Users/ne/apps/GEO/projects/{slug}/`

### 3.3 GeoTask

- `id` / `project_id` / `task_type`（`audit`|`rewrite`|`intent`|`probing`|…）  
- `status`：`pending`|`running`|`success`|`failed`  
- `progress` / `log_output` / `duration_ms`  
- 行为：派发本机 Python、抓 stdout、落盘后标 success

**说明**：小毛驴已有通用异步任务（语音/视频）；**GEO SOP 任务不混用那套队列**，避免领域耦合。通用 AI 产物仍走小毛驴任务接口。

---

## 4. GEO 业务 API（自有，复数资源、路径无动词）

认证可二选一（实现时定一种并写进联调清单）：

- **A. 浏览器直连小毛驴**：登录调 `:3001` 的 `account` 接口，GEO 只收 JWT；  
- **B. GEO 薄代理**：`POST /api/v1/sessions` → 透传 `POST /api/v1/xiulan/login`；`GET /api/v1/me` → 透传 `/api/v1/xiulan/me`。

### 4.1 项目

- `GET/POST /api/v1/projects`  
- `GET/PUT /api/v1/projects/:project_id`

### 4.2 任务

- `POST /api/v1/projects/:project_id/tasks`  Body: `{"task_type":"audit"}`  
- `GET /api/v1/projects/:project_id/tasks`  
- `GET /api/v1/tasks/:task_id`  
- `GET /api/v1/tasks/:task_id/events`（SSE 日志）

### 4.3 产物

- `GET /api/v1/projects/:project_id/reports`  
- `POST /api/v1/projects/:project_id/bundles`（打包；**禁止**路径写成 `/export-bundle`）

上传客户图：**不要**自建上传接口，前端/BFF 调小毛驴 `POST /api/v1/community/uploads`。

---

## 5. 任务调度与 Python 工兵（落地定稿）

1. **现网主路径**：`tools/geo/server.py`（:8088）承担 GEO BFF；`gateway/main.go` 为可选透传网关（对话/登录/KB），默认 `vio-source-client: geo`。  
2. **GeoTask 执行方式（首期）**：`TaskManager` 在**同进程线程**内 `import` 调用 `audit`/`rewrite` 等模块，捕获 stdout 写入日志并 SSE 推送；**项目级互斥队列**保证同项目同时只有一个 `running`。  
   - 约束：互斥锁只在**单 GEO 进程**内有效；生产机只跑一个 :8088 实例。  
   - 后续若拆多 worker，再改为 `os/exec` 子进程 + 跨进程锁（Redis/文件锁）。  
3. LLM 继续走 `tools/geo/llm.py` → 同机 `:3001` `/api/v1/xiulan/chat`（禁止旁路直连厂商 Key，除非 `GEO_LLM_DIRECT=1` 应急）。

---

## 6. 过渡策略

1. **先鉴权 + 集中盘**：去掉硬编码单账号，JWT 接小毛驴，`projects/` 只认服务器盘。  
2. **再 Job 化**：长任务进 GeoTask + SSE；管理台接任务日志 / 打包 / KB 入口。  
3. **再收 KB/上传**：材料上传与品牌库切到小毛驴能力包。  
4. **不以「重写 Go Gin 主后端」为挡路条件**；Python BFF 可长期服役，Go 仅作透传增强。**不得**借过渡期新建用户库。


---

## 7. 跨电脑协作遗留问题与防御性设计 (Review 订正补充)

### 6.1 网络访问与服务通道 (避免依赖本地 SSH 隧道)
1. **现状**：公司电脑访问家里 M4 上的管理端原本依赖 SSH 端口转发隧道（`3002 -> 127.0.0.1:3002`），以绕过 LocalAdmin 鉴权限制。
2. **解法**：
   - GEO 业务壳（现网 Python `:8088`）与小毛驴开放 API `:3001` 交互全部走公共 JWT（`login` / `me`），不触发 LocalAdmin；
   - 外部访问支持两种通道：
     - **通道 A（内网协作）**：同事电脑加入 Tailscale，直接浏览器打开 `http://100.83.64.112:8088`；
     - **通道 B（公网直连，推荐）**：复用既有的 Nginx 反代配置（见 `deploy/nginx_geo.conf`），将 `geo.baicl.cc` 指向 `:8088`，同事无需配任何 VPN/Tailscale，直接输入域名即可访问。

### 6.2 项目并发互斥锁 (防文件同时写入损坏)
1. **痛点**：若两位同事在不同电脑上几乎同时对同一个项目点击长任务，会导致并发写同一个 `outputs/` 文件，造成数据损坏。
2. **防范机制**：
   - `TaskManager` 引入**项目粒度互斥队列锁（Project Task Mutex）**；
   - 同一个项目在同一时刻只允许**一个**计算任务处于 `running` 状态；若有新任务提交，自动进入 `pending` 排队，前序任务完成后按序唤醒。
   - 前提：生产机只跑**一个** GEO `:8088` 进程。
### 6.3 协作数据共享与审计
1. **权限策略**：前期作为内部运营协同工具，默认采用“团队全员共享”机制（所有成员均可查看所有项目与报告）；
2. **操作溯源**：每次发起诊断、修改配置或重新生成时，任务记录中自动记录当前发起人的雪花 `user_id` 与姓名，方便追溯。
