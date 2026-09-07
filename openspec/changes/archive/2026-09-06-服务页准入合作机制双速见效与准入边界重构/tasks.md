## 1. 准备与规范定义

- [x] 1.1 核对 `projects/nextgeo/outputs/services/index.html` 中的 `#fit` 板块代码与视觉布局
- [x] 1.2 确认 4 张卡片的文案与双速见效（14天敏捷 vs 180天壁垒）及双向准入结构

## 2. 页面代码重构

- [x] 2.1 重构 `projects/nextgeo/outputs/services/index.html` 中的 `#fit` 区块主副标题与 4 张核心卡片
- [x] 2.2 双向镜像对齐到 `projects/nextgeo/outputs/site/services/index.html`

## 3. 验证与审查

- [x] 3.1 运行 DOM 平衡与 Emoji 校验脚本，确保 0 违规与容器标签绝对闭合
- [x] 3.2 验证本地服务渲染效果（`http://localhost:8088/sites/nextgeo/services/#fit`）
- [x] 3.3 执行 OpenSpec 跨端审查，并在 `review-log.md` 记录结论

## 4. Git 协同与同步

- [x] 4.1 提交代码变更至 Git 仓库
- [x] 4.2 推送到远端双仓库（`origin main` 和 `github main`，坚决不向生产服务器推送）
