## 1. 编写商业结案证书生成引擎核心 (`tools/geo/certificate.py`)

- [x] 1.1 实现 `build_delivery_certificate_html(project_id)`，生成符合 A4 纸张公文排版、防伪水印与双签章栏的 HTML。
- [x] 1.2 自动计算交付文件的 SHA256 数字指纹，生成资产移交明细清单。
- [x] 1.3 输出 `09_GEO全案商业交付结案与数字资产移交证书.html`。

## 2. CLI 与 Web 服务端集成 (`tools/geo/cli.py` & `server.py` & `web/`)

- [x] 2.1 在 `tools/geo/cli.py` 中新增 `geo certificate` 子命令。
- [x] 2.2 在 `tools/geo/server.py` 中新增 `/api/projects/{id}/certificate` 与 `/api/share/{token}/certificate`。
- [x] 2.3 在 `web/index.html` 与 `web/share.html` 中提供一键打印/查看证书按钮。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 运行 `geo certificate xuzhou_xuanyuan` 与 3 大母版项目，验证 HTML 渲染与 SHA256 哈希计算正确。
- [x] 3.2 严格遵守项目规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录审查结论。

