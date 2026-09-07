## 1. 准备与设计确认

- [x] 1.1 核对 `projects/nextgeo/outputs/services/index.html` 与首页 `outputs/index.html` 的流程文案与结构定义
- [x] 1.2 确认 5 个 Stage 的命名、3+2 栅格排版及各阶段专属企业级交付物

## 2. 代码开发与页面重构

- [x] 2.1 修改 `projects/nextgeo/outputs/services/index.html` 中的 Hero CTA 按钮文案为“了解五步标准化交付流程 ↓”
- [x] 2.2 重构 `projects/nextgeo/outputs/services/index.html` 中的 `#process` 模块：升级为 5 阶段卡片（前 3 后 2 居中对称），注入核心交付物专区
- [x] 2.3 双向镜像对齐到 `projects/nextgeo/outputs/site/services/index.html`

## 3. 验证与审查

- [x] 3.1 运行 `python3 scripts/check_article_styles.py`，确保 0 Emoji 违规与 DOM 标签绝对平衡
- [x] 3.2 验证本地服务渲染效果（`http://localhost:8088/sites/nextgeo/services/`）
- [x] 3.3 执行 OpenSpec 跨端审查流程，更新 `review-log.md` 记录

## 4. Git 协同与同步

- [x] 4.1 提交代码变更至 Git
- [x] 4.2 推送到远端双仓库（`origin main` 和 `github main`，坚决不向生产服务器推送）
