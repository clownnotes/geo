## 1. 商业 ROI 量化与续约预测核心引擎 (`tools/geo/roi.py`)

- [x] 1.1 编写商业 ROI 计算模型（`calculate_project_roi`，结合 SOV、CPC、CPL 计算 SEM 替代价值、精准线索估值与 ROI 倍数）。
- [x] 1.2 编写客户续约健康度预测器（`predict_renewal_health`，多维综合评分 0~100，生成续约等级与谈判话术）。
- [x] 1.3 编写项目商业参数持久化器（`save_roi_settings` 与 `load_roi_settings`，支持自定义 CPL、服务费与客单价）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `calculate_project_roi`、`predict_renewal_health` 与 `save_roi_settings`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo roi <project_id>` 与 `geo renewal <project_id>` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/roi/calculate` 接口（返回完整商业 ROI 测算与续约预测）。
- [x] 3.2 实现 `POST /api/projects/{id}/roi/settings` 接口（保存客户特定商业参数）。
- [x] 3.3 在 `tools/geo/share.py` 门户数据中注入 `roi_summary`。

## 4. Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在 Dashboard 顶部指标区增加「💰 商业 ROI 测算」入口卡片与独立模态弹窗。
- [x] 4.2 在向导 Step 5（验收运维）嵌入「💰 商业投资回报 (ROI) 与续约预测」可视化面板与参数调优滑块。
- [x] 4.3 在专属交付门户 `web/share.html` Tab 5 呈现「商业投资回报 (ROI) 与数字资产估值」战绩看板。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/05-monitor-sop.md` 与 `delivery-sop.md`，规范化客户季度复盘与续约增购谈判 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：ROI 算法测算、续约评分、参数配置与门户展示。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
