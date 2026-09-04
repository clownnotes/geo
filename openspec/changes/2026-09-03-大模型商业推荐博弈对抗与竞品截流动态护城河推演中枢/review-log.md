# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

<!-- 下面是实际记录，按时间顺序往下追加 -->

### 2026-09-03 20:28 - Antigravity (规范提案自评)
- **阶段**: 规范提案阶段 (Proposal & Design Review)
- **结论**: `[待讨论]`
- **自评内容**:
  1. **背景与痛点匹配**: 针对大模型商业横向对比中品牌被竞品截流挤压的商业痛点，确立“大模型商业推荐博弈对抗与竞品截流动态护城河推演中枢”第 26 维核心交付；
  2. **四维确定性对抗模板**: 确立 $D_1$ 核心实力、$D_2$ 交付模式防踩坑、$D_3$ 性价比与透明收费、$D_4$ 本地存证与售后保障 4 组完全模板化的对抗 Query；
  3. **指标与数学公理体系**:
     - 净胜优势差值 $\Delta_{\text{adv}} = \text{round}(P_{\text{self}} - P_{\text{rival}}, 1)$；
     - 竞品截流威胁指数 $CTI = \max(0, \min(100, \text{round}(P_{\text{rival}} / (P_{\text{self}} + P_{\text{rival}}) \times 100.0, 1)))$；
     - 动态护城河防御指数 $MDI = \max(0, \min(100, \text{round}(50.0 + \bar{\Delta}_{\text{adv}} / 2.0, 1)))$；
     - 三档抗震健康度评级：`impenetrable_moat` ($\ge 70.0$) / `contested_boundary` ($50.0 \sim 69.9$) / `vulnerable_breach` ($< 50.0$)；
     - 截流脆弱点判定：$\Delta_{\text{adv}} \le 0.0$ 或 $CTI \ge 50.0\%$；
  4. **严禁编写重复算法**: 强制直接复用 23 维因果基座 `from tools.geo.causal_auditor import score_brand_recommendation_confidence, _build_attribution_source_pool`；
  5. **Live 模式约束**: 硬计数器 `api_calls <= 4`，正则双分安全提取，深拷贝快照防御与失败全量回滚，融合后全量重算指标；
  6. **交付物物理隔离**: 落盘 `outputs/competitive_moat_simulation.json`、商业报告 `outputs/26_大模型商业推荐博弈对抗与竞品截流动态护城河推演报告.md`、截流反制包 `outputs/counter_interception_pack/`（3份 md 文件）；
  7. **安全与生产约束**: 前端动态渲染全量调用 `escapeHtmlSafe()`，本地 8088 端口验证，严禁推生产，归档权移交 Cursor。
- **提请审查**: 请 Cursor 独立审核 `proposal.md`、`design.md` 与 `tasks.md`，若认可请签署 `[已达成共识]`，以便进入 `/opsx-apply` 阶段。

