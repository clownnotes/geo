# Tasks: 企业建档极简重构实施清单

## 1. 数据库独立物理字段迁移（数据结构先行）

- [x] 1.1 编写 UP 数据库迁移脚本 `migrations/2026-11-24_add_enterprise_onboarding_fields_to_geo_projects.up.sql`，在 `geo_projects` 表中复用已有 `name` 与 `domain` 列，新增 7 个独立物理字段（`brand_name`、`category`、`one_liner`、`target_audience`、`contact_phone`、`expected_queries`、`competitor_names`），并运行语法校验验证无报错
- [x] 1.2 编写成对的 DOWN 数据库迁移脚本 `migrations/2026-11-24_add_enterprise_onboarding_fields_to_geo_projects.down.sql`，在 `migrations/idempotent_migration_test.go` 中新增迁移测试函数，并将新 `.up.sql` 加入 `migrations/real_mysql_idempotent_test.go` 的 `targetFiles` 白名单，运行单元测试验证正反向迁移与 DDL 幂等容错通过

## 2. Go 后端模型、传输对象、仓储与业务逻辑改造

- [x] 2.1 更新 GORM 数据模型 `model/entity/geo/geo_project.go`，扩充 `BrandName`、`Category`、`OneLiner`、`TargetAudience`、`ContactPhone`、`ExpectedQueries`、`CompetitorNames` 等 7 个实体字段与映射标签，运行 `go test ./model/entity/geo/...` 验证编译通过
- [x] 2.2 更新客户档案数据传输对象 `dto/geo_dto.go`，在 `CreateGeoProjectReq` 中彻底删除 `Code` 字段关闭后门，将 `BrandName`、`Category`、`OneLiner` 设为必填，补充 6 项选填字段，并同步更新 `GeoProjectResp` 增加对应字段，运行 `go test ./dto/...` 验证无类型错误
- [x] 2.3 改造核心业务逻辑 `pkg/geo/logic/geo_project_logic.go` 的 `Append` 方法，使用 `utf8.RuneCountInString` 实现 `OneLiner` 15 至 80 字严格校验、无条件将雪花 ID 自动派生至 `code`、基于配置常量派生绝对 `output_dir` 并落盘独立字段，并在已有的 `Modify` 方法中支持各字段更新，编写并运行业务逻辑单元测试（包含正向创建与少于15字/缺必填的反向红线断言）验证全部 PASS
- [x] 2.4 改造客户仓储检索逻辑 `pkg/geo/repository/geo_project_repo.go` 的 `SearchWorkbench` 方法，将模糊匹配扩展覆盖 `brand_name / category / name / domain / code`，编写单测验证按品牌简称和核心品类可精准检索出目标客户
- [x] 2.5 改造接口处理器 `restful/gin/handler/geo_handler.go` 的 `CreateProject` 与 `UpdateProject` 方法，确保参数绑定适配新 DTO、函数体严格控制在 30 行以内，运行接口测试确认合法输入返回 201 Created，非法输入返回 400 BadRequest
- [x] 2.6 改造任务调度业务逻辑 `pkg/geo/logic/geo_worker_logic.go` 的 `Append` 方法，在调用后厂客户端提交任务前读取企业主档，将企业档案字段（品牌、品类、一句话母盘、工商名、域名、电话、问题库、竞品等）自动注入任务入参 `params`，运行单测验证任务入参组装正确

## 3. GEO 后厂 Worker 目录与配置初始化改造

- [x] 3.1 在 `src/tools/worker/handlers.py` 实现 `ensure_project_yaml` 助手函数，在任务分发前检查 `projects/{project_id}` 目录与 `project.yaml`，若缺失则基于任务入参幂等创建目录骨架并按映射表写入标准 YAML 配置（严格断言 `keywords` 与 `competitors` 为 YAML 列表结构，写入 `business_one_liner` 与 `area_served`），编写 Python 单元测试验证空目录下调用任务能自动生成 `project.yaml` 且各键名与列表类型断言通过

## 4. 前端管理端建档组件、卡片展示与工作台流转改造

- [x] 4.1 更新前端强类型定义文件 `src/admin/types/geoTypes.ts` 与 `src/admin/types/geoWorkbenchTypes.ts`，新增 3 项必填与 6 项选填字段定义，并同步更新 `src/admin/composables/useGeoProjects.ts` 中的接口入参，运行类型检查命令验证零 TS 报错
- [x] 4.2 重构快捷建档弹窗组件 `src/admin/components/geo/workbench/EnterpriseQuickCreateModal.vue`，彻底移除代号、服务辐射范围、归属合作方和默认二级域名输入项；实现 3 项必填字段输入（含 15~80 字一句话母盘动态字数统计与原灰色提示语）和 6 项选填卡片，创建成功后发射 `success` 事件并关闭弹窗，在浏览器中检查组件渲染与校验交互正常
- [x] 4.3 改造企业卡片展示组件 `src/admin/components/geo/workbench/EnterpriseCard.vue` 与 `src/admin/components/geo/GeoProjectCard.vue`，卡片主标题优先展示 `brand_name`（老项目兜底 `name || code`），副标题展示 `category`，杜绝新企业直接暴露纯数字代号
- [x] 4.4 改造企业选择面板与工作台联动 `src/admin/components/geo/workbench/EnterpriseSelectTab.vue` 与 `src/admin/views/geo/geo-workbench.vue`，在接收到快捷建档成功事件后自动加载最新列表、选定新企业雪花 ID 并平滑直达工作台干活面板（`geo_tab=work&project_id=...`），在 Safari 验证动线顺畅
- [x] 4.5 改造客户档案大盘视图 `src/admin/views/geo/geo-projects.vue` 中的新建/编辑弹窗，同步适配 3 必填 + 6 选填设计，移除代号输入框，新建成功后直接通过路由导航直达该企业的专属工作台页面，验证页面跳转与表单重置行为符合预期

## 5. 存量兼容性验收、Nginx 配置校验与端到端系统自测

- [x] 5.1 存量 `output_dir` 归一化与 Nginx 生成器崩溃防御：在 `cmd/gen_geo_nginx/main.go` 增加反向断言测试，确认当企业 `domain` 非空但 `output_dir` 为空时能精准拦截报错，对存量老数据执行 `output_dir` 绝对路径回填校验，验证存在真实域名时配置渲染正确且花括号平衡
- [x] 5.2 执行端到端完整流转自测：在开发环境录入一家新企业（3 必填 + 选填），验证接口 201 成功响应、数据库各字段独立落盘、自动直达工作台；触发后厂异步任务验证 `project.yaml` 自动生成且字段与列表结构完全合规；同时执行反向断言测试（少于15字母盘、缺必填），验证 100% 精准返回 400 拦截
