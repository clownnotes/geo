## 1. 行业大盘聚合与批量并发调度引擎 (`tools/geo/benchmark.py`)

- [x] 1.1 编写跨项目行业数据聚合器（`calculate_industry_benchmarks`，统计各行业的均值、中位数、Top 10% 标杆线及 Citation 平台占比）。
- [x] 1.2 编写单项目行业对标评级器（`evaluate_project_against_benchmark`，计算超越同行百分比、段位标签与核心差距）。
- [x] 1.3 编写基于 `ThreadPoolExecutor` 的批量多项目并发跑批器（`run_batch_pipeline`，支持指定步骤与并发度）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `calculate_industry_benchmarks`、`evaluate_project_against_benchmark` 与 `run_batch_pipeline`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo benchmark` 与 `geo batch` 子命令（支持 `--all`、`--industry`、`--step`、`--concurrency`）。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `GET /api/benchmark/industries` 接口（返回全库各行业 Benchmark 宏观均值）。
- [x] 3.2 实现 `GET /api/projects/{id}/benchmark` 接口（返回指定客户与所属行业的横向对比数据）。
- [x] 3.3 实现 `POST /api/batch/trigger` 接口（支持管理端异步批量触发多项目流水线）。

## 4. Web 管理端与客户交付门户前端升级

- [x] 4.1 在 Dashboard 统计指标区增加「🌐 行业大盘宏观基准」卡片（展示行业平均提及率与 Top 平台）。
- [x] 4.2 在项目列表表头增加「🚀 批量并发生产」操作弹窗（支持选择全量/指定行业、执行阶段与并发线程数）。
- [x] 4.3 在向导页 Step 5 与专属分享门户 `web/share.html` 中增加「🎯 行业横向对标与超越战绩」可视化卡片（客户 SOV vs 行业均值 vs 行业标杆）。

## 5. SOP 文档更新与全流程实测

- [x] 5.1 更新 `docs/sop/05-monitor-sop.md` 与 `delivery-sop.md`，规范化行业 Benchmark 话术与续费指标。
- [x] 5.2 端到端实测：运行行业聚合、执行批量并发跑批、测试 Web API 与只读门户对标渲染。
- [x] 5.3 在 `review-log.md` 记录审查与实测结论。
