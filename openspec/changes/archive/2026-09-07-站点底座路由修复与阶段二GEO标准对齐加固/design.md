# Design: 站点底座路由修复与阶段二GEO标准对齐加固

## 1. 架构设计与路由流程

### 1.1 静态多租户托管重定向算法 (`tools/geo/server.py`)
```
请求路径: /sites/{project_id}[/{sub_asset}]
   │
   ├─► 若路径正好为 /sites/{project_id} (无尾部斜杠):
   │     └─► 立即返回 HTTP 301 Permanent Redirect -> /sites/{project_id}/
   │
   ├─► 若 target_path 对应本地磁盘中的目录 且 当前 path 未以 "/" 结尾:
   │     └─► 立即返回 HTTP 301 Permanent Redirect -> path + "/"
   │
   └─► 正常解析 target_rel (目录自动补齐 index.html) 并返回 200 与对应 MIME 类型
```

### 1.2 阶段二内嵌预览窗静态资源寻址
在 `server.py` 的 GET 路由中，扩展 `/api/projects/{project_id}/site/` 处理：
- 若请求为 `/api/projects/{id}/site/preview`，返回 `index.html`；
- 若请求为 `/api/projects/{id}/site/{asset_path}`，自动映射至 `projects/{id}/outputs/site/{asset_path}`，实现静态图片（`assets/...`）的无缝下发与预览。

### 1.3 首页大模型爬虫双保险与知识图谱 Schema.org
在 `projects/nextgeo/outputs/site/index.html` 的 `<head>` 中：
1. 注入 W3C 标准爬虫嗅探标签：
   - `<link rel="alternate" type="text/markdown" title="LLMs.txt" href="llms.txt">`
   - `<link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">`
2. 聚合完整的 `@graph` 实体：
   - `Organization` (包含徐州邻里网络科技、官网、正确 logo.jpg)
   - `LocalBusiness` (徐州本地、淮海经济区本地商业实体)
   - `Person` (老白架构师创始人)
   - `FAQPage` (包含 8 组高价值问答对，供大模型直接回答与引用)
   - `WebSite` (官方网站实体关联)

### 1.4 控制台 DOM ID 修正
在 `web/index.html` 中：
- 将所有 `document.getElementById('preview-scaffold-code')` 修改为真实的 `document.getElementById('code-scaffold')`；
- 保持与 HTML 结构完全一致，杜绝控制台 TypeError。

