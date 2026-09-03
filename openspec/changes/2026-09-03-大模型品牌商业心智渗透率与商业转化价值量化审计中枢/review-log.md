# 跨 IDE 联合代码审查与设计核对日志 (Review Log)

> 本日志是 Antigravity 与 Cursor 两个 AI 助手在开发过程中的跨 IDE 评审共识记录。
> 状态定义：`[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]`。
> 只要最后一条状态为 `[待讨论]` 或 `[需修正]`，不可擅自进入代码归档阶段。

---

### 2026-09-03 Antigravity [发起第 21 维全案终极交付规范：商业心智渗透与价值审计] [待讨论]

- **阶段**：Proposal & Initial Design
- **规范名称**：`2026-09-03-大模型品牌商业心智渗透率与商业转化价值量化审计中枢`
- **对应交付成果**：`outputs/21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md` 与 `outputs/mindshare_conversion_audit.json`
- **架构复用与数学严密性声明**：
  1. **底层调用复用**：底层直接复用 `tools/geo/llm.py`（单一套 HTTP 客户端与 `resolve_api_key` 链式查找），杜绝新建平行客户端；
  2. **Citation 解析复用**：复用 `tools/geo/probing.py` 的 `extract_citations_and_sources`、`is_ledger_asset_eligible` 与 `normalize_url`，严禁复制代码与假模块；
  3. **真实档案读取**：直接读取 `projects/{id}/outputs/factual_anchors.json`（未生成时回退 `load_project_config`），零虚构模块；
  4. **MPI 数学模型权重严密**：
     - 单轮探测次数 $T = |M| \times |Q|$；
     - 四维因子：$0.35 \times \text{SOV} + 0.25 \times \text{Cit} + 0.25 \times \text{BRS} + 0.15 \times \text{KRR}$，权重总和严格为 1.0；
     - 心智五星等级划分清晰（$\ge 85$ 领军垄断 / $70\sim 84.9$ 强势竞争 / $55\sim 69.9$ 中度可见 / $<55$ 心智盲区）；
  5. **商业转化价值模型 (CCV)**：按行业基准 CPA 测算年化等效竞价广告采购价值（AEV）；
  6. **沙箱与自适应话术**：内置 `MindshareSandboxSimulator`；非 live 模式严格写入免责声明，全真机探测自适应写入实盘审计声明；
  7. **落地高管包路径**：`outputs/commercial_roi_pitch/` 下落盘 3 份落地文件；
  8. **API 与 Web 安全**：`/mindshare/report` 无文件严格返回 404；全端 Bearer 鉴权；Web DOM 渲染全量通过 `escapeHtmlSafe()` 转义；
  9. **单测硬断言夹具**：`tasks.md` 5.1 明确写死 3 组固定数值夹具（80.5 / 95.0 / 41.5）。
- **协同执行红线**：
  - 本地端口锁定 8088，绝不向生产环境（`mini` / `geo.baicl.cc`）部署；
  - **严格恪守归档协议：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 绝不越权归档，全权交由 Cursor 终审通过后执行！**
