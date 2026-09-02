## 1. 分发台账与收录核验核心引擎 (`tools/geo/dist_bot.py`)

- [x] 1.1 编写渠道台账读取与初始化器（`get_distribution_ledger`，支持 `dist_ledger.json` 持久化，覆盖 5 大主流渠道）。
- [x] 1.2 编写外链 URL 记录与更新器（`record_distributed_url`，更新特定平台 URL 并计算总体完成率）。
- [x] 1.3 编写外链连通性与存活核验器（`verify_distribution_url` 与 `verify_all_channels`，检测 HTTP 状态与可访问性）。
- [x] 1.4 编写富文本格式化复制器（`format_rich_text_copy`，生成适合公众号/知乎带样式的 HTML 富文本）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `get_distribution_ledger`、`record_distributed_url` 与 `verify_distribution_url`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo record <project_id>` 与 `geo verify-dist <project_id>` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/distribution/ledger` 接口（返回台账与各渠道收录进度）。
- [x] 3.2 实现 `POST /api/projects/{id}/distribution/record` 接口（外发链接填报与自动连通性核验）。
- [x] 3.3 实现 `POST /api/projects/{id}/distribution/verify` 接口（一键全量外链复测）。
- [x] 3.4 在 `tools/geo/share.py` 门户数据中注入 `distribution_ledger` 真实外链。

## 4. Web 管理端与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 4（矩阵分发）增加「🚀 全渠道发布台账与自动化回填」交互模块与进度条。
- [x] 4.2 编写渠道 URL 快速回填弹窗/内联表单与一键外链跳转。
- [x] 4.3 在专属交付门户 `web/share.html` Tab 4 呈现真实已发布渠道外链与收录证明徽章。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/04-distribute-sop.md` 与 `delivery-sop.md`，规范化外发台账回填与收录核验 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：台账更新、外链验证、API 响应与门户链接跳转。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
