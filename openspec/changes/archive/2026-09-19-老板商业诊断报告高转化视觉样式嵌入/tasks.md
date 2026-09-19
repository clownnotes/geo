# 细分任务清单：老板商业诊断报告高转化视觉样式嵌入

- [x] 1. 前端 DOM 结构与容器重构 (`web/index.html`)
  - [x] 1.1 在【老板商业转化版】交付物标题栏注入双样式切换分段器：`[高转化视觉版 (HTML)]` 与 `[文本底稿 (MD)]`
  - [x] 1.2 在右侧工具栏增加【全屏大屏】快捷图标
  - [x] 1.3 在内容区域新增沙箱隔离容器 `#container-step-1-boss-visual` 及其嵌入的 `iframe`，默认展示视觉版，纯文本容器设为隐藏
- [x] 2. 前端 JS 交互与数据刷新联动 (`web/index.html`)
  - [x] 2.1 增加 `currentBossReportStyle` 状态，实现 `switchBossReportStyle(style)` 切换高亮与容器显示隐藏
  - [x] 2.2 实现 `loadBossReportVisual(forceReload)` 加载/刷新大屏 HTML
  - [x] 2.3 实现 `openBossReportFullscreen()` 新标签页全屏展示
  - [x] 2.4 在 `loadStepPreviews()` 与 `runStep1Audit` 成功回调中联动刷新视觉版大屏
- [x] 3. 自动化回归测试与规范核对
  - [x] 3.1 补充自动化测试 `tests/test_boss_visual_style_embed.py`，核验 DOM 结构、切换函数与 0 Emoji 商业红线
  - [x] 3.2 运行全量测试套件确保 100% 通过（OK）
  - [x] 3.3 本地启动 `:8088`，在页面上人工校验高转化浅紫微流光大屏渲染与样式切换
