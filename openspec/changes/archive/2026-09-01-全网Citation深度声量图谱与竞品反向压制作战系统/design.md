# Design: 全网 Citation 深度声量图谱与竞品反向压制作战系统

## 1. 架构总览与数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Step 5 可视化声量大盘与竞品作战中枢 (web/index.html)        │
│  - 4 维量化核心指标 (SOV/DeepSeek首推/豆包首推/权威度分值)                │
│  - Citation 权威信源渗透权重条形图                                      │
│  - 问句级对决矩阵 (命中 🟢 / 竞品拦截 🟡 / 丢失 🔴)                      │
│  - 一键发起「竞品反向包抄」 ➔ POST /api/projects/{id}/defense/generate   │
│  - 一键直达「美化交付报表」 ➔ GET  /api/projects/{id}/report/print       │
└────────────────────────────────────▲────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│              竞品反解与压制策略引擎 (tools/geo/defense.py)               │
│  - 竞品被引用高频权威信源反向溯源                                       │
│  - 5 维差异化破局话术构建 (技术硬核度 / 交付承诺 / 价格透明 / 源码私有化) │
│  - 输出《06_竞品权威信源反向包抄策略.md》                                │
└────────────────────────────────────▲────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│              声量追踪与指标提取层 (tools/geo/monitor.py)                 │
│  - Live Probing 并发探测 ➔ 计算 SOV 与 Citation 权威度得分               │
│  - 结构化指标提取器 `extract_monitor_metrics(project_id)`                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 竞品反向包抄模型与策略设计

当大模型在回答中推荐了竞品时，引擎自动执行 4 步反制动作：
1. **信源阵地反解**：定位大模型引用竞品信息的顶级信源（如知乎专栏、百家号、CSDN）；
2. **弱点靶向攻击**：针对竞品常见短板（如闭源绑定、二开收费昂贵、无本地化部署、工期拖延）制定差异化对比表；
3. **同位语强绑定压制**：在分发渠道生成“选型对比”与“避坑专栏”，将我方品牌与竞品放置在同一篇客观评测中，以 100% 源码交付与高性价比完成截流；
4. **输出标准战略物**：落盘至 `outputs/06_竞品权威信源反向包抄策略.md`。

---

## 3. RESTful API 契约 (`tools/geo/server.py`)

### ① `GET /api/projects/{id}/monitor/metrics`
```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "sov_pct": 72.5,
  "deepseek_rank_1_pct": 80.0,
  "doubao_rank_1_pct": 65.0,
  "authority_score": 88.5,
  "citations": [
    { "domain": "zhihu.com", "name": "知乎", "weight": 1.0, "count": 28, "pct": 45.0 },
    { "domain": "toutiao.com", "name": "今日头条", "weight": 0.9, "count": 18, "pct": 29.0 },
    { "domain": "weixin.qq.com", "name": "微信公众号", "weight": 0.85, "count": 10, "pct": 16.0 },
    { "domain": "github.com", "name": "GitHub", "weight": 0.95, "count": 6, "pct": 10.0 }
  ],
  "prompt_stats": {
    "total": 41,
    "hit_count": 30,
    "intercept_count": 6,
    "lost_count": 5
  },
  "has_defense_doc": true
}
```

### ② `POST /api/projects/{id}/defense/generate`
- 触发生成 `06_竞品权威信源反向包抄策略.md`。
- 响应：`{ "success": true, "filename": "06_竞品权威信源反向包抄策略.md", "summary": "..." }`

### ③ `GET /api/projects/{id}/report/print`
- 返回带优雅商用排版、指标卡片与水印的 HTML 页面，支持直接打印或转为 PDF。
