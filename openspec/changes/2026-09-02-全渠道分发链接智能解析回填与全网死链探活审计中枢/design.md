# Design: 全渠道分发链接智能解析回填与全网死链探活审计中枢

## 1. 架构流程与模块设计 (`tools/geo/distributor.py` / `health_checker.py`)

```
运营人员粘贴任意包含链接的文本 / URL 列表
                     │
                     ▼
       parse_mixed_links(raw_text)
       ├── 正则提取所有 http:// 与 https:// 链接
       ├── 域名模式匹配 (Domain Rule Matrix):
       │   ├── toutiao.com / wtt.toutiao.com ──► 头条号/微头条 (豆包生态)
       │   ├── zhihu.com/p/ / zhihu.com/question ──► 知乎专栏 (DeepSeek生态)
       │   ├── mp.weixin.qq.com ──► 微信公众平台 (腾讯元宝/搜一搜)
       │   ├── github.com ──► GitHub 开源仓库 (DeepSeek生态)
       │   ├── baike.baidu.com / wenku.baidu.com / zhidao.baidu.com ──► 百度生态 (文心一言)
       │   └── 其他域名 ──► 垂直行业权威媒体 (SEO外链)
       │
       ▼
   backfill_publication_ledger(project_id, links)
       ├── 读取 04_全网分发渠道执行与存活台账.md
       ├── 智能去重 (URL 唯一性校验)
       ├── 增量回填追加到各渠道分类表格中
       └── 重新计算存活率并更新台账汇总指标
                     │
                     ▼
   audit_channel_links_health(project_id, concurrency=8)
       ├── 多线程并发 HTTP HEAD / GET 状态探测 (带 Chrome User-Agent)
       ├── 检测 200 / 301 / 302 (存活) vs 404 / 403 / 500 / Timeout (死链/异常)
       ├── 动态回写台账表格中的「当前状态」列
       └── 输出审计报告：总链接数、存活数、死链列表与存活率 %
```

---

## 2. API 接口定义

- **`POST /api/projects/{id}/ledger/batch-add`**
  - 请求体：`{"raw_text": "https://mp.weixin.qq.com/... \n https://zhuanlan.zhihu.com/p/..."}`
  - 返回：`{"success": true, "added_count": 2, "duplicates": 0, "items": [...]}`
- **`POST /api/projects/{id}/ledger/audit`**
  - 请求体：`{}`
  - 返回：`{"success": true, "total": 12, "alive": 12, "dead": 0, "alive_rate": "100.0%", "details": [...]}`
- **`GET /api/projects/{id}/ledger/summary`**
  - 返回台账统计与当前存活状态。

