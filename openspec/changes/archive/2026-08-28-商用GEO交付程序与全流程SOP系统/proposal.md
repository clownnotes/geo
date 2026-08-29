# Proposal: 商用GEO交付程序与全流程SOP系统

## Why (为什么做)

1. **商业化接单与自用交付痛点**：
   - 现阶段 GEO（生成式引擎优化）在市场上多停留在概念或零散的单一脚本阶段，缺乏一套**标准化的商业接单交付程序**与**端到端闭环 SOP**。
   - 面对外部商业客户或内部自用项目时，缺乏统一的“诊断-改造-重构-分发-监控”流水线，导致交付效率低、客户说服力不足、效果难以量化归因，无法形成高单价与高续费率。
2. **核心业务目标**：
   - 构建一套**开箱即用、工程化程度高、支持多客户管理的商业级 GEO 交付工具（CLI 与工作流）**。
   - 建立一套**规范化、可落地的商业接单与自用交付全流程 SOP 手册**，包含从售前体检报告、技术补丁交付、普林斯顿 9 因子内容重构、渠道分发到周/月度监控自动报表的全套标准化资产。

---

## What Changes (改动了什么)

1. **研发商用 GEO 交付工具程序（`tools/geo` 交付套件）**：
   - **客户体检与诊断器 (`geo audit`)**：基于 Crawl4AI 模拟 AI 爬虫抓取，并发测试 DeepSeek/豆包基准可见度，自动生成《企业 AI 可见度诊断报告》。
   - **技术底座脚手架 (`geo scaffold`)**：一键为客户生成标准合规的 `/llms.txt`、`/llms-full.txt`、Schema.org (JSON-LD) 实体元数据及 `robots.txt` 放行补丁。
   - **普林斯顿 9 因子内容重构引擎 (`geo rewrite`)**：基于 MarkItDown 批量解析客户存量资料（PDF/Word/PPT），通过结构化 Prompt 流水线自动产出高事实密度、含数据对比表与真实 Q&A 的 Markdown 语料。
   - **多平台矩阵分发格式化工具 (`geo distribute`)**：将重构语料自动转换为适配字节系（头条/掘金）与 DeepSeek 系（知乎/GitHub）的发布包。
   - **自动化监控与周报生成引擎 (`geo monitor`)**：定时批量并发调用主流大模型 API 检索核心行业词，提取品牌提及率、排名、引用链接，自动生成客户交付报表。
2. **制定全套商用交付 SOP 规范体系（`docs/sop/` 系列文档）**：
   - **SOP-01**：售前获客与现状诊断 SOP（含诊断报告模板与商业报价方案）。
   - **SOP-02**：站点底座技术改造交付 SOP（含 SSR 验证与 Schema 注入标准）。
   - **SOP-03**：普林斯顿 9 因子内容重构与质检 SOP（含语料编写规范与质检打分表）。
   - **SOP-04**：高权重信源矩阵借壳分发 SOP（含平台选型与发布指引）。
   - **SOP-05**：可见度监控与续费交付 SOP（含监控周报模板与竞品反向归因流程）。
3. **建立多客户项目隔离配置规范 (`projects/<client_id>/`)**：
   - 支持多客户数据隔离、关键词库配置、原始资料存储与历史交付物沉淀。

---

## Capabilities (新增或修改的对外能力)

| 阶段 | 交付程序能力 (CLI / Script) | 交付 SOP 与标准化资产 |
| :--- | :--- | :--- |
| **1. 诊断立项** | `python3 -m tools.geo audit --url <url> --keywords <file>` | 《企业 AI 可见度现状体检报告.md》+ 签单报价方案 |
| **2. 底座改造** | `python3 -m tools.geo scaffold --config <project.yaml>` | `llms.txt`、`JSON-LD` 注入代码片段、`robots.txt` |
| **3. 内容重构** | `python3 -m tools.geo rewrite --input <doc_dir>` | 《普林斯顿 9 因子增强语料库》+ 参数对比表 + FAQ |
| **4. 渠道分发** | `python3 -m tools.geo distribute --platform all` | 头条/掘金/知乎/GitHub 专属发布 Markdown 包 |
| **5. 效果监控** | `python3 -m tools.geo monitor --schedule weekly` | 《GEO 效果与声量增长周报/月报》+ 竞品引用归因表 |

---

## Impact (受影响的部分)

- **新增程序模块**：`tools/geo/`（核心命令行与交付套件代码）。
- **新增文档规范**：`docs/sop/` 下扩展 5 个细分阶段的标准化操作指引文档与客户报告模板。
- **配置与数据隔离**：新增 `projects/` 模板目录，用于管理不同商业客户的项目配置与交付成果。
- **环境依赖**：增加 Python 依赖（`crawl4ai`、`markitdown`、`jinja2`、`openai`/`requests`、`tabulate` 等）。
