## 1. 实体知识图谱与拓扑核心引擎 (`tools/geo/graph.py`)

- [x] 1.1 编写实体与三元组关系提纯算法（`build_entity_knowledge_graph`，从项目档案、语料库提炼 6 类节点与 6 种谓词三元组）。
- [x] 1.2 编写多格式图谱导出器（`export_graph_formats`，输出《10_企业行业实体关系知识图谱.md》、JSON-LD KnowledgeGraph 与 Cypher 脚本）。
- [x] 1.3 编写高清矢量图谱渲染器（`generate_graph_svg`，生成支持拓扑网络布局的高清 SVG 图谱）。
- [x] 1.4 编写复合长尾多跳子图检索器（`query_entity_subgraph`，支持基于关键词的多跳关联实体与关系推理）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `build_entity_knowledge_graph`、`export_graph_formats`、`generate_graph_svg` 与 `query_entity_subgraph`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo graph <project_id> [--export cypher|jsonld|svg]` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/graph/data` 接口（返回图谱节点与边数据）。
- [x] 3.2 实现 `GET /api/projects/{id}/graph/svg` 接口（返回图谱 SVG 矢量图）。
- [x] 3.3 在专属交付门户 `tools/geo/share.py` 注入知识图谱摘要与节点数据。

## 4. Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 2（技术底座）/ Step 3 及顶部增加「🕸️ 实体关系知识图谱」动态拓扑可视化弹窗。
- [x] 4.2 在专属交付门户 `web/share.html` 嵌入知识图谱拓扑网络交互卡片。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/delivery-sop.md` 与 `02-scaffold-sop.md`，规范化 Graph RAG 实体构建与维护 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：图谱构建、SVG 渲染、API 数据与门户交互。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
