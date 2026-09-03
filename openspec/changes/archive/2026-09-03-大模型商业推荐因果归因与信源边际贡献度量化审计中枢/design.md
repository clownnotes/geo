# 技术架构设计：大模型商业推荐因果归因与信源边际贡献度量化审计中枢 (第 23 维核心交付)

## 1. 架构总览与反事实执行流程

```mermaid
graph TD
    A[真实商业 Query 采样: flat_queries] --> B[可观测我方信源切片池构建: 03/anchors/台账存活页]
    B --> C[全量基线推荐推演 P_baseline (Top-3 留存加权)]
    C --> D[逐一切片反事实抽离消融 Leave-One-Out Ablation]
    D --> E[推导各切片边际跌幅 Delta_P 与 MCR 贡献率 (Shapley Proxy)]
    E --> F[计算品牌因果鲁棒性指数 CRI 与单点故障 SPOF 识别]
    F --> G[信源角色三档分类: 👑基石 / ⚡催化 / 🥀冗余]
    G --> H[计算 4 维雷达指标 radar_metrics]
    H --> I[落盘: causal_attribution_audit.json]
    H --> J[落盘: 23号商业审计公文报告.md]
    H --> K[落盘: attribution_optimization_pack 三件套]
    I --> L[API 路由 / CLI 终端大盘 / Web 控制台]
```

---

## 2. 数学模型、防饱和公式与 5 组固定数值夹具

### 2.1 推荐置信度得分模型 (防饱和 Top-3 留存加权聚合)
为彻底杜绝简单求和导致多切片求和溢出饱和到 100 使得 LOO 消融失效的问题，采纳**Top-3 留存加权聚合模型**：
- 设当前信源子集为 $U \subseteq S$；
- 对子集 $U$ 中的每个切片 $s$，计算其与查询 $q$ 的有效证据值：
  $$v(q, s) = \text{score\_dense\_similarity}(q, s.\text{text}) \times \text{AuthBonus}(s)$$
  （Relevance 复用 `tools.geo.rerank_simulator.score_dense_similarity`，字符 2-gram 余弦相似度，$\epsilon=1e-9$）；
- 将集合 $U$ 中所有切片的有效得分降序排列，截取 Top-3 切片得分：$v_{(1)} \ge v_{(2)} \ge v_{(3)}$（若切片数少于 3 个，不足项补 0.0）；
- 商业意图推荐置信度定义为：
  $$P(Brand|q, U) = \text{round}\left(100.0 \times \big(0.60 \cdot v_{(1)} + 0.25 \cdot v_{(2)} + 0.15 \cdot v_{(3)}\big), 1\right)$$
  **性质保证**：取值严格在 $[0.0, 100.0]$，永不饱和溢出；当抽离核心主干信源 $s_{(1)}$ 时，次优切片顺延顶上，得分必然平滑下挫，LOO 边际敏感度极高。

### 2.2 统一信源权威权重表 (AuthBonus)
彻底消除文档内部矛盾，严格以实际数据路径为准：
| 信源类别 | 数据文件 / 提取源 | 权威权重 AuthBonus | 物理意义 |
|:---|:---|:---:|:---|
| **事实档案金标准** | `projects/{id}/outputs/factual_anchors.json` | **1.0** | 官方营业执照、核心资质、官网事实硬锚点 |
| **9 因子高优语料** | `projects/{id}/outputs/03_普林斯顿9因子语料库.md` | **0.8** | 结构化权威长文、结论先行评测报告 |
| **台账存活落地页** | `dist_bot.get_distribution_ledger` (`is_ledger_asset_eligible`) | **0.7** | 第三方媒体专栏、百家号、CSDN 等存活外链文章 |
| **降级保底信源** | 纯项目配置兜底切片 | **0.5** | 通用简介兜底片段 |

### 2.3 反事实消融与 Shapley 代理边际贡献率 (MCR)
- **全量基线推荐得分**：
  $$P_{\text{base}}(Q, S) = \frac{1}{|Q|} \sum_{q \in Q} P(Brand|q, S)$$
- **反事实抽离得分 (Leave-One-Out Ablation)**：
  对任意信源切片 $s_i \in S$，计算将其抽离后的平均推荐得分：
  $$P_{\text{ablated}}(Q, S \setminus \{s_i\}) = \frac{1}{|Q|} \sum_{q \in Q} P(Brand|q, S \setminus \{s_i\})$$
- **边际因果跌幅 (Marginal Drop)**：
  $$\Delta P(s_i) = \max\left(0.0, P_{\text{base}}(Q, S) - P_{\text{ablated}}(Q, S \setminus \{s_i\})\right)$$
- **信源边际因果贡献率 (Marginal Contribution Rate, MCR, Shapley Proxy)**：
  $$MCR(s_i) = \begin{cases} \text{round}\left( \frac{\Delta P(s_i)}{\sum_{j=1}^m \Delta P(s_j)} \times 100.0, 1 \right), & \text{若 } \sum_{j=1}^m \Delta P(s_j) > 0 \\ 0.0, & \text{否则} \end{cases}$$
  （注：各切片独立四舍五入，总和与 100% 允许存在 $\le 0.2\%$ 的正常浮点精度误差）。

### 2.4 品牌因果鲁棒性指数 (CRI) 与三档评级
衡量品牌在最关键单一信源遭遇封禁/失效时的承压抗震能力：
$$CRI = \begin{cases} \text{round}\left( \frac{\min_{i=1}^m P_{\text{ablated}}(Q, S \setminus \{s_i\})}{P_{\text{base}}(Q, S)} \times 100.0, 1 \right), & \text{若 } P_{\text{base}} > 0 \\ 0.0, & \text{否则} \end{cases}$$

**三档鲁棒性评级枚举**：
1. `high_resilience` (🟢 高度抗震 / 矩阵式容灾)：$CRI \ge 75.0\%$；
2. `moderate_dependency` (🟡 中度依赖 / 存在次级单点)：$50.0\% \le CRI < 75.0\%$；
3. `fragile_single_point` (🔴 脆弱单点 / 抽离即坍塌)：$CRI < 50.0\%$。

### 2.5 信源角色分类与单点故障标记
- 👑 核心基石 (`cornerstone`)：$MCR(s_i) \ge 25.0\%$；
- ⚡ 协同催化 (`catalyst`)：$10.0\% \le MCR(s_i) < 25.0\%$；
- 🥀 冗余低效 (`redundant`)：$MCR(s_i) < 10.0\%$；
- **关键单点故障 (`critical_spof`)**：若某信源 $MCR(s_i) \ge 40.0\%$ 且抽离后得分 $P_{\text{ablated}} < 50.0$，标记为 `critical_spof = True`。

### 2.6 雷达指标操作定义 (radar_metrics 四维量化公式)
1. **因果抗震度 (`causal_robustness`)**：直接取 $CRI$ 值；
2. **基石信源纯度 (`cornerstone_purity`)**：基石信源的 MCR 累加和：
   $$\text{cornerstone\_purity} = \text{round}\left(\sum_{s \in \text{Cornerstones}} MCR(s), 1\right)$$
3. **单点故障免疫度 (`single_point_immunity`)**：
   $$\text{single\_point\_immunity} = \text{round}\left(\max\big(0.0, 100.0 - \max_{s \in S}(MCR(s))\big), 1\right)$$
   （最大单一切片边际贡献越低，单点依赖度越低，免疫度越高）；
4. **预算有效转化率 (`budget_efficiency_ratio`)**：非冗余信源切片数（基石+催化）占总切片数的比例：
   $$\text{budget\_efficiency\_ratio} = \text{round}\left(\frac{N_{\text{cornerstone}} + N_{\text{catalyst}}}{N_{\text{total\_sources}}} \times 100.0, 1\right)$$

### 2.7 5 组固定数值测试夹具（Fixtures 契约）
- **夹具 1 (CRI 高度抗震)**：$P_{\text{base}} = 80.0$，最坏单一抽离得分 $P_{\text{min}} = 64.0 \implies CRI = 80.0\%$ (`high_resilience`)；
- **夹具 2 (CRI 中度依赖)**：$P_{\text{base}} = 80.0$，最坏单一抽离得分 $P_{\text{min}} = 48.0 \implies CRI = 60.0\%$ (`moderate_dependency`)；
- **夹具 3 (CRI 脆弱单点)**：$P_{\text{base}} = 80.0$，最坏单一抽离得分 $P_{\text{min}} = 32.0 \implies CRI = 40.0\%$ (`fragile_single_point`)；
- **夹具 4 (MCR 边际贡献率与角色分类)**：
  设有 3 个信源切片，累积边际跌幅为 $\Delta_1 = 30.0, \Delta_2 = 15.0, \Delta_3 = 5.0$（总和 $50.0$）：
  - $MCR_1 = 30.0 / 50.0 \times 100.0 = 60.0\% \implies \texttt{cornerstone}$；
  - $MCR_2 = 15.0 / 50.0 \times 100.0 = 30.0\% \implies \texttt{cornerstone}$；
  - $MCR_3 = 5.0 / 50.0 \times 100.0 = 10.0\% \implies \texttt{catalyst}$；
- **夹具 5 (单点故障归因判定)**：
  若某信源 $MCR = 60.0\% \ (\ge 40.0\%)$ 且抽离后得分 $40.0 \ (< 50.0) \implies \text{标记 } \texttt{critical\_spof = True}$。
- **加深夹具 6 (Top-3 留存加权推荐概率)**：
  当 $v_{(1)}=1.0, v_{(2)}=0.8, v_{(3)}=0.6$ 时，
  $P = \text{round}(100 \times (0.60 \times 1.0 + 0.25 \times 0.8 + 0.15 \times 0.6), 1) = 89.0$ 分。

---

## 3. 切片池真实路径点名与数据依赖

严格杜绝虚构模块与伪造路径：
1. **9 因子语料切片**：读取 `projects/{project_id}/outputs/03_普林斯顿9因子语料库.md`，按 `## ` 拆分为知识切片，赋权 `auth_bonus = 0.8`；
2. **事实档案切片**：读取 `projects/{project_id}/outputs/factual_anchors.json`，缺失时平滑降级至 `load_project_config(project_id)`，赋权 `auth_bonus = 1.0`；
3. **真实台账落地页**：调用 `tools.geo.dist_bot.get_distribution_ledger(project_id)`，遍历 `channels` 与 `custom_links`，严格经由 `tools.geo.probing.is_ledger_asset_eligible` 过滤存活页面，赋权 `auth_bonus = 0.7`；
4. **商业 Query 采样**：优先读取 `projects/{project_id}/outputs/keywords_intent_matrix.json` 的顶层主字段 `flat_queries`（至少 5 组真实意图原句）。

---

## 4. `--live` 语义与预算边界契约

- **Out of Scope**：绝不在本地加载或下载大型模型，不进行神经网络梯度反向推导。沙箱默认运行轻量确定的 `CausalAttributionSimulator`；竞品切片反事实消融 Out of Scope；
- **`--live` 真实 API 调用与预算严格锁死**：
  - **调用次数上限**：严格锁死为至多 $1 + 2 = 3$ 次（1 次全量基线状态 + 至多 2 次 Top-2 核心基石信源抽离状态）；
  - **Prompt 与裁决对象**：向 `tools.geo.llm.call_model_raw` 发送商业意图提问及当前切片上下文，要求给出推荐置信度评分（0~100 整数）；
  - **生产字典安全解包**：
    `text = resp if isinstance(resp, str) else (resp or {}).get("content") or ""`
    提取大模型返回的概率并按 **70% 沙箱因果分 + 30% 在线 Judge 裁决分** 融合更新 $P_{\text{base}}$ 与对应 $P_{\text{ablated}}$，随后更新 CRI 与 MCR；
  - **降级保护**：若在线调用失败或超时，平滑降级至纯沙箱打分，且设置 `is_live_judged = False`；
  - **自适应公文报告**：报告第 1 节自动根据 `use_live` 切换“沙箱推演免责说明（含反事实 LOO Shapley 近似代理声明）”或“真实联网 API 实盘审计声明”。

---

## 5. JSON 数据契约 (`outputs/causal_attribution_audit.json`)

与 12 号诊断和 22 号演习文件严格隔离，顶层契约字段如下：

```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "client_name": "徐州璇源网络科技有限公司",
  "timestamp": "2026-09-03 05:40:00",
  "use_live": false,
  "summary": {
    "cri": 76.5,
    "grade_code": "high_resilience",
    "grade_name": "🟢 高度抗震 (High Resilience)",
    "baseline_score": 88.5,
    "worst_case_score": 67.7,
    "total_sources_audited": 12,
    "cornerstone_count": 2,
    "catalyst_count": 4,
    "redundant_count": 6,
    "spof_detected": false
  },
  "radar_metrics": {
    "causal_robustness": 76.5,
    "cornerstone_purity": 65.0,
    "single_point_immunity": 82.0,
    "budget_efficiency_ratio": 50.0
  },
  "source_attributions": [
    {
      "source_id": "src_01",
      "title": "徐州璇源网络科技有限公司 核心业务资质与直营交付保障",
      "source_type": "9因子语料",
      "auth_bonus": 0.8,
      "marginal_drop": 24.5,
      "mcr": 35.2,
      "role": "cornerstone",
      "critical_spof": false
    }
  ]
}
```

---

## 6. CLI、API 与 Web 端规范

1. **CLI 命令行**：
   - `python3 -m tools.geo attribution <project_id> [--models M] [--live] [--optimize] [--report]`
   - 终端打印 ANSI 仪表盘：企业名称、CRI 鲁棒性指数、评级、基线得分、核心基石信源 TOP3、单点故障预警及优化包落盘路径；
2. **后端 API 挂载 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/attribution/status`：获取最新因果归因审计状态；
   - `POST /api/projects/{id}/attribution/audit`：触发信源反事实消融与归因审计计算；
   - `POST /api/projects/{id}/attribution/optimize`：生成 `attribution_optimization_pack` 优化三件套；
   - `GET /api/projects/{id}/attribution/report`：获取 23 号公文报告（无文件返回 404，禁止后台隐式计算）；
   - 全量继承统一 Bearer Token 鉴权拦截；
3. **Web 控制台升级 (`web/index.html`)**：
   - Header 导航与向导 Step 5 新增「🧬 因果归因 (23)」入口；
   - 模态窗口 `causal-attr-modal`：展示 CRI 仪表盘、信源边际贡献度 MCR 堆叠条形图、基石/催化/冗余分类标签与在线公文报告预览；
   - 动态数据表格渲染强制经过 `escapeHtmlSafe()` 进行 XSS 防御。
