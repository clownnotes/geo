# Proposal: 客户三级搜索意图挖掘与长尾关键词拓扑演进裂变器 (Customer 3-Tier Search Intent Mining & Long-Tail Keyword Expansion Topology Engine)

## Why (为什么做 / 业务背景与痛点)

1. **关键词粗放单一，无法覆盖大模型真实自然语言提问**：
   - 传统 SEO 依赖宽泛行业词，但在大模型对话场景中，用户的提问具有极强的因果逻辑与具体约束（如包含地域、付费方式、质保时效、避坑指标）；
2. **缺乏标准「3 级搜索意图漏斗与语义拓扑」体系**：
   - 需建立 **L1 品牌与行业核心词（认知层）** ➔ **L2 选型对标与商业防坑词（决策层）** ➔ **L3 痛点解决与场景长尾词（行动层）** 的三级拓扑结构；
3. **缺少与真实 API 评测池的自动化联动机制**：
   - 演进裂变出的高价值长尾词库需要能够一键灌入 `eval` 真实 API 评测池与 `monitor` 监控模块，形成闭环。

---

## What Changes (改动范围)

1. **意图挖掘与拓扑裂变引擎核心 (`tools/geo/intent.py` / `evolution.py`)**：
   - `build_3tier_intent_matrix(project_id: str) -> dict`：结合行业领域特征、差异化承诺、地域属性，自适应裂变生成 3 级（L1/L2/L3）共 30~50 组高价值长尾提示词矩阵；
   - `render_intent_topology_markdown(project_id: str, matrix: dict) -> str`：渲染生成 `outputs/11_三级搜索意图挖掘与长尾关键词裂变拓扑.md` 与 `outputs/keywords_intent_matrix.json`；
   - `sync_intent_keywords_to_eval(project_id: str, tier: str = "all") -> dict`：将演进词库一键同步至 `project.yaml` 或直接触发评测；
2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
   - `geo intent <pid> [--tier l1|l2|l3|all] [--sync-eval]`
3. **Server 路由与 Web 管理端交互升级**：
   - 新增 `GET /api/projects/{id}/intent/matrix`
   - 新增 `POST /api/projects/{id}/intent/generate`
   - 新增 `POST /api/projects/{id}/intent/sync-eval`
   - Web 管理端 Step 2 与 Step 5 增加 3 级意图漏斗可视化卡片、一键裂变与同步至评测。

---

## Capabilities (对外能力)

- **3 级意图自动裂变**：认知层、决策层、行动层全面覆盖；
- **Prompt 提示词模板生成**：为评测沙箱提供贴近用户真实提问的 Query 模板；
- **全链路数据贯通**：从意图挖掘直接输送到 5 大模型评测大盘。

---

## Impact (影响分析)

- 解决客户词库薄弱问题，大幅提升真实评测覆盖度与 Citation 捕获率。

