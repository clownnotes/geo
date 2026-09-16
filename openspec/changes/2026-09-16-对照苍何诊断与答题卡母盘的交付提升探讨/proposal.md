# Proposal: 对照苍何诊断与答题卡母盘的交付提升探讨

## Why

外部「苍何」流程擅长**短时诊断报告**；产品口述 8 步覆盖**从信息到月验**的运营闭环。我们已有 0～5 步工程交付，但在名词（答题卡/母盘）、选词确认、建库门闩、双站边界、月度采样协议、诊断报告形态、舆情与「虚拟数据标注」上仍有可提升点。需要先把对照结论写进规范与欠账，**探讨拍板后再决定做哪些**。

## What Changes

- 新增对照真源：`docs/strategy/geo-flow-benchmark-canghe.md`
- 新增名词尺子：`docs/specs/answer-card-vs-master.md`（母盘 vs 答题卡）
- 在 `docs/strategy/roadmap-2026.md` 挂 U1～U10 提升欠账（与对照文档同编号）
- 轻量修订 SOP/交付手册中与 U2/U3/U5/U7 相关的「应写清」条文（探讨共识后落笔；本变更以规范探讨为主，**默认不改管理台大功能**）
- **不在本变更**：实现 AIVO 级 HTML 诊断产品、上线月度 100 次自动采样器（除非探讨后另开 apply）

## Capabilities

### New Capabilities

- `geo-flow-benchmark`: 外部流程对照与提升条目台账（探讨用）
- `answer-card-master-glossary`: 答题卡/母盘定义与硬规则

### Modified Capabilities

- `delivery-five-steps`: 明确与口述 8 步、诊断报告的缺口映射（文档层）

## Impact

- 文档：strategy / specs /（可选）sop-01、05、delivery-sop
- 代码：本变更默认不动；链接检查诚实文案已在前序落地（U10）
- 风险：若把「虚拟诊断」当实测卖给客户会翻车 → U7 必须先于任何模拟提及率产品化
