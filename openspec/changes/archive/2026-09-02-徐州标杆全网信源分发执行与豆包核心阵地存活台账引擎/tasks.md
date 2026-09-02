## 1. 分发台账中枢引擎升级与对齐 (`tools/geo/dist_bot.py`)

- [x] 1.1 升级 `DEFAULT_CHANNELS`，对齐中国本土 5 大模型生态阵营（今日头条/豆包、知乎/DeepSeek、微信/元宝、GitHub/Kimi、百度/文心、稀土掘金/辅助）。
- [x] 1.2 优化 `verify_distribution_url`，增强知乎/头条/微信/CSDN 反爬智能识别与标题提取容错。
- [x] 1.3 优化 `markdown_to_styled_html`，确保内联排版直接兼容微信公众平台富文本与知乎编辑器。

## 2. 徐州标杆项目（自营）真实信源分发台账落地

- [x] 2.1 审查并更新 `projects/xuzhou_xuanyuan/outputs/dist_ledger.json`，确保涵盖 5 大本土阵营。
- [x] 2.2 运行 `geo verify-dist xuzhou_xuanyuan`，执行多线程并发存活探测与完成率核验。
- [x] 2.3 验证 Web 端 Step 4 与交付门户（`share.html`）中的分发卡片呈现与跳转。

## 3. SOP 与实战文档定版与全流程验证

- [x] 3.1 完善 `docs/sop/04-distribute-sop.md`，规范化今日头条（长文+微头条双发）、知乎专栏、微信公众号与 GitHub 的发稿 SOP。
- [x] 3.2 更新 `docs/pilot/xuzhou-dev.md`，追加徐州标杆全网信源落地清单与回填指引。
- [x] 3.3 严格遵循规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录审查结论。

