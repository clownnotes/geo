# Proposal: 阶段三真实大模型API重构与RAG自动联动中枢

## Why (为什么做)
1. **真实 AI 思考缺失（核心痛点）**：
   - 经代码审查，当前环境未配置任何 LLM API Key（`DEEPSEEK_API_KEY`、`ARK_API_KEY` 等），阶段三的普林斯顿重构 100% 运行在 Python 离线模板字符串拼接兜底逻辑（`transform_princeton_corpus_fallback`）中；
   - 导致提纯出来的 2379 字官网素材并未真正被大模型深度理解、推理和自适应融合，生成的对比表格和 Q&A 问答对带有明显的预设模板痕迹，缺乏企业真实业务灵气与深度。
2. **母盘更新后 RAG 状态割裂（流程断层）**：
   - `03_普林斯顿9因子高权威语料库.md` 是阶段四全网分发与 RAG 检索的唯一核心母盘；
   - 但目前母盘重构后，系统并不会自动更新 RAG 语义分块切片诊断（`rag_diag`）与全案质检报告，需要运营人员反复手动点击多处按钮，操作链路断裂。
3. **缺乏直观的 LLM 运行态感知**：
   - 控制台未清晰展示当前到底处于“真实大模型驱动”还是“Python 离线模板拼接”状态，给操作者带来认知困惑。

## What Changes (改动了什么)
1. **大模型配置热插拔中枢（支持 Web 界面配置与 .env 持久化）**：
   - 支持在 Web 端直接配置/切换 DeepSeek（DeepSeek-V3 / R1）与火山引擎豆包（Doubao-pro-32k）API Key；
   - 自动持久化至本地 `.env`（并确保加进 `.gitignore`，杜绝密钥泄漏）；
   - 在阶段三控制台顶部增加常驻状态徽标：清晰标明 `🟢 运行中: DeepSeek-V3 深度重构` 或 `🟡 离线模式: Python 规则模板兜底`。
2. **普林斯顿 9 因子大模型重构提示词增强与全量素材融合**：
   - 升级 `tools/geo/rewrite.py` 中的 LLM Prompt，将 `raw_materials/` 下的所有已提纯事实（`raw_extracted_facts.md`、`website_crawled_raw.md` 等）完整喂给大模型；
   - 强制大模型基于真实抓取的数据输出具有绝对商业说服力的对比参数矩阵。
3. **母盘更新 ➔ RAG 切片诊断自动级联刷新**：
   - 当点击【执行普林斯顿重构】完成 `03_普林斯顿9因子高权威语料库.md` 后，自动在后台同步执行 `diagnose_rag_chunks`，无缝更新 `12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md`；
   - 前端 RAG 诊断按钮展示最新切片分数徽章（如 `88.5分 极佳`）。

## Capabilities (新增或修改的对外能力)
1. `GET /api/llm/status`：获取当前大模型配置与联通状态（供应商、当前模型、连通延迟）；
2. `POST /api/llm/config`：在控制台安全保存/更新 API Key 并进行即时 Ping 探测；
3. `POST /api/projects/{id}/rewrite` 响应体升级：增加 `cascade_rag` 字段，返回最新生成的母盘内容及联动的 RAG 切片评分。

## Impact (受影响的部分)
- `tools/geo/utils.py`：增强 `.env` 本地加载支持与 API 连通性测试；
- `tools/geo/rewrite.py`：重构逻辑增加对 `raw_materials/` 多源事实的聚合注入及 RAG 级联触发；
- `web/index.html`：阶段三头部增加 LLM 状态徽章与快捷配置弹窗；
- 向下兼容：若用户未配置 API Key，系统 100% 平滑降级为当前的 Python 行业模板，绝不阻塞任何现有功能。

