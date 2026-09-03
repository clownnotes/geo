# 评审日志：大模型提示词敏感度扰动与生成鲁棒性压力测试中枢 (第 25 维核心交付)

---

### 2026-09-03 Antigravity [发起第 25 维提案：提示词敏感度扰动与生成鲁棒性压力测试中枢] [待讨论]

- **阶段**：Initial Proposal & Technical Design Review
- **核心能力与规范设计**：
  1. **四维确定性商业微扰动生成算法**：
     - 基线 Query 优先读取 `keywords_intent_matrix.json` 中首条真实 Prompt，确定性派生 4 组变体：$V_1$ 口语化置换、$V_2$ 质疑避坑口吻、$V_3$ 句式倒装重排、$V_4$ 预算横向对比；
  2. **严禁编写重复算法**：
     - 强制直接复用 23 维防饱和 Top-3 推荐概率模型：`from tools.geo.causal_auditor import score_brand_recommendation_confidence, _build_attribution_source_pool`；
  3. **严谨数学量化模型**：
     - 扰动均值 $\bar{P}$、样本标准差 $\sigma$、变异系数 $CV = \sigma / \bar{P}$、留存率 $RR = \bar{P} / P_{\text{orig}}$；
     - 生成鲁棒性指数：$GRI = \text{round}(RR \times (1.0 - CV), 1)$；
     - 鲁棒性三档评级：`rock_solid` ($\ge 75\%$) / `moderate_fluctuation` ($50\sim 74.9\%$) / `fragile_sensitive` ($<50\%$)；
     - 高危脆弱扰动判定：跌幅 $\ge 15.0$ 分；
  4. **6 组固定数值夹具锁定**：
     - 包含磐石抗震（$91.0\%$）、中度波动（$66.2\%$）、脆弱敏感（$29.8\%$）、高危脆弱项识别、四维雷达与 Top-3 聚合算法；
  5. **Live 模式调用预算与快照防御**：
     - 预算锁死至多 5 次调用（基线 1 次 + 4 组变体各 1 次，硬计数器 `api_calls <= 5`）；
     - 生产字典安全解包与正则防御；
     - 融合后强制基于全新 5 个得分全量重算统计量、GRI、高危项与雷达；
     - 进入 live 前深拷贝沙箱快照，中途任何异常 100% 完整回滚纯沙箱；
  6. **交付资产与公文报告物理隔离**：
     - 数据文件：`outputs/prompt_robustness_stress_test.json`（对齐顶层 Schema）；
     - 商业报告：`outputs/25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md`；
     - 容灾加固包：`outputs/robustness_hardening_pack/`（3 份文件）。
- **协同与安全红线守则**：
  - 本地测试严格锁定 8088 端口，绝对隔离生产服务器；
  - **根据最高指示：“归档交给另一个 IDE，都审核通过，它来归档”，Antigravity 坚决不执行归档，提请 Cursor 独立初审签署 `[已达成共识]`！**
- **状态结论**：`[待讨论]`，提请 Cursor 进行独立设计初审。
