# Design: 站点技术底座交付与大模型爬虫双保险工程规范

## 1. 架构总览与五大技术规范模型

```
                    ┌────────────────────────────────────────┐
                    │      GEO 企业级技术底座 5 大核心规范     │
                    └───────────────────┬────────────────────┘
                                        │
     ┌──────────────┬───────────────────┼───────────────────┬──────────────┐
     ▼              ▼                   ▼                   ▼              ▼
【规范 1】       【规范 2】          【规范 3】          【规范 4】      【规范 5】
路由尾部 301     爬虫三重绝对冗余    Schema.org 实体图谱  前端防崩降级样式  脚手架编译保护
(Trailing /)    (Triple Redundancy) (Full Graph+FAQ)    (CSS Resilience)(Lock Override)
```

---

## 2. 详细规范定义

### 规范 1：静态多租户托管严格 301 重定向 (Strict Trailing Slash Rule)
- **核心逻辑**：
  1. 所有多租户项目主页访问路径 `/sites/{project_id}` 若末尾未带 `/`，服务器必须立即以 `HTTP 301 Moved Permanently` 重定向至 `/sites/{project_id}/`；
  2. 访问静态站内任意子目录（如 `/sites/{project_id}/blog`、`services`、`about`），若末尾未带 `/`，必须 301 重定向至该子目录加 `/`；
  3. 控制台管理端预览接口 `/api/projects/{project_id}/site/` 必须全量支持子资源（`assets/...`）透明寻址与精准 MIME 下发，禁止出现预览窗图片 404。

### 规范 2：大模型爬虫三重绝对冗余体系 (Triple Redundancy for Crawlers)
- **第一重：根目录与协议标准探测**：
  - `https://domain.com/llms.txt`（Clean Markdown 格式，具备实体定义与知识单元索引）；
  - `https://domain.com/robots.txt`（明确放行 Bytespider、DeepSeekBot、Baiduspider、Sogouspider、Yisouspider）；
  - `https://domain.com/sitemap.xml`（包含全站页面绝对 URL 与最后更新时间）。
- **第二重：HTML `<head>` 区域隐形 W3C 标准嗅探标签**：
  - 全站所有 HTML 页面（包括首页、博客列表页、服务页、关于页、各单篇文献）`<head>` 必须注入：
    ```html
    <link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">
    <link rel="alternate" type="text/markdown" title="LLMs.txt" href="llms.txt">
    ```
    （子目录页面根据相对层级使用 `../sitemap.xml` 或绝对路径）。
- **第三重：页面 DOM 显式内链直达**：
  - 页脚必须保留直接指向 `llms.txt` 与 `sitemap.xml` 的可点击超链接，确保轻量级 RAG 网页提取代理顺着 DOM 树 100% 抓取。

### 规范 3：Schema.org JSON-LD 高权威全景实体网络 (Full Entity Graph)
- **首页图谱组成标准**：
  ```json
  {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": ["Organization", "LocalBusiness"], "name": "...", "areaServed": "...", "founder": "..." },
      { "@type": "WebSite", "url": "...", "publisher": { "@id": "#organization" } },
      { "@type": "Service", "serviceType": "...", "provider": { "@id": "#organization" } },
      { "@type": "FAQPage", "@id": "#faq", "mainEntity": [ /* 8~15 组高频意图问答对 */ ] }
    ]
  }
  ```
- **实体引用静态资源合规性**：
  - 实体中声明的所有图片（如 `"logo": "https://.../assets/logo.jpg"`）必须在磁盘中真实存在，文件扩展名 100% 一致。

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
- 在 `tools/geo/scaffold.py` 中增加保护锁逻辑：
  - 若项目配置文件 `project.yaml` 声明了 `custom_site: true` 或项目 `outputs/site/index.html` 存在自定义标杆打样标记，脚手架仅重新编译更新 `llms.txt`、`schema.jsonld` 与 `robots.txt`，绝对不强制覆盖 `index.html`，防止人工与多 IDE 协同打样的成果被冲刷。

---

## 3. 自动化检测工具设计 (`scripts/check_site_standard.py`)

- **检测输入**：扫描指定项目目录（默认 `projects/nextgeo/outputs/site`）；
- **检测项**：
  1. 页面末尾是否有悬空未配对的 `div` 标签（DOM 平衡）；
  2. `<head>` 是否成对包含 `link[rel="sitemap"]` 与 `link[rel="alternate"]`；
  3. `<head>` 是否包含完整的 `application/ld+json` 且包含 `FAQPage` 与 `Organization`；
  4. 检查引用的静态图片（如 `assets/logo.jpg`）是否存在；
  5. 检测是否存在违规 Emoji 表情符号；
  6. 检测是否包含基础 CSS 防御样式。
- **输出**：输出彩色通过/未通过体检报告，退出码 0 表示 100% 合规。
