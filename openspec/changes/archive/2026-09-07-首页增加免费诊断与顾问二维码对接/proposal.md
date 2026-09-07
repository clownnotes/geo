# Proposal: 首页增加免费诊断与顾问二维码对接

## Why (为什么做)
1. **转化漏斗痛点**：当前 NextGEO 官方首页（`nextgeo.baicl.cc`）首屏 Hero 区域仅提供两个常规跳转链接——“查看 NextGEO 服务”（跳转至 `services/`）和“了解 邻里GEO”（跳转至 `about/`）。B2B 决策者在首屏浏览后，缺少一个低摩擦、直观且具备明确价值回报的即时线索入口。
2. **对标行业高转化标准**：参考头部 GEO 平台（如必火 GEO `https://www.bihuogeo.com/#contact`），其核心转化战略以“免费诊断”（先诊断、再优化、扫码添加专属顾问）贯穿首屏与全局，能让意向企业主在 10 秒内产生主动咨询意向。
3. **真实沟通物料到位**：用户已提供最新的官方微信二维码素材（`/Users/a1/Pictures/我的公司和个人证明资料/GEO 微信账号的二维码.jpg`）。此前站点 `services/#contact` 部分暂以头像 `logo.jpg` 替代二维码，亟需将正式二维码资产纳入项目，打通全渠道微信触达与咨询闭环。

## What Changes (改动了什么)
1. **静态资产规范引入**：
   - 将用户提供的二维码源文件复制至 `projects/nextgeo/outputs/assets/wechat-qr.jpg`；
   - 保持与 `projects/nextgeo/outputs/site/assets/wechat-qr.jpg` 的双向镜像对齐。
2. **首页首屏 Hero 动作按钮扩展**：
   - 在 `projects/nextgeo/outputs/index.html` 首屏按钮组中，于“了解 邻里GEO”旁新增醒目的「免费诊断」CTA 按钮；
   - 按钮视觉采用高辨识度的品牌紫框或高质感微渐变设计，遵循 0 Emoji 规范，与现有按钮形成主次分明、高专业度的视觉梯队。
3. **轻量极速交互（无缝诊断弹窗 + 静态兜底）**：
   - 点击“免费诊断”按钮在当前页直接调出原生轻量「企业 GEO 免费诊断与 AI 可见度体检」弹窗（Modal），减少页面跳失；
   - 弹窗内展示清晰的免费诊断三大维度（大模型品牌提及现状推演、行业高意向问法缺口排查、官网知识底座规范评测）、真实微信二维码、一键拨打电话（13150568888）与微信添加提示；
   - 支持点击遮罩关闭、右上角 SVG 叉号关闭及 Esc 键盘响应；
   - 无 JS 或右键新窗口打开场景下默认回退跳转至 `services/#contact` 兜底。
4. **服务页与全站联动物料修正**：
   - 同步修正 `projects/nextgeo/outputs/services/index.html` 中 `#contact` 板块内的二维码图片，由旧的 `logo.jpg` 替换为新引入的 `wechat-qr.jpg`，确保全站咨询物料严谨一致。

## Capabilities (新增或修改的对外能力)
- **直接商机捕获能力**：首页首屏具备即时扫码/拨号能力，大幅缩短 B2B 客户从认知到咨询的转化链路。
- **顾问式诊断体验**：通过明确的“先诊断、再优化”承诺，降低客户对 GEO 商业服务的理解门槛与决策疑虑。
- **全站一致的微信触点**：全站所有指向微信二维码的场景均统一使用高清真实顾问二维码。

## Impact (受影响的部分)
- **受影响文件**：
  - `projects/nextgeo/outputs/assets/wechat-qr.jpg`（新增）
  - `projects/nextgeo/outputs/site/assets/wechat-qr.jpg`（新增镜像）
  - `projects/nextgeo/outputs/index.html`（修改）
  - `projects/nextgeo/outputs/site/index.html`（修改镜像）
  - `projects/nextgeo/outputs/services/index.html`（修改）
  - `projects/nextgeo/outputs/site/services/index.html`（修改镜像）
- **依赖与规范合规**：
  - 零外部运行时依赖（纯原生 HTML/CSS/Tailwind + 极简原生 JS）；
  - 100% 遵循 `AGENTS.md` 规范：0 Emoji、DOM 标签完全平衡配对、严格时间与镜像对齐。
