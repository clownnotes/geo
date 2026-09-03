# 跨 IDE 联合评审日志 (Review Log)

---

### 2026-09-02 Antigravity [发起提案：多大模型实时联网探测与Citation信源溯源对账中枢] [待讨论]

- **阶段**：Proposal & Design Initial Submission
- **需求范围**：
  1. 研发 `tools/geo/llm_gateway.py` 与 `tools/geo/probing.py`，实现多大模型（豆包、DeepSeek、Kimi 与高保真沙箱）统一调用网关；
  2. 研发正文 Citation 角标（`[1]`、`[[1]]`、`^1`）与尾部 Sources 链接提取解析算法；
  3. 研发捕获信源与项目 `04_全网分发渠道执行与存活台账`（`dist_ledger.json`）的自动对账算法，精确标记 Hit 转化；
  4. 测算实盘核心指标：实测提及率 (`real_sov_pct`)、信源角标占有率 (`citation_share_pct`)、首位推荐率 (`top1_recommendation_rate`)；
  5. 统一规范生成全案第 18 维交付物：`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`；
  6. 注册 CLI `geo probe` 并挂载管理端 3 个鉴权 API 端点；
  7. 升级 `web/index.html`，新增「🤖 多模型实时探测」工作台模态与对账透视；
  8. 编写 `tests/test_probing.py` 单测套件。
- **协同约束声明**：
  - 本端（Antigravity）负责方案设计与后续代码研发；
  - 严格遵守红线：**本地 8088 端口测试、禁私自推生产；最终归档严格交由另一个 IDE（Cursor）在独立复审后执行！**

- **状态结论**：`[待讨论]`，提请跨 IDE（Cursor 等）进行独立审查对齐。
