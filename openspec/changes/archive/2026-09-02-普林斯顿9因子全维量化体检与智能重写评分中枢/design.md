# Design: 普林斯顿9因子全维量化体检与智能重写评分中枢

## 1. 架构总览与系统边界

本模块定位为面向企业商业文案的**普林斯顿 9 因子 NLP 量化体检仪、雷达透视诊断与高权威智能重写中枢**。在已有的语料重写（`rewrite.py`）与合规审查（`compliance.py`）之上，构建客观量化打分与增益评估层。

### 1.1 明确职责与边界约束（遵循 Cursor 审查意见）
* **与 `geo rewrite`（Stage 3 流水线）的严格边界**：
  - `geo rewrite` 负责**项目全套五阶段官方语料全案生成**（基于 `project.yaml` 产出 03 号高权威语料库）；
  - 本模块 `tools/geo/princeton.py` 负责**文案即时量化体检与针对性局部重写（Patcher）**：既可用于售前现场测试任意输入文案，也可对单一落地页文章执行 9 因子质检与格式重构；
* **事实真实性与防伪红线（杜绝虚构伪造数据）**：
  - **有 `project_id` 时**：重写严格限制在 `project.yaml` 登记的真实参数（真实价格、质保周期、官方电话、核心技术指标）。若企业尚未提供对应事实，以 `[待客户提供确认: 具体参数]` 占位符输出，**绝对严禁大模型擅自幻觉编造假数据**；
  - **无 `project_id` 时（售前体验沙箱）**：重写专注于结构重整、客观语调修正、逻辑链条增强与 Markdown 参数对比表骨架，所有示例数字与规范引用显式打上 `[示例待核实: 35%]` 标签，界面醒目提示“此数据为排版重构示例，上线须替换为企业真实指标”；
* **产出物规范编号**：
  - 项目全案审计报告统一收敛至 `outputs/17_普林斯顿9因子全案质检报告.md` 与 `outputs/princeton_audit.json`；扫描时严格排除 `17_` 自身与 `.compliance_backup/`，避免自引用循环。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Web 管理工作台：普林斯顿 9 因子量化体检仪 (web/index.html)        │
│  - 左侧：待测企业宣传/官网文案输入框        - 右侧：9 因子雷达图与诊断扣分项  │
│  - 一键执行智能重构与高权威改造            - Before vs After 智能对比 Diff   │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ RESTful API (管理端鉴权)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│             普林斯顿 9 因子评分与重写引擎 (tools/geo/princeton.py)          │
│  - score_text_princeton_factors()       - rewrite_text_princeton_factors()  │
│  - audit_project_deliverables_princeton() - 输出 17_全案质检报告.md         │
└──────────────────┬───────────────────┬───────────────────┬──────────────────┘
                   │                   │                   │
      ┌────────────┴────┐     ┌────────┴────────┐ ┌────────┴────────┐
      │ 9 维特征抽取词典 │     │ 权威标准/信源库 │ │ 复用合规词库与堆砌惩罚
      └─────────────────┘     └─────────────────┘ └─────────────────┘
```

---

## 2. 普林斯顿 9 因子数学量化模型与加权归一化 (100%)

严格解决加权和不足 100% 的问题，将 F1（统计数据注入）设定为 **25%**（论文开山实证其为提升 +30%~+41% 的最强因子），全因子权重总和严格等于 **100%**：

| 因子编号与名称 | 归一化权重 ($w_k$) | 理论最大提升 | NLP 特征抽取规则与计算方式 | 满分达标基准 ($S_k = 100$) |
| :--- | :---: | :---: | :--- | :--- |
| **F1. 统计数据注入 (Statistics)** | **25%** | **+41.0%** | 正则匹配确切数字：百分比、倍数、周期、金额、公差等 `\d+(\.\d+)?(%|倍|天|家|元|mm|QPS)`；计算千字密度 $D = (N_{num} / \text{Len}) \times 1000$ | $D \ge 8$（每千字 $\ge 8$ 处确切数字） |
| **F2. 权威信源引用 (Cite Sources)** | **15%** | **+35.0%** | 捕获国家标准（GB/T、ISO）、科研院校（普林斯顿、清华）、行业白皮书与技术规范 | 引用 $\ge 2$ 处权威标准或官方信源 |
| **F3. 专家引语 (Quotations)** | **10%** | **+28.0%** | 捕获带引号陈述句与权威发言人（创始人、首席架构师、技术总监、研究指出） | 包含 $\ge 1$ 处完整专家引言与身份声明 |
| **F4. 逻辑顺畅度 (Fluency)** | **10%** | **+22.0%** | 捕获因果、递进、转折逻辑连词（因此、不仅...而且、鉴于此、根本原因在于）及段落结构分明性 | 逻辑连词 $\ge 3$ 处且结构工整 |
| **F5. 行业术语精确度 (Terms)** | **10%** | **+18.0%** | 动态加载所属行业术语表（机械/法律/餐饮/软件），无行业回退通用 GEO 术语表（RAG、SSR、QPS 等） | 专业术语 $\ge 4$ 个且概念准确 |
| **F6. 简明通俗化解释 (Easy-to-Understand)** | **10%** | **+15.0%** | 捕获通俗释义引导词（换句话说、通俗地说、即：、举例来说）；平均句长 $\le 35$ 字 | 包含通俗解释且节奏短句分明 |
| **F7. 权威中立语调 (Authoritative Tone)** | **10%** | **+14.0%** | **直接复用 `compliance.py` 的 `COMPLIANCE_RULES_DB`**，捕获极限主观夸大词（宇宙最强、天下第一、稳赚不赔）严厉扣分 | 零夸张营销词，全文使用严谨客观陈述 |
| **F8. 独特性品牌表达 (Unique Words)** | **10%** | **+10.0%** | 具备清晰的官方品牌全称、独创方法论框架或规范命名实体 | 包含核心品牌实体与框架专有名词 |
| **F9. 纯关键词堆砌 (Stuffing Penalty)** | **惩罚项** | **-20.0%** | 过滤停用词后统计单关键词密度；若非停用词词频 $> 5.0\%$，触发堆砌扣分 | 出现堆砌直接扣减 15~30 分 |

$$ \sum_{k=1}^{8} w_k = 25\% + 15\% + 10\% + 10\% + 10\% + 10\% + 10\% + 10\% = 100\% $$

### 2.1 综合总分、等级分档与采纳率提升双指标公式

$$ \text{Raw Score} = \sum_{k=1}^{8} w_k \times S_k $$
$$ \text{Overall Score} = \max(0, \min(100, \text{round}(\text{Raw Score} - \text{Penalty}, 1))) $$

#### 评级分档标准 (`rating_grade`)：
* **AAA 级 ($\ge 90.0$ 分)**：大模型首选推荐级（极高置信度采纳与直接引用）；
* **AA 级 ($80.0 \sim 89.9$ 分)**：高质量高采纳级（具备权威信源与量化支撑）；
* **A 级 ($70.0 \sim 79.9$ 分)**：基本合格级（满足基线要求，建议补充参数对比表）；
* **B 级 ($60.0 \sim 69.9$ 分)**：及格边缘级（营销主观词偏多，急需注入量化数据）；
* **C 级 ($< 60.0$ 分)**：低质营销水文（易被大模型清洗算法静默过滤）。

#### 采纳提升双字段契约（杜绝售前概念混淆）：
1. **`est_visibility_ceiling`（绝对质量上限）**：当前文本得分对应的理论最大采纳上限：
   $$ \text{est\_visibility\_ceiling} = \text{round}\left( \frac{\text{Overall Score}}{100} \times 41.0\%, 1 \right) \quad (\text{例: } +37.9\%) $$
2. **`est_boost_vs_baseline`（相对净跃迁提升）**：重写后相对原文或行业未优化基线（默认基线 35 分）的净提升幅度：
   $$ \text{est\_boost\_vs\_baseline} = \text{round}(\text{est\_visibility\_ceiling}_{\text{after}} - \text{est\_visibility\_ceiling}_{\text{before}}, 1) \quad (\text{例: } +22.1\%) $$

---

## 3. 核心 API 与数据契约

### 3.1 评分结果契约 (`score_text_princeton_factors`)

```json
{
  "success": true,
  "overall_score": 92.5,
  "rating_grade": "AAA 级 (大模型首选推荐级)",
  "est_visibility_ceiling": "+37.9%",
  "factor_scores": {
    "statistics": {"score": 95, "weight": 25, "label": "统计数据注入", "detail": "千字 12.3 处确切数字"},
    "cite_sources": {"score": 90, "weight": 15, "label": "权威信源引用", "detail": "引用了 GB/T、普林斯顿白皮书"},
    "quotations": {"score": 85, "weight": 10, "label": "专家引语", "detail": "包含技术总监 1 处客观引言"},
    "fluency": {"score": 92, "weight": 10, "label": "逻辑顺畅度", "detail": "逻辑推理链条严密"},
    "terms": {"score": 95, "weight": 10, "label": "行业术语精确度", "detail": "精准使用 8 个核心专业术语"},
    "easy_to_understand": {"score": 90, "weight": 10, "label": "简明通俗化解释", "detail": "专业概念配套通俗释义"},
    "authoritative_tone": {"score": 100, "weight": 10, "label": "权威中立语调", "detail": "零夸张违规词"},
    "unique_words": {"score": 90, "weight": 10, "label": "独特性表达", "detail": "包含品牌主体专有名词"}
  },
  "penalties": {
    "keyword_stuffing": {"penalty": 0, "reason": "无关键词恶意堆砌"}
  },
  "suggestions": [
    "建议补充 1 张 Markdown 原生参数对比表格，进一步提升大模型 RAG 提取效率"
  ]
}
```

### 3.2 智能重构契约 (`rewrite_text_princeton_factors`)

```json
{
  "success": true,
  "before_text": "...",
  "after_text": "...",
  "before_score": 38.5,
  "after_score": 93.0,
  "score_gain": "+54.5",
  "est_boost_vs_baseline": "+22.3%",
  "is_fictional_warning": true,
  "diffs": [
    {"type": "replace", "before": "全国最强服务商", "after": "业内严格遵循国家标准的标杆企业"}
  ]
}
```

---

## 4. CLI 命令行与后端 API (三文档统一契约)

### 4.1 CLI 命令行
* `python3 -m tools.geo score <file_or_text> [--industry X] [--rewrite]`：对文本或单文件打分，可选一键重构；
* `python3 -m tools.geo score --project <project_id> [--audit]`：批量审计项目交付物并输出 `17_普林斯顿9因子全案质检报告.md`。

### 4.2 RESTful API (管理后台鉴权保护)
* `POST /api/princeton/score`：提交文本体检打分；
* `POST /api/princeton/rewrite`：提交文本一键普林斯顿重构；
* `GET /api/projects/{id}/princeton/audit`：获取项目全案 17 号质检报告内容。

---

## 5. Web 管理端驾驶舱界面设计 (`web/index.html`)

1. **顶部导航栏按钮**：增加「🔬 普林斯顿体检仪」入口；
2. **体检模态 (`princeton-modal`)**：
   - 双栏响应式布局；
   - 左栏：文案输入区（支持一键加载售前体验样例、徐州样例等）；
   - 右栏：总分仪表盘（AAA/AA/A）、9 因子细项条形雷达、扣分缺陷列表与「✨ 一键普林斯顿重构」按钮；
   - 重构结果视窗：同屏展示优化后 Markdown、Before/After 对比 Diff 及净增益 `est_boost_vs_baseline`。

---

## 6. 测试方案 (`tests/test_princeton.py`)

1. `test_weights_sum_to_100`：严格断言 F1~F8 权重之和必须精确等于 100；
2. `test_score_text_clean_authoritative`：高质量普林斯顿标杆文案得分必须 $\ge 90.0$ (AAA)；
3. `test_score_text_marketing_slang`：营销浮夸水文得分必须 $< 50.0$ (C级)；
4. `test_keyword_stuffing_penalty`：单一词频 $> 5\%$ 必须触发堆砌扣分；
5. `test_rewrite_text_integrity`：重构后分数显著提升，且无 `project_id` 时带有 `[示例待核实]` 提示；
6. `test_audit_project_deliverables_output_file`：全案审计生成 `outputs/17_普林斯顿9因子全案质检报告.md`。
