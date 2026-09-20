## 1. 准备与规则核对

- [x] 1.1 核对全局协作规则与 AGENTS.md 规范，确认所有修复在开发态（127.0.0.1:8088）严格单测验证，未经用户明确指示绝不擅自推生产。

## 2. 核心代码修复

- [x] 2.1 修改 `tools/geo/server.py` 的 `console_gate`：在未登录拦截判定中，加入公开官网 `/sites/` 以及大模型爬虫文件 `/robots.txt`、`/llms.txt`、`/sitemap.xml` 白名单，确保公开静态资源与爬虫无条件放行；
- [x] 2.2 修改 `tools/geo/server.py` 的 `do_GET` 中 `/sites/` 静态路由分支：修正已登录 RBAC 检查与公开站点访问的关系，允许免密外部访客与爬虫读取已生成的公开站点资源，同时严格保留防路径穿越（`..`）与 301 尾部斜杠补齐；
- [x] 2.3 检查全站爬虫响应头：确保返回公开官网静态内容及爬虫协议时，绝不添加 `X-Robots-Tag: noindex, nofollow, noarchive` 阻断头；
- [x] 2.4 保持内部防护不降级：确认未登录访问 `/.env`、`server.py`、`AGENTS.md`、`/api/projects/` 时继续坚决返回 404。

## 3. 自动化测试与验证

- [x] 3.1 编写/更新针对性测试套件 `tests/test_site_crawler_and_gate.py`：
  - 测试用例 A：模拟未登录爬虫请求 `/sites/nextgeo/`，断言返回 HTTP 200 且无 noindex 响应头；
  - 测试用例 B：模拟未登录爬虫请求 `/robots.txt` 与 `/llms.txt`，断言返回 HTTP 200；
  - 测试用例 C：模拟未登录请求 `/.env`、`server.py`，断言返回 HTTP 404；
  - 测试用例 D：模拟未登录请求私有业务接口 `/api/projects/nextgeo`，断言返回 HTTP 404；
  - 测试用例 E：模拟未登录浏览器访问 `/`，断言正常重定向至登录页 `login.html`；
- [x] 3.2 运行针对性测试，确保 100% 通过；
- [x] 3.3 运行全量测试套件，确保现有 RBAC 与大盘功能不受任何破坏。
