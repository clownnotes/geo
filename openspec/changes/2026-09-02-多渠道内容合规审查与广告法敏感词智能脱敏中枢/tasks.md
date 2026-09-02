## 1. 编写内容合规与广告法风控脱敏核心引擎 (`tools/geo/compliance.py`)

- [x] 1.1 建立 P0(广告法极限词)、P1(平台引流虚假承诺)、P2(垂直行业违规承诺) 敏感词与安全替换映射库 `COMPLIANCE_RULES_DB`。
- [x] 1.2 实现 `inspect_content_compliance(project_id: str, text: str = None)`，扫描项目全渠道发稿语料并计算合规就绪度得分。
- [x] 1.3 实现 `sanitize_content_text(text: str)` 与 `sanitize_project_deliverables(project_id: str)`，支持一键无损智能脱敏替换。
- [x] 1.4 实现 `render_compliance_report_markdown(project_id: str, comp: dict)`，自动输出 `outputs/13_多渠道内容合规与广告法风控审查报告.md` 与 `outputs/compliance_inspection.json`。

## 2. CLI、服务端与 Web 端大一统集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，新增 `compliance` 子命令（支持 `--inspect`、`--sanitize`）。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `GET/POST /api/projects/{id}/compliance/inspect` 与 `POST /api/projects/{id}/compliance/sanitize`。
- [x] 2.3 更新 `web/index.html`，在 Step 4 矩阵发稿中心接入「🛡️ 内容合规与广告法风控审查」弹窗与一键脱敏交互。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 编写 `tests/test_compliance.py` 单元测试，覆盖敏感词命中、智能脱敏替换、全项目扫描与资产落盘。
- [x] 3.2 针对 4 大母版项目执行合规审查与报告生成，本地验证通过并 Git 推送。


