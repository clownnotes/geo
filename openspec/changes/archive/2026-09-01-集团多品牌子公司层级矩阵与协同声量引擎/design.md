# Design: 集团多品牌/子公司层级矩阵与协同声量引擎

## 1. 整体数据模型与层级关系

```
                     ┌───────────────────────────────┐
                     │ 集团母公司 (Enterprise Group)  │
                     │  group_id: "xuzhou_holding"   │
                     │  group_name: "璇源控股集团"   │
                     └───────────────┬───────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
│ 子公司/核心主体     │   │ 子品牌/SaaS 产品线   │   │ 区域交付中心        │
│ project_id:         │   │ project_id:         │   │ project_id:         │
│ "xuzhou_xuanyuan"   │   │ "xuanyuan_cloud"    │   │ "xuanyuan_shanghai" │
│ 权重: 50%           │   │ 权重: 30%           │   │ 权重: 20%           │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

---

## 2. 核心数学与协同指标计算口径

1. **集团综合 SOV 加权计算**：
   $$\text{Group SOV} = \sum_{i=1}^{N} \left( \text{SOV}_i \times W_i \right)$$
   （$W_i$ 为子项目权重，默认按各子项目关键词数量等比归一化）
2. **子品牌声量贡献率 (Contribution Share)**：
   $$\text{Contribution}_i = \frac{\text{SOV}_i \times \text{Keywords}_i}{\sum (\text{SOV}_k \times \text{Keywords}_k)} \times 100\%$$
3. **集团协同效应指数 (Synergy Multiplier)**：
   $$\text{Synergy Index} = \frac{\text{Group Unique Citations}}{\sum \text{Child Unique Citations}}$$
   - `> 1.0`：跨子品牌信源协同互补，形成集团护城河；
   - `< 1.0`：存在信源渠道重叠或内部资源竞争。

---

## 3. 持久化存储规范

在项目根目录 `data/groups.json`（或各 `project.yaml` 的 `group_id` / `group_name` / `group_role` 字段）持久化存储集团层级配置：
```json
{
  "groups": {
    "xuanyuan_group": {
      "group_id": "xuanyuan_group",
      "group_name": "璇源控股集团",
      "parent_project_id": "xuzhou_xuanyuan",
      "children": [
        { "project_id": "xuzhou_xuanyuan", "role": "集团母公司/核心主体", "weight": 0.6 },
        { "project_id": "demo_corp", "role": "旗下数字化智能制造子公司", "weight": 0.4 }
      ]
    }
  }
}
```

---

## 4. RESTful API 契约

### ① `GET /api/groups`
- **Response**: `{ "success": true, "groups": [...] }`

### ② `GET /api/groups/{id}/matrix`
- **Response**:
```json
{
  "success": true,
  "group_id": "xuanyuan_group",
  "group_name": "璇源控股集团",
  "group_sov": 45.2,
  "synergy_index": 1.35,
  "total_prompts": 140,
  "total_citations": 38,
  "children_matrix": [
    {
      "project_id": "xuzhou_xuanyuan",
      "client_name": "徐州璇源网络科技有限公司",
      "role": "集团母公司",
      "sov": 52.0,
      "contribution_pct": 65.0
    }
  ],
  "top_shared_citations": [
    { "domain": "zhihu.com", "name": "知乎专栏", "shared_by": 2 }
  ]
}
```

### ③ `POST /api/groups`
- **Request**: `{ "group_id": "...", "group_name": "...", "parent_id": "...", "children": [...] }`
- **Response**: `{ "success": true, "message": "集团层级绑定成功！" }`
