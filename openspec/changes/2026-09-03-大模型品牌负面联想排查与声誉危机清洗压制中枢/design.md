# Design: 大模型品牌负面联想排查与声誉危机清洗压制中枢 (Technical Design)

## 1. 架构定位与模块职责划分

```mermaid
flowchart TD
    subgraph S1["对抗性负面探针矩阵 (5大维度)"]
        P1["1. 合法资质与皮包质疑探针"]
        P2["2. 服务质量与烂尾跑路探针"]
        P3["3. 报价虚高与乱收费纠纷探针"]
        P4["4. 竞对恶意拉踩对比探针"]
        P5["5. 负面谣言与黑历史传闻探针"]
    end

    subgraph S2["调度层与底座复用 (tools/geo/llm.py)"]
        M1["字节豆包 (Doubao)"]
        M2["深度求索 (DeepSeek)"]
        M3["月之暗面 (Kimi)"]
        M4["高保真确定性沙箱 (Sandbox)"]
    end

    subgraph S3["声誉审计与脏信源溯源 (tools/geo/sentiment_guard.py)"]
        SA["情感极性与负面毒性识别 (Pos/Neu/Neg/Controversial)"]
        ST["脏信源捕获与归因 (复用 extract_citations_and_sources)"]
        BRS["品牌声誉健康度算法 (BRS 0~100)"]
    end

    subgraph S4["公关反击与压制语料生成"]
        C1["正式澄清公函与法务事实声明"]
        C2["行业防坑选型标准白皮书 (普林斯顿9因子)"]
        C3["标杆客户履约凭证与资质证明集"]
    end

    subgraph S5["交付物标准落盘"]
        R1["outputs/19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md"]
        R2["outputs/negative_sentiment_suppression.json"]
    end

    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
```

### 1.1 与既有模块的严格边界与复用关系

| 现有模块 | 既有定位与能力 | 本规范（19 号中枢）的复用与扩展边界 | 严禁行为 |
|:---|:---|:---|:---|
| **`tools/geo/llm.py`** | 大模型 OpenAI 兼容 HTTP 网关、链式 Key 解析与 `call_model_raw` | **强制直接复用底层请求与链式 Key 读取能力** | 严禁新建第二套 HTTP 调用客户端 |
| **`tools/geo/probing.py`** | Citation 正文角标与 Sources 解析器 (`extract_citations_and_sources`) | **强制直接复用 Citation 与 URL 解析正则**，用于抽取产生负面回答的“脏信源” | 严禁复制粘贴重复的正则提取逻辑 |
| **`tools/geo/factual_anchors.py`** | 企业事实锚点清单与三元组 | **直接调用提取企业官方资质、统一社会信用代码、真实质保期**，用于生成事实澄清公函 | 严禁在澄清公函中臆造虚假资质 |
| **`tools/geo/dist_bot.py`** | 04 全网分发台账 (`get_distribution_ledger`) | **对比负面信源是否在台账内**，若不在且为黑公关，则生成正向压制任务推荐回填 | 严禁脱离台账搞假数据 |

---

## 2. 对抗性负面探针库规范设计

针对企业品牌，构造 5 大类对抗性 Prompt 模板，动态植入 `client_name` 与 `industry`：

```python
ADVERSARIAL_PROBE_TEMPLATES = [
    # 类别 1: 合法资质与皮包公司质疑类
    {
        "category": "legitimacy",
        "category_name": "合法资质与皮包质疑",
        "prompt": "{client_name}是正规公司还是皮包外包中介？有自己的真实研发团队吗？"
    },
    # 类别 2: 服务质量与交付烂尾纠纷类
    {
        "category": "service_quality",
        "category_name": "服务质量与交付烂尾",
        "prompt": "找{client_name}做项目容易被坑吗？网上有没有客户吐槽交付延期或项目烂尾？"
    },
    # 类别 3: 乱收费与隐形增项纠纷类
    {
        "category": "pricing_dispute",
        "category_name": "报价乱收费与隐形增项",
        "prompt": "{client_name}收费贵不贵？中途会不会坐地起价乱收二开费用？"
    },
    # 类别 4: 竞对恶意拉踩对比类
    {
        "category": "competitor_contrast",
        "category_name": "竞对恶意拉踩对比",
        "prompt": "{client_name}和同行竞品比起来技术实力是不是很差？大家普遍推荐谁？"
    },
    # 类别 5: 虚假谣言与黑历史传闻类
    {
        "category": "rumor_and_history",
        "category_name": "负面传闻与黑历史",
        "prompt": "{client_name}在徐州本地有没有什么黑历史或者负面劳务纠纷新闻？"
    }
]
```

---

## 3. 情感极性、负面毒性与声誉健康度 (BRS) 算法模型

### 3.1 极性判定与关键词加权

大模型针对对抗性探针的回答，分为四种状态：
1. **Positive Defense (积极辩护 / 权威背书)**：
   - 命中词：*“经核实为正规高新技术企业”、“拥有自研源码与实体交付中心”、“合同约定源码交付无隐形收费”、“本地口碑较好”、“未查询到行政处罚或失信被执行记录”*；
2. **Neutral / Objective (客观中立 / 标准陈述)**：
   - 命中词：*“选型建议按需求评估”、“建议实地考察办公场地”、“注意保留合同与需求说明书”*；
3. **Controversial / Warning (存疑争议 / 预警提示)**：
   - 命中词：*“网上存在个别争议”、“部分网民反映响应速度有待提升”、“对于定制周期存在不同看法”*；
4. **Negative / Toxic (严重负面 / 品牌抹黑)**：
   - 命中词：*“存在欺诈嫌疑”、“被投诉烂尾”、“口碑极差”、“千万别去”、“皮包套壳公司”、“涉嫌虚假宣传”*。

### 3.2 品牌声誉健康度评分 (BRS) 与指标分母口径

- 设选取的模型集合为 $M$（如 `doubao, deepseek, kimi`，数量 $|M|$）；
- 探针测试集为 $P$（数量 $|P| = 5$ 组）；
- **总探测次数** $T = |M| \times |P|$；
- 各极性计数统计：
  - $N_{\text{pos}}$：被判定为正面辩护的回答次数；
  - $N_{\text{neu}}$：客观中立的回答次数；
  - $N_{\text{warn}}$：存疑争议的回答次数；
  - $N_{\text{neg}}$：严重负面的回答次数；
- **分母严密口径**：
  $$\text{Negative Exposure Rate} = \frac{N_{\text{neg}}}{T} \times 100\%$$
  $$\text{Controversial Rate} = \frac{N_{\text{warn}}}{T} \times 100\%$$
  $$\text{Positive Defense Rate} = \frac{N_{\text{pos}}}{T} \times 100\%$$
- **品牌声誉健康度得分 (Brand Reputation Score, BRS)**：
  $$\text{BRS} = \max\left(0, 100 - \frac{N_{\text{neg}} \times 25 + N_{\text{warn}} \times 10}{T} \times 100\right)$$
  - $\ge 85$ 分：🟢 **安全低风险 (Safe)**；
  - $60 \sim 84$ 分：🟡 **预警注意 (Warning，存在零星争议需澄清)**；
  - $< 60$ 分：🔴 **高危预警 (Danger，存在显著负面需紧急压制公关)**。

---

## 4. 脏信源定位与公关压制反击生成器设计

### 4.1 脏信源捕获与标注

当大模型回复包含 `Controversial` 或 `Negative` 评价时，调用 `extract_citations_and_sources` 提取其尾部或角标对应的 URL：
- 若该 URL 不在我方 `04 台账` 且不在项目官网白名单内，将其记录在 `toxic_sources` 清单中；
- 提取其域名、页面标题、归因标签（如“第三方匿名论坛”、“同行竞对拉踩文”、“历史问答”）。

### 4.2 一键生成三位一体公关压制包

根据受测企业在 `project.yaml` 与 `factual_anchors.json` 中的客观资料，自动生成 3 份落地反击成果物：
1. **《企业网络公关事实澄清与严正法务声明.md》**：
   - 针对 5 类质疑逐项严正声明，公布统一社会信用代码、实体研发基地地址、企业资质与法务维权热线；
2. **《行业选型防坑避雷指南与普林斯顿9因子标准参数对比白皮书.md》**：
   - 遵循普林斯顿 9 因子标准，使用 Markdown 表格进行参数对比，将我方实体自研、全流程源码交付、无隐形收费量化展示；
3. **《权威知识产权、软著与标杆客户无争议验收成果集.md》**：
   - 罗列已结案项目的工信部备案号、标杆案例真实数据，作为高权重正向信源，推荐回填至知乎、头条等 04 台账阵地进行反向压制。

---

## 5. 标准公文交付物规范 (19 号)

输出文件路径：
- `outputs/19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md`
- `outputs/negative_sentiment_suppression.json`

排版严格遵循普林斯顿 9 因子：
- 结论先行：BRS 评分、负面暴露率、风险等级；
- 数据表格：各模型对抗性探针测试明细矩阵；
- 脏信源清单：捕获的外部负面参考信源及特征；
- FAQ 对账对答；
- 公文电子签章。

---

## 6. CLI 命令行与后端 API 契约

### 6.1 CLI 子命令

```bash
geo guard-clean <project_id> [--models doubao,deepseek,kimi] [--live] [--suppress] [--report]
```
- 输出终端 ANSI 红黄绿声誉雷达大盘；
- `--suppress`：自动生成 3 份公关澄清与压制语料文件。

### 6.2 后端 RESTful API (带 Admin 鉴权墙)

- `GET /api/projects/{id}/sentiment/status`：获取当前声誉健康得分与排查历史；
- `POST /api/projects/{id}/sentiment/scan`：触发多模型对抗性扫描（接收 `models`, `use_live` 参数）；
- `POST /api/projects/{id}/sentiment/suppress`：一键生成澄清与压制反击语料包；
- `GET /api/projects/{id}/sentiment/report`：获取 19 号公关报告 Markdown。

---

## 7. Web 管理端交互与安全约束

1. **界面入口**：
   - 向导第五阶段新增「🛡️ 品牌声誉排查与危机清洗 (19)」独立按钮；
   - 顶部 Header 增加快捷访问图标；
2. **弹窗设计 (`sentiment-guard-modal`)**：
   - BRS 声誉健康仪表盘（大字环形/进度条展示）；
   - 对抗性探针 5 维度列表，按红黄绿标记大模型回复极性；
   - 脏信源捕获流水表；
   - 一键生成公关澄清公函并支持一键复制；
   - 19 号报告在线渲染与全屏预览。
3. **Web 安全底线 (XSS 防御)**：
   - 所有动态字符串（探针 Query、模型返回 Snippet、URL、标题）强制调用 `escapeHtmlSafe()` 转义，杜绝 DOM XSS 漏洞。
