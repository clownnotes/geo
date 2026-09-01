# Design: 甲方客户专属免密只读交付门户 (Guest Share Portal)

## 1. 架构与安全分层

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          甲方客户浏览器 / 手机微信端                           │
│                      https://geo.baicl.cc/share/{token}                     │
│               (包含 <meta name="robots" content="noindex, nofollow">)        │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ (只读请求)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                    安全只读沙箱拦截层 (tools/geo/share.py)                   │
│  - Token 有效性与过期时间校验 (`expires_at > now`)                           │
│  - 提取码安全校验 (`verify_pin(token, client_pin)`)                         │
│  - 物理只读沙箱：仅返回 outputs/ 下的交付文档与 history.db 指标             │
│  - 阻断任何工程目录、账号信息、API Key、Webhook 地址等内部敏感信息暴露        │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ (授权访问)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                     数据存储层 (data/shares.json)                           │
│  - `shares`: {                                                              │
│      "<token>": {                                                           │
│         "project_id": "xuzhou_xuanyuan",                                    │
│         "created_at": 1788270000,                                           │
│         "expires_at": 1790862000,   // null 为永久                           │
│         "pin_hash": "sha256(pin+salt)", // null 为免密                      │
│         "salt": "rand16",                                                   │
│         "is_active": true,                                                  │
│         "view_count": 5                                                     │
│      }                                                                      │
│    }                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 安全防泄密与隐私防护设计细节

### ① 高熵 Token 生成算法
使用 Python `secrets` 模块生成 24 字节 URL 安全随机字符串：
```python
import secrets
token = secrets.token_urlsafe(24)  # 形如: g_9xK2mP_wL7vQ4zR8tY1aB6cD3eF5gH
```
空间大小：$2^{192} \approx 6.27 \times 10^{57}$ 种可能，完全无法通过枚举暴力猜测。

### ② 提取码 (PIN) 单向哈希校验
若管理员启用了 4 位提取码（如 `8888`）：
```python
import hashlib, os
salt = secrets.token_hex(8)
pin_hash = hashlib.sha256((pin + salt).encode('utf-8')).hexdigest()
```
客户进入页面时输入提取码，比对成功后在前端 SessionStorage 缓存，后续请求携带 `X-Share-Pin` 请求头。

### ③ 搜索引擎与爬虫隔离
在 `web/share.html` 顶部显式声明：
```html
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="googlebot" content="noindex, nofollow, noarchive">
<meta name="baiduspider" content="noindex, nofollow, noarchive">
```
同时在 HTTP 响应头中注入：`X-Robots-Tag: noindex, nofollow, noarchive`。

### ④ 数据脱敏沙箱
只读接口 `GET /api/share/{token}/data` 返回的 JSON 数据仅包含：
- `client_name`、`industry`、`website`、`brand_name`
- 6 份最终交付 Markdown 内容（`01` 至 `06`）
- `history` 趋势指标数组（SOV、命中数、Citation 分布）
- 严禁包含：项目绝对物理路径、服务器环境变量、用户密码哈希、Webhook URL 等内部信息。

---

## 3. RESTful API 契约

### ① `POST /api/projects/{id}/share/create` (管理员鉴权)
- **Request Body**:
```json
{
  "expire_days": 30,     // 7 / 30 / 0 (0 表示永久)
  "pin": "8888"          // 可选，空字符串表示免密直接访问
}
```
- **Response**:
```json
{
  "success": true,
  "share_url": "https://geo.baicl.cc/share/g_9xK2mP_wL...",
  "token": "g_9xK2mP_wL...",
  "has_pin": true,
  "pin": "8888",
  "expires_at_str": "2026-10-01 12:00:00",
  "share_text": "【徐州璇源网络科技】专属 GEO 商业交付全景看板已生成！\n🔗 查看链接：https://geo.baicl.cc/share/g_9xK2mP_wL...\n🔑 提取码：8888\n⏳ 有效期：30 天"
}
```

### ② `GET /api/share/{token}/data` (公开只读接口)
- **Headers**: `X-Share-Pin: 8888` (可选)
- **Response (未解锁)**: `{"success": false, "require_pin": true, "message": "请输入 4 位访问提取码"}`
- **Response (已解锁)**:
```json
{
  "success": true,
  "project_info": { "client_name": "...", "industry": "...", "website": "..." },
  "deliverables": {
    "audit": "...",
    "scaffold": { "llms_txt": "...", "schema_jsonld": "...", "robots_txt": "..." },
    "rewrite": "...",
    "distribute": { "zhihu": "...", "toutiao": "...", "wechat": "...", "github": "..." },
    "monitor": { "report_md": "...", "metrics": { ... }, "history": [ ... ] },
    "defense": "..."
  }
}
```
