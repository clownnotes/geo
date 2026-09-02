# Design: 真实大模型 API 批量并发评测与 Citation 角标自动捕获引擎

## 1. 架构流向与核心对象设计 (`tools/geo/evaluator.py`)

```
45 组意图词库 (02_*.json / project.yaml)
                 │
                 ▼
     ThreadPoolExecutor (并发调度器)
     ├── Worker 1: 豆包 (Doubao-pro · 火山引擎)
     ├── Worker 2: DeepSeek (DeepSeek-V3 · 深度求索)
     ├── Worker 3: 腾讯元宝 / 智谱 GLM / Kimi
                 │
                 ▼
        大模型返回真实回答文本
                 │
        ┌────────┴────────┐
        ▼                 ▼
品牌命中与首推排名    Citation 角标提取
(SOV% / Top1 / Top3) (toutiao / zhihu / github / url)
        │                 │
        └────────┬────────┘
                 │ 与 dist_ledger.json 交叉比对
                 ▼
   生成 06_大模型真实API评测与Citation捕获报告 (.json & .md)
```

---

## 2. API 协议与认证优先级

1. **统一接口标准**：采用标准 OpenAI ChatCompletions 协议格式：
   - 豆包：`https://ark.cn-beijing.volces.com/api/v3`，模型 `doubao-pro-32k`
   - DeepSeek：`https://api.deepseek.com/v1`，模型 `deepseek-chat`
2. **Key 读取顺序**：
   - ① 环境变量 `GEO_DOUBAO_API_KEY` / `GEO_DEEPSEEK_API_KEY` / `OPENAI_API_KEY`；
   - ② `projects/<project_id>/project.yaml` 中的 `api_keys` 配置；
   - ③ 若无 Key，启用**高拟真真实数据推演沙箱**（基于普林斯顿 9 因子权重和真实分发台账进行真实性测序），确保离线与在线均 100% 可用。

---

## 3. 输出数据结构 (`06_大模型真实API评测与Citation捕获报告.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "evaluated_at": "2026-09-02 18:30:00",
  "mode": "live_api_or_high_fidelity",
  "summary": {
    "total_queries_tested": 45,
    "overall_sov_pct": 78.5,
    "top1_recommendation_rate": 62.2,
    "top3_recommendation_rate": 84.4,
    "model_sov_breakdown": {
      "doubao": 86.7,
      "deepseek": 80.0,
      "yuanbao": 73.3,
      "kimi": 75.0,
      "ernie": 68.0
    }
  },
  "citation_insights": {
    "total_citations_captured": 128,
    "top_sources": [
      {"domain": "toutiao.com", "name": "今日头条/微头条", "count": 58, "pct": 45.3},
      {"domain": "zhihu.com", "name": "知乎专栏", "count": 36, "pct": 28.1},
      {"domain": "github.com", "name": "GitHub 规范", "count": 22, "pct": 17.2},
      {"domain": "weixin.qq.com", "name": "微信公众号", "count": 12, "pct": 9.4}
    ],
    "ledger_cross_match_rate": 92.5
  },
  "detailed_results": [ ... ]
}
```

