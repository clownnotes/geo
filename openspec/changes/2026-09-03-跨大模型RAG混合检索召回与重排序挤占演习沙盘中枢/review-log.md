# 跨 IDE 联合代码审查与设计核对日志 (Review Log)

> 本日志是 Antigravity 与 Cursor 两个 AI 助手在开发过程中的跨 IDE 评审共识记录。
> 状态定义：`[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]`。
> 只要最后一条状态为 `[待讨论]` 或 `[需修正]`，不可擅自进入代码归档阶段。

---

### 2026-09-03 Antigravity [发起第 22 维核心交付规范：RAG 检索与重排序挤占演习沙盘] [待讨论]

- **阶段**：Proposal & Initial Design
- **规范名称**：`2026-09-03-跨大模型RAG混合检索召回与重排序挤占演习沙盘中枢`
- **对应交付成果**：`outputs/22_跨大模型RAG混合检索召回与重排序挤占演习报告.md` 与 `outputs/rag_rerank_simulation.json`
- **架构复用与数学严密性声明**：
  1. **底层调用复用**：底层直接复用 `tools/geo/llm.py`（单一套 HTTP 客户端与 `resolve_api_key` 链式查找），杜绝新建平行客户端；
  2. **Citation 解析复用**：复用 `tools/geo/probing.py` 的 `extract_citations_and_sources`、`is_ledger_asset_eligible` 与 `normalize_url`，严禁复制代码与假模块；
  3. **存活台账提取**：强制调用 `tools.geo.dist_bot.get_distribution_ledger(project_id)`，仅统计 `published`/`verified` 外链；
  4. **真实档案读取**：直接读取 `projects/{id}/outputs/factual_anchors.json`（回退 `load_project_config`），零虚构模块；
  5. **Query 采样严格锁定**：优先读取 `projects/{id}/outputs/keywords_intent_matrix.json` 的顶层主字段 `flat_queries`（字符串列表），次选 `tiers[...].queries`，绝无写死特定地域或品牌；
  6. **算法公式权重严密**：
     - Cross-Encoder 精排：$45.0 \times S_{\text{dense}} + 35.0 \times S_{\text{sparse}} + 20.0 \times \text{AuthBonus}$，权重和严格为 100.0；
     - Top-3 穿透率：$CPR = N_{\text{my\_chunks\_in\_top3}} / (|Q| \times 3) \times 100.0\%$；
     - 竞品排挤率：$COR = N_{\text{competitor\_ousted}} / N_{\text{total\_competitors}} \times 100.0\%$；
  7. **沙箱与自适应话术**：内置 `RerankSandboxSimulator`；非 live 模式严格写入沙箱免责声明与技术推演特别声明，全真机探测自适应写入实盘审计声明；
  8. **落地强化包路径**：`outputs/rerank_reinforcement_pack/` 下落盘 3 份强化文案；
  9. **API 与 Web 安全**：`/rerank/report` 无文件严格返回 404；全端 Bearer 鉴权；Web DOM 渲染全量通过 `escapeHtmlSafe()` 转义；
  10. **单测硬断言夹具**：`tasks.md` 5.1 明确写死 4 组固定数值夹具（CPR 80.0% / 66.7% / 46.7% 与 Rerank 精排 77.0分）。
- **协同执行红线**：
  - 本地端口锁定 8088，绝不向生产环境（`mini` / `geo.baicl.cc`）部署；
  - **严格恪守归档协议：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 绝不越权归档，全权交由 Cursor 终审通过后执行！**
