# Proposal：统一 SaaS 官网母版补齐紫色联系卡片、微信二维码与页脚联系人

## 用户核心原话实录（第一真理源）

> “是不是还应该有，上传微信二维码，联系人，联系电话这几个？否则只是个 LOGO 很多私人信息都没有展示的地方。你看那？”（并附 `www.baicl.cc` 紫色 CTA 联系卡片与页脚「联系老白 · llms.txt · sitemap.xml」截图）
>
> “/openspec-propose 可以做方案吧。”

---

## Why

第一版 `templates/baicl-saas/index.html.tmpl` 统一母版只支持 LOGO 与基础联系文字，缺少 `www.baicl.cc` 官网转化率最高的紫色 CTA 联系卡片（含联系人、一键拨打咨询电话按钮、右侧微信二维码图片与微信号提示）以及页脚右侧的「联系{联系人}」入口。补齐该能力后，企业官网既能完整承接高转化留资，又继续保持“缺什么就留白什么”的极简真实原则。

---

## What Changes

- **统一母版升级（`templates/baicl-saas/index.html.tmpl`）**：
  - 在 `<!-- SAAS_SECTION:FAQ -->` 与 `<!-- SAAS_SECTION:FOOTER -->` 之间新增 `<!-- SAAS_SECTION:CTA -->` 区块与 `{{CTA_SECTION_HTML}}` 占位符，内联复刻 `www.baicl.cc` 紫色渐变 CTA 联系卡片样式（支持移动端自适应、0 Emoji、不依赖外部 CDN）；
  - 在页脚右侧 `llms.txt · sitemap.xml` 左侧新增 `{{FOOTER_CONTACT_LINK_HTML}}` 占位符，有联系人或电话时展示「联系{联系人}」跳转 `#contact-cta`。
- **后厂编译与微信二维码安全校验（`src/tools/geo/scaffold.py` & `src/tools/worker/handlers.py`）**：
  - `PROFILE_KEYS` 新增 `contact_person`、`wechat_qr_file` / `wechat_qr`；
  - `scaffold.py` 复用与 LOGO 同等严格的 `os.path.realpath` 路径白名单与图片后缀白名单（`.png/.jpg/.jpeg/.webp/.svg`）复制微信二维码至 `outputs/site/assets/wechat-qr.<ext>`；
  - 严格留白规则：联系人/电话/微信二维码全无时不渲染 CTA 区块；有联系人或电话但无二维码时不渲染二维码空框；同步将联系人与电话写入 `llms.txt` 与 `schema.jsonld`。
- **IDE 精修文档同步（`docs/specs/saas-site-master-guide.md`）**：补充 `SAAS_SECTION:CTA` 区块锚点、紫色联系卡片内置样式类及二维码资产路径说明。

---

## Capabilities

### New Capabilities
<!-- 无新建顶级能力，直接扩展既有 saas-turnkey-site 契约。 -->

### Modified Capabilities
- `saas-turnkey-site`: 新增紫色 CTA 联系卡片、微信二维码路径白名单安全复制、页脚联系人快捷入口及对应的缺省留白规则。

---

## Impact

- 修改：`templates/baicl-saas/index.html.tmpl`、`src/tools/geo/scaffold.py`、`src/tools/worker/handlers.py`、`docs/specs/saas-site-master-guide.md`、`tests/test_saas_turnkey_site.py`
- 仍严格遵守前店后厂红线（无 MySQL、无管理台页面、0 Emoji、`custom_site: true` 防覆盖不变）。
