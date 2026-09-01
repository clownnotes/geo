## 1. 自动化巡检与历史数据库开发 (`tools/geo/patrol.py`)

- [x] 1.1 编写 SQLite 时序库初始化与持久化函数（`init_history_db` / `record_project_history` / `get_project_history`）。
- [x] 1.2 编写异动告警规则分析器（`check_alert_conditions`，支持 SOV 暴跌、竞品拦截、占位词失守识别）。
- [x] 1.3 编写企微 / 飞书 / 钉钉 Webhook 消息发送器（`send_webhook_alert`，支持 Markdown 卡片与富文本格式）。
- [x] 1.4 实现单项目与全量项目巡检主流程（`run_patrol_project` / `run_patrol_all`）。

## 2. 通知配置与数据存储

- [x] 2.1 编写全局通知配置文件读写辅助模块（`load_notification_settings` / `save_notification_settings`，持久化至 `data/notifications.json`）。

## 3. CLI 命令与工具库集成 (`tools/geo/`)

- [x] 3.1 在 `tools/geo/__init__.py` 中导出 `run_patrol_all`、`run_patrol_project` 与 `get_project_history`。
- [x] 3.2 在 `tools/geo/cli.py` 中注册 `geo patrol` 子命令（支持 `--all`、`--project` 与 `--notify` 参数）。

## 4. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 4.1 实现 `GET /api/projects/{id}/history` 接口（返回最近 12 周巡检历史时序列表）。
- [x] 4.2 实现 `GET /api/settings/notifications` 与 `POST /api/settings/notifications` 配置管理接口。
- [x] 4.3 实现 `POST /api/settings/notifications/test` 发送测试告警消息接口。
- [x] 4.4 实现 `POST /api/patrol/trigger` 手动触发巡检接口。

## 5. Web 工作台交互升级 (`web/index.html`)

- [x] 5.1 顶部导航栏增加「🔔 告警配置」按钮与模态弹窗（支持配置 Webhook、阈值与一键测试连通性）。
- [x] 5.2 在 Step 5 增加「📈 多周声量环比趋势大盘」与「历史巡检时序列表」可视化组件。
- [x] 5.3 在项目总览 Dashboard 增加「⚡ 一键全项目自动巡检」快捷操作。

## 6. SOP 文档更新与全流程实测

- [x] 6.1 更新 `docs/sop/05-monitor-sop.md`，纳入自动化巡检与异动告警处置标准。
- [x] 6.2 运行 CLI 与 Web 接口实测：巡检并记录 history.db，模拟 Webhook 告警与测试连通性。
- [x] 6.3 在 `review-log.md` 记录评审与实测结论。
