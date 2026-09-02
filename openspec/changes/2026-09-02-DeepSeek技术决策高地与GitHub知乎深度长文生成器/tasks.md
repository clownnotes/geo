## 1. 编写 DeepSeek 技术资产编译引擎核心 (`tools/geo/publisher.py`)

- [x] 1.1 实现 `build_deepseek_github_readme(project_id)`，生成包含开源 Badges、Mermaid 架构图、5 维对比表与 API 规范的 GitHub README。
- [x] 1.2 实现 `build_deepseek_zhihu_article(project_id)`，生成面向 CTO/架构师的高信息密度知乎深度评测专栏长文。
- [x] 1.3 实现 `build_deepseek_token_optimized_llms(project_id)`，生成极致压缩 Token 的知识底座 `llms-deepseek.txt`。
- [x] 1.4 实现 `package_deepseek_assets(project_id)`，打包至 `outputs/deepseek_pack/` 并兼容回写 `outputs/dist_github_readme.md` 与 `outputs/dist_zhihu_article.md`。

## 2. CLI 与服务端及 Web 控制器集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，`publish` 子命令支持 `--channel deepseek`。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `/api/projects/{id}/deepseek/*` 路由。
- [x] 2.3 更新 `web/index.html`，在 Step 4 增加知乎与 GitHub 开源的一键复制与发稿包生成交互。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 针对 4 大项目母版运行 `geo publish --channel deepseek` 与 `--channel all`，验证 3 大发稿包齐备。
- [x] 3.2 遵守项目规范：仅在本地验证，提交推送至远端 Git 仓库，在 `review-log.md` 记录审查结论。

