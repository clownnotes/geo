## 1. 编写爬虫抓取仿真与 RAG 语义分块诊断核心 (`tools/geo/crawler.py` / `rag_diag.py`)

- [x] 1.1 实现 `simulate_crawler_fetch(url: str, spider_type: str = "bytespider")`，支持 Bytespider / 百度蜘蛛 / DeepSeek 真实 UA 抓取与 Clean Markdown 提纯。
- [x] 1.2 实现 `diagnose_rag_chunks(project_id: str, text_or_file: str = None)`，按 400 Token / 50 Token 重叠切块并对实体、量化指标、表格、FAQ 逐块打分。
- [x] 1.3 实现 `render_rag_diagnostic_markdown(project_id: str, diag: dict)`，输出 `outputs/12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md` 与 `outputs/rag_chunks_diagnostic.json`。

## 2. CLI、服务端与 Web 端大一统集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，新增 `crawl` 与 `rag-diag` 子命令。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `/api/projects/{id}/crawler/simulate` 与 `/api/projects/{id}/rag/diagnose`。
- [x] 2.3 更新 `web/index.html`，在 Step 1 / Step 3 接入「🕷️ 爬虫仿真与 RAG 切片诊断」弹窗与可视化看板。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 编写 `tests/test_crawler_rag_diag.py` 单元测试，覆盖爬虫仿真、分块切片算法与评分准确性。
- [x] 3.2 针对 4 大母版项目生成 RAG 诊断报告，本地验证通过并 Git 推送。


