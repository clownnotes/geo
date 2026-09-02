## 1. 大模型实时测序与沙箱即时召回引擎 (`tools/geo/playground.py`)

- [x] 1.1 编写双轨大模型查询模拟器（`simulate_llm_query`，支持未优化 Base 与普林斯顿语料 Context 注入的 Before/After 对比生成）。
- [x] 1.2 编写大模型回答质检与置信度评估器（`evaluate_response_quality`，计算品牌命中、Rank 排位、事实命中与 0~100 得分）。
- [x] 1.3 编写批量 Prompt 沙箱测序器（`run_batch_simulation`，从 5 维问答对抽样测序并汇总整体命中率）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `simulate_llm_query`、`evaluate_response_quality` 与 `run_batch_simulation`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo test <project_id>` 子命令（支持 `--query "xxx"` 与 `--compare` 参数）。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `POST /api/projects/{id}/playground/simulate` 接口（单条 Prompt 实时测序与 Before/After 对比）。
- [x] 3.2 实现 `POST /api/projects/{id}/playground/batch` 接口（批量沙箱并发测序）。
- [x] 3.3 实现公开专属客户门户 `POST /api/share/{token}/simulate` 接口。

## 4. Web 管理端与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 5（验收运维）及 Dashboard 顶部增加「🧪 AI 测序沙箱」入口。
- [x] 4.2 编写 Playground 双栏对比模态弹窗（支持自拟问句即时测序、双栏 Before/After 实时对比与高亮渲染）。
- [x] 4.3 在专属交付门户 `web/share.html` 嵌入沙箱交互测序卡片。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/05-monitor-sop.md` 与 `delivery-sop.md`，规范化售前与交付阶段的沙箱测序标准。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：双轨测序、评分算法、API 响应与 Web/门户交互。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
