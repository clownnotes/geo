# 接入小毛驴统一API与GEO协作网站搭建 (Proposal)

## 1. 业务背景与痛点 (Why)

1. **多电脑协作断层**：当前 GEO 偏单机本地文件（读写本机 `projects/{project_id}`）。同事换电脑就各存一份，容易覆盖、重复分析，做不到多人同址协同。
2. **拒绝重复造轮子**：小毛驴开放平台（管理台 `http://100.83.64.112:3002`，同机业务 API `http://127.0.0.1:3001`）已有成熟的 **7 大能力包**（账号 / 对话 / 语音 / 视频视觉 / 知识库 / 订阅 / 社区）。GEO 禁止再自建：用户表、密码加密、JWT 签发、LLM Key 轮询、社区级对象上传、通用 RAG 切片。
3. **同机部署铁律**：GEO 生产进程与小毛驴 **同一台物理机**——SSH 别名 `mini`（Tailscale `100.83.64.112`，用户 `ne`，目录 `/Users/ne/apps/GEO` 与 `/Users/ne/apps/xiulan`）。同机互调必须走 `127.0.0.1:3001`，禁止绕公网 `nextdoor.baicl.cc`。
4. **职责边界**：小毛驴管「人、算力、通用 AI、公共上传」；GEO 只做「项目、SOP 流水线、爬虫/探针/质检等行业算法」与集中式 `projects/` 资产。

---

## 2. 核心改动内容 (What)

1. **全面复用小毛驴开放能力（能复用的一律复用）**  
   以能力中心为准：`http://100.83.64.112:3002/community/admin/api-management?tab=capabilities`，契约真源见 XiuLan `api-capabilities.ts`。

   | 能力包 | GEO 是否复用 | 用途 |
   | :--- | :--- | :--- |
   | `account` | **必复用** | 手机号密码 / 微信扫码 / 微信快捷登录、`/me` 画像、统一 JWT 与雪花 ID |
   | `chat` | **必复用** | `SSE /api/v1/xiulan/chat`（阶段一解读、阶段三改写等已在用；禁止再自建 LLM 网关） |
   | `community`（uploads） | **必复用** | `POST /api/v1/community/uploads` 传 Logo / 素材图 |
   | `kb` | **优先复用** | 品牌/客户资料进小毛驴知识库切片与问答；GEO 本地知识目录可作镜像/备份 |
   | `media`（vision upload） | **按需复用** | 多模态参考图、截图分析 |
   | `voice` / `media` 视频 / `sub` | **暂不纳入首期** | 与 GEO SOP 无刚需；日后做口播/充值再开 |
   | `community` 笔记评论流 | **暂不纳入** | 非 GEO 交付主路径 |

2. **中心化部署与集中式存储（同机 `ne`）**  
   - 废止「每人电脑各存一份项目」作为生产模式；  
   - GEO Web / 任务调度 / `projects/` 落在 `mini` 的 `/Users/ne/apps/GEO`；  
   - 同事只用浏览器访问（局域网 / Tailscale），上传与推演都在服务器完成。

3. **GEO 业务壳（薄 BFF + Python 工兵）**  
   - **不**在小毛驴里重写 26 维 GEO 算法；  
   - GEO 侧提供：项目 CRUD、成员可见性、异步 Job（派发本机 Python CLI）、报告/ZIP 下载、SSE 任务日志；  
   - 登录：浏览器拿小毛驴 JWT（或经 GEO 薄代理透传），GEO 只验签/缓存 `UserSnapshot`，**不存密码、不发 Token**。

4. **接入身份**  
   - 登记 `vio-source-client: geo`（或管理台已建档 brand_key）；  
   - 所有对 `:3001` 的调用带该头 + `Authorization: Bearer <JWT>`（或机器密钥场景沿用现有 `NEXTDOOR_API_KEY`）。

---

## 3. 对外能力清单 (Capabilities)

| 能力标识 | 能力名称 | 说明 |
| :--- | :--- | :--- |
| `auth.sso` | 统一账号直通登录 | 复用小毛驴 `account` 全套，雪花 ID 字符串，跨端 SSO |
| `llm.nextdoor` | 大模型经小毛驴出海 | 复用 `chat`；同机 Base=`http://127.0.0.1:3001` |
| `asset.upload.shared` | 公共素材上传 | 复用 `community/uploads`（及按需 `vision/upload`） |
| `kb.shared` | 共享知识库 | 优先复用小毛驴 `kb` |
| `project.manage` | 多用户项目集中管理 | **GEO 自有**：项目/成员/配置，磁盘 `projects/{slug}` |
| `job.pipeline` | 异步 SOP 调度 | **GEO 自有**：体检/改写/探针等 Python Job + 日志流 |
| `portal.web` | 统一运营大盘 | 浏览器多人在线；后端在 `ne@mini` |

---

## 4. 影响范围分析 (Impact)

1. **CLI 保留**：`./geo audit` 等本机脚本仍可跑；生产以服务器集中目录为准。  
2. **目录不改**：`projects/{id}/project.yaml` 与 `outputs/` 结构保持。  
3. **同事本机**：无需自配 Python 全家桶，浏览器即可开工。  
4. **禁止事项**：禁止新建第二套用户库；禁止把 LLM Key 散落到各同事电脑；禁止同机调公网绕回。
