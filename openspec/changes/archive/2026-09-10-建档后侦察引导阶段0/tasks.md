# 任务清单：建档后侦察引导阶段0

## A. 口径

- [x] 未侦察：创建/进入流水线 → 阶段 0；已有基线 → 直达 01；进 01 仅软确认（Antigravity 共识）
- [x] 托管占位固定 `https://{client_id}.baicl.cc` + `site_pending: true`
- [x] 一句话业务新建必填 15～80 字；`site_pending` 时剧本跳过官网/URL 题
- [x] 更新 SOP：创建后必经阶段 0；占位站与一句话口径

## B. 后端与 CLI

- [x] `normalize_official_url` + 创建写入 `site_pending` / `business_one_liner`；缺一句话 400
- [x] `scalar_keys`（及 bool）支持新字段
- [x] `probe-script`：优先一句话；`site_pending` 跳过 URL 题并补足 6～10 条
- [x] 单测：URL 规范化、占位、长度校验、pending 剧本无官网题

## C. 前端

- [x] `step-0-probe` 面板 + 侧栏「00 侦察建档」（Lucide `radar`）
- [x] `enterWizard` / 创建成功按 `probe_status` 路由；未侦察进 01 软确认
- [x] 三步命令复制 + 刷新状态 + `site_pending` Tag
- [x] 新建弹窗：裸域名、托管勾选、一句话必填；缩短 Cursor 长文案
- [x] 0 Emoji 自检（阶段 0 / 新建弹窗无彩色表情）

## D. 停步

- [x] 单测 `tests.test_probe_backfill` 8/8 通过；逻辑本地可验证
- [x] `review-log`；**等待验收**（不归档、不推生产）
