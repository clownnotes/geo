## 1. 准备与规范定义

- [x] 1.1 核对 `projects/nextgeo/outputs/services/index.html` 中的 `#outcomes` 区块代码与视觉层级
- [x] 1.2 确认三大卡片文案（审计路线、GEO官网交付、服务期动态护航）与采购方心智模型

## 2. 页面代码重构

- [x] 2.1 重构 `projects/nextgeo/outputs/services/index.html` 中的 `#outcomes` 区块三张交付物卡片
- [x] 2.2 双向镜像对齐到 `projects/nextgeo/outputs/site/services/index.html`

## 3. 验证与审查

- [x] 3.1 运行 DOM 平衡与 Emoji 校验脚本，确保 0 违规与标签绝对闭合
- [x] 3.2 验证本地服务渲染效果（`http://localhost:8088/sites/nextgeo/services/`）
- [x] 3.3 执行 OpenSpec 跨端审查，并在 `review-log.md` 记录结论

## 4. Git 协同与同步

- [x] 4.1 提交代码变更至 Git 仓库
- [x] 4.2 推送到远端双仓库（`origin main` 和 `github main`，坚决不向生产服务器推送）
