# 提案：大模型商业推荐因果归因与信源边际贡献度量化审计中枢 (第 23 维核心交付)

## 1. 需求背景与痛点 (Why)

在完成了第 21 维（商业心智渗透率与等效广告价值量化）和第 22 维（跨模型 RAG 混合检索召回与重排序挤占演习）之后，GEO 代运营体系已经构建了从宏观商业价值到微观切片挤占的完整链条。

然而，企业客户与管理决策层在深入落地时必然追问终极问题：
1. **因果归因黑盒**：“我们在全网分发了数十篇新闻、专栏、官网与问答，大模型在推荐我们品牌时，**到底是哪一篇内容或哪几个外链起到了决定性的因果支撑**？”
2. **预算分配盲目**：“如果某些渠道内容对大模型的最终推荐毫无因果贡献（边际价值为 0），我们为什么还要持续投入成本维护？哪些信源是绝对不能丢的‘核心基石’？”
3. **单点故障风险**：“若当前推荐高度依赖单一信源（如某篇高权重专栏），一旦该文章被下架、降权或被竞品针对性反超，大模型推荐是否会瞬间雪崩（单点脆弱性）？”

传统广告归因（Multi-Touch Attribution）依赖 Cookie 与点击流，在大模型生成式时代完全失效。本项目需要研发**基于反事实因果推断（Counterfactual Intervention）与 Shapley 近似代理边际贡献度理论（Shapley Proxy / Leave-One-Out Ablation）**的“大模型商业推荐因果归因与信源边际贡献度量化审计中枢”，为企业建立首个**生成式 AI 信源因果贡献审计大盘**。

---

## 2. 改动范围与对外能力 (What & Capabilities)

### 核心能力 1：信源反事实消融实验引擎 (Counterfactual Ablation Engine)
- 构建可观测我方信源切片全集 $S$（竞品切片消融属于 Out of Scope），测算基线商业意图推荐得分 $P_{\text{base}}(Q, S)$；
- 逐一执行反事实抽离（Leave-One-Out Ablation），量化切片抽离前后的决策跌幅 $\Delta P(q, s_i)$；
- 聚合推导各信源切片的边际因果贡献率 $MCR(s_i)$（反事实 LOO 边际贡献代理，严禁夸大为全联盟理论 Shapley 值）。

### 核心能力 2：品牌因果鲁棒性与单点故障预警 (CRI & SPOF Auditor)
- 计算最坏情况留存率，输出品牌因果鲁棒性指数（Causal Robustness Index, CRI）；
- 提供三档评级（`high_resilience` / `moderate_dependency` / `fragile_single_point`）；
- 自动标记单点故障风险（`critical_spof`），指明最脆弱的信源单点。

### 核心能力 3：信源角色三档分类与预算优化建议 (Source Role Taxonomy)
- 自动划分为：👑 核心基石（`cornerstone`）、⚡ 协同催化（`catalyst`）、🥀 冗余低效（`redundant`）；
- 输出信源 ROI 投入调整指南，指导企业高管精准削减无效分发支出。

### 核心能力 4：信源边际归因优化三件套与 23 号公文报告物理落盘
- 自动在 `outputs/attribution_optimization_pack/` 下物理落盘 3 份落地加固文案：
  1. `01_核心基石信源护城河死保加固清单.md`
  2. `02_低边际贡献信源ROI预算缩减与重构建议.md`
  3. `03_单点故障因果容灾与多渠道替补方案.md`
- 规范生成 `outputs/23_大模型商业推荐因果归因与信源边际贡献度量化审计报告.md` 与 `outputs/causal_attribution_audit.json`。

### 核心能力 5：多端贯通（CLI / 后端 API / Web 控制台）
- CLI 注册 `geo attribution <project_id> [--models M] [--live] [--optimize] [--report]`；
- 后端提供状态查询、因果消融演练、优化包生成与报告读取接口（严格 Bearer 鉴权，无报告返回 404）；
- Web 控制台在向导 Step 5 和 Header 增加 23 号入口，开发 `causal-attr-modal` 全屏模态窗口，全量 DOM 渲染经 `escapeHtmlSafe()` 转义防御 XSS。

---

## 3. 边界与 Out of Scope 说明

1. **算力与算法边界**：绝不下载或在本地部署运行参数量达数十 GB 的因果神经网络，不进行模型内参梯度反向推导。沙箱基于可观测切片池与 Top-3 留存加权推荐概率模型进行确定性因果反事实推演；
2. **理论话术边界**：算法定位为**反事实 LOO 边际贡献度（Shapley 近似代理，Shapley Proxy）**，报告与对外文案严格以此为准，不宣传全联盟 $2^{|S|}$ 指数级全量 Shapley 值；竞品切片反事实消融属于 Out of Scope；
3. **`--live` 语义与预算界定**：仅通过 `tools.geo.llm.call_model_raw` 在线调用真实大模型，对全量基线及 MCR 最高的前 2 篇核心切片抽离状态进行在线真实采样裁决（API 调用上限严格锁死为 3 次），安全提取 `content` 字典内容，按 70% 沙箱因果分 + 30% 在线 Judge 裁决分融合更新，异常时平滑回退沙箱打分并置 `is_live_judged = False`；
4. **资产隔离**：落盘文件严格为 `causal_attribution_audit.json`，与 12 号 `rag_chunks_diagnostic.json` 及 22 号 `rag_rerank_simulation.json` 物理隔离，杜绝覆盖冲突。
