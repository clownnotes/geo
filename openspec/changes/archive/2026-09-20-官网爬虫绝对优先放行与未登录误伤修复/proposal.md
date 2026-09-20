# Proposal: 官网爬虫绝对优先放行与未登录误伤修复

## Why (为什么做)

1. **核心痛点与现象**：
   - 生产环境与开发环境中，对外公开官网（`https://www.baicl.cc` / `/sites/nextgeo/`）访问报 **404 Not Found**，同时各大 AI 爬虫必读的根文件（`/robots.txt`、`/llms.txt`、`/sitemap.xml`）全部被阻断；
   - 导致真实客户、访客以及所有主流大模型 AI 爬虫（字节豆包 Bytespider、DeepSeek、百度等）均无法抓取官网任何内容，严重瘫痪了商业 GEO 核心业务。

2. **根本原因剖析（误伤链条）**：
   - 前天（9月19日）在做“纯内部安全加固与敏感文件防泄露”时，在 `tools/geo/server.py` 中引入了总门卫 `console_gate`：规定凡是未登录者除登录页和登录接口外，访问其他任何路径一律直接打回 404；
   - 误将对外公开展示的客户企业官网（`/sites/` 静态目录）和爬虫探针文件判定为“内部未授权请求”，关门拦截；
   - 在静态文件路由层（第 3185 行），又将未登录访客当作越权运营账号处理，再次误判 404；
   - 严重违背了商业 GEO 项目的核心使命与师弟指示的最高红线：**“其他都要保护，但官网一定要优先保障各大公司的爬虫能够爬到！绝不能因保护后台数据把爬虫拒之门外！”**

## What Changes (改动了什么)

1. **改造未登录总门拦截器 (`console_gate`)**：
   - 确立“公开官网与爬虫探测绝对优先通行”原则；
   - 将公开企业静态站路径（`/sites/*`）以及全站爬虫探针（`/robots.txt`, `/llms.txt`, `/sitemap.xml`）明确加入未登录白名单放行列表；
   - 坚决守住安全红线：`/.env`、`server.py`、`AGENTS.md`、`docs/`、`web/` 内部代码及后台 API（`/api/projects/` 等）依然维持 404 严防死守，未登录连根毛都抓不到。
2. **修复公开官网静态托管鉴权逻辑 (`tools/geo/server.py`)**：
   - 区分“内部管理预览”与“对外公开静态托管”：对外公开的静态站点（如已上线的 `nextgeo` 等）对公网爬虫和免密访客 100% 开放读取；
   - 修复未登录访客访问 `/sites/{project_id}/` 时因 `_site_ident is None` 被误判 404 的问题。
3. **消除大模型爬虫阻断标记**：
   - 确保对外静态官网页面与资源绝对不携带 `X-Robots-Tag: noindex, nofollow, noarchive` 阻断头；
   - 确保 `robots.txt` 明确放行国内主流 5 大 AI 爬虫（Bytespider, DeepSeek, Baiduspider 等）。
4. **单元测试与回归防护**：
   - 编写自动化回归测试 `tests/test_site_crawler_and_gate.py`，模拟真实未登录访客与爬虫 User-Agent 探测，验证：官网与爬虫探针 200 秒开；后台与敏感源码 404 严密拒止。

## Capabilities (对外能力)

1. **官网秒级复活**：`https://www.baicl.cc` 及 `/sites/nextgeo/` 对外恢复正常访问，HTML、CSS、JS 与图片 assets 渲染完整无破损；
2. **AI 爬虫通道秒级畅通**：豆包、DeepSeek、Kimi 等 AI 爬虫能 100% 抓取到 Clean Markdown、`llms.txt` 和普林斯顿 9 因子事实源；
3. **后台数据安全不打折**：内部未登录代码物理隔离机制依然生效，黑客与爬虫无法通过未登录探测偷取任何系统敏感文件与后台私有接口。

## Impact (受影响的部分)

- `tools/geo/server.py`（核心网关拦截门与静态站点处理）
- `tests/test_site_crawler_and_gate.py`（新增自动化回归测试用例）
- 生产机（Mac mini）上的服务热载验证
