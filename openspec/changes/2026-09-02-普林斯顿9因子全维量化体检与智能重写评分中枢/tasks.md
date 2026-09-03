## 1. 准备工作

- [ ] 1.1 核对 `AGENTS.md` 本地开发端口规范（8088）与生产隔离红线，梳理普林斯顿 9 因子归一化权重（总和严格为 100%）与特征正则库。

## 2. 研发普林斯顿 9 因子量化评分与重写引擎 (`tools/geo/princeton.py`)

- [ ] 2.1 编写 `score_text_princeton_factors`，实现 9 维特征抽取、100% 归一化加权打分、分档标准（AAA/AA/A/B/C）与双采纳率指标（ceiling / boost）。
- [ ] 2.2 复用 `COMPLIANCE_RULES_DB` 极限营销词库扣分，实现纯关键词堆砌负惩罚算法（非停用词词频 $> 5.0\%$ 扣分）。
- [ ] 2.3 编写 `rewrite_text_princeton_factors`，严格遵循事实真实性红线（有 ID 绑真实锚点，无 ID 标注 `[示例待核实]`），输出前后对比 Diff。
- [ ] 2.4 编写 `audit_project_deliverables_princeton`，排除自身与备份目录，自动生成 `outputs/17_普林斯顿9因子全案质检报告.md` 与 `outputs/princeton_audit.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo score <file_or_text> [--industry X] [--rewrite]` 与 `geo score --project <id> [--audit]`。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/princeton/score`、`/api/princeton/rewrite` 与 `/api/projects/{id}/princeton/audit`（管理端鉴权拦截）。

## 4. Web 管理控制台体检仪界面升级 (`web/index.html`)

- [ ] 4.1 在顶部导航栏新增「🔬 普林斯顿体检仪」入口按钮。
- [ ] 4.2 开发全屏模态窗口 `princeton-modal`，实现文案输入、实时 9 因子雷达看板与缺陷列表。
- [ ] 4.3 实现「✨ 一键普林斯顿重构」交互，同屏对比优化前后文本及采纳率提升数据。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_princeton.py`，全量覆盖权重和等于 100 断言、标杆高分、水文低分、堆砌扣分、防伪标记与 17 号报告生成。
- [ ] 5.2 运行全库单元测试，确保 100% 通过。
- [ ] 5.3 在 `review-log.md` 中记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
