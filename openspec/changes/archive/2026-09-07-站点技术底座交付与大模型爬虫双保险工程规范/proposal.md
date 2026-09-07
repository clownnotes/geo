# Proposal: 站点技术底座交付与大模型爬虫双保险工程规范

## 1. 核心指导思想 (Why)

> **最高准则**：一切以大模型（DeepSeek、豆包、ChatGPT、Kimi、元宝、通义等）与真实企业访客能够 100% 毫秒级抓取、无障碍渲染、准确理解并首选推荐为唯一导向。

### 现状与核心痛点：
1. **静态官网多租户托管 URL 尾部斜杠缺失导致相对路径崩盘**：
   - 静态站点依赖相对路径加载资源（如 `assets/logo.jpg`、`blog/` 等）；
   - 若服务器在用户访问 `/sites/{project_id}` 时未执行 301 强制重定向至 `/sites/{project_id}/`，浏览器 Base URL 会错位退至 `/sites/`，导致页面静态资源全部 404，样式与图片散架；
   - 该 301 规则虽已在 `fb0928e` 中实现，但缺乏自动化测试守护与全局工程规范约束。
2. **大模型爬虫抓取缺少三重冗余（Triple Redundancy）机制**：
   - 传统建站仅在根目录放置 `llms.txt` 或仅在页脚放置普通链接；
   - 轻量级 RAG 代理抓取深度有限，普通爬虫难以自动发现非标路径；
   - 必须建立“**根目录标准直达 + HTML `<head>` 双保险标准嗅探标签 + 页面 DOM 显式内链**”的三重绝对冗余抓取保障体系。
3. **大模型首屏单次抓取建图率不足与页面类型 Schema 割裂**：
   - 多数企业官网首页仅有浅层的 `Organization`，缺少 `LocalBusiness` 本地商业拓扑与决策最关心的 `FAQPage` 问答对；
   - 同时不同页面（首页、列表页、正文单页、服务页）对于 Schema.org 的需求各异，此前缺少统一的「页面类型合规矩阵」。
4. **前端样式过度裸奔依赖外部 Play CDN 的脆弱性**：
   - 国内弱网、无翻墙或离线环境下，一旦外部 CDN（如 `cdn.tailwindcss.com`）连接超时或被 Safari 隐私插件拦截，页面将瞬间退化为不可读的原始裸 HTML；
   - 必须规范“防御性内联 CSS 兜底（CSS Resilience Standard）”，即便外部 CDN 失效，页面也必须保持弹性容器约束、自适应图片和基础字阶。
5. **脚手架批量编译对定制化打样站点的防覆盖保护缺失**：
   - 运行阶段二通用脚手架时，若盲目覆盖已有定制官网（如 NextGEO 官方旗舰站），会导致企业精心打样的内容被回滚为通用模板；
   - 必须以 `project.yaml: custom_site: true` 为唯一权威信源建立防覆盖保护锁。

---

## 2. 改动内容 (What Changes)

1. **确立并沉淀统一工程规范文档**：
   - 新增技术规范文档：[`docs/specs/site-scaffold-standard.md`](docs/specs/site-scaffold-standard.md)（《站点技术底座交付与大模型爬虫双保险工程规范》）；
   - 在 [`AGENTS.md`](AGENTS.md) 中新增“第 7 章：站点技术底座与大模型爬虫工程规范”，作为全团队（Antigravity、Cursor、Windsurf、Claude）开发的最高执行约束。
2. **制定「页面类型 Schema 与底座合规矩阵」**：
   - **首页**：必须具备 Organization+LocalBusiness + WebSite + Service + FAQPage (8~15组) + 三重冗余嗅探 + CSS 兜底（Block 级别）；
   - **博客知识库列表页**：必须具备 CollectionPage + Blog(+ItemList) + 三重冗余嗅探；
   - **博文/案例单页**：必须具备 Article/TechArticle + 三重冗余嗅探（FAQPage **非强制**）；
   - **服务/关于页**：具备 Service/AboutPage/Organization + 三重冗余嗅探。
3. **实现脚手架定制保护锁 (`tools/geo/scaffold.py`)**：
   - 读取 `project.yaml` 中的 `custom_site: true` 配置；
   - 若开启保护，仅编译更新 `/llms.txt`、`/robots.txt` 与 `/schema.jsonld`，严禁覆盖 `index.html` 及站内已有定制目录（about/services/blog 等）。
4. **开发自动化分级核验脚本 (`scripts/check_site_standard.py`)**：
   - 支持按「页面类型矩阵」进行分级校验；
   - 首页、底座三件套、301 路由断言设为阻断性 Error；
   - 存量页面的双保险标签与 CSS 兜底在当前规范沉淀迭代设为 Warning 缺口台账，支持后续专项治理。

---

## 3. 对外能力 (Capabilities)

1. **跨 IDE（Antigravity & Cursor）统一底座交付标准**：明确首页与不同类型页面的差异化合规门槛，杜绝“一把尺子量全站”的认知冲突；
2. **零死链、零 404 路由防御与持续守门**：将 301 重定向与静态资源映射纳入自动化测试常态守门；
3. **定制资产安全保障**：确保多 IDE 协作时，任何批量生成命令绝不抹杀人工定制的高价值打样页面。

---

## 4. 影响范围 (Impact)

- **规范文档**：`AGENTS.md`、`docs/specs/site-scaffold-standard.md`；
- **配置与脚本**：`projects/nextgeo/project.yaml`、`tools/geo/scaffold.py`、`scripts/check_site_standard.py`；
- **非破坏性保证**：不改动任何线上既有博文内容与双栏排版，纯工程规范与保护机制落地。
