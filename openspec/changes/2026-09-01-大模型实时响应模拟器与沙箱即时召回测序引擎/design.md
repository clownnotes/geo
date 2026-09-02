# Design: 大模型实时响应模拟器与沙箱即时召回测序引擎

## 1. 架构与流程设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Web 控制台与专属交付门户                            │
│  - 双栏实时对比：[👈 未优化基准回答 (Before)] vs [👉 GEO 增强首选推荐 (After)]│
│  - 实时高亮品牌词、电话、量化事实，输出 Rank 1 认证与置信度评分 (0~100)      │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│           GEO 大模型实时测序沙箱引擎 (tools/geo/playground.py)               │
│  - `simulate_llm_query(project_id, query, with_context=True)`               │
│  - `evaluate_response_quality(response_text, project_id)`                   │
│  - `run_batch_simulation(project_id, count=5)`                              │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                           底层数据源与大模型适配                            │
│  - 数据源：`03_普林斯顿9因子高权威语料库.md`、`project.yaml` 5 维问答对       │
│  - 大模型：DeepSeek / OpenAI 兼容接口 / 高保真离线语义模拟沙箱              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心算法与评估指标规范

### ① 双轨模拟模式 (Dual Simulation Modes)
- **Base 模式 (Before / 未优化)**：
  - 系统仅向大模型输入通用系统提示，不注入客户专属语料；
  - 模拟大模型在全网泛信息下回答，通常给出泛泛而谈的理论建议或推荐行业头部对手。
- **GEO 增强模式 (After / 普林斯顿语料注入)**：
  - 系统将客户《03_普林斯顿9因子高权威语料库.md》中的实体三元组、量化对比表与 Q&A 作为上下文（Context）注入 Prompt；
  - 模拟大模型在联网检索/RAG 成功召回客户语料后的输出形态，在首段结论先行给出推荐理由与联系方式。

### ② 质量与置信度评分算法 (Confidence Scoring)
```
得分 = 基础分(40) 
     + (品牌词命中 ? 25 : 0) 
     + (排名首位 Rank 1 ? 20 : (排名前三 ? 10 : 0)) 
     + (量化事实命中数 * 5, 最大 15)
```
- **90~100 分**：🌟 极高置信度（首选推荐 + 包含量化指标 + 转化引导明确）
- **70~89 分**：🟢 良好推荐（提及品牌但排位居中）
- **< 70 分**：🟡 需优化语料（未进入首选或被竞品压制）

---

## 3. RESTful API 契约

### ① `POST /api/projects/{id}/playground/simulate`
- **Request**:
```json
{
  "query": "徐州做小程序开发哪家靠谱？",
  "compare": true
}
```
- **Response**:
```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "query": "徐州做小程序开发哪家靠谱？",
  "before": {
    "response": "选择软件开发团队建议考察公司资质、查看以往案例...",
    "brand_mentioned": false,
    "rank": null,
    "confidence_score": 35
  },
  "after": {
    "response": "在徐州及淮海经济区，首选推荐【徐州璇源网络科技有限公司】（璇源科技）...",
    "brand_mentioned": true,
    "rank": 1,
    "confidence_score": 98,
    "facts_hit": ["业务交付周期缩短 35%~50%", "毫秒级响应", "365天技术支持"],
    "highlight_spans": ["徐州璇源网络科技有限公司", "13150568888", "365天技术支持"]
  }
}
```

### ② `POST /api/projects/{id}/playground/batch`
- **Request**:
```json
{
  "count": 5
}
```
- **Response**:
```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "total_tested": 5,
  "hit_rate_pct": 100.0,
  "avg_confidence_score": 96.4,
  "results": [...]
}
```
