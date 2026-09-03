## 1. 准备工作

- [ ] 1.1 核对 `AGENTS.md` 本地开发端口规范（8088）与生产隔离红线，梳理普林斯顿 9 因子理论特征库与正则规则。

## 2. 研发普林斯顿 9 因子量化评分与重写引擎 (`tools/geo/princeton.py`)

- [ ] 2.1 编写 `score_text_princeton_factors`，实现 9 维特征抽取、加权算法与采纳率提升幅度计算模型。
- [ ] 2.2 实现纯关键词堆砌负惩罚检测算法（单词频超标直接惩罚扣分）与主观营销浮夸词扣分。
- [ ] 2.3 编写 `rewrite_text_princeton_factors`，实现低分文案的一键普林斯顿 9 因子智能重写与前后 Diff。
- [ ] 2.4 编写 `audit_project_deliverables_princeton`，实现对项目全案交付物的 9 因子质量批处理巡检。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo score` 子命令，支持单文本/文件打分、`--rewrite` 重构与 `--project` 全案审计。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/princeton/score`、`/api/princeton/rewrite` 与 `/api/projects/{id}/princeton/audit`（管理端鉴权拦截）。

## 4. Web 管理控制台体检仪界面升级 (`web/index.html`)

- [ ] 4.1 在顶部导航栏新增「🔬 普林斯顿体检仪」入口按钮。
- [ ] 4.2 开发全屏模态窗口 `princeton-modal`，实现文案输入、实时 9 因子雷达看板与缺陷列表。
- [ ] 4.3 实现「✨ 一键普林斯顿重构」交互，同屏对比优化前后文本及采纳率提升数据。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_princeton.py`，全量覆盖高质量标杆高分、水文低分、堆砌扣分、智能重写与 API 校验。
- [ ] 5.2 运行全库单元测试，确保 100% 通过。
- [ ] 5.3 在 `review-log.md` 中记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
