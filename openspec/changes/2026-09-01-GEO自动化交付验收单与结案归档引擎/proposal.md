# Proposal: GEO 自动化交付验收单与结案归档引擎 (Acceptance Report & Delivery Archive Engine)

## Why (为什么做 / 商业与业务痛点)

1. **项目结案回款的最后 1 公里（Contract Sign-off & Final Payment）**：
   - 目前 GEO 交付物分布在 5 个阶段中（诊断报告、底座补丁、语料库、分发台账、监测周报、ROI 测算）；
   - 在向客户发起尾款结案申请时，商务和顾问需要一份**具备法务与公章签署格式的标准《GEO 商业交付验收结案确认单》**，明确列出 6 大合同履约条款达成情况（如 SOV 达成率、外网收录数、底座上线情况）；
   - 缺少一键生成盖章级结案单（支持一键打印 PDF）与一键全量打包离线归档（ZIP）的自动化工具。
2. **合同履约率量化评分（Fulfillment Score 0~100%）**：
   - 将 6 维交付成果（S1~S5 及 ROI）自动计算为清晰明确的履约率百分比（如 98.5% ✅ 符合全额回款验收标准），消除甲乙双方结案争议。
3. **全套交付物一键离线 ZIP 归档包**：
   - 方便甲方技术团队与法务归档，将全套 10+ 份交付物（含 Markdown、HTML、SVG 图表、JSON-LD 与 README）一键打包下载。

---

## What Changes (改动范围)

1. **研发交付验收与归档核心引擎 (`tools/geo/acceptance.py`)**：
   - `generate_acceptance_report(project_id)`：汇总全流程交付物生成《00_GEO商业交付验收结案确认单.md》；
   - `calculate_fulfillment_score(project_id)`：计算 6 维合同履约达成率（0~100%）与条款达标打勾项；
   - `export_project_archive_zip(project_id)`：一键打包全套交付物为 ZIP 归档包。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo signoff <project_id>` 与 `geo pack <project_id>`。
3. **后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)**：
   - `GET /api/projects/{id}/acceptance/data`
   - `GET /api/projects/{id}/acceptance/print`（美化版公章结案单打印页）
   - `GET /api/projects/{id}/acceptance/download-zip`（ZIP 归档包流式下载）
   - 在 `tools/geo/share.py` 门户中增加结案验收与一键下载能力。
4. **Web 管理工作台与专属交付门户升级 (`web/index.html` & `web/share.html`)**：
   - Step 5 及顶部工具栏增加「📜 交付结案验收单」与「📦 下载全套归档包」按钮；
   - 专属交付门户（`web/share.html`）提供一键查看结案单与全套成果 ZIP 下载。
5. **SOP 知识库更新 (`docs/sop/delivery-sop.md` & `05-monitor-sop.md`)**：
   - 规范化结案验收与回款流程。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/acceptance/data`
- `GET /api/projects/{id}/acceptance/print`
- `GET /api/projects/{id}/acceptance/download-zip`
- CLI: `python3 -m tools.geo signoff <project_id>`
- CLI: `python3 -m tools.geo pack <project_id>`

---

## Impact (影响分析)

- **完全向下兼容**：结案单文件输出为 `outputs/00_GEO商业交付验收结案确认单.md`，ZIP 包保存于 `outputs/`；
- **回款效率显著提升**：标准化交付结案确认单极大加速企业客户内部审批与财务放款。
