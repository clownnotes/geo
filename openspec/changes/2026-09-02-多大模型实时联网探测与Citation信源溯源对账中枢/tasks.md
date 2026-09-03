## 1. 准备工作

- [ ] 1.1 核对 `AGENTS.md` 本地开发端口规范（8088）与生产隔离红线，锁定 API Key 链式降级查找规范（`GEO_*` ➔ 通用名 ➔ `ARK_*`）。

## 2. 研发多模型适配与 Citation 溯源解析引擎 (`tools/geo/probing.py`)

- [ ] 2.1 复用 `tools/geo/llm.py` 底层调用能力，实现多模型请求调度与确定性高保真 `SandboxSimulator`（单测默认沙箱）。
- [ ] 2.2 编写 `extract_citations_and_sources`，实现正文角标（`[1]`、`[[1]]`、`^1`）与尾部参考信源列表的双通道结构化解析。
- [ ] 2.3 强制复用 `dist_bot.get_distribution_ledger(project_id)`，编写 `trace_citations_against_ledger`，落实 Exact Hit 与严密 Domain Hit 判定逻辑。
- [ ] 2.4 编写 `run_live_probing`，落实明确分母口径的三大指标计算（实测 SOV、Citation Share、Top-1 Rate），规范生成 `outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo probe <project_id> [--models M] [--sample N] [--live] [--report]` 子命令。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/probing/status`、`/api/projects/{id}/probing/run` 与 `/api/projects/{id}/probing/report`（管理端鉴权拦截）。

## 4. Web 管理控制台实时探测工作台升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「🤖 Citation 信源角标溯源对账」独立卡片与入口（与 06 评测明确区分功能）。
- [ ] 4.2 开发全屏模态窗口 `probing-modal`，实现模型选择、采样滑块、三大 KPI 卡片与多模型横向对比。
- [ ] 4.3 渲染 Citation 角标溯源对账表格（URL 与标题输出强制经过 `esc()` XSS 防护）及 18 号报告在线预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_probing.py`，全量覆盖沙箱降级、Key 优先级读取、角标提取正则、真实台账 Exact Hit 比对、指标公式与 18 号报告生成。
- [ ] 5.2 运行全库单元测试，确保 100% 通过。
- [ ] 5.3 在 `review-log.md` 中记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
