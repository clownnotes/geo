# 接入小毛驴统一API与GEO协作网站搭建 (Tasks)

## 阶段 1：方案探讨与 API 契约对齐（当前阶段，Strict Stage Boundary）
- [x] 1.1 现场核对能力中心页与 `api-capabilities.ts` 七大包路径
- [x] 1.2 锁定部署锚点：`ne@mini`（100.83.64.112），同机 API `:3001` / 管理台 `:3002`，GEO `:8088`
- [x] 1.3 修订 proposal/design：必复用 account+chat+uploads；优先 kb；禁止自建用户/JWT/LLM 网关
- [x] 1.4 review-log 记录 Cursor 审查修正并停步（本阶段不写业务源码）

## 阶段 2：同机鉴权与接入身份
- [x] 2.1 确认管理台接入方档案存在 `vio-source-client=geo`（或等价 brand_key）
- [x] 2.2 GEO Web/BFF：对接 `POST /api/v1/xiulan/login`、`GET /api/v1/xiulan/me`、扫码 `GET /api/auth/wechat-qr`（可直连或薄代理）
- [x] 2.3 同机 Base 固定 `NEXTDOOR_BASE_URL=http://127.0.0.1:3001`；禁止生产绕公网
- [x] 2.4 雪花 ID 全链路按字符串；单测：测试账号登录 → 带 JWT 调 `/me` 成功
- [x] 2.5 去除 GEO 硬编码单一账号登录路径

## 阶段 3：集中式项目与资产（仅 GEO 域）
- [x] 3.1 项目 CRUD + 成员可见性（只存 `user_id` 引用，不建用户主表）
- [x] 3.2 映射 `/Users/ne/apps/GEO/projects/{slug}`，在线读写 `project.yaml`
- [x] 3.3 报告列表 + `POST .../bundles` 打包下载（路径无动词）
- [x] 3.4 图片/素材改走 `POST /api/v1/community/uploads`（不自建上传）

## 阶段 4：异步 Job + Python 工兵
- [x] 4.1 GeoTask 模型与派发（pending→running→success/failed；含项目级并发互斥队列锁，防多电脑同时写入 outputs 踩踏）
- [x] 4.2 TaskManager 同进程线程调度工兵模块并捕获 stdout 写日志（单实例互斥；非跨进程 os/exec）
- [x] 4.3 `GET /api/v1/tasks/:id/events` SSE
- [x] 4.4 锁定 LLM 仍走 `SSE /api/v1/xiulan/chat`（回归 `tools/geo/llm.py`）

## 阶段 5：知识库与联调验收
- [x] 5.1 （优先）后端透传/客户端已对接 `POST /api/kb/documents` + `POST /api/kb/chat`（单测覆盖）
- [ ] 5.2 两台电脑经 Tailscale 同时打开 GEO，验证同盘无冲突（**待生产机拉码重启后的真实双机验收**）
- [x] 5.3 对照能力中心清单做「复用/不复用」验收表（voice/视频/sub/笔记流标记为不做）
- [x] 5.4 Web 管理台：小毛驴手机号登录文案 + 微信扫码入口 +「协作与任务」页（任务 SSE / bundles / KB）
- [x] 5.5 OpenSpec 已归档（`openspec/changes/archive/...`）；代码已在 `github/main` @ `1784250`
- [ ] 5.6 生产机 `ne@mini`：`git pull` + **重启 :8088**，确认 `auth_sso.py` / 登录页 /「协作与任务」可用（**截至复审仍停在旧提交 `8cd5adf`，未部署**）
