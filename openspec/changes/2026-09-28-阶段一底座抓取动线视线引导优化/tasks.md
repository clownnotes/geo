# Tasks: 阶段一官网底座真机探测与中栏数据实时落盘闭环

## 1. 准备与规范核对

- [x] 1.1 核对 `AGENTS.md §3.3`（文案杜绝彩色 Emoji）、`§3.5`（克制视觉）、`§4.5`（本地零编译，打包构建必须在 NE1 服务器）。
- [x] 1.2 确认修改涉及的核心文件：`tools/geo/server.py`、`stage1Config.js`、`useStep1.js`、`Step1App.vue`、`StudioSop.vue`。

## 2. 后端接口强化与前端端到端编码

- [x] 2.1 强化 `GEO/tools/geo/server.py`：在 `/api/projects/{id}/run/audit` 响应中透传 `metrics: ares.get('metrics')`，确保前端能直接获取结构化抓取结果。
- [x] 2.2 扩展 `GEO/web/step0-src/stage1Config.js`：实现 `buildCrawledMetricsMarkdown(ctx, metrics)` 格式化函数，将真抓数据（连通状态、/llms.txt、/robots.txt、Schema、SSR、技术底座分）格式化为专业企业级 Markdown 文本。
- [x] 2.3 改造 `GEO/web/step0-src/useStep1.js`：
  - 头部补充 import 导入 `buildCrawledMetricsMarkdown`，防运行时 ReferenceError；
  - 新增 `isCrawling` 响应式状态并对外导出；
  - 改造 `handleAction('crawlMetrics')`，真正通过 `fetch` 调用 `/api/projects/{id}/run/audit`；
  - 抓取成功后将返回的真实 metrics 格式化并覆盖更新至 `files['01_网络底座指标_待对照.md'].content`；
  - 同步触发本地持久化 `saveState()`，并升级提示指引下方主按钮。
- [x] 2.4 改造 `GEO/web/step0-src/components/studio/StudioSop.vue`：
  - 新增 `props.actionLoadingMap`（默认 `{}`）；
  - 动作按钮在抓取中展示 `loader-2` 转圈图标、禁用点击并展示“正在探测官网底座…”。
- [x] 2.5 补齐胶水层连接 `GEO/web/step0-src/Step1App.vue`：
  - 从 `useStep1()` 解构出 `isCrawling`；
  - 在 `<StudioSop>` 标签上绑定 `:action-loading-map="{ crawlMetrics: isCrawling }"`。
- [x] 2.6 文案与代码 Emoji 规整自检：检索改动文件，确保不引入任何彩色 Emoji 表情。

## 3. 构建与端到端真机验收

- [x] 3.1 跨端构建（严格遵守 `AGENTS.md §4.5`）：在 NE1 服务器执行仓库根构建命令 `npm run build:step0`，产物写入 `web/assets/step0/` 并由 `stamp-build.mjs` 打版本戳。
- [x] 3.2 运行端到端冒烟测试（`npm run smoke:step0`），确保 4/4 项全部 PASS（注意冒烟第 1 步会重建并生成最终生效版本戳，验收以末次戳为准）。
- [ ] 3.3 浏览器真机验证（NE1 开发环境 8088 端口 · 人工浏览器验收项，AI 不得代勾）：
  - 点击“真抓网络底座指标”；
  - 观察按钮出现转圈动画与“正在探测官网底座…”；
  - 观察 Network 面板确实向 `/api/projects/.../run/audit` 发送了 POST 请求；
  - 观察中栏编辑器内容**实时刷新为真实探测出的客观技术指标**；
  - 观察服务端 `projects/{id}/outputs/audit_metrics.json` 实体文件真实落盘；
  - 观察按钮变为浅绿“已抓取真实指标”且下方推进大按钮呼吸高亮。
