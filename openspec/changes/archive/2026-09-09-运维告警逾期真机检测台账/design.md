# Design: 运维告警逾期真机检测台账

## Architecture

```
[仪表盘粉条] ──摘要──► N 逾期 / M 将逾期
                         │
                         ▼
              [运维告警 = 检测台账]
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   客户逾期列表     检测日志面板      次要：全量 API 巡检
        │                ▲           （口径：仅供参考）
        │ 进入流水线      │
        ▼                │
   真机回填 manual-ingest ─┴── 写 check_log + 刷新「上次真机」
```

### 核心实体

| 实体 | 含义 |
|------|------|
| **CheckEvent（检测日志）** | 一次有效检测动作的不可变记录 |
| **LedgerRow（台账行）** | 每项目聚合：上次有效真机时间、覆盖、SOV、逾期态 |
| **OverduePolicy** | `warn_days` / `overdue_days` / `min_manual_keywords` |

面向对象三问：

1. **什么叫「测过了」？** 仅 **mode=manual_probe（真机）** 且本周期内回填词数 ≥ `min_manual_keywords`（默认 **1** 先可交付；建议配置升到 P0 词包全量）。  
2. **API/离线算不算？** 默认可写日志但 **不延长逾期时钟**。  
3. **从未测过？** 台账状态 = `never`（展示「从未真机检测」），排序置顶，等同运营优先级最高。

## Interface

### API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ops/check-ledger` | `{ success, policy, rows:[{project_id, client_name, status, last_manual_at, manual_keyword_count, last_sov_pct, days_since}] }` |
| GET | `/api/ops/check-logs?project_id=&limit=` | 日志列表，新→旧 |
| POST | `/api/settings/notifications` | 扩展字段 merge：`warn_days`, `overdue_days`, `min_manual_keywords`, `overdue_webhook_enabled` |

`status` 枚举：`ok` | `warn` | `overdue` | `never`。

真机回填：保持 `POST /api/projects/{id}/monitor/manual-ingest`；成功后内部调用 `append_check_log(...)` 并可选重算周报指标。

### 前端（`home-ops`）

1. 顶区：`geo-page-head` + 政策摘要（7/14 天）+ 「机器全量巡检（仅供参考）」按钮（现有全量能力降级展示）。  
2. 台账表：客户、状态 Tag、上次真机、覆盖词、最近 SOV、天数、操作（去真机检测）。  
3. 下方或侧栏：检测日志（可按当前筛选客户过滤）。  
4. 仪表盘 `loadPatrolStatus`：改为同时拉 ledger 摘要，文案「已逾期 X 家 · 将逾期 Y 家 · 从未检测 Z 家」。

### 进入客户

`enterWizard(id)` + `switchView('mon-probing')`（或现有真机回填入口），避免新建第三套检测页。

## Data

### 方案 A（推荐）：全局 JSONL / JSON

`data/ops_check_logs.jsonl`（**每事件一行 JSON，append-only**；单文件足够当前项目量级）。采用 JSONL 而非整数组 JSON：避免每次回填读改写整个数组带来的并发竞态与无界重写；聚合时按行 tail 读取。

```json
{
  "id": "chk_20260909_xxx",
  "project_id": "xuzhou_xuanyuan",
  "at": "2026-09-09T04:00:00Z",
  "operator": "13150568888",
  "mode": "manual_probe",
  "keywords": ["徐州GEO哪家好"],
  "keyword_count": 1,
  "sov_pct": 45.0,
  "summary": "真机回填 1 词；命中 1",
  "source_ref": "projects/xuzhou_xuanyuan/outputs/05_manual_probes.json"
}
```

> **时区铁律**：`at` 一律存 **UTC（带 `Z`）**；`days_since` 必须用 tz-aware 时间比较（`datetime.now(timezone.utc)`），**严禁** naive `datetime.now()` 与 `+08:00` 字符串混算——本机 dev 处于 `America/Los_Angeles(-07:00)`、生产在中国(+08:00)，混用会让 7/14 天边界偏移约 15 小时而误判逾期。展示时可转 `Asia/Shanghai`。
> `source_ref` 记**项目相对全路径**（`05_manual_probes.json` 是 per-project 文件，全局日志不能只写裸文件名）。

`mode`: `manual_probe` | `api_patrol` | `offline_estimate`。

台账聚合：扫各项目最新一条 `manual_probe` + `05_manual_probes.json` 词数兜底。

### 方案 B（备选）

每项目 `outputs/ops_check_log.json` + 列表 API 聚合。全局文件更利于运维页一次拉取。

**本期采用方案 A。**

### 通知配置扩展（`data/notifications.json`）

```json
{
  "warn_days": 7,
  "overdue_days": 14,
  "min_manual_keywords": 1,
  "overdue_webhook_enabled": false
}
```

与现有 `enabled` / `min_sov_threshold` / `drop_threshold_pct` 并存：  
- **逾期**管「人有没有按时真机测」；  
- **SOV 安全线/突降**管「测完之后数字差不差」（仅对非 offline 的真机/API 序列有意义）。

## UI 规范

- 复用 `geo-btn` / `geo-alert` / `geo-tag*` / `geo-metric-hint`（状态列旁可挂「什么叫逾期」说明）。  
- 禁止 Emoji。  
- 全量巡检：次要按钮样式 + 帮助文案，避免再占主 CTA。

## 风险

- 真机回填若只记单词，SOV 波动大 → `min_manual_keywords` 与后续 P0 词包要在 review 钉死是否本期强制。  
- `last_patrol_time` 与「上次真机」易混淆 → UI 分两行，禁止混用同一字段清空逾期。  
- 操作者取自登录用户名；无登录上下文时写 `system`。
- **通知字段写入护栏**：新增 `warn_days`/`overdue_days`/`min_manual_keywords`/`overdue_webhook_enabled` 必须走现有 `save_notification_settings(merge=True)`（`tools/geo/patrol.py:57`），**严禁**整文件覆写，否则会冲掉 `alert_history`/`last_patrol_time`/`webhook_url` 等存量字段。
- **`never` 与 `overdue` 视觉区分**：二者都偏红但语义不同——「从未真机检测」用独立 Tag（slate/紫 + 文案「从未检测」）并排序置顶，「已逾期」用红；不得合并为同一 Tag。
- **`min_manual_keywords=1` 的 SOV 误导**：本期默认 1 词即清逾期，但台账「最近 SOV」列须并显当次样本词数（`keyword_count`），1 词样本标注「样本量小，仅供参考」，避免单条真机把 SOV 当结论。

## 二期预留

- P0 词包强制全覆盖才算有效周检。  
- 逾期周报 Webhook。  
- 允许「API 巡检也可清逾期」的高级开关（默认关）。
