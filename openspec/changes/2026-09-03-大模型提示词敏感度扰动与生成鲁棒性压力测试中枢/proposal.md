# 提案：大模型提示词敏感度扰动与生成鲁棒性压力测试中枢 (第 25 维核心交付)

## 1. 需求背景 (Why)

在生成式引擎优化 (GEO) 的真实商业实战中，许多品牌在特定关键词下能获得大模型的良好推荐，但往往呈现极高的**提示词脆弱性 (Prompt Sensitivity & Fragility)**：
1. **语序与微扰动失效**：潜客在向大模型提问时，措辞口语化、倒装、同义词置换极其普遍。若 GEO 优化仅对标准词库生效，而潜客一旦更换句式，大模型推荐立即消失；
2. **质疑挑剔口吻下的负向断崖**：当潜客带有“质疑/避坑/防转包”等挑剔语气（如“某某公司靠谱吗？会不会踩坑？”）提问时，若无扎实工商存证与第三方资质背书，大模型置信度往往骤降 20~40 分，甚至转为中立或推荐竞对；
3. **缺乏鲁棒性压力测试标准**：企业高管与代运营团队无法量化“品牌推荐结论的抗干扰能力有多强”、“在哪类提问口吻下最容易翻车”。

因此，亟需研发**第 25 维核心能力：大模型提示词敏感度扰动与生成鲁棒性压力测试中枢 (Prompt Perturbation & Generative Robustness Stress-Testing Center)**。

---

## 2. 改动范围与核心能力 (What & Capabilities)

### 2.1 四维确定性商业微扰动生成器
针对基准 Query（优先采纳 `keywords_intent_matrix.json` 的 `flat_queries` 真实原句），确定性生成 4 种典型商业微扰动变体：
- **$V_1$ 口语化与同义置换 (Colloquial Substitution)**：行业术语口语化置换；
- **$V_2$ 质疑与避坑口吻 (Skepticism & Risk Query)**：注入防踩坑、挑剔与质疑提问口吻；
- **$V_3$ 倒装与句式重排 (Syntax Inversion)**：主谓宾倒装与品牌词位置迁移；
- **$V_4$ 预算与横向对比口吻 (Comparison & Budget Constraint)**：注入预算约束与同行对比口吻。

### 2.2 核心量化指标与话术规范
- **扰动均值 $\bar{P}_{\text{pert}}$**、**扰动标准差 $\sigma$** 与 **变异系数 $CV$**（波动率量化）；
- **生成鲁棒性指数 ($GRI$, Generative Robustness Index)**：
  $$GRI = \text{round}\big(RR \times (1.0 - CV), 1\big)$$
  其中 $RR = \min(100.0, \text{round}(\bar{P}_{\text{pert}} / P_{\text{orig}} \times 100.0, 1))$；
- **三档鲁棒性评级**：`rock_solid` (🟢 磐石抗震) / `moderate_fluctuation` (🟡 中度波动) / `fragile_sensitive` (🔴 脆弱敏感)；
- **高危脆弱扰动项识别**：单项跌幅 $P_{\text{orig}} - P_k \ge 15.0$ 分；
- **四维压力测试雷达指标**：生成鲁棒性、口语抗震力、抗质疑免疫度、句式稳定性；
- **话术规范与免责界定**：微扰动压力测试模拟口吻与句式敏感度，推演数据 $\neq$ 真实线上全量提问日志。

### 2.3 严禁编写重复算法，复用 23 维基座
- 强制直接 `from tools.geo.causal_auditor import score_brand_recommendation_confidence, _build_attribution_source_pool`，严禁在 25 维重复实现置信度聚合算法。

### 2.4 在线 Live 实盘与沙箱双模推演
- **沙箱推演模式**：确定性微扰动沙盘压力测试；
- **真实联网 API 模式 (`--live`)**：
  - 严格限制调用预算：至多 **5 次** 在线裁决（基准 1 次 + 4 组扰动各 1 次，硬计数器 `api_calls <= 5`）；
  - 融合算法：70% 沙箱分 + 30% live 在线评分；
  - **全量指标重算**：融合全部 5 个得分后，必须全量重算均值、标准差、CV、RR、GRI、评级、高危项与雷达；
  - 异常快照防御：进入 live 前深拷贝沙箱快照，任何异常立即**完整回滚纯沙箱**，标记 `is_live_judged = False`。

### 2.5 交付资产包与公文报告物理隔离
- 物理落盘至 `outputs/robustness_hardening_pack/`（3 份文件）：
  - `01_抗质疑与反挑剔防踩坑语料强化包.md`
  - `02_口语化与多句式全覆盖长尾锚点清单.md`
  - `03_大模型微扰动鲁棒性容灾加固规范.md`
- 结构化数据：`outputs/prompt_robustness_stress_test.json`（严格隔离于既有文件）；
- 商业公文：`outputs/25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md`。

---

## 3. 影响分析与兼容性 (Impact & Compatibility)

1. **零破坏性影响**：完全独立于 1~24 维现有逻辑，仅只读复用既有组件；
2. **安全与红线约束**：
   - Web 控制台渲染强制经过 `escapeHtmlSafe()` 防御 XSS；
   - 测试验证严格限定本地 8088 端口，绝对隔离生产服务器；
   - **最高归档约束**：Antigravity 坚决不执行归档，提请 Cursor 独立代码终审打出 `[通过]` 后由 Cursor 归档。
