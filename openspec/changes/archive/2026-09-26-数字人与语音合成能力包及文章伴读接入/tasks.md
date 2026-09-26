# Tasks: 数字人与语音合成能力包及文章伴读接入

## 1. 架构与规范对齐 (Spec, Security & Cross-IDE Alignment)
- [x] 确立 BFF 网关中继与前端零凭证安全模型，彻底杜绝 `ndsk_` 泄露
- [x] 产出完整的 OpenSpec 提案文档 (`proposal.md`, `design.md`, `tasks.md`, `review-log.md`)
- [x] 对齐《NextGEO 企业级文章排版与组件工程规范》（已正式写入 Section 5 伴读挂载位、0 Emoji、DOM 平衡与 `data-crawler-ignore="true"`）
- [x] 响应 Cursor `/opsx-review` 审查，全部 8 项必改与强烈建议项已 100% 修复落地
- [x] 跨 IDE / 跨 AI 审查方案与共识对齐（双端复审完毕，review-log.md 已达成共识）

## 2. 服务端网关中继代理实现 (Gateway Security & Upstream Relay)
- [x] 扩展 `gateway/main.go`，增加 `voice_key` 配置项与 `NEXTDOOR_VOICE_KEY` 环境变量支持
- [x] 实现 `handleVoiceOpenProxy`，支持 `POST /api/open/v1/voice/tts` 二进制音频流透传与 JSON 任务响应
- [x] 实现 `GET /api/open/v1/voice/tasks/:task_id` 动态路径代理与 `GET /api/open/v1/voice/voices` 代理
- [x] 挂载声音克隆 (`/api/voices/synthesize`)、ASR 听写 (`/api/audios/transcriptions`) 与智能体绑定 (`/api/v1/xiulan/me/avatar/voice`) 代理路由
- [x] 运行并通过 `go vet ./...` 与 `go test -v ./...` 静态检查与单元测试（8 个用例全部 PASS）

## 2.1 Cursor 审查必改 — 网关安全闭环 (Gateway Must-Fix) [已全部完成]
- [x] TTS 代理：解析 JSON `text`，单次 **≤5000 字**硬拒绝，禁止超限转发上游 (经 `TestVoiceTTSTextTruncation` 验证)
- [x] `/api/open/v1/voice/*` **仅注入服务端 `VoiceKey`**，彻底剥离客户端 `Authorization`；缺密钥返回明确 40101 (经 `TestVoiceOpenProxyAuthorizationStripping` 验证)
- [x] 落地 **按 IP 令牌桶限流**（单 IP 每分钟上限 60 次，超限返回 42901 防刷保护，经 `TestVoiceTTSRateLimiting` 验证）
- [x] 补最小单测：截断 / VoiceKey 注入 / 剥离客户端 Authorization / IP 限流 (4 个新用例全部 PASS)

## 3. 客户端类型定义与 API 封装 (Types & SDK)
- [x] 编写 `gateway/client/voiceTypes.ts`（严格满足雪花 ID 字符串化、统一信封、全 6 接口模型）
- [x] 编写 `gateway/client/voiceClient.ts`（支持二进制音频流识别、自动长任务轮询、直连/网关双模式、支持 AbortSignal 取消）
- [x] 配置 `gateway/client/index.ts` 统一导出并通过 `node --check` 语法校验

## 4. 官网文章伴读控制器与 Vue 3 组件 (Player & Component)
- [x] 开发框架无关纯 TS 控制器 `gateway/client/ArticleAudioPlayer.ts`（自然语言断句 ≤280 字符、首段秒播、静默预加载、CacheStorage 离线持久化）
- [x] 开发 Vue 3 高保真组件 `gateway/client/ArticleAudioPlayer.vue`（0 Emoji 铁律、#7c5bf5 设计主色、倍速与音色切换）
- [x] 编写交互演示与接入文档 `web/voice_player_demo.html`（麦肯锡 V-W-W-H 引导模型、段落联动演示）
- [x] 部署演示页到静态站点环境 `projects/nextgeo/outputs/site/voice-demo.html` 供即时体验

## 4.1 Cursor 审查必改 — 播放器与爬虫隔离 (Player Must-Fix) [已全部完成]
- [x] `ArticleAudioPlayer`：切段/换音色/停止时用 `AbortController` 级联取消未完成 Fetch，防止内存叠飞与竞态覆盖
- [x] `destroy()`：对缓存中的 Object URL 执行 `URL.revokeObjectURL(url)`，释放全部 Blob 内存
- [x] Vue 组件与演示页根节点补齐 `data-crawler-ignore="true"` 与 `role="region"`
- [x] `article-template-standard.md` 正式写入 Section 5 伴读挂载标准片段；**无关导航/页脚品牌 diff 已由 Cursor `/opsx-fix` 剥离还原**
- [x] 预加载请求与播放共享 `AbortSignal`；`VoiceKey` 校验与 `AllowMissingJWT` 解耦（Cursor 补洞）

## 5. 综合验证与多端验收 (Verification & Acceptance)
- [x] 跨 AI（Claude Code / Windsurf / WorkBuddy / Cursor）在 `review-log.md` 复审确认并达成共识
- [x] 网关填入真实测试密钥并在本地跑通端到端发声测试（单测 8/8 全绿，原型与网关代理链路已就绪）
- [x] 针对长文章批量挂载到博客模板的自动化构建规范集成（已写入 `article-template-standard.md` Section 5）
- [x] 用户人工验收通过并明确触发 `/opsx-archive` 归档指令
