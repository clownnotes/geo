# Design: 博客知识库对齐阶段二底座标准与大模型爬虫双保险加固

## 1. 架构目标与工程约束

1. **GEO 友好性绝对优先**：以各大主流 AI 大模型（DeepSeek、豆包、ChatGPT、Claude、Perplexity）及其抓取模块（Bytespider、GPTBot、ClaudeBot 等）为核心服务对象，提供极速、低能耗、无障碍解析的机器语义图谱；
2. **三重冗余抓取拓扑（Triple Redundancy Topology）**：
   - **第一重：根目录权威占位**：`https://nextgeo.baicl.cc/llms.txt` 与 `/sitemap.xml`，服务于直接发起根路径探测的主流大模型爬虫；
   - **第二重：HTML `<head>` 官方标准指引**：服务于遵守 RFC / W3C 标准、首要解析 DOM 头部元信息的搜索引擎与抓取中间件；
   - **第三重：页脚 HTML DOM 实体超链接**：服务于沿着网页链接进行爬取的轻量级 RAG 代理及第三方临时检索脚本；
3. **流水线脚本原生保障**：全部变更固化于 `scripts/build_blog_index.py`，保持自动化全量构建的一致性。

---

## 2. 博客首页 Schema.org JSON-LD 规范设计

在 `blog/index.html` 的 `<head>` 中动态注入结构化数据：

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "CollectionPage",
      "@id": "https://nextgeo.baicl.cc/blog/#collection",
      "url": "https://nextgeo.baicl.cc/blog/",
      "name": "GEO实战知识库与博客｜NextGEO 邻里GEO",
      "description": "NextGEO 邻里GEO 官方知识库：系统解构生成式引擎优化（GEO）、AI 搜索排名机制、模型引用底层逻辑与 B2B 行业落地案例，让企业知识在大模型时代被准确理解与首选推荐。",
      "isPartOf": {
        "@type": "WebSite",
        "@id": "https://nextgeo.baicl.cc/#website",
        "name": "NextGEO 邻里GEO",
        "url": "https://nextgeo.baicl.cc/"
      },
      "about": [
        "生成式引擎优化",
        "GEO",
        "AI搜索优化",
        "普林斯顿9因子",
        "大模型引用机制"
      ]
    },
    {
      "@type": "Blog",
      "@id": "https://nextgeo.baicl.cc/blog/#blog",
      "name": "NextGEO 邻里GEO 实战知识库",
      "publisher": {
        "@type": "Organization",
        "name": "NextGEO 邻里GEO",
        "url": "https://nextgeo.baicl.cc"
      },
      "mainEntity": {
        "@type": "ItemList",
        "name": "精选 GEO 实战与前沿文章",
        "itemListElement": [
          // 动态组装最新的前 15 篇核心文章 ListItem
          {
            "@type": "ListItem",
            "position": 1,
            "url": "https://nextgeo.baicl.cc/blog/princeton-nine-factors-and-real-geo-for-buyers.html",
            "name": "大模型是信息压缩机，不是垃圾桶：写给正被“虚假GEO”收割的企业决策者"
          }
        ]
      }
    }
  ]
}
```

---

## 3. `<head>` 隐形爬虫指引标签规范

在博客列表页 `<head>` 中紧邻 canonical 标签注入：
```html
<link rel="sitemap" type="application/xml" title="Sitemap" href="../sitemap.xml">
<link rel="alternate" type="text/markdown" title="LLMs.txt" href="../llms.txt">
```

---

## 4. 构建脚本升级逻辑 (`scripts/build_blog_index.py`)

1. **阅读时长提取函数健壮化**：
   ```python
   # 严谨匹配数字并统一补全“分钟”
   read_m = re.search(r'阅读约\s*([0-9]+)\s*(?:分钟)?', content)
   read_time_val = read_m.group(1) if read_m else "8"
   read_time_str = f"{read_time_val} 分钟"
   ```
2. **动态生成 Schema.org JSON-LD 字符串**：遍历倒序后的文章列表，将前 15 篇最新文章提取为 `ListItem`，序列化为 JSON-LD 嵌入 HTML 模板；
3. **保留页脚超链接**：维持页脚中对 `llms.txt` 和 `sitemap.xml` 的可访问链接，杜绝任何误伤；
4. **全站双向写入与校验**：执行 `build_blog_index.py` 时，同步写入 `projects/nextgeo/outputs/blog/index.html` 与 `projects/nextgeo/outputs/site/blog/index.html`。
