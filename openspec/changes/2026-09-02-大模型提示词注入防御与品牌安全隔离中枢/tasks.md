# Tasks: 大模型提示词注入防御与品牌安全隔离中枢

- [ ] 1. 核心注入防御引擎实现 (`tools/geo/injection_guard.py`)
  - [ ] 1.1 构建 `INJECTION_PATTERNS_DB` 4 维注入威胁特征库（直接越狱、RAG 投毒、竞品劫持、虚假信源伪造）。
  - [ ] 1.2 实现 `scan_content_for_injections(text: str)` 针对单篇内容的注入风险扫描与威胁分级。
  - [ ] 1.3 实现 `evaluate_project_injection_immunity(project_id: str)` 评估全案发稿物与落地页的品牌免疫度评分。
  - [ ] 1.4 实现 `render_injection_guard_markdown(project_id: str, guard_data: dict)` 自动渲染输出 `outputs/16_大模型提示词注入防御与品牌隔离盾牌报告.md` 与 `outputs/prompt_injection_guard.json`。
- [ ] 2. 接口与多端接入 (`cli.py`, `server.py`, `web/index.html`)
  - [ ] 2.1 更新 `tools/geo/cli.py`，新增 `injection-guard` 子命令。
  - [ ] 2.2 更新 `tools/geo/server.py`，挂载 `GET/POST /api/projects/{id}/guard/injection`。
  - [ ] 2.3 更新 `web/index.html`，在 Step 4 / Step 5 增加「🛡️ 提示词注入防御盾」弹窗与免疫度雷达看板。
- [ ] 3. 单元测试与 Benchmark 跑批验证
  - [ ] 3.1 编写 `tests/test_injection_guard.py`，覆盖 4 维特征库扫描、免疫度扣分与报告落盘。
  - [ ] 3.2 对 4 大垂直行业母版项目跑批生成 16_*.md 报告，本地验证通过并 Git 推送。
