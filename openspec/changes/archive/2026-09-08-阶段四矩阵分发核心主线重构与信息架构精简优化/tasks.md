## 1. 后端 API 补齐与联动逻辑优化

- [x] 1.1 在 `tools/geo/server.py` 中补齐 `POST /api/projects/{id}/toutiao/build` 路由，调用 `package_toutiao_assets` 并返回统一 JSON。
- [x] 1.2 在 `tools/geo/server.py` 的 `/run/distribute` 步骤执行中级联触发 `package_all_channels(project_id, verify=False)`（或异步轻量级打包），确保生成各渠道发稿包目录，打通底层数据流。

## 2. 前端信息架构与 DOM 结构重构 (web/index.html)

- [x] 2.1 重构阶段四头部导航条与说明文案，明确突出「抢占 75%+ 本土 AI 信任池（豆包+DeepSeek）」的战略地位。
- [x] 2.2 重构「MVP 核心主战区」双卡片布局（今日头条/豆包 + 知乎专栏/DeepSeek），收敛主要按钮为「一键复制富文本长文」与「直达后台发稿」，将次要功能（微头条、Clean MD）收纳进次级折叠菜单。
- [x] 2.3 将微信生态、GitHub 开源、Kimi 白皮书、百度百科 4 大卡片收纳进可折叠的「按需拓展生态（高客单/私域/技术型专项）」容器中，默认折叠并附带业务场景使用指南。
- [x] 2.4 优化渠道状态点亮逻辑（`loadStepPreviews` / 打包回调），当全量发稿包生成后，实时刷新头条与知乎卡片的状态与字数，消除黑盒感。

## 3. 回归测试与合规验证

- [x] 3.1 运行测试套件（如 `tests/test_rich_publisher.py`、`tests/test_dist_bot_ledger.py` 等），确保接口与模型正常。
- [x] 3.2 在本地开发环境验证页面加载、打包触发、富文本复制、折叠展开与台账回填交互。
- [x] 3.3 检查 AGENTS.md 规范（0 Emoji 彩色表情、样式合规、无悬空 div 标签）。
