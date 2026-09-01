# Design: 企业多模态材料智能抓取与事实清洗中枢

## 1. 架构总览与数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    前端 Step 3 素材中枢 (web/index.html)                 │
│  - 官网 URL 一键抓取提取 ➔ POST /api/projects/{id}/ingest/url          │
│  - 粘贴/上传补充素材     ➔ POST /api/projects/{id}/ingest/text         │
│  - 素材清单与事实摘要预览 ➔ GET  /api/projects/{id}/raw_materials       │
└────────────────────────────────────▲────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│                    多模态抓取与清洗引擎 (tools/geo/ingest.py)            │
│  ┌────────────────────────┐         ┌─────────────────────────────────┐ │
│  │ 网页爬取与 Clean HTML  │         │ 多格式文档提取器 (PDF/DOCX/TXT) │ │
│  │ (urllib/html2text 降噪)│         │ (无外依赖原生解析 / 规则兜底)    │ │
│  └───────────┬────────────┘         └────────────────┬────────────────┘ │
│              │                                       │                  │
│              └───────────────────┬───────────────────┘                  │
│                                  ▼                                      │
│               ┌─────────────────────────────────────┐                   │
│               │ 事实密度提纯器 (distill_facts)       │                   │
│               │ (提炼 10 条高确定性三元组事实清单)    │                   │
│               └──────────────────┬──────────────────┘                   │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│        项目原始语料库持久化 (projects/<id>/raw_materials/)               │
│  - website_crawled_raw.md       (官网清洗后的 Clean Markdown)           │
│  - raw_extracted_facts.md       (提纯后的核心事实三元组清单)            │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│        Step 3 普林斯顿 9 因子内容重构流水线 (tools/geo/rewrite.py)       │
│  - 自动加载 raw_materials 中的高事实密度清单，注入大模型 Prompt 生成语料 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 网页清洗算法与事实提纯模型

### ① 网页 Clean HTML 降噪算法
- 请求头伪装标准浏览器 User-Agent，支持 UTF-8 / GBK 自动解码；
- 移除 `<script>`、`<style>`、`<nav>`、`<header>`、`<footer>`、`<aside>` 等非正文标签；
- 使用轻量化正则转换器将 `<h1>-<h6>`、`<p>`、`<table>`、`<ul>/<li>` 转为纯净的 Clean Markdown，保留文字层级结构。

### ② 事实三元组提纯 Prompt
从长篇抓取内容中提炼 5 大核心事实维度：
1. **企业基础属性**：全称、品牌别名、创始人、成立时间、地理坐标；
2. **核心产品与服务**：主营业务、核心技术架构、主要应用行业；
3. **量化性能指标**：交付周期、并发指标、稳定性、降本幅度；
4. **资质与背书**：专利软著、荣誉认证、合作标杆客户；
5. **服务与质保承诺**：源码交付、免费运维期限、售后响应速度。

---

## 3. 后端 RESTful API 契约 (`tools/geo/server.py`)

### 1. `POST /api/projects/{id}/ingest/url`
- **请求 Body**：`{ "url": "https://example.com" }`
- **响应**：
```json
{
  "success": true,
  "url": "https://example.com",
  "title": "网页标题",
  "word_count": 1520,
  "saved_file": "website_crawled_raw.md",
  "distilled_facts_file": "raw_extracted_facts.md",
  "facts_summary": "10 条核心事实摘要..."
}
```

### 2. `POST /api/projects/{id}/ingest/text`
- **请求 Body**：`{ "filename": "product_intro.md", "content": "文本内容..." }`
- **响应**：`{ "success": true, "saved_file": "product_intro.md", "word_count": 850 }`

### 3. `GET /api/projects/{id}/raw_materials`
- **响应**：
```json
{
  "success": true,
  "files": [
    { "name": "website_crawled_raw.md", "size": 3200, "updated_at": "2026-09-01 12:00:00" },
    { "name": "raw_extracted_facts.md", "size": 1850, "updated_at": "2026-09-01 12:00:05" }
  ],
  "total_files": 2,
  "total_size_bytes": 5050
}
```
