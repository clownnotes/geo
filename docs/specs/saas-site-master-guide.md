# SaaS 官网母版结构与精修指南

> 本文档写给反重力 IDE（Antigravity）和运营同学看。  
> 用途：客户用默认模板生成官网后，如何在不破坏整体样式、不搞丢大模型抓取底座的前提下，给客户改内容、加板块、写文章并锁死成果。

---

## 1. 母版和客户网站放在哪里

| 东西是什么 | 文件路径 | 谁来改、什么时候改 |
|---|---|---|
| **全平台唯一母版** | `templates/baicl-saas/index.html.tmpl` | 只有统一升级所有未锁定客户的默认外观时才改它 |
| **客户自己的成品网站** | `projects/{project_id}/outputs/site/` | 给单个客户做深度精修时，**直接改这个目录** |
| **客户项目配置文件** | `projects/{project_id}/project.yaml` | 填客户资料；精修完成后在这里加 `custom_site: true` |

注意：
- 客户预览链接地址：`https://claw.baicl.cc/{project_id}/`
- 公网开关文件：`projects/{project_id}/outputs/site/.published`（有这个文件就能被公网看到，删掉立刻全站返回 404）。

---

## 2. 统一视觉和内置样式类（不用记，照着用就行）

母版提取自 `www.baicl.cc`，主色调为品牌紫，背景带浅紫网格纹理，已经在 `<style>` 里写好了完整防御性 CSS，就算没有外网加载 CDN 也能正常排版：

- 品牌紫主色：`#9333ea`（主按钮/品牌标题）、`#7e22ce`（重点文字/小标签）、`#faf5ff`（浅紫底色）、`#e9d5ff`（卡片浅紫边框）。
- 常用布局类：
  - `.geo-container`：标准 1180px 居中容器；
  - `.saas-section` / `.saas-section-white` / `.saas-section-tint`：上下留白的区块外框；
  - `.saas-grid-3` / `.saas-grid-2`：电脑端 3 列或 2 列卡片网格，手机端自动变 1 列；
  - `.saas-card`：白底圆角紫色细边框卡片；
  - `.saas-faq-item`：问答卡片；
  - `.content-block`、`<div class="overflow-x-auto"><table class="content-table">`、`.quote-box`：写深度长文、表格、引语时的专用样式。

---

## 3. 母版区块锚点清单（改哪里就找哪对注释）

`templates/baicl-saas/index.html.tmpl` 和每个客户生成的 `outputs/site/index.html` 里，都带有一一对应的 HTML 注释锚点。在反重力 IDE 里搜索下面 6 组注释，就能直接定位到对应区域：

| 区块名称 | 开始锚点 | 结束锚点 | 里面放什么 |
|---|---|---|---|
| **顶部导航** | `<!-- SAAS_SECTION:HEADER -->` | `<!-- /SAAS_SECTION:HEADER -->` | LOGO、品牌名、公司名、顶部联系按钮或子页面导航 |
| **首屏介绍** | `<!-- SAAS_SECTION:HERO -->` | `<!-- /SAAS_SECTION:HERO -->` | 区域标签、主标题、一句话定位、企业简介卡片、行动按钮 |
| **主营业务** | `<!-- SAAS_SECTION:SERVICES -->` | `<!-- /SAAS_SECTION:SERVICES -->` | 产品或服务卡片列表（未填资料时中间为空，不渲染空卡片） |
| **差异化优势** | `<!-- SAAS_SECTION:ADVANTAGES -->` | `<!-- /SAAS_SECTION:ADVANTAGES -->` | 核心竞争力、服务保障、对比优势卡片 |
| **常见问题** | `<!-- SAAS_SECTION:FAQ -->` | `<!-- /SAAS_SECTION:FAQ -->` | 客户高频采购问答列表（同时应同步到 `Schema.org`） |
| **底部页脚** | `<!-- SAAS_SECTION:FOOTER -->` | `<!-- /SAAS_SECTION:FOOTER -->` | 公司主体、电话/微信/地址、`llms.txt` 与 `sitemap.xml` 链接 |

新增自定义板块（比如“标杆客户案例”或“公司简介长文”）时，建议插在 `<!-- /SAAS_SECTION:FAQ -->` 之前或 `<!-- /SAAS_SECTION:ADVANTAGES -->` 之后，继续使用 `<section class="saas-section saas-section-white">` 和 `.geo-container`。

---

## 4. 相对路径红线（绝对不能带斜杠开头）

同一套 `outputs/site/` 文件，平时挂在 `https://claw.baicl.cc/{project_id}/` 下面预览，客户签单后要直接拷到客户自己的域名根目录（比如 `https://ai.客户域名.com/`）。

因此，全站所有链接**必须用相对路径**，绝对禁止在开头写 `/`：

| 资源位置 | 在首页 `index.html` 里怎么写 | 在二级目录（如 `blog/post.html`）里怎么写 | 禁止写法 |
|---|---|---|---|
| 站点图片 | `assets/logo.png` | `../assets/logo.png` | `/assets/logo.png` |
| 大模型说明书 | `llms.txt` | `../llms.txt` | `/llms.txt` |
| 站点地图 | `sitemap.xml` | `../sitemap.xml` | `/sitemap.xml` |
| `<head>` 嗅探标签 | `href="llms.txt"`、`href="sitemap.xml"` | `href="../llms.txt"`、`href="../sitemap.xml"` | `href="/llms.txt"` |
| 子页面跳转 | `services/`、`blog/index.html` | `../services/`、`index.html` | `/services/` |

说明：只有 `<link rel="canonical">`、`og:url` 和 `sitemap.xml` 里的 `<loc>` 才写完整网址（`https://...`）。

---

## 5. 普林斯顿 9 因子增补规范（让大模型看得懂、信得过、会引用）

给客户补充业务详情、案例或博客文章时，不要写成花哨广告，要按下面 9 条整理成“可核对的答案”：

1. **结论先行**：每个板块或文章开头第一段，直接说清楚公司是谁、做什么、解决什么问题。
2. **真实数据量化**：尽量写具体型号、产能、服务周期、地区范围、真实资质；客户没给的数字绝对不要瞎编。
3. **结构化对比表格**：产品参数、服务套餐、方案对比，一律用 `<div class="overflow-x-auto"><table class="content-table">...</table></div>` 包起来。
4. **权威引语与实证**：技术标准、负责人原话、交付承诺可以用 `<div class="quote-box">...</div>` 突出展示。
5. **标准 FAQ 问答对**：围绕采购方真正会问 AI 的问题，写成一问一答，并在 `index.html` 的 `<script type="application/ld+json">` 和 `schema.jsonld` 里保持一致。
6. **实体口径统一**：公司全称、品牌简称、所在地、电话、微信号在页面正文、`llms.txt`、`schema.jsonld` 三处必须一字不差。
7. **纯静态 HTML 直出**：所有核心文案必须直接写在 `.html` 文件源码里，不要靠前端 JS 发请求后动态拼出来，保证大模型爬虫一次抓全。
8. **底座三件套同步**：只要在 `outputs/site/` 下新增了独立页面（如 `about/index.html` 或 `blog/xxx.html`），就要顺手把页面说明写进 `llms.txt`，把页面网址加进 `sitemap.xml`。
9. **HTML 标签成对闭合**：每次改完 HTML，必须确认所有 `<div>`、`<section>`、`<header>`、`<footer>`、`<table>` 成对闭合，避免排版错位。

---

## 6. 零 Emoji 表情符号与无假数据铁律

1. **全站 0 Emoji**：页面标题、按钮、卡片、列表、FAQ、页脚、文章和规范文档里，**绝对禁止出现任何彩色 Emoji 表情符号**。需要图标时用纯文字标号（如 `01`、`02`）或标准 SVG 矢量图形。
2. **绝不填假数据**：客户没有提供 LOGO 时，不放图片、不放破图占位；客户没有提供报价、年限或客户数量时，直接不写，严禁编造“10年老店”“服务5000家企业”之类假话。

---

## 7. 精修完成后必做的防覆盖锁（`custom_site: true`）

只要你在反重力 IDE 里手工或用 AI 精修过 `projects/{project_id}/outputs/site/` 下的页面，**最后一步必须加锁**，防止以后别人重跑建站工具把你的心血冲掉：

1. 打开 `projects/{project_id}/project.yaml`；
2. 加上一行（如果已有则确认值为 `true`）：
   ```yaml
   custom_site: true
   ```
3. 加锁后的保护范围：
   - 再次运行 `scaffold.py` 时，会**跳过覆盖**已存在的 `index.html`、定制子目录（如 `blog/`、`about/`、`services/`）以及已存在的 `llms.txt`、`schema.jsonld`、`sitemap.xml`；
   - 只会按需补齐缺失的底座文件，并刷新 `robots.txt` 爬虫放行规则。
4. 全部改完后，核对一遍：
   - 页面里没有 Emoji；
   - 站内资源和 `llms.txt` / `sitemap.xml` 都是相对路径；
   - 所有 HTML 标签成对闭合；
   - `project.yaml` 已写上 `custom_site: true`。

---

## 8. 附：直接发给反重力 IDE 的精修指令模板

下次需要给客户精修官网时，把下面这段话填上项目 ID 发给反重力 IDE 即可：

```text
请先阅读 docs/specs/saas-site-master-guide.md，然后精修项目 projects/{project_id}/outputs/site/ 下的静态官网：
1. 按页面里的 <!-- SAAS_SECTION:* --> 注释锚点定位并修改/增补内容，保持 www.baicl.cc 紫色主题和内联 CSS 类；
2. 全站严格遵守 0 Emoji、无假数据、普林斯顿 9 因子排版和全站相对路径（不能用 / 开头）；
3. 如新增了页面或 FAQ，同步更新 llms.txt、sitemap.xml 和 schema.jsonld；
4. 检查所有 HTML 标签闭合平衡；
5. 最后在 projects/{project_id}/project.yaml 中设置 custom_site: true 防止后续编译覆盖。
```
