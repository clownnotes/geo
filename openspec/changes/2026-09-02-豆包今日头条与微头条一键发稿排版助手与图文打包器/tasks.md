## 1. 编写头条发稿排版与图文打包引擎核心 (`tools/geo/publisher.py`)

- [x] 1.1 实现 `build_toutiao_article_html(project_id)`，将 9 因子语料转换为头条后台兼容的精美富文本 HTML。
- [x] 1.2 实现 `build_toutiao_micro_post(project_id)`，生成决策篇、价格篇、避坑篇 3 组 150 字微头条强观点文案。
- [x] 1.3 实现 `package_toutiao_assets(project_id)`，将富文本 HTML、微头条短动态与 SEO 自检清单打包至 `outputs/toutiao_pack/`。

## 2. CLI 与 Web 服务端集成 (`tools/geo/cli.py` & `server.py`)

- [x] 2.1 在 `tools/geo/cli.py` 中新增 `geo publish` 子命令，支持一键导出头条图文发稿包。
- [x] 2.2 在 `tools/geo/server.py` 中新增 `/api/projects/{id}/toutiao/preview` 与一键复制富文本接口。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 针对 `xuzhou_xuanyuan` 与 3 大行业母版运行 `geo publish`，验证富文本渲染与打包无报错。
- [x] 3.2 严格遵守项目规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录审查结论。

