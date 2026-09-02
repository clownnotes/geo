# Design: 大模型 Citation 信源权威度权重评分与外链信任度推演中枢

## 1. 架构与五大模型信源亲和度矩阵 (`tools/geo/citation_authority.py`)

```
   项目外链台账 (dist_ledger.json: 8 大渠道有效外链)
                           │
                           ▼
          [1. 信源基础权威库 (CHANNEL_AUTHORITY_DB)]
          ├── 今日头条/微头条 (DA: 92) ➔ 豆包亲和度: 98% ｜ 文心: 75% ｜ DeepSeek: 60%
          ├── 知乎专栏/问答 (DA: 95)  ➔ DeepSeek亲和度: 99% ｜ 豆包: 88% ｜ Kimi: 90%
          ├── 微信公众号文章 (DA: 96)  ➔ 腾讯元宝亲和度: 100% ｜ 豆包: 70% ｜ DeepSeek: 65%
          ├── GitHub开源仓库 (DA: 98) ➔ DeepSeek亲和度: 98% ｜ Kimi: 85% ｜ 豆包: 70%
          ├── 百家号/百度百科 (DA: 94)  ➔ 百度文心亲和度: 98% ｜ Kimi: 92% ｜ 豆包: 75%
          └── 企业官方网站 (DA: 75)   ➔ 全模型通用直读底座 (含 /llms.txt + JSON-LD)
                           │
                           ▼
          [2. 单条外链反向推演与采纳概率评估 (score_single_backlink)]
          ├── 域名基础权威权重 (Domain Authority: 0~100)
          ├── 链接存活状态与响应时延 (Live Status: HTTP 200, Latency)
          ├── 普林斯顿9因子承载度 (Princeton 9-Factor Fit)
          └── 预估大模型采纳率 (Estimated Citation Rate: 0~100%)
                           │
                           ▼
          [3. 全案信源权威总览与提权建议 (evaluate_project_citation_authority)]
          ├── 综合信源权威指数 (Overall Source Authority: 0~100分)
          ├── 五大模型生态覆盖完整度 (Model Coverage Balance)
          └── 交付资产自动落盘 (15_报告.md + citation_authority_matrix.json)
```

---

## 2. 数据模型 (`citation_authority_matrix.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "evaluated_at": "2026-09-02 06:30:00",
  "overall_authority_score": 93.4,
  "total_backlinks": 8,
  "live_backlinks": 8,
  "model_affinity_summary": {
    "doubao": 94.2,
    "deepseek": 96.5,
    "yuanbao": 92.0,
    "kimi": 89.5,
    "baidu": 91.0
  },
  "links_breakdown": [
    {
      "channel": "zhihu",
      "url": "https://zhuanlan.zhihu.com/p/xxx",
      "title": "徐州企业数字化转型避坑指南",
      "domain_authority": 95,
      "http_status": 200,
      "estimated_citation_rate": 96.0,
      "best_fit_models": ["DeepSeek", "Kimi", "豆包"]
    }
  ],
  "authority_optimization_tips": [
    "建议补充百度百科或百家号外链，进一步提升百度文心生态权重"
  ]
}
```

