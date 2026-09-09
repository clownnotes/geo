# Review Log — 运维告警逾期真机检测台账

## 2026-09-09 | Cursor | propose 阶段

### 背景共识（用户讨论）

- API 全量探针与未登录真搜不一致；未接模型时全量检测意义有限。  
- 运维告警应改为 **人工半联动**：提醒谁多久没测 → 点进公司 → 真机检测 → 程序统计 → **检测日志**。  
- 挑战结论已吸收：要钉死逾期天数；真机才清逾期；全量 API 降为可选并标口径；不做重型工单；最小台账有意义。

### 提案默认值（待确认）

| 项 | 默认 |
|----|------|
| 将逾期 | 7 天 |
| 已逾期 | 14 天 |
| 有效真机最少词数 | 1（先可交付；二期升 P0 全覆盖） |
| 从未真机 | 状态 `never`，优先处理 |
| API/离线 | 可写日志，**默认不清逾期** |

### 请对端 / 产品确认

- [ ] 7 / 14 天是否合适。  
- [ ] 本期 `min_manual_keywords=1` 是否接受（或必须按固定 P0 词包全测才算有效）。  
- [ ] 逾期周报 Webhook 是否放入本期（design 标 P1/二期）。

**结论**：`[待讨论]`

---

## 2026-09-09 | QwenWork | review 阶段（propose 审查，回真实代码核验复用地基 + 钉口径）

### 复用地基真实性核验（防"规范与代码同源虚构"）

逐项回真实代码，design 声称复用的入口**全部真实存在**，无虚构：

- `POST /api/projects/{id}/monitor/manual-ingest`：端点在 `server.py`；前端 `openManualProbeModal`→`fetch(.../manual-ingest)`（`index.html:6680`）、按钮「真机实测回填」(1026/1039)。✅
- `run_patrol_project` / 全量巡检：`patrol.py` + 前端 `btn-patrol-all`「全量巡检」(246)、`home-ops` 巡检条(243-253)、`loadPatrolStatus`。✅
- 向导真机入口 `switchView('mon-probing')`：`nav-mon-probing`(359)、`panel-mon-probing`(1411)。✅
- `data/notifications.json` 存在；`save_notification_settings(merge=True)`(`patrol.py:57`) 已支持合并。✅
- `history.db`(`patrol.py`)、`05_manual_probes.json`(per-project，如 `projects/nextgeo/outputs/`)。✅

### 已订正进 design/tasks 的技术护栏

- 🟡 **时区一致性（关键）**：`at` 统一存 UTC（带 `Z`），`days_since` 用 tz-aware 比较；本机 dev 在 `America/Los_Angeles(-07:00)`、生产 +08:00，naive `now()` 混 `+08:00` 会让 7/14 天边界偏约 15h 误判。→ design Data + task 1.4 + 回归 task 4.3。
- 🟡 **存储改真·JSONL**：`ops_check_logs.jsonl` append-only 每行一条，避免整数组读改写的并发竞态与无界重写。→ task 1.2。
- 🟡 **通知 merge 护栏**：新增字段走 `save_notification_settings(merge=True)`，禁止整文件覆写冲掉 `alert_history`/`last_patrol_time`。→ design 风险 + task 1.5。
- 🟢 **`source_ref` 记项目相对全路径**（05 文件是 per-project）。→ design Data。
- 🟢 **`never` 与 `overdue` 视觉区分** + `never` 置顶。→ design 风险 + task 4.4。
- 🟢 **单词样本 SOV 误导**：台账并显 `keyword_count`，1 词标「样本量小」。→ design 风险 + task 1.6。

### 对三个「请确认」项的技术建议（默认值均可配置，非代码硬编码）

1. **7 / 14 天**：合理，且落 `notifications.json` 可配。→ 建议采纳默认。
2. **`min_manual_keywords=1`**：本期接受（先可交付），二期升 P0 全覆盖；已要求台账并显样本词数对冲误导。→ 建议采纳。
3. **逾期周报 Webhook**：建议本期**仅接口预留 + 开关默认关**（proposal #5 已如此），推送实现放二期。→ 建议采纳。

### 结论

- 方案地基真实、口径清晰、无数据迁移、复用现有能力、禁 Emoji 已声明；无 🔴 阻断项。技术护栏已并入规范。

**结论**：`[已达成共识]`（方案可进入 apply；三个默认值/范围项按上述建议，若产品无异议即按 7/14、`min_manual_keywords=1`、Webhook 本期仅预留 落地）

> 停步：本轮仅审查与规范订正，未编码、未归档。待用户确认三项默认值并下达 `/opsx-apply`。

---

## 2026-09-09 | Cursor | apply 阶段

### 落地

1. `tools/geo/check_ledger.py`：JSONL 日志、UTC、台账聚合、逾期档位。
2. API：`GET /api/ops/check-ledger`、`GET /api/ops/check-logs`；`manual-ingest` / `run_patrol_project` 写日志；通知 POST `merge=True` + 7/14/最少词数字段。
3. 前端：运维台账表 + 检测日志；仪表盘逾期摘要；机器全量降级文案；通知弹窗可配天数。

### 验证

```text
python3 -m unittest tests.test_check_ledger tests.test_partners -v
# 8 tests OK（含时区边界）
```

### 默认值（按审查建议采纳）

7 / 14 天；`min_manual_keywords=1`；Webhook 逾期周报仅预留开关默认关。

**结论**：`[已修正]`（待产品 `:8088` 验收，不归档）

---

## 2026-09-09 | QwenWork | review 阶段（apply 后代码复核，回真实代码 + 跑测试）

### 核验方式

不采信 Cursor 的 `[已修正]` 口头结论。逐项回 `tools/geo/check_ledger.py`、`server.py`、`patrol.py`、`web/index.html` 真实实现；本机运行 `python3 -m unittest tests.test_check_ledger tests.test_partners -v` → **8 tests OK**；Emoji 码位扫描 `index.html` → **0 命中**。

### 前轮技术护栏落实情况（全部闭环，且带回归测试）

- ✅ **UTC 存储 + tz-aware 判定**：`utc_now_iso()` 输出 `%...Z`；`parse_at_utc`/`days_since_utc` 全程 `timezone.utc`、naive 自动补 UTC、`astimezone(utc)`（`check_ledger.py:31-61`）。并有 **`test_timezone_boundary_warn_overdue`（LA/UTC/+08 边界档位一致）** 回归——正是我上轮标的 🟡。
- ✅ **JSONL append-only**：`open(LOG_FILE,"a")` 每行一条，读取逐行 `json.loads`、坏行跳过（`check_ledger.py:91-115`）。
- ✅ **通知 merge 护栏**：`server.py:676` `save_notification_settings(body, merge=True)`；`patrol.py:62-67` merge 分支保留旧字段。
- ✅ **source_ref 全路径**：`projects/{id}/outputs/05_manual_probes.json`（`check_ledger.py:88-89,258`）。
- ✅ **never/overdue/warn 视觉区分**：前端 Tag `never`=slate-800 / `overdue`=rose / `warn`=amber（`index.html:5216-5218`），`never` 经 `STATUS_ORDER` 排序置顶（`check_ledger.py:21,223`）。
- ✅ **单词样本注**：`keyword_count<=1` → `sample_note="样本量小，仅供参考"`（`check_ledger.py:208-210`）。
- ✅ **仅 manual_probe 清逾期**：`_latest_valid_manual` 过滤 `mode!=manual_probe`；`run_patrol_project` 写 `api_patrol` 日志（`patrol.py:366-369`）但结构上不影响逾期时钟。
- ✅ **manual-ingest 挂钩**：`server.py:653-664` 回填成功后 `log_manual_ingest`，try/except 包裹，日志失败不阻断回填。
- ✅ **降级文案 + 仪表盘摘要**：「机器全量巡检（仅供参考）」(247) + 政策说明(244) + 帮助弹窗(6104)；仪表盘「已逾期/将逾期/从未真机/正常」计数摘要(5202)。
- ℹ️ 默认值按建议采纳：7/14、`min_manual_keywords=1`、Webhook 开关默认关。

### 无 🔴/🟡 遗留

- 未发现破坏现有业务、契约不符或 Emoji 违规；台账聚合 `limit=5000` 取新→旧，超量丢旧事件仅影响极旧覆盖统计，当前量级可接受（🟢 备忘，非本期问题）。

**结论**：`[通过]`（代码审查通过，可进入产品验收。建议产品在 `:8088` 点验：造一条过期日志→列表标红→真机回填→转正常且日志新增一条；归档/无记录客户落「从未真机」置顶；全量巡检按钮不再单独清逾期）

> 停步：本轮仅审查，未编码、未归档。是否归档由用户显式下达 `/opsx-archive`。

---

## 2026-09-09 | Cursor | archive 阶段

用户显式下达 `/opsx-archive` 并要求 git 提交与推送远程。tasks 全部完成；对端审查结论为 `[通过]`。

**结论**：`[通过]`
