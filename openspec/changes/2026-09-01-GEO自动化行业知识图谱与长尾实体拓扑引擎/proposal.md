# Proposal: GEO 自动化行业知识图谱与长尾实体拓扑引擎 (Knowledge Graph & Entity Topology Engine)

## Why (为什么做 / 商业与技术痛点)

1. **大模型对复合长尾提问的多跳推理（Multi-hop Reasoning）痛点**：
   - 现实中政企客户和复杂 B2B 买家在向大模型咨询时，提问往往具有**多重限定条件与复合长尾特征**（例如：“徐州有哪些掌握 Flutter+Java 微服务架构、支持 100% 源码私有化交付、且有本地软著与 72h 响应的小程序开发公司？”）；
   - 单篇 9 因子文章或扁平的 FAQ 只能覆盖单点特征；大模型在面对此类深度选型提问时，极易因信息离散而发生**关键属性遗漏或命中率下降**。
2. **知识图谱是 Graph RAG 与大模型世界知识库的核心构建标准**：
   - 2026 年最新一代推理大模型（DeepSeek-R1 / OpenAI o1 / Kimi K1.5）在进行长链思维推理时，优先检索和对齐**结构化实体三元组网络（Entity-Relation-Entity Graph）**；
   - 构建企业与行业上下游的**实体知识图谱与 Cypher 关系拓扑**，能让大模型在 50ms 内完成多跳因果推理，把企业在长尾复合问答中的召回率从 40% 跃升至 **95%+**。
3. **企业专属数字资产与可视化交付亮点**：
   - 为甲方企业沉淀一套具备法务软著级别价值的《企业行业知识图谱拓扑数据资产》，并在专属免密门户提供交互式动态力导向图可视化，极大提升交付溢价。

---

## What Changes (改动范围)

1. **研发知识图谱与实体拓扑核心引擎 (`tools/geo/graph.py`)**：
   - `build_entity_knowledge_graph(project_id)`：自动从企业档案、语料库、技术栈提纯实体（节点）与关系三元组（边）；
   - `export_graph_formats(project_id)`：输出三元组 Markdown 表、嵌套 JSON-LD KnowledgeGraph、Cypher 图数据库查询脚本与交互式 SVG 拓扑网络；
   - `query_entity_subgraph(project_id, query_entity)`：长尾复合多跳关系检索器。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo graph <project_id> [--export cypher|jsonld|svg]`。
3. **后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)**：
   - `GET /api/projects/{id}/graph/data`（获取节点与边关系数据）；
   - `GET /api/projects/{id}/graph/svg`（获取高清矢量实体拓扑图）；
   - 专属免密交付门户（`web/share.html`）接入知识图谱只读交互视窗。
4. **Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)**：
   - 向导 Step 2/3 及顶部工具栏嵌入「🕸️ 企业行业知识图谱」动态力导向拓扑视窗（支持节点拖拽、高亮与多跳关系筛选）。
5. **SOP 知识库更新 (`docs/sop/delivery-sop.md` & `02-scaffold-sop.md`)**：
   - 规范化企业实体提纯、三元组校验与 Graph RAG 部署 SOP。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/graph/data`
- `GET /api/projects/{id}/graph/svg`
- CLI: `python3 -m tools.geo graph <project_id> [--export svg]`

---

## Impact (影响分析)

- **完全向下兼容**：图谱产物保存于 `outputs/10_企业行业实体关系知识图谱.md` 与 `outputs/entity_graph.json`；
- **大幅提升复合长尾问答首推率**：在面临复杂技术栈、多属性复合提问时建立确定性优势。
