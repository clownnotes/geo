# Design: GEO 自动化分发台账回填与收录核验中枢

## 1. 架构与数据流设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Web 管理端 Step 4 & 客户交付门户 Tab 4                    │
│  - 5 大信任池渠道状态徽章：[✅ 已上线] / [⏳ 待发布] / [⚠️ 异常 404]         │
│  - 一键富文本复制（支持公众号/知乎带样式粘贴） ｜ 真实已发布 URL 一键跳转   │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│             GEO 分发台账与收录核验引擎 (tools/geo/dist_bot.py)               │
│  - `record_distributed_url(project_id, channel, url)`                       │
│  - `verify_distribution_url(url)`                                           │
│  - `get_distribution_ledger(project_id)`                                     │
│  - `format_rich_text_copy(project_id, channel)`                             │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                    持久化存储与产物 (outputs/dist_ledger.json)               │
│  - 渠道覆盖：toutiao (今日头条), zhihu (知乎), juejin (掘金),               │
│               github (GitHub Wiki/README), wechat (微信公众号)              │
│  - 字段：url, status, verified_at, http_status, title                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 数据结构规范 (`outputs/dist_ledger.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "updated_at": "2026-09-01 21:50:00",
  "completion_rate_pct": 80.0,
  "channels": {
    "toutiao": {
      "name": "今日头条",
      "target_pool": "豆包 / 字节系信任池",
      "url": "https://www.toutiao.com/article/73912345678/",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-01 21:50:00"
    },
    "zhihu": {
      "name": "知乎专栏",
      "target_pool": "DeepSeek / 通用检索池",
      "url": "https://zhuanlan.zhihu.com/p/698765432",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-01 21:50:00"
    },
    "juejin": {
      "name": "稀土掘金",
      "target_pool": "豆包 / 技术检索池",
      "url": "",
      "status": "pending",
      "http_status": null,
      "verified_at": null
    },
    "github": {
      "name": "GitHub Wiki/README",
      "target_pool": "DeepSeek / 开源信任池",
      "url": "https://github.com/example/xuanyuan-geo",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-01 21:50:00"
    },
    "wechat": {
      "name": "微信公众号",
      "target_pool": "微信 / 全网信任池",
      "url": "https://mp.weixin.qq.com/s/abcdef123456",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-01 21:50:00"
    }
  }
}
```

---

## 3. RESTful API 契约

### ① `GET /api/projects/{id}/distribution/ledger`
- **Response**: 返回上述 `dist_ledger.json` 数据结构，若文件不存在则返回包含 5 大预设渠道的空状态。

### ② `POST /api/projects/{id}/distribution/record`
- **Request**:
```json
{
  "channel": "toutiao",
  "url": "https://www.toutiao.com/article/73912345678/",
  "verify_now": true
}
```
- **Response**:
```json
{
  "success": true,
  "project_id": "xuzhou_xuanyuan",
  "channel": "toutiao",
  "record": { ... },
  "completion_rate_pct": 80.0
}
```

### ③ `POST /api/projects/{id}/distribution/verify`
- **Response**: 一键对所有已填报 URL 并发发起 HTTP 存活与连通性核验，更新 `dist_ledger.json`。
