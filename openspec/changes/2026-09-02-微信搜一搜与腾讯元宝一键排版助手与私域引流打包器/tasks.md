## 1. 编写微信内联富文本排版与视频号脚本引擎核心 (`tools/geo/publisher.py`)

- [x] 1.1 实现 `build_wechat_article_html(project_id)`，生成 100% 纯内联 CSS、兼容微信公众号后台的精美富文本 HTML。
- [x] 1.2 实现 `build_wechat_video_script(project_id)`，生成 60 秒竖屏视频号口播脚本与 3 组爆款封面。
- [x] 1.3 实现 `package_wechat_assets(project_id)`，将长文 HTML、视频号 Markdown 与搜一搜发稿指南打包至 `outputs/wechat_pack/`。

## 2. CLI 与 Web 服务端集成 (`tools/geo/cli.py` & `server.py`)

- [x] 2.1 在 `tools/geo/cli.py` 的 `publish` 子命令中支持 `--channel wechat` 与 `--channel all`。
- [x] 2.2 在 `tools/geo/server.py` 中增加 `/api/projects/{id}/wechat/preview` 与 `/api/projects/{id}/wechat/video` 路由。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 针对 `xuzhou_xuanyuan` 与 3 大行业母版运行 `geo publish --channel wechat`，验证内联样式保真度与脚本落盘完整。
- [x] 3.2 严格遵守项目规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录审查结论。

