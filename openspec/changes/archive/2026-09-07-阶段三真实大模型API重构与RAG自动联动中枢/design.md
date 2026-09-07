# Design: 阶段三真实大模型API重构与RAG自动联动中枢

## 1. 核心架构与数据流向 (Architecture & Data Flow)

```
[素材录入] 官网爬虫 / 客户资料
        │
        ▼
[raw_materials/ 目录持久化]
        │
        ▼
[阶段三主入口] POST /api/projects/{id}/run/rewrite   ← 现网真实路径（非 /rewrite）
        │  (管理端登录态 / 本地免登规则同现网)
        │
        ├── ① 统一解析器 resolve_llm_runtime()（见 §2，与 Web 写入键名一致）
        │     ├── 有 Key: Token 预算截断素材 ➔ Prompt ➔ DeepSeek/豆包（timeout=120s）
        │     └── 无 Key / 超时 / 401: Python Fallback
        │
        ▼
[run_rewrite → 落盘母盘 03_普林斯顿9因子高权威语料库.md]  ← 成功即保留
        │
        ├── ② 级联（挂在母盘落盘之后，失败隔离）
        │     └── diagnose_rag_chunks(project_id, text_or_file=母盘路径, run_crawler=False)
        │           └── 经 §3.4 映射层裁剪后返回 rag 标量字段
        │
        ▼
[前端] 语料预览刷新 + RAG 徽标 + LLM 状态 Tag（0 Emoji）

旁路入口（不写母盘、不级联）：
  POST /api/princeton/rewrite  → rewrite_text_princeton_factors（粘贴文案局部 Patcher）
  → 前端明示「局部改写，不刷新 RAG 母盘诊断」
```

`pipeline` 内 `run_rewrite` 与单独 `run/rewrite` **共用**落盘后级联（级联下沉在 `run_rewrite` 内）。

---

## 2. 统一大模型探测链（禁止 yaml 存 Key + 钉死写入键名）

唯一运行时解析入口收敛到 `tools/geo/llm.py`；`utils.get_configured_llm` / `call_llm_api` 改为**薄封装调用同一解析器**，禁止再维护第二套 env 判断。

```
① .env（gitignored；仅鉴权写入或人工本地配置）
       ↓
② OS 环境变量（见下方「唯一写入键」+ 兼容只读别名）
       ↓ 未命中或失败（Ping 10s / 重构 120s / 401）
③ Python Fallback
```

**禁止** `project.yaml` 的 `api_keys`。

### 2.1 Web `/api/llm/config` 唯一写入键（钉死，防 status 在线 / 重构 Fallback）

| provider | 必须写入的 Key 变量 | 可选写入 |
| :--- | :--- | :--- |
| deepseek | **`DEEPSEEK_API_KEY`** | `DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL` |
| doubao / ark | **`ARK_API_KEY`**（主） | 可同步写 `DOUBAO_API_KEY` 同值；`DOUBAO_MODEL`、`ARK_BASE_URL` |
| openai 兼容代理 | **`GEO_LLM_API_KEY`** 或 `OPENAI_API_KEY` | `GEO_LLM_BASE_URL` / `OPENAI_BASE_URL`、`GEO_LLM_MODEL` |

- **禁止** Web 写入 `GEO_DEEPSEEK_API_KEY` / `GEO_DOUBAO_API_KEY` 作为唯一密钥（避免 llm.py 读到、utils 读不到的分裂）。
- 统一解析器读取顺序（两侧一致）：
  - DeepSeek：`DEEPSEEK_API_KEY` →（兼容只读）`GEO_DEEPSEEK_API_KEY`
  - 豆包：`ARK_API_KEY` → `DOUBAO_API_KEY` →（兼容只读）`GEO_DOUBAO_API_KEY`
- **默认模型统一**：DeepSeek=`deepseek-chat`；豆包=`doubao-pro-32k`（可用 env 覆盖；废除未配置时落到 `doubao-seed-1-6-250615` 的漂移）。
- **解析结果必须携带 `source`**：`.env` | `env` | `none`（供 status / 前端 Tag 展示；禁止伪造）。

---

## 3. 接口与组件设计

### 3.1 鉴权
- `GET /api/llm/status`、`POST /api/llm/config`、主重构入口：**必须** `check_auth()`；有 `X-Forwarded-*` 不得免登写 Key。
- 匿名：`401`。

### 3.2 `GET /api/llm/status`（输出字段白名单）

**允许返回的字段仅限**：

`configured` | `provider` | `model` | `base_url` | `source` | `api_key_masked` | `latency_ms` | `status` | `cached`

```json
{
  "configured": true,
  "provider": "deepseek",
  "model": "deepseek-chat",
  "base_url": "https://api.deepseek.com",
  "source": ".env",
  "api_key_masked": "sk-****abcd",
  "latency_ms": 120,
  "status": "ready",
  "cached": false
}
```

**硬性禁止**：
- 禁止响应中出现 `api_key` 明文；
- **禁止**将 `get_configured_llm()` 返回 dict **整包** `json.dumps` / 透传给客户端；
- 必须由专用 `build_llm_status_payload()` 按白名单组装。

探针：连通性 + 鉴权（不查余额）；timeout=10s；TTL 缓存 60s；`?refresh=1` 强制探测。  
探测请求统一走 `POST {base_url}/chat/completions`（极小 `max_tokens`），**禁止**依赖 `/models`（兼容代理未必提供）。映射：`401/403 → auth_failed`；超时/网络 → `unreachable`；其余成功 → `ready`。

### 3.3 `POST /api/llm/config`
1. `check_auth` → 401；
2. 按 §2.1 写入**唯一键名**（白名单）；
3. Ping 失败 → **不落盘**；
4. 成功：原子写 `.env`（创建 + `0600` + tmp/`os.replace`）+ 热更新 `os.environ`（**写入键强制覆盖**进程内同名变量，禁止 setdefault 被旧 OS 值压死）；
5. 成功后**立即清空** status TTL 缓存，保证下次 `GET /api/llm/status` 反映新配置。

### 3.4 阶段三主重构：`POST /api/projects/{id}/run/rewrite`

处理：
1. 鉴权；
2. `run_rewrite`：Token 预算 → **`call_llm_api(..., timeout=120)`**（禁止默认 30s）→ 落盘母盘 → 级联；
3. 级联调用写死：  
   `diagnose_rag_chunks(project_id, text_or_file=<母盘路径>, run_crawler=False)`；
4. **级联落盘防降级（方案 A，强制）**：`run_crawler=False` 时，落盘前读取已有 `outputs/rag_chunks_diagnostic.json` 的 `crawler_simulation`；若旧值非空且新结果该字段为 `None`，则**回填旧爬虫仿真**再写 JSON 与 `12_*.md`。禁止用缺章报告静默覆盖完整全量诊断。若无旧文件可回填，报告第 1 章允许标注「本次为重构级联快检，尚未执行全量爬虫仿真」。
5. **映射与裁剪层**（禁止透传 `diagnose_rag_chunks` 原始 dict）：

| API `rag` 字段 | 来源 |
| :--- | :--- |
| `ok` | 异常捕获外为 `True`；异常或 `success is False` 为 `False` |
| `score` | `rag_readiness_score` |
| `total_chunks` | `total_chunks` |
| `golden_chunks` | `golden_chunks_count` |
| `entity_coverage_pct` | `entity_coverage_pct` |
| `error` | 异常字符串；成功时为 `null` |

**丢弃**（HTTP 响应）：`chunks`、`crawler_simulation` 及一切大体积明细（爬虫仿真仅保留在磁盘报告内，不进 API）。

6. 同步等待；前端/网关超时建议 ≥ 180s。
7. 响应契约：
```json
{
  "success": true,
  "step": "rewrite",
  "mode": "llm",
  "provider": "deepseek",
  "message": "阶段 3：普林斯顿 9 因子内容重构已完成！",
  "rag": {
    "ok": true,
    "score": 88.5,
    "total_chunks": 10,
    "golden_chunks": 7,
    "entity_coverage_pct": 92.0,
    "error": null
  }
}
```
级联失败：`success: true`，`rag.ok: false`，`rag.error` 有文案；**不回滚母盘**。

### 3.5 旁路：`POST /api/princeton/rewrite`
局部 Patcher；不写母盘；不级联；前端隔离文案。

### 3.6 前端
LLM Tag（0 Emoji）+ 配置弹窗 + 主按钮 `/run/rewrite` + 按 `rag.ok`/`rag.score` 更新徽标。

---

## 4. Token 预算与超时

| 场景 | 规则 |
| :--- | :--- |
| 素材 | 上限 50000；优先级 facts > website_crawled > 其它 |
| RAG | `run_crawler=False` + 传母盘路径 |
| Ping | 10s；缓存 60s |
| 重构 | **显式 timeout=120** |
| HTTP | 同步；客户端 ≥ 180s |

---

## 5. 安全与兜底

1. Key 严禁进 Git；`.env` gitignore；
2. status 仅白名单字段 + 脱敏；
3. 无 Key / 超时 / 401 → Fallback；
4. RAG 失败不回滚母盘；
5. `.env` 原子写。
