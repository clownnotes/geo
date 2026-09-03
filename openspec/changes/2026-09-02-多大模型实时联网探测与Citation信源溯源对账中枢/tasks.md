## 1. 准备工作

- [ ] 1.1 核对 `AGENTS.md` 本地开发端口规范（8088）与生产隔离红线，梳理主流大模型 Citation 返回结构与正则模式。

## 2. 研发多模型适配网关与 Citation 溯源解析引擎 (`tools/geo/llm_gateway.py`, `tools/geo/probing.py`)

- [ ] 2.1 编写 `tools/geo/llm_gateway.py`，实现 `LLMGateway` 与 `SandboxSimulator`，支持豆包、DeepSeek、Kimi 与高保真沙箱双模切换。
- [ ] 2.2 编写 `extract_citations_and_sources`，实现正文角标（`[1]`、`[[1]]`、`^1`）与尾部参考信源列表的结构化解析。
- [ ] 2.3 编写 `trace_citations_against_ledger`，实现捕获信源与项目 `dist_ledger.json`（04 台账）的全自动对账与 Hit 标记。
- [ ] 2.4 编写 `run_live_probing`，实现多模型并发探测、三大核心指标（Real SOV、Citation Share、Top-1 Rate）测算，并输出 `outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo probe <project_id> [--models M] [--sample N] [--live] [--report]` 子命令。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/probing/status`、`/api/projects/{id}/probing/run` 与 `/api/projects/{id}/probing/report`（管理端鉴权拦截）。

## 4. Web 管理控制台实时探测工作台升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段（监控与长效代运营）及顶部快捷栏增加「🤖 多模型实时探测」入口。
- [ ] 4.2 开发全屏模态窗口 `probing-modal`，实现模型多选、采样滑块、三大 KPI 卡片与多模型横向对比。
- [ ] 4.3 渲染 Citation 角标溯源对账表格（高亮显示 04 台账命中文章与角标序号）及 18 号报告在线预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_probing.py`，全量覆盖沙箱降级、角标正则解析、台账对账比对、实测指标公式与 18 号报告生成。
- [ ] 5.2 运行全库单元测试，确保 100% 通过。
- [ ] 5.3 在 `review-log.md` 中记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
