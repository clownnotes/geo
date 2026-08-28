---
name: opsx-apply
description: 按照 OpenSpec 的 tasks.md 任务清单逐项执行编码与开发
---

# OpenSpec Apply 执行流程

当用户触发此技能时，作为 Coder（执行开发者）：
1. 查找当前活动变更目录：`openspec/changes/<当前活动变更>/`。
2. 读取 `tasks.md`，确认前置审核记录 `review-log.md` 是否已为 `[通过]` 或 `[已达成共识]`。
3. 按照 `tasks.md` 中的未完成项（`- [ ]`）顺序编码实现。
4. 每完成一个子任务，更新 `tasks.md` 为已完成（`- [x]`）。
5. 编码完成后运行测试或验证，并提醒师弟进行功能验收。
