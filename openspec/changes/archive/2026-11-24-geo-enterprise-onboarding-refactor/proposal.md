# Proposal: 企业建档极简重构（雪花 ID 唯一标识、独立字段迁移、创建直达工作台）

## 用户核心原话实录（第一真理源）

> 1. 「做个 GEO 的企业建档，要有自己独立的数据库表。我们要以企业雪花 ID 作为唯一的数字身份证与真相源，取消什么『项目唯一代号』人工填写，无论是用户还是后台都是 AI 处理，不需要人工记什么英文代号。代号以前对应底层目录，要考虑怎么处理现有的存量代号与目录，不能破坏现有服务。」
> 2. 「建档输入要极简，必填项只保留 3 项：日常品牌简称、主打核心品类、一句话讲清楚客户的业务和优势（作为核心母盘，要保留字数要求）。原来那些很有价值的灰色提示语要留着。」
> 3. 「选填的项有：公司工商全称、主打客群/细分行业、官网域名（没有就不要填，保持为空，千万不要默认分配什么二级域名，分不清真假官网）、官方客服电话/微信、客户期望问题库、已知竞品。同样保留原有灰色提示语。」
> 4. 「彻底删除这些不需要的东西：项目唯一代号输入框、服务辐射范围、归属合作方（建档后再在合作方模块单独绑定，单一职责）、暂无官网由我方托管创建默认二级域名的勾选与分配逻辑。」
> 5. 「建档成功后，不要停在列表，直接跳转到该企业的工作台页面，带着企业的雪花 ID 直接进入工作台干活。」
> 6. 「在独立表里通过成对的迁移加物理字段，不要跨表借字段。前后端要完全打通，严格遵守工程守则。」

## Why

过去企业建档流程设计不够合理，要求用户自己绞尽脑汁手写英文字符代号，还塞入了大量不属于建档阶段的干扰项（比如服务辐射范围、归属合作方、甚至强行给没有官网的企业分配假二级域名），不仅增加操作负担，而且容易造成数据混乱。
现在通过将企业雪花 ID 确立为唯一的数字化身份证，取消手工代号填写，把建档输入压缩到最核心的 3 项必填内容，选填信息规整保留并复用已有公司名称与域名列，建档完成后一键直达企业工作台，并通过任务调度协议自动将档案数据打通至后厂项目配置文件，能让业务人员录入更轻松、系统数据更规范、前店后厂架构更坚固。

## What Changes

- **雪花 ID 唯一主键与彻底关闭代号入参**：
  - 前端彻底取消「项目唯一代号」输入框，Go 后端 `CreateGeoProjectReq` 彻底移除 `Code` 参数；
  - 创建企业档案时，后端在业务逻辑中无条件基于新生成的雪花 ID 自动派生 `code = fmt.Sprintf("%d", id)`，彻底杜绝人工代号；
  - 存量老项目原有英文代号只读兼容，保持底层目录与 Nginx 规则不受破坏。
- **精简必填字段（仅保留 3 项）**：
  - 日常品牌简称（`brand_name`，必填，保留提示语：“买家常搜口语词，T3/T4/T5 提问主角。”）
  - 主打核心品类（`category`，必填，保留提示语：“最精炼行业词，T1/T2 拿它问『做XX哪家靠谱』。”）
  - 一句话讲清楚客户的业务和优势（`one_liner`，必填，15 至 80 字，保留提示语：“必填核心母盘。讲清『卖什么』和『比同行强在哪』，决定出题买家场景准不准。”）
- **选填字段标准落盘与复用已有字段（避免双真相源）**：
  - 公司工商全称：直接复用 `geo_projects` 表中现有的 `name` 列（选填，执照法定全称），不新增重复的 `company_name` 字段，杜绝双真相源；
  - 主打客群 / 细分行业（`target_audience`，选填，卖给谁，用于垂直赛道提问）；
  - 官网域名：复用 `geo_projects` 表中现有的 `domain` 列（选填，真实官网链接；若无官网则明确留空为 NULL，严禁默认分配二级域名）；
  - 官方客服电话 / 微信（`contact_phone`，选填，用于真实联络与真机反查）；
  - 客户期望问题库（`expected_queries`，选填，完整问句，换行分隔）；
  - 已知竞品（`competitor_names`，选填，对标竞品名称，换行分隔）。
- **彻底删除 4 项冗余与越权项**：
  - 删除「项目唯一代号」输入框（用户无需记忆或手写代号）；
  - 删除「服务辐射范围」多选卡片及聚焦城市输入框（不属于基础建档范畴）；
  - 删除「归属合作方」选择器（改在合作方模块单独绑定，单一职责）；
  - 删除「暂无官网由我方托管创建默认二级域名」勾选框与默认分配逻辑（避免真假官网混淆）。
  - GEO 仓旧管理台 `src/web/index.html`（旧 :8088）的建档表单随旧管理台下线一并退场不再维护，全部建档能力收敛至小毛驴前店。
- **打通 Go 后端到后厂 project.yaml 与目录初始化闭环**：
  - Go 后端向后厂提交任务时，在任务参数中携带企业的完整档案数据；
  - 后厂 Worker 在执行任务前幂等创建 `projects/{project_id}` 目录并生成/同步 `project.yaml`，严格对齐后厂 YAML 键名与列表数据结构（如 `keywords`、`competitors` 列表，`business_one_liner`、`area_served`），保障建站与体检引擎正常读取，不产生 FileNotFoundError。
- **修复 output_dir 绝对路径口径**：
  - 默认产物目录采用基于配置/常量的绝对路径规范生成，与生产 Nginx 的 root/alias 路径完全一致，杜绝相对路径导致 404；
  - 官网域名为空的企业在生成 Nginx 配置时自动跳过生成独立 server 块。
- **前端卡片展示优化与检索增强**：
  - 前端企业卡片与列表优先展示日常品牌简称 `brand_name`，副标题展示品类 `category`，存量老项目兜底展示 `name || code`；
  - 关键词搜索扩展支持品牌简称、核心品类、公司全称、域名及代号的联合模糊检索。
- **建档完成直达企业工作台**：
  - 快捷新建或立项成功后，前端弹窗自动关闭，页面自动导航并选中新建的企业工作台页面，并将该企业的雪花 ID 同步写入 URL 查询参数（`geo_tab=work&project_id=...`）。

## Capabilities

### New Capabilities
- `enterprise-onboarding`: 覆盖企业建档输入校验、雪花 ID 唯一主键生成、后端 `geo_projects` 独立物理字段存储、向后厂同步档案并生成规范 project.yaml、以及前端创建成功后自动导航至企业工作台的端到端行为契约。

### Modified Capabilities
<!-- 本次变更不修改存量 dual-workspace-governance 与 geo-worker-contract 的规格需求，仅增加 enterprise-onboarding 独立能力 -->

## Impact

- **数据库迁移**：新增成对的迁移文件 `2026-11-24_add_enterprise_onboarding_fields_to_geo_projects.up.sql` 与 `.down.sql`，复用 `name` 与 `domain` 列，新增 7 个独立业务物理列。
- **Go 后端**：
  - 模型：`model/entity/geo/geo_project.go` 扩展对应物理字段；
  - 数据传输对象：`dto/geo_dto.go` 在 `CreateGeoProjectReq` 中移除 `Code`，新增 3 项必填与选填字段，更新 `GeoProjectResp`；
  - 业务逻辑：`pkg/geo/logic/geo_project_logic.go` 的 `Append` 方法自动派生雪花 ID 为 `code`，严格校验母盘字数；使用已有的 `Modify` 方法更新档案；在 `pkg/geo/logic/geo_worker_logic.go` 的 `Append` 方法中提交任务时携带档案参数；
  - 仓储层：`pkg/geo/repository/geo_project_repo.go` 检索逻辑扩展支持多字段匹配；
  - 接口处理器：`restful/gin/handler/geo_handler.go` 保持薄层转发，使用已有的 `CreateProject` 与 `UpdateProject`。
- **GEO 后厂 Worker**：
  - 调度分发：在 `src/tools/worker/handlers.py` 中增加任务前置检查，基于传入的档案参数幂等创建 `projects/{project_id}` 目录并生成对齐真实键名与列表结构的 `project.yaml`，打通后厂配置消费链条。
- **管理端前端（Vue 3）**：
  - 弹窗组件：`src/admin/components/geo/workbench/EnterpriseQuickCreateModal.vue` 重构为 3 必填 + 6 选填卡片，移除冗余字段，增加字数统计与校验；
  - 卡片与列表展示：`EnterpriseCard.vue` 与 `GeoProjectCard.vue` 优先展示 `brand_name`；
  - 客户列表视图：`src/admin/views/geo/geo-projects.vue` 新建/编辑弹窗同步适配；
  - 工作台协同：`EnterpriseSelectTab.vue` 与 `geo-workbench.vue` 保证新建成功后平滑携带 `project_id` 直达工作台；
  - 类型与通信：`src/admin/types/geoTypes.ts`、`src/admin/types/geoWorkbenchTypes.ts` 与 `useGeoProjects.ts` 更新字段定义。
- **后厂与 Nginx 兼容**：
  - 存量老项目 `code` 保持原状不受破坏；新项目 `code` 等于雪花 ID 字符串，`output_dir` 自动推导为绝对路径；
  - `cmd/gen_geo_nginx/main.go` 仅在 `domain` 非空且不为默认共享域名时生成独立 server 块，官网域名为空时正常跳过，完全兼容。
