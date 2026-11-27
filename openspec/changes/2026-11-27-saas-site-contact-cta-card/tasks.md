# Tasks：统一 SaaS 官网母版补齐紫色联系卡片、微信二维码与页脚联系人

## 1. 统一母版与精修规范升级

- [x] 1.1 更新 `templates/baicl-saas/index.html.tmpl`，新增 `<!-- SAAS_SECTION:CTA -->` 区块与 `{{CTA_SECTION_HTML}}`、`{{FOOTER_CONTACT_LINK_HTML}}` 占位符及紫色渐变 CTA 卡片内联防御性 CSS（含纯白二维码底框与移动端自适应，0 Emoji，相对路径），同步更新 `docs/specs/saas-site-master-guide.md` 补录 CTA 锚点与二维码说明，验证 HTML 标签闭合与 0 Emoji。

## 2. 后厂编译引擎、Worker 通道与单测补齐

- [x] 2.1 更新 `src/tools/geo/scaffold.py` 与 `src/tools/worker/handlers.py`：`PROFILE_KEYS` 补齐 `contact_person`、`wechat_qr_file`、`wechat_qr`；抽象 `_resolve_safe_image_asset` 统一校验并复制 LOGO 与微信二维码至 `outputs/site/assets/`；实现紫色 CTA 卡片与页脚联系人按需留白渲染（全函数 <= 50 行，0 Emoji）。
- [x] 2.2 在 `tests/test_saas_turnkey_site.py` 新增 3 类场景单测（完整联系人+电话+合法二维码渲染、仅电话无二维码/越界二维码安全拒绝留白、全空隐藏 CTA 卡片），并跑通全套 `pytest` 回归确认 100% 通过。
