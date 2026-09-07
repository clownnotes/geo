# Tasks: 阶段三真实大模型API重构与RAG自动联动中枢

- [x] 1. 后端大模型管理与状态探测 API（安全优先）
  - [x] 1.1 `.env` 自动加载；缺失则创建；`0600` + tmp/`os.replace`；确认 `.gitignore` 含 `.env`；加载时 **`.env` 键覆盖 `os.environ`**（禁止 setdefault 被旧 OS 值压死）
  - [x] 1.2 收敛解析到 `llm.py`；utils 薄封装；**Web 只写** `DEEPSEEK_API_KEY` / `ARK_API_KEY`（可选同步 `DOUBAO_API_KEY`）；解析两侧同序读取；统一豆包默认模型 `doubao-pro-32k`；解析结果携带 `source`（`.env`/`env`/`none`）；禁止 yaml Key
  - [x] 1.3 `GET /api/llm/status`：`check_auth`；**字段白名单**组装（禁止整包透传 `get_configured_llm()`）；脱敏；探针走 `chat/completions`（禁依赖 `/models`）；`401/403→auth_failed`、超时→`unreachable`；TTL 60s + `?refresh=1`
  - [x] 1.4 `POST /api/llm/config`：`check_auth`；按 §2.1 唯一键写入；Ping 失败不落盘；成功热更新环境（强制覆盖）并**清空 status TTL 缓存**

- [x] 2. 普林斯顿重构 + RAG 级联
  - [x] 2.1 `run_rewrite`：50k 预算；**`call_llm_api(..., timeout=120)`**；失败 Fallback
  - [x] 2.2 落盘后级联：`diagnose_rag_chunks(project_id, text_or_file=母盘, run_crawler=False)`；**方案 A**：落盘前若新 `crawler_simulation` 为空则回填旧 JSON 中的爬虫仿真，禁止缺章覆盖 12_ 报告；异常不回滚母盘
  - [x] 2.3 升级 `POST /api/projects/{id}/run/rewrite`：鉴权；**RAG 映射层**（`ok←success`，`score←rag_readiness_score`，`golden_chunks←golden_chunks_count`，`error←异常`）；**丢弃 `chunks`**；不得新增幽灵 `/rewrite`
  - [x] 2.4 旁路 `/api/princeton/rewrite`：不级联；前端隔离文案

- [x] 3. 前端
  - [x] 3.1 LLM Tag（0 Emoji；latency/source；立即检测）
  - [x] 3.2 配置弹窗写入 §2.1 唯一键
  - [x] 3.3 主按钮 `/run/rewrite`；读 `rag.ok`/`rag.score`；超时 ≥ 180s

- [x] 4. 回归
  - [x] 4.1 无 Key：Fallback + 级联不阻断
  - [x] 4.2 假 Key：不写 `.env`
  - [x] 4.3 有效 Key：写入 `DEEPSEEK_API_KEY` 后 status 与 rewrite **同为在线 LLM**；级联后 RAG 分数/切片更新且 **12_ 报告仍保留非空爬虫仿真章**（若级联前旧 JSON 有 `crawler_simulation`）；无外网爬虫
  - [x] 4.4 超时 Fallback
  - [x] 4.5 `/api/princeton/rewrite` 后母盘/RAG mtime 不变
  - [x] 4.6 status 响应 JSON **不含** `api_key` 字段（仅 `api_key_masked`）
  - [x] 4.7 保存 config 后立即 `GET /api/llm/status` 须反映新状态（TTL 已失效）
