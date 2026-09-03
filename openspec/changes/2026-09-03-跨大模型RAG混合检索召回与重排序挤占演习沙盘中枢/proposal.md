# Proposal: 跨大模型 RAG 混合检索召回与重排序挤占演习沙盘中枢 (Multi-LLM RAG Hybrid Retrieval & Rerank Competition Simulator)

## Why (为什么做 / 破解大模型生成式搜索最深层物理黑盒)

1. **大模型生成式搜索（GEO）的最深层物理底层：RAG 重排序挤占机制**
   - 现有的各大主流商用大模型（豆包、DeepSeek、Kimi、腾讯元宝）在进行联网生成时，其真实底层调用链是：
     $$\text{用户 Query} \longrightarrow \text{粗排多路检索 (Dense 向量 + BM25 稀疏)} \longrightarrow \text{重排序模型 (Cross-Encoder Reranker)} \longrightarrow \text{Top-3/Top-5 黄金上下文} \longrightarrow \text{生成回答与 Citation}$$
   - **痛点**：即便企业生产了优质内容，如果该切片在 Reranker 交叉编码精排阶段被竞品或第三方高权重资讯“挤出黄金 Top-3 窗口”，大模型在最终推理时就**根本“看不到”该切片**，从而导致 Citation 角标归零、推荐席位丧失。

2. **从「黑盒猜测」到「可量化、可演练、可反制的重排演习沙盘」**：
   - 本中枢模拟主流 Reranker（如 BAAI/bge-reranker-v2-m3、Cohere Rerank、Qwen-Rerank）的注意力重排机制；
   - 引入核心量化指标：**重排上下文穿透率 (Context Penetration Rate, CPR %)** 与 **竞品排挤阻断率 (Competitor Ousting Rate, COR %)**；
   - 仿真演习企业切片 vs 竞品切片在 Top-3 窗口中的排挤概率，让技术团队在上线前就能提前发现重排序盲区。

3. **赋能高权威语料的定向语义重构与护城河加固**：
   - 自动生成面向开发运营团队的 **《跨大模型 RAG 混合检索召回与重排序挤占演习报告.md》** 与 **`outputs/rerank_reinforcement_pack/`** 强化包（包含 Dense 语义锚点对齐清单、BM25 稀疏关键词注入切片、上下文穿透防御文案），形成物理层面的不可撼动壁垒。

---

## What Changes (改动范围与复用策略)

1. **研发 RAG 混合检索与重排演习引擎 (`tools/geo/rerank_simulator.py`)**：
   - **底层复用**：强制直接复用 `tools/geo/llm.py`（底层模型调用网关与 Key 链式查找）、`tools/geo/probing.py`（Citation 解析与 `is_ledger_asset_eligible` 外链校验），强制调用 `tools.geo.dist_bot.get_distribution_ledger` 读取存活外链；
   - **真实档案读取**：直接读取 `projects/{id}/outputs/factual_anchors.json`（回退 `load_project_config`），绝无虚构模块；
   - **Query 来源锁定**：优先读取 `projects/{id}/outputs/keywords_intent_matrix.json` 的顶层主字段 `flat_queries`（字符串列表），次选 `tiers[...].queries`，严禁写死特定地域或品牌；
   - **数学模型与算法**：实现 Dense 语义相似度、BM25 词频评分、RRF 倒数排名融合与 Cross-Encoder Rerank 综合精排；
   - **重排强化包 (`outputs/rerank_reinforcement_pack/`)**：生成 3 份针对性重排强化落地成果物；
   - **标准公文落盘**：生成 `outputs/22_跨大模型RAG混合检索召回与重排序挤占演习报告.md` 与 `rag_rerank_simulation.json`（自适应话术与免责声明）。

2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo rerank <project_id> [--models M] [--live] [--reinforce] [--report]` 子命令，输出 ANSI 终端重排序挤占沙盘流水。

3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/rerank/status`：获取当前重排穿透率 CPR、竞品排挤率 COR 与 Top-3 命中大盘；
   - `POST /api/projects/{id}/rerank/simulate`：触发全域 RAG 检索与重排序挤占仿真演习；
   - `POST /api/projects/{id}/rerank/reinforce`：一键生成重排序语义强化包；
   - `GET /api/projects/{id}/rerank/report`：获取 22 号公文报告（无文件严格返回 404，禁止自动后台计算）。

4. **Web 管理工作台升级 (`web/index.html`)**：
   - 向导 Step 5 新增「🔀 RAG 重排演习沙盘 (22)」独立卡片与操作入口，顶部 Header 增加入口；
   - 开发全屏模态窗口 `rerank-sim-modal`：展示 CPR 穿透率仪表盘、COR 排挤率卡片、Top-3 窗口挤占矩阵与报告预览（全量 `escapeHtmlSafe` 转义）。

5. **自动化测试套件 (`tests/test_rerank_simulator.py`)**：
   - 覆盖固定数值夹具强断言、沙箱仿真、强化包落盘、自适应话术及 API 鉴权/404 语义。

---

## Out of Scope (范围排除声明)

- 本中枢模拟主流 Reranker 的交叉注意力与打分机制，不直接下载部署多吉字节的本地巨型权重模型，以确保 CI/CD 与本地环境秒级轻量高效运行。

---

## Impact (影响分析)

- **纯增量开发**：复用既有模块，不破坏 01~21 号任何既有功能与数据；
- **最高协同协议遵循**：本地测试锁定 8088 端口，严禁推向生产服务器；**归档严格留给 Cursor 在独立终审通过后执行！**
