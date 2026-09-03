## 1. 准备工作与规范对齐

- [x] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定 `tools/geo/llm.py` 底座复用、`tools/geo/dist_bot.py` 的 `get_distribution_ledger`、`tools/geo/probing.py` 的 `is_ledger_asset_eligible`、`projects/{id}/outputs/factual_anchors.json` 真实档案读取规则，以及复用 `tools.geo.rerank_simulator.score_dense_similarity`（杜绝维护多套相似度；锁定 Query 采样自 `keywords_intent_matrix.json` 的 `flat_queries` 真实字段；严格隔离 12 号/22 号与 23 号输出文件）。

## 2. 研发因果归因与信源边际贡献度审计引擎 (`tools/geo/causal_auditor.py`)

- [x] 2.1 构建防饱和 Top-3 留存加权推荐置信度模型 `score_brand_recommendation_confidence`（$0.60 v_{(1)} + 0.25 v_{(2)} + 0.15 v_{(3)}$，权重表 anchors 1.0 / 03 语料 0.8 / 台账落地页 0.7 / 保底 0.5）。
- [x] 2.2 实现信源反事实消融推导算法：逐一切片 Leave-One-Out 抽离、边际因果跌幅 $\Delta P(s_i)$ 与信源边际因果贡献率 $MCR(s_i)$（Shapley Proxy）计算。
- [x] 2.3 实现品牌因果鲁棒性指数 $CRI$ 与三档评级判定（`high_resilience` / `moderate_dependency` / `fragile_single_point`），以及单点故障 `critical_spof` 预警标记。
- [x] 2.4 实现信源角色三档分类逻辑（👑 `cornerstone` / ⚡ `catalyst` / 🥀 `redundant`）、四维雷达量化指标计算及优化包生成器 `generate_attribution_optimization_pack`（在 `outputs/attribution_optimization_pack/` 下物理落盘 3 份加固文件）。
- [x] 2.5 实现公文报告生成与独立落盘：落盘 `outputs/23_大模型商业推荐因果归因与信源边际贡献度量化审计报告.md`（含反事实 LOO Shapley 近似代理声明、自适应沙箱推演与 live 实盘审计声明）与 `outputs/causal_attribution_audit.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [x] 3.1 在 `tools/geo/cli.py` 中注册 `geo attribution <project_id> [--models M] [--live] [--optimize] [--report]` 子命令并输出 ANSI 终端因果归因审计大盘。
- [x] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/attribution/status`、`/api/projects/{id}/attribution/audit`、`/api/projects/{id}/attribution/optimize` 与 `/api/projects/{id}/attribution/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404，禁止自动后台计算）。

## 4. Web 控制台因果归因审计沙盘升级 (`web/index.html`)

- [x] 4.1 在向导第五阶段新增「🧬 商业推荐因果归因与信源审计 (23)」独立卡片与操作入口，顶部 Header 增加入口。
- [x] 4.2 开发全屏模态窗口 `causal-attr-modal`，展示 CRI 鲁棒性仪表盘、基石/催化/冗余分类标签、信源 MCR 边际贡献排行表与报告在线 Markdown 预览。
- [x] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御。

## 5. 自动化测试与跨 IDE 联合审查

- [x] 5.1 编写 `tests/test_causal_auditor.py`，全量覆盖：
  - 固定数值夹具 1：$P_{\text{base}}=80.0, P_{\text{min}}=64.0 \implies CRI = 80.0\%$ (`high_resilience` 🟢 高度抗震)；
  - 固定数值夹具 2：$P_{\text{base}}=80.0, P_{\text{min}}=48.0 \implies CRI = 60.0\%$ (`moderate_dependency` 🟡 中度依赖)；
  - 固定数值夹具 3：$P_{\text{base}}=80.0, P_{\text{min}}=32.0 \implies CRI = 40.0\%$ (`fragile_single_point` 🔴 脆弱单点)；
  - 固定数值夹具 4 (MCR 边际贡献率与角色分类)：$\Delta_1=30, \Delta_2=15, \Delta_3=5 \implies MCR_1=60.0\% (\text{cornerstone}), MCR_2=30.0\% (\text{cornerstone}), MCR_3=10.0\% (\text{catalyst})$；
  - 固定数值夹具 5 (单点故障归因)：$MCR \ge 40.0\%$ 且抽离后得分 $< 50.0 \implies \text{标记 } \texttt{critical\_spof = True}$；
  - 固定数值夹具 6 (Top-3 留存加权推荐概率)：$v_{(1)}=1.0, v_{(2)}=0.8, v_{(3)}=0.6 \implies P = 89.0$ 分；
  - 断言 `_sample_business_queries` 优先采纳 `keywords_intent_matrix.json` 的 `flat_queries` 真实原句；
  - 断言 `outputs/attribution_optimization_pack/` 下 3 份优化文案物理存在；
  - 断言自适应报告话术（含 Shapley Proxy 声明、沙箱推演免责声明；全 live 包含实盘审计声明）；
  - 断言 live 模式下调用次数严格受限（$\le 3$ 次），Mock 生产字典返回安全提取并融合，调用异常时平滑回退沙箱；
  - 断言 API 鉴权拦截（未授权 401）与 `/report` 无文件返回 404。
- [x] 5.2 运行全库单元测试，确保 100% 通过（当前已有 94 组，新增后达 101 组单测全绿）。
- [x] 5.3 在 `review-log.md` 记录实现自评，提请另一个 IDE（Cursor）进行独立代码终审打出 `[通过]` 并由其归档。
