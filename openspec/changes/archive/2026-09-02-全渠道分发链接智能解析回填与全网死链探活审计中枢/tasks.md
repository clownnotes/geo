## 1. 编写智能链接解析与全网死链探活中枢 (`tools/geo/health_checker.py` / `distributor.py`)

- [x] 1.1 实现 `parse_mixed_links(raw_text: str)`，支持从任意混合多行文本中提取 URL 并智能判定平台渠道（头条/知乎/微信/GitHub/百度）。
- [x] 1.2 实现 `backfill_publication_ledger(project_id: str, links: list[dict])`，增量去重回填至 `04_全网分发渠道执行与存活台账.md` 并刷新存活率。
- [x] 1.3 实现 `audit_channel_links_health(project_id: str, concurrency: int = 8)`，多线程并发 HTTP 探活并回写存活状态。

## 2. CLI 与服务端及 Web 管理端交互升级 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，增加 `ledger` 子命令（支持 `add` 与 `audit`）。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `/api/projects/{id}/ledger/batch-add`、`/audit` 与 `/summary`。
- [x] 2.3 更新 `web/index.html`，在 Step 4 全渠道分发台账板块接入「智能粘贴链接解析入账」弹窗与「一键全网死链探活」进度展示。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 运行单元测试与真实项目台账回填探活，验证去重、状态更新与存活率重算。
- [x] 3.2 遵守项目规范：仅在本地测试，提交推送至远端 Git 仓库，在 `review-log.md` 记录审查结论。

