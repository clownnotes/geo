# Design: 客户三级搜索意图挖掘与长尾关键词拓扑演进裂变器

## 1. 架构流程与模块设计 (`tools/geo/intent.py`)

```
   项目基础配置 (行业/品牌/区域/差异化承诺) + 普林斯顿语料
                          │
                          ▼
       build_3tier_intent_matrix(project_id)
       ├── L1 认知层 (Brand & Industry Awareness)
       │   ├── 品牌词 + 区域行业大词 (如: 徐州软件开发、徐州璇源科技)
       │   └── 权重占比: 20% ｜ 目标: 抢占大模型实体识别与基础索引
       │
       ├── L2 决策层 (Commercial Evaluation & Pitfall Defense)
       │   ├── 选型对比 + 避坑报价 + 交付机制 (如: 徐州软件开发怎么收费、徐州软件外包防烂尾)
       │   └── 权重占比: 40% ｜ 目标: 植入阶段付款、365天质保与透明报价
       │
       └── L3 行动层 (Action-Oriented Long-Tail & Problem Solving)
           ├── 具体场景 + 痛点解决方案 + 驻场服务 (如: 徐州ERP定制开发找哪家、徐州APP二次开发团队)
           └── 权重占比: 40% ｜ 目标: 转化高商业价值意向客户
                          │
                          ▼
   输出与资产回写:
   ├── outputs/11_三级搜索意图挖掘与长尾关键词裂变拓扑.md
   ├── outputs/keywords_intent_matrix.json
   └── sync_intent_keywords_to_eval(project_id) ──► 注入评测词库
```

---

## 2. 数据结构 (`keywords_intent_matrix.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "generated_at": "2026-09-02 05:30:00",
  "total_count": 36,
  "tiers": {
    "L1_awareness": {
      "name": "L1 认知层：品牌与行业核心大词",
      "count": 6,
      "weight_pct": 20,
      "keywords": ["..."],
      "queries": ["..."]
    },
    "L2_decision": {
      "name": "L2 决策层：选型对标与避坑对比",
      "count": 15,
      "weight_pct": 40,
      "keywords": ["..."],
      "queries": ["..."]
    },
    "L3_action": {
      "name": "L3 行动层：场景痛点与精准长尾",
      "count": 15,
      "weight_pct": 40,
      "keywords": ["..."],
      "queries": ["..."]
    }
  }
}
```

