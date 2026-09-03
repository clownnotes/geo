## 1. 准备工作与规范对齐

- [ ] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定 `tools/geo/llm.py` 底座复用、`tools/geo/dist_bot.py` 的 `get_distribution_ledger`、`tools/geo/probing.py` 的 `is_ledger_asset_eligible` 与 `projects/{id}/outputs/factual_anchors.json` 真实档案读取规则（杜绝虚构模块路径；锁定 Query 采样自 `keywords_intent_matrix.json` 的 `flat_queries` 真实字段而非写死特定品牌；严格隔离 12 号诊断与 22 号演习文件）。

## 2. 研发 RAG 混合检索与重排演习引擎 (`tools/geo/rerank_simulator.py`)

- [ ] 2.1 构建确定性 RAG 检索沙箱 `RerankSandboxSimulator`（支持构建我方真实切片 03/04/anchors 与竞品干扰切片池 14/competitor_gap，模拟两阶段检索重排）。
- [ ] 2.2 实现阶段 1 粗排打分模型：Dense 语义相似度 `score_dense_similarity`（$\epsilon=1e-9$）、Sparse 词频 `score_sparse_bm25`（$k_1=1.2, b=0.75, \text{avgdl}=256$）与 RRF 倒数排位融合 `calculate_rrf_rankings`（常数 $k=60$，截断取 Top-10 候选）。
- [ ] 2.3 实现阶段 2 Cross-Encoder 重排算法 `score_cross_encoder_rerank`（公式权重 45% Dense + 35% Sparse + 20% AuthBonus），截取 Top-3 黄金上下文窗口。
- [ ] 2.4 实现穿透率 `calculate_cpr` 与竞品排挤率 `calculate_cor`（操作定义：被阻挡在 Top-3 之外的竞品人次 / 进入粗排候选的竞品总人次），完成三档评级判定（`full_penetration` / `partial_contention` / `severe_dropout`）。
- [ ] 2.5 实现重排序语义强化包生成器 `generate_rerank_reinforcement_pack`（生成 `outputs/rerank_reinforcement_pack/` 下 3 份强化文案），并规范落盘 `outputs/22_跨大模型RAG混合检索召回与重排序挤占演习报告.md`（自适应话术与免责声明）与 `outputs/rag_rerank_simulation.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo rerank <project_id> [--models M] [--live] [--reinforce] [--report]` 子命令并输出 ANSI 终端重排演习沙盘。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/rerank/status`、`/api/projects/{id}/rerank/simulate`、`/api/projects/{id}/rerank/reinforce` 与 `/api/projects/{id}/rerank/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404，禁止自动后台计算）。

## 4. Web 控制台 RAG 重排演习沙盘升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「🔀 RAG 重排演习沙盘 (22)」独立卡片与操作入口，顶部 Header 增加入口。
- [ ] 4.2 开发全屏模态窗口 `rerank-sim-modal`，展示 CPR 黄金穿透率大字仪表盘、COR 竞品排挤率卡片、Top-3 窗口挤占矩阵表与报告在线预览。
- [ ] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御，并支持 22 号报告在线 Markdown 预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_rerank_simulator.py`，全量覆盖：
  - 固定数值夹具 1：$N_{\text{my}}=12, T_{\text{slots}}=15 \implies CPR = 80.0\%$（`full_penetration` 🟢 全面穿透）；
  - 固定数值夹具 2：$N_{\text{my}}=10, T_{\text{slots}}=15 \implies CPR = 66.7\%$（`partial_contention` 🟡 中度挤占）；
  - 固定数值夹具 3：$N_{\text{my}}=7, T_{\text{slots}}=15 \implies CPR = 46.7\%$（`severe_dropout` 🔴 严重滑落）；
  - 固定数值夹具 4 (Cross-Encoder 精排得分)：$S_{\text{dense}}=0.8, S_{\text{sparse}}=0.6, \text{AuthBonus}=1.0 \implies S_{\text{rerank}}=77.0$ 分；
  - 固定数值夹具 5 (COR 竞品排挤率闭环)：$N_{\text{ousted}}=8, N_{\text{comp\_candidates}}=10 \implies COR = 80.0\%$；
  - 断言 `_sample_business_queries` 优先采纳 `keywords_intent_matrix.json` 的 `flat_queries` 真实原句；
  - 断言 `outputs/rerank_reinforcement_pack/` 下 3 份强化文案物理存在；
  - 断言自适应报告话术（沙箱免责 + 技术演练推演声明；全 live 包含实盘审计声明）；
  - 断言 API 鉴权拦截（未授权 401）与 `/report` 无文件返回 404。
- [ ] 5.2 运行全库单元测试，确保 100% 通过（当前已有 86 组，新增后将达 92+ 组单测全绿）。
- [ ] 5.3 在 `review-log.md` 记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
