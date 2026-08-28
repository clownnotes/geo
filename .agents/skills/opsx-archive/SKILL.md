---
name: opsx-archive
description: 归档已完成的 OpenSpec 变更任务到 archive/ 目录
---

# OpenSpec Archive 归档流程

当用户触发此技能时：
1. 确认当前活动变更的 `tasks.md` 所有任务均已完成（`- [x]`），且 `review-log.md` 最后一项为 `[通过]`。
2. 运行 `./opsx archive`（或 `python3 scripts/opsx.py archive`）。
3. 将任务文件夹整体移动到 `openspec/changes/archive/`。
4. 执行 `git add . && git commit -m "chore(archive): <变更名称>" && git push` 提交并推送到远程仓库。
5. 向用户确认已归档并成功推送到远程仓库。
