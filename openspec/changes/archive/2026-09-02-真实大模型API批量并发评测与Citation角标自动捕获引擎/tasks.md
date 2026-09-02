## 1. 编写真实大模型 API 批量并发评测核心 (`tools/geo/evaluator.py`)

- [x] 1.1 实现统一 OpenAI 协议适配器与环境 Key 检测机制（支持豆包、DeepSeek 等真实 API，无 Key 优雅降级）。
- [x] 1.2 实现 `extract_citations_and_sov(response_text, company_info)`，精准提取品牌命中、首推排名与 Citation 角标。
- [x] 1.3 实现基于 `ThreadPoolExecutor` 的 45 词批量并发调度器与结果聚合汇总。
- [x] 1.4 输出 `06_大模型真实API评测与Citation捕获报告.json` 与 `.md` 结构化报告。

## 2. CLI 与 Web 服务端集成 (`tools/geo/cli.py` & `server.py`)

- [x] 2.1 在 `tools/geo/cli.py` 中新增 `geo eval` 子命令，支持并发跑批评测。
- [x] 2.2 在 `tools/geo/server.py` 中增加 `/api/projects/{id}/eval/run` 与 `/api/projects/{id}/eval/report` 接口。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 运行 `geo eval xuzhou_xuanyuan --limit 10` 与母版评测，验证 SOV、Citation 捕获与报告落盘完整。
- [x] 3.2 严格遵守项目规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录审查结论。

