# Proposal: 竞对大模型声量差距逆向分析与反超作战沙盘 (Competitor LLM SOV Gap Analysis & Leapfrog Strategy Engine)

## Why (为什么做 / 业务背景与痛点)

1. **商业成交最强驱动力在于“击败竞品”**：
   - 企业决策者购买 GEO 服务的最核心诉求是了解：为什么行业同行/竞品在大模型问答中被优先推荐？其声量和信源布局在哪些平台？
2. **缺乏多维声量雷达差距量化与根因透视**：
   - 传统诊断仅列出竞品名称，缺少对竞品在五大本土模型（豆包、DeepSeek、元宝、Kimi、文心）的**声量占有率 (SOV Gap)**、**9 因子语料成熟度**、**外链信源密度**的 6 维量化对比与雷达图；
3. **缺少针对性的反超打击战术路线图 (Leapfrog Action Roadmap)**：
   - 亟需一套能够自动逆向竞品破绽（如：价格模糊、缺乏开源背书、无官方 FAQ）、制定“人无我有、人有我优”的 3 阶段反超作战沙盘。

---

## What Changes (改动范围)

1. **竞对声量差距逆向与反超战术引擎 (`tools/geo/competitor_gap.py`)**：
   - `analyze_competitor_gap(project_id: str, competitor_name: str = None) -> dict`：
     - 计算本品牌 vs 竞品在 6 大维度（模型召回率、外链权威度、价格透明度、量化承诺力、开源技术背书、幻觉免疫力）的得分对比；
     - 深度逆向竞品 3 大声量优势与 3 大致命破绽；
     - 制定 3 阶段反超战术路线图（短期截流、中期包抄、长期壁垒）；
   - `render_competitor_gap_markdown(project_id: str, gap_data: dict) -> str`：
     - 自动渲染输出交付级 `outputs/14_竞对大模型声量差距深度逆向与反超作战沙盘.md` 与 `outputs/competitor_gap_analysis.json`；
2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
   - `geo competitor-gap <pid> [--competitor <name>]`
3. **服务端 API 与 Web 端大一统集成 (`tools/geo/server.py`, `web/index.html`)**：
   - 挂载 `GET/POST /api/projects/{id}/competitor/gap`；
   - Web 端 Step 1 现状体检增加「⚔️ 竞对差距与反超沙盘」弹窗与 6 维雷达图/差距大盘。

---

## Capabilities (对外能力)

- **竞品声量渗透率与 6 维雷达差距量化**；
- **竞品致命破绽逆向与关键词反向截流作战方案**；
- **为销售团队提供极具说服力的竞品降维打击提案依据**。

---

## Impact (影响分析)

- 极大提升 GEO 服务的客单价与签约转化率，直接赋能商业售前与交付团队。

