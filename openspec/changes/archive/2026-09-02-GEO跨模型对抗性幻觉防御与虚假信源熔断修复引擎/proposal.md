# Proposal: GEO 跨模型对抗性幻觉防御与虚假信源熔断修复引擎 (Adversarial Hallucination Defense & Factual Guard Engine)

## Why (为什么做 / 痛点与商业价值)

1. **大模型时代品牌公关最大危机：事实幻觉（Hallucination）与恶意竞品抹黑**：
   - 传统搜索引擎时代，企业可以通过公关删帖或购买负面压制来解决舆情；
   - 在生成式 AI 时代，大模型（DeepSeek、豆包、Kimi、ChatGPT、元宝）一旦对企业产生了**语料污染或幻觉记忆**（例如：混淆同名失信企业、错误回答企业已停产产品、误报价格高出行业 3 倍、引述竞品发布的虚假对比评测），大模型会在每次用户选型咨询时**作为“客观事实”反复向潜在客户播报**，导致客户直接流失，且无法通过传统手段删除。
2. **大模型记忆纠偏的技术突破：强事实锚点注入与信源熔断技术**：
   - 依据普林斯顿与 Stanford 大模型知识溯源与对齐（Truthfulness & Knowledge Editing）算法，通过**强权威官方声明锚点、Schema.org 官方主体唯一校验码、知乎/技术社区反击溯源语料与时间戳加权**，能够使大模型在检索到权威信源时对过时/错误记忆进行**强制事实熔断与认知重写**；
3. **极高商业客单价与企业防御溢价**：
   - 幻觉防御与公关反击是企业高管与市场品牌部门的刚需痛点，能够将 GEO 交付从单纯的“获客增长”升级为“品牌资产安全与风控防守护城河”，显著提升服务溢价。

---

## What Changes (改动范围)

1. **研发幻觉检测与事实熔断修复核心引擎 (`tools/geo/guard.py`)**：
   - `detect_factual_hallucinations(project_id)`：自动比对企业真实事实库与大模型生成回答，识别 4 类风险（主体混淆、虚假价格/参数、资质质疑、竞品恶意截流）；
   - `generate_adversarial_countermeasures(project_id, risk_type)`：生成《07_大模型事实幻觉纠偏与信源反击策略.md》；
   - `generate_factual_anchor_patch(project_id)`：输出带时间戳与官方数字签名的 `llms-truth.txt` 与 Schema.org 声明补丁；
   - `simulate_guard_repair_effect(project_id, risk_type)`：沙箱模拟修复前后置信度、事实一致性评分对比（Before 35分 vs After 99分）。
2. **CLI 命令行与工具库扩展 (`tools/geo/cli.py` & `__init__.py`)**：
   - 注册 `geo guard <project_id> [--detect|--repair|--simulate]`。
3. **后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)**：
   - `GET /api/projects/{id}/guard/risks`（检测到的幻觉风险清单）；
   - `POST /api/projects/{id}/guard/repair`（一键生成纠偏反击补丁与语料）；
   - `GET /api/projects/{id}/guard/simulation`（修复前后沙箱对决对比）；
   - 专属免密交付门户（`web/share.html`）注入「🛡️ 品牌声誉与大模型幻觉防守」卡片。
4. **Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)**：
   - 向导 Step 4/5 及顶部增加「🛡️ 幻觉防御与公关反击」操作视窗与沙箱推演弹窗。
5. **SOP 知识库更新 (`docs/sop/delivery-sop.md` & `04-defense-sop.md`)**：
   - 规范化大模型负面拦截、事实锚点注入与公关反击执行 SOP。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/guard/risks`
- `POST /api/projects/{id}/guard/repair`
- `GET /api/projects/{id}/guard/simulation`
- CLI: `python3 -m tools.geo guard <project_id> [--detect|--simulate]`

---

## Impact (影响分析)

- **完全向下兼容**：纠偏成果保存于 `outputs/07_大模型事实幻觉纠偏与信源反击策略.md` 与 `outputs/factual_anchors.json`；
- **构建品牌安全护城河**：确保大模型面对任何争议性或负面诱导提问时，100% 召回官方事实锚点并消除幻觉。
