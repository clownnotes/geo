# saas-turnkey-site Delta Specification

## ADDED Requirements

### Requirement: 紫色 CTA 联系卡片、微信二维码安全校验与页脚联系人留白渲染
建站编译引擎 SHALL 支持通过 `contact_person`、`telephone`、`wechat` 与 `wechat_qr_file`（或 `wechat_qr`）在统一母版 `<!-- SAAS_SECTION:CTA -->` 区域渲染 `www.baicl.cc` 同款紫色渐变联系卡片，并在页脚右侧渲染「联系{联系人}」快捷入口。微信二维码源文件路径 MUST 与 LOGO 遵循同等安全校验（经 `realpath` 限定在项目 `raw_materials/` 或 `outputs/site/assets/` 内且为 `.png/.jpg/.jpeg/.webp/.svg` 图片后缀），越界或非法后缀 MUST 拒绝复制并按无二维码安全留白；当联系人、电话与微信二维码全部为空时，系统 MUST 隐藏整个 CTA 卡片与页脚联系人链接。

#### Scenario: 联系人、电话与微信二维码齐全时渲染完整紫色联系卡
- **WHEN** 客户项目提供了 `contact_person`、`telephone`、`wechat` 及合法的 `wechat_qr_file` 并触发建站编译
- **THEN** 系统将二维码安全复制至 `outputs/site/assets/`，`index.html` 渲染完整紫色联系卡（含联系人标题、直连电话、相对路径二维码 `<img>` 与一键拨打按钮），且页脚右侧展示指向 `#contact-cta` 的「联系{联系人}」链接

#### Scenario: 仅提供联系人或电话、未提供微信二维码时留白二维码区
- **WHEN** 客户项目提供了 `contact_person` 或 `telephone`，但未提供 `wechat_qr_file`（或提供了越界/非法后缀路径）
- **THEN** 系统不复制非法文件，紫色联系卡正常展示文字与拨号按钮，且卡片右侧 MUST NOT 渲染二维码 `<img>` 或占位空框

#### Scenario: 联系人、电话与微信二维码全空时整块隐藏 CTA
- **WHEN** 客户项目未提供 `contact_person`、`telephone`、`wechat` 与 `wechat_qr_file`
- **THEN** 编译输出的 `index.html` 中 `<!-- SAAS_SECTION:CTA -->` 区域为空白（不输出 `<section id="contact-cta">`），页脚仅保留 `llms.txt` 与 `sitemap.xml`
