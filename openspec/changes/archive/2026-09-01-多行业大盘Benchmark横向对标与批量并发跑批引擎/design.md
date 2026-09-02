# Design: 多行业大盘 Benchmark 横向对标与批量并发跑批引擎

## 1. 架构与数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Web 控制台与客户交付门户                             │
│  - Dashboard「🌐 行业大盘宏观基准」卡片                                        │
│  - Step 5 & share.html「🎯 行业横向对标与超越战绩」卡片                        │
│  - 项目列表「🚀 批量并发生产调度」弹窗                                          │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│             行业大盘聚合与批量调度引擎 (tools/geo/benchmark.py)              │
│  - `calculate_industry_benchmarks()` ➔ 聚合全项目行业指标与分位数            │
│  - `evaluate_project_against_benchmark(project_id)` ➔ 判定超越战绩与短板    │
│  - `run_batch_pipeline(targets, step, workers)` ➔ ThreadPoolExecutor 并发跑批│
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                           底层数据源与流水线支持                             │
│  - 项目配置 `projects/<id>/config.json` (获取 industry)                      │
│  - 监控指标 `extract_monitor_metrics(project_id)`                            │
│  - 历史时序库 `projects/<id>/history.db`                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 行业 Benchmark 计算模型与超越战绩算法

### ① 行业聚合数据结构
```python
{
  "industry_name": "工业互联网/智能制造",
  "project_count": 8,
  "avg_sov": 42.5,
  "median_sov": 40.0,
  "top_10_percent_sov": 75.0,
  "avg_top3_rate": 48.0,
  "avg_authority_score": 86.5,
  "top_citation_platforms": [
    { "domain": "zhihu.com", "name": "知乎", "share": 38.5 },
    { "domain": "toutiao.com", "name": "今日头条", "share": 31.0 },
    { "domain": "github.com", "name": "GitHub", "share": 18.5 },
    { "domain": "weixin.qq.com", "name": "微信", "share": 12.0 }
  ]
}
```

### ② 客户超越同行战绩判定 (Percentile Rank)
- **超越同行百分比 (Beat Rate)**：
  根据客户当前 SOV 在同行业所有项目及基准分布中的排名：
  $$ \text{Beat Rate} = \min\left(99.0\%, \max\left(10.0\%, \frac{\text{Client SOV}}{\text{Top 10\% SOV}} \times 90.0\%\right)\right) $$
- **战绩标签**：
  - `SOV >= Top 10%` ➔ 🏆 `行业领头羊 (Top Tier)`
  - `SOV >= 行业平均线` ➔ 🟢 `第一梯队强阵地 (Above Average)`
  - `SOV < 行业平均线` ➔ 🟡 `蓄力爬坡期 (Growth Stage)`

---

## 3. 批量并发调度器设计 (`run_batch_pipeline`)

使用 Python 标准库 `concurrent.futures.ThreadPoolExecutor` 实现多项目安全并发：
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_batch_pipeline(project_ids: list, step: str = "pipeline", max_workers: int = 4) -> list:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pid = {
            executor.submit(_execute_single_step, pid, step): pid 
            for pid in project_ids
        }
        for future in as_completed(future_to_pid):
            pid = future_to_pid[future]
            try:
                data = future.result()
                results.append({"project_id": pid, "success": True, "result": data})
            except Exception as e:
                results.append({"project_id": pid, "success": False, "error": str(e)})
    return results
```

---

## 4. RESTful API 契约

### ① `GET /api/benchmark/industries` (公开/管理通用)
- 返回全库所有行业的宏观均值、项目总数与 Top 信源渠道。

### ② `GET /api/projects/{id}/benchmark` (鉴权/只读共享通用)
- 返回该项目在所属行业的对标卡片（客户 SOV vs 行业均值 vs 行业领头羊，超越百分比与差距）。

### ③ `POST /api/batch/trigger` (管理员鉴权)
- **Request Body**:
```json
{
  "target": "all",              // "all" 或 ["proj1", "proj2"]
  "industry": "工业互联网",      // 可选过滤行业
  "step": "pipeline",           // "pipeline" / "audit" / "scaffold" / "rewrite" / "distribute" / "monitor"
  "max_workers": 4
}
```
- **Response**: `{ "success": True, "task_id": "...", "total": 12, "message": "批量任务已在后台并发执行" }`
