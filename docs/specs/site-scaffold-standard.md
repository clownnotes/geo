# 站点技术底座交付与大模型爬虫双保险工程规范

> 本文档是全团队（Antigravity、Cursor、Windsurf、Claude 等）在开发、交付与重构客户企业官网底座、静态多租户路由及大模型爬虫协议时的**统一最高执行标准**。

---

## 1. 核心指导思想 (Why)

一切以大语言模型（DeepSeek、豆包、ChatGPT、Kimi、元宝、通义等）与真实企业决策者能够 **100% 毫秒级抓取、无障碍渲染、准确理解并首选推荐** 为唯一导向。坚决摒弃任何由于路径错位、协议缺失、CDN 超时或脚手架误覆盖引发的线上生产事故。

---

## 2. 五大核心技术底座规范

### 规范一：静态多租户托管严格 301 重定向 (Strict Trailing Slash Rule)
- **核心原则**：所有基于相对路径构建的静态站点，根路径或子目录 URL 结尾必须拥有斜杠 `/`，否则浏览器会将上下文 Base URL 锁定至父级，引发全量相对资源（`assets/`、图片、子页面）404 崩溃。
- **服务端行为约束**：
  1. 凡请求 `/sites/{project_id}`（末尾缺少 `/`），服务端必须立即以 `HTTP 301 Moved Permanently` 重定向至 `/sites/{project_id}/`；
  2. 凡请求站内任意静态子目录（如 `/sites/{project_id}/blog`、`about`、`services`），服务端必须立即 301 重定向至该子目录加 `/`；
  3. 控制台管理端预览接口 `/api/projects/{project_id}/site/` 必须全量支持子路径静态资源（`assets/...`）寻址与精确 MIME 下发，禁止出现预览窗图片 404 破损。

### 规范二：大模型爬虫三重绝对冗余体系 (Triple Redundancy for Crawlers)
大模型爬虫抓取能力参差不齐（从高并发官方爬虫到轻量级 RAG 单页提取代理）。全站必须构建三重绝对冗余：
1. **第一重：根目录与协议标准探测**：
   - 必须提供 `https://domain.com/llms.txt`（Clean Markdown 格式，具备实体定义与知识单元索引）；
   - 必须提供 `https://domain.com/robots.txt`（明确放行 Bytespider、DeepSeekBot、Baiduspider、Sogouspider、Yisouspider）；
   - 必须提供 `https://domain.com/sitemap.xml`（包含全站页面绝对 URL 与最后更新时间）。
2. **第二重：HTML `<head>` 隐形 W3C 标准嗅探标签**：
   - 全站所有 HTML 页面 `<head>` 区域必须成对注入：
     ```html
     <link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">
     <link rel="alternate" type="text/markdown" title="LLMs.txt" href="llms.txt">
     ```
     （子目录页面按层级使用 `../sitemap.xml` 或绝对路径）。
3. **第三重：页面 DOM 显式内链直达**：
   - 页脚必须保留直接指向 `llms.txt` 与 `sitemap.xml` 的可点击超链接，确保轻量级 RAG 代理可沿着 DOM 树 100% 抓取。

### 规范三：页面类型 Schema.org 差异化合规矩阵 (Page Type Matrix)
严禁“一把尺子量全站”，页面按路由与职能必须严格遵循以下 Schema.org 规范：

| 页面类型 | 判定路径规则 | Schema.org 强制类型 | 必须包含要素 |
| :--- | :--- | :--- | :--- |
| **P1: 企业首页** | `index.html` (根页面) | `Organization` + `LocalBusiness` + `WebSite` + `Service` + `FAQPage` | 必须包含 8~15 组采购意图问答对、本地商业坐标与创始人实体 |
| **P2: 博客知识库列表** | `blog/index.html` | `CollectionPage` + `Blog` (+ `ItemList`) | 必须包含最新核心博文的 ListItem 映射列表 |
| **P3: 博文与案例单页** | `blog/*.html`, `geo/*.html`, `case-studies/*.html` | `Article` 或 `TechArticle` | 必须包含 headline、author、datePublished（FAQPage **非强制**） |
| **P4: 服务与关于单页** | `services/index.html`, `about/index.html` | `Service` 或 `AboutPage` 或 `Organization` | 包含阶段服务清单、交付边界、准入机制或团队背景 |

- **实体静态资源合规**：Schema 中声明的图片（如 `"logo": ".../assets/logo.jpg"`）必须在本地磁盘真实存在且文件扩展名 100% 一致。

### 规范四：前端排版防御性 CSS 兜底规范 (CSS Resilience Standard)
- **防御原则**：严禁仅依赖外部 Play CDN（如 `cdn.tailwindcss.com`）。
- **必须内联的防御样式**：在页面的 `<style>` 标签中必须内联以下核心重置与容器保护规则，确保在无外网或 CDN 超时时页面不飞散：
  ```css
  *, *::before, *::after { box-sizing: border-box; }
  img, picture, video, canvas, svg { display: block; max-width: 100%; height: auto; }
  body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; }
  a { color: inherit; text-decoration: none; }
  ul, ol { list-style: none; margin: 0; padding: 0; }
  .geo-container { width: min(1180px, calc(100% - 40px)); margin-left: auto; margin-right: auto; }
  ```

### 规范五：脚手架编译防覆盖锁定机制 (Scaffold Override Protection)
- **唯一信源**：`projects/{project_id}/project.yaml` 中的 `custom_site: true`；
- **锁行为规范**：
  1. 当项目声明 `custom_site: true` 时，脚手架 `run_scaffold(project_id)` 仅重新生成与编译 `/llms.txt`、`/robots.txt`、`/schema.jsonld` 与 `02_站点技术底座改造交付包.md`；
  2. **严禁重新生成并覆盖 `index.html`**；
  3. **严禁破坏或覆盖已存在的定制子站目录（如 `about/`、`services/`、`blog/` 等）**；
  4. 控制台日志必须明确打印：`[PROTECTED] 项目已锁定 custom_site: true，保留定制官网页面。`
