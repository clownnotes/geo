# Proposal: 阶段一官网底座真机探测与中栏数据实时落盘闭环

## Why (为什么做)
- **痛点现状**：在阶段一（01 诊断现状并出具报告）的第 1 步中，点击“真抓网络底座指标”按钮目前仅是纯前端 mock 假动作：点击后只是切换了 Tab 并弹出了一个 Toast 提示，根本没有向后台发送真实的探测请求。中间栏呈现的《01_网络底座指标_待对照.md》只是写死在 JS 代码里的静态字符串模板，没有真实抓取、没有数据更新、没有落盘到磁盘文件中。
- **业务诉求**：结合老赵哥的《AI看的sop.md》与既有真实 Python 抓取引擎（`tools/geo/audit.py`），给客户当面做商业诊断时，必须有实锤的“真实技术底座数据（5/5 达标项）”和“阶段零问答底牌（豆包首推率 0%、竞品截流账）”。因此必须彻底废弃假动作，端到端打通真抓取、真显中栏与真实文件落盘。

## What Changes (改动了什么)
1. **端到端真实调用**：点击“真抓网络底座指标”时，前端真正向后端发送 `POST /api/projects/{id}/run/audit` 请求（携带 `{ mode: "crawl" }` 参数），按钮显示 loading 加载中状态。
2. **后端真机网络探测**：后端 Python 执行 `run_audit_crawl(project_id)`，真实利用 HTTP/TLS 模块探测客户官网的连通性、根目录 `/llms.txt`、`/robots.txt` 本土 AI 爬虫（Bytespider/DeepSeekSpider）放行状态、Schema.org (JSON-LD) 结构化数据、SSR 渲染空壳检测与 DNS 双栈解析。
3. **真实文件落盘**：后端真实把抓取指标写入 `projects/{id}/outputs/audit_metrics.json`，并实时组装生成《01_企业底座技术体检审计报告.md》与《01_企业AI可见度商业诊断报告.md》。
4. **中栏真实数据实时回填**：抓取成功后，前端从后端获取最新的真实探测数据，实时覆盖更新中栏编辑器内的《01_网络底座指标_待对照.md》，让交付人员肉眼可见地看到客观抓取结果（真实响应状态码、大模型爬虫规则、技术健康分与告警项）。
5. **动线状态与视线引导闭环**：抓取完成后，动作按钮自动切换为浅绿色“已抓取真实指标 (点击重新抓取)”状态，下方的【确认完成，前往出具初稿】主推进按钮获得柔和呼吸微光晕引导，消除操作断层。

## Capabilities (对外能力)
- **官网技术底座实时探测能力（Live Website Audit Probing）**：支持毫秒级真机网络探测，客观量化 5 大技术底座指标与健康得分。
- **中栏在线资产动态刷新（Live Output Sync）**：真抓数据完成后即刻反哺回填至中栏工作区 Markdown 文件，实现“看得见的抓取”。
- **磁盘实体文件自动化落盘（Outputs Persistence）**：抓取结果与体检报告真实写入服务器硬盘，刷新页面依然保持。

## Impact (受影响的部分)
- `GEO/web/step0-src/stage1Config.js`：新增 `buildCrawledMetricsMarkdown(ctx, metrics)` 客观指标 Markdown 组装函数；
- `GEO/web/step0-src/useStep1.js`：改造 `handleAction('crawlMetrics')`，接入后端 `POST /api/projects/{id}/run/audit` 接口，增加 loading 状态管理与中栏内容动态刷新；
- `GEO/web/step0-src/Step1App.vue`：解构 `isCrawling` 并透传 `:action-loading-map` 至 `<StudioSop>`；
- `GEO/web/step0-src/components/studio/StudioSop.vue`：动作按钮支持 loading 加载中文案与转圈图标；
- `GEO/tools/geo/server.py`：确保 `/api/projects/{id}/run/audit` 接口在响应中返回详细的 `metrics` 字典与格式化报告摘要；
- 前后端协同严格遵循企业级规范，严禁引入任何彩色 Emoji 表情符号。
