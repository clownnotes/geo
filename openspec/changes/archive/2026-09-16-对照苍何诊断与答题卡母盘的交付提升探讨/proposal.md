# Proposal: 对照苍何诊断与答题卡母盘的交付提升探讨

## Why

外部「苍何」偏短时诊断报告；产品口述 8 步是交付运营闭环。我方已有 0～5 步，但名词（母盘/关键词/文章）、选词与首次发文口径、侧栏「首次 vs 维护」、诊断快报/深化分档等需先在 **OpenSpec 本变更**里定稿，避免散落旁路文档造成歧义。

## What Changes

- **规范真源仅本目录**：`design.md`（已定共识）+ `review-log.md` + `prompts/diag-deepen-report-ide.md`  
- **已落地代码**：管理台侧栏改为「首次交付 + 日常/经营/监管/发帖运维」（`web/index.html`）  
- **清理**：删除本轮误建在 `docs/specs/`、`docs/strategy/geo-flow-benchmark-canghe.md` 的旁路文件；SOP/roadmap 改引用本 OpenSpec  
- **不在本变更强做**：深化报告管理台按钮、词确认门闩产品化（见 design §G）

## Capabilities

### New / Clarified

- 母盘·关键词·文章名词与两套体系  
- 首次头条+知乎各一篇；词清单维护期继续  
- 侧栏 IA；发帖运维入口  
- ①快报 + 可选②深化（IDE 提示词）

### Out of scope here

- 实现完整 AIVO HTML 流水线  
- 虚拟提及率当实测卖给客户（禁止）

## Impact

- OpenSpec 本目录 = 唯一探讨真源  
- `web/index.html` 导航  
- `docs/sop/04|05|delivery-sop`、`roadmap-2026` 交叉引用改为指向本 design  
- 删除旁路 specs 文件（见 tasks）
