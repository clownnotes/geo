# Proposal: 多大模型实时联网探测与Citation信源溯源对账中枢 (Multi-LLM Live Probing Gateway & Citation Footprint Tracer)

## Why (为什么做 / 商业痛点与战略闭环)

1. **从「离线预估/投影」走向「真实联网大模型动态推演」的关键跃迁**：
   - 目前各母版的 AI 声量多带有 `is_projected=True` 标签，依赖离线推演基线；但在商业实战和结案回款中，客户最强烈的诉求是：**“这一刻，让豆包、DeepSeek、Kimi 当场回答我的 30 组搜索意图，看看它们到底有没有提到我，排在第几个，以及底部的参考信源引用了谁！”**
   - 需要统一抽象中国本土主流大模型（字节豆包 Doubao、DeepSeek、月之暗面 Kimi、阿里通义千问、百度文心）的探测与联网检索适配层。

2. **从「仅测声量提及」深入到「Citation 角标信源归因与外发资产对账」**：
   - GEO 的真正护城河不仅是模型文本中出现品牌名字，而是大模型在生成答案时**将我方官方网站、知乎深度解答、技术白皮书作为权威信源进行角标引用（Citation `[1]`、`[2]`）**；
   - 必须建立一套深层 Citation 溯源解析与对账引擎，将模型回答中捕获的参考信源 URL，与我方在 `04_全网分发渠道执行与存活台账` 中外发的资产做全自动关联核验（Hit / Miss），证明我方外发工作的直接商业贡献与 ROI。

3. **双模运行：满足自动化 CI/CD 与现场 Live 交互双重需求**：
   - 既支持配置真实 API Key 进行实盘联网轮询；
   - 又内置高保真沙箱模型（Sandbox Simulation），保证无外部 Key、离线开发与自动化测试套件秒级全绿通过。

---

## What Changes (改动范围)

1. **研发多大模型统一调用网关与 Citation 溯源解析引擎 (`tools/geo/llm_gateway.py` & `tools/geo/probing.py`)**：
   - `LLMGateway`：统一封装豆包（字节火山方舟）、DeepSeek（OpenAI 兼容协议）、Kimi（Moonshot）与沙箱仿真模式，具备并发限速、重试与超时熔断保护；
   - `extract_citations_and_sources(model_response: dict) -> dict`：
     - 正则匹配正文内角标引用（`[1]`、`[2]`、`[[1]]`、`^1` 等）；
     - 解析结构化参考信源列表（URL、标题、域名、发布时间）；
   - `trace_citations_against_ledger(citations: list, project_id: str) -> dict`：
     - 将捕获的参考信源 URL 与项目 `dist_ledger.json`（04 台账）比对，标记外发信源采纳（Hit Rate）、竞对采纳与第三方平台分布；
   - `run_live_probing(project_id: str, models: list = None, query_sample_size: int = 5, use_live: bool = False) -> dict`：
     - 选取项目核心意图 Query（来自 11 号拓扑或 02 评测词库），多模型并发执行探测；
     - 产出真实实测指标：`real_sov_pct`（实测提及率）、`citation_share_pct`（信源采纳率）、`top1_recommendation_rate`（首位推荐率）；
     - 生成规范成果：`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`。

2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo probe` 子命令：
     - `geo probe <project_id> [--models doubao,deepseek,kimi] [--sample 5] [--live]`：对指定项目执行多模型实时联网探测并输出终端高保真对比表格；
     - `geo probe <project_id> --report`：生成并落盘 18 号 Citation 溯源对账报告。

3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/probing/status`：获取当前探测状态与历史对账摘要；
   - `POST /api/projects/{id}/probing/run`：触发并发探测（支持传递 models、sample_size、live 模式）；
   - `GET /api/projects/{id}/probing/report`：获取 18 号报告内容。

4. **Web 管理工作台界面升级 (`web/index.html`)**：
   - 项目向导第五阶段（监控与长效代运营）及顶部快捷栏增加「🤖 多模型实时探测与信源溯源」入口；
   - 模态弹窗提供：模型选择器（豆包/DeepSeek/Kimi/沙箱）、一键探测按钮、多模型提及对比柱状图、Citation 角标溯源对账列表（直观展示哪篇文章被大模型采纳为 `[1]` 号参考信源）。

5. **自动化测试套件 (`tests/test_probing.py`)**：
   - 覆盖网关沙箱与多协议适配、Citation 角标与 URL 解析算法、台账对账比对逻辑、指标统计与 18 号成果落盘。

---

## Capabilities (对外能力)

- **中国本土主流大模型统一标准化探测与调用接口**；
- **大模型正文 Citation 引用角标与溯源 URL 全自动精确解析**；
- **外发分发资产（04 台账）与大模型采纳信源全自动闭环对账（Hit/Miss）**；
- **真实 SOV、信源占有率与首位推荐率实测三维指标体系**；
- **全案第 18 维交付物《大模型实时联网探测与Citation信源溯源对账报告》落盘**。

---

## Impact (影响分析)

- **向下完全兼容**：本模块为纯增量基础设施，可被 `monitor.py` 与 `eval_benchmark.py` 无缝复用；
- **极速沙箱支持**：CI/CD 单测默认使用沙箱仿真，毫秒级通过，零外部网络抖动风险；
- **严格遵循规范**：本地 8088 端口测试，严禁私自推向生产；归档严格交由 Cursor 独立复审后执行。
