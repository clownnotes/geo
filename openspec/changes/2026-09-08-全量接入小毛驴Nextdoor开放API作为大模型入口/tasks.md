# Tasks: 全量接入小毛驴 Nextdoor 开放 API 作为大模型入口

- [x] 1. 运行时与适配器（核心）
  - [x] 1.1 在 `tools/geo/llm.py` 实现 `resolve_nextdoor_runtime()`：读取 `NEXTDOOR_BASE_URL` / `JWT` / `SOURCE_CLIENT` / `CHAT_MODE`；默认 Base `http://127.0.0.1:3001`、brand `geo`、mode `flash`；携带 `source`
  - [x] 1.2 实现 Nextdoor Chat 客户端：POST `/api/v1/xiulan/chat`，注入 JWT + `vio-source-client`；SSE 聚合 `delta.content`（兼容多形态）；忽略 heartbeat/hit/queue；超时尊重入参
  - [x] 1.3 改造 `resolve_llm_runtime` / `call_llm_api`：**默认走 Nextdoor**；仅 `GEO_LLM_DIRECT=1` 时走旧 OpenAI 兼容；无凭证返回可识别失败文案
  - [x] 1.4 `.env` 加载/原子写入白名单改为 Nextdoor 键；与 gateway 的 `NEXTDOOR_*` 命名对齐

- [x] 2. 状态与配置 API
  - [x] 2.1 `GET /api/llm/status`：字段白名单按 design §5.1；探针打 Nextdoor 极短 chat；TTL 可保留 60s
  - [x] 2.2 `POST /api/llm/config`：只写 Nextdoor 白名单；Ping 失败不落盘；鉴权规则与现网一致
  - [x] 2.3 废弃/隐藏主路径厂商 Key 写入（DIRECT 不进默认 UI）

- [x] 3. 前端与文案
  - [x] 3.1 配置弹窗改为 Nextdoor 字段（Base URL / JWT / 品牌 / mode）
  - [x] 3.2 LLM Tag 展示 `Nextdoor · {brand} · {mode}` / Fallback / 未配置（0 Emoji）
  - [x] 3.3 SOP 短节：`docs/sop/` 增补「阶段三走小毛驴开放 API」前置清单（design §7）

- [x] 4. 调用链回归与测试
  - [x] 4.1 确认 `rewrite` / `ingest` / `distribute` 等无需改签名即可走新入口
  - [x] 4.2 单测：mock SSE 聚合成功；401/超时失败；无 JWT → none；DIRECT 开关行为
  - [x] 4.3 扩展 `tests/test_llm_rag_cascade.py`：母盘路径在 mock Nextdoor 下仍级联 RAG（或保持 full 模式断言）
  - [ ] 4.4 本地手工：配置 JWT → status ready → 增量/全量重构一次（有算力账号）

- [x] 5. 协同与停步
  - [x] 5.1 在 `review-log.md` 等待跨 IDE / 用户审查结论为 `[已达成共识]` 或 `[通过]` 后再 `/opsx-apply`
  - [x] 5.2 apply 完成后立即 STOP，等待人工验收；严禁擅自 archive
