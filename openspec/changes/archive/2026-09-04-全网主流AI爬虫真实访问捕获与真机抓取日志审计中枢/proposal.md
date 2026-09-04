# Proposal: 全网主流AI爬虫真实访问捕获与真机抓取日志审计中枢 (第 31 维)

## 1. Why (需求背景与战略价值)

在 GEO 全链路体系中，企业自有网站（官网、独立站、文档库）是承载 `/llms.txt`、`/llms-full.txt`、Schema.org (JSON-LD) 实体元数据以及普林斯顿 9 因子核心语料的**第一权威事实策源地**。

系统在前期已完成了：
- **第 12 维**：大模型爬虫抓取仿真器（主动向目标站点发起 HTTP 探测）；
- **第 18/30 维**：下游生成端大模型联网探测与 Citation 信源角标反查对账。

然而，在商业交付与客户沟通中，甲方企业董事长、CTO、技术顾问经常提出最直接、最尖锐的现场质问：
> **“你们部署了 `/llms.txt` 和 Schema 语料，字节跳动的 Bytespider、百度的 Baiduspider、OpenAI 的 GPTBot 到底有没有真正来抓过我们网站？抓取的频次是多少？有没有抓到核心产品页面？有没有因为防火墙或 WAF 规则被 403 拦截了？”**

目前系统尚缺少**对生产环境 Web 服务器访问日志（Nginx、Caddy、Apache、CDN 等）中真实 AI 爬虫足迹的反向捕获、特征识别与量化审计中枢**。这一缺口导致：
1. **抓取盲区**：无法证实站点底座改造后，各大模型爬虫在互联网真实世界的入库与抓取频次；
2. **阻断隐患**：许多企业部署了高强度 WAF 或防盗链规则，将 Bytespider / GPTBot 等大模型爬虫误判为恶意扫描并直接 403 拦截，导致 GEO 语料完全无法被大模型收录却浑然不知；
3. **交付代差缺失**：无法向甲方高管出具不可辩驳的“真机爬虫到访心跳流与真实抓取资产详单”。

因此，根据《2026 战略路线图》三大铁律（**【铁律 1】搜索质量真实抓取提升 + 【铁律 3】商业交付绝对专业代差**），立项推进第 31 维《全网主流AI爬虫真实访问捕获与真机抓取日志审计中枢》。

---

## 2. What Changes (改动范围与工程定位)

本规范坚决遵循“零平行烟囱、高复用、数据可信”原则，在现网工程体系上增量构建：

1. **核心审计引擎 (`tools/geo/spider_auditor.py`)**：
   - **User-Agent 特征库复用与扩充**：复用并扩展 `tools/geo/crawler.py` 中的爬虫特征，覆盖全网 10+ 主流大模型爬虫特征指纹（Bytespider 字节豆包、Baiduspider 百度文心、DeepSeek-Crawler、MoonshotBot Kimi、TencentHunyuanBot 腾讯元宝、GPTBot/ChatGPT-User OpenAI、ClaudeBot Anthropic、PerplexityBot、Google-Extended 等）；
   - **通用访问日志解析器 (Log Parser)**：支持标准 Nginx Combined 格式、Caddy JSON/Common 格式与 CDN 访问日志，精准提取客户端 IP、访问时间、HTTP 方法、请求路径、状态码、抓取字节数、User-Agent；
   - **确定性回放沙箱 (`SandboxLogGenerator`)**：当未提供生产日志文件时，内置确定性高拟真沙箱回放，保障自动化单测与离线演示 100% 毫秒级稳定通过，绝不依赖外部网络；
   - **全案公文与结构化 JSON 导出**：导出公文级 Markdown《31_全网主流AI爬虫真实访问捕获与真机抓取日志审计报告.md》与结构化账本 `outputs/spider_access_audit.json`。
2. **CLI 命令行指令 (`tools/geo/cli.py`)**：
   - 注册 `geo spider-audit <project_id> [--log-file /path/to/access.log] [--report]`。
3. **Web 后端 API (`tools/geo/server.py`)**：
   - 挂载 `POST /api/projects/{id}/spider-audit/run`（Bearer Token 强鉴权保护）；
   - 挂载 `GET /api/projects/{id}/spider-audit/status`。
4. **高管只读交付门户战果反哺 (`tools/geo/share.py` & `web/share.html`)**：
   - 在 `compile_portal_data()` 中挂载 `spider_access_summary` 字典，真实映射爬虫到访总数、200 抓取成功率、`/llms.txt` 抓取状态与到访热力；
   - 在无审计数据时严格执行 `status: "never_run"` 优雅降级，绝不虚构假数据；
   - 在 `web/share.html` 对应位置增设【全网主流 AI 爬虫真实到访心跳与抓取热力大屏】卡片。

---

## 3. Capabilities (对外能力与量化指标)

1. **主流 AI 爬虫精准捕获与分类**：
   - 字节跳动 Bytespider（头条/豆包生态）；
   - 百度 Baiduspider / Baiduspider-render（百度百科/文心生态）；
   - 深度求索 DeepSeek-Crawler / DeepSeekBot（技术决策高地）；
   - 月之暗面 MoonshotBot / Kimi-Crawler（研报全网扫描）；
   - 腾讯混元 TencentHunyuanBot（微信搜一搜/元宝独占池）；
   - 国际主流：GPTBot, ClaudeBot, PerplexityBot, Google-Extended。
2. **三维核心审计指标量化**：
   - **大模型爬虫抓取总频次 (Total AI Spider Hits)** 与各厂商占比分布；
   - **核心技术资产抓取覆盖率**：`/llms.txt`、`/llms-full.txt`、`/schema.jsonld`、`robots.txt`、官网首页与核心方案页的独立访问次数；
   - **抓取健康度与状态码分布**：HTTP 200/304 成功率、403 阻断率、404 丢失率与 5xx 服务端错误率。
3. **安全与异常阻断诊断建议**：
   - 🔴 **严重风险 (Danger)**：`/llms.txt` 或根目录出现 403 阻断，出具具体的 Nginx/WAF 防护规则放行配置指南；
   - 🟡 **预警风险 (Warning)**：无大模型爬虫访问记录或 HTTP 200 成功率低于 85%，出具主动提交 Sitemaps 与外链引蜘蛛建议；
   - 🟢 **健康就绪 (Safe)**：成功率 $\ge 95\%$ 且主流大模型爬虫均有近期抓取记录。

---

## 4. Impact (影响与依赖分析)

- **受影响文件**：
  - 新建：`tools/geo/spider_auditor.py`
  - 修改：`tools/geo/cli.py`（增加 `spider-audit` 命令解析与执行逻辑）
  - 修改：`tools/geo/server.py`（增加 Web API 路由与鉴权保护）
  - 修改：`tools/geo/share.py`（高管门户挂载 `spider_access_summary` 与 `never_run` 降级）
  - 修改：`web/share.html`（增加 AI 爬虫到访心跳大屏卡片）
  - 测试：新建 `tests/test_spider_auditor.py`（全量单测秒绿，0 外部网络依赖）
- **工程与安全纪律**：
  - 严格遵循《AGENTS.md》，所有测试与功能全部在本地开发环境（`127.0.0.1:8088`）运行与验证，**严禁私自推送到生产服务器（`mini` / `geo.baicl.cc`）**；
  - 严格遵循 OpenSpec 协同流程，待跨 IDE 审查达成共识后方可开工。
