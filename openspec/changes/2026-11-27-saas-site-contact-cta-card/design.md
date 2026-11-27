# Design：统一 SaaS 官网母版补齐紫色联系卡片、微信二维码与页脚联系人

## Context

详见 `proposal.md` 的 Why 部分。当前 `templates/baicl-saas/index.html.tmpl` 与 `src/tools/geo/scaffold.py` 已实现极简母版和 LOGO 安全留白，需在此基础上补齐 `www.baicl.cc` 风格的紫色渐变 CTA 联系卡片与页脚「联系{联系人}」快捷锚点。

---

## 用户核心原话与 AI 技术决定 1 对 1 映射推导链条表

| 序号 | 用户核心原话（第一真理源） | AI 理解与技术决定 | 对应落地点 |
|---|---|---|---|
| 1 | “是不是还应该有，上传微信二维码，联系人，联系电话这几个？” | 扩展 `scaffold.py` 与 `handlers.py` 支持 `contact_person`、`telephone`、`wechat`、`wechat_qr_file` 参数，复用 `realpath` + 图片后缀白名单安全复制二维码至 `outputs/site/assets/` | `src/tools/geo/scaffold.py`、`src/tools/worker/handlers.py` |
| 2 | 附 `www.baicl.cc` 紫色渐变联系卡与页脚「联系老白 · llms.txt · sitemap.xml」截图 | 在母版新增 `<!-- SAAS_SECTION:CTA -->`（`{{CTA_SECTION_HTML}}`）复刻紫色渐变 CTA 卡片，页脚右侧新增 `{{FOOTER_CONTACT_LINK_HTML}}` | `templates/baicl-saas/index.html.tmpl` |
| 3 | 延续“没资料就留白”的极简原则 | 无二维码时不渲染二维码 `<img>`；联系人/电话/微信/二维码全空时整块隐藏 CTA 卡片与页脚联系链接，0 假数据、0 Emoji | `src/tools/geo/scaffold.py` |

---

## Goals / Non-Goals

**Goals:**
- 在母版内联防御性 CSS 中完整实现紫色 CTA 卡片的桌面端双栏与移动端单栏自适应布局。
- 复用一套统一的图片安全复制函数同时服务 LOGO 与微信二维码（减少重复代码，单函数 <= 50 行）。
- 同步更新 `docs/specs/saas-site-master-guide.md` 与 `tests/test_saas_turnkey_site.py`。

**Non-Goals:**
- 不改变已有 18 个占位符名称，仅增量新增 `{{CTA_SECTION_HTML}}` 与 `{{FOOTER_CONTACT_LINK_HTML}}`。
- 不破坏 `custom_site: true` 防覆盖锁。

---

## Decisions

### 决策 1：模板新增 2 个占位符与 1 组锚点
- 锚点：`<!-- SAAS_SECTION:CTA -->` ... `<!-- /SAAS_SECTION:CTA -->`（位于 FAQ 与 FOOTER 之间）。
- 占位符：
  - `{{CTA_SECTION_HTML}}`：有联系人/电话/微信/二维码任一项时渲染 `<section id="contact-cta" class="saas-cta-wrap">...</section>`；全空时传 `""`。
  - `{{FOOTER_CONTACT_LINK_HTML}}`：有联系人或电话时渲染 `<a href="#contact-cta">联系{联系人或我们}</a> · `；全空时传 `""`。

### 决策 2：抽公共图片安全复制函数 `_resolve_safe_image_asset`
- 将原有 `_resolve_safe_logo` 抽象为通用安全图片解析与复制函数 `_resolve_safe_image_asset(project_id, site_dir, raw_path, target_stem)`，LOGO 使用 `target_stem="logo"`，微信二维码使用 `target_stem="wechat-qr"`，统一执行 `realpath` 目录边界校验与 `.png/.jpg/.jpeg/.webp/.svg` 白名单拦截。

---

## Risks / Trade-offs

- **[Risk] 二维码图片在深紫背景上对比度不足导致无法扫码** → Mitigation：为二维码外层强制包裹纯白圆角底框（`background: #ffffff; padding: 12px; border-radius: 16px;`），与 `www.baicl.cc` 截图视觉一致，确保微信 100% 秒扫。
