# Proposal: 甲方客户专属免密只读交付门户 (Guest Share Portal)

## Why (为什么做 / 业务痛点与安全诉求)

1. **业务痛点：管理后台与甲方查看权限未做隔离**
   - 当前查看交付成果需要登录 GEO 管理后台，如果直接给甲方账号密码，存在甲方误删项目、篡改配置或查看其他客户隐私的风险；
   - 直接发送 ZIP 压缩包或 Markdown 原始文件，甲方老板在手机端（微信打开）阅读体验较差，无法交互式查看声量曲线与 Citation 图谱。
2. **安全防泄露诉求（解答客户信息防泄密问题）**
   - **高熵不可猜测 Token**：采用密码学强随机数（24 字节 URL-safe Token，计算空间 $2^{192}$），杜绝任何暴力穷举枚举可能；
   - **防爬虫与防搜索引擎收录**：门户全局注入 `noindex, nofollow, noarchive` 协议头与 Meta 标签，防止被百度、Google 或爬虫索引抓取；
   - **支持可选 4 位访问提取码 (PIN Code)**：针对高保密要求客户，支持生成带提取码的专属链接（类似百度网盘加密分享）；
   - **时间窗口控制与一键秒级作废**：支持 7 天 / 30 天 / 永久有效，管理端支持一键作废已发出的分享链接，瞬间切断访问通道。

---

## What Changes (改动范围)

1. **研发分享链接与安全权限管理模块 (`tools/geo/share.py`)**：
   - 实现安全 Token 生成、提取码加盐校验、有效期判断与作废逻辑（存储于 `data/shares.json`）；
   - 实现安全沙箱数据提取器 `get_shared_project_data(token, pin=None)`（仅暴露 5+1 交付产物与声量指标，物理阻断任何写操作与配置泄漏）。
2. **构建专属甲方移动端/桌面端只读交付门户 (`web/share.html`)**：
   - 包含客户企业 Header（企业名、行业、官方 GEO 认证徽章）；
   - 5 步交付全景 Tab 切换浏览（体检报告、底座补丁、普林斯顿语料、四平台分发稿、声量周报、竞品包抄策略）；
   - 渲染历史声量爬坡走势图与 Citation 权威分布进度条；
   - 提取码验证解锁模态窗口（如果启用了 PIN 保护）；
   - 一键打包下载交付 ZIP 包与一键美化打印周报。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `POST /api/projects/{id}/share/create`：生成新的分享链接（支持设置有效天数与可选提取码）；
   - `GET /api/projects/{id}/share/info`：管理端查看当前项目已生成的有效分享链接及作废；
   - `DELETE /api/share/{share_id}`：管理员作废指定分享链接；
   - `GET /api/share/{token}/data`：公开只读数据接口（带 PIN 鉴权与过期拦截）；
   - `GET /share/{token}`：直接返回 `web/share.html` 页面渲染。
4. **Web 管理工作台交互 (`web/index.html`)**：
   - 向导页顶部操作栏增加 **「🔗 生成客户专属交付链接」** 按钮与弹窗，支持一键复制「链接 + 提取码」文案发给客户。
5. **CLI 命令行与 SOP 文档**：
   - 增加 `geo share <project_id> [--days 30] [--pin 1234]` 子命令；
   - 更新交付 SOP 手册。

---

## Capabilities (对外能力)

- `GET /share/{token}` (公开只读交付门户)
- `GET /api/share/{token}/data` (只读沙箱数据)
- `POST /api/projects/{id}/share/create`
- `GET /api/projects/{id}/share/info`
- `DELETE /api/share/{share_id}`
- CLI: `python3 -m tools.geo share <project_id> [--days 30] [--pin 1234]`

---

## Impact (影响分析)

- **完全解耦**：管理端写权限与甲方只读门户完全物理隔离；
- **客户感知大幅跃升**：从发送“一堆冷冰冰的文件”升级为发送“专属高规格商业 GEO 数据看板链接”。
