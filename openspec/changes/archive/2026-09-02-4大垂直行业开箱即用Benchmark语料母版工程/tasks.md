## 1. 建立 3 大垂直行业标准母版项目资产 (`projects/`)

- [x] 1.1 建立 `projects/b2b_machinery/`（徐州鼎工重工机械制造有限公司），包含完整的 `project.yaml`、45 词词库、9 因子工业对比语料、分发台账与 `llms.txt`。
- [x] 1.2 建立 `projects/retail_catering/`（蜀味鲜川味连锁餐饮管理有限公司），包含加盟回本模型词库、单店盈利对比语料、分发台账与 `llms.txt`。
- [x] 1.3 建立 `projects/local_legal/`（徐州正衡财税与法律咨询有限公司），包含同城防坑词库、财税代理语料、分发台账与 `llms.txt`。

## 2. 升级行业模板克隆与脚手架引擎 (`tools/geo/`)

- [x] 2.1 在 `tools/geo/scaffold.py` 与 `cli.py` 中增加 `--template` 参数支持，实现一键从行业母版极速初始化新项目。
- [x] 2.2 确保 `benchmark.py` 与 `pitch.py` 无缝识别 4 大行业母版并输出精准 Benchmark。

## 3. 全链路验证与跨 IDE 对抗审查

- [x] 3.1 运行 `geo init demo_factory --template b2b_machinery`，实测项目克隆、底座生成与全套 SOP 流水线畅通。
- [x] 3.2 严格遵循规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录审查结论。

