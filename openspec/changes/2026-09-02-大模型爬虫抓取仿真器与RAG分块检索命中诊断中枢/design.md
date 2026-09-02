# Design: 大模型爬虫抓取仿真器与 RAG 分块检索命中诊断中枢

## 1. 架构流程与模块设计 (`tools/geo/crawler.py` / `rag_diag.py`)

```
   企业官网 URL / 本地 03 普林斯顿语料
                     │
                     ▼
      [1. 大模型爬虫仿真抓取 (simulate_crawler_fetch)]
      ├── 模拟 Bytespider (豆包/字节跳动)
      ├── 模拟 Baiduspider (百度文心)
      ├── 模拟 DeepSeek-Crawler (深度求索)
      └── 提纯 Clean Markdown + 去噪 + 提取 Title / Links / Meta
                     │
                     ▼
      [2. RAG 语义分块与切片诊断 (diagnose_rag_chunks)]
      ├── 滑动窗口分块: 400 Token / 重叠 50 Token (按中英文标点断句)
      ├── 逐 Chunk 评分与特征透视:
      │   ├── 品牌实体与核心主张命中 (Entity Match)
      │   ├── 量化参数与硬指标密度 (Quantitative Score)
      │   ├── Markdown 对比表格保留 (Table Integrity)
      │   └── FAQ 问答对完整度 (Q&A Recall)
      └── 综合检索有效召回率 (RAG Readiness Score: 0~100分)
                     │
                     ▼
      [3. 交付资产自动落盘与同步]
      ├── outputs/12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md
      └── outputs/rag_chunks_diagnostic.json
```

---

## 2. 数据结构 (`rag_chunks_diagnostic.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "analyzed_at": "2026-09-02 05:45:00",
  "rag_readiness_score": 92.5,
  "total_chunks": 8,
  "avg_chunk_tokens": 340,
  "entity_coverage_pct": 100.0,
  "table_preservation_pct": 100.0,
  "qa_pairs_count": 5,
  "chunks": [
    {
      "chunk_id": 1,
      "tokens": 320,
      "preview": "...",
      "entity_hits": ["徐州璇源", "段晓奇"],
      "quantitative_hits": ["365天", "100%"],
      "score": 95.0,
      "grade": "🟢 黄金召回块"
    }
  ]
}
```

