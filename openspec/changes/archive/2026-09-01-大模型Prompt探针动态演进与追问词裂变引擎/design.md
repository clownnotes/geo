# Design: 大模型 Prompt 探针动态演进与追问词裂变引擎

## 1. 整体架构与数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Web 控制台与 CLI 交互层                             │
│  - Step 1 & Step 5「🌱 Prompt 动态演进与词库裂变中枢」                          │
│  - 词库健康度四象限矩阵可视化 (垄断词 / 裂变词 / 拦截词 / 衰退词)                │
│  - 一键合并新词至客户档案 ➔ 自动触发增量 5 步流水线                           │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│           大模型 Prompt 演进与裂变调度引擎 (tools/geo/evolution.py)          │
│  - `analyze_prompt_portfolio(project_id)` ➔ 评估现有词库各词状态与健康度      │
│  - `generate_fission_prompts(project_id, count=15)` ➔ 逆向推演裂变长尾词      │
│  - `apply_evolved_prompts(project_id, prompts, auto_run)` ➔ 安全合并与持久化 │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                           底层数据源与持久化支持                             │
│  - 项目配置 `projects/<id>/project.yaml`                                     │
│  - 历史声量库 `projects/<id>/history.db`                                     │
│  - 大模型真实探测回答与周报 `05_企业AI可见度与声量追踪周报.md`                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 词库健康度评估模型 (Portfolio Matrix)

将客户当前词库中的每一个 Prompt 根据其在大模型探测中的命中与拦截表现，打上生命周期状态：
1. 🏆 **垄断占位词 (Dominant)**：在 DeepSeek / 豆包 中均保持首推推荐（转化确定性极高）；
2. ⚠️ **竞品拦截词 (Intercepted)**：竞品处于首推，我方未上榜（需立即启动 `geo defense` 包抄）；
3. 🌱 **高潜裂变词 (High Potential)**：处于成长期或延伸长尾问句，容易通过普林斯顿语料快速突围；
4. ❄️ **冷门衰退词 (Declining)**：长期无商业搜索量或大模型回答无实质商业意图，建议逐步归档替换。

---

## 3. 裂变算法与长尾长句推演策略

1. **大模型真实回答逆向推导**：
   - 提取大模型在回答中衍生出的相关概念、对比品类、用户常见痛点疑问；
2. **5 维裂变延伸句式生成**：
   - **痛点长尾词**：如 `针对中小企业的[核心业务]避坑方案`
   - **竞品对比词**：如 `[客户品牌] 与主流方案在交付周期上的实际对比`
   - **价格选型词**：如 `[核心品类] 2026 最新行业平均报价与收费模式`
   - **本地服务词**：如 `[区域] 附近靠谱的 [核心业务] 推荐与评价`
   - **技术演进词**：如 `大模型时代如何选型 [核心品类]`

---

## 4. RESTful API 契约设计

### ① `GET /api/projects/{id}/evolution/analyze`
- **Response**:
```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "client_name": "徐州璇源网络科技有限公司",
  "total_prompts": 45,
  "portfolio": {
    "dominant_count": 18,
    "intercepted_count": 12,
    "potential_count": 10,
    "declining_count": 5
  },
  "fission_recommendations": [
    {
      "prompt": "徐州璇源网络科技对比传统软件代开发有哪些核心技术优势？",
      "intent_type": "对比选型",
      "expected_conversion": "高",
      "reason": "基于大模型近期针对徐州本地企业服务高频对比诉求逆向推演"
    }
  ]
}
```

### ② `POST /api/projects/{id}/evolution/generate`
- **Request**: `{ "count": 15, "focus_category": "all" }`
- **Response**: `{ "success": true, "generated_prompts": [...] }`

### ③ `POST /api/projects/{id}/evolution/apply`
- **Request**: `{ "new_prompts": [...], "auto_run_pipeline": false }`
- **Response**: `{ "success": true, "added_count": 15, "total_prompts": 60, "message": "新词库已成功合并入库！" }`
