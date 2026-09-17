# Review Log: 管理台阶段零 Vue3 组件岛

## 2026-09-17 Cursor（propose）

- **来源**：产品确认大单页易错；小毛驴前端已 Vue3；拍板「先拆最痛的阶段零小岛，再继续改功能」；前序 `创建与阶段零先探活再长问选题` 已归档（细测后续补）。
- **已写入**：`proposal.md`（绞杀式只迁 step0）/ `design.md`（Vite+Vue3、挂载桥、假丢数据护栏、产物放 `web/assets/step0/`）/ `tasks.md`。
- **请审**：
  1. 是否同意 **只迁阶段零**，其余步骤暂留 HTML？
  2. 构建产物路径 `web/assets/step0/` 是否可接受（少改 server）？
  3. 壳↔岛桥用 `window.__GEO_STEP0__` 是否可接受（后续可再收紧）？
- 状态：`[待讨论]` — 确认前不 apply；请产品或其他 IDE 在本日志回复。
