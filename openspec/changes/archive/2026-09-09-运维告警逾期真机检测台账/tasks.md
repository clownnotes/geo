## 1. 规则与数据

- [x] 1.1 在 `notifications` 配置中增加 `warn_days`(7)、`overdue_days`(14)、`min_manual_keywords`(1)，POST merge 不丢旧字段。
- [x] 1.2 新增 `data/ops_check_logs.jsonl`（**append-only 每行一条**）与 `append_check_log` / `list_check_logs` / `build_check_ledger`（`tools/geo/check_ledger.py`）。
- [x] 1.3 明确：仅 `mode=manual_probe` 且词数达标才刷新「上次真机」并影响逾期；API/离线只记账不清逾期。
- [x] 1.4 **时区**：日志 `at` 一律存 UTC（带 `Z`）；`days_since` 用 `datetime.now(timezone.utc)` 做 tz-aware 比较。
- [x] 1.5 通知新增字段必须走 `save_notification_settings(merge=True)`。
- [x] 1.6 日志记 `keyword_count`；台账「最近 SOV」并显样本词数，1 词样本标「样本量小，仅供参考」。

## 2. API 与回填挂钩

- [x] 2.1 `GET /api/ops/check-ledger`、`GET /api/ops/check-logs`。
- [x] 2.2 `manual-ingest` 成功后写检测日志（含 operator、keywords、汇总 SOV/摘要）。
- [x] 2.3 （可选）`run_patrol_project` 成功后写 `mode=api_patrol` 日志，仍不清真机逾期。

## 3. 前端运维与仪表盘

- [x] 3.1 重做 `home-ops`：台账表 + 状态 Tag + 去真机检测；检测日志区。
- [x] 3.2 全量巡检按钮降为次要，文案「机器测，仅供参考」+ `geo-metric-hint`。
- [x] 3.3 仪表盘巡检条改为逾期摘要，链到运维告警。
- [x] 3.4 通知设置弹窗可编辑 7/14 天与最少真机词数。

## 4. 验证

- [x] 4.1 单元：无日志 → `never`；旧日志 → `overdue`；新真机 → `ok`（`tests/test_check_ledger.py`）。
- [x] 4.2 本地模块冒烟：`build_check_ledger` 可聚合现网项目；请产品 `:8088` 点验台账→真机回填。
- [x] 4.3 时区回归：7/14 边界在 offset -7/0/+8 下档位一致。
- [x] 4.4 `never` 与 `overdue` Tag 文案/色阶可区分，`never` 排序置顶。
- [x] 4.5 勾选 tasks；review-log 记结论；**停步不归档**。
