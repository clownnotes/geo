## 1. 准备与物料引入

- [x] 1.1 读取并校验源二维码 `/Users/a1/Pictures/我的公司和个人证明资料/GEO 微信账号的二维码.jpg`，复制至 `projects/nextgeo/outputs/assets/wechat-qr.jpg`
- [x] 1.2 同步复制该图片至生产镜像目录 `projects/nextgeo/outputs/site/assets/wechat-qr.jpg`

## 2. 代码开发与页面集成

- [x] 2.1 修改 `projects/nextgeo/outputs/index.html`，在 Hero 区域动作按钮组（“了解 邻里GEO”旁）添加“免费诊断”CTA 按钮
- [x] 2.2 在 `projects/nextgeo/outputs/index.html` 注入「免费 GEO 诊断与 AI 可见度体检」模态弹窗及极简原生交互脚本（支持遮罩关闭、Esc 响应与兜底跳转，100% 0 Emoji）
- [x] 2.3 修改 `projects/nextgeo/outputs/services/index.html`，将 `#contact` 板块内的老白二维码图片替换为 `wechat-qr.jpg`
- [x] 2.4 将改动严格对齐同步至 `projects/nextgeo/outputs/site/index.html` 与 `projects/nextgeo/outputs/site/services/index.html` 镜像

## 3. 验证与测试

- [x] 3.1 运行 `python3 scripts/check_article_styles.py` 自动化检测脚本，核验 0 Emoji 违规与 DOM 闭合平衡
- [x] 3.2 在本地开发环境验证桌面端与移动端弹窗视觉、二维码扫码可用性与交互顺畅度
- [x] 3.3 汇报进展并严格停步等待用户验收

