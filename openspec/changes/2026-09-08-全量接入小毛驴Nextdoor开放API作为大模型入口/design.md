# Design: 全量接入小毛驴 Nextdoor 开放 API 作为大模型入口

## 1. 延迟与同机拓扑（先答产品问题）

```
[GEO tools/geo :8088]  --HTTP-->  [Nextdoor 统一后端 :3001 / 127.0.0.1]
                                      |
                                      +--> llmproxy --> 厂商 chat/completions
```

- **同机 / 同 Tailscale 网段**：推荐 `NEXTDOOR_BASE_URL=http://127.0.0.1:3001`（或生产反代后的本机 upstream）。
- **延迟结论**：回环 RTT 通常 <1ms～数 ms；端到端耗时几乎全部来自模型推理与 Token 生成。相对「GEO 直连 DeepSeek 公网」，同机经 Nextdoor **不会明显变慢**，还可能因专属链 / 本地调度更稳。
- **禁止**默认走公网绕一圈再回本机；仅异地调试才用 `https://nextdoor.baicl.cc`。

---

## 2. 架构总览

```
业务模块 (rewrite / ingest / distribute / probing / …)
        │
        ▼
utils.call_llm_api / get_configured_llm   ← 对外签名保持稳定
        │
        ▼
llm.resolve_llm_runtime()
        │
        ├── 默认：provider=nextdoor
        │         POST {base}/api/v1/xiulan/chat
        │         Header: Authorization: Bearer <JWT>
        │                 vio-source-client: <brand>   # 建议 geo
        │         Body: { mode, messages, stream: true }
        │         聚合 SSE delta.content → 完整文本
        │
        ├── 应急：GEO_LLM_DIRECT=1 时才允许旧 OpenAI 兼容直连（默认关）
        │
        └── 失败：返回失败 → 调用方走既有 Python Fallback
```

前端对话组件（若启用）仍可经 `gateway/:8090` 透传；**批处理不经 gateway**，避免 Python→Go→Nextdoor 双跳。

---

## 3. 契约对齐（对照开放平台 chat 能力包）

| 项 | 约定 |
| :--- | :--- |
| 上游路径 | `POST /api/v1/xiulan/chat` |
| 鉴权 | `Authorization: Bearer <JWT>`（仅后端 `.env` / 环境变量） |
| 品牌头 | `vio-source-client: geo`（或管理台登记的 `brand_key`） |
| 请求体 | `mode`: `flash` \| `think` \| `auto`；`messages`: `[{role, content}]`；`stream`: `true`（主路径） |
| 成功形态 | SSE：`data: {"choices":[{"delta":{"content":"..."}}]}` 或平台等价 `delta` 字段；以聚合后的纯文本交付业务 |
| 失败形态 | HTTP 非 2xx 或握手期 JSON `{code≠0}` → 映射为 `call_llm_api` 失败 |
| 雪花 ID | 若响应含 id，一律按 `string` 处理，禁止转 Number |
| 专属链 | Nextdoor `ChatService` 按 `ClientBrand` 解析接入端模型链（已有 2026-09-05 逻辑） |

**聚合规则（钉死）**：
1. 读 SSE 直到 `data: [DONE]` 或连接关闭；
2. 拼接所有 content delta；忽略 `_hit` / `_heartbeat` / `_queue` 元数据帧；
3. 若全程无 content 且出现 error 帧 → 失败；
4. 超时：沿用调用方传入的 `timeout`（重构默认 120s）。

可选优化（非阻塞）：若上游对 `stream:false` 返回可解析 JSON 正文，可作批处理快路径；必须以集成测试锁定，失败则回退 SSE 聚合。

---

## 4. 环境变量与配置白名单

### 4.1 主路径（Web `/api/llm/config` 唯一写入）

| 变量 | 说明 |
| :--- | :--- |
| `NEXTDOOR_BASE_URL` | 默认 `http://127.0.0.1:3001` |
| `NEXTDOOR_JWT_TOKEN` | 服务账号 / 管理员登录 JWT（禁止入 Git） |
| `NEXTDOOR_SOURCE_CLIENT` | 默认 `geo` |
| `NEXTDOOR_CHAT_MODE` | 默认 `flash`。有专属链时**不改变梯队选模**；主要用于计费档与整链失败后回落全站池时的 `ChatByMode` |

与 `gateway/config.yaml` 对齐：gateway 可读同一组 env（已有 `NEXTDOOR_*` 覆盖逻辑）。

### 4.2 应急直连（默认关闭）

仅当 `GEO_LLM_DIRECT=1` 时解析旧 `DEEPSEEK_*` / `ARK_*`；Web 主配置 UI **不展示**厂商 Key 表单（或折叠为「应急直连」高级区且默认隐藏）。

### 4.3 安全

- JWT 禁止下发浏览器；status 仅返回脱敏（前 6 + `…` + 后 4）。
- `POST /api/llm/config`：`check_auth`；Ping 失败不落盘；原子写 `.env`（0600）。

---

## 5. API 与 UI

### 5.1 `GET /api/llm/status`

字段白名单：`status`、`provider`（`nextdoor`|`direct`|`none`）、`base_url`、`brand`、`mode`、`api_key_masked`（JWT 脱敏）、`latency_ms`、`source`、`message`。

探针：对 Nextdoor 发极短 user 消息（如「ping」）或复用现有 chat 最小请求；`401/403→auth_failed`，超时/连接失败→`unreachable`。

### 5.2 `POST /api/llm/config`

Body：`{ base_url?, jwt_token, source_client?, mode? }` → 写入 §4.1 → Ping → 成功才落盘。

### 5.3 前端

- 阶段三 LLM Tag：展示 `Nextdoor · geo · flash` / `Fallback` / `未配置`。
- 配置弹窗标题改为「小毛驴 / Nextdoor 开放 API」；字段对齐 §4.1；文案说明「同机回环、厂商 Key 在 Nextdoor 统一管理」。

---

## 6. 调用方兼容策略

| 模块 | 策略 |
| :--- | :--- |
| `rewrite.py` | 继续 `call_llm_api(..., timeout=120)`；mode 可用 env `NEXTDOOR_CHAT_MODE=think` |
| `ingest` / `distribute` / `defense` / `evolution` | 签名不变 |
| `probing` / 多模型评测 | **本期**：统一经 Nextdoor（由中枢选模）；若需「多厂商对照」报表，标为后续变更（依赖 Nextdoor 多链或保留 DIRECT 应急） |
| RAG 级联 | 不改；仍挂在母盘落盘后 |

---

## 7. 前置运维清单（人工，写入 SOP 短节）

1. Nextdoor 管理台「API 管理 → 接入前端」登记 `brand_key=geo`，启用，绑定专属模型链；
2. 能力包勾选至少包含 `chat`；
3. 签发长期可用 JWT（或运维账号登录导出），写入 GEO `.env`；
4. 本机确认 `curl -H "Authorization: Bearer …" -H "vio-source-client: geo" http://127.0.0.1:3001/api/v1/xiulan/me` 返回 `code===0`。

---

## 8. 风险与缓解

| 风险 | 缓解 |
| :--- | :--- |
| SSE 字段形态与样例不完全一致 | 适配器兼容多种 delta 路径；单测用录制夹具 |
| JWT 过期导致全站 Fallback | status Tag 醒目；config 一键重探测 |
| 长 Prompt 触达中枢上下文上限 | 保持现有 50k 素材预算；超限截断策略不变 |
| 误开 DIRECT 双轨 | 默认关；文档与 UI 标明应急 |
| 在 GEO 重复实现冷却/特惠 | **禁止**：阶梯、特惠优先、冷静期一律复用 Nextdoor `llmproxy` 模型/Key 全局状态；接入组只配顺序与是否复用特惠 |

### 8.1 复用铁律（产品共识）

- 接入端专属组 = **编排**（顺序 + 特惠复用开关），不是第二套熔断中心。
- 模型在组内调用失败 → 写入**该模型/Key 的全站冷静**；管理台统一恢复后，所有链（含 GEO）同时受益。
- GEO **不得**本地维护「挂了休息几分钟」或 per-brand cooldown。

### 8.2 与小毛驴模型管理对照审计（2026-09-08）

对照源码：`ChatService` 分流、`client_*` 阶梯链、`api_frontends` 专属组、`llmproxy` 冷静。

| 项 | 结论 |
| :--- | :--- |
| 专属组自上而下 + 特惠优先 + 模型/Key 全局冷静 | **无冲突**，与产品共识一致，GEO 复用即可 |
| GEO 再配厂商 Key / 本地冷却 | **已禁止**，无冲突 |
| `mode=flash/think` 与专属链 | **软冲突（认知）**：专属链命中时走 `Chat(client_*)`，**不按**全站「免费/深度」调用分配选模；`mode` 主要影响计费价与「整链失败后的回落」。UI 勿暗示 GEO 的 flash/think 会改专属梯队 |
| 专属链整链失败 | **软冲突（边界）**：现网会 **降级回落全站 `ChatByMode(mode)`**（社区 flash/think 池），不是「组内全挂就彻底失败」。与「组里挂了就挂了」不完全同义——单模型冷静=组内顺位；**整链打光**仍可能打到全站池 |
| 模型列表「调用分配」标签（免费/深度/解读…） | **无调度冲突**：那是全站 `dispatch_*` 挂载；接入专属组只认组内成员顺序。标签灰掉不阻止该模型进 GEO 专属梯队 |
| JWT 身份 | **运营依赖**：每次 chat 走该 JWT 用户的算力/订阅；须用有额度的服务账号，否则与模型管理无关但会全站 Fallback |
| brand / Base URL | **配置一致性**：Spec 默认 `geo` + `:3001`；gateway 示例曾用 `geo-custom-brand` / `:9000`——必须与管理台「接入前端」登记值、本机实际监听端口一致，否则专属链不生效（回落全站默认） |

**Spec 订正（本期）**：
1. 文档钉死：有专属链时，选模 = 管理台接入组编排；`NEXTDOOR_CHAT_MODE` 不改变专属梯队顺序。
2. 整链回落行为写明为「**沿用 Nextdoor 现网（产品已拍板）**」：专属链打光后回落全站 `ChatByMode`；GEO **不**改为 fail-closed。
3. 前置清单增加：核对 `brand_key`、专属链已启用、JWT 账号有算力。

---

## 9. 非目标

- 不在本期让浏览器直持 JWT 调 Nextdoor；
- 不要求 Nextdoor 新增裸 OpenAI `/v1/chat/completions` 开放能力包（以现有 `xiulan/chat` 为真 API）；
- 不自动部署生产、不改 Nginx。
