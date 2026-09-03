# Design: GEO多项目商业运营全景驾驶舱与代运营大盘报告中枢

## 1. 架构总览与系统边界

本项目定位为面向全案代运营团队、企业集团管理层与业务负责人的**跨项目全景商业运营、决策驾驶舱与报告生成中枢**。在已完成的 16 维资产与单项目商业结案中枢之上，构建全域聚合分析层。

### 1.1 明确系统职责与边界约束（遵循 Cursor 审查意见）
* **与现有 `patrol.py` 严格解耦、杜绝平行造轮子**：
  - 现网 `patrol.run_patrol_all`、`geo patrol --all`、`POST /api/patrol/trigger` 负责**底层重度执行**（重跑 `run_monitor`、写 SQLite、推送 Webhook）；
  - 本模块 `portfolio --patrol` 与 `/api/portfolio/patrol` **严格定位为「只读健康大盘聚合与风险红黑榜计算」**：优先只读各项目已落盘的 JSON 文件，极速计算风险分级（`normal` / `warning` / `danger`），不重跑 monitor、不写历史时序库、不发送重复 Webhook 报警；若用户需要重新探测外网，复用现网 `patrol.run_patrol_all`。
* **数据落盘优先与真实函数提取**：
  - 履约达成率优先读 `acceptance_summary.json`，缺失则调用 `calculate_fulfillment_score(pid)`；
  - 财务估值与续约健康度优先调用 `calculate_project_roi(pid)`（实盘 `roi_settings.json` 仅存 5 项参数，估值由该计算器统一产出），确保估值与续约打分 100% 真实不硬编码；
  - 攻防、权威度、合规严格读取对应落盘 JSON。
* **报告路径规范**：
  - 大盘月报收敛在项目统一报告目录 `reports/GEO代运营全域多项目执行与商业回报大盘报告.md`，严禁随意污染代码仓库根目录。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Web 管理工作台：全域大盘驾驶舱 (web/index.html)            │
│  - 4 维宏观 KPI 卡片 (规模 / 声量 / 安全 / 财务组合ROI)  - 多项目横向对比矩阵│
│  - 全盘风险预警雷达 (红黑榜)                          - 一键导出大盘执行月报  │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ RESTful API (管理端鉴权)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                  多项目商业运营聚合引擎 (tools/geo/portfolio.py)            │
│  - get_portfolio_summary()              - run_portfolio_health_patrol()     │
│  - generate_portfolio_executive_report() - 组合 ROI% 与 Σ 财务总价值测算   │
└──────────────────┬───────────────────┬───────────────────┬──────────────────┘
                   │                   │                   │
      ┌────────────┴────┐     ┌────────┴────────┐ ┌────────┴────────┐
      │ 徐州软件标杆母版 │     │ B2B重工机械母版 │ │ 本地律所/餐饮母版│ ... 过滤 _template
      │ xuzhou_xuanyuan │     │ b2b_machinery   │ │ local_legal etc │
      └─────────────────┘     └─────────────────┘ └─────────────────┘
```

---

## 2. 字段映射契约与实盘数据模型

### 2.1 全域大盘指标与实盘读取来源映射表 (Field Mapping Matrix)

严格对齐实盘真实读取源，杜绝编造字段：

| 聚合指标类别 | 聚合字段名 (`portfolio_summary`) | 底层实盘读取来源与逻辑 | 字段说明与缺省兜底策略 |
| :--- | :--- | :--- | :--- |
| **基础信息** | `project_id` | `project.yaml` ➔ `client_id` 或 `project_id` | 项目唯一标识符 |
| | `client_name` | `project.yaml` ➔ `client_name` | 企业客户法定全称 |
| | `industry` | `project.yaml` ➔ `industry` | 垂直所属行业 |
| **履约达成** | `fulfillment_score` | `acceptance_summary.json` ➔ `fulfillment_rate`<br>(回退: `calculate_fulfillment_score`) | 6 维合同商业加权履约分 (0~100) |
| | `is_passed` | 同上 ➔ `is_passed` | 是否达 $\ge 90.0$ 全额结案回款线 |
| | `manifest_generation_pct` | `acceptance_summary.json` ➔ `manifest_summary.generation_rate_pct` | 16 维主交付物齐套率 (0~100%) |
| | `has_archive_zip` | `outputs/{pid}_geo_delivery_archive.zip` 存在性 | 全套离线 ZIP 归档包是否存在 |
| **声量战绩** | `raw_sov_pct` | `calculate_project_roi` ➔ `metrics_summary.raw_sov_pct` | **真实实测 SOV**（无实测为 0.0%） |
| | `effective_sov_pct` | `calculate_project_roi` ➔ `metrics_summary.effective_sov_pct` | 综合折算 SOV（含行业投影基线） |
| | `is_projected_sov` | `calculate_project_roi` ➔ `metrics_summary.is_projected` | **声量是否为模型投影值** |
| | `gap_lead_score` | `competitor_gap_analysis.json` ➔ `radar_comparison.overall_gap_lead` | 领先主竞对综合分值（缺省为 null） |
| | `citation_authority_score`| `citation_authority_matrix.json` ➔ `overall_authority_score` | 9 因子信源权威度总分 (0~100) |
| **安全风控** | `injection_immunity_score` | `prompt_injection_guard.json` ➔ `immunity_score` | 品牌提示词注入免疫度 (0~100) |
| | `injection_threats_count` | `prompt_injection_guard.json` ➔ `total_threats` | 提示词注入威胁残留数 (应为 0) |
| | `compliance_violations` | `compliance_inspection.json` ➔ `total_violations` | **广告法合规违规残留数** (应为 0) |
| | `dead_links_count` | `citation_authority_matrix.json` ➔ `dead_backlinks` (主源) | 矩阵外发渠道死链总数 (应为 0) |
| **财务商业** | `annual_service_fee` | `calculate_project_roi` ➔ `financial_valuation.annual_service_fee` | 年度 GEO 服务费合同额 (元) |
| | `sem_replacement_value` | 同上 ➔ `financial_valuation.sem_replacement_value` | 等效 SEM 竞价替代年化节省 (元) |
| | `leads_inbound_value` | 同上 ➔ `financial_valuation.leads_inbound_value` | AI 首推销售线索商机估值 (元) |
| | `digital_asset_value` | 同上 ➔ `financial_valuation.digital_asset_value` | 权威信任池数字资产估值 (元) |
| | `total_business_value` | 同上 ➔ `financial_valuation.total_business_value` | 商业创造年化总价值 (元) |
| | `roi_pct` | 同上 ➔ `financial_valuation.roi_pct` | 单项目投资回报率 (%) |
| | `renewal_health_score` | `calculate_project_roi` ➔ `renewal_health.score` | 续约健康度评分 (0~100) |
| | `renewal_grade` | 同上 ➔ `renewal_health.grade` | 续约健康等级文案 |

---

## 3. 严谨财务量化公式与风险分级评估模型

### 3.1 财务大盘量化计算公式（严格组合投资回报率）

$$ \text{Total Business Value} = \sum_{i=1}^{N} \text{total\_business\_value}_i $$
$$ \text{Total Service Fee} = \sum_{i=1}^{N} \text{annual\_service\_fee}_i $$
$$ \text{Portfolio ROI \%} = \frac{\text{Total Business Value} - \text{Total Service Fee}}{\text{Total Service Fee}} \times 100\% $$

* **组合投资回报率 (`portfolio_roi_pct`)**：以全盘总创造价值减去总服务费投入除以总服务费投入计算；
* **单项目平均 ROI (`avg_project_roi_pct`)**：作为辅助单项均值展示；
* **实盘数据量级**：全托管项目加总年度服务费为 **¥84,000 元**，创造年化总商业价值为 **¥1,115,450 元**，净增收益 **¥1,031,450 元**，全盘组合 ROI 约为 **+1227.9%**。

### 3.2 动态三级风险分级评估模型 (`risk_level`)

锁定方案 ①：**投影声量仅作为状态附注标签，不单独构成 warning**；徐州项目因履约 89.3 分 (<90) 和续约 64 分精准判定为 `warning`，其余三大母版（履约 97.9、续约 95、零安全合规问题）准确判定为 `normal`：

```python
def evaluate_project_risk(p_card: dict) -> tuple:
    """
    根据项目运行指标动态判定风险等级与归因清单 (严格对齐 Cursor 审查契约)
    返回: (risk_level, risk_reasons)
    risk_level: "danger" | "warning" | "normal"
    """
    reasons = []

    # 1. 红色高危 (Danger)
    if p_card.get("compliance_violations", 0) > 0:
        reasons.append(f"存在 {p_card['compliance_violations']} 处广告法违规风险")
    if p_card.get("injection_threats_count", 0) > 0:
        reasons.append(f"存在 {p_card['injection_threats_count']} 处提示词注入安全隐患")
    if p_card.get("dead_links_count", 0) >= 3:
        reasons.append(f"外链渠道死链超标 ({p_card['dead_links_count']} 条)")
    if not p_card.get("is_projected_sov", False) and p_card.get("raw_sov_pct", 0.0) < 30.0 and p_card.get("raw_sov_pct", 0.0) > 0:
        reasons.append(f"实测声量严重偏低 ({p_card['raw_sov_pct']}%)")

    if reasons:
        return "danger", reasons

    # 2. 黄色预警 (Warning)
    if not p_card.get("is_passed", False) or p_card.get("fulfillment_score", 0) < 90.0:
        reasons.append(f"履约分未过全额结案线 ({p_card.get('fulfillment_score')} 分)")
    if p_card.get("renewal_health_score", 100) < 70:
        reasons.append(f"续约健康度偏低 ({p_card.get('renewal_health_score')} 分 · {p_card.get('renewal_grade', '')})")
    if not p_card.get("is_projected_sov", False) and p_card.get("raw_sov_pct", 0.0) < 60.0 and p_card.get("raw_sov_pct", 0.0) > 0:
        reasons.append(f"实测声量爬坡培育中 ({p_card.get('raw_sov_pct')}% < 60%)")

    if reasons:
        return "warning", reasons

    # 3. 绿色优良 (Normal)
    reasons_ok = ["各项交付与运营指标均健康达标"]
    if p_card.get("is_projected_sov", False):
        reasons_ok.append("AI 声量处于行业投影培育期 (待配置真实 API 轮询)")
    return "normal", reasons_ok
```

---

## 4. Web 控制台驾驶舱界面设计 (`web/index.html`)

锁定方案 (a)：**单卡双行展示，严格保持 7 列网格布局**：
* 原第 3 张占位的硬编码「平均 AI 声量提升 +100.0%」卡片替换为：
  - 顶部主标题：「全域商业总价值」；
  - 中间大字：「¥1,115,450 元」；
  - 底部副行：「组合 ROI: +1227.9% (13.28x)」；
  - 点击直接弹出全域大盘驾驶舱模态框；
* 布局完全维持原有的 `2xl:grid-cols-7`，杜绝页面溢出挤爆；
* 顶部导航栏增加「📊 全域大盘驾驶舱」按钮。
