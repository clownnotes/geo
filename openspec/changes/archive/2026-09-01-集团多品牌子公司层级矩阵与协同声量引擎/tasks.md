## 1. 集团矩阵层级与协同声量计算引擎 (`tools/geo/group.py`)

- [x] 1.1 编写集团层级配置存储与读取器（`load_groups_config`、`save_group_config`，支持持久化至 `data/groups.json`）。
- [x] 1.2 编写集团综合加权 SOV 与协同效应指数计算器（`calculate_group_matrix`，计算集团总 SOV、子品牌声量贡献率与共享信源）。
- [x] 1.3 编写集团多品牌竞品防御与拦截汇总分析器（`analyze_group_defense`）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `load_groups_config`、`calculate_group_matrix` 与 `save_group_config`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo group` 子命令（支持 `--id <group_id>` 与 `--list` 参数）。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `GET /api/groups` 接口（返回全量集团列表及母子层级拓扑）。
- [x] 3.2 实现 `GET /api/groups/{id}/matrix` 接口（返回集团综合声量、协同指数与子品牌矩阵表）。
- [x] 3.3 实现 `POST /api/groups` 接口（创建或更新集团层级绑定）。

## 4. Web 管理工作台前端升级 (`web/index.html`)

- [x] 4.1 在 Dashboard 统计指标区增加「🏢 集团多品牌矩阵」透视卡片。
- [x] 4.2 编写集团多品牌大盘弹窗（展示集团加权 SOV、协同倍数、子品牌贡献率分布图表及共享信源列表）。

## 5. SOP 文档更新与本地端到端实测

- [x] 5.1 更新 `docs/sop/delivery-sop.md` 与 `overview.md`，规范化集团级多品牌矩阵交付流程。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：集团绑定、协同计算、API 响应与 Web 弹窗渲染。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
