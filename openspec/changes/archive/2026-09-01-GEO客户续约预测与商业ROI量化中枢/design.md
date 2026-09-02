# Design: GEO 客户续约预测与商业 ROI 量化中枢

## 1. 架构与量化算法设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Web 管理工作台 Step 5 & 客户交付门户 Tab 5                │
│  - 💰 商业投资回报率: 360%~480% (等效节省 ¥120,000+ / 获客线索估值 ¥68,000) │
│  - 📈 续约健康度评分: 92/100 (极高概率续约) + 定制续约提案话术建议           │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│           商业 ROI 量化与续约预测计算引擎 (tools/geo/roi.py)                 │
│  - `calculate_project_roi(project_id, custom_params=None)`                  │
│  - `predict_renewal_health(project_id)`                                     │
│  - `save_roi_settings(project_id, settings)`                                │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│        基础数据接入层 (Metrics / History / Dist Ledger / Benchmarks)        │
│  - SOV 占有率、Rank 1 首推率、分发台账收录数、反向拦截竞品数                │
│  - 行业基准参数 (默认 CPL: 120~200 元, 行业基础服务费: 30,000 元)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 商业算法数学公式规范

### ① 等效 SEM 竞价替代节省价值 ($V_{SEM}$)
$$V_{SEM} = \text{月度核心 Prompt 检索基准量 (如 2500 次)} \times \text{SOV 达成率} \times \text{行业平均 CPC (如 6.5 元)} \times 12 \text{ 个月}$$

### ② AI 首推精准线索估值 ($V_{Leads}$)
$$V_{Leads} = \text{首推 Rank 1 问答数} \times \text{月度预估转化线索 (如 8 条/月)} \times \text{行业单线索成本 CPL (如 160 元)} \times 12 \text{ 个月}$$

### ③ 语料库与数字资产沉淀估值 ($V_{Asset}$)
$$V_{Asset} = \text{已收录外发平台数} \times 3,000 \text{ 元/平台信任池} + \text{9因子高权重语料库基础估值 (15,000 元)}$$

### ④ 综合商业 ROI 百分比
$$\text{总商业创造价值 } V_{Total} = V_{SEM} + V_{Leads} + V_{Asset}$$
$$\text{综合 ROI } = \frac{V_{Total} - \text{年度服务费成本}}{\text{年度服务费成本}} \times 100\%$$

### ⑤ 续约健康度得分模型 ($S_{Renewal}$, 0~100)
- **基础分**：40 分
- **SOV 表现**：$\text{SOV} \times 0.25$（上限 25 分）
- **Rank 1 首推排位**：若存在 Rank 1 则 +15 分
- **分发完成率**：$\text{Completion Rate} \times 0.10$（上限 10 分）
- **巡检稳定性与无严重异动**：+10 分
- **评级判定**：
  - $\ge 85$ 分：🌟 **极高概率续约（建议主推年度增购包）**
  - $70 \sim 84$ 分：🟢 **健康续约（建议安排季度复盘汇报）**
  - $< 70$ 分：⚠️ **需重点公关（建议安排现场沙箱实测答辩）**

---

## 3. RESTful API 契约

### ① `GET /api/projects/{id}/roi/calculate`
- **Response**:
```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "annual_service_fee": 30000,
  "cpl": 160,
  "cpc": 6.5,
  "sem_replacement_value": 117000,
  "leads_inbound_value": 76800,
  "digital_asset_value": 27000,
  "total_business_value": 220800,
  "roi_pct": 636.0,
  "roi_multiplier": 7.36,
  "renewal_health": {
    "score": 95,
    "grade": "极高概率续约",
    "tier_advice": "当前各项指标处于行业前 10%，客户满意度极高。建议在服务到期前 30 天呈递《年度深度防守与矩阵裂变增购提案》。",
    "talking_points": [
      "已实现 60%~100% SOV 首选推荐，年化替代传统竞价预算超过 11 万元；",
      "全网沉淀 4 大高权重信任池外链资产，大模型 Citation 稳居第一；",
      "续约增购可扩展至集团矩阵多子品牌与 15 组追问裂变词库。"
    ]
  }
}
```

### ② `POST /api/projects/{id}/roi/settings`
- **Request**:
```json
{
  "annual_service_fee": 35000,
  "cpl": 180,
  "cpc": 7.0
}
```
