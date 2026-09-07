# Tasks: 阶段三真实大模型API重构与RAG自动联动中枢

- [ ] 1. 后端大模型管理与状态探测 API
  - [ ] 1.1 在 `tools/geo/utils.py` 中增加自动加载项目根目录 `.env` 环境变量支持
  - [ ] 1.2 在 `tools/geo/server.py` 中实现 `GET /api/llm/status`（带探针测活与脱敏展示）与 `POST /api/llm/config`（保存并写入 `.env`）
  - [ ] 1.3 确认 `.gitignore` 包含 `.env` 配置文件，杜绝密钥泄露风险
- [ ] 2. 阶段三普林斯顿重构 Prompt 升级与 RAG 级联联动
  - [ ] 2.1 升级 `tools/geo/rewrite.py`：读取 `raw_materials/` 目录下全部事实文件并融入大模型 Prompt
  - [ ] 2.2 在 `run_rewrite` 完成后增加自动级联触发 `tools.geo.rag_diag.diagnose_rag_chunks(project_id)`
  - [ ] 2.3 升级 `/api/projects/{id}/rewrite` 接口，回传母盘生成结果与 RAG 诊断实时评分
- [ ] 3. 前端界面感知与快捷配置交互
  - [ ] 3.1 在阶段三面板头部新增 LLM 状态徽章（显示当前连接的大模型或离线状态）
  - [ ] 3.2 增加【大模型配置弹窗】：支持一键填入 DeepSeek / 豆包 Ark API Key 并测活保存
  - [ ] 3.3 重构成功后，前端自动刷新下方 Markdown 预览并同步更新 RAG 诊断按钮分数
- [ ] 4. 回归验证与质量验收
  - [ ] 4.1 离线兜底回归：在无 Key 状态下验证平滑降级，确保语料与 RAG 诊断 100% 正常
  - [ ] 4.2 配置 Key 联通测试：填入有效 API Key 验证真实大模型思考重构与 RAG 切片自动刷新

