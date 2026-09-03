# 跨 IDE 审查日志：大模型商业推荐因果归因与信源边际贡献度量化审计中枢

---

### 2026-09-03 Antigravity [发起提案与设计：反事实消融推导、CRI鲁棒性与Shapley边际贡献度] [待讨论]

- **阶段**：Proposal & Design Ready for Cursor Review
- **提案背景与核心设计要点**：
  1. **填补 GEO 归因终极黑盒**：解决企业客户在全网投放数十篇内容后，无法证明“到底哪篇内容对大模型推荐品牌起到了决定性因果支撑”的商业痛点；
  2. **反事实消融数学模型与 5 组固定数值夹具**：
     - 基线得分 $P_{\text{base}}$ 与逐一切片 Leave-One-Out 抽离得分 $P_{\text{ablated}}$；
     - 边际因果跌幅 $\Delta P(s_i)$ 与边际贡献率 $MCR(s_i)$；
     - 品牌因果鲁棒性指数 $CRI = \min(P_{\text{ablated}}) / P_{\text{base}} \times 100.0\%$，三档枚举 `high_resilience` (≥75%), `moderate_dependency` (50%~74.9%), `fragile_single_point` (<50%)；
     - 信源角色分类：👑 核心基石 (`cornerstone`, MCR≥25%), ⚡ 协同催化 (`catalyst`, 10%~24.9%), 🥀 冗余低效 (`redundant`, MCR<10%)；
     - 单点故障标记：$MCR \ge 40\%$ 且抽离后得分 $<50$ 记为 `critical_spof = True`；
     - 提供 5 组固定数值夹具，写入单测硬断言；
  3. **真实路径点名与数据依赖**：
     - 我方切片提取自 `03_普林斯顿9因子语料库.md`、`factual_anchors.json` 与台账 `get_distribution_ledger` 中存活的落地页（`is_ledger_asset_eligible`）；
     - 商业 Query 采样自 `keywords_intent_matrix.json` 的顶层主字段 `flat_queries`；
  4. **`--live` 语义与 Out of Scope 契约**：
     - 绝不在本地运行大型神经网络模型；
     - 确定性沙箱算法轻量秒级完成；
     - `--live` 仅调用真实在线大模型 API (`call_model_raw`)，安全提取 `content` 字典内容并按 70/30 融合精排得分，异常平滑降级纯沙箱且标记 `is_live_judged = False`；
     - 报告自动切换实盘或沙箱审计声明；
  5. **文件隔离与多端契约**：
     - 独立落盘 `causal_attribution_audit.json`（与 12 号、22 号严格隔离）；
     - 生成公文报告 `23_大模型商业推荐因果归因与信源边际贡献度量化审计报告.md` 与优化三件套 `outputs/attribution_optimization_pack/`；
     - CLI 终端输出高保真 ANSI 大盘，API 支持鉴权与 404，Web 前端采用 `escapeHtmlSafe()` 防御 XSS。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，严禁推向生产服务器；
  - **提案阶段先对齐共识，待 Cursor 独立审查并签署 `[已达成共识]` 后方可进入 apply 开发阶段！**
- **状态结论**：`[待讨论]`，提请 Cursor 独立初审。
