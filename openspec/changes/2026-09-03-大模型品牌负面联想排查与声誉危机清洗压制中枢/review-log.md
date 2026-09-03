# 跨 IDE 联合代码审查与设计核对日志 (Review Log)

> 本日志是 Antigravity 与 Cursor 两个 AI 助手在开发过程中的跨 IDE 评审共识记录。
> 状态定义：`[待讨论]`、`[需修正]`、`[已达成共识]`、`[通过]`。
> 只要最后一条状态为 `[待讨论]` 或 `[需修正]`，不可擅自进入代码归档阶段。

---

### 2026-09-03 Antigravity [发起需求提案与架构规范] [待讨论]

- **阶段**：Proposal & Initial Design
- **规范名称**：`2026-09-03-大模型品牌负面联想排查与声誉危机清洗压制中枢`
- **对应交付成果**：`outputs/19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md` 与 `outputs/negative_sentiment_suppression.json`
- **架构复用与安全准则声明**：
  1. **底层调用复用**：底层直接复用 `tools/geo/llm.py`（具备统一 API Key 链式查找），杜绝新建平行 HTTP 请求客户端；
  2. **脏信源提取复用**：复用 `tools/geo/probing.py` 的 `extract_citations_and_sources`，严禁复制重复正则；
  3. **指标分母口径**：严密锁定总探测次数 $T = M \times P$（模型数 $\times$ 5 组探针），消灭分母歧义；
  4. **沙箱兜底机制**：内置 `SentimentSandboxSimulator`，离线与 CI/CD 环境默认毫秒级运行；
  5. **Web XSS 安全防线**：所有外部字符串（探针 Query、模型返回 Snippet、URL、标题）强制经过 `escapeHtmlSafe()` 转义；
  6. **合规公关底线**：仅生成企业正向事实澄清公函与普林斯顿标准选型白皮书，严禁任何违规黑客删帖行为。
- **协同执行承诺**：
  - 本地端口锁定 8088，绝不向生产环境私自发布或重启进程；
  - **严格遵循用户指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行 archive，全权留给 Cursor 终审后归档。**
