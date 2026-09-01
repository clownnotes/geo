# Proposal: 多行业大盘 Benchmark 横向对标与批量并发跑批引擎

## Why (为什么做 / 业务痛点)

1. **业务痛点：单一客户的声量缺乏行业横向基准（缺少“尺子”）**
   - 客户在查看自身 SOV 为 45% 时，往往无法判断效果好坏；
   - 商业代运营需要权威的行业大盘基准数据（Industry Benchmark）：展示「客户企业 vs 所属行业平均线 vs 行业头部水平」的三维对标；
   - 在交付报告、专属门户与周报中自动生成行业背书（如*“您的 AI 可见度已超越本行业 78.5% 的竞品”*），大幅提升交付说服力与客户续费率。
2. **效率痛点：规模化代运营（20~100 家企业）缺乏批量并发跑批能力**
   - 当前流水线主要面向单项目点击或执行，当有数十家客户需要统一下发技术底座改造或跑全量流水线时，人工逐个操作效率低；
   - 需要提供多线程并发批量跑批命令（`geo batch --pipeline --all` / `geo batch --monitor --industry "制造业"`）。
3. **管理端缺乏跨行业宏观态势透视看板**
   - 管理后台缺乏按行业维度（如制造业、企服软件、本地生活、电商等）聚合的宏观大盘透视图。

---

## What Changes (改动范围)

1. **研发行业大盘分析与横向对标引擎 (`tools/geo/benchmark.py`)**：
   - 实现跨项目多维数据聚合器 `calculate_industry_benchmarks()`：自动提取各项目的行业标签、SOV、Top3 推荐率、Citation 平台渗透，计算行业平均值、中位数与前 10% 标杆线；
   - 实现单客户行业对标评级器 `evaluate_project_against_benchmark(project_id)`：计算超越同行百分比、核心短板差距与优化潜力；
   - 实现批量并发调度器 `run_batch_pipeline(target_ids=None, industry=None, step="pipeline", max_workers=4)`。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo benchmark [--industry <name>]` 子命令（查看各行业宏观均值）；
   - 注册 `geo batch [--step <step>] [--all] [--industry <name>] [--concurrency 4]` 批量并发跑批子命令。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/benchmark/industries`：获取全库所有行业的宏观 Benchmark 指标与 Top 平台分布；
   - `GET /api/projects/{id}/benchmark`：获取指定客户与所属行业的横向对比数据（含超越百分比）；
   - `POST /api/batch/trigger`：管理端异步批量触发多项目流水线/巡检。
4. **Web 管理工作台与专属分享门户升级**：
   - 管理端 Dashboard 顶部增加「🌐 行业大盘基准 (Benchmark)」宏观聚合卡片；
   - 向导页 Step 5 与专属分享门户 `web/share.html` 中新增 **「🎯 行业横向对标雷达与超越战绩」** 模块；
   - 项目列表表头增加「🚀 批量并发生产」操作入口。
5. **SOP 知识库更新 (`docs/sop/delivery-sop.md` & `05-monitor-sop.md`)**：
   - 规范化行业对标数据在续费谈判中的使用标准。

---

## Capabilities (对外能力)

- `GET /api/benchmark/industries`
- `GET /api/projects/{id}/benchmark`
- `POST /api/batch/trigger`
- CLI: `python3 -m tools.geo benchmark [--industry <name>]`
- CLI: `python3 -m tools.geo batch [--step <pipeline/audit/monitor>] [--all] [--industry <name>]`

---

## Impact (影响分析)

- **完全向下兼容**：自动基于现有的 `projects/<id>/config.json`、周报与 `history.db` 动态聚合计算，0 额外侵入；
- **交付说服力跃升**：让客户的每一次投入都有行业 Benchmark 标尺可量化对齐。
