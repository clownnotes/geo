# Tasks: 开发者与写文同事双轨视界彻底解耦与全阶段白盒流水线复原

- [x] 1. 全局 RBAC UI 收口 <!-- id: 1 -->
  - [x] 1.1 `applyRbacUi()` 增加 `[data-geo-writer-only]`：开发者隐藏、写文显示；勿挂在 `.home-panel` 根上
  - [x] 1.2 `getStep0BridgeProps()` 增加 `isDeveloper: () => isDeveloper()`（或布尔快照 + 登录后 remount）

- [x] 2. 阶段 00 双轨 <!-- id: 2 -->
  - [x] 2.1 `web/step0-src`：恢复开发者 Cursor / 反重力 / 落盘卡片；`v-if="isDeveloper"`；写文仍只见手工三步
  - [x] 2.2 取消 `copyCursorPrompt` / `copyAntigravity*` / `copyPreviewForIde` 的 toast 空壳，恢复真实复制（仅开发者入口能点到）
  - [x] 2.3 执行 `npm run build:step0`，提交更新后的 `web/assets/step0/step0.js`

- [x] 3. 阶段 01 双轨 <!-- id: 3 -->
  - [x] 3.1 开发者：复原老板版/工程师版 4 步 UI，挂 `data-geo-dev-only`。标题保持「老板决策版」，不要改成「开发者白盒版」
  - [x] 3.1a 工程师版：补回 ② 按钮组缺失的 `</div>`，让 ③④ 和 ①② 平级（现在 ③④ 被塞进 ② 的盒子里，开发者界面被挤坏）
  - [x] 3.2 恢复 `copyBossAuditToIde` / `copyStep1AuditToIde` / `copyDiagDeepenPrompt` 真实请求与剪贴板（对接已有开发者路由）
  - [x] 3.3 写文：隐藏 `#tab-audit-top-tech`；新增主按钮「用小毛驴写商业诊断」（`data-geo-writer-only`）
  - [x] 3.4 实现 `runWriterStep1AiGenerate`：共用 `isAuditRunning`；无摸底则提示；无 metrics 先 `crawl` 再 `interpret`；禁止只打 `interpret`
  - [x] 3.5 文案白话，不写死「5~8 秒」
  - [x] 3.6 `switchAuditTopTab` 替换 `className` 之后再调用 `applyRbacUi()`。写文同事一键成功会切回老板版，不能把工程师页签的 `hidden` 冲掉
  - [x] 3.7 `runWriterStep1AiGenerate`：上锁必须在「查摸底」那个 `await` 之前；没摸底、失败都在 `finally` 里开锁

- [x] 4. 阶段 02 / 03 补洞 <!-- id: 4 -->
  - [x] 4.1 `:910` 导出源码包按钮补 `data-geo-dev-only`
  - [x] 4.2 `:1101` 复制 9 因子全文补 `data-geo-dev-only`

- [x] 5. 阶段 04 双轨 <!-- id: 5 -->
  - [x] 5.1 恢复 IDE 工地 DOM（改写包 + 写回口令），`data-geo-dev-only`
  - [x] 5.2 恢复 `copyIdeRewritePack` / `copyWritebackCommand` 真实实现
  - [x] 5.3 写文网页闭环保持可用；与 IDE 卡互斥

- [x] 6. 阶段 05 <!-- id: 6 -->
  - [x] 6.1 ROI 看板根节点（约 `:1555`）整块 `data-geo-dev-only`
  - [x] 6.2 确认全套 ZIP 仍 `data-geo-dev-only`；**不**改 `/roi/calculate` 权限档

- [x] 7. 回归测试 <!-- id: 7 -->
  - [x] 7.1 新增 `tests/test_dual_track_perspectives.py`（静态属性 + 关键路由 403/200，见 design 第五节）
  - [x] 7.2 本地跑相关用例全绿后停步，等人验收；不归档、不推生产
