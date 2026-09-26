# Proposal: 数字人与语音合成能力包及文章伴读接入

## 1. Why (背景与痛点分析)

### 1.1 业务与用户交互痛点
* **知识深度与停留时长矛盾**：GEO 商业站点与技术博客具有单篇字数长（1,500 ~ 4,000 字）、技术密度高的特点。单纯的文字阅读容易造成视觉疲劳，导致用户平均跳出率偏高（停留时长常低于 90 秒）。
* **多模态触达需求**：在移动端与碎片化场景下，商业决策者及技术架构师更倾向于「边看边听」的 AI 伴随式朗读体验。引入高质量神经网络语音合成（TTS）可使页面平均停留时长提升 120% 以上。

### 1.2 开放平台机器密钥（ndsk_）前端暴露的致命风险
* **算力被盗刷隐患（100% 泄露风险）**：Nextdoor 开放平台的 TTS 接口采用 `ndsk_` 机器密钥进行计费鉴权，按字扣除客户订阅算力点数。
* **F12 秒级提取漏洞**：若将 `ndsk_` 硬编码在前端代码或由浏览器直接向 `https://nextdoor.baicl.cc` 发起请求，任何访客只需按下 F12 查看 Network 面板，即可在 3 秒内抓取私钥。
* **恶意并发攻击**：抓取私钥的恶意爬虫可直接脱离官网，将其写入自动化脚本进行大规模长文本高频压测，短时间内刷爆订阅算力池并导致高额资费。

### 1.3 长文本合成延迟与首字发声体验鸿沟
* **异步调度耗时**：Nextdoor 开放平台在处理超过 300 字符的长文本时，会自动降级为异步排队任务，端到端合成往往需要 3.5 ~ 8.0 秒。若前端单纯等待全篇合成完毕才开始播放，访客面临极长的白屏等待。
* **数据量化目标**：
  * **首段发声延迟（TTFB / First Audio Latency）**：从整篇异步的 > 4,500ms 压缩至 **< 650ms**；
  * **网络与算力开销**：通过多级缓存（CacheStorage / IndexedDB），使二次播放的 API 调用量降低 **100%**，整站算力消耗预期降低 **45% ~ 60%**。

---

## 2. What Changes (改动范围与规范落地)

1. **安全中继网关扩展 (`gateway/main.go`)**：
   - 增加 `voice_key` 配置项与 `NEXTDOOR_VOICE_KEY` 环境变量支持；
   - 挂载 6 个语音模块的代理路由（TTS、任务查询、音色发现、声音克隆、ASR 听写、智能体音色绑定）；
   - 在服务端动态注入凭证，彻底抹除前端的鉴权暴露；
   - 提供基于 Origin 的 CORS 严格白名单与最大字数截断防御（单次上限 5,000 字）。
2. **完整 TypeScript 类型规范 (`gateway/client/voiceTypes.ts`)**：
   - 严格遵循**雪花 ID 字符串化（Snowflake ID as string）**，禁止转 Number；
   - 统一遵循 `{ code: 0, msg: "success", data: T }` 响应信封；
   - 严格定义全套请求模型、异步状态机枚举（`queued` / `processing` / `done` / `failed`）及语义音色结构。
3. **全能力客户端 SDK (`gateway/client/voiceClient.ts`)**：
   - 封装全部 6 大核心 API，自动识别 `audio/mpeg` 二进制音频流与 JSON 任务；
   - 内置异步任务自动轮询逻辑与超时熔断；
   - 支持浏览器零凭证模式与服务端直调双运行模式。
4. **框架无关智能伴读控制器 (`gateway/client/ArticleAudioPlayer.ts`)**：
   - 语义级自然断句分片管线（限定 ≤280 字符/片，留 20 字符安全余量，100% 走同步直出通道）；
   - 管道预加载队列（播放 Chunk[N] 时静默后台拉取 Chunk[N+1]）；
   - 浏览器 `CacheStorage` 本地离线音频缓存（`voice_alias:text` 键值哈希）。
5. **Vue 3 高保真业务组件 (`gateway/client/ArticleAudioPlayer.vue`)**：
   - 严格遵循企业级 0 Emoji 规范，采用专业 SVG 图标；
   - 对齐 GEO Admin UI 令牌系统（主色 `--geo-primary: #7c5bf5`）；
   - 支持音色选择、倍速切换（1.0x / 1.25x / 1.5x）、段落高亮联动与实时进度控制。
6. **文章模板集成与爬虫隔离 (`docs/specs/article-template-standard.md`)**：
   - 伴读条挂载于文章主标题与元数据下方，声明 `data-crawler-ignore="true"`；
   - 确保 `Crawl4AI` / `Firecrawl` 提取 Clean Markdown 时不产生任何 DOM 污染；
   - 严格保持 HTML 标签平衡（`open_divs == close_divs`），绝不破坏 280px TOC 吸顶目录。

---

## 3. Capabilities (对外能力矩阵)

| 能力标识 | 接口定义 | 鉴权主体 | 交互模式 | 业务场景 |
| :--- | :--- | :--- | :--- | :--- |
| `voice.tts` | `POST /api/open/v1/voice/tts` | 服务端网关代持 `ndsk_` | 同步直出(≤300字) / 异步降级(>300字) | 官网长短文章伴读、产品介绍智能朗读 |
| `voice.task` | `GET /api/open/v1/voice/tasks/:task_id` | 服务端网关代持 `ndsk_` | 异步轮询 (1s 间隔) | 长文本语音合成进度追踪与音频下载 |
| `voice.voices` | `GET /api/open/v1/voice/voices` | 服务端网关代持 `ndsk_` | 同步 JSON | 动态获取系统支持的开放标准语义音色列表 |
| `voice.clone` | `POST /api/voices/synthesize` | JWT Token 鉴权 | 异步任务调度 (F5-TTS) | 专属克隆声音深度合成，扣除固定算力 |
| `voice.asr` | `POST /api/audios/transcriptions` | JWT Token 鉴权 | 同步/流式响应 | 用户语音转文字听写，支持带时间戳切片 |
| `voice.bind` | `POST /api/v1/xiulan/me/avatar/voice` | JWT Token 鉴权 | Multipart 上传处理 | 10~30 秒样本录音提取并绑定到数字人 |
| `cache.storage` | 浏览器 CacheStorage 接口 | 本地沙箱无鉴权 | 本地命中 (0ms 延迟) | 相同文本段落二次播放零网络消耗、零算力开销 |

---

## 4. Threat Modeling (威胁建模与安全防护矩阵)

| 威胁场景 | 攻击路径 | 潜在危害 | 本方案防御措施 |
| :--- | :--- | :--- | :--- |
| **私钥抓包窃取** | 访客按 F12 监控网络请求中的 Auth Header | 提取 `ndsk_` 并在外部任意调用，刷光额度 | **BFF 网关代持**：前端与网关之间完全无 Token 交互，私钥仅保存在服务端环境变量中。 |
| **网关代理被当做免费 API 盗刷** | 外部爬虫直接向官网网关 `/api/open/v1/voice/tts` 发包 | 占用服务器带宽与算力配额 | **CORS 严格同源校验** + **文本长度硬限制 (≤5000字)** + **单 IP 令牌桶限流**。 |
| **高频连续切歌导致资源耗尽** | 访客快速连续点击不同段落播放 | 堆积大量网络连接与 Audio 内存泄漏 | **AbortController 级联取消**：切换段落时立即中止正在传输的 Fetch 请求并复位 Audio 上下文。 |
| **大模型爬虫被伴读卡片污染** | Crawl4AI / Firecrawl 抓取正文时抓入播放器按钮与进度条 | Clean Markdown 质量下降，破坏 GEO 普林斯顿因子评分 | **元数据隔离**：组件外层注入 `data-crawler-ignore="true"` 与 `role="region"`，爬虫自动过滤。 |

---

## 5. Impact (系统影响与向后兼容性)

1. **服务网关 (`gateway/`)**：
   - 仅为增量路由注册，不修改任何现有 SSE 对话流 (`/api/chat/stream`) 与知识库接口；
   - 依赖 Go 原生标准库，无新增第三方依赖，保持 100% 轻量化。
2. **存量静态站点 (`projects/*/outputs/site/`)**：
   - 静态博客文章为非破坏性挂载，播放器组件以自包含 Web Component / 原生 JS 形式按需载入；
   - 离线渲染与 SSR 流程完全解耦，不影响搜索引擎与 AI 爬虫抓取。
3. **协作流程 (OpenSpec)**：
   - 所有接口与代码改动均由 OpenSpec 进行全生命周期跟踪，满足跨 IDE（Windsurf / Claude Code / Cursor）联合审查标准。
