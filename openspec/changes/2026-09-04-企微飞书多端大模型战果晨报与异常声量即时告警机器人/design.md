# Design: 企微飞书多端大模型战果晨报与异常声量即时告警机器人 (第 33 维)

## 1. 架构设计与对象模型 (Architecture)

### 1.1 系统数据流与组件关系图

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   数据输入层 (真实 Outputs 资产)                         │
│  • 30 维: live_probing_trace.json (首推率/Citation)   • 31 维: spider_access_audit.json│
│  • 32 维: rival_crack_result.json (竞对反超套件)      • 19 维: negative_sentiment.json │
│  • 20 维: knowledge_decay.json (知识保鲜度)          • 28 维: 高管门户免密 Token 链接  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  核心引擎层 (alert_bot.py)                              │
│                                                                                        │
│   ┌──────────────────────────────┐              ┌─────────────────────────────────┐   │
│   │  MorningBriefingAggregator   │              │     InstantAnomalyDetector      │   │
│   │  - 真实聚合各维度实测战果     │              │  - 🔴 P0 品牌声誉负面危机排查   │   │
│   │  - 事实红线：未实测标待测试   │              │  - 🔴 P1 竞品霸榜强行截流排查   │   │
│   │  - 提取高管大屏免密直达链接  │              │  - 🟡 P1 爬虫 403 阻断/断崖排查 │   │
│   │                              │              │  - 🟡 P2 知识半衰期老化排查     │   │
│   └──────────────┬───────────────┘              └────────────────┬────────────────┘   │
│                  │                                               │                     │
│                  └───────────────────────┬───────────────────────┘                     │
│                                          ▼                                             │
│                       ┌─────────────────────────────────────┐                         │
│                       │        WebhookCardFormatter         │                         │
│                       │  • format_feishu() (交互式卡片+按钮)│                         │
│                       │  • format_wecom()  (富文本 Markdown)│                         │
│                       │  • format_dingtalk() (ActionCard)   │                         │
│                       │  • format_markdown_report() (公文)  │                         │
│                       └──────────────────┬──────────────────┘                         │
│                                          │                                             │
│                                          ▼                                             │
│                       ┌─────────────────────────────────────┐                         │
│                       │         AlertBotDispatcher          │                         │
│                       │  • is_ssrf_safe_url() 强安全校验    │                         │
│                       │  • --dry-run 本地零公网网络回放     │                         │
│                       │  • HTTP POST 发送与重试容错         │                         │
│                       │  • 告警历史记录持久化落盘           │                         │
│                       └──────────────────┬──────────────────┘                         │
└──────────────────────────────────────────┼─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  多端触达与战果反哺层                                   │
│  • 飞书/企微/钉钉管理群 (秒级送达)                                                      │
│  • 《33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md》 (公文审计)                 │
│  • 高管交付门户 web/share.html (大模型战果推送与即时告警中枢大屏卡片)                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心面向对象三问分析

1. **它是谁（Entity / Value Object）**：
   - `BriefingData`：晨报聚合指标数据模型（项目 ID、日期、联网实测首推率、Citation 角标数、AI 爬虫访问频次、竞对反超状态、门户免密直达 URL、数据状态）；
   - `AnomalyAlert`：异动告警数据模型（告警 ID、级别 `P0`/`P1`/`P2`、触发类型、标题、详情描述、受影响指标、建议反制指令）；
   - `CardPayload`：格式化后的平台原生 Webhook 请求体（平台类型、JSON 结构体、字符预览）。
2. **它的生命周期与不可变性**：
   - 晨报数据与告警记录一旦生成并推送，作为不可变历史日志持久化保存至 `projects/{id}/outputs/alert_bot_history.json`；
   - 每次生成均自动附带 SHA-256 防伪流水号。
3. **它的边界与安全性（三不与四防）**：
   - **防内网探测 (SSRF)**：所有配置或输入的 Webhook URL 必须通过 `is_ssrf_safe_url` 拦截，杜绝私网回环；
   - **防虚构数据**：晨报中未执行维度的指标统一显式标记为 `[待实测]`，禁止填充恒定假设值；
   - **防死锁与网络阻塞**：网络发送统一设置 5 秒严格超时；单测环境默认强制 `--dry-run` 拦截外部出站。

---

## 2. 接口与数据契约设计 (Interface Specification)

### 2.1 命令行 CLI (`tools/geo/cli.py`)

```bash
# 1. 发送战果晨报（默认 dry-run 纯本地预览）
python3 -m tools.geo alert-bot xuzhou_xuanyuan --type briefing --channel feishu --dry-run

# 2. 真实发送晨报至指定 Webhook 并生成第 33 号公文
python3 -m tools.geo alert-bot xuzhou_xuanyuan --type briefing --webhook "https://open.feishu.cn/open-apis/bot/v2/hook/xxx" --report

# 3. 扫描并触发异常异动即时报警
python3 -m tools.geo alert-bot xuzhou_xuanyuan --type alert --dry-run

# 4. 发送连通性测试卡片
python3 -m tools.geo alert-bot xuzhou_xuanyuan --type test --channel wecom --dry-run
```

### 2.2 服务端 REST API (`tools/geo/server.py`)

1. **`POST /api/projects/{id}/alert-bot/send`**
   - **Headers**: `Authorization: Bearer <token>`
   - **Request Body**:
     ```json
     {
       "type": "briefing",          // "briefing" | "alert" | "test"
       "channel": "feishu",         // "feishu" | "wecom" | "dingtalk" | "auto"
       "webhook_url": "https://...",// 可选，未传时读取系统配置
       "dry_run": true              // 默认为 true（安全模式）
     }
     ```
   - **Response**:
     ```json
     {
       "status": "ok",
       "project_id": "xuzhou_xuanyuan",
       "type": "briefing",
       "channel": "feishu",
       "delivered": false,
       "dry_run": true,
       "card_preview": { ... },
       "timestamp": "2026-09-04T12:00:00Z"
     }
     ```

2. **`GET /api/projects/{id}/alert-bot/history`**
   - **Headers**: `Authorization: Bearer <token>`
   - **Response**:
     ```json
     {
       "project_id": "xuzhou_xuanyuan",
       "total_sent": 12,
       "anomalies_detected": 1,
       "history": [ ... ],
       "last_briefing": { ... }
     }
     ```

3. **`GET /api/projects/{id}/alert-bot/preview?type=briefing&channel=feishu`**
   - **Headers**: `Authorization: Bearer <token>`
   - **Response**:
     ```json
     {
       "channel": "feishu",
       "type": "briefing",
       "card_payload": { ... },
       "rendered_markdown": "### 🌤️ GEO 大模型战果晨报..."
     }
     ```

---

## 3. 多端原生卡片协议规范 (Card Templates)

### 3.1 飞书交互式卡片 (Feishu Interactive Card)
- **卡片特征**：支持彩色 Header 标题栏（晨报用 `turquoise`/`blue`，P0 报警用 `carmine`/`red`）；
- **布局**：
  - 核心指标高对比度展示（首推率、Citation 命中数、AI 爬虫访问数）；
  - 异动声量风险排查清单；
  - 底部操作按钮：`【📊 查看高管交付大屏】`（免密跳转 Token 链接）与 `【⚡️ 启动自愈流水线】`。

### 3.2 企业微信 Markdown 模板 (WeCom Markdown)
- **卡片特征**：利用企微原生 Markdown 语法（`<font color="info">`、`<font color="warning">`、引用块、无序列表）；
- **布局**：标题 ➔ 核心指标看板 ➔ 异动预警清单 ➔ 一键超链接跳转。

### 3.3 钉钉 Markdown / ActionCard
- **卡片特征**：ActionCard 单选/多选跳转按钮与 Markdown 渲染。

---

## 4. 高管交付门户反哺与优雅降级契约

在 `tools/geo/share.py` 中挂载 `alert_bot_summary`，全面对齐以下规范（包含主键与跨端兼容别名）：
```json
{
  "has_data": true,
  "status": "active",
  "status_label": "🤖 战果机器人已接入：已建立多端晨报与声量异动主动触达机制",
  "total_dispatched": 3,
  "total_sent": 3,
  "last_dispatch_time": "2026-09-04 09:00:00",
  "last_briefing_time": "2026-09-04 09:00:00",
  "total_anomalies_intercepted": 0,
  "anomalies_detected_count": 0,
  "recent_history": [],
  "recent_alerts": [],
  "webhook_configured": false,
  "audit_doc": "outputs/33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md"
}
```
当项目未运行过 alert-bot 时，返回：
```json
{
  "has_data": false,
  "status": "never_run",
  "status_label": "⚪️ 待配置企微/飞书战果晨报与异动告警机器人",
  "total_dispatched": 0,
  "total_sent": 0,
  "last_dispatch_time": null,
  "last_briefing_time": null,
  "total_anomalies_intercepted": 0,
  "anomalies_detected_count": 0,
  "webhook_configured": false,
  "recent_history": [],
  "recent_alerts": [],
  "audit_doc": ""
}
```
`web/share.html` 中增设只读状态卡片，严格支持 `never_run` 优雅降级。
