# Proposal: 全量接入小毛驴 Nextdoor 开放 API 作为大模型入口

## Why (为什么做)

1. **统一真相源与算力入口**：小毛驴 AI（Nextdoor 开放平台）已是同机部署的模型中枢——厂商 Key、专属调用链、算力扣费、熔断与模型矩阵均在 Nextdoor 管理台维护。GEO 阶段三却仍把 DeepSeek/豆包 Key 写入本仓 `.env` 直连厂商，造成「双套密钥、双套探测、运营改价要改两处」的分裂。
2. **既有契约已就绪**：开放平台 `chat` 能力包（`/api/v1/xiulan/chat` SSE、`intent/match`、`writing-flow`）与 GEO `gateway/`（8090）已按 2026-09-05 规范落地；后端对 `vio-source-client`（如 `geo`）支持接入端专属模型链。缺口只在：**业务批处理 LLM（重构 / 提纯 / 分发 / 探测等）尚未走同一入口**。
3. **同机拓扑无转发痛点**：Nextdoor 与 GEO 同机（本机 Tailscale `100.83.64.112` 上 3001/3002 + 本地 8088）。经 `127.0.0.1` 回环或同网段调用，额外延迟在毫秒级，相对大模型推理（数秒～数十秒）可忽略；不构成拒绝统一接入的理由。

## What Changes (改动了什么)

1. **唯一 LLM 入口收敛到 Nextdoor 开放 API**：
   - `tools/geo/llm.py` / `utils.call_llm_api` 默认改为调用 Nextdoor `POST /api/v1/xiulan/chat`（JWT + `vio-source-client`），收集完整回复文本后返回给既有调用方；
   - 覆盖全量业务调用点：阶段三重构、素材提纯、分发文案、探测、防御、演进等一切现走 `call_llm_api` / `get_configured_llm` 的路径。
2. **配置面改为「开放平台凭证」而非厂商 Key**：
   - Web「配置 API Key」弹窗改为配置 / 探测 Nextdoor：`NEXTDOOR_BASE_URL`、`NEXTDOOR_JWT_TOKEN`、`NEXTDOOR_SOURCE_CLIENT`、可选 `mode`（`flash`/`think`/`auto`）；
   - 禁止再把厂商 `DEEPSEEK_API_KEY` / `ARK_API_KEY` 作为主路径写入（兼容只读：仅当显式 `GEO_LLM_DIRECT=1` 应急直连时保留，默认关闭）。
3. **与现有 gateway 正交协同**：
   - 前端对话类能力继续可走 `gateway/:8090`；
   - Python 批处理**直连** Nextdoor Base URL（不强制经 Go 网关二次跳），同凭证、同品牌头，避免双跳。
4. **无中枢时平滑降级**：Nextdoor 不可达 / 401 / 超时 → 沿用现有 Python Fallback（模板拼接），status 明确展示 `nextdoor` / `fallback` / `none`。

## Capabilities (新增或修改的对外能力)

1. **`resolve_nextdoor_runtime()`**：解析同机/生产 Base URL、JWT、品牌标识、默认 mode；`source` 标注 `.env`/`env`/`none`。
2. **`call_llm_api` → Nextdoor Chat 适配器**：组装 `messages`（system+user）、请求 SSE（或 `stream:false` 若上游稳定支持）、聚合 `delta.content` 为完整文本；超时与现网一致（重构 120s 等）。
3. **`GET /api/llm/status`**：探测改为对 Nextdoor 发极短 chat（或专用健康检查），返回 `provider=nextdoor`、脱敏 JWT、`base_url`、`brand`、`latency_ms`、`status`。
4. **`POST /api/llm/config`**：只写 Nextdoor 白名单 env；Ping 失败不落盘。
5. **管理台前置条件清单（文档化）**：接入端 `brand_key`（建议 `geo`）已在 Nextdoor「API 管理 → 接入前端」启用，并绑定专属模型链；JWT 为有效登录态账号。

## Impact (受影响的部分)

- **核心代码**：`tools/geo/llm.py`、`utils.py`；间接影响 `rewrite.py`、`ingest.py`、`distribute.py`、`monitor.py`/`probing.py`、`defense.py`、`evolution.py`、`intent.py` 等所有 LLM 调用方（接口签名尽量不变）。
- **服务与 UI**：`tools/geo/server.py` 的 `/api/llm/status|config`；`web/index.html` 配置弹窗与 LLM Tag 文案。
- **配置**：根目录 `.env` 键名切换；`gateway/config.yaml` 与 Python 侧共享同一套 `NEXTDOOR_*` 约定。
- **测试**：扩展 / 替换 `tests/test_llm_rag_cascade.py`，增加 Nextdoor SSE 聚合与无 JWT 降级用例（mock HTTP，不打真网）。
- **不在本期**：改 Nextdoor 上游开放新「裸 chat/completions」能力包；不改生产自动部署；不把 JWT 下发浏览器。
- **阶段隔离**：本变更仅 `propose`；审查通过后再 `/opsx-apply`；严禁擅自归档。
