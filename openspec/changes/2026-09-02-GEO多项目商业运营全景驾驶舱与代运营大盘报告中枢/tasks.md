## 1. 准备工作

- [x] 1.1 核对 `AGENTS.md` 本地开发端口规范（8088）与生产隔离红线，核验四大母版实盘 JSON 存在性。

## 2. 研发多项目商业运营聚合引擎 (`tools/geo/portfolio.py`)

- [x] 2.1 编写 `scan_managed_projects`（过滤 `_template` 与非法目录）与 `get_portfolio_summary`，落实设计文档中「实盘字段映射表」与「组合投资回报率 Portfolio ROI%」严谨公式。
- [x] 2.2 落实动态风险分级评估模型（`normal` / `warning` / `danger`），区分 `raw_sov` 与投影值，徐州项目因 89.3 分和续约 64 分精准判定为 `warning`，其余三大母版判定为 `normal`。
- [x] 2.3 编写 `run_portfolio_health_patrol`，仅执行只读健康扫描与红黑榜生成（零副作用、不重跑 monitor 写库、不重发 Webhook）。
- [x] 2.4 编写 `generate_portfolio_executive_report`，自动生成《GEO代运营全域多项目执行与商业回报大盘报告.md》，收敛输出至 `reports/` 目录。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [x] 3.1 在 `tools/geo/cli.py` 中注册 `geo portfolio [--patrol] [--report]` 子命令并实现终端高保真表格输出。
- [x] 3.2 在 `tools/geo/server.py` 中挂载 `/api/portfolio/summary`、`/api/portfolio/patrol`、`/api/portfolio/report` 端点（挂载管理鉴权校验）。

## 4. Web 管理控制台驾驶舱界面升级 (`web/index.html`)

- [x] 4.1 在首页顶部指标条中，将原占位硬编码卡片「平均 AI 声量提升」平滑替换为「全域年化总价值」与「组合投资回报率」，保持 7 列网格布局。
- [x] 4.2 在顶部导航栏新增「📊 全域大盘驾驶舱」按钮，实现多项目横向对比矩阵、风险徽章与快速直达项目工作台。
- [x] 4.3 支持在大盘界面中一键触发全域只读健康巡检与一键在线预览/下载大盘执行月报。

## 5. 自动化测试与跨 IDE 联合审查

- [x] 5.1 编写 `tests/test_portfolio.py`，全量覆盖目录过滤、财务加总、组合 ROI%、风险判定逻辑与 API 端点。
- [x] 5.2 本地运行全库单元测试，确保 100% 通过。
- [ ] 5.3 在 `review-log.md` 中记录自评与对账细节，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
