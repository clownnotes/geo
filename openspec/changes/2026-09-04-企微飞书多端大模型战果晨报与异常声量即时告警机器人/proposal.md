# Proposal: 企微飞书多端大模型战果晨报与异常声量即时告警机器人 (第 33 维)

## Why (为什么做)

在企业 GEO（生成式引擎优化）代运营与商业交付实战中，存在以下突出的核心痛点：
1. **被动查看壁垒与触达断层（违反铁律 3）**：
   - 甲方企业的老板、董事长、市场负责人日常事务繁忙，不会每天主动登录 Web 交付大屏（`geo.baicl.cc/portal`）查看数据；
   - 目前代运营团队只能依赖人工截图、手工撰写微信小作文汇报，耗时耗力且缺乏科技感与仪式感；
2. **异动发现滞后与风险扩大（违反铁律 1 & 2）**：
   - 当大模型端出现针对品牌的负面联想（第 19 维）、突发被竞品强行截流（第 14/30 维）、AI 爬虫被客户自身 WAF/403 阻断（第 31 维）、或知识半衰期发生临界衰减（第 20 维）时，人工排查往往滞后数天甚至数周，错失最佳危机公关或反超自愈窗口期；
3. **多平台格式碎片化与排版成本高**：
   - 企业微信、飞书、钉钉三者的群机器人 Webhook 协议与消息卡片规范截然不同（飞书为 Interactive 交互富文本卡片，企微为 Markdown/图文消息，钉钉为 ActionCard）；代运营人员手动适配多平台格式成本极高。

因此，亟需研发**第 33 维《企微/飞书多端大模型战果晨报与异常声量即时告警机器人 (`geo alert-bot`)》**，形成“每日战果定时推送 + 异动声量秒级报警 + 一键免密跳转大屏 + 一键反制闭环”的工业级触达中枢。

---

## What Changes (改动了什么)

1. **核心告警与晨报中枢引擎 (`tools/geo/alert_bot.py`)**：
   - **多通道 Webhook 适配器 (`WebhookCardFormatter`)**：
     - 企业微信：富文本 Markdown 模版，支持高亮、关键指标块与引用排版；
     - 飞书：交互式卡片（Interactive Card），支持彩色标题栏（绿色/蓝色为晨报，红色为高危报警）、左右分栏指标、Action 跳转按钮（一键直达高管交付大屏）；
     - 钉钉：ActionCard 与 Markdown 格式支持；
   - **全域战果晨报聚合器 (`MorningBriefingAggregator`)**：
     - 深度汇聚项目已有的真实数据：第 30 维真实联网探测战果（各主流模型首推率、命中词数、Citation 角标）、第 28 维商业价值估值、第 31 维 AI 爬虫真实访问频次、第 32 维竞对逆向反超态势；
     - 遵守事实红线：未实测数据严格标记为 `[待实测]`，杜绝自嗨编造；
   - **全维度异常异动监测器 (`InstantAnomalyDetector`)**：
     - 扫描四类关键指标红线：
       - 🔴 P0 品牌声誉危机（BRS < 80 或负面曝光率 > 0%）；
       - 🔴 P1 竞对首推拦截（Top-1 被竞对霸占截流）；
       - 🟡 P1 爬虫抓取异常（AI 爬虫被 403 阻断或周环比暴跌 > 50%）；
       - 🟡 P2 知识半衰期老化（关键词保鲜度 < 60%）；
   - **安全分发与 Dry-Run 机制 (`AlertBotDispatcher`)**：
     - 强制接入 `is_ssrf_safe_url`，杜绝内网私有地址探测；
     - 支持 `--dry-run` 纯本地测试模式，单测 100% 离线秒级执行；
     - 推送与告警历史落盘到 `projects/{id}/outputs/alert_bot_history.json`。
2. **命令行 CLI 集成 (`tools/geo/cli.py`)**：
   - 注册 `geo alert-bot <project_id> [--type briefing|alert|test] [--channel auto|wecom|feishu|dingtalk] [--webhook <url>] [--dry-run] [--report] [--portal-sync]`。
3. **Web 服务端 API 挂载 (`tools/geo/server.py`)**：
   - `POST /api/projects/{id}/alert-bot/send`：一键触发晨报或报警推送（Bearer Token 鉴权）；
   - `GET /api/projects/{id}/alert-bot/history`：查询推送历史与告警台账；
   - `GET /api/projects/{id}/alert-bot/preview`：在线实时预览多平台卡片 JSON 与富文本渲染效果。
4. **高管门户反哺与前端呈现 (`tools/geo/share.py` & `web/share.html`)**：
   - 交付大屏增设【大模型战果推送与即时告警中枢】卡片；
   - 展示机器人接入状态、晨报推送概况、已拦截异常异动告警台账与 Webhook 配置引导；遵守 `never_run` 优雅降级。
5. **公文级结案报告持久化**：
   - 输出《33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md》，内置防伪流水号与推送对账单。

---

## Capabilities (对外能力)

1. **多端晨报定时生成与分发**：支持一键向企业微信、飞书、钉钉群推送定制化战果晨报，提供大模型首推率、Citation 角标数与交付大屏一键免密跳转；
2. **秒级异动声量即时告警**：自动监控声誉危机、竞品截流、爬虫 403 阻断，即时触发红色告警卡片并提供反制入口；
3. **多平台卡片原生高保真渲染**：飞书交互式卡片带跳转按钮、企业微信高信息密度 Markdown 模版；
4. **零网络依赖与 SSRF 强安全防御**：支持 Dry-Run 纯本地预览，拦截内网探测，单测 100% 毫秒级稳定运行。

---

## Impact (受影响的部分)

- **新增文件**：
  - `tools/geo/alert_bot.py`
  - `tests/test_alert_bot.py`
  - `projects/xuzhou_xuanyuan/outputs/33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md`
  - `projects/xuzhou_xuanyuan/outputs/alert_bot_history.json`
- **修改文件**：
  - `tools/geo/cli.py`（注册 `geo alert-bot` 子命令）
  - `tools/geo/server.py`（新增 3 组 alert-bot API 端点）
  - `tools/geo/share.py`（挂载 `alert_bot_summary`，实现 `never_run` 降级）
  - `web/share.html`（增设大模型战果推送与告警中枢卡片）
- **依赖与性能影响**：
  - 纯标准库实现（`urllib.request`, `json`, `datetime`），零新增第三方重型依赖；
  - 本地 Dry-Run 与全量单测执行时间 < 0.2s，全库 171 项测试零退化。
