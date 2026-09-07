# Design: 站点技术底座交付与大模型爬虫双保险工程规范

## 1. 架构总览与页面类型合规矩阵

```
                    ┌────────────────────────────────────────┐
                    │      GEO 企业级技术底座 5 大核心规范     │
                    └───────────────────┬────────────────────┘
                                        │
     ┌──────────────┬───────────────────┼───────────────────┬──────────────┐
     ▼              ▼                   ▼                   ▼              ▼
【规范 1】       【规范 2】          【规范 3】          【规范 4】      【规范 5】
路由尾部 301     爬虫三重绝对冗余    页面类型图谱矩阵    前端防崩降级样式  脚手架编译保护
(Trailing /)    (Triple Redundancy) (Matrix by Type)    (CSS Resilience)(custom_site: true)
```

---

## 2. 页面类型合规矩阵 (Page Type Compliance Matrix)

为彻底避免“一把尺子量全站”的认知错误，全站页面按路由与功能划分为 4 类，分别定义差异化的校验门槛：

| 页面类型 | 判定路径规则 | Schema.org 强制类型 | 必须元素 | 爬虫双保险嗅探标签 | CSS 降级兜底 | 违规级别 |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **P1: 企业首页** | `index.html` (根页面) | `Organization` + `LocalBusiness` + `WebSite` + `Service` + `FAQPage` (8~15组) | 必须包含首屏标杆三元组与联系方式 | 必须 (阻塞) | 必须 (阻塞) | **Error (阻断)** |
| **P2: 博客知识库列表** | `blog/index.html` | `CollectionPage` + `Blog` (+ `ItemList`) | 必须包含多篇核心博文的 ListItem 映射 | 必须 (阻塞) | 建议 | **Error / Warn** |
| **P3: 博文与案例单页** | `blog/*.html`, `geo/*.html`, `case-studies/*.html` | `Article` 或 `TechArticle` (+ author/datePublished) | 双栏黄金栅格、280px 吸顶目录、DOM 标签严格平衡 | 推荐 (当前 Warn) | 建议 (当前 Warn) | **Warn (存量台账)** |
| **P4: 服务与关于单页** | `services/index.html`, `about/index.html` | `Service` 或 `AboutPage` 或 `Organization` | 阶段服务清单/准入机制/团队资质 | 推荐 (当前 Warn) | 建议 (当前 Warn) | **Warn (存量台账)** |

---

## 3. 详细规范定义

### 规范 1：静态多租户托管严格 301 重定向 (Strict Trailing Slash Rule)
- **核心逻辑**：
  1. 所有多租户项目主页访问路径 `/sites/{project_id}` 若末尾未带 `/`，服务端必须立即以 `HTTP 301 Moved Permanently` 重定向至 `/sites/{project_id}/`；
  2. 访问静态站内任意子目录（如 `/sites/{project_id}/blog`、`services`、`about`），若末尾未带 `/`，必须 301 重定向至该子目录加 `/`；
  3. 控制台管理端预览接口 `/api/projects/{project_id}/site/` 必须全量支持子资源（`assets/...`）透明寻址与精准 MIME 下发，禁止出现预览窗图片 404；
- **守护门禁**：通过自动化测试脚本对 `/sites/{id}`、`/sites/{id}/blog` 断言 Location 头部包含结尾 `/`。

### 规范 2：大模型爬虫三重绝对冗余体系 (Triple Redundancy for Crawlers)
- **第一重：根目录与协议标准探测**：
  - `https://domain.com/llms.txt`（Clean Markdown 格式，具备实体定义与知识单元索引）；
  - `https://domain.com/robots.txt`（明确放行 Bytespider、DeepSeekBot、Baiduspider、Sogouspider、Yisouspider）；
  - `https://domain.com/sitemap.xml`（包含全站页面绝对 URL 与最后更新时间）。
- **第二重：HTML `<head>` 区域隐形 W3C 标准嗅探标签**：
  - `<head>` 区域必须包含：
    ```html
    <link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">
    <link rel="alternate" type="text/markdown" title="LLMs.txt" href="llms.txt">
    ```
  - **路径容错标准**：检测工具对 `href="sitemap.xml"`、`../sitemap.xml`、`../../sitemap.xml`、绝对路径 `/sitemap.xml` 均视为合规。
- **第三重：页面 DOM 显式内链直达**：
  - 页脚必须保留直接指向 `llms.txt` 与 `sitemap.xml` 的可点击超链接，确保轻量级 RAG 网页提取代理顺着 DOM 树 100% 抓取。

### 规范 3：Schema.org JSON-LD 高权威全景实体网络
- 按照上述“页面类型合规矩阵”配置；
- **实体引用静态资源合规性**：实体中声明的所有图片（如 `"logo": "https://.../assets/logo.jpg"`）必须在磁盘中真实存在，文件扩展名 100% 一致。

### 规范 4：前端排版防御性 CSS 兜底 (CSS Resilience Standard)
- **防御原则**：严禁仅依赖外部 Play CDN（如 `cdn.tailwindcss.com`）；
- **内联兜底标准**：页面 `<style>` 中必须内联基础重置与排版约束：
  ```css
  *, *::before, *::after { box-sizing: border-box; }
  img, picture, video, canvas, svg { display: block; max-width: 100%; height: auto; }
  body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; }
  a { color: inherit; text-decoration: none; }
  ul, ol { list-style: none; margin: 0; padding: 0; }
  .geo-container { width: min(1180px, calc(100% - 40px)); margin-left: auto; margin-right: auto; }
  ```

### 规范 5：脚手架编译防覆盖锁定机制 (Scaffold Override Protection)
- **唯一信源**：`projects/{project_id}/project.yaml` 中的 `custom_site: true`；
- **行为规范**：
  - 当 `custom_site: true` 时：运行 `run_scaffold(project_id)` 仅允许重新编译更新 `/llms.txt`、`/robots.txt`、`/schema.jsonld`（以及必要时的 sitemap）；
  - **严禁重新生成并覆盖 `index.html`**；
  - **严禁触碰或覆盖已存在的定制子站目录（如 about/、services/、blog/ 等）**；
  - 控制台日志明确打印 `[PROTECTED] 项目声明了 custom_site: true，已跳过覆盖 index.html`。

---

## 4. 自动化分级体检脚本设计 (`scripts/check_site_standard.py`)

- **模式定位**：分级把关（Block 级致命错误 vs 存量台账建议）；
- **分级判断规则**：
  - 🔴 **阻断级 (Error -> exit 1)**：
    1. 首页缺少 Schema.org 或缺少关键实体（Organization / LocalBusiness / FAQPage）；
    2. 首页 `<head>` 缺少 `link[rel="alternate"]` 或 `link[rel="sitemap"]`；
    3. 静态多租户路由末尾斜杠 301 重定向失效；
    4. 根目录底座 3 件套（`llms.txt`、`robots.txt`、`schema.jsonld`）缺失；
    5. Schema 中引用的 Logo 文件不存在；
    6. 页面存在严重未配对闭合的悬空 `div` 标签（破坏栅格布局）。
  - 🟡 **缺口台账级 (Warning -> 仅提示统计，不阻断 exit 0)**：
    1. 存量博文或服务页缺少 `<head>` 双嗅探标签（留待后续批处理更新）；
    2. 存量博文缺少防御性内联 CSS 兜底（留待后续统一补齐）；
    3. `robots.txt` 未显式出现某一特定大模型爬虫。
