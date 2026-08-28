---
name: opsx
description: OpenSpec 核心工作流总入口（支持 propose, review, apply, status, archive）
---

# OpenSpec 统一入口

当用户输入 `/opsx` 时：
1. 检查当前工作区是否有正在进行的变更目录（`openspec/changes/`）。
2. 如果有进行中的变更，展示当前任务状态与 `tasks.md` 进度（类似于 status）。
3. 询问用户下一步操作：
   - 📝 **创建新需求**（执行 propose）
   - 🔍 **跨 IDE 审查**（执行 review）
   - 💻 **继续编写代码**（执行 apply）
   - 📦 **验收归档**（执行 archive）
