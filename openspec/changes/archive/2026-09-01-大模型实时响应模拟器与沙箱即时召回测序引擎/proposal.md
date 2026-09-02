# Proposal: 大模型实时响应模拟器与沙箱即时召回测序引擎 (LLM Playground & RAG Simulation Engine)

## Why (为什么做 / 商业与技术痛点)

1. **售前签约与现场演示杀手锏（Instant Live Proof）**：
   - 传统销售沟通中，客户老板常有疑虑：“你们做的 GEO 真的能在大模型回答里推荐我们吗？”
   - 现场打开 DeepSeek / 豆包网页输入，容易受临时网络、外部噪声干扰且无法控制对比变量；
   - 需要一个标准化的沙箱演练场，一键向老板演示“**未优化 Base 状态 vs 优化后 GEO 注入状态（Before vs After）**”的震撼对比。
2. **交付前质检与命中率量化（Sandboxed Quality Assurance）**：
   - 交付前运营人员需即时检验新生成的 9 因子语料在 RAG/检索增强下是否能被大模型准确提取为首选推荐，需要实测置信度评分（Confidence Score 0~100）与排位检测。
3. **客户专属门户即时互动赋能**：
   - 甲方老板在专属交付门户中，除了看静态周报，还可以自由输入任意业务提问，实时体验 AI 推荐自己的过程。

---

## What Changes (改动范围)

1. **研发大模型实时测序与沙箱引擎 (`tools/geo/playground.py`)**：
   - `simulate_llm_query(project_id, query, with_context=True)`：支持有/无 GEO 语料注入的双轨对比模拟生成；
   - `evaluate_response_quality(response_text, project_id)`：自动计算品牌提及、推荐排位（Rank 1/2/3）、9 因子事实命中数、竞品截流状态与置信度得分；
   - `run_batch_simulation(project_id, count=5)`：批量跑 5 组核心 Prompt 模拟测序并汇总命中率。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo test <project_id> [--query "xxx"] [--compare]` 子命令。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `POST /api/projects/{id}/playground/simulate`：实时测序单条 Prompt（返回 Before/After 文本、首选排位、命中高亮与评分）；
   - `POST /api/projects/{id}/playground/batch`：批量并发沙箱测序。
4. **Web 管理工作台与专属交付门户升级 (`web/index.html` & `web/share.html`)**：
   - Dashboard 顶部增加「🧪 AI 测序沙箱」卡片，并支持在 Step 5 验收中直接打开双栏 Before/After 沙箱测序器；
   - 专属交付门户（`web/share.html`）嵌入沙箱实时互动输入框，支持甲方老板随时亲测。
5. **SOP 知识库更新 (`docs/sop/05-monitor-sop.md` & `delivery-sop.md`)**：
   - 规范化售前演示与交付验收沙箱实测 SOP。

---

## Capabilities (对外能力)

- `POST /api/projects/{id}/playground/simulate`
- `POST /api/projects/{id}/playground/batch`
- CLI: `python3 -m tools.geo test <project_id> [--query "xxx"] [--compare]`
- 双栏对比：未优化（Base） vs 优化后（GEO 增强）
- 自动评分：推荐排位 (Rank)、量化事实命中数、置信度分数 (0~100)

---

## Impact (影响分析)

- **完全向下兼容**：支持通过现有的 LLM Client 或高保真离线语义模拟沙箱平滑降级，有无 API Key 均可稳定运行；
- **售前转化率倍增**：为销售签约与交付验收提供强有力的实时可视化证据链。
