# GEO 后厂常驻服务(18092)部署与端到端联调测试报告

- **变更名**：`geo-workbench-and-mysql-backend`
- **验证环境**：Mac mini M4 (NE1, 100.83.64.112)
- **服务实例**：
  - 前店开发端：小毛驴 Go 后端 (`:3002`，LaunchAgent `com.xiulan.backend-3002`)
  - 后厂车间端：GEO Python Worker (`:18092`，LaunchAgent `com.xiulan.geo-worker-18092`)
  - 关系型数据库：`Leishen-DB` 开发库 (`test.nextdoor.baicl.cc`)
- **执行时间**：2026-11-23 17:51:30

---

## 一、服务部署与凭据治理

1. **Launchd Plist 模板**：
   - 文件位置：`next核心项目/05_独立微服务集群/com.xiulan.geo-worker-18092.plist`
   - 工作目录：`/Users/ne/apps/GEO`
   - 程序入口：`/usr/bin/python3 -m tools.worker --host 127.0.0.1 --port 18092`
   - 依赖路径：`PYTHONPATH=/Users/ne/apps/GEO/src`
   - 运行策略：`RunAtLoad=true`, `KeepAlive=true`
2. **凭据安全与单源对齐**：
   - 随机生成 32 字节高强度十六进制凭证；
   - mini 端 `~/Library/LaunchAgents/com.xiulan.geo-worker-18092.plist` 与 `/Users/ne/apps/xiulan/dev/etc/.env.dev` 统一配置 `GEO_WORKER_INTERNAL_TOKEN`，两端凭据保持严格一致；
   - 生产模式下严禁混连开发配置，配置缺失直接 Fatal 阻断。
3. **消除路径遮蔽与 DDL 订正**：
   - 彻底移走 mini 机器根目录下的遗留 `tools/` 副本，确保 `PYTHONPATH=/Users/ne/apps/GEO/src` 精准命中 `src/tools/` 最新版本；
   - 新增增量迁移 `migrations/2026-11-23_alter_geo_worker_jobs_worker_job_id_null.up.sql`，执行 ALTER TABLE 将 `worker_job_id` 订正为 `DEFAULT NULL`，根除历史空串默认值。

---

## 二、成对正反断言测试执行记录

### 1. 直连后厂微服务测试 (:18092)

| 断言类型 | 测试动作 | 请求参数 / Header | 预期状态码 | 实际状态码 | 判定结果 |
|---|---|---|---|---|---|
| 正向探活 | `GET /health` | 无 Header | 200 | 200 | 通过 (status: ok) |
| 反向门禁 1 | `POST /worker/jobs` | 缺失 `X-Geo-Internal-Token` | 401 | 401 | 通过 (Missing required header) |
| 反向门禁 2 | `POST /worker/jobs` | 使用 `Authorization: Bearer <token>` | 401 | 401 | 通过 (Forbidden: Use X-Geo-Internal-Token) |
| 反向门禁 3 | `POST /worker/jobs` | 携带错误 Token (`wrong_secret`) | 401 | 401 | 通过 (Invalid internal service token) |
| 反向门禁 4 | `POST /worker/jobs` | 携带非法 `job_type` (`invalid_type`) | 400 | 400 | 通过 (Invalid or missing job_type) |
| 反向门禁 5 | `POST /worker/jobs` | 参数中注入非法 MySQL DSN | 400 | 400 | 通过 (Security Violation: MySQL parameter detected) |
| 反向门禁 6 | `GET /worker/jobs/:id` | 查询不存在的任务 ID (带合法 Token) | 404 | 404 | 通过 (Job not found) |
| 反向门禁 7 | `GET /worker/jobs/:id` | 查询不存在的任务 ID (无 Token) | 401 | 401 | 通过 (未授权阻断在先) |

---

## 三、前店与后厂全链路端到端测试 (:3002 -> :18092 -> MySQL)

### 1. 动线全景
1. 管理员通过 PC 端管理平台发起异步计算任务：
   `POST http://127.0.0.1:3002/api/v1/geo/projects/:project_id/worker-jobs`（携带合规管理员 JWT）；
2. Go 后端开启 MySQL 本地事务，写入 `geo_worker_jobs` 表，生成全局唯一雪花主键（初始状态 `queued`）并提交；
3. Go 后端调用 `GeoWorkerClient.SubmitJob` 直连后厂微服务 `:18092`，获得后厂内部 `worker_job_id`，回写数据库状态为 `running`，向前端返回 HTTP 202 Accepted 及雪花 `job_id`；
4. 后台独立协程以固定间隔轮询后厂任务状态，探测到终态后将 `status`、`finished_at` 与 `result_payload`（包含输出文件相对与绝对路径）回写至 MySQL。

### 2. 全部 9 类任务真实端到端落库核验数据

全部 9 类任务均通过 `:3002` 真实触发，由后厂 `:18092` 执行计算，并由 Go 轮询协程回写至真实 MySQL `geo_worker_jobs` 表：

| job_type | 所属客户 | 雪花主键 (id) | 后厂任务号 (worker_job_id) | 终态 | 完成时间 | 产出成果文件路径核验 |
|---|---|---|---|---|---|---|
| `diagnose` | nextgeo | `328109714141097984` | `job_db2d46057cdd4b23b4f125bb8222e57f` | succeeded | 2026-11-23 17:50:52 | `outputs/01_企业AI可见度现状体检与商业诊断报告.md`<br>`outputs/01_企业AI可见度商业诊断报告.md`<br>`outputs/01_企业底座技术体检审计报告.md`<br>`outputs/audit_metrics.json` |
| `probe` | nextgeo | `328109718612226048` | `job_167a546ca10442a687a5b8989b652449` | succeeded | 2026-11-23 17:50:53 | `outputs/05_企业AI可见度与声量追踪周报.md`<br>`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md`<br>`outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md` |
| `build_site` | demo_corp | `328109723062382592` | `job_09849bd8e9654b0e87d93cfacbb4a732` | succeeded | 2026-11-23 17:50:54 | `outputs/site/index.html`<br>`outputs/site/llms.txt`<br>`outputs/site/robots.txt`<br>`outputs/site/schema.jsonld`<br>`outputs/02_站点技术底座改造交付包.md` |
| `build_blog` | nextgeo | `328109727516733440` | `job_5e7db5ad90ba497190f018871eb4688b` | succeeded | 2026-11-23 17:50:56 | `outputs/03_普林斯顿9因子高权威语料库.md` |
| `boss_report` | nextgeo | `328109731966889984` | `job_fe6edb40e25d4069a7e41a10f70c4b17` | succeeded | 2026-11-23 17:50:57 | `outputs/01_企业AI可见度商业诊断报告.html` |
| `share_portal` | nextgeo | `328109736429629440` | `job_9407263ac4044772b7c4364b532e898e` | succeeded | 2026-11-23 17:50:58 | `outputs/share_portal_data.json`<br>`outputs/00_GEO交付看板_离线单文件版.html` |
| `distribute_pack` | demo_corp | `328109740875591680` | `job_ef81b122c68d45779d030df53f979eff` | succeeded | 2026-11-23 17:50:59 | `outputs/dist_toutiao_article.md`<br>`outputs/dist_zhihu_article.md`<br>`outputs/dist_wechat_article.html`<br>`outputs/dist_channels_checklist.md`<br>`outputs/distribute_run_log.json`<br>`outputs/04_多平台矩阵借壳分发包.md` |
| `acceptance_report` | demo_corp | `328109745355108352` | `job_9c0020f74a36427f965f02301fadf17b` | succeeded | 2026-11-23 17:51:00 | `outputs/00_GEO商业交付验收结案确认单.md`<br>`outputs/acceptance_summary.json`<br>`outputs/07_选型差异化对比图.svg`<br>`outputs/08_企业技术全景架构图.svg`<br>`outputs/09_60秒短视频高转化口播脚本.md`<br>`outputs/09_GEO全案商业交付结案与数字资产移交证书.html` |
| `pitch_roi` | demo_corp | `328109749788487680` | `job_0ff099d7ecc64572beeb83856835e195` | succeeded | 2026-11-23 17:51:01 | `outputs/00_GEO全案商业服务投标建议书与PitchDeck.md` |

---

## 四、增量迁移与运维服务收口核验

1. **增量迁移入库与 runner 登记确认**：
   - 迁移脚本：`migrations/2026-11-23_alter_geo_worker_jobs_worker_job_id_null.up.sql`
   - DDL 内容：`ALTER TABLE geo_worker_jobs MODIFY COLUMN worker_job_id VARCHAR(128) NULL DEFAULT NULL;`
   - 表结构核验：`SHOW COLUMNS FROM geo_worker_jobs LIKE 'worker_job_id'` 输出 `varchar(128) YES NULL DEFAULT NULL`
   - 迁移版本登记核验：查询 `schema_migrations` 实测已记录：
     `('2026-11-23_alter_geo_worker_jobs_worker_job_id_null', '2026-11-23 09:10:42')`
2. **旧管理台服务与端口下线核验**：
   - 旧 LaunchAgent：`com.geo.web-8088` 已正式 unload；
   - 端口状态：`lsof -i :8088` 返回空（端口 8088 已完全释放）；
   - 后厂常驻服务：`launchctl list | grep geo` 实测仅 `com.xiulan.geo-worker-18092` 在线稳定运行；
   - Nginx 代理配置：`deploy/nginx_geo.conf` 中指向 `127.0.0.1:8088` 的反代 `location /` 与文档反代已正式注释下线，严禁整块删除。
3. **真实 CDN Purge 客户端集成**：
   - 新建 `pkg/geo/cdnclient/cdn_client.go`，由 Go 后端发出真实 HTTP POST 刷新请求，支持动态注入端点与鉴权凭据；
   - 彻底移除了 Handler 中的本地合成任务 ID 逻辑；
   - 成对测试：`cdn_client_test.go` 覆盖 Token 缺失、服务端拒绝 (500) 与成功返回 (200) 三条完整分支；
   - 单测与 E2E 验证全部通过。
4. **Nginx 客户配置生成器完善与红线 0.2 治理**：
   - `cmd/gen_geo_nginx/main.go` 严格模块化拆分为 11 个独立函数，每个函数 <= 35 行，彻底满足红线 0.2 函数行数门禁（<= 50 行）；
   - 解决多租户根域名互斥：对绑定了 `geo.baicl.cc` 的客户项目（如 `xuzhou_xuanyuan`），略过生成独立整站块，统一由共享多租户 `server_name geo.baicl.cc` 块承接，根除同名 server 块冲突；
   - 严格包含 `location ~* ^/sites/([^/]+)$ { return 301 /sites/$1/; }` 缺尾斜杠 301 永久重定向规则；
   - 为各客户站点生成专属子路径静态映射；
   - 在 mini 端就地重新生成 `deploy/nginx_customer.conf`（4400 字节，5 客户整站块 + 1 共享多租户块，花括号平衡）。
5. **GEO 仓平行源停写收口**：
   - `ad_orders.py`：在非测试目录默认停写 `projects/{id}/ad_orders.json`，业务状态由小毛驴 Go 后端 `geo_ad_orders` 承接；
   - `check_ledger.py`：默认停写 `data/ops_check_logs.jsonl`；
   - `patrol.py`：默认停写 `projects/{id}/history.db`；
   - `task_runner.py`：默认停写 `data/tasks.json`；
   - 单元测试与测试临时目录不受影响（23 项 Python 测试全部通过）。
6. **红线 0.2 函数行数治理与 Launchd 彻底清理**：
   - mini 端执行 `launchctl bootout` 并物理删除 `/Users/ne/Library/LaunchAgents/com.geo.web-8088.plist`，彻底杜绝机器重启复活 8088；
   - `pkg/geo/logic/geo_worker_logic.go` 完成重构：`Append`（39 行）、`pollWorkerJob`（24 行），全文件 10 个函数最大 39 行，全部进入 <= 50 行红线内；
   - 重新交叉编译并在 mini 端重启 `com.xiulan.backend-3002`。
7. **真实 MySQL 幂等迁移测试覆盖**：
   - `migrations/real_mysql_idempotent_test.go` 将 `2026-11-23_create_geo_five_tables.up.sql` 与 `2026-11-23_alter_geo_worker_jobs_worker_job_id_null.up.sql` 纳入 `targetFiles`；
   - 真实在线执行 2 轮重复迁移与结构验证（`TestRealMySQLIdempotentMigrations`），验证 5 张 GEO 业务表存在性，断言 `geo_worker_jobs.worker_job_id` 为 `IS_NULLABLE=YES`，测试全部 PASS（9.25s）。

---

## 五、门禁与合规核验总结

1. **红线 0.1.1**：全篇报告与源码 0 Emoji；
2. **红线 0.3**：成对反向红线断言全部通过（401 / 400 / 404 精准返回，无默认兜底）；
3. **红线 9.2**：后厂 Python 进程严格 0 MySQL 链接，参数注入 `mysql://` 即刻返回 400 阻断；
4. **OpenSpec 规格一致性**：`openspec validate geo-workbench-and-mysql-backend --strict` 验证通过。
