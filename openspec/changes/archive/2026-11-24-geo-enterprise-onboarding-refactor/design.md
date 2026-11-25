# Design: 企业建档极简重构技术方案

## Context

在现有系统演进中，企业建档作为 GEO 业务的第一个操作节点，此前承载了过多非核心逻辑（如手工输入英文代号、选择辐射范围、绑定合作方、强行分配假二级域名等）。根据前店后厂架构定位规范（`dual-workspace-governance`），小毛驴（`/Users/a1/next核心项目`）作为唯一的业务前店与数据大管家，必须以企业雪花 ID 作为唯一真相源，并在 `geo_projects` 物理表中以独立列形式固化企业核心属性；同时必须保持对后厂无状态计算车间（`projects/{code}`）与 Nginx 静态站点挂载的完全兼容。

## Goals / Non-Goals

**Goals:**
- 将企业建档输入项从冗余繁琐精简为「3 项必填 + 6 项选填」，彻底剔除代号、辐射范围、合作方及假二级域名的输入与存储逻辑。
- 确立企业雪花 ID（分布式 uint64 / 前端 string）为前店全流程唯一数字身份证，取消前端手工填写代号，后端无条件基于雪花 ID 自动派生底层 code 与基于配置常量的绝对 output_dir。
- 避免双真相源：复用已有 `name` 列作为公司工商全称，复用已有 `domain` 列作为官网域名；在独立物理表 `geo_projects` 中新增 7 个独立业务物理字段，提供成对的 `.up.sql` / `.down.sql` 迁移脚本。
- 打通数据闭环：Go 后端在提交后厂任务时自动在入参中透传企业主档，后厂 Worker 在执行任务前幂等创建目录骨架并生成/同步规范 YAML 列表结构的 `project.yaml`，彻底解决 `FileNotFoundError` 隐患与类型错位。
- 建档成功后立即携带雪花 ID 直达企业工作台（`geo-workbench?geo_tab=work&project_id=...`）。
- 保持存量项目代号、后厂计算车间磁盘输出路径与 Nginx 多租户配置 100% 正常运行，不破坏任何存量服务。

**Non-Goals:**
- 不在建档环节处理合作方分成记账（合作方绑定在专属合作方管理模块中的 `geo_project_partners` 关系表闭环）。
- 不重写企业工作台内的具体作业子面板（如待办、SOP、保活基线、代采等子组件逻辑保持既有接口）。
- 不维护 GEO 仓旧管理台 `src/web/index.html`（旧 :8088）的建档表单，旧表单随旧管理台下线一并退场。

## 1对1映射推导链条表（用户核心原话 vs AI技术决定）

| 序号 | 用户核心原话实录（第一真理源） | AI 理解与技术决定 | 落地文件与架构闭环 |
|---|---|---|---|
| 1 | 「做个 GEO 的企业建档，要有自己独立的数据库表。我们要以企业雪花 ID 作为唯一的数字身份证与真相源，取消什么『项目唯一代号』人工填写，无论是用户还是后台都是 AI 处理，不需要人工记什么英文代号。代号以前对应底层目录，要考虑怎么处理现有的存量代号与目录，不能破坏现有服务。」 | 1. 前端彻底移除 code 输入框，前后端接口全生命周期统一使用雪花 ID（前端以 string 防精度丢失）。<br>2. 彻底关闭代号入参后门：`CreateGeoProjectReq` 移除 `Code` 字段，后端无条件由雪花 ID 自动派生 `code = fmt.Sprintf("%d", id)`。<br>3. 数据库保留 `code` 列与 `active_code` 唯一索引；存量老项目保持原有 code 字符串不变，新建项目 code 为雪花 ID 字符串，两套共存完全兼容。 | `model/entity/geo/geo_project.go`<br>`dto/geo_dto.go`<br>`pkg/geo/logic/geo_project_logic.go`<br>`cmd/gen_geo_nginx/main.go` |
| 2 | 「建档输入要极简，必填项只保留 3 项：日常品牌简称、主打核心品类、一句话讲清楚客户的业务和优势（作为核心母盘，要保留字数要求）。原来那些很有价值的灰色提示语要留着。」 | 1. 在 `geo_projects` 表新增 `brand_name VARCHAR(128)`、`category VARCHAR(128)`、`one_liner VARCHAR(255)` 物理列。<br>2. UI 保留高价值灰色提示语与示例占位符。<br>3. 前端与后端双重校验 `one_liner` 字符长度在 15 至 80 字区间（Go 后端使用 `utf8.RuneCountInString` 精确对齐），UI 提供动态字数统计指示器。 | `migrations/*.up.sql`<br>`EnterpriseQuickCreateModal.vue`<br>`pkg/geo/logic/geo_project_logic.go` |
| 3 | 「选填的项有：公司工商全称、主打客群/细分行业、官网域名（没有就不要填，保持为空，千万不要默认分配什么二级域名，分不清真假官网）、官方客服电话/微信、客户期望问题库、已知竞品。同样保留原有灰色提示语。」 | 1. 避免双真相源：复用表内已有 `name VARCHAR(191)` 列作为「公司工商全称（选填）」，不新增 `company_name` 列；复用已有 `domain VARCHAR(191)` 列作为「官网域名（选填）」。<br>2. 新增 `target_audience VARCHAR(255)`、`contact_phone VARCHAR(64)`、`expected_queries TEXT`、`competitor_names TEXT` 独立物理列（新增物理列总计 7 个）。<br>3. 官网域名未填时严格落盘空字符串或 NULL，绝对不执行默认拼接 `{代号}.baicl.cc`；Nginx 配置文件生成器判断 domain 为空自动跳过生成独立 server 块，避免生成假官网。 | `migrations/*.up.sql`<br>`model/entity/geo/geo_project.go`<br>`dto/geo_dto.go`<br>`cmd/gen_geo_nginx/main.go` |
| 4 | 「彻底删除这些不需要的东西：项目唯一代号输入框、服务辐射范围、归属合作方（建档后再在合作方模块单独绑定，单一职责）、暂无官网由我方托管创建默认二级域名的勾选与分配逻辑。」 | 1. 彻底删除前端建档弹窗中对应代号、辐射范围（含聚焦城市）、合作方选择、托管二级域名的输入与展示组件。<br>2. 合作方绑定严格由合作方管理模块的 `geo_project_partners` 关系表承接。<br>3. 前端提交 Payload 剔除无关参数，后端废弃相关冗余字段接收；GEO 仓旧管理台 `src/web/index.html` 对应旧表单随旧台退场，不再维护。 | `EnterpriseQuickCreateModal.vue`<br>`geo-projects.vue`<br>`dto/geo_dto.go`<br>`src/web/index.html` |
| 5 | 「建档成功后，不要停在列表，直接跳转到该企业的工作台页面，带着企业的雪花 ID 直接进入工作台干活。」 | 1. 快捷建档成功后，弹窗 emit 成功事件并关闭，触发 `useGeoWorkbench().selectEnterprise`。<br>2. 页面自动切换至工作台面板（`geo_tab=work`），并由 `useGeoContext` 将雪花 ID 同步写入 URL query（`project_id={id}`）。<br>3. 档案管理列表页新建成功后，调用导航器直接跳转工作台相同路径。 | `EnterpriseQuickCreateModal.vue`<br>`EnterpriseSelectTab.vue`<br>`geo-workbench.vue`<br>`geo-projects.vue` |
| 6 | 「在独立表里通过成对的迁移加物理字段，不要跨表借字段。前后端要完全打通，严格遵守工程守则。」 | 1. 创建规范的 `.up.sql` 与 `.down.sql` 迁移，新增 7 个独立物理列，严格执行 DDL 幂等与双向回滚，依赖 `sql_runner` 容错机制。<br>2. Go 后端在 `GeoWorkerLogic.Append` 中提交后厂任务时自动在入参中透传企业主档，后厂 Worker 幂等初始化目录骨架并按消费键名规范生成 `project.yaml`（列表结构严禁写字符串），打通前后端与后厂完整闭环。<br>3. Go 后端遵守单函数 < 50 行、Handler < 30 行规范，前端遵守单组件 < 200 行规范。 | `migrations/` 目录<br>`pkg/geo/` 各分层<br>`src/tools/worker/handlers.py` |

## 业务对象三问对齐

1. **对象是谁 (Entity)**：
   - 核心业务实体英文名词：`GeoProject`（企业客户独立档案）。
   - 坚决杜绝泛指词，在所有代码、DTO 与模型中统一命名为 `GeoProject` / `geo_projects`。
2. **属性有哪些 (Attributes)**：
   - 核心唯一主键：`id` (BIGINT UNSIGNED, 分布式雪花 ID)。
   - 底层安全兼容属性：
     - `code` (VARCHAR(128), 自动等于雪花 ID 字符串)；
     - `active_code` (防冲突生成列)；
     - `output_dir` (VARCHAR(191), 自动初始化为基于配置常量的绝对路径 `{GEO_PROJECTS_BASE_DIR}/{code}/outputs/site`)。
   - 3 项必填核心业务属性：
     - `brand_name` (VARCHAR(128) NOT NULL DEFAULT '')：日常品牌简称。
     - `category` (VARCHAR(128) NOT NULL DEFAULT '')：主打核心品类。
     - `one_liner` (VARCHAR(255) NOT NULL DEFAULT '')：一句话业务与优势（15~80 字）。
   - 6 项选填辅助业务属性（2 个复用存量列 + 4 个新增列）：
     - `name` (VARCHAR(191) NULL DEFAULT '')：公司工商全称（复用已有列，执照法定全称，杜绝双真相源）。
     - `domain` (VARCHAR(191) NULL DEFAULT '')：真实官网域名（复用已有列，无官网即为空，绝不胡乱分配）。
     - `target_audience` (VARCHAR(255) NULL DEFAULT '')：主打客群 / 细分行业。
     - `contact_phone` (VARCHAR(64) NULL DEFAULT '')：官方客服电话 / 微信。
     - `expected_queries` (TEXT NULL)：客户期望问题库（换行分隔）。
     - `competitor_names` (TEXT NULL)：已知竞品（换行分隔）。
   - 系统与生命周期属性：`lifecycle_phase` (VARCHAR(32)), `is_pinned` (TINYINT(1)), `created_at`, `updated_at`, `deleted_at`。
3. **行为由谁做 (Behaviors)**：
   - 创建新企业档案：由 `GeoProjectLogic.Append` 方法闭环执行。负责校验必填项、校验一句话母盘字数、生成雪花 ID、派生 code 与绝对 output_dir、插入 `geo_projects` 物理表并在同一个数据库事务中级联初始化 8 个默认 SOP 步骤（`step-0` 至 `step-7`）。
   - 更新企业档案：由已有的 `GeoProjectLogic.Modify` 方法闭环执行（统一方法命名，不造 `Update`）。支持更新选填或必填业务属性。
   - 查询与检索档案：由 `GeoProjectLogic.Fetch` 与 `GeoProjectLogic.ListWorkbenchProjects` 闭环执行，`geo_project_repo.go` 扩展支持 `brand_name / category / name / domain / code` 联合模糊检索与工作台置顶排序。
   - 任务参数装配：由 `GeoWorkerLogic.Append` 在提交任务前自动读取企业主档并将档案字段填充至 `params`。
   - 控制器薄层规范：`GeoHandler.CreateProject`、`GeoHandler.UpdateProject`（方法名与源码 `geo_handler.go:107` 严格对齐）函数体严格不超过 30 行，仅负责参数解析与响应状态码映射。

## 数据库迁移设计 (.up.sql / .down.sql)

实测查证 `restful/gin/main.go`（第 359-400 行），后端 GORM `AutoMigrate` 仅对用户等部分表做自动迁移，完全不包含 `geo_projects`。因此 `geo_projects` 表结构演进严格依赖 `migrations/` 目录。
迁移文件命名采用小毛驴统一迁移规范：
- `migrations/2026-11-24_add_enterprise_onboarding_fields_to_geo_projects.up.sql`
- `migrations/2026-11-24_add_enterprise_onboarding_fields_to_geo_projects.down.sql`

**UP 迁移设计内容（严格新增 7 个独立物理列）：**
（说明：MySQL 8.0.46 不支持 `ALTER TABLE ADD COLUMN IF NOT EXISTS` 语法，脚本遵循小毛驴既有模式，依赖 `sql_runner` 对 duplicate column 错误的容忍机制保证幂等）。
```sql
-- 为 geo_projects 表扩展企业建档极简重构独立物理字段 (复用已有 name 与 domain 列，严格新增 7 列)
ALTER TABLE `geo_projects`
  ADD COLUMN `brand_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '日常品牌简称(T3/T4/T5主角)' AFTER `code`,
  ADD COLUMN `category` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '主打核心品类(T1/T2提问词)' AFTER `brand_name`,
  ADD COLUMN `one_liner` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '一句话讲清业务和优势(15-80字核心母盘)' AFTER `category`,
  ADD COLUMN `target_audience` VARCHAR(255) NULL DEFAULT '' COMMENT '主打客群/细分行业(T2垂直赛道)' AFTER `name`,
  ADD COLUMN `contact_phone` VARCHAR(64) NULL DEFAULT '' COMMENT '官方客服电话/微信(T5题反查底牌)' AFTER `domain`,
  ADD COLUMN `expected_queries` TEXT NULL COMMENT '客户期望问题库(换行分隔)' AFTER `contact_phone`,
  ADD COLUMN `competitor_names` TEXT NULL COMMENT '已知竞品列表(换行分隔)' AFTER `expected_queries`;
```

**DOWN 迁移设计内容：**
```sql
-- 回滚 geo_projects 新增的企业建档 7 个字段
ALTER TABLE `geo_projects`
  DROP COLUMN `competitor_names`,
  DROP COLUMN `expected_queries`,
  DROP COLUMN `contact_phone`,
  DROP COLUMN `target_audience`,
  DROP COLUMN `one_liner`,
  DROP COLUMN `category`,
  DROP COLUMN `brand_name`;
```

## 后端改造设计（Go 后端）

1. **实体定义 (`model/entity/geo/geo_project.go`)**：
   在 `GeoProjectModel` 中追加 `BrandName`, `Category`, `OneLiner`, `TargetAudience`, `ContactPhone`, `ExpectedQueries`, `CompetitorNames` 等 7 个字段及 gorm tag（已有的 `Name` 映射工商全称，`Domain` 映射官网）。
2. **数据传输对象 (`dto/geo_dto.go`)**：
   - `CreateGeoProjectReq`：彻底删除 `Code` 字段，杜绝人工代号；将 `BrandName`、`Category`、`OneLiner` 设为必填字段；补充 `Name`（工商全称）、`Domain`（官网域名）、`TargetAudience`、`ContactPhone`、`ExpectedQueries`、`CompetitorNames` 等 6 项选填字段。
   - `UpdateGeoProjectReq`：增加所有新业务字段的可选指针类型。
   - `GeoProjectResp`：返回全部独立字段给前端，提供完整回显。
3. **业务逻辑层 (`pkg/geo/logic/geo_project_logic.go` & `geo_worker_logic.go`)**：
   - `Append` 方法改造：
     - 校验 `BrandName` 非空、`Category` 非空；
     - 使用 `utf8.RuneCountInString(oneLiner)` 严格校验字符长度在 [15, 80] 之间，若不满足直接返回 `ErrBadRequest`；
     - 生成雪花 ID：`projectID := idgen.NewID()`；
     - 无条件派生安全代号：`code := fmt.Sprintf("%d", projectID)`；
     - 派生绝对输出路径：取消硬编码路径字面量，读取常量或环境变量 `GEO_PROJECTS_BASE_DIR`（开发环境由环境变量指定，生产环境默认指向 `/Users/ne/apps/GEO/projects`），通过 `filepath.Join(baseDir, code, "outputs", "site")` 拼装绝对路径；
     - 将各独立字段赋予实体并在事务中落盘，级联初始化 8 个 SOP 默认步骤。
   - `Modify` 方法改造：保持原有方法命名，支持各独立字段局部更新。
   - `geo_worker_logic.go` 改造：在 `Append` 方法中调用后厂客户端提交任务前，读取关联的 `GeoProjectModel`，在 `params` 中注入该企业档案数据：`brand_name`, `category`, `one_liner`, `company_name` (即 `project.Name`), `domain`, `target_audience`, `contact_phone`, `expected_queries`, `competitor_names`。
4. **仓储层搜索扩展 (`pkg/geo/repository/geo_project_repo.go`)**：
   - `SearchWorkbench` 改造：将检索条件扩展为 `brand_name LIKE ? OR category LIKE ? OR name LIKE ? OR domain LIKE ? OR code LIKE ?`，确保搜索品牌或品类时能精准命中。
5. **接口处理器 (`restful/gin/handler/geo_handler.go`)**：
   - `CreateProject` 接收新 DTO 并调用 `Append`，创建成功返回 201 Created。
   - `UpdateProject`（与现有源码函数名一致）接收参数并调用 `Modify`。方法体严格保持在 30 行以内。

## GEO 后厂 Worker 目录与配置初始化设计 (Python)

### 1. 痛点分析与消费依据
- `src/tools/geo/scaffold.py:439` 调 `load_project_config(project_id)`；
- `src/tools/geo/utils.py:172-173` 在 `projects/{id}/project.yaml` 不存在时直接抛出 `FileNotFoundError`；
- 后厂引擎真实消费字段包括：
  - `industry`、`competitors`（列表）、`slogan`、`area_served`（`defense.py:26-30`）；
  - `defense.py:68` 直接执行 `"、".join(competitors)`，若 `competitors` 为字符串会发生按字符截断；
  - `keywords` 列表（`scaffold.py:37`、`intent.py:513`、`distribute.py:251`、`audit.py:574`）；
  - `business_one_liner` 校验母盘字数（`utils.py:46`）。

### 2. 前店字段 -> 后厂 project.yaml 映射与结构规范

| 前店字段 (MySQL/DTO) | 前店类型 | 后厂 project.yaml 键 | YAML 类型 | 转换与清洗规则 | 真实消费引擎与场景 |
|---|---|---|---|---|---|
| `code` | string | `client_id` | string | 标量字符串（数字雪花代号或老代号） | `utils.py` 目录基准与项目标识 |
| `brand_name` | string | `brand_name` | string | 标量字符串 | `defense.py`、`audit.py` 出题与体检主角 |
| `name` | string | `company_name` | string | 标量字符串（自动兼顾 `client_name`） | `defense.py`、`scaffold.py` 版权抬头 |
| `category` | string | `industry` | string | 标量字符串 | `defense.py`、`scaffold.py` 行业分类 |
| `one_liner` | string | `business_one_liner` / `slogan` | string | 标量字符串，同时写入 `business_one_liner` 与 `slogan`，不覆盖存量 `company_profile` | `utils.py:46` 母盘字数校验、`intent.py` |
| `target_audience` | string | `area_served` / `target_audience` | string | 标量字符串，同时写入 `area_served` 与 `target_audience` | `audit.py:638`、`defense.py:30` |
| `domain` | string | `official_url` | string | 标量字符串（若为空则写空字符串） | `scaffold.py`、`audit.py` 抓取与建站 |
| `contact_phone` | string | `telephone` | string | 标量字符串 | `intent.py`、`audit.py` 联络核验 |
| `expected_queries` | text | `keywords` | **list** | **必须为 YAML 列表**：按 `\n` 切分并 strip 过滤空行，输出为 `- "问句"`，严禁存字符串 | `utils.py`、`intent.py`、`distribute.py` 核心词库 |
| `competitor_names` | text | `competitors` | **list** | **必须为 YAML 列表**：按 `\n` 切分并 strip 过滤空行，输出为 `- "竞品"`，严禁存字符串，防 `"、".join` 逐字截断 | `defense.py:29,68` 竞品压制大纲与 Prompt |
| (系统生成) | - | `master_version` | string | 固定标量 `"1.0.0"` | `utils.py:188` 母盘版本坐标 |

### 3. 后厂实现逻辑
在 `src/tools/worker/handlers.py` 的 `dispatch_job` 函数执行前，增加 `ensure_project_yaml(project_id, params)` 助手函数：
1. 检查 `projects/{project_id}/` 目录是否存在，不存在则使用 `os.makedirs` 创建，并建立 `outputs/` 与 `raw_materials/` 子目录；
2. 检查 `project.yaml` 是否存在；若不存在或入参含有档案信息，则按上述映射表将字符串切分为列表并写入 YAML 文件；
3. 严格遵循前店后厂架构红线：Go 后端绝不直接写后厂磁盘目录，后厂 Worker 保持无状态自闭环。

## 前端改造设计（Vue 3 管理端）

1. **类型定义与 Composable**：
   - `geoTypes.ts` 与 `geoWorkbenchTypes.ts`：扩充新字段定义，去除已废弃字段。
   - `useGeoProjects.ts`：更新 `createProject` 入参签名，支持提交新表单数据。
2. **弹窗重构 (`EnterpriseQuickCreateModal.vue`)**：
   - 顶部布局：保留麦肯锡风格简洁紫边卡片容器。
   - 核心必填区（红星必填，显式呈现原灰色提示语）：
     - 日常品牌简称：输入框 + 提示语「买家常搜口语词，T3/T4/T5 提问主角。」
     - 主打核心品类：输入框 + 提示语「最精炼行业词，T1/T2 拿它问『做XX哪家靠谱』。」
     - 一句话优势：文本域（minlength 15, maxlength 80） + 右上角实时字数统计（`X/80 字`） + 提示语「必填核心母盘。讲清『卖什么』和『比同行强在哪』，决定出题买家场景准不准。」
   - 更多选填资产区（可折叠或独立区块，保留原有价值提示语）：
     - 公司工商全称（绑定 `name` 字段）
     - 主打客群 / 细分行业（绑定 `target_audience`）
     - 官网域名（绑定 `domain`，留空即无，绝无二级域名勾选框）
     - 官方客服电话 / 微信（绑定 `contact_phone`）
     - 客户期望问题库（绑定 `expected_queries`，多行文本域）
     - 已知竞品（绑定 `competitor_names`，多行文本域）
   - 彻底删除代号、辐射范围、合作方、默认二级域名相关 DOM 与变量。
   - 校验逻辑：前端实时校验 3 项必填项与一句话字数，未达 15 字或超过 80 字禁用提交按钮并显式红框报错。
   - 成功直达流转：调用 API 成功后，`emit('success', created)` 并关闭弹窗。
3. **企业卡片展示优化 (`EnterpriseCard.vue` & `GeoProjectCard.vue`)**：
   - 卡片主标题优先展示 `enterprise.brand_name || enterprise.name || enterprise.code`；
   - 副标题展示 `enterprise.category`，杜绝新企业直接暴露 19 位数字代号。
4. **工作台直达流转 (`EnterpriseSelectTab.vue` & `geo-workbench.vue`)**：
   - 在 `EnterpriseSelectTab.vue` 的 `handleCreateSuccess` 中，加载最新企业列表后，调用 `emit('select-enterprise', created)`。
   - 在 `geo-workbench.vue` 中，`handleSelectEnterprise` 自动将 `activeTab` 切换为 `'work'`，通过 `useGeoContext` 将雪花 ID 写入 URL query `project_id` 与 `geo_tab=work`，实现一秒直达企业干活面板。
5. **客户档案列表页同步 (`geo-projects.vue`)**：
   - 新建/编辑弹窗同步采用相同的 3 必填 + 6 选填设计，移除代号输入框。新建成功后直接通过路由导航直达该企业的专属工作台页面。

## Risks / Trade-offs

- **[Risk] 存量老项目与后厂目录兼容性风险**
  - 表象：后厂 worker 和本地开发脚本此前重度依赖形如 `projects/nextgeo` 这样的英文代号目录，如果新建项目取消了代号，后厂会不会找不到目录报错？
  - 缓解措施：在数据库层面保留 `code` 列，新项目自动把雪花 ID 作为 `code`（如 `projects/190012345678901234`），纯数字字符完全符合系统目录名正则；老项目原有英文代号原封不动保留，双轨兼容无缝过渡。后厂调度器通过 `ensure_project_yaml` 幂等创建目录与配置，两端无缝兼容。
- **[Risk] 存量 output_dir 为空或相对路径导致 Nginx 生成器 Fatal 崩溃**
  - 表象：`cmd/gen_geo_nginx/main.go:122` 在 `outDir == ""` 时直接 `log.Fatalf`。如果存量老数据有绑定域名但 `output_dir` 为空，会破坏 Nginx 配置生成。
  - 缓解措施：在实施阶段增加存量数据归一化回填脚本/迁移；同时单测显式断言「绑定了域名但 output_dir 为空」必须被防线捕获并显式报错，杜绝盲目生成残缺配置。
- **[Risk] 前端输入字数与后端 Unicode 判定差异**
  - 表象：JS `string.length` 与 Go 后端 `len(str)`（字节数）计算汉字长度不同，可能导致前端显示 15 字而后端按字节算成 45 字节或反向报错。
  - 缓解措施：Go 后端必须使用 `utf8.RuneCountInString(oneLiner)` 计算字符数，严格与前端的字符计数口径 100% 对齐。

## Migration Plan

1. 在开发环境执行数据库迁移 `2026-11-24_add_enterprise_onboarding_fields_to_geo_projects.up.sql`，并在 `migrations/idempotent_migration_test.go` 与 `real_mysql_idempotent_test.go` 增加测试验证；
2. 升级 Go 后端 Model、DTO、Repo、Logic 与 Handler，运行自动化单元测试验证雪花 ID 自动派生、检索匹配与字数区间校验；
3. 更新 GEO 后厂 Worker 的 `ensure_project_yaml` 逻辑，验证异步建站任务在空目录下的自动初始化与 YAML 列表结构规范；
4. 更新 Vue 3 前端类型定义与建档弹窗组件，卡片优先展示品牌简称，本地 Safari 验证建档与自动直达工作台动线；
5. 运行 `cmd/gen_geo_nginx` 验证 Nginx 配置生成器对新老档案与绝对路径的兼容性。
