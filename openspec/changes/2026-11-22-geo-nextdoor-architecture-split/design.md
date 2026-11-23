# Design: GEO 与小毛驴双工作区“前店后厂”整肃架构设计（稳定加固版）

## Context

参见 `proposal.md - Why` 与 `proposal.md - 核心原话实录`。
当前 GEO 工作台以单文件 `src/web/index.html`（1.18 MB）加 Python `server.py`（334 KB）读写散装 YAML/JSON 运行，存在前端易改坏、纯文件缺乏强字段约束、无法直接复用小毛驴（`/Users/a1/next核心项目`）本地模型与统一权限底座的问题。
结合交叉审核意见，本设计确立“小毛驴前店（Vue 3 + Go + 关系型数据库）+ GEO 后厂（同机旁挂异步 Python Worker）+ Nginx 静态托管客户官网”的三段式稳定架构，并按“第一步写好双边规则 -> 第二步分仓独立整肃代码”推进。

---

## Goals / Non-Goals

**Goals:**
- 明确双工作区在反重力（Antigravity）开发时的物理分工与 4 处规则文件对齐方案，让 AI 在小毛驴单工作区即可完成 90% 的日常前后端开发；
- 将客户静态官网托管从 Python 中剥离，明确交由 Nginx 直接挂载磁盘目录（含缺尾斜杠 301 规则）；
- 将 GEO 后厂计算升级为同机旁挂（`127.0.0.1` + launchd 常驻）的异步任务模型（`POST /worker/jobs` + `GET /worker/jobs/{job_id}`），避免长耗时爬虫与大模型采样卡死；
- 确立小毛驴数据库单一真相源（含 `geo_projects`、`geo_sop_steps`、`geo_ad_orders`、`geo_baseline_posts`、`geo_worker_jobs`），消除双真相源冲突；
- 按仓库拆分为独立 OpenSpec 变更各自闭环：本仓负责立双边规则、盘点 `src/tools/geo/` 74 个文件归属、提纯异步 Worker 并下线旧管理台；小毛驴仓另立变更承接建表与 Vue 3/Go 开发。

**Non-Goals:**
- 不在本阶段直接修改业务源码或直接覆写 `AGENTS.md` / `RULES.md`（规则文件修改需按 0.10 铁律在对话中过目确认后再落盘）；
- 不保留老 `8088` 管理台的长期双轨并行过渡期，规划一次性整肃迁移；
- 不把 `fork/` 下的 PHP（GEOFlow）或 TypeScript（GEORank）作为主底座，仅按需拆取其诊断算法思路。

---

## 用户原话与技术决策 1 对 1 映射推导链条表

| 序号 | 师弟核心原话 | AI 理解与架构定位 | 技术决策（落实到具体结构与规约） |
|---|---|---|---|
| 1 | “这个就像是一个工作台。能够引导人把每一步 SOP 做好……包括外包记账和自研日常维护两个版块” | 系统核心是内部 SOP 引导工作台，包含基本盘长期维护（0~7 步 + 每月保活）与快速见效代采记账（4 个时间点） | 在小毛驴 `XiuLan_IDE` 用 Vue 3 复用四级导航（左侧 1/2 级宏观模块 + 顶部 3 级步骤胶囊 + 4 级托盘），每一步拆分为 `<=200` 行的独立 `.vue` 组件，加装步骤前置检查与大厅待办驾驶舱 |
| 2 | “有数据库的重型开发，反而正确率会更高……复用小毛驴的框架设计比较好” | 关系型数据库 Schema + ORM + Go 强类型编译器能为 AI 提供硬护栏，且直接复用小毛驴本地模型、雪花 ID 与 RBAC 权限 | 在小毛驴 `统一后端-Go` 新增 `geo_*` 系列表与 GORM 模型，确立数据库为唯一业务真相源（含 `geo_worker_jobs` 异步任务表与 `geo_baseline_posts` 保活真源表），严禁 GEO 后厂写库 |
| 3 | “需要一份工作区的规则……第一步，把两个工作区的 rules 和每个文件夹对应 AGENTS 文件写好” | 反重力按工作区加载规则，必须先写死双边 `AGENTS.md` 和 `RULES.md`，再开始整肃代码 | 第一步先对齐并落盘 `GEO/AGENTS.md` 与小毛驴 `AGENTS.md`、`XiuLan_IDE/RULES.md`、`统一后端-Go/RULES.md`；第二步再按仓拆分执行代码改造 |
| 4 | “不用过渡期铁律了。下一个规范就是按照我们定的架构，开始整肃以前的代码了” | 不背历史包袱双轨运行，先盘清旧代码去留，再按新架构一次性整肃 | 在 GEO 仓先输出 `src/tools/geo/` 74 个模块的留/迁/删分类表，提纯 4 类异步 Worker 接口（落点新建目录 `src/tools/worker/`），仅下线 `deploy/nginx_geo.conf` 中指向 `127.0.0.1:8088` 的反代 `location`（保留 `geo.baicl.cc` 域名，改由 `mini` 本机 Nginx 直接挂载静态目录），最后迁移客户数据并下线 `src/web/index.html` |

---

## 整体架构与部署拓扑（三段式解耦）

```text
+-------------------------------------------------------------------+
| [对客静态层] Nginx (公网 VPS 反代 / 边缘 CDN -> mini 磁盘目录)     |
|   - 直接挂载 projects/{id}/outputs/site/                          |
|   - 处理缺尾斜杠 301 重定向、/llms.txt、/robots.txt、/sitemap.xml |
|   - 完全不经过 Go 与 Python 业务进程                              |
+-------------------------------------------------------------------+

+-------------------------------------------------------------------+
| [前店与大管家] 小毛驴工作区：/Users/a1/next核心项目 (mini 内置SSD) |
|   - 开发预览 :3002 / 生产 :3001 (launchd 守护)                    |
|   - Vue 3 (XiuLan_IDE)：四级导航工作台 + 按 SOP 拆组件            |
|   - Go (统一后端-Go)：Handler -> Logic -> Repository -> Model    |
|   - 核心表：geo_projects / geo_sop_steps / geo_ad_orders /        |
|             geo_baseline_posts / geo_worker_jobs                  |
+-------------------------------------------------------------------+
                           |
                           | 127.0.0.1 内网异步 HTTP + 内部凭证
                           | POST /worker/jobs  &  GET /worker/jobs/{id}
                           v
+-------------------------------------------------------------------+
| [后厂车间] GEO 工作区：/Users/a1/代码/GEO (与 Go 同机 launchd 旁挂)|
|   - Python 无状态 Worker：绑定 127.0.0.1 专属内部端口              |
|   - 9 类任务：diagnose/probe/build_site/build_blog + 交付对客 5 类 |
|   - 产出的 HTML/图片落盘至 outputs/ 并同步 GEOZiLiao              |
+-------------------------------------------------------------------+
```

---

## 小毛驴核心数据模型蓝图（面向对象三问）

### 1. `GeoProject`（`geo_projects` 表 — 实体客户档案）
- **属性**：雪花 ID `id`、`code`、`name`、`domain`、`lifecycle_phase`（`initial_batch` 初期密集期 / `monthly_retention` 月度保活期）、`output_dir`。
- **行为**：由 `GeoProjectLogic` 负责建档与状态流转。

### 2. `GeoSopStep`（`geo_sop_steps` 表 — SOP 0~7 步闯关状态）
- **属性**：雪花 ID `id`、`project_id`、`step_code`（`step-0` 至 `step-7`）、`status`（`pending` / `in_progress` / `done`）、`input_payload`、`output_payload`、`completed_at`。
- **行为**：由 `GeoSopLogic` 校验前置步骤并记录成果。

### 3. `GeoAdOrder`（`geo_ad_orders` 表 — 外包代采记账）
- **属性**：雪花 ID `id`、`project_id`、`platform_name`、`external_order_url`、`client_ordered_at`、`vendor_paid_at`、`vendor_delivered_at`、`client_accepted_at`。
- **行为**：由 `GeoAdOrderLogic` 维护 4 个核心时间戳，不记中间过程流水。

### 4. `GeoBaselinePost`（`geo_baseline_posts` 表 — 基本盘保活唯一真相源）
- **属性**：雪花 ID `id`、`project_id`、`slug`、`title`、`published_at`。
- **行为**：由 `GeoBaselineLogic` 在后厂 `build_blog` 成功返回后落库，唯一负责计算 30 天保活健康度并在大厅预警。

### 5. `GeoWorkerJob`（`geo_worker_jobs` 表 — 异步后厂任务追踪）
- **属性**：雪花 ID `id`、`project_id`、`job_type`（基础 4 类 `diagnose` / `probe` / `build_site` / `build_blog` 与交付对客 5 类 `boss_report` / `share_portal` / `distribute_pack` / `acceptance_report` / `pitch_roi`）、`worker_job_id`、`status`（`queued` / `running` / `succeeded` / `failed`）、`result_payload`、`error_message`、`started_at`、`finished_at`。
- **行为**：由 `GeoWorkerClient` 提交至 GEO Python Worker 并轮询更新状态，失败时透传底层原因。

---

## 双边 4 处规则文件更新清单（第一步优先执行）

1. **`/Users/a1/代码/GEO/AGENTS.md`**：定位为后厂异步计算车间与静态成品仓，禁止新增管理台/业务数据库表，定义异步 Worker 契约与 Nginx 静态托管职责。
2. **`/Users/a1/next核心项目/AGENTS.md`**：登记 GEO 为前店后厂正式模块，明确业务全在小毛驴、静态官网由 Nginx 托管、计算调同机旁挂 GEO Worker。
3. **`/Users/a1/next核心项目/02_管理员操作端/XiuLan_IDE/RULES.md`**：约定 GEO 工作台 Vue 3 组件位置、四级导航复用规范及禁止直连 Python 端口。
4. **`/Users/a1/next核心项目/04_统一大后端代码/统一后端-Go/RULES.md`**：约定 `geo_*` 表前缀、GORM 迁移规范、异步 `GeoWorkerClient` 调用规范。

---

## 存量老代码整肃策略（第二步执行）

- **GEO 仓任务（本变更追踪）**：先盘点 `src/tools/geo/` 74 个模块并输出留/迁/删分类表；随后提纯异步 Worker 接口（落点 `src/tools/worker/`，本变更新建）并下线 `src/web/index.html` 与旧管理台路由，同时仅下线 `deploy/nginx_geo.conf` 中指向 `127.0.0.1:8088` 的反代 `location`，保留 `geo.baicl.cc` 域名并改为由 `mini` 本机 Nginx 直接挂载 `projects/{id}/outputs/site/` 静态目录；客户独立域名配置单独新建 `deploy/nginx_customer.conf`（待建），以未删除的 `geo_projects.domain` 作为 `server_name`、以未删除的 `geo_projects.output_dir` 作为 `root`，由小毛驴 Go 工具命令 `cmd/gen_geo_nginx/main.go`（待建，本变更新建，实测不存在，严禁 shell 裸拼 SQL 与硬编码密码）生成；`geo.baicl.cc` 只做 `/sites/{project_id}/`，`nextgeo` 根路径挂 `www.baicl.cc`。
- **小毛驴仓任务（在小毛驴 `openspec/` 另立独立变更追踪）**：建 `geo_*` 5 张表、实现 `Geo*Logic` / `GeoWorkerClient` 与 Vue 3 工作台，完成后执行一次性客户数据导入。

---

## Risks / Trade-offs

- **[Risk] `src/tools/geo/` 存量 74 个文件耦合度高，直接删除可能误伤有用算法** → **Mitigation**：代码改造前必须先输出完整的 74 文件归属清单（留后厂提纯 / 迁入 Go / 废弃归档），经人工确认后再动刀。
- **[Risk] `data/ops_check_logs.jsonl` 与 `projects/{id}/history.db` 是巡检写出的两份平行源，只停定时器仍会留一份 JSON 记账** → **Mitigation**：停巡检以停止 `server.py` 的 `:8088` 进程为准（实测 `/api/portfolio/patrol` 位于 L952-L953、`/api/patrol/trigger` 位于 L1787-L1788），并把两份文件一并列入退场清单停写归档。
- **[Risk] 异步任务执行期间后厂进程重启导致任务状态悬空** → **Mitigation**：`GeoWorkerJob` 增加超时兜底巡检，若超过阈值仍处于 `running` 且后厂查无此任务则标为 `failed` 并暴露诊断信息。
