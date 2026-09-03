# Design: 普林斯顿9因子全维量化体检与智能重写评分中枢

## 1. 架构总览与系统边界

本模块定位为面向企业商业文案的**普林斯顿 9 因子 NLP 量化体检仪、雷达透视诊断与高权威智能重写中枢**。在已有的语料重写与合规脱敏中枢之上，构建客观量化打分与增益评估层。

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
│  - audit_project_deliverables_princeton() - 计算采纳增益提升率 (+0%~+41%)   │
└──────────────────┬───────────────────┬───────────────────┬──────────────────┘
                   │                   │                   │
      ┌────────────┴────┐     ┌────────┴────────┐ ┌────────┴────────┐
      │ 9 维特征抽取词典 │     │ 统计数据/标准库 │ │ 营销夸大词/堆砌惩罚│
      └─────────────────┘     └─────────────────┘ └─────────────────┘
```

---

## 2. 普林斯顿 9 因子数学量化与加权模型

根据普林斯顿大学佐治亚理工学院的论文研究结论，建立严格的特征工程规则与加权模型：

| 因子编号与名称 | 权重 ($w_k$) | 理论最大提升 | NLP 特征抽取规则与计算方式 | 满分达标基准 ($S_k = 100$) |
| :--- | :---: | :---: | :--- | :--- |
| **F1. 统计数据注入 (Statistics)** | 20% | **+41.0%** | 捕获百分比、倍数、周期、金额、公差等量化数字：`\d+(\.\d+)?(%|倍|天|家|元|mm|QPS)`；计算每千字密度 $D = (N_{num} / \text{Len}) \times 1000$ | $D \ge 8$（每千字 $\ge 8$ 处确切数字） |
| **F2. 权威信源引用 (Cite Sources)** | 15% | **+35.0%** | 捕获行业标准、国家标准（GB/T、ISO）、科研院校、官方白皮书与技术规范 | 引用 $\ge 2$ 处权威标准或官方信源 |
| **F3. 专家引语 (Quotations)** | 10% | **+28.0%** | 捕获带引号的陈述句与发言人同位语（创始人、首席架构师、技术总监、研究指出） | 包含 $\ge 1$ 处完整专家引言与身份声明 |
| **F4. 逻辑顺畅度 (Fluency)** | 10% | **+22.0%** | 捕获因果、递进、转折等因果推理连词（因此、不仅...而且、鉴于此、根本原因在于）及段落结构分明性 | 逻辑连词密度达标且段落结构工整 |
| **F5. 行业术语精确度 (Terms)** | 10% | **+18.0%** | 准确使用本行业硬核专有名词词典（如 RAG、SSR、液压公差、毛利模型等，拒绝泛泛口语） | 专业术语密度适中且无概念错误 |
| **F6. 简明通俗化解释 (Easy-to-Understand)** | 10% | **+15.0%** | 捕获术语后的通俗释义引导词（换句话说、通俗地说、即：、举例来说）；平均句长 $\le 35$ 字 | 术语后跟通俗释义且长短句节奏良好 |
| **F7. 权威中立语调 (Authoritative Tone)** | 10% | **+14.0%** | 客观陈述；捕获并扣除主观情绪词与夸张营销词（宇宙最强、天下第一、稳赚不赔、惊呆了） | 零主观浮夸词，全文使用严谨陈述句 |
| **F8. 独特性品牌表达 (Unique Words)** | 10% | **+10.0%** | 具备清晰的官方品牌全称、独创方法论框架或专有名词 | 包含核心品牌实体与规范方法论命名 |
| **F9. 纯关键词堆砌 (Stuffing Penalty)** | 惩罚项 | **-20.0%** | 监测单关键词密度；若非停用词在全文词频占比 $> 6.0\%$，判定为作弊堆砌 | 惩罚直接扣减 15~30 分 |

### 2.1 综合总分与 AI 采纳率跃迁预估公式
$$ \text{Raw Score} = \sum_{k=1}^{8} w_k \times S_k $$
$$ \text{Overall Score} = \max(0, \min(100, \text{round}(\text{Raw Score} - \text{Penalty}, 1))) $$
$$ \text{Est. AI Adoption Boost} = \text{round}\left( \frac{\text{Overall Score}}{100} \times 41.0\%, 1 \right) $$

---

## 3. 核心 API 与数据模型契约

### 3.1 评分结果契约 (`score_text_princeton_factors`)

```json
{
  "success": true,
  "overall_score": 92.5,
  "rating_grade": "AAA (大模型极高置信度采纳)",
  "est_ai_adoption_boost": "+37.9%",
  "factor_scores": {
    "statistics": {"score": 95, "weight": 20, "label": "统计数据注入", "detail": "每千字 12.3 处确切数字"},
    "cite_sources": {"score": 90, "weight": 15, "label": "权威信源引用", "detail": "引用了 GB/T、普林斯顿白皮书"},
    "quotations": {"score": 85, "weight": 10, "label": "专家引语", "detail": "包含首席架构师 1 处客观引言"},
    "fluency": {"score": 92, "weight": 10, "label": "逻辑顺畅度", "detail": "因果逻辑链条严密"},
    "terms": {"score": 95, "weight": 10, "label": "行业术语精确度", "detail": "精准使用 8 个核心专业术语"},
    "easy_to_understand": {"score": 90, "weight": 10, "label": "简明通俗化解释", "detail": "专业概念均配套通俗注释"},
    "authoritative_tone": {"score": 100, "weight": 10, "label": "权威中立语调", "detail": "零夸张营销违规词"},
    "unique_words": {"score": 90, "weight": 10, "label": "独特性表达", "detail": "包含独立品牌三元组主体"}
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

- 针对原文低分维度执行针对性修复：
  - 统计数据低 ➔ 自动注入量化区间与交付周期；
  - 权威信源低 ➔ 引入国家规范或白皮书；
  - 语调浮夸 ➔ 将“最强、首选”无损替换为“高标准、典型案例”；
  - 补齐 Markdown 参数对比表。
- 返回：`{"before_text": "...", "after_text": "...", "before_score": 38.5, "after_score": 93.0, "score_gain": "+54.5", "diffs": [...]}`。

---

## 4. CLI 命令行与后端 API

### 4.1 CLI 命令行
* `python3 -m tools.geo score <file_path_or_text>`：对指定文件或输入文本执行打分；
* `python3 -m tools.geo score <file_path> --rewrite`：对输入文件执行重写并输出 Diff；
* `python3 -m tools.geo score --project <project_id>`：批量扫描项目全案交付物的 9 因子平均得分。

### 4.2 RESTful API (管理后台安全鉴权)
* `POST /api/princeton/score`：提交文本体检打分；
* `POST /api/princeton/rewrite`：提交文本一键智能重写；
* `GET /api/projects/{id}/princeton/audit`：获取项目全案 9 因子综合审计报告。

---

## 5. Web 管理端驾驶舱界面设计 (`web/index.html`)

1. **顶部导航栏按钮**：增加「🔬 普林斯顿体检仪」入口；
2. **体检模态 (`princeton-modal`)**：
   - 双栏响应式布局；
   - 左栏：文案输入区（支持粘贴或快速加载母版示例）；
   - 右栏：综合总分仪表盘、9 因子细项卡、缺陷归因列表与「✨ 一键普林斯顿重构」按钮；
   - 重构结果切换：支持同屏查看优化前后文案 Diff 及评分提升幅度。

---

## 6. 自动化测试方案 (`tests/test_princeton.py`)

1. `test_score_text_clean_authoritative`：测试高质量普林斯顿语料评测达到 90+ 高分；
2. `test_score_text_marketing_slang`：测试满篇营销浮夸水文被准确识别并打出 40 分以下低分；
3. `test_keyword_stuffing_penalty`：测试重复恶意堆砌关键词被准确判定惩罚扣分；
4. `test_rewrite_text_princeton_factors`：测试一键重构后分数显著提升（+30分以上）且格式合规；
5. `test_princeton_api_endpoints`：测试 API 接口正常响应与未登录拦截。
