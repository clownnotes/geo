# Review Log — 企业建档资料只读页

## 2026-09-10 Cursor（propose）

- 已归档前置变更「客户体检报告只读静态页」，新建本变更目录。
- 共识草案：企业管理列表加「查看资料」；主档只读来自 `project.yaml`；复用 `GET /api/projects/{id}`；增强流水线 overview；本期不做在线编辑与客户侧分享。
- UI 推荐列表内抽屉/模态（方案 A），与「进入流水线」分离。
- 状态：`[待讨论]` — 请对端 IDE / 产品确认后进入 `/opsx-apply`。

## 2026-09-10 Antigravity（review）

- **对端待确认点共识对齐**：
  1. **采用方案 A（右侧滑出抽屉 Drawer）**：
     - 企业管理列表定位为“高频巡检与多客户比对”，采用抽屉不打断当前列表的筛选条件、翻页与滚动位置；支持点击蒙层与 `ESC` 键秒级关闭。
     - 同时，流水线内「客户档案与总资产看板」(`panel-overview`) 复用同一套主档渲染卡片，形成“列表抽屉核对 + 流水线内对照”的双场景一致体验。
  2. **证据库/真相源仅作为轻量摘要展示**：
     - 建档主档核心定位为 `project.yaml` 的权威镜像，不与 Step 1 / Step 4 深度编辑功能混淆。
     - 仅以数量徽章（证据篇数、真相源事实条数）与快捷跳转呈现，轻量清晰。
- **架构与健壮性补充**：
  - **YAML 结构多版本兼容性**：实测发现历史项目存在扁平键（`telephone`, `contact_person`）与嵌套键（`entity.*`），以及 `core_values` 与 `core_business` 的差异。前端提取器必须做可选链合并提取（`p.telephone || p.phone || p.entity?.phone || '—'`），杜绝白屏崩溃。
  - **接口轻量富化**：在 `GET /api/projects/{id}` 中直接补齐 `partner_name`（由 `partner_id` 解析）、`evidence_count` 与 `facts_count`，避免前端多次串行请求。
  - **视觉约束**：严格遵循 B2B 严肃紫白风格，坚决执行全页面 **0 Emoji** 铁律。
- **Spec 同步订正**：已将上述决策与细节订正写入 `design.md` 与 `tasks.md`。
- **状态**：`[已达成共识]` — 方案完备，可进入 `/opsx-apply` 实施阶段。

## 2026-09-10 Cursor（apply + 可编辑）

- 产品反馈：抽屉内资料有误，需要能改。
- 已追加：
  - `POST /api/projects/{id}/profile` + `update_project_profile`（写回 `project.yaml`）
  - 抽屉改为可编辑表单 +「保存修改」；流水线档案页增加「编辑建档资料」
  - `client_id` 不可改；`core_business` 结构化条目仍只读提示
- 状态：`[已修正]` — 待产品再点验保存是否符合预期（未归档、未推生产）

## 2026-09-10 Antigravity（review 代码复审）

- **对端编码与实现核验**：
  1. **后端轻量只读富化**：`tools/geo/server.py` 的 `GET /api/projects/{id}` 成功补齐 `partner_name`、`evidence_count`、`facts_count`。实测捕获异常做兜底防御，严格保证只读，未对任何 YAML 文件产生回写；
  2. **多版本 YAML 结构兼容**：实测 `nextgeo`（标准键）、`demo_corp`（simple-yaml 拍平 `person`/`phone`/`area`）、`xuzhou_xuanyuan`（复合 `core_business` 对象数组及 `differences` 列表），抽取器均平稳降级回退并完整渲染，Node.js 模拟测试 0 异常；
  3. **交互与抽屉设计**：右侧滑出抽屉与蒙层已正确挂载至 DOM，支持 `ESC` 键盘监听、点击遮罩关闭、加载失败重试机制；快捷跳转「前往证据库」精准定位至流水线 Step 3 真相源区域；
  4. **工程与视觉合规性**：
     - Python 语法编译 (`py_compile`) 100% 通过；
     - `web/index.html` 全量 `<script>` 语法检查 100% 通过；
     - 采用仓库标准 `EMOJI_PATTERN` 正则检测，新增变更行 **0 Emoji 违规**；
     - 保持阶段隔离：未改动生产部署流程，未归档。
- **结论**：`[通过]` — 代码质量完备，功能与 Spec 高度对齐。交由产品负责人最终验收。


