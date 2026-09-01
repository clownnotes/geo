## 1. 意图逆向推演核心引擎开发 (`tools/geo/intent.py`)

- [x] 1.1 编写 4 类买家角色与 5 维意图分类大模型 Prompt 构建器（`build_intent_mining_prompt`）。
- [x] 1.2 编写大模型响应解析器与去重格式化逻辑，支持返回分类字典与扁平关键词列表。
- [x] 1.3 编写行业自适应离线规则引擎（`generate_intent_fallback`），保证无 API Key 时高质量兜底。
- [x] 1.4 实现 `mine_project_intent(project_id)`，支持直接读取并就地更新指定项目的 `project.yaml`。

## 2. CLI 命令与工具库集成 (`tools/geo/`)

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `mine_project_intent` 与 `generate_intent_for_company`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo intent <project_id>` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `POST /api/intent/generate`：接收企业信息与行业，实时生成 50 组意图词库。
- [x] 3.2 增加参数合法性校验与错误保护。

## 4. Web 工作台交互升级 (`web/index.html`)

- [x] 4.1 在【+ 新建客户项目】弹窗的意图词库输入框上方增加「✨ AI 智能推演 50 组用户提问」按钮。
- [x] 4.2 实现前端 JavaScript 异步调用、加载态 Spinner、自动回填文本框与 Toast 提示。

## 5. 跨 IDE 审查、端到端实测与文档归档

- [x] 5.1 运行 CLI 测试：`python3 -m tools.geo intent xuzhou_xuanyuan` 验证词库生成质量。
- [x] 5.2 启动 Web 服务，实测前端新建项目时一键推演 50 组意图问句。
- [x] 5.3 在 `review-log.md` 中记录最终评审结论并更新进度。
