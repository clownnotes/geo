# Proposal: 大模型爬虫抓取仿真器与 RAG 分块检索命中诊断中枢 (LLM Crawler Simulator & RAG Chunking Retrieval Diagnostic Engine)

## Why (为什么做 / 业务背景与痛点)

1. **大模型爬虫抓取可见度黑盒**：
   - 客户常常怀疑自己的官网或分发文章能否被各大模型蜘蛛（Bytespider / 百度蜘蛛 / DeepSeek）正常抓取，是否存在 JS 阻塞或 Clean Markdown 乱码；
2. **缺乏 RAG 语义分块（Chunking）切片诊断**：
   - 大模型在检索（RAG）企业语料时，会先将文章按照 300~500 字切块。如果核心差异化承诺（如 365天质保、阶段付款、蔡司三坐标检测）被跨块截断，大模型将无法完整召回；
3. **缺少交付级 RAG 检索命中度体检报告**：
   - 需要对企业官网及生成的 03 语料库进行自动化分块切片，逐块评分（品牌实体命中、数据量化命中、FAQ 结构命中），生成可视化的仿真诊断报告。

---

## What Changes (改动范围)

1. **爬虫抓取与 RAG 诊断核心引擎 (`tools/geo/crawler.py` / `rag_diag.py`)**：
   - `simulate_crawler_fetch(url: str, spider_type: str = "bytespider") -> dict`：模拟字节跳动 Bytespider、百度蜘蛛、DeepSeek 爬虫进行 HTTP 抓取与 Clean Markdown 提纯；
   - `diagnose_rag_chunks(project_id: str, text_or_file: str = None) -> dict`：按标准 400 Token 窗口与 50 Token 重叠进行语义切块，逐块计算实体命中率、量化参数命中率与普林斯顿 9 因子符合度；
   - `render_rag_diagnostic_markdown(project_id: str, diag: dict) -> str`：渲染生成 `outputs/12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md` 与 `outputs/rag_chunks_diagnostic.json`；
2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
   - `geo crawl <url> [--spider bytespider|baidu|deepseek]`
   - `geo rag-diag <pid> [--file <path>]`
3. **服务端 API 与 Web 端大一统集成 (`tools/geo/server.py`, `web/index.html`)**：
   - 挂载 `POST /api/projects/{id}/crawler/simulate` 与 `GET/POST /api/projects/{id}/rag/diagnose`；
   - Web 端 Step 1 / Step 3 增加「🕷️ 大模型爬虫与 RAG 诊断」弹窗。

---

## Capabilities (对外能力)

- **多模型爬虫仿真抓取**：真实还原主流爬虫眼中的网页结构；
- **RAG 切片语义透视**：可视化每一个 Chunk 的召回价值；
- **交付级诊断报告**：为客户出具技术级抓取与分块体检结论。

---

## Impact (影响分析)

- 强化 GEO 技术深度背书，为商业客户提供直观的大模型底层抓取与分块召回体检。

