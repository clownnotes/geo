## 1. 准备与梳理

- [x] 1.1 核对阶段四 `ide-pack`、`writeback-cmd`、`ide-clipboard`，以及阶段零 `boss-audit-pack`、`deepen-prompt` 的前端调用。
- [x] 1.2 改写只调用 `llm.resolve_llm_runtime()` 与 `llm.call_nextdoor_chat()`。不新建第二套客户端。

## 2. 后端算力接口与安全加固

- [x] 2.1 在 `tools/geo/server.py` 实现 `GET /api/projects/{id}/answer-rewrite/content`：读取指定渠道当前草稿或定稿文本。
- [x] 2.2 实现 `POST /api/projects/{id}/answer-rewrite/ai-generate`：在服务端暗箱组装 9 因子 Prompt，调用小毛驴大模型直接生成渠道改写稿，仅向前端返回成文文本。
- [x] 2.3 实现 `POST .../answer-rewrite/save-final`：渠道必须在 `CHANNEL_META` 内，只写表里的 `writeback` / `publish_sync`。忽略请求里的文件名和路径。响应不带磁盘路径。
- [x] 2.4 按 `design.md` 第 4 节，把配方口、`/export`、`/acceptance/download-zip`、`/site/nginx-conf` 收进开发者专属。不要锁 `/monitor/prompts`，不要锁 `/export-audit-html`，不要用 `/download`、`/file` 这种短后缀。
- [x] 2.5 `ai-generate` 忽略自由指令；模型若吐出配方、源码或文件清单，丢掉，只返回固定人话。报错也不回传异常原文。
- [x] 2.6 `brief` 对运营去掉模具、禁写条、写回路径和规范原文。
- [x] 2.7 运营读取 `output/{文件名}` 时，文件名含 `9因子`、`语料`、`prompt`、`SOP` 或以 `.py` 结尾则 403。不要把全部产出文件都关掉。

## 3. 前端界面去 IDE 化与内置编辑器

- [x] 3.1 改造 `web/index.html` 阶段四“段 B”卡片：移除“复制给 IDE 改写”、“复制写回口令”等割裂且易泄密的流程。页面流程改为「看题目 → 网页里改 → 放行确认」。
- [x] 3.2 增加【小毛驴 AI 智能改写】、在线内容编辑区与【保存定稿】按钮，完成网页内闭环。
- [x] 3.3 阶段零拿掉「贴给 IDE」：`web/step0-src` 文案与按钮改为本页出题 + 去豆包问；复制到外部 IDE / 反重力 / Cursor 的函数一律拒绝；已重新 `npm run build` 打包 `web/assets/step0/step0.js`。

## 4. 验证与回归

- [x] 4.1 自动化测试：运营调第 4 节配方口和两个整包下载为 403；`/monitor/prompts` 仍可调；`brief` 走 `sanitize_brief_for_operator`；`save-final` 拒绝表外渠道；敏感文件名走 `is_sensitive_output_filename`；新增页面静态护栏断言。7/7 通过。
- [x] 4.2 界面实测护栏：源码与打包产物不得再出现「复制给 IDE / 贴反重力 / 给 Cursor」指路文案（见 `test_07`）。
