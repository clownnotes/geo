## 1. 准备工作

- [x] 1.1 核对 `AGENTS.md` 本地开发端口规范（8088）与生产隔离红线，核对 01~16 资产主文件与别名回退标准。

## 2. 商业验收与结案归档引擎升级 (`tools/geo/acceptance.py`)

- [x] 2.1 锁定 `DELIVERABLES_MANIFEST` 为 01~16 共 16 项主交付报告清单，00 验收单/标书/证书列入衍生附件避免循环依赖。
- [x] 2.2 落实双轨制履约评估架构：保留 6 维合同加权履约分（S1~S6），新增 16 维交付物齐套率核验。
- [x] 2.3 升级 `generate_acceptance_report`，在《00_GEO商业交付验收结案确认单.md》中结构化渲染 16 维资产矩阵与验收标准，并持久化 `acceptance_summary.json`。
- [x] 2.4 完善 `export_project_archive_zip` 打包算法，白名单打包交付资产，严格排除 `roi_settings.json` 等内部私密配置。

## 3. 甲方专属免密只读门户升级 (`tools/geo/share.py`, `tools/geo/server.py`, `web/share.html`)

- [x] 3.1 更新 `tools/geo/share.py`：落盘优先读取避免请求时重跑推演，真实绑定 `immunity_score`、`overall_authority_score`、`rag_readiness_score` 等指标。
- [x] 3.2 更新 `tools/geo/server.py`：保留原 `/api/share/{token}/download-zip`（兼容 `/archive`），新增 `/api/share/{token}/file?key={key}` 严格白名单与防穿透只读端点。
- [x] 3.3 更新 `web/share.html`：基线 7 Tab 保持稳定，新增 Tab 8「🛡️ 核心黑科技与攻防安全中枢」与 Tab 9「🏛️ 商业交付结案单」，修复内部缺失的闭合括号。

## 4. 自动化测试与母版全量跑批

- [x] 4.1 新建 `tests/test_acceptance.py`，覆盖 16 维清单校验、双轨履约评分、ZIP 敏感排查与四大母版全绿验证。
- [x] 4.2 对四大行业母版（徐州轩辕、B2B重工、本地律所、连锁餐饮）全量跑批生成最新 00 结案确认单与 ZIP 包，16 维齐套率全部达到 100%。
- [x] 4.3 闭环 Cursor 提出的全部 4 处 P0 与 6 处 P1 审查意见，提请跨 IDE 最终复审归档。


