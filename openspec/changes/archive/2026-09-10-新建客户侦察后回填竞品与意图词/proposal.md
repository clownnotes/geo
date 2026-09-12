# Proposal: 新建客户侦察后回填竞品与意图词

## Why (为什么做)

- **痛点**：新建客户弹窗要求运营「自己想」主要竞品与核心意图词；多数情况下不知道填什么，于是瞎编假竞品，或一键灌满 50 组假想问句。空壳项目与本地 GEO 打样已证明：假名单与糙词库会污染监测、审计与交付叙事。
- **已证实污染源**：`tools/geo/server.py` 新建项目时，若词库/竞品为空会强制写入 `["行业核心推荐词", "好用方案对比"]` 与 `["竞品A", "竞品B"]`——一期必须拆除。
- **已具备能力**：外部 IDE（Cursor）出剧本 + 反重力在已登录豆包的 Safari 上实战提问（见 `docs/specs/llm-browser-probe-sop.md`）。
- **目标顺序翻转**：先建壳 → 实战侦察 → 从答案回填竞品与必测问句 →（可选）再裂变长尾。空着创建优于瞎填；不强制 50 词。

## What Changes (改动了什么)

### 一期（本变更 apply 范围）

1. **拆除假占位**：创建时允许 `keywords: []`、`competitors: []`，不再静默塞假词/假竞品。
2. **新建弹窗降压**：代号 / 名称 / 官网 / 行业必填；意图词与竞品可选；文案「空比瞎填好」；0 Emoji。
3. **侦察状态**：`probe_status` / `probe_baseline_id` / `probe_baseline_at` 写入 `project.yaml`；经现有 `POST /api/projects/{id}/profile` 的 `scalar_keys` 读写（**不新开专用状态 API**）。
4. **企业管理 UI**：未侦察徽章 / 词库 0「待回填」；「推演 50」降级为必测草稿或基线后扩写文案。
5. **CLI**：`probe-script`（6～10 题）+ `probe-preview` / `probe-apply`（从 probe 文件回填）；供 Cursor 无 UI 调用。
6. **SOP**：扩展 `llm-browser-probe-sop.md` 与战略清单 P2 承接说明。

### 二期（明确不做于本变更）

- Web 端 JSON 上传回填、`/probe/script|preview|apply` 专用 HTTP 接口。
- 管理台内嵌反重力 / 豆包自动化。

## Capabilities (新增或修改的对外能力)

| 能力 | 期次 | 说明 |
| :--- | :--- | :--- |
| 空壳建档 | 一期 | `POST /api/projects` 允许空词库/竞品，默认 `probe_status=unprobed` |
| 侦察状态读写 | 一期 | 经 `update_project_profile` / `POST .../profile` |
| 必测题 + 回填 CLI | 一期 | `geo probe-script` / `probe-preview` / `probe-apply` |
| 企业管理侦察展示 | 一期 | 列表角标 + 新建文案 |
| Web 探测上传回填 | 二期 | 不在本变更编码 |

## Impact (受影响的部分)

- **前端**：`web/index.html`（新建弹窗、企业管理表、资料抽屉展示；一期资料抽屉仅展示状态与 IDE 回填说明，不做上传控件）。
- **后端**：`tools/geo/server.py` 创建逻辑；`tools/geo/utils.py` 的 `scalar_keys`；新建 CLI 模块与单测。
- **规范**：`docs/specs/llm-browser-probe-sop.md`；`docs/strategy/nextgeo-local-geo-backlog.md`。
- **非目标**：生产部署；博文批量改写；替代 `geo intent` 引擎（仅调整入口时机）。
