---
name: opsx-propose
description: 使用 OpenSpec 创建新功能需求提案（生成 proposal.md、design.md、tasks.md 与 review-log.md）
---

# OpenSpec Propose 流程

当用户触发此技能时，执行以下步骤：
1. 询问或提取用户要开发的需求名称（中文）。
2. 在项目根目录下执行 `./opsx propose <需求名称>`（或 `python3 scripts/opsx.py propose <需求名称>`）。
3. 引导用户或根据上下文自动填充：
   - `proposal.md`：背景痛点（Why）、改动内容（What）、对外能力（Capabilities）、影响范围（Impact）
   - `design.md`：架构对象、前后端接口与数据库 Schema
   - `tasks.md`：细分的开发与验证任务清单
4. 提示用户可以通过另一个 IDE 进行跨端审查（Review），或向 `review-log.md` 输出意见。
