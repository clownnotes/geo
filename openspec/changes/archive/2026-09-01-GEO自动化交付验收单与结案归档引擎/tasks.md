## 1. 交付验收与归档核心引擎 (`tools/geo/acceptance.py`)

- [x] 1.1 编写 6 维合同履约达成率评估算法（`calculate_fulfillment_score`，计算各阶段完成度并输出 0~100 综合达标率）。
- [x] 1.2 编写全量交付物汇总与结案确认单生成器（`generate_acceptance_report`，输出《00_GEO商业交付验收结案确认单.md》）。
- [x] 1.3 编写全套交付物打包归档器（`export_project_archive_zip`，将全部交付 Markdown、HTML、SVG 图表与底座代码打包为 ZIP）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `generate_acceptance_report`、`calculate_fulfillment_score` 与 `export_project_archive_zip`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo signoff <project_id>` 与 `geo pack <project_id>` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/acceptance/data` 接口（返回结案单结构化数据与履约评分）。
- [x] 3.2 实现 `GET /api/projects/{id}/acceptance/print` 接口（美化版 A4 纸排版公章结案单打印页）。
- [x] 3.3 实现 `GET /api/projects/{id}/acceptance/download-zip` 接口（流式下载 ZIP 归档包）。
- [x] 3.4 在专属交付门户 `tools/geo/share.py` 注入结案单与归档下载入口。

## 4. Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 5（验收运维）及顶部增加「📜 交付结案验收」与「📦 下载归档包」操作按钮与弹窗。
- [x] 4.2 在专属交付门户 `web/share.html` Tab 5 呈现「📜 商业交付结案确认单」与一键全量 ZIP 下载卡片。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/delivery-sop.md` 与 `05-monitor-sop.md`，规范化结案验收与回款闭环 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：结案单生成、ZIP 归档下载、HTML 打印与门户互动。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
