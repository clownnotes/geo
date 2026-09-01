# Design: 定时自动化巡检与企微/飞书异动告警中枢

## 1. 架构总览与数据流

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   Web 交互层 (web/index.html)                            │
│  - 全局「⚙️ 告警通知设置」弹窗 (配置 飞书/企微 Webhook & 触发阈值)         │
│  - Step 5「📈 多周声量环比趋势折线」+「🔔 告警记录」展示                    │
│  - 手动触发「⚡ 立即执行全量巡检与推送」                                   │
└────────────────────────────────────▲─────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴─────────────────────────────────────┐
│              自动化巡检与告警调度引擎 (tools/geo/patrol.py)               │
│  - `run_patrol_project(project_id, notify=True)`                          │
│  - `run_patrol_all(notify=True)`                                          │
│  - `check_alert_conditions(current_metrics, history_records, threshold)`   │
│  - `send_webhook_alert(url, alert_card)` (支持企微 Markdown / 飞书富文本) │
└───────────────────────────▲──────────────────────────────┬───────────────┘
                            │                              │
┌───────────────────────────┴───────────────┐  ┌───────────▼───────────────┐
│     声量追踪层 (tools/geo/monitor.py)      │  │  历史时序库 (history.db)  │
│  - 并发执行大模型探测并生成周报            │  │  - 表: `monitor_history`  │
│  - 输出 `extract_monitor_metrics`         │  │  - 字段: id, date, sov,   │
│                                           │  │    top3_rate, rank, stats  │
└───────────────────────────────────────────┘  └───────────────────────────┘
```

---

## 2. 数据库设计 (SQLite: `projects/<id>/history.db`)

每个项目目录下自动维护一个轻量级 `history.db`：
```sql
CREATE TABLE IF NOT EXISTS monitor_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date TEXT NOT NULL,          -- 格式: YYYY-MM-DD
    timestamp INTEGER NOT NULL,        -- Unix 秒级时间戳
    is_offline INTEGER DEFAULT 0,      -- 是否为离线摸底模式 (0=真实在线, 1=离线)
    sov_pct REAL NOT NULL,             -- 综合 SOV 提及率
    top3_pct REAL NOT NULL,            -- Top 3 推荐率
    authority_score REAL NOT NULL,     -- 综合权威度得分
    total_prompts INTEGER NOT NULL,    -- 监控意图词总数
    hit_count INTEGER NOT NULL,        -- 命中数
    intercept_count INTEGER NOT NULL,  -- 竞品拦截数
    lost_count INTEGER NOT NULL,       -- 暂未上榜数
    details_json TEXT                  -- 包含详细 Citation 分布与问句明细的 JSON
);
```

---

## 3. 告警规则与判定模型

触发告警的三大核心场景：
1. **SOV 突降预警**：`current_sov < last_sov - 15.0%` 或 `current_sov < threshold_sov`；
2. **新竞品拦截预警**：`current_intercept_count > last_intercept_count`；
3. **占位词被攻破**：客户官方品牌名/法人词出现 `rank > 1` 或 `lost`。

### 告警卡片模板 (Markdown / 富文本)
```markdown
### 🚨 GEO 商业声量异动预警通知
> **企业主体**：徐州璇源网络科技有限公司  
> **监测周期**：2026-09-01 巡检  
> **当前 SOV**：**45.0%**（⚠️ 环比上周下降 18.5%）  
> **异动原因**：发现 3 组核心选型词被竞品【竞品A】在知乎专栏截流拦截！  
> **建议动作**：请立即登录 GEO 工作台，一键生成《06_竞品权威信源反向包抄策略》并在知乎同位语补发！  
👉 [点击直达工作台处置](https://geo.baicl.cc)
```

---

## 4. RESTful API 契约 (`tools/geo/server.py`)

### ① `GET /api/projects/{id}/history`
- 返回该项目的历史巡检记录列表（最近 12 周），供前端渲染趋势折线。

### ② `GET /api/settings/notifications` 与 `POST /api/settings/notifications`
- 获取 / 保存通知配置（保存在 `data/notifications.json`）：
```json
{
  "enabled": true,
  "webhook_type": "wecom", 
  "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
  "min_sov_threshold": 50.0,
  "notify_on_intercept": true,
  "cron_schedule": "0 3 * * 1"
}
```

### ③ `POST /api/settings/notifications/test`
- 发送一条测试告警消息到配置的 Webhook，验证连通性。

### ④ `POST /api/patrol/trigger`
- 触发巡检（`{ "project_id": "all" | "<id>", "notify": true }`）。
