# Tasks: 企微飞书多端大模型战果晨报与异常声量即时告警机器人 (第 33 维)

## Phase 1: 核心聚合与多端卡片引擎 (`tools/geo/alert_bot.py`)
- [x] 1.1 创建 `tools/geo/alert_bot.py` 基础框架，集成 SSRF 防护（复用 `is_ssrf_safe_url`）与 Webhook 调度器 `AlertBotDispatcher`，支持 `--dry-run` 纯本地执行。
- [x] 1.2 实现战果晨报数据聚合器 `MorningBriefingAggregator`，读取 30/31/32/19/20/28 真实资产，严格执行事实红线（未实测数据标注 `[待实测]`）。
- [x] 1.3 实现多维度异动告警检测器 `InstantAnomalyDetector`，支持 P0 声誉危机、P1 竞品首推截流、P1 爬虫 403/断崖、P2 知识衰减告警挖掘。
- [x] 1.4 实现多端原生 Webhook 卡片格式化器 `WebhookCardFormatter`，支持企微 Markdown、飞书 Interactive 卡片（带按钮与状态色彩）与钉钉 ActionCard。

## Phase 2: 报告持久化、CLI 与服务端集成
- [x] 2.1 实现公文级结案报告《33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md》与 `alert_bot_history.json` 历史台账持久化输出。
- [x] 2.2 在 `tools/geo/cli.py` 注册 `geo alert-bot <project_id> [--type briefing|alert|test] [--channel auto|wecom|feishu|dingtalk] [--webhook <url>] [--dry-run] [--report] [--portal-sync]`。
- [x] 2.3 在 `tools/geo/server.py` 挂载 `POST /api/projects/{id}/alert-bot/send`、`GET .../history`、`GET .../preview` 接口与 Bearer Token 强鉴权。

## Phase 3: 高管交付门户战果反哺与大屏呈现
- [x] 3.1 在 `tools/geo/share.py` 的 `compile_portal_data()` 中接入 `alert_bot_summary`，严格实施 `never_run` 优雅降级契约。
- [x] 3.2 在 `web/share.html` 中增设【大模型战果推送与即时告警中枢】卡片，展示机器人接入状态、推送记录与异动告警日志。

## Phase 4: 全栈单元测试、跨端审查与交付闭环
- [x] 4.1 编写完整单元测试 `tests/test_alert_bot.py`，覆盖 SSRF 拦截、多平台模板渲染、数据聚合事实红线、异动检测、CLI 与 API 鉴权、门户降级（100% 离线零公网网络依赖）。
- [x] 4.2 运行项目全量单元测试（全库 179 项），确保 100% 秒绿通过（耗时 < 4.5s）。
- [x] 4.3 跨 IDE 审查协同与 `review-log.md` 审核记录更新与放行。
