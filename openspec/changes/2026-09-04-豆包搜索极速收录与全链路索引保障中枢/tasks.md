# Tasks: 豆包搜索极速收录与全链路索引保障中枢 (第 34 维)

## Phase 1: 核心体检与提权引擎 (`tools/geo/doubao_indexer.py`)
- [x] 1.1 创建 `tools/geo/doubao_indexer.py` 基础框架与数据模型（`DoubaoCheckItem`、`DoubaoAuditResult` 等）。
- [x] 1.2 实现 `DoubaoReadinessAuditor`，涵盖 robots.txt、/llms.txt、schema.jsonld、Bytespider 真实到访、头条母池资产与意图覆盖 6 大指标，计算 DRS 指数 (0~100) 与评级。
- [x] 1.3 实现 `DoubaoBoosterPackGenerator`，自动生成 `outputs/doubao_booster_pack/` 四件套（极简快照 HTML、头条/微头条提权文案、高意向问答对 JSON、排障 Checklist）。
- [x] 1.4 实现 `DoubaoLiveVerifier`，联动 30 维实测数据对账高频买家意图词在豆包中的收录与角标命中状态。

## Phase 2: 报告持久化、CLI 与服务端集成
- [x] 2.1 实现标准 34 号公文结案报告《34_豆包大模型搜索极速收录与全链路索引保障报告.md》与 `doubao_index_audit.json` 持久化生成。
- [x] 2.2 在 `tools/geo/cli.py` 注册 `geo doubao-index <project_id> [--audit] [--boost] [--verify] [--dry-run] [--report] [--portal-sync]`。
- [x] 2.3 在 `tools/geo/server.py` 挂载 `GET /api/projects/{id}/doubao-index/audit`、`POST .../boost`、`GET .../report` 接口并集成 Bearer Token 强鉴权。

## Phase 3: 高管交付门户战果反哺与大屏呈现
- [x] 3.1 在 `tools/geo/share.py` 的 `compile_portal_data()` 中接入 `doubao_index_summary` 与 34 号公文映射，严格对齐 `never_run` 优雅降级契约。
- [x] 3.2 在 `web/share.html` 中增设【豆包第一主战模型收录与提权保障态势】高管看板卡片，展示 DRS 指数、Bytespider 抓取通过率与提权加速包状态。

## Phase 4: 全栈单元测试、全库回归与交付闭环
- [x] 4.1 编写专项单元测试 `tests/test_doubao_indexer.py`（8 组单测覆盖体检指标、提权包产物、意图对账、CLI/API 鉴权与门户优雅降级，100% 离线确定性）。
- [x] 4.2 运行全库 180+ 项单元测试，确保 100% 秒绿通过（0 error, 0 failure）。
- [x] 4.3 跨 IDE 审查协同更新 `review-log.md` 审核记录与终审放行。
