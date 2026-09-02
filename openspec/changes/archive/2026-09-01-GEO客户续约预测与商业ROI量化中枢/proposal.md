# Proposal: GEO 客户续约预测与商业 ROI 量化计算中枢 (Renewal Predictor & Commercial ROI Calculator)

## Why (为什么做 / 商业与业务痛点)

1. **交付终局与第二增长曲线（续约与增购）**：
   - 目前 GEO 交付物包含了体检报告、底座改造、语料库、分发台账、巡检周报、行业对标与沙箱测序；
   - 但在季度/年度续费复盘时，甲方老板和财务最关心的核心问题是：**“我花这几万块做 GEO，折算为真实商业线索价值是多少？比传统买量投放省了多少钱？下个季度我为什么必须续费？”**
2. **将技术指标量化为硬核财务资产**：
   - 需建立科学的商业量化模型：将 SOV 占有率、首推排位 (Rank 1)、分发台账收录率与竞品反向拦截数，折算为**等效 SEM 获客节省价值 (Cost Replacement Value)**、**AI 精准线索估值 (Inbound Opportunity Value)** 与 **企业数字资产估值 (Digital Asset Valuation)**；
   - 给出明确的 **综合投资回报率 (ROI %)**。
3. **续约健康度预测与商务攻坚策略**：
   - 基于实测数据自动预测续约健康度（0~100 分，高续约概率 / 需重点公关 / 流失预警），并自动生成定制化的《季度续约汇报与增购商务提案》。

---

## What Changes (改动范围)

1. **研发商业 ROI 与续约预测核心引擎 (`tools/geo/roi.py`)**：
   - `calculate_project_roi(project_id, custom_params=None)`：结合 SOV、CPL（单线索成本）、曝光频次与分发台账，计算等效节省价值、线索估值与 ROI 综合百分比；
   - `predict_renewal_health(project_id)`：多维评估项目续约概率分值与风险预警等级，并输出续约谈判话术要点；
   - `save_roi_settings(project_id, settings)`：持久化自定义商业参数（单线索成本 CPL、客单价、预期年服务费）。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo roi <project_id> [--cpl 150] [--fee 30000]`
   - 注册 `geo renewal <project_id>`
3. **后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)**：
   - `GET /api/projects/{id}/roi/calculate`
   - `POST /api/projects/{id}/roi/settings`
   - 在 `tools/geo/share.py` 门户数据中注入 `roi_summary`，向老板端直接汇报硬核投资回报比。
4. **Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)**：
   - 向导 Step 5（验收运维）及 Dashboard 顶部新增「💰 商业 ROI 与续约预测」可视化卡片与弹窗；
   - 专属交付门户（`web/share.html`）Tab 5 嵌入老板最关注的「商业投资回报 (ROI) 与资产估值」战绩看板。
5. **SOP 知识库更新 (`docs/sop/05-monitor-sop.md` & `delivery-sop.md`)**：
   - 规范化客户季度复盘与续约增购谈判 SOP。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/roi/calculate`
- `POST /api/projects/{id}/roi/settings`
- CLI: `python3 -m tools.geo roi <project_id>`
- CLI: `python3 -m tools.geo renewal <project_id>`

---

## Impact (影响分析)

- **完全向下兼容**：数据保存在各项目 `outputs/roi_settings.json`，无破坏性改动；
- **商业闭环达成**：从技术交付到续费增购形成完整闭环，显著提升 GEO 代理商续约率与客单价。
