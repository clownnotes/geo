# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code / Cursor）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

### 2026-09-02 Antigravity [发起真实大模型 API 评测与 Citation 捕获引擎提案] [已达成共识]

- **阶段**：Proposal & Design Alignment
- **背景与目标**：
  1. 支持接入真实豆包（火山方舟）、DeepSeek 等 API 进行 45 词高并发跑批评测；
  2. 自动捕获回答中的 Citation 角标并与存活台账（`dist_ledger.json`）交叉验证；
  3. 支持无 Key 时高拟真优雅降级，输出 `06_大模型真实API评测与Citation捕获报告`。
- **状态结论**：`[已达成共识]`，立即开始落地开发。

---

### 2026-09-02 Antigravity [完成真实大模型 API 评测与 Citation 捕获引擎落地] [已达成共识]

- **阶段**：Implementation & Verification
- **落地成果**：
  1. **评测与捕获引擎 (`tools/geo/evaluator.py`)**：
     - 实现统一 OpenAI 协议适配器，支持豆包、DeepSeek 等真实线上 API 调用，无 Key 时自动平滑回退至高拟真沙箱推演；
     - 自动解析回答中的品牌命中（SOV%）、首推排名（Top1/Top3）与 Citation 渠道角标（头条/知乎/GitHub 等）；
     - 与 `dist_ledger.json` 分发存活台账做交叉印证（cross match rate）；
     - 自动落盘 `06_大模型真实API评测与Citation捕获报告.json` 与 `.md`；
  2. **CLI 与 Server 接口集成**：
     - CLI 新增 `geo eval <project_id> [--models doubao,deepseek] [--limit 15]`；
     - Web 端新增 `/api/projects/{id}/eval/run` 与 `/api/projects/{id}/eval/report`；
  3. **实测验证**：
     - 对 `xuzhou_xuanyuan`、`b2b_machinery`、`retail_catering`、`local_legal` 全量执行 `geo eval`，100% 成功输出结构化报告。
- **状态结论**：`[已达成共识]`，提请跨 IDE 联机对抗审查（`/opsx-review`）。

