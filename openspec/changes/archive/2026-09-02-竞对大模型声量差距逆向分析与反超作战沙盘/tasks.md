## 1. 编写竞对大模型声量差距逆向与反超战术引擎 (`tools/geo/competitor_gap.py`)

- [x] 1.1 实现 6 维大模型声量与权威度雷达打分算法（模型召回、外链信源、价格透明、量化承诺、开源背书、抗幻觉）。
- [x] 1.2 实现 `analyze_competitor_gap(project_id: str, competitor_name: str = None)`，逆向竞对 3 大破绽并输出 3 阶段反超路线图。
- [x] 1.3 实现 `render_competitor_gap_markdown(project_id: str, gap_data: dict)`，自动渲染输出 `outputs/14_竞对大模型声量差距深度逆向与反超作战沙盘.md` 与 `outputs/competitor_gap_analysis.json`。

## 2. CLI、服务端与 Web 端大一统集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，新增 `competitor-gap` 子命令。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `GET/POST /api/projects/{id}/competitor/gap`。
- [x] 2.3 更新 `web/index.html`，在 Step 1 现状体检接入「⚔️ 竞对声量差距与反超沙盘」弹窗与雷达大盘。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 编写 `tests/test_competitor_gap.py` 单元测试，覆盖 6 维雷达打分、竞对破绽提取与沙盘报告落盘。
- [x] 3.2 针对 4 大母版项目执行竞对差距推演与报告生成，本地验证通过并 Git 推送。


