# Tasks: 多版本生成采纳与草稿废纸篓安全回档

## 1. 准备与规范核对

- [ ] 1.1 核对 `AGENTS.md §3.3`（文案杜绝彩色 Emoji）、`§3.5`（克制视觉）、`§4.5`（本地零编译，打包构建必须在 NE1 服务器）。
- [ ] 1.2 确认修改涉及的核心文件：`StudioFileTree.vue`、`stage1Config.js`、`useStep1.js`、`Step1App.vue`、`StudioEditor.vue`。

## 2. 前端组件与业务逻辑编码

- [ ] 2.1 改造左栏资源管理器组件 `GEO/web/step0-src/components/studio/StudioFileTree.vue`：
  - 完善草稿（未采纳）文件的删除触发按钮（Lucide `trash-2` 图标，hover 时浮现），派发 `deleteFile` 事件；
  - 保护已采纳文件，不展示删除按钮；
  - 底部新增【已归档 / 废纸篓】折叠抽屉，汇总展示所有 `is_deleted` 文件并提供【恢复】按钮（Lucide `rotate-ccw` 图标），派发 `restoreFile` 事件。
- [ ] 2.2 扩展阶段一配置字典 `GEO/web/step0-src/stage1Config.js`：
  - 为初始生成的 6 个核心文件注入默认属性：`isActive: true`、`versionTag: 'V1'`、`is_deleted: false` 以及格式化生成时间戳。
- [ ] 2.3 升级阶段一业务逻辑 `GEO/web/step0-src/useStep1.js`：
  - 实现 `handleDeleteFile(filename)`：对未采纳草稿标记 `is_deleted = true`，平滑切换选中文件并调用 `saveState()`；
  - 实现 `handleRestoreFile(filename)`：将废纸篓文件标记 `is_deleted = false`，恢复至主列表并调用 `saveState()`；
  - 实现 `handleAdoptFile(filename)`：将候选版本升格为 `isActive = true`，同类旧底牌退回为草稿；
  - 重新抓取时注入最新生成时间戳；
  - 在 `return` 对象中导出新方法供外部调用。
- [ ] 2.4 改造胶水层与中栏组件 (`Step1App.vue` & `StudioEditor.vue`)：
  - `Step1App.vue` 绑定 `<StudioFileTree>` 的 `delete-file` 与 `restore-file` 事件；
  - 中栏编辑器展示文件生成时间戳与版本号，针对草稿文件展示【采纳该版本为生效底牌】动作按钮。
- [ ] 2.5 文案与代码 Emoji 规整自检：检索改动文件，确保不引入任何彩色 Emoji 表情。

## 3. 构建与端到端真机验收

- [ ] 3.1 跨端构建（严格遵守 `AGENTS.md §4.5`）：在 NE1 服务器执行仓库根构建命令 `npm run build:step0`，产物写入 `web/assets/step0/` 并由 `stamp-build.mjs` 打版本戳。
- [ ] 3.2 运行端到端冒烟测试（`npm run smoke:step0`），确保 4/4 项全部 PASS。
- [ ] 3.3 浏览器真机验证（NE1 开发环境 8088 端口 · 人工浏览器验收项，AI 不得代勾）：
  - 观察草稿文件 hover 出现删除垃圾桶图标，点击成功移入废纸篓；
  - 观察已采纳文件受到强制保护，不出现删除按钮；
  - 观察左栏底部的【已归档 / 废纸篓】抽屉展开展示被删文件，点击【恢复】一键原位复原；
  - 观察中栏顶部清晰展示生成时间戳与版本信息；
  - 观察刷新页面后，采纳标记、时间戳与废纸篓状态 100% 保持。
