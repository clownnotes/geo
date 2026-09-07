---
name: opsx-apply
description: 按照 OpenSpec 的 tasks.md 任务清单逐项执行编码与开发
---

# OpenSpec Apply 执行流程

当用户触发此技能时，作为 Coder（执行开发者）：
1. 查找当前活动变更目录：`openspec/changes/<当前活动变更>/`。
2. 读取 `tasks.md`，同时检查 `review-log.md` 中是否有对端 IDE 提出的修改意见（若有且尚未修复，优先纳入本次编码中解决）。
3. 按照 `tasks.md` 中的未完成项（`- [ ]`）及审查意见顺序编码实现。
4. 每完成一个子任务，更新 `tasks.md` 为已完成（`- [x]`）；若修复了审查意见，在 `review-log.md` 记录 `[已修正]`。
5. 编码完成后运行测试或验证，向用户汇报当前进度，等待用户验收。
6. **【重要边界约束】**：严禁在未获用户明确指示的情况下擅自执行 opsx-archive 归档！归档必须由用户显式触发。
