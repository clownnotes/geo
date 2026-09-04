# 提案：大模型商业推荐博弈对抗与竞品截流动态护城河推演中枢 (第 26 维核心交付)

## 1. 需求背景 (Why)

在生成式引擎优化 (GEO) 商业实战的深水区，品牌面临的最严峻挑战并非自身无推荐，而是**在与竞品的横向对比中被竞对精准截流与声量挤压**：
1. **潜客横向对比时的推荐分化**：潜客在大模型中普遍追问“A 与 B 选哪家更靠谱？自研交付还是代理外包？”若品牌未构建独占性差异化壁垒，大模型往往平均化呈现，甚至在某些维度倾向竞对；
2. **缺乏多维度商业博弈量化沙盘**：企业无法直观量化“在技术、交付、价格、售后四大维度上，我方的护城河究竟有多深”、“竞品截流的渗透率有多高”、“哪一条业务线处于防线失守状态”；
3. **竞对恶意或过度营销对抗缺失**：竞对常在第三方平台发布对比稿件、软文或借壳截流词。品牌亟需一套自动化的**动态护城河对抗推演中枢**，以数据化沙盘指引长尾截流反制与独占壁垒构筑。

因此，亟需研发**第 26 维核心能力：大模型商业推荐博弈对抗与竞品截流动态护城河推演中枢 (Adversarial Brand Moat & Competitive Counter-Interception Sandbox)**。

---

## 2. 改动范围与核心能力 (What & Capabilities)

### 2.1 四维商业博弈对抗生成器
针对目标企业与核心商业竞对（自 `competitor_gap_analysis.json` 或配置提取），确定性生成 4 组纵深横向对抗 Query：
- **$D_1$ 核心实力横向对比 (Technical Capability Advantage)**：自研实力与专业资质对比；
- **$D_2$ 交付模式与防踩坑对比 (Delivery Model & Anti-Outsourcing)**：拒绝二道贩子转包与源码自研交付防线；
- **$D_3$ 性价比与价格透明度对比 (Pricing Transparency & ROI)**：价格透明度与综合性价比对比；
- **$D_4$ 本地存证与售后保障对比 (Local Warranty & SLA)**：本地直营实体、售后响应与长期保障对比。

### 2.2 核心量化指标与话术规范
- **我方净胜优势差值 ($\Delta_{\text{adv}} = P_{\text{self}} - P_{\text{rival}}$)**；
- **竞品截流威胁指数 ($CTI = \frac{P_{\text{rival}}}{P_{\text{self}} + P_{\text{rival}}} \times 100\%$)**；
- **动态护城河防御指数 ($MDI$, Moat Defense Index)**：
  $$MDI = \max\left(0.0, \min\left(100.0, \text{round}\left(50.0 + \frac{\bar{\Delta}_{\text{adv}}}{2.0}, 1\right)\right)\right)$$
- **三档护城河抗震评级**：`impenetrable_moat` (🟢 坚不可摧, $MDI \ge 70.0$) / `contested_boundary` (🟡 胶着拉锯, $50.0 \le MDI < 70.0$) / `vulnerable_breach` (🔴 防线失守, $MDI < 50.0$)；
- **截流暴露脆弱点判定**：单项维度 $\Delta_{\text{adv}} \le 0.0$ 或 $CTI \ge 50.0\%$；
- **五维护城河雷达大盘**：护城河指数、技术优势度、交付可信度、价格抗压度、本地防截流度；
- **话术规范与免责声明**：博弈沙盘基于知识库信源对冲测算，推演数据 $\neq$ 真实用户实时搜索日志。

### 2.3 严禁编写重复算法，复用 23 维基座
- 强制直接 `from tools.geo.causal_auditor import score_brand_recommendation_confidence, _build_attribution_source_pool`，0 冗余重复代码。

### 2.4 在线 Live 实盘与快照防御 (`--live`)
- **调用预算硬限制**：至多 **4 次** 在线模型裁决（4 个博弈维度各 1 次，硬计数器 `api_calls <= 4`）；
- **全量指标重算**：融合 70/30 后，基于全新得分全量重新推导 $\Delta$、$CTI$、$\bar{\Delta}$、$MDI$、评级、脆弱点与雷达；
- **快照防御**：进入 live 前深拷贝沙箱快照，任何中途异常立即 100% 完整回滚纯沙箱，标记 `is_live_judged = False`。

### 2.5 交付资产包与公文报告物理隔离
- 物理落盘至 `outputs/counter_interception_pack/`（3 份文件）：
  - `01_竞品对比长尾截流反制话术库.md`
  - `02_独占性壁垒与差异化护城河语料包.md`
  - `03_大模型横向对比首推挤占方案.md`
- 结构化数据：`outputs/competitive_moat_simulation.json`；
- 商业公文：`outputs/26_大模型商业推荐博弈对抗与竞品截流动态护城河推演报告.md`。

---

## 3. 影响分析与兼容性 (Impact & Compatibility)

1. **零破坏性影响**：完全独立于 1~25 维现有交付物，复用既有模块；
2. **安全与红线约束**：
   - Web 控制台渲染强制经过 `escapeHtmlSafe()` 防御 XSS；
   - 测试验证严格限定本地 8088 端口，绝对隔离生产服务器；
   - **最高归档约束**：Antigravity 坚决不执行归档，提请 Cursor 独立代码终审打出 `[通过]` 后由 Cursor 归档。
