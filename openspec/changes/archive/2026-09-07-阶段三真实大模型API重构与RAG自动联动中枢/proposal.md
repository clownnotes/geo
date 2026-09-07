# Proposal: 阶段三真实大模型API重构与RAG自动联动中枢

## Why (为什么做)
1. **真实 AI 思考缺失（核心痛点）**：
   - 经代码审查，当前环境未配置任何有效 LLM API Key（`DEEPSEEK_API_KEY`、`ARK_API_KEY` 等），阶段三的普林斯顿重构 100% 运行在 Python 离线模板字符串拼接兜底逻辑（`transform_princeton_corpus_fallback`）中；
   - 导致提纯出来的官网素材并未真正被大模型深度理解、推理和自适应融合，生成的对比表格和 Q&A 问答对带有明显的预设模板痕迹，缺乏企业真实业务灵气与深度。
2. **母盘更新后 RAG 状态割裂（流程断层）**：
   - `03_普林斯顿9因子高权威语料库.md` 是阶段四全网分发与 RAG 检索的唯一核心母盘；
   - 但目前母盘重构后，系统并不会自动更新 RAG 语义分块切片诊断（`rag_diag`）与全案质检报告，需要运营人员反复手动点击多处按钮，操作链路断裂。
3. **缺乏直观的 LLM 运行态感知与安全配置通道**：
   - 控制台未清晰展示当前到底处于“真实大模型驱动”还是“Python 离线模板拼接”状态；
   - 之前缺少安全的 Web 配置入口，操作者无法便捷持久化 Key 到本地。

## What Changes (改动了什么)
1. **大模型配置安全热插拔中枢（支持 Web 界面配置与 .env 持久化）**：
   - 支持在 Web 端直接配置/切换 DeepSeek（DeepSeek-V3 / R1）与火山引擎豆包（Doubao-pro-32k）API Key；
   - 仅限已登录管理员操作（严格挂接 `check_auth`），严格限制白名单环境变量写入，保存前强制进行连通性与鉴权探测，探测失败坚决不落盘；
   - 自动持久化至本地 `.env`（由 `.gitignore` 强力隔离，禁止明文入库；彻底废除 project.yaml 存 Key 设计）；
   - 在阶段三控制台顶部增加常驻状态徽标：清晰标明 `[在线: DeepSeek-V3]`（带延迟）或 `[离线: 规则兜底]`（严格遵循 0 Emoji 商业标准）。
2. **统一 LLM 调用解析器与 Token 预算安全控制**：
   - 收敛全站 LLM 解析至 `tools/geo/llm.py`；Web 配置**只写入** `DEEPSEEK_API_KEY` / `ARK_API_KEY`（禁止仅写 `GEO_DEEPSEEK_*` 导致 status 在线、重构 Fallback）；
   - status 接口按字段白名单组装，禁止整包透传含明文 Key 的内部 dict；
   - `raw_materials` 50k 截断；探针 10s / 重构显式 timeout=120s。
3. **普林斯顿 9 因子大模型重构提示词增强与全量素材融合**：
   - 升级 `tools/geo/rewrite.py`，安全有序注入 `raw_materials/` 事实；
   - 强制基于真实抓取数据输出对比参数矩阵。
4. **母盘更新 ➔ RAG 切片诊断自动级联刷新（对齐现网路由）**：
   - 主入口 `POST /api/projects/{id}/run/rewrite`；级联下沉在 `run_rewrite` 落盘后；
   - `diagnose_rag_chunks(..., run_crawler=False)`；落盘前**回填旧爬虫仿真**，禁止缺章覆盖 12_ 完整报告；
   - HTTP 层映射 `ok/score/golden_chunks/error`，**丢弃 chunks 明细**；
   - 旁路 `/api/princeton/rewrite` 不写母盘、不级联。

## Capabilities (新增或修改的对外能力)
1. `GET /api/llm/status`：白名单字段 + 脱敏 + TTL 缓存；
2. `POST /api/llm/config`：鉴权、唯一键写入、Ping 失败不落盘；
3. `POST /api/projects/{id}/run/rewrite`：`mode`/`provider`/`rag.{ok,score,golden_chunks,error}`（无 chunks 膨胀）。

## Impact (受影响的部分)
- `tools/geo/llm.py` / `utils.py`：统一解析、`.env` 加载与原子写入；
- `tools/geo/server.py`：新增 `/api/llm/status|config`；**增强现有** `/run/rewrite` 响应（不新增幽灵 `/rewrite`）；
- `tools/geo/rewrite.py`：Token 预算 + 落盘后 RAG 级联（`run_crawler=False`）；
- `web/index.html`：LLM Tag、配置弹窗、主流程走 `/run/rewrite`、旁路 Patcher 文案隔离；
- 向下兼容：无 Key / 超时仍 Fallback，0 阻断。

