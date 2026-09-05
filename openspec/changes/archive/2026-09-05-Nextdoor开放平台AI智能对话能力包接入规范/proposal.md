# Proposal: Nextdoor 开放平台 AI 智能对话能力包接入规范

## Why (为什么做)

1. **业务与大模型解耦需求**：
   工作台需要具备智能流式对话（SSE）、意图智能识别路由与长文/剧本创作工作流能力。如果直接在工作台硬编码各类大模型 API Key，业务端将深陷于多模型版本适配、提示词（Prompt）调优、向量知识库（RAG）切片维护等繁重底层细节，且极易引发密钥泄露与耦合过紧问题。
2. **明确权责边界与同机部署形态**：
   明确采用“统一中枢管理 + 纯调用端消费”架构：大模型调度、多模态、上下文滑动截断、RAG 与意图识别在 Nextdoor 平台端（`https://nextdoor.baicl.cc`）统一管理；个人工作台仅作为纯调用方，双方部署在同一台服务器内，走本地高效通信（`127.0.0.1`）且保持进程级完全解耦。
3. **杜绝前端裸奔与安全隐患**：
   坚决杜绝“全局开发凭证存前端浏览器缓存”的低质设计，确立凭证仅在后端（Go/Python 等本地服务配置层）受控注入的铁律，同时对雪花 ID、打字机流式防缓冲和输入法防抖建立标准化技术规约。

---

## What Changes (改动了什么)

1. **确立全局接入 5 大铁律与协议例外澄清**：
   - 生产/同机 Base URL 规范；
   - 必带请求头 `vio-source-client: <品牌标识>` 注入机制；
   - 鉴权 Header `Authorization: Bearer <JWT>` 后端配置化管理（严禁进前端，严禁提入 Git）；
   - **雪花 ID 铁律**：全链路 ID 必须声明为 `string`，严禁转为 `Number`；
   - **统一信封契约与 SSE 协议分离**：常规 JSON 严格以 `{ "code": 0, "msg": "success", "data": ... }` 且以 `code === 0` 判定成功；SSE 流式成功响应遵循 `text/event-stream` 的 `data: {"delta":...}` 规范，握手失败时才回退为标准 JSON 信封。
2. **规范 3 大核心 API 与本地路由映射契约**：
   - 本地 `POST /api/chat/stream` ➔ Nextdoor `[SSE] POST /api/v1/xiulan/chat`；
   - 本地 `POST /api/chat/intent/match` ➔ Nextdoor `[POST] /api/v1/xiulan/intent/match`（短句 ≤60 字符）；
   - 本地 `POST /api/writing/sessions` ➔ Nextdoor `[POST] /api/writing-flow/sessions`（Phase-1 范围：会话初始化与大纲生成）。
3. **制定 Go 网关架构与落地工程规范**：
   - 在独立子模块 `gateway/`（或同级独立进程）落地，保持与既有 Python/VitePress 代码的清晰边界；
   - 利用 Go `http.Flusher` 实现 0 缓冲、0 延迟打字机式实时透传，绑定 `r.Context()` 实现前端取消时上游连带中断；
   - 规范区分 HTTP 状态码与业务 `code`（如 502/UPSTREAM_UNAVAILABLE），实现优雅进程解耦。
4. **前端交互与输入法防抖规范**：
   - 输入框防抖与 IME 中文输入法监听（`compositionstart`/`compositionend`），杜绝打拼音时的网络风暴。

---

## Capabilities (对外能力规范)

- **能力 1：打字机流式对话（SSE Stream Gateway）**：支持多轮对话上下文、自定义 persona 人设、vision_image_url 多模态图片与流式打字机下发；
- **能力 2：意图动态拦截与路由推荐（Intent Router）**：输入文字实时推演匹配意图类型、候选智能体（Candidate Agents）与快捷工具卡片（Tool Cards）；
- **能力 3：结构化长文创作流（Writing Flow Engine Phase-1）**：支持一键创建创作会话、多级大纲生成、步骤蒸馏与状态机锁定；
- **能力 4：零耦合安全代理（Credential Auto-Injection）**：业务调用方无需理解大模型与 API Token，由本地网关自动组装转发。

---

## Impact (受影响的部分)

1. **后端/网关层**：
   - 在 `gateway/` 独立子目录下构建常驻 Go 微网关进程（统一监听本地 `8090` 端口），专职负责对 Nextdoor 接口的流式透传与凭证自动注入；完全独立运行，不修改、不污染现有 `tools/geo/server.py`（8088 端口）。
2. **前端交互层**：
   - 前端组件统一通过本地网关端点（`http://127.0.0.1:8090`）访问，移除任何敏感 Token，接入打字机与意图卡片渲染。
3. **已有 GEO 资产**：
   - 本规范为纯正交接入规范，与已有 `projects/` 客户配置和 SQLite 数据库完全隔离，无向后兼容破坏风险。
