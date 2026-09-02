## 1. 编写 Citation 信源权威度与外链信任度推演核心引擎 (`tools/geo/citation_authority.py`)

- [x] 1.1 建立全网核心分发渠道基础域名权威库 `CHANNEL_AUTHORITY_DB`（头条、知乎、微信、GitHub、百家号等及五大模型亲和度）。
- [x] 1.2 实现 `score_single_backlink(link_item: dict)`，对单条外链计算域名权重、五大模型亲和度与预估被采纳率。
- [x] 1.3 实现 `evaluate_project_citation_authority(project_id: str)`，汇总全案外链权威指数、五大模型生态覆盖度与提权建议。
- [x] 1.4 实现 `render_citation_authority_markdown(project_id: str, auth_data: dict)`，自动输出 `outputs/15_大模型Citation信源权威度与外链信任度评分报告.md` 与 `outputs/citation_authority_matrix.json`。

## 2. CLI、服务端与 Web 端大一统集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，新增 `citation-auth` 子命令。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `GET/POST /api/projects/{id}/citation/authority`。
- [x] 2.3 更新 `web/index.html`，在 Step 5 持续运营面板接入「🏆 信源权威度与 Citation 矩阵」弹窗与全景看板。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 编写 `tests/test_citation_authority.py` 单元测试，覆盖单链权威评分、五大模型亲和度矩阵与全项目资产落盘。
- [x] 3.2 针对 4 大母版项目执行外链信源权威度推演与报告生成，本地验证通过并 Git 推送。


