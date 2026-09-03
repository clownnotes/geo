## 1. 准备工作与规范对齐

- [ ] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定 `tools/geo/llm.py` 底座复用、`tools/geo/dist_bot.py` 的 `get_distribution_ledger`、`tools/geo/probing.py` 的 `is_ledger_asset_eligible` 与 `projects/{id}/outputs/factual_anchors.json` 真实档案读取规则（杜绝虚构模块路径；锁定 Query 采样自项目意图库而非写死特定品牌）。

## 2. 研发大模型品牌商业心智渗透与商业转化价值审计引擎 (`tools/geo/mindshare_auditor.py`)

- [ ] 2.1 构建确定性商业意图仿真沙箱 `MindshareSandboxSimulator`（支持多模型多意图探测仿真，返回 Top-1 首推、提及与 Citation 结果）。
- [ ] 2.2 实现 MPI 商业心智渗透指数加权算法 `calculate_mpi`（严格权重 0.35 Weighted SOV + 0.25 Cit + 0.25 BRS + 0.15 KRR；**缺 19/20 outputs 档案时严格按中性 50.0 兜底并标记 imputed，严禁填 95/85 乐观分**）与五星评级判定。
- [ ] 2.3 实现商业转化价值测算模型 `estimate_commercial_conversion_value`（统一公式 $\text{AEV} = \text{round}(|Q| \times 365 \times (\text{MPI}/100.0) \times CPA \times 0.20, 0)$，严格验算 $|Q|=5, \text{MPI}=88.5, CPA=150 \implies 48454$ 元）。
- [ ] 2.4 实现高管商务汇报包生成器 `generate_commercial_pitch_pack`（生成 `outputs/commercial_roi_pitch/` 下 3 份董事会简报、ROI 测算书与续约规划建议书），并规范落盘 `outputs/21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md`（自适应话术与财务非凭证声明）与 `mindshare_conversion_audit.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo mindshare <project_id> [--models M] [--live] [--pitch] [--report]` 子命令并输出 ANSI 商业心智渗透大盘。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/mindshare/status`、`/api/projects/{id}/mindshare/audit`、`/api/projects/{id}/mindshare/pitch` 与 `/api/projects/{id}/mindshare/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404，禁止自动后台计算）。

## 4. Web 控制台商业心智渗透与价值审计工作台升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「💎 商业心智渗透与价值审计 (21)」独立卡片与操作入口，顶部 Header 增加入口。
- [ ] 4.2 开发全屏模态窗口 `mindshare-audit-modal`，展示 MPI 核心大字仪表盘、等效广告价值卡、四维因子雷达拆解与商业意图流水表。
- [ ] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御，并支持 21 号报告在线 Markdown 预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_mindshare_auditor.py`，全量覆盖：
  - 固定数值夹具 1：$\text{SOV}=80.0, \text{Cit}=60.0, \text{BRS}=90.0, \text{KRR}=100.0 \implies \text{MPI}=80.5$（`strong_contender` 四星强势竞争）；
  - 固定数值夹具 2：$\text{SOV}=100.0, \text{Cit}=80.0, \text{BRS}=100.0, \text{KRR}=100.0 \implies \text{MPI}=95.0$（`market_leader` 五星心智垄断）；
  - 固定数值夹具 3：$\text{SOV}=40.0, \text{Cit}=20.0, \text{BRS}=60.0, \text{KRR}=50.0 \implies \text{MPI}=41.5$（`underrepresented` 两星心智盲区）；
  - 固定数值夹具 4 (AEV 估值闭环)：$|Q|=5, \text{MPI}=88.5, CPA=150 \implies \text{AEV}=48454$ 元（系数 0.20 业务商机转化）；
  - 缺档兜底策略断言：无 19/20 outputs 文件时，断言 BRS=50.0、KRR=50.0、`brs_imputed=True`、`krr_imputed=True`，报告包含缺测说明；
  - 断言 `outputs/commercial_roi_pitch/` 下 3 份高管商务交付文件物理存在；
  - 断言自适应报告话术（沙箱免责 + 财务非凭证免责声明；全 live 包含实盘审计声明）；
  - 断言 API 鉴权拦截（未授权 401）与 `/report` 无文件返回 404。
- [ ] 5.2 运行全库单元测试，确保 100% 通过（当前已有 79 组，新增后将达 85+ 组单测全绿）。
- [ ] 5.3 在 `review-log.md` 记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
