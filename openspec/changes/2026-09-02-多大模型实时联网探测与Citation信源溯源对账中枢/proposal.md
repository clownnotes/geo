# Proposal: 多大模型实时联网探测与Citation信源溯源对账中枢 (Multi-LLM Live Probing Gateway & Citation Footprint Tracer)

## Why (为什么做 / 商业痛点与战略闭环)

1. **从「离线预估/投影」走向「真实联网大模型动态推演」的关键跃迁**：
   - 目前各母版的 AI 声量多带有 `is_projected=True` 标签，依赖离线推演基线；但在商业实战和结案回款中，客户最强烈的诉求是：**“这一刻，让豆包、DeepSeek、Kimi 当场回答我的 30 组搜索意图，看看它们到底有没有提到我，排在第几个，以及底部的参考信源引用了谁！”**
   - 需要统一适配中国本土主流大模型（字节豆包 Doubao、DeepSeek、月之暗面 Kimi）的探测调用。
   - *（注：阿里通义千问、百度文心明确列为 Out of Scope，后续按需扩展）*。

2. **从「仅测声量提及」深入到「Citation 角标信源归因与外发资产对账」**：
   - GEO 的真正护城河不仅是模型文本中出现品牌名字，而是大模型在生成答案时**将我方官方网站、知乎深度解答、技术白皮书作为权威信源进行角标引用（Citation `[1]`、`[2]`）**；
   - 研发 Citation 溯源解析与对账引擎，调用 `dist_bot.get_distribution_ledger`，将捕获的参考信源 URL 与项目 `04_全网分发渠道执行与存活台账`（`dist_ledger.json`）自动比对核验（Hit / Miss），证明我方外发资产的直接引流转化与商业贡献。

3. **双模运行：满足自动化 CI/CD 与现场 Live 交互双重需求**：
   - 既支持配置真实 API Key（兼容 `GEO_*` 优先级）进行实盘联网轮询；
   - 又内置高保真沙箱模型（Sandbox Simulation），保证无外部 Key、离线开发与自动化测试套件秒级全绿通过。

---

## What Changes (改动范围与复用策略)

1. **复用既有底层，研发探测与 Citation 溯源解析引擎 (`tools/geo/probing.py`)**：
   - **底层复用**：直接复用 `tools/geo/llm.py` 发起模型调用，支持链式降级读取环境变量（优先 `GEO_*` ➔ 通用名 ➔ `ARK_*`）；
   - **台账复用**：强制调用 `dist_bot.get_distribution_ledger(project_id)` 统一提取发布外链与官网资产；
   - `extract_citations_and_sources(model_response: dict) -> dict`：
     - 双通道解析正文角标（`[1]`、`[[1]]`、`^1`）与尾部参考信源列表；
   - `trace_citations_against_ledger(citations: list, project_id: str) -> dict`：
     - 精准三级对账判定：`exact_hit`（完全吻合）、`domain_hit`（路径匹配）、`third_party_or_competitor`；
   - `run_live_probing(project_id: str, models: list = None, query_sample_size: int = 5, use_live: bool = False) -> dict`：
     - 多模型并发探测，精准测算三大指标：`real_sov_pct`（实测提及率）、`citation_share_pct`（信源角标占有率）、`top1_recommendation_rate`（首位推荐率）；
     - 生成规范成果：`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`。

2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo probe` 子命令：
     - `geo probe <project_id> [--models doubao,deepseek,kimi] [--sample 5] [--live]`：对指定项目执行多模型实时联网探测并输出终端高保真对比表格；
     - `geo probe <project_id> --report`：生成并落盘 18 号 Citation 溯源对账报告。

3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/probing/status`：获取当前探测状态与历史对账摘要；
   - `POST /api/projects/{id}/probing/run`：触发并发探测运行；
   - `GET /api/projects/{id}/probing/report`：获取 18 号报告内容。

4. **Web 管理工作台界面升级 (`web/index.html`)**：
   - 向导 Step 5 新增「🤖 Citation 信源角标溯源对账」独立卡片与按钮，与 06 评测入口明确区分职责；
   - 模态弹窗提供：模型选择器（豆包/DeepSeek/Kimi/沙箱）、一键探测、实测 SOV 对比柱状图、Citation 角标溯源对账流水表（带 `esc()` XSS 防护）。

5. **自动化测试套件 (`tests/test_probing.py`)**：
   - 覆盖沙箱降级、Key 优先级读取、角标提取正则、台账真实比对 Hit、三维指标测算与 18 号成果落盘。

---

## Out of Scope (范围排除声明)

- 阿里通义千问、百度文心 API 适配不在本次范围，后续按需扩展；
- 不替代 06 号宏观评测报告（06 侧重品牌全案综合评分与竞品反差，18 侧重具体外发文章的角标命中与溯源归因）。

---

## Impact (影响分析)

- **纯增量开发**：复用 `llm.py` 与 `dist_bot.py`，不侵入现有数据管道；
- **全自动 CI/CD**：单测默认使用确定性沙箱，毫秒级全绿通过，零网络阻塞；
- **严格遵循规范**：本地 8088 端口测试，严禁私自向生产环境发布；归档严格交由 Cursor 独立复审后执行。
