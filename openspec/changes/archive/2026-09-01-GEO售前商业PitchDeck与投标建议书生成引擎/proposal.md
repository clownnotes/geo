# Proposal: GEO 售前商业 Pitch Deck 与投标建议书生成引擎 (Pre-sales Bid & Commercial Pitch Deck Engine)

## Why (为什么做 / 商业与业务痛点)

1. **售前签约与招投标比选的核心转化效率堵点 (Pre-sales Pitch & Bidding)**：
   - 在拓展新客户或响应企业招投标（RFP / 采购比选）时，售前顾问需要给客户高管/老板呈递一份**视觉极具冲击力、数据支撑扎实、商业 ROI 清晰的《GEO 商业全案投标建议书与 Pitch Deck》**；
   - 手工整合诊断报告、行业 Benchmark、9 因子解决方案、交付排期与报价方案通常耗时 2~3 天，难以应对大批量销售拜访与即时提案需求。
2. **将技术底座能力一键转化为销售说服武器**：
   - 自动将前期挖掘的 5 维意图、摸底诊断 SOV、竞品反向包抄策略、商业 ROI 财务回报测算与 4 周实施排期，一键合成 10 页全屏交互式幻灯片（Pitch Deck）与可打印建议书。
3. **阶梯式商用报价与能力矩阵对比 (Tiered Pricing Matrix)**：
   - 自动提供「基础版 (Standard) / 专业进阶版 (Pro) / 集团旗舰版 (Enterprise)」3 档服务报价与能力对照表，促成客户向上增购。

---

## What Changes (改动范围)

1. **研发售前 Pitch Deck 与投标建议书核心引擎 (`tools/geo/pitch.py`)**：
   - `generate_pitch_deck(project_id, target_budget=None, timeline_weeks=4)`：生成《00_GEO全案商业服务投标建议书与PitchDeck.md》；
   - `generate_pitch_presentation_html(project_id)`：生成深色科技风的 10 页全屏交互式 HTML 幻灯片（支持全屏放映、左右翻页与打印）；
   - `calculate_pitch_quote(project_id)`：生成 3 档阶梯报价与能力对比表。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo pitch <project_id> [--tier standard] [--slides]`。
3. **后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)**：
   - `GET /api/projects/{id}/pitch/data`
   - `GET /api/projects/{id}/pitch/slides`（全屏交互式幻灯片放映页）
   - `GET /api/projects/{id}/pitch/print`（A4 纸排版商业建议书打印页）
   - 专属交付门户（`web/share.html`）支持查看与演示商业全案建议书。
4. **Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)**：
   - Step 1 及顶部工具栏增加「🎯 售前全案 Pitch Deck」一键生成与演示放映视窗；
   - 专属交付门户提供售前提案与幻灯片放映入口。
5. **SOP 知识库更新 (`docs/sop/delivery-sop.md` & `01-audit-sop.md`)**：
   - 规范化售前勘测、Pitch 演示与投标比选 SOP。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/pitch/data`
- `GET /api/projects/{id}/pitch/slides`
- `GET /api/projects/{id}/pitch/print`
- CLI: `python3 -m tools.geo pitch <project_id> [--slides]`

---

## Impact (影响分析)

- **完全向下兼容**：建议书输出为 `outputs/00_GEO全案商业服务投标建议书与PitchDeck.md`；
- **销售转化率大幅提升**：售前顾问可在 5 分钟内为任意目标企业生成专属 Pitch 演示文稿与投标建议书。
