# Design: GEO多项目商业运营全景驾驶舱与代运营大盘报告中枢

## 1. 架构总览与系统边界

本项目定位为面向全案代运营团队、企业集团管理层与业务负责人的**跨项目全景商业运营、决策驾驶舱与报告生成中枢**。在已完成的 16 维资产与单项目商业结案中枢之上，构建全域聚合分析层。

### 1.1 明确系统职责与边界约束（遵循 Cursor 审查意见）
* **与现有 `patrol.py` 严格解耦、杜绝平行造轮子**：
  - 现网 `patrol.run_patrol_all`、`geo patrol --all`、`POST /api/patrol/trigger` 负责**底层重度执行**（重跑 `run_monitor`、写 SQLite、推送 Webhook）；
  - 本模块 `portfolio --patrol` 与 `/api/portfolio/patrol` **严格定位为「只读健康大盘聚合与风险红黑榜计算」**：优先只读各项目已落盘的 JSON 文件，极速计算风险分级（`normal` / `warning` / `danger`），不重跑 monitor、不写历史时序库、不发送重复 Webhook 报警；若用户需要重新探测外网，复用现网 `patrol.run_patrol_all`。
* **数据落盘优先与惰性补齐**：
  - 默认 100% 只读各项目 `outputs/` 下已生成的结构化 JSON，若个别老旧项目缺失 `acceptance_summary.json`，则调用对应模块函数惰性补算并即刻持久化回写，保障秒级聚合响应。
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

### 2.1 全域大盘指标与实盘 JSON 字段映射表 (Field Mapping Matrix)

为彻底杜绝“张冠李戴”与读错字段，本模块对内统一映射、对外严谨对齐实盘底层 Key：

| 聚合指标类别 | 聚合字段名 (`portfolio_summary`) | 底层实盘读取来源与字段 | 字段说明与缺省兜底策略 |
| :--- | :--- | :--- | :--- |
| **基础信息** | `project_id` | `project.yaml` ➔ `project_id` | 项目唯一标识符 |
| | `client_name` | `project.yaml` ➔ `client_name` | 企业客户法定全称 |
| | `industry` | `project.yaml` ➔ `industry` | 垂直所属行业 |
| **履约达成** | `fulfillment_score` | `acceptance_summary.json` ➔ `fulfillment_rate`<br>(回退: `calculate_fulfillment_score`) | 6 维合同商业加权履约分 (0~100) |
| | `is_passed` | `calculate_fulfillment_score` ➔ `is_passed` | 是否达 $\ge 90.0$ 全额结案回款线 |
| | `manifest_generation_pct` | `acceptance_summary.json` ➔ `manifest_summary.generation_rate_pct` | 16 维主交付物齐套率 (0~100%) |
| | `has_archive_zip` | `outputs/{pid}_geo_delivery_archive.zip` 存在性 | 全套离线 ZIP 归档包是否存在 |
| **声量战绩** | `raw_sov_pct` | `outputs/05_周报.json` 或 `monitor` ➔ `raw_sov_pct` | **真实实测 SOV**（无实测为 0.0%） |
| | `effective_sov_pct` | `roi_settings.json` 或 `roi` ➔ `metrics_summary.effective_sov_pct` | 综合折算 SOV（含行业投影基线） |
| | `is_projected_sov` | `roi` ➔ `metrics_summary.is_projected` | **声量是否为模型投影值**（重要标志） |
| | `gap_lead_score` | `competitor_gap_analysis.json` ➔ `radar_comparison.overall_gap_lead` | 领先主竞对综合分值（缺省为 null） |
| | `citation_authority_score`| `citation_authority_matrix.json` ➔ `overall_authority_score` | 9 因子信源权威度总分 (0~100) |
| **安全风控** | `injection_immunity_score` | `prompt_injection_guard.json` ➔ `immunity_score` | 品牌提示词注入免疫度 (0~100) |
| | `injection_threats_count` | `prompt_injection_guard.json` ➔ `total_threats` | 提示词注入威胁残留数 (应为 0) |
| | `compliance_violations` | `compliance_inspection.json` ➔ `total_violations` | **广告法合规违规残留数** (应为 0) |
| | `dead_links_count` | `citation_authority_matrix.json` ➔ `dead_backlinks` 或 `dist_ledger.json` | 矩阵外发渠道死链总数 (应为 0) |
| **财务商业** | `annual_service_fee` | `roi_settings.json` ➔ `financial_valuation.annual_service_fee` | 年度 GEO 服务费合同额 (元) |
| | `sem_replacement_value` | `roi_settings.json` ➔ `financial_valuation.sem_replacement_value` | 等效 SEM 竞价替代年化节省 (元) |
| | `leads_inbound_value` | `roi_settings.json` ➔ `financial_valuation.leads_inbound_value` | AI 首推销售线索商机估值 (元) |
| | `digital_asset_value` | `roi_settings.json` ➔ `financial_valuation.digital_asset_value` | 权威信任池数字资产估值 (元) |
| | `total_business_value` | `roi_settings.json` ➔ `financial_valuation.total_business_value` | 商业创造年化总价值 (元) |
| | `roi_pct` | `roi_settings.json` ➔ `financial_valuation.roi_pct` | 单项目投资回报率 (%) |
| | `renewal_health_score` | `roi_settings.json` ➔ `renewal_health.score` | 续约健康度评分 (0~100) |
| | `renewal_grade` | `roi_settings.json` ➔ `renewal_health.grade` | 续约健康等级文案 |

---

## 3. 严谨财务量化公式与风险分级评估模型

### 3.1 财务大盘量化计算公式（杜绝虚假算术平均）

在代运营商业大盘中，对投资回报率做简单算术平均在财务统计上失真且无效，本引擎确立严格的**组合投资回报率 (Portfolio ROI)** 算法：

$$ \text{Total Business Value} = \sum_{i=1}^{N} \text{total\_business\_value}_i $$
$$ \text{Total Service Fee} = \sum_{i=1}^{N} \text{annual\_service\_fee}_i $$
$$ \text{Portfolio ROI \%} = \frac{\text{Total Business Value} - \text{Total Service Fee}}{\text{Total Service Fee}} \times 100\% $$

* **组合投资回报率 (`portfolio_roi_pct`)**：以全盘总创造价值减去总服务费投入除以总服务费投入计算，真实反映代运营资金杠杆效率；
* **单项目平均 ROI (`avg_project_roi_pct`)**：仅作为辅助统计展示，并明确标注为“各项目单项均值”。
* **实盘数据量级**：四大垂直行业母版加总年度服务费为 **¥67,200 元**，创造年化总商业价值约 **¥918,580 元**，净增收益 **¥851,380 元**，全盘组合 ROI 约为 **+1266.9%**。

### 3.2 动态三级风险分级评估模型 (`risk_level`)

针对 Cursor 提出的“投影声量不能当实测”审查意见，本模型优先基于 `raw_sov_pct`，当声量处于投影状态时绝不因投影高分误判为优良：

```python
def evaluate_project_risk(p_card: dict) -> tuple:
    """
    动态评估项目健康度
    返回: (risk_level, risk_reasons)
    risk_level: "danger" | "warning" | "normal"
    """
    reasons = []
    
    # 1. 红色高危指标 (Danger)
    if p_card.get("compliance_violations", 0) > 0:
        reasons.append(f"存在 {p_card['compliance_violations']} 处广告法违规风险")
    if p_card.get("injection_threats_count", 0) > 0:
        reasons.append(f"存在 {p_card['injection_threats_count']} 处提示词注入安全隐患")
    if p_card.get("dead_links_count", 0) >= 3:
        reasons.append(f"外发渠道死链超标 ({p_card['dead_links_count']} 条)")
    if p_card.get("raw_sov_pct", 0.0) > 0 and p_card["raw_sov_pct"] < 30.0:
        reasons.append(f"实测声量严重低迷 ({p_card['raw_sov_pct']}%)")
    
    if reasons:
        return "danger", reasons

    # 2. 黄色预警指标 (Warning)
    # 徐州标杆项目：89.3 分未达 90 分全额线，且续约得分 64，准确进入 Warning
    if not p_card.get("is_passed", False) or p_card.get("fulfillment_score", 0) < 90.0:
        reasons.append(f"履约分未过全额回款线 ({p_card.get('fulfillment_score')} 分)")
    if p_card.get("renewal_health_score", 100) < 70:
        reasons.append(f"续约健康度偏低 ({p_card.get('renewal_health_score')} 分 · {p_card.get('renewal_grade', '')})")
    if p_card.get("is_projected_sov", False):
        reasons.append("AI 声量处于行业投影期 (待配置 API 真实轮询)")
    elif p_card.get("raw_sov_pct", 0.0) < 60.0:
        reasons.append(f"实测声量爬坡中 ({p_card.get('raw_sov_pct')}% < 60%)")

    if reasons:
        return "warning", reasons

    # 3. 绿色优良 (Normal)
    return "normal", ["各项指标健康达标"]
```

---

## 4. 核心功能实现逻辑与代码组织

### 4.1 核心模块 (`tools/geo/portfolio.py`)

1. **`scan_managed_projects() -> list[str]`**：
   - 扫描 `PROJECTS_DIR` 下所有目录；
   - 严格跳过 `_template`、`.` 开头的隐藏目录、缺少 `project.yaml` 或 `load_project_config` 解析失败的目录；
   - 对齐现网 `patrol.run_patrol_all` 的安全边界。
2. **`get_portfolio_summary() -> dict`**：
   - 遍历合法项目列表，优先从落盘 JSON 提取各项关键指标；
   - 聚合计算宏观 4 大维度（规模、声量、安全、财务组合 ROI）；
   - 输出完整的 `project_cards` 与全局 KPI。
3. **`run_portfolio_health_patrol() -> dict`**：
   - **轻量只读巡检**：遍历全量项目最新落盘状态，快速输出全域风险红黑榜（`danger_list`, `warning_list`, `healthy_list`）；
   - 零副作用：不调外部 API、不发 Webhook，毫秒级响应。
4. **`generate_portfolio_executive_report() -> dict`**：
   - 采用普林斯顿 9 因子结构化编写，自动保存至 `reports/GEO代运营全域多项目执行与商业回报大盘报告.md`；
   - 自动生成目录、全盘宏观 KPI 表、四大母版对比矩阵、风险整改台账与下阶段投资建议。

---

## 5. 后端 API 与 CLI 契约

### 5.1 CLI 命令行
* `python3 -m tools.geo portfolio`：使用 ANSI 表格高保真打印全域 KPI 与多项目矩阵；
* `python3 -m tools.geo portfolio --patrol`：执行只读健康扫描并打印风险红黑榜；
* `python3 -m tools.geo portfolio --report`：生成并落盘月度大盘报告。

### 5.2 后端 RESTful API (管理端安全鉴权)
* `GET /api/portfolio/summary`：返回全局大盘聚合数据（需管理员登录鉴权）；
* `POST /api/portfolio/patrol`：执行健康聚合巡检并返回红黑榜；
* `GET /api/portfolio/report`：返回大盘报告 Markdown 内容与下载路径。

---

## 6. Web 控制台驾驶舱界面升级 (`web/index.html`)

1. **首页顶部指标条升级**：
   - 将原占位性质的硬编码卡片「平均 AI 声量提升 +100.0%」平滑升级为**「全域年化商业价值」**（动态显示 `¥918,580`）与**「组合投资回报率」**（动态显示 `+1266.9%`），保持 7 列网格布局不被挤爆。
2. **全局大盘驾驶舱模态 (`portfolio-modal`)**：
   - 顶部导航栏新增「📊 全域大盘驾驶舱」按钮；
   - 弹出全屏驾驶舱模态框，包含四大 KPI 卡、多项目横向对比矩阵、风险徽章与一键导出大盘报告入口。

---

## 7. 测试方案 (`tests/test_portfolio.py`)

1. `test_scan_managed_projects`：验证准确识别四母版并跳过 `_template` 与非法目录；
2. `test_get_portfolio_summary_financials`：验证财务加总（全盘服务费、全盘总价值、组合 ROI% 计算）；
3. `test_project_risk_evaluation_honesty`：验证徐州（89.3分）判定为 `warning`，其他三大母版判定为 `normal`，投影声量标识有效；
4. `test_generate_portfolio_executive_report`：验证报告输出至 `reports/` 且包含四大母版数据；
5. `test_portfolio_api_endpoints`：验证 HTTP API 正确响应。
