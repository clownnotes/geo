# Tasks: 阶段五真机实测提问词复制与搜索结果回填解析

- [x] 1. 后端语义解析与持久化引擎 (`tools/geo/monitor.py`)
  - [x] 1.1 抽象公共回答解析函数 `parse_probe_text(content, client_name, brand_name, competitors)`：
    - 实现纯文本清洗与 HTML 剥离；
    - 实现多格式位次识别（列表序号、表格列、首推关键词匹配）；
    - 实现竞品拦截分析（兼容字符串与字典竞品数据）；
    - 实现 URL 与中文脚注信源提取（支持“知乎/今日头条/微信/GitHub”等域名映射与加权）。
  - [x] 1.2 实现真机数据持久化与周报动态合并函数 `ingest_manual_probe_result(project_id, keyword, model, content, notes)`：
    - 入参校验：`model` 属于 `deepseek|doubao|yuanbao|kimi`，`content` 严格限制 <= 100KB；
    - 持久化写入 `outputs/05_manual_probes.json`；
    - 动态更新《`05_企业AI可见度与声量追踪周报.md`》（标注 `[真机实测]` 文本 Tag，严禁 Emoji）；
    - 重新计算并返回与 `/monitor/metrics` 结构 100% 对齐的 `metrics` 字典。
  - [x] 1.3 实现 `get_project_monitor_prompts(project_id)`：
    - 读取项目词库与实体配置，为 DeepSeek（技术评测）、豆包（场景推荐）、元宝（微信私域）、Kimi（长研报）分别生成定制 Prompt；
    - 附带各平台直达链接与免登录无痕访问指引。
  - [x] 1.4 **全量探测回灌铁律**：
    - 改造 `run_monitor`，在周报输出前必须先加载 `outputs/05_manual_probes.json`；
    - 执行多源合并（同一 `keyword + model` 优先级：真机实测 > 实时 API 探测 > 离线基准估算），保证重新执行监测绝不冲掉已录入的真机验收数据。

- [x] 2. 后端 REST API 路由打通 (`tools/geo/server.py`)
  - [x] 2.1 新增 `GET /api/projects/{id}/monitor/prompts` 路由：鉴权校验，返回平台列表与各关键词定制提问词。
  - [x] 2.2 新增 `POST /api/projects/{id}/monitor/manual-ingest` 路由：校验 Bearer Token、请求参数与 content 体积，调用 `ingest_manual_probe_result` 并返回 `parsed` 与 `metrics`。

- [x] 3. 前端交互组件与大盘联动 (`web/index.html`)
  - [x] 3.1 阶段五控制栏新增入口：在 `panel-step-5-acceptance` 顶部操作栏增加「真机实测回填」按钮（使用 Lucide `clipboard-check` 图标，0 Emoji，企业级微边框风格）。
  - [x] 3.2 构建「真机无痕实测与回填助手」双栏模态弹窗：
    - 左栏：词库即时搜索过滤、高频前 30 项截断、平台 Tab 切页、定制 Prompt 展示、一键复制（含 1.5s 状态切换）、免登录打开平台（`target="_blank" rel="noopener noreferrer"`）；
    - 右栏：平台与关键词联动选择器、回答文本粘贴区、字符数实时统计、清空与示例填充、提交解析按钮（带 loading 状态）。
  - [x] 3.3 数据闭环与大盘联动：
    - 提交成功后弹出 Toast 提示位次；
    - 立即调用 `loadMonitorDashboardMetrics()` 动态刷新主大盘 4 维量化指标卡、信源分布条形图与商业 ROI 价值看板。

- [x] 4. 自动化测试与交付验证
  - [x] 4.1 编写单元测试脚本 `tests/test_manual_probe_ingest.py`：
    - 验证包含 DeepSeek / 豆包网页真实文本（含 HTML 标签、多行序号、无 URL 中文脚注）的解析正确性；
    - 验证 `ingest_manual_probe_result` 对 `05_manual_probes.json` 的持久化与周报合并；
    - 验证 `run_monitor` 重新执行后对真机实测行的完整保留与优先级回灌；
    - 验证 100KB 超限与非法 model 校验。
  - [x] 4.2 本地 8088 页面端到端闭环验证：在未配置 API Key 的环境下，通过复制 Prompt ➔ 回填回答 ➔ 解析录入 ➔ 驱动指标大盘与周报全部点亮。
