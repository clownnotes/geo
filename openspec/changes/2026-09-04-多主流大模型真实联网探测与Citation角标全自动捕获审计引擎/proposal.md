# Proposal: 多主流大模型真实联网探测与 Citation 角标全自动捕获审计引擎 (第 30 维)

## Why (为什么做 / 业务痛点与战略价值)

在完成 1~29 维度的全栈工程建设（涵盖站点底座、普林斯顿 9 因子、全渠道富文本、高管交付门户与热补丁自愈）后，系统已具备深厚的生成、优化、分发与自愈能力。然而，在面向真实商业客户的交付与复盘对账中，依然存在**“最后一公里真实证据链闭环”**的严峻挑战：

1. **从“单点离线沙箱”跨越到“全域多大模型真实联网交叉验证”**：
   - 现有的 `evaluator.py` 与 `live_probing.py` 主要是历史孤立脚本或沙箱模拟，缺少统一的多主流模型真实在线 Web Grounding（联网搜索）并发探测调度中枢；
   - 真实商业客户（特别是投资人与 CMO）最常提出：“别光看本地算法打分，我现在就想看豆包、DeepSeek、Kimi、腾讯元宝在联网状态下，实时搜索我们行业词时到底有没有推荐我们，排第几名？”
2. **Citation 引用角标与分发台账（`dist_ledger.json`）的反向对账缺失**：
   - 真实大模型联网搜索回答时，会在正文中输出引用角标（如 `[1]`、`[2]`）并在文末列出参考网页信源；
   - 过去缺乏**自动化逆向反查机制**：无法自动判定大模型引用的今日头条文章、知乎专栏、GitHub 仓库或官网链接，是否正是我们代运营团队在阶段四为客户分发的高权重信源；
   - 缺少这一对账，就无法用铁一般的事实向甲方高管证明：“大模型推荐你，正是因为采纳了我们为你分发的这篇知乎长文或头条动态！”
3. **全面契合《2026 战略路线图》三大铁律**：
   - **【铁律 1：搜索质量真实提升】**：通过真实 API 探测，精准捕获大模型引用的信源域名与正文切片，反向检验哪些平台信源最容易被主流 AI 爬虫采纳，指导后续分发重心；
   - **【铁律 2：SOP 生产大幅提效】**：一线代运营不再需要人工逐个打开 4 个大模型网页手动输入 45 组意图词截屏。一键全自动并发跑批，15 秒内自动生成结构化对账台账；
   - **【铁律 3：商业交付绝对代差】**：将真实 Citation 反查对账结果作为核心证据链，直接注入到第 28 维《高管只读交付门户》，让企业决策者一目了然看到全网信源采纳实况，强力支撑续费大单。

---

## What Changes (改动了什么)

1. **新建核心在线探测与反查审计引擎 (`tools/geo/live_auditor.py`)**：
   - 实现统一的真实多模型网络请求器：支持标准 OpenAI 兼容协议（火山方舟豆包、DeepSeek、腾讯元宝、月之暗面 Kimi 等），支持动态 API Key 环境变量或项目专属配置读取；
   - **优雅降级机制**：无真实 API Key 或离线断网时，自动平滑切入高拟真确定性沙箱，保证单测 100% 毫秒级通过与自动化回归稳定；
   - **智能 Citation 引用角标与来源逆向解析器**：
     - 精准解析 Markdown 超链接 `[标题](URL)`、正文引用标记 `[1]` / `【1】` / `[Ref]` 及文末 Sources/References 来源列表；
     - 自动清洗规范化 URL 协议、域名、主干路径与锚点；
   - **分发存活台账（`dist_ledger.json`）与资产反向对账器**：
     - 将抓取到的 Citation 信源与项目 `dist_ledger.json`（已发布存活外链）、`projects/<id>/outputs/` 各平台发稿包及官方域名做**真实集合交集比对**；
     - 严格杜绝公式虚构，输出 `dist_matched_citations`（官方分发直接命中条目）、`organic_citations`（全网自然信源）及 `citation_hit_rate`（官方信源采纳率）；
   - **公文级报告与结构化资产落盘**：
     - 输出公文级 Markdown 报告：`projects/<id>/outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md`；
     - 导出机器可读审计明细：`projects/<id>/outputs/live_citation_audit.json`。
2. **CLI 命令行工具链集成 (`tools/geo/cli.py`)**：
   - 注册顶级子命令 `geo probe-audit <project_id>`（别名 `geo citation-audit`）；
   - 支持 `--models doubao,deepseek,kimi,yuanbao`、`--limit N`、`--sandbox`（强制沙箱）、`--reconcile`（开启分发台账对账）等灵活参数。
3. **Web 后端 API 与高管门户数据反哺 (`tools/geo/server.py` & `tools/geo/share.py`)**：
   - 在 `server.py` 挂载 `POST /api/projects/{id}/citation-audit/run`（Bearer Token 鉴权保护）与 `GET /api/projects/{id}/citation-audit/report`；
   - 在 `share.py` 的 `compile_portal_data()` 中挂载 `live_citation_summary`：量化展示大模型真实联网实测首推率（SOV）、角标捕获总数、以及官方分发信源采纳命中数。
4. **自动化单元测试全覆盖 (`tests/test_live_auditor.py`)**：
   - 编写全套自动化单测，覆盖模型矩阵调度、降级沙箱、Citation 正则提取、台账反向对账、CLI 交互及高管门户联动。

---

## Capabilities (新增或修改的对外能力)

- **能力 1 (全自动并发实测)**：`geo probe-audit <project_id> --limit 15` 一键对 4 大主流大模型发起并发意图探测；
- **能力 2 (角标精确捕获)**：自动从大模型联网回答中解析引用角标，提取出结构化的 `citation_urls`、`source_domains` 与正文引用片段；
- **能力 3 (分发信源反向对账)**：真实计算我们的头条/知乎/微信/GitHub 外链被大模型联网引用的命中率与采纳条数，彻底打破“分发了不知道有没有被大模型采纳”的黑盒；
- **能力 4 (高管门户战果联动)**：为免密交付大屏提供无可争议的“真实大模型引用证据链”，让非技术高管直接查验模型推荐背后的信源佐证。

---

## Impact (受影响的部分)

- **新建文件**：
  - `tools/geo/live_auditor.py`：第 30 维核心探测与反查中枢；
  - `tests/test_live_auditor.py`：配套自动化单测试卷。
- **改动文件**：
  - `tools/geo/cli.py`：注册 `geo probe-audit` 子命令；
  - `tools/geo/server.py`：挂载带强鉴权的探测触发与报告读取 API；
  - `tools/geo/share.py`：高管交付大屏追加 `live_citation_summary` 真实对账数据；
  - `docs/strategy/roadmap-2026.md`：同步更新第 30 维战略定义。
- **向后兼容性**：
  - 100% 向后兼容历史报告与命令；
  - 默认无 API Key 时自动平滑降级，确保离线测试与生产环境稳健运行。

