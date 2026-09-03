# Proposal: 大模型品牌商业心智渗透率与商业转化价值量化审计中枢 (LLM Mindshare Penetration & Commercial Conversion Value Auditor)

## Why (为什么做 / 商业痛点与终极大盘交付刚需)

1. **直击董事长与 CMO 的灵魂拷问：GEO 到底创造了多少商业价值？**
   - 在完成了 01~20 号维度的技术基建（底座改造、语料分发、台账存活、实时探测、声誉清洗、记忆自愈）之后，企业高管（董事长、投资人、CMO）最关注的不是单条提示词代码，而是**商业底线结果**：
     - “我们在豆包、DeepSeek、Kimi 中到底占领了多少市场心智份额？”
     - “相比竞品，我们拦截了多少原本可能流失的高意向商业商机？”
     - “这套 GEO 代运营体系为我们折算节约了多少高昂的百度/巨量竞价广告成本（Ad Equivalent Value）？”
   - 本中枢旨在将 01~20 号的技术成果聚合成终极量化指标：**大模型商业心智渗透指数 (Mindshare Penetration Index, MPI 0~100.0)** 与 **商业转化价值模型 (Commercial Conversion Value, CCV)**，为企业管理层提供极具商业说服力的董事会级审计公文。

2. **从「离散技术指标」到「全域商业心智大盘总览」**：
   - 现有的 18 号（SOV/角标率）、19 号（BRS 声誉分）、20 号（KRR 留存率）各自独立；
   - 本中枢引入权威的 **MPI 四维加权融合模型 (35% SOV + 25% Citation + 25% BRS + 15% KRR)**，给出全案唯一的企业级心智健康度总分与五星渗透评级，让复杂的 AI 评测结果变成一眼看懂的商业商业指数。

3. **赋能高客单价代运营续约与增购提案**：
   - 自动生成面向企业决策层的 **《GEO 商业心智渗透与商业转化价值审计公文报告.md》** 与 **`outputs/commercial_roi_pitch/`** 高管汇报资产包，清晰展示代运营投入产出比（ROI），成为代运营服务商锁定百万级年度大单的关键杀手锏。

---

## What Changes (改动范围与复用策略)

1. **研发大模型品牌商业心智渗透与商业转化价值审计引擎 (`tools/geo/mindshare_auditor.py`)**：
   - **底层复用**：强制直接复用 `tools/geo/llm.py`（单一套 HTTP 客户端与 `resolve_api_key` 链式查找）、`tools/geo/probing.py` 的 `extract_citations_and_sources` / `is_ledger_asset_eligible` / `normalize_url`，并读取项目既有的 18/19/20 号 outputs 历史结果；
   - **读取事实档案**：直接读取 `projects/{id}/outputs/factual_anchors.json`（未生成时回退 `load_project_config`），严禁虚构假模块；
   - **MPI 四维加权融合算法**：严格按照 $0.35 \times \text{SOV} + 0.25 \times \text{Cit} + 0.25 \times \text{BRS} + 0.15 \times \text{KRR}$ 封闭测算，输出 0.0 ~ 100.0 分；
   - **商业转化价值模型 (CCV)**：测算等效公域竞价广告价值（Ad Equivalent Value, AEV）与高意向商机拦截估值；
   - **高管汇报自愈包 (`outputs/commercial_roi_pitch/`)**：生成 3 份高管商务交付成果物；
   - **标准公文落盘**：生成 `outputs/21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md` 与 `mindshare_conversion_audit.json`（自适应 live / sandbox 话术）。

2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo mindshare <project_id>` 子命令：
     - 支持 `--models M`、`--live`、`--pitch`（生成高管汇报包）、`--report`；
     - 输出终端 ANSI 高保真商业心智渗透大盘。

3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/mindshare/status`：获取当前 MPI 得分、心智等级与商业价值估值；
   - `POST /api/projects/{id}/mindshare/audit`：触发全域心智渗透与商业价值审计；
   - `POST /api/projects/{id}/mindshare/pitch`：一键生成高管汇报资产包；
   - `GET /api/projects/{id}/mindshare/report`：获取 21 号公文报告（无文件严格返回 404，禁止自动后台计算）。

4. **Web 管理工作台升级 (`web/index.html`)**：
   - 向导 Step 5 新增「💎 商业心智渗透与价值审计 (21)」独立卡片与操作入口，顶部 Header 增加入口；
   - 开发全屏模态窗口 `mindshare-audit-modal`：展示 MPI 核心仪表盘、商业价值等效卡、四维因子雷达拆解与在线报告预览（全量 `escapeHtmlSafe` 转义）。

5. **自动化测试套件 (`tests/test_mindshare_auditor.py`)**：
   - 覆盖固定数值夹具断言、沙箱仿真、高管包落盘、话术自适应与 API 鉴权/404 语义。

---

## Out of Scope (范围排除声明)

- 本规范致力于提供量化的公域搜索商业价值与等效竞价广告审计，不作为财务维度的审计凭证；
- 模型范围覆盖主流本土模型（豆包、DeepSeek、Kimi）及沙箱，不包含境外模型。

---

## Impact (影响分析)

- **纯增量开发**：复用既有模块，不破坏 01~20 号任何既有功能与数据；
- **最高协同协议遵循**：本地测试锁定 8088 端口，严禁推向生产；**归档严格留给 Cursor 在独立终审通过后执行！**
