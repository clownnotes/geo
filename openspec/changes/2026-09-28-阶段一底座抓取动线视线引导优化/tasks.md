# Tasks: 阶段一底座抓取动线视线引导优化

## 1. 准备与规范核对

- [ ] 1.1 核对 `AGENTS.md §3.3`（文案杜绝彩色 Emoji）、`§3.5`（克制视觉）、`§4.5`（本地零编译，打包构建必须在 NE1 服务器）。
- [ ] 1.2 确认修改涉及的 4 个关键源文件：`stage1Config.js`、`useStep1.js`、`Step1App.vue`、`StudioSop.vue`。

## 2. 代码开发与状态串联

- [ ] 2.1 扩展 `GEO/web/step0-src/stage1Config.js`：在 Step 1 动作定义中配置 `completedLabel: '已抓取真实指标 (点击重新抓取)'`。
- [ ] 2.2 改造 `GEO/web/step0-src/useStep1.js`：
  - 新增 `crawledMetrics` 响应式状态（读取 `savedState?.crawledMetrics || false`）；
  - 在 `saveState()` 中将 `crawledMetrics: crawledMetrics.value` 写入真实存储键 `` `geo_step1_state_${clientId}` ``；
  - 在 `handleAction('crawlMetrics')` 中置 `crawledMetrics.value = true` 并触发保存；
  - 升级 Toast 文案为“已完成抓取：真实底座指标已就绪！请核对中栏数据，确认无误后点击下方【前往出具初稿】”（杜绝彩色 Emoji）。
- [ ] 2.3 改造 `GEO/web/step0-src/components/studio/StudioSop.vue`：
  - 新增 `props.actionCompletedMap` 属性（默认 `{}`）；
  - 实现防污染核心函数 `isActionDone(type)` 与 `shouldHighlightProceed(step, idx)`；
  - 动作按钮按完成态展示浅绿背景 `bg-emerald-50 text-emerald-700 border-emerald-200` 与 `check-circle` 图标；
  - 主推进按钮上方增加静态提示，并为主按钮追加 `animate-pulse ring-2 ring-[#7c5bf5]/40` 呼吸高亮（杜绝 `animate-bounce` 弹跳）。
- [ ] 2.4 补齐胶水层连接 `GEO/web/step0-src/Step1App.vue`：
  - 从 `useStep1()` 解构出 `crawledMetrics`；
  - 在 `<StudioSop>` 标签上绑定 `:action-completed-map="{ crawlMetrics: crawledMetrics }"`。
- [ ] 2.5 文案与代码 Emoji 规整自检：检索改动文件，确保不引入任何彩色 Emoji 表情。

## 3. 构建与端到端真机验收

- [ ] 3.1 跨端构建（严格遵守 `AGENTS.md §4.5`）：在 NE1 服务器执行仓库根构建命令 `npm run build:step0`，产物写入 `web/assets/step0/` 并由 `stamp-build.mjs` 打版本戳。
- [ ] 3.2 浏览器真机验证（NE1 开发环境 8088 端口）：
  - 进入阶段一第 1 步；
  - 点击“真抓网络底座指标”；
  - 检查右上角 Toast 文案正确、无 Emoji；
  - 检查按钮文字自动变为“已抓取真实指标 (点击重新抓取)”并呈浅绿完成态；
  - 检查下方主按钮【确认完成，前往出具初稿】呈现呼吸高亮并有静态引导文字；
  - 刷新浏览器，确认已抓取状态与动线高亮成功保持（localStorage 持久化生效）；
  - 检查阶段 0 / 阶段 2 / 阶段 3 动线无任何异常与样式污染。
