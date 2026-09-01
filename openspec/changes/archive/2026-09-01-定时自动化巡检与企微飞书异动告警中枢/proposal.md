# Proposal: 定时自动化巡检与企微/飞书异动告警中枢

## Why (为什么做 / 业务痛点)

1. **痛点：声量监测依赖人工手动触发，无法做到无人值守的主动代运营**
   - 当前 Step 5 监控周报需要运营人员每周手动点击或在 CLI 运行，当代运营企业客户达到 10~50 家时，人工操作容易遗漏；
   - 需要一个后台常驻/Cron 驱动的自动化巡检引擎，按周/按日自动遍历所有处于活跃期的客户项目，并发探测主流大模型（DeepSeek、豆包）。
2. **痛点：当竞品拦截或大模型声量断崖下跌时缺乏即时预警**
   - 如果某一周竞品发布了高权重内容，导致大模型在核心选型词中将我方挤出首推，交付团队难以及时知晓；
   - 需要支持配置企业微信群机器人（WeCom Webhook）或飞书群机器人（Feishu Webhook），一旦发现 **「SOV 跌破预警阈值（如 <50%）」** 或 **「发现新增竞品拦截词（Top 1 被竞品占领）」**，立即向运营群推送结构化的富文本告警卡片。
3. **沉淀历史趋势时序数据库 (SQLite)**
   - 自动将每次巡检的 SOV、各平台提及位次存入 `projects/<id>/history.db`，支持 Web 端展示多周环比声量折线趋势。

---

## What Changes (改动范围)

1. **研发自动化巡检与告警调度引擎 (`tools/geo/patrol.py`)**：
   - 实现全项目自动化遍历探测逻辑 `run_patrol_all(dry_run=False)`；
   - 实现 SQLite 历史声量时序库存储 `record_project_history(project_id, metrics)` 与 `get_project_history(project_id)`；
   - 实现企微 / 飞书 / 钉钉 Webhook 告警消息组装与发送器 `send_webhook_alert(webhook_url, alert_data)`。
2. **CLI 命令扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo patrol [--all] [--project ID] [--notify]` 子命令，方便系统 Crontab 挂载（如 `0 3 * * 1 geo patrol --all --notify`）。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/history`：获取指定项目的历史多周 SOV 环比数据；
   - `POST /api/patrol/trigger`：管理端手动触发全量/单项目异步巡检与告警测试；
   - `GET/POST /api/settings/notifications`：配置与测试全局企业微信/飞书 Webhook 地址与告警阈值。
4. **Web 交付工作台大盘升级 (`web/index.html`)**：
   - 在总览页顶部增加「⏰ 自动化巡检与告警状态」面板；
   - 在 Step 5 中增加「📈 多周声量环比趋势图」与「🔔 告警推送记录」；
   - 在系统右上角增加「⚙️ 告警通知设置」模态弹窗，支持配置 Webhook URL 并发送测试消息。
5. **SOP 知识库更新 (`docs/sop/05-monitor-sop.md`)**：
   - 将无人值守自动化巡检与异动告警处理规范写入 SOP-05。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/history`
- `POST /api/patrol/trigger`
- `GET /api/settings/notifications` & `POST /api/settings/notifications`
- CLI: `python3 -m tools.geo patrol [--all] [--project <id>] [--notify]`

---

## Impact (影响分析)

- **完全向后兼容**：现有项目无需做任何数据迁移，`history.db` 将在巡检时自动轻量创建；
- **实现真正的无人值守代运营**：从“客户催问效果”转变为“系统自动巡检、异常自动预警、周一早晨自动出报”，极大提升 GEO 代运营团队的专业度与人效。
