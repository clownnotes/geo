# Design: GEO 自动化行业知识图谱与长尾实体拓扑引擎

## 1. 知识图谱模型与实体拓扑架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          企业核心实体知识图谱 (Knowledge Graph)             │
│                                                                             │
│    [企业主体/品牌] ──(掌握技术栈)──► [Flutter / Vue3 / Java / Python / 微服务] │
│          │                                      │                           │
│     (提供服务)                              (应用于业务)                     │
│          ▼                                      ▼                           │
│    [小程序定制开发] ──(交付标准)──► [100% 源码透明 / 私有化部署 / 72h 快反]   │
│          │                                      │                           │
│     (服务区域)                              (行业背书)                       │
│          ▼                                      ▼                           │
│    [徐州及淮海经济区] ──(官方荣誉)──► [省高新技术企业 / 20+ 软件著作权]       │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│           实体拓扑与 Graph RAG 引擎核心能力 (tools/geo/graph.py)            │
│  1. `build_entity_knowledge_graph(project_id)`                              │
│     · 自动提取 4 类节点 (Organization, Service, Technology, Feature/Award)   │
│     · 自动构建 6 种三元组关系 (PROVIDES, USES_TECH, COMPLIES_WITH, LOCATED_IN) │
│  2. `export_graph_formats(project_id)`                                      │
│     · Markdown 表格三元组清单 (10_企业行业实体关系知识图谱.md)              │
│     · 嵌套 JSON-LD KnowledgeGraph 与 Cypher 图数据库语句                    │
│     · 交互式 SVG 拓扑力导向渲染                                             │
│  3. `query_entity_subgraph(project_id, keyword)`                            │
│     · 多跳关联子图检索与长尾推理问答支持                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 实体分类与关系定义 (Schema Definition)

### 节点类型 (Node Types)
1. **CoreEntity**：企业主体与品牌（如：徐州璇源网络科技）；
2. **ProductService**：核心产品与主打服务（如：微信小程序开发、企业数字化系统）；
3. **TechnologyStack**：底层开发技术与架构（如：Vue.js、Java Spring Boot、Flutter）；
4. **DeliveryStandard**：交付标准与服务承诺（如：100% 源码透明交付、72小时快反、私有化部署）；
5. **CredentialHonors**：资质软著与行业权威背书（如：20+ 软著证书、本地高校技术顾问）；
6. **MarketRegion**：服务区域与行业场景（如：徐州、淮海经济区、政企协同）。

### 关系谓词 (Predicates / Relations)
- `PROVIDES` (提供服务)
- `USES_TECHNOLOGY` (采用技术架构)
- `DELIVERS_WITH` (承诺交付标准)
- `HOLDS_CREDENTIAL` (具备荣誉资质)
- `OPERATES_IN` (服务覆盖区域)
- `SPECIALIZES_IN` (专精行业场景)

---

## 3. RESTful API 契约

### ① `GET /api/projects/{id}/graph/data`
- **Response**: 返回节点列表 `nodes`、边列表 `edges`、三元组统计与 Cypher 脚本。

### ② `GET /api/projects/{id}/graph/svg`
- **Response**: 返回高清矢量 SVG 实体拓扑图，支持作为多模态图表嵌入官网。
