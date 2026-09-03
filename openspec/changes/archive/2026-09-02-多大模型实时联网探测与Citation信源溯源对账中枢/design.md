# Design: 多大模型实时联网探测与Citation信源溯源对账中枢

## 1. 架构定位、系统边界与既有模块复用契约

本中枢在现有的监控（`monitor.py`）、AI 可见度评测（`evaluator.py`）与信源权威度推演（`citation_authority.py`）之上，构建**实时联网探测、回答正文 Citation 角标提取与外发渠道资产闭环对账层**。

### 1.1 与既有 `evaluator.py` / `llm.py` / `dist_bot.py` 的严格复用与边界对照（采纳方案 A）

坚决杜绝平行造轮子与重复基础设施建设，严格复用已有成熟底层：

| 维度 | 既有模块 (`llm.py` / `evaluator.py`) | 本模块 (`probing.py` / 统一网关) | 复用与分工关系 |
| :--- | :--- | :--- | :--- |
| **底层模型调用** | `tools/geo/llm.py` 已实现标准 OpenAI 与火山方舟调用 | 复用 `llm.py` 既有底层请求逻辑，对其返回结构统一封装为规范数据类 | **强制复用**：禁止新建第二套并行 HTTP 请求客户端 |
| **评测业务定位** | `evaluator.py`：全案宏观 AI 可见度 Benchmark，产出 06 号报告，侧重品牌综合提及与竞对声量对比 | `probing.py`：**Citation 深度溯源与台账闭环对账 v2**，产出 18 号报告，侧重正文角标 `[1]` 解析与 04 台账真实 URL 资产的 Hit/Miss 对账 | **正交互补**：本模块是 04 台账外发成果在 AI 端的端到端归因验证 |
| **台账数据读取** | `dist_bot.py` 中的 `get_distribution_ledger(project_id)` | 本模块强制调用 `dist_bot.get_distribution_ledger` 获取台账 | **强制复用**：严禁私自绕过该接口手动读取或硬编码 |
| **Web 交互入口** | Step 5 原有 `eval-modal`（06 评测大盘） | 新增独立 `probing-modal`（18 号 Citation 溯源与资产对账透视） | **双入口清晰分工**：06 看宏观声量排名，18 看具体外发文章是否被采纳为角标信源 |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             Web 管理工作台：多模型实时探测与信源溯源 (web/index.html)          │
│  - 模型选择器 (豆包 / DeepSeek / Kimi / 沙箱)   - 实时意图 Query 探测控制台  │
│  - 实测 SOV 柱状图对比 (豆包 vs DeepSeek vs Kimi) - Citation 信源角标对账表  │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ RESTful API (管理端鉴权，XSS esc() 转义)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│             实时探测与 Citation 溯源引擎 (tools/geo/probing.py)              │
│  - run_live_probing()                    - extract_citations_and_sources()  │
│  - trace_citations_against_ledger()      - 严格三大指标计算 (SOV/Share/Top1)│
└──────────────────┬───────────────────┬───────────────────┬──────────────────┘
                   │ 强制复用          │ 强制复用          │ 规范产出
┌──────────────────▼───────────────────┐┌──────────────────▼┐┌──────────────────▼┐
│ 统一模型调用适配 (复用 tools/geo/llm.py)││ 04 外发资产台账源  ││ outputs/18_大模型│
│ - Doubao (优先级: GEO_DOUBAO > DOUBAO)││ dist_bot.        ││ 实时联网探测与  │
│ - DeepSeek (GEO_DEEPSEEK > DEEPSEEK) ││ get_distribution_││ Citation信源溯源 │
│ - Kimi (GEO_KIMI > MOONSHOT)         ││ ledger()          ││ 对账报告.md      │
│ - SandboxSimulator (高保真沙箱)      ││ + project.yaml 官网││ live_probing_    │
└──────────────────────────────────────┘└───────────────────┘│ trace.json        │
                                                             └───────────────────┘
```

---

## 2. API Key 兼容优先级与沙箱模式

### 2.1 API Key 严格兼容读取优先级表（写死契约）

为消除 `llm.py` 与 `evaluator.py` 的命名分歧，所有模型必须按以下顺序**按优先级链式降级查找**：

1. **豆包 (Doubao / 字节火山方舟)**：
   - API Key 查找：`os.getenv("GEO_DOUBAO_API_KEY")` ➔ `os.getenv("DOUBAO_API_KEY")` ➔ `os.getenv("ARK_API_KEY")`
   - Endpoint 查找：`os.getenv("GEO_DOUBAO_ENDPOINT_ID")` ➔ `os.getenv("DOUBAO_ENDPOINT_ID")`
2. **DeepSeek (官方 / 硅基流动)**：
   - API Key 查找：`os.getenv("GEO_DEEPSEEK_API_KEY")` ➔ `os.getenv("DEEPSEEK_API_KEY")`
   - Base URL：默认 `https://api.deepseek.com/v1`（可通过 `DEEPSEEK_BASE_URL` 覆盖）
3. **Kimi (Moonshot AI)**：
   - API Key 查找：`os.getenv("GEO_KIMI_API_KEY")` ➔ `os.getenv("MOONSHOT_API_KEY")`
4. **范围约束 (Out of Scope 声明)**：
   - 本次 v1 聚焦 **豆包、DeepSeek、Kimi** 与 SandboxSimulator；
   - 阿里通义千问、百度文心明确列为 **Out of Scope**（后续版本按需扩展），避免验收扯皮。

### 2.2 SandboxSimulator (确定性高保真沙箱)
* 触发条件：对应模型未提供任何有效 Key，或调用参数指定 `use_live=False`；
* 行为特征：
  - 基于传入的 `project_id`、`project.yaml` 实体与台账已外发文章，以确定性伪随机数生成带真实感且合规的回答；
  - 正文中精准植入 `[1]`、`[2]` 角标与尾部 Sources；
  - 响应耗时模拟真实网络（200~400ms）；
  - 严禁在沙箱模式输出「具备法律效力审计报告」类过度公关文案；
  - **单测严格使用该模式**，秒级全绿通过，保证 CI/CD 稳定。

---

## 3. Citation 角标提取与外发资产对账算法

### 3.1 双通道 Citation 引用提取
* **通道 A（正文解析）**：
  - 正则模式匹配：`\[(\d+)\]`（如 `[1]`、`[2]`）、`\[\[(\d+)\]\]`、`\^(\d+)`；
  - 尾部 Sources 块匹配：捕获 `参考资料` / `参考信源` / `Sources:` 下方的 Markdown 链接 `\[(\d+)\]\s*\[(.*?)\]\((.*?)\)`；
* **通道 B（结构化元数据提取）**：
  - 若调用返回中带有 `search_results` / `citations` / `tool_calls` 结构体，直接提取 URL 与 Title；
* **URL 归一化**：忽略协议前缀（http/https）、末尾斜杠 `/` 及 UTM 追踪参数。

### 3.2 外发资产台账严格对账契约 (`trace_citations_against_ledger`)
* **台账加载契约**：必须通过 `dist_bot.get_distribution_ledger(project_id)` 获取完整台账；
* **我方资产基准库组装**：
  1. `ledger["channels"]` 中所有 `url` 非空且 `status in ("published", "verified")` 的渠道发布外链（与 `dist_bot` 完成率口径对齐，避免核验通过后资产掉出 Hit 池）；
  2. `ledger.get("custom_links", [])` 中登记的额外发布链接；
  3. `project.yaml` 中登记的企业官方网站 `official_url`；
* **严密对账判定逻辑（杜绝同站竞对文章误伤）**：
  1. **精确命中 (`exact_hit`)**：Citation URL 与我方台账 URL 完全一致；
  2. **同渠道有效命中 (`domain_hit`)**：域名与我方外发渠道一致（如 `zhuanlan.zhihu.com`），且**URL 路径前缀或文章 ID 与我方台账登记文章一致**；（若仅域名相同但路径属于竞对或未登记，严格归类为 `third_party_or_competitor`，不计入我方 Hit！）；
  3. **竞对/第三方信源 (`third_party_or_competitor`)**：未被我方台账覆盖的公开平台、竞对网站。

---

## 4. 实测三大量化指标公式与分母口径澄清

为彻底消除指标歧义，明确分母口径：

### 4.1 全局综合指标 (Summary Level)
* 设选取了 $M$ 个模型（如豆包、DeepSeek、Kimi 共 3 个），每个模型探测 $Q$ 组 Query（如 5 组），总探测次数为 $T = M \times Q$（例如 15 次）：
1. **实测大模型提及率 (`real_sov_pct`)**：
   $$ \text{Real SOV} = \frac{\sum_{i=1}^{T} I(\text{该次探测中提及我方品牌})}{T} \times 100\% $$
2. **首位推荐率 (`top1_recommendation_rate`)**：
   $$ \text{Top-1 Rate} = \frac{\sum_{i=1}^{T} I(\text{该次探测将我方排在首位推荐})}{T} \times 100\% $$
3. **Citation 信源角标占有率 (`citation_share_pct`)**：
   $$ \text{Citation Share} = \frac{\text{捕获到的我方资产角标命中总数}}{\text{全部探测捕获到的所有有效角标总数}} \times 100\% $$
   （若捕获角标总数为 0，兜底为 0.0%）。

### 4.2 单模型明细指标 (`model_breakdown`)
* 对单个模型 $m$（探测了 $Q$ 组 Query）：
  - `sov_pct` = 该模型提及 Query 数 / $Q \times 100\%$；
  - `top1_pct` = 该模型首推 Query 数 / $Q \times 100\%$；
  - `citation_hits` = 该模型回答中命中我方台账资产的角标次数。

---

## 5. 统一规范产出物契约

1. **结构化 JSON 成果**：`outputs/live_probing_trace.json`
2. **全案第 18 维公文 Markdown 报告**：`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md`
   - 严格遵循普林斯顿 9 因子标准：结论先行、三大 KPI 量化对账表格、各模型雷达对比表、FAQ 问答对与企业公章声明。

---

## 6. CLI 与 RESTful API

### 6.1 CLI 命令行
* `python3 -m tools.geo probe <project_id> [--models doubao,deepseek,kimi] [--sample 5] [--live]`
* `python3 -m tools.geo probe <project_id> --report`

### 6.2 RESTful API (管理端登录鉴权拦截)
* `GET /api/projects/{id}/probing/status`
* `POST /api/projects/{id}/probing/run`
* `GET /api/projects/{id}/probing/report`

---

## 7. Web 管理端驾驶舱升级与安全规范

1. **入口清晰**：向导 Step 5 新增「🤖 Citation 信源角标溯源对账」独立卡片与按钮，与 06 评测入口明确区分功能（06 看宏观分数，18 看角标对账）；
2. **模态弹窗 (`probing-modal`)**：展示实测 SOV、Citation Share、Top-1 三大 KPI，多模型横向对比柱状图，实时 Citation 溯源对账流水表；
3. **XSS 安全防护**：**所有渲染的捕获 URL 与信源标题必须经过既有 `esc()` 函数转义**，杜绝 XSS 注入风险。
