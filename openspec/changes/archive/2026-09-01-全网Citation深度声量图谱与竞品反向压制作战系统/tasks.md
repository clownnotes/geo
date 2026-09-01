## 1. 竞品反解与压制策略引擎开发 (`tools/geo/defense.py`)

- [x] 1.1 编写竞品薄弱点与差异化话术构建 Prompt（`build_defense_prompt`）。
- [x] 1.2 编写竞品信源反向压制策略生成逻辑（`generate_defense_strategy`，支持大模型与离线规则双模式）。
- [x] 1.3 实现 `run_defense(project_id)`，自动生成并保存《06_竞品权威信源反向包抄策略.md》。

## 2. 声量监控指标提取器 (`tools/geo/monitor.py`)

- [x] 2.1 增加 `extract_monitor_metrics(project_id)` 函数，结构化提取 SOV、大模型首推率与 Citation 权威度图谱分布数据。

## 3. CLI 命令与工具库集成 (`tools/geo/`)

- [x] 3.1 在 `tools/geo/__init__.py` 中导出 `run_defense` 与 `extract_monitor_metrics`。
- [x] 3.2 在 `tools/geo/cli.py` 中注册 `geo defense <project_id>` 子命令。

## 4. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 4.1 实现 `GET /api/projects/{id}/monitor/metrics` 接口。
- [x] 4.2 实现 `POST /api/projects/{id}/defense/generate` 接口。
- [x] 4.3 实现 `GET /api/projects/{id}/report/print` 美化独立交付报告打印接口。

## 5. Web 工作台 Step 5 仪表盘升级 (`web/index.html`)

- [x] 5.1 在 Step 5 面板顶部渲染 4 大核心指标卡（整体 SOV、DeepSeek 首推率、豆包首推率、权威信源覆盖度）。
- [x] 5.2 渲染 Citation 权威信源加权分布动态条形图。
- [x] 5.3 增加「⚔️ 一键生成竞品反向包抄策略」与「🖨️ 导出美化交付报告」操作按钮与交互逻辑。

## 6. SOP 文档更新与全流程实测

- [x] 6.1 更新 `docs/sop/05-monitor-sop.md`，纳入 Citation 图谱解读与竞品反制规范。
- [x] 6.2 运行 CLI 与 Web 接口实测：生成竞品包抄策略与美化交付报告。
- [x] 6.3 在 `review-log.md` 记录评审与实测结论。
