---
name: opsx-review
description: 跨 IDE 联合代码审查与设计核对（对照 RULES/Specs 审查活动变更并在 review-log.md 输出结论）
---

# OpenSpec Review 审查流程

当用户触发此技能时，作为 Reviewer（审查者）执行：
1. 查找当前活动变更目录：`openspec/changes/<当前活动变更>/`。
2. 读取该变更下的 `proposal.md`、`design.md`、`tasks.md`，并对照全局规则（`RULES.md` / `AGENTS.md` / `复用索引`）。
3. 检查代码改动（Git Diff）或方案是否存在：
   - 🔴 违反规则（如自增 ID、软删除漏过滤、面条代码、破坏现有业务）
   - 🟡 性能或架构风险
   - 🟢 代码优化建议
4. 向 `review-log.md` 追加格式化审查记录，并给出明确结论：`[通过]`、`[需修正]`、`[待讨论]` 或 `[已达成共识]`。
