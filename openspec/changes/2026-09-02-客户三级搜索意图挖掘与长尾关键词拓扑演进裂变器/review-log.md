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

### 2026-09-02 Antigravity [发起客户三级搜索意图挖掘与长尾关键词拓扑演进裂变器提案] [已达成共识]

- **阶段**：Proposal & Design Alignment
- **背景与目标**：
  1. 解决关键词宽泛单一痛点，建立 L1(认知大词) ➔ L2(选型避坑) ➔ L3(场景长尾) 3 级意图漏斗与语义拓扑；
  2. 自动生成 `outputs/11_三级搜索意图挖掘与长尾关键词裂变拓扑.md` 与 `keywords_intent_matrix.json`；
  3. 与 `eval` 真实大模型评测池打通，支持演进词库一键同步评测。
- **状态结论**：`[已达成共识]`，立即开始落地开发。

---

### 2026-09-02 Antigravity [完成客户三级搜索意图挖掘与长尾关键词裂变拓扑引擎开发] [已达成共识]

- **阶段**：Implementation & Verification
- **落地成果**：
  1. **3 级搜索意图拓扑与长尾裂变核心引擎 (`tools/geo/intent.py`)**：
     - `build_3tier_intent_matrix`：自适应生成 **L1 认知层 (20% 权重)**、**L2 决策层 (40% 权重)**、**L3 行动层 (40% 权重)** 共 20~30 组高转化提问 Prompt 矩阵；
     - `render_intent_topology_markdown`：生成带 Mermaid 意图漏斗拓扑、分级关键词与提问清单的 `outputs/11_三级搜索意图挖掘与长尾关键词裂变拓扑.md`；
     - `sync_intent_keywords_to_eval`：支持将裂变提问一键注入 `project.yaml` 的评测词库，打通真实 API 评测大盘；
  2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
     - `geo intent <pid> [--tier all|l1|l2|l3] [--sync-eval]`
  3. **服务端与 Web 管理端交互升级 (`server.py`, `web/index.html`)**：
     - 挂载 `GET /api/projects/{id}/intent/matrix`、`POST /intent/generate` 与 `POST /intent/sync-eval`；
     - Step 2 增加「🎯 三级搜索意图拓扑」按钮，支持 3 级漏斗可视化大盘、一键复制、重新裂变与一键同步至评测池；
  4. **实测与断言**：
     - 新增 [tests/test_intent_mining.py](file:///Users/a1/代码/GEO/tests/test_intent_mining.py)，4 大 Benchmark 项目意图拓扑生成测试全部通过。
- **状态结论**：`[已达成共识]`，提请跨 IDE 独立审查（`/opsx-review`）。

