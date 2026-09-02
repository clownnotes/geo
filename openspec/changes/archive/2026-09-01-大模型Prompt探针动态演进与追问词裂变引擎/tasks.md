## 1. 大模型 Prompt 演进与裂变调度引擎 (`tools/geo/evolution.py`)

- [x] 1.1 编写词库生命周期与健康度评估器（`analyze_prompt_portfolio`，划分垄断、拦截、高潜与衰退四大阵营）。
- [x] 1.2 编写基于大模型逆向语义的 5 维追问词裂变生成器（`generate_fission_prompts`，支持痛点、对比、价格、区域、技术长尾裂变）。
- [x] 1.3 编写词库安全合并与流水线下发器（`apply_evolved_prompts`，去重合并入 `project.yaml`，支持触发增量流水线）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `analyze_prompt_portfolio`、`generate_fission_prompts` 与 `apply_evolved_prompts`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo evolve <project_id>` 子命令（支持 `--count 15` 与 `--apply` 参数）。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/evolution/analyze` 接口（返回词库四象限健康度与智能推荐词）。
- [x] 3.2 实现 `POST /api/projects/{id}/evolution/generate` 接口（逆向推演裂变 15 组高质量新 Prompt）。
- [x] 3.3 实现 `POST /api/projects/{id}/evolution/apply` 接口（一键合并新词至客户档案并可触发更新）。

## 4. Web 管理工作台前端交互升级 (`web/index.html`)

- [x] 4.1 在 Step 1（商业意图）与 Step 5（声量大盘）增加「🌱 词库动态演进与裂变中枢」操作入口。
- [x] 4.2 编写词库裂变弹窗（展示健康度矩阵分布、一键裂变候选词列表、支持勾选与一键合并扩容）。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/05-monitor-sop.md` 与 `delivery-sop.md`，规范化季度词库裂变与续费提案 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：词库评估、智能裂变、去重合并入库、API 与 CLI 验证。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
