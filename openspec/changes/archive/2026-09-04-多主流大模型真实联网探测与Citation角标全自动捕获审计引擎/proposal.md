# Proposal: 多主流大模型真实联网探测与 Citation 角标全自动捕获审计引擎 (第 30 维)

## Why (为什么做 / 业务痛点与战略价值)

在完成 1~29 维度的全栈工程建设（涵盖站点底座、普林斯顿 9 因子、全渠道富文本、高管交付门户与热补丁自愈）后，系统已具备深厚的生成、优化、分发与自愈能力。前期第 18 维已建立了基于 `probing.py` 的基础探测中枢与台账比对机制，但在面向真实商业客户交付与高管汇报时，依然存在以下**关键增量缺口**：

1. **高管只读交付门户（第 28 维）缺少实测 Citation 证据链挂载**：
   - 现网 `share.py` 的 `compile_portal_data()` 目前仅包含体检、心智渗透率 (MPI)、竞对截流与自愈摘要，**完全缺少真实大模型联网探测与 Citation 角标反查数据**；
   - 甲方企业高管在查看免密交付大屏时，急需看到：“大模型在真实联网推荐我们时，到底采纳了哪篇头条、知乎或 GitHub 链接？”
2. **本土主流模型矩阵覆盖缺口（腾讯元宝）**：
   - 现网 `tools/geo/llm.py` 仅配置了 DeepSeek、豆包、Kimi，尚缺腾讯元宝（Hunyuan 微信独占生态）的统一适配与密钥调度；
3. **角标解析本土化增强与极速重对账（`--reconcile-only`）诉求**：
   - 现网角标解析主要覆盖 `[1]` / `[[1]]` / `^1`，对于本土模型常出现的中文方头括号 `【1】`、`[注1]` 等尚缺鲁棒支持；
   - 在分发台账回填（`dist_bot`）或手工追加外链后，代运营人员需要**免重新调用大模型 API 的极速重对账能力（`--reconcile-only`）**，在 1 秒内刷新对账数据并同步门户。
4. **全面契合《2026 战略路线图》三大铁律**：
   - **【铁律 1：搜索质量真实提升】**：通过真实 API 与沙箱双模探测，精准捕获大模型引用的信源域名与正文切片，反向指导分发重心；
   - **【铁律 2：SOP 生产大幅提效】**：提供一键并发探测与 `--reconcile-only` 毫秒级重对账，摆脱重复调 API 耗时；
   - **【铁律 3：商业交付绝对代差】**：将真实 Citation 反查对账结果作为核心证据链，直接注入到第 28 维《高管只读交付门户》，让企业决策者一目了然看到全网信源采纳实况，强力支撑续约大单。

---

## What Changes (改动了什么 / 严禁平行烟囱，增量扩展基座)

坚决杜绝再造一套平行的“第三套探测引擎”。第 30 维定位为**对第 18 维 `probing.py`、`llm.py` 与第 28 维 `share.py` 的增量扩展与高管门户闭环**：

1. **底层大模型供给矩阵扩充 (`tools/geo/llm.py`)**：
   - 在 `PROVIDERS` 中新增 `yuanbao`（腾讯元宝 / Hunyuan API 标准兼容配置）；
   - 支持 `GEO_YUANBAO_API_KEY` / `HUNYUAN_API_KEY` 链式降级读取，使探测矩阵扩展为豆包、DeepSeek、Kimi、元宝 4 大主力。
2. **核心探测与反查中枢增量增强 (`tools/geo/probing.py`)**：
   - **角标正则补丁**：在 `extract_citations_and_sources()` 中增量扩展对中文角标 `【(?P<idx>\d+)】`、`\[注(?P<idx>\d+)\]` 的双通道解析；
   - **对账规则严格保持**：严格复用 `is_ledger_asset_eligible`、`trace_citations_against_ledger` 与 `dist_bot.get_distribution_ledger`，**坚决杜绝裸渠道域名算作命中**，仅 `exact_hit` / 路径前缀 `domain_hit` 计入我方资产，未匹配资产记录为 `third_party_or_competitor`（不虚抬命中率）；
   - **极速重对账模式**：新增 `reconcile_existing_trace(project_id)`，支持在不调用大模型的前提下，基于已有 `live_probing_trace.json` 读取最新 `dist_ledger.json` 重新计算对账与公文；
   - **公文 30 号输出**：增强报告生成器，生成面向高管交付的 `outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md` 并保持与 `live_probing_trace.json` 指标完全同源。
3. **高管只读交付门户数据联动 (`tools/geo/share.py` & 前端模板)**：
   - 在 `compile_portal_data()` 中新增 `live_citation_summary` 挂载；
   - 自动读取 `live_probing_trace.json`，计算实测 SOV、Top1 首推率、Citation 捕获数、我方分发命中率；
   - **优雅降级**：无探测数据时严格返回 `status: "never_run"`，得分 0，绝不伪造虚假数据。
4. **CLI 命令行与 Web API 集成 (`tools/geo/cli.py` & `tools/geo/server.py`)**：
   - 扩展 `geo probe` 命令，新增 `--reconcile-only`、`--portal-sync` 参数；
   - 挂载 `geo probe-audit` 别名并在 `--help` 中明确标明底层复用 `probing.py`；
   - 复用既有 `/api/projects/{id}/probing/run`，新增 `POST /api/projects/{id}/probing/reconcile` 接口，享受既有 Bearer Token 强鉴权保护。
5. **增量测试套件覆盖 (`tests/test_probing.py` 或 `tests/test_live_probing_audit.py`)**：
   - 编写元宝 provider 适配、中文方头角标提取、`--reconcile-only` 离线重对账、以及高管门户 `live_citation_summary` 联动降级的全套单测。

---

## Capabilities (新增或修改的对外能力)

- **能力 1 (四大主流模型矩阵全覆盖)**：支持豆包、DeepSeek、Kimi、元宝统一调用与沙箱回退；
- **能力 2 (本土化角标精准提取)**：完美兼容 `[1]`、`[[1]]`、`^1`、`【1】`、`[注1]` 等多种大模型格式；
- **能力 3 (极速离线重对账)**：`geo probe <project_id> --reconcile-only` 毫秒级基于最新分发台账刷新对账结论；
- **能力 4 (高管门户战果挂载)**：免密交付大屏新增“真实大模型引用证据链”卡片，打通从探测到交付的最后一公里。

---

## Impact (受影响的部分)

- **改动文件**：
  - `tools/geo/llm.py`：新增 `yuanbao` 供应商配置与密钥链；
  - `tools/geo/probing.py`：增强中文角标解析、新增 `reconcile_existing_trace`、支持 30 号公文输出；
  - `tools/geo/cli.py`：扩展 `geo probe` / `geo probe-audit` 参数支持；
  - `tools/geo/server.py`：新增 `/api/projects/{id}/probing/reconcile` 路由；
  - `tools/geo/share.py`：挂载 `live_citation_summary` 并实现 `never_run` 降级；
  - `tests/test_probing.py`：扩充增量单测。
- **100% 杜绝平行烟囱**：不引入孤立的 `live_auditor.py`，全量复用 18 维现有函数。
- **向后兼容性**：完全兼容既有 `geo probe` 调用与 `live_probing_trace.json` 契约。


