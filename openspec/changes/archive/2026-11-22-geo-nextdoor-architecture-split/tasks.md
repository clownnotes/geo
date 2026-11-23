# Tasks: GEO 与小毛驴双工作区分工规则及后厂接口整肃

## 1. 第一步：双边 4 处规则文件对齐（人机联动确认后落盘）

- [x] 1.1 起草并在对话框展示 `GEO/AGENTS.md` 修订文本（明确后厂车间定位、异步 Worker 契约、Nginx 静态托管、禁止新增管理台与业务状态文件），经产品负责人确认后落盘并核验可读性
- [x] 1.2 起草并在对话框展示 `/Users/a1/next核心项目/AGENTS.md` 修订文本（登记 GEO 为前店后厂正式模块、同机旁挂端口与 Nginx 静态托管分工），经确认后落盘
- [x] 1.3 起草并在对话框展示 `/Users/a1/next核心项目/02_管理员操作端/XiuLan_IDE/RULES.md` 修订文本（明确 GEO Vue 3 组件目录、四级导航复用规范与禁止前端直连 Python 红线），经确认后落盘
- [x] 1.4 起草并在对话框展示 `/Users/a1/next核心项目/04_统一大后端代码/统一后端-Go/RULES.md` 修订文本（明确 `geo_*` 5 张核心表前缀、雪花 ID、GORM 迁移规范与异步 `GeoWorkerClient` 规范），经确认后落盘

## 2. 第二步（GEO 仓整肃）：存量盘点、异步 Worker 提纯与旧管理台下线

- [x] 2.1 盘点 `src/tools/geo/` 全部 74 个 Python 文件与 `fork/` 临时原型端口占用，输出《存量模块留/迁/删分类确认表》交由产品负责人确认，确保不误删核心诊断与建站算法
- [x] 2.2 剥离 `src/tools/geo/server.py` 对旧管理台路由、RBAC 与 `ad_orders.json` 等业务状态的耦合，提纯后的异步任务 Worker 入口落点为新建目录 `src/tools/worker/`（本变更新建，尚无现存目录；实测 `src/tools/` 现有只有 `__init__.py`、`__pycache__` 与 `geo`，无 `worker`），仅绑定 `127.0.0.1:18092`，只暴露 `POST /worker/jobs` 与 `GET /worker/jobs/{job_id}`（支持全部 9 类任务：基础 4 类 `diagnose`/`probe`/`build_site`/`build_blog` 与交付对客 5 类 `boss_report`/`share_portal`/`distribute_pack`/`acceptance_report`/`pitch_roi`）并带 `X-Geo-Internal-Token` 内部服务凭证校验；同时仅下线 `deploy/nginx_geo.conf` 中指向 `127.0.0.1:8088` 的反代 `location`，保留 `geo.baicl.cc` 域名并改为由 `mini` 本机 Nginx 直接挂载 `projects/{id}/outputs/site/` 静态目录；新建 `deploy/nginx_customer.conf`（待建）承载客户独立域名，以未删除的 `geo_projects.domain` 作为 `server_name`、以未删除的 `geo_projects.output_dir` 作为 `root`，由小毛驴 Go 工具命令 `cmd/gen_geo_nginx/main.go`（待建，本变更新建，实测不存在，严禁 shell 裸拼 SQL 与硬编码密码）生成；`geo.baicl.cc` 只做 `/sites/{project_id}/`，`nextgeo` 根路径挂 `www.baicl.cc`
- [x] 2.3 为异步 Worker 编写并运行自动化测试（覆盖 9 类任务提交/查询正向用例，以及无凭证 401、非法任务类型 400 反向断言），确认全部通过
- [x] 2.4 配合小毛驴前店联调通过及客户数据迁出后，归档并下线 `src/web/index.html` 等旧管理台文件及旧路由，验证 GEO 仓仅保留后厂 Python Worker 与 `projects/{id}/outputs/` 静态产物

## Workflow follow-up

- 在小毛驴工作区（`/Users/a1/next核心项目`）新建独立的 OpenSpec 变更，承接以下成对任务并与本仓 `2.4` 联调收口后分别归档：
  - 编写 `geo_*` 五表 `up.sql`/`down.sql` 迁移（含 MySQL 8.0.46 `GENERATED ALWAYS AS (...) STORED` 唯一索引、`ROW_FORMAT=DYNAMIC`、`VARCHAR(191)` 与 `updated_at datetime NULL DEFAULT NULL`）；
  - 在 `restful/gin/resp/resp.go` 新增 `Created(c, data)`（201）与 `Accepted(c, data)`（202）封装，并在 `Geo*Logic`、`GeoWorkerClient`、`/api/v1/geo/...` 路由与前端 `apiFetch`（HTTP 409 优先冲突提示）中成对实现；
  - 编写 `cmd/gen_geo_nginx/main.go`（引入 `vioconstant`，失败 Fatal + 原子写入 `deploy/nginx_customer.conf`）与 `XiuLan_IDE` Vue 3 四级导航 GEO 工作台。
