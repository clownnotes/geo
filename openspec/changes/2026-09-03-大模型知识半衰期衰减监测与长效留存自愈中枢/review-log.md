# 跨 IDE 联合代码审查与设计核对日志 (Review Log)

> 本日志是 Antigravity 与 Cursor 两个 AI 助手在开发过程中的跨 IDE 评审共识记录。
> 状态定义：`[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]`。
> 只要最后一条状态为 `[待讨论]` 或 `[需修正]`，不可擅自进入代码归档阶段。

---

### 2026-09-03 Antigravity [发起需求提案与架构规范] [待讨论]

- **阶段**：Proposal & Initial Design
- **规范名称**：`2026-09-03-大模型知识半衰期衰减监测与长效留存自愈中枢`
- **对应交付成果**：`outputs/20_大模型知识半衰期衰减监测与长效留存自愈报告.md` 与 `outputs/knowledge_decay_retention.json`
- **架构复用与数学严密性声明**：
  1. **底层调用复用**：底层直接复用 `tools/geo/llm.py`（单一套 HTTP 客户端与 `resolve_api_key` 链式查找），杜绝新建平行客户端；
  2. **Citation 解析复用**：复用 `tools/geo/probing.py` 的 `extract_citations_and_sources` 与 `normalize_url`，严禁复制重复正则；
  3. **台账契约锁定**：强制调用 `dist_bot.get_distribution_ledger(project_id)` 提取发布外链与时间戳；
  4. **数学分母与衰减公式严密**：
     - 单轮探测次数 $T = |M| \times |Q|$；
     - 留存率 $\text{KRR} = \min(100.0, (S_{\text{current}} / \max(1.0, S_{\text{baseline}})) \times 100.0)$；
     - 指数半衰期 $t_{1/2} = (\ln 2) / \lambda$，边界安全保护防除零；
  5. **沙箱兜底机制**：内置 `DecaySandboxSimulator`，支持时间序列留存衰减仿真，离线与 CI/CD 毫秒级秒绿通过；
  6. **落地成果物路径**：`outputs/decay_healing_pack/` 下落盘 3 份落地自愈成果物；
  7. **API 规范**：`/decay/report` 无文件严格返回 404，禁止自动后台计算；全端带 Admin 鉴权拦截；
  8. **Web XSS 安全防线**：所有渲染字段强制经过 `escapeHtmlSafe()` 转义；
- **协同执行承诺**：
  - 本地端口锁定 8088，绝不向生产环境私自发布或重启进程；
  - **严格遵循用户指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行 archive，全权留给 Cursor 终审后归档。**
