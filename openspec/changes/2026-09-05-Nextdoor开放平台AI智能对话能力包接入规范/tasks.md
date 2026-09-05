# 任务清单: Nextdoor 开放平台 AI 智能对话能力包接入规范

## 1. 接入规范与工程隔离准备

- [x] 1.1 核对并固化全局 5 大铁律（同机 Base URL、`vio-source-client`、后端存 Token、雪花 ID 强制字符串、`code === 0` 统一判错）。
- [x] 1.2 确认本地网关对外路由映射表（`/api/chat/stream`、`/api/chat/intent/match`、`/api/writing/sessions`）与统一错误码表。
- [x] 1.3 确认工程隔离边界：在 `gateway/` 独立子目录管理 Go 模块，并在根目录 `.gitignore` 中加入 `gateway/config.yaml`，防止敏感 Token 误提入 Git。
- [x] 1.4 确认长文创作流（Writing Flow）Phase-1 范围仅限于会话初始化与大纲生成。

---

## 2. Go 后端独立流式网关开发 (`gateway/`)

- [x] 2.1 初始化 `gateway/go.mod` 与 `config.yaml.example` 示例配置（固定监听 `8090` 端口），支持从环境变量与本地 yaml 加载凭证，配置放行 `8088` 跨域。
- [x] 2.2 实现 `[SSE] handleChatStream`：使用 `http.Flusher` + `X-Accel-Buffering: no` 实现打字机数据流 0 缓冲、0 延迟透传；遇上游中途中断自动补发 `event:error` + `[DONE]` 帧保证前端收尾。
- [x] 2.3 绑定 `r.Context()` 实现断流联动：当浏览器主动 abort 中断时，自动连带取消对 Nextdoor 上游的 HTTP 请求。
- [x] 2.4 实现 `[POST] handleIntentMatch`：校验 `1 ≤ query(rune) ≤ 60`，超长直接防御性短路返回 `{matched: false}`（不打上游且不报错）；合格短句自动透传。
- [x] 2.5 实现 `[POST] handleWritingSessions`：结构化透传长文创作会话创建。
- [x] 2.6 实现进程级错误解耦与隔离：上游 Nextdoor 握手失败、未启动（50201）或超时（50401）时，统一转译为标准错误 JSON 信封，保证主进程稳定不崩。

---

## 3. 前端交互与 API 客户端开发 (Frontend Client)

- [x] 3.1 编写 TypeScript 类型定义，强制标注 `session_id`、`agent_id` 等雪花 ID 为 `string` 类型。
- [x] 3.2 封装基于 Fetch + ReadableStream 的打字机读取逻辑，接入 `AbortController` 手动随时掐断流。
- [x] 3.3 实现输入框监听防抖与中文输入法（IME）`compositionstart` / `compositionend` 事件绑定，杜绝打拼音时的网络请求风暴。
- [x] 3.4 编写现代化 UI 交互组件示例（支持打字机展现、候选智能体卡片路由与多模态图片预览）。

---

## 4. 验证与跨端审查 (Verification & Review)

- [x] 4.1 在本地（127.0.0.1）验证流式输出的打字机顺滑度与断流打断响应（抓包确认上游请求连带中断）。
- [x] 4.2 验证 Nextdoor 服务关闭/断开时的 50201 错误优雅捕获与前端友好提示。
- [x] 4.3 跨 IDE（Windsurf / Claude Code / Cursor）对照 RULES 与 review-log.md 核对闭环，结论推进入 `[通过]`。
