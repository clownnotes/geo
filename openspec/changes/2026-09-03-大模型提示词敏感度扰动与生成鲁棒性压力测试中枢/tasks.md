## 1. 准备工作与规范对齐

- [ ] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定导入并复用 `tools.geo.causal_auditor.score_brand_recommendation_confidence` 与 `_build_attribution_source_pool`（严禁编写重复算法；严格物理隔离 12/22/23/24 号与 25 号输出文件）。

## 2. 研发提示词敏感度扰动与生成鲁棒性测试引擎 (`tools/geo/robustness_tester.py`)

- [ ] 2.1 构建确定性四维微扰动生成器（$V_1$ 口语化 ➔ $V_2$ 质疑避坑 ➔ $V_3$ 倒装重排 ➔ $V_4$ 预算对比），基于基准 Query 确定性输出 4 组扰动变体，复用防饱和 Top-3 推荐概率模型计算各阶段得分 $P_k$。
- [ ] 2.2 实现均值 $\bar{P}_{\text{pert}}$、标准差 $\sigma$、变异系数 $CV$、留存率 $RR$ 与生成鲁棒性指数 $GRI$ 计算公式。
- [ ] 2.3 实现高危脆弱扰动项（跌幅 $\ge 15.0$ 分）识别逻辑与鲁棒性三档评级（`rock_solid` / `moderate_fluctuation` / `fragile_sensitive`）。
- [ ] 2.4 实现四维压力测试雷达量化指标计算与容灾加固包生成器 `generate_robustness_hardening_pack`（在 `outputs/robustness_hardening_pack/` 下物理落盘 3 份加固文件）。
- [ ] 2.5 实现公文报告生成与独立落盘：落盘 `outputs/25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md`（含沙箱推演与 live 实盘声明，注明微扰动测试为敏感度推演，非真实用户线上交互全集）与 `outputs/prompt_robustness_stress_test.json`。
- [ ] 2.6 实现有限预算 Live 模式（至多 5 次 API 调用硬限制，深拷贝快照防御，中途异常 100% 完整回滚纯沙箱，5 个得分融合后必须基于最新 $P$ 全量重算均值、标准差、CV、RR、GRI、评级、高危项与雷达）。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo robustness <project_id> [--models M] [--live] [--harden] [--report]` 子命令并输出 ANSI 终端压力测试大盘。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/robustness/status`、`/api/projects/{id}/robustness/test`、`/api/projects/{id}/robustness/harden` 与 `/api/projects/{id}/robustness/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404）。

## 4. Web 控制台压力测试升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「🛡️ 提示词敏感度与生成鲁棒性压力测试 (25)」独立卡片与操作入口，顶部 Header 增加入口。
- [ ] 4.2 开发全屏模态窗口 `robustness-test-modal`，展示 GRI 仪表盘、微扰动变体对比流失表、高危脆弱项预警、四维压力测试雷达与报告在线 Markdown 预览。
- [ ] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_robustness_tester.py`，全量覆盖：
  - 固定数值夹具 1：$P_{\text{orig}}=80.0, P_1=76.0, P_2=74.0, P_3=78.0, P_4=72.0 \implies \bar{P}=75.0, \sigma=2.24, CV=0.030, RR=93.8\% \implies GRI = 91.0\%$ (`rock_solid` 🟢 磐石抗震)；
  - 固定数值夹具 2：$P_{\text{orig}}=80.0, P_1=60.0, P_2=50.0, P_3=70.0, P_4=60.0 \implies \bar{P}=60.0, \sigma=7.07, CV=0.118, RR=75.0\% \implies GRI = 66.2\%$ (`moderate_fluctuation` 🟡 中度波动)；
  - 固定数值夹具 3：$P_{\text{orig}}=80.0, P_1=40.0, P_2=20.0, P_3=50.0, P_4=30.0 \implies \bar{P}=35.0, \sigma=11.18, CV=0.319, RR=43.8\% \implies GRI = 29.8\%$ (`fragile_sensitive` 🔴 脆弱敏感)；
  - 固定数值夹具 4：$P_{\text{orig}}=80.0, P_2=60.0 \implies \Delta_{\text{drop}} = 20.0 \ge 15.0 \implies$ 命中高危脆弱变体；
  - 固定数值夹具 5：$P_{\text{orig}}=80.0, P_1=76.0, P_2=74.0, P_3=78.0, P_4=72.0 \implies \text{Colloquial}=95.0\%, \text{Skepticism}=92.5\%, \text{Syntax}=97.5\%, \text{Comparison}=90.0\%$；
  - 固定数值夹具 6：$v_{(1)}=1.0, v_{(2)}=0.8, v_{(3)}=0.6 \implies P = 89.0$ 分；
  - 硬断言总体标准差分母为 $n=4$（严禁 $n-1$）；
  - 硬断言四维微扰动确定性生成输出内容（$V_1$ 严格为 `"徐州做系统写代码找外包团队推荐哪家比较好？"`）；
  - 硬断言五维雷达数学计算公式；
  - 硬断言 JSON 顶层 Schema 字段（`baseline_query`、`summary.retention_rate` 等）；
  - 硬断言 `outputs/robustness_hardening_pack/` 下 3 份加固文件物理存在；
  - 硬断言自适应报告话术（沙箱推演声明 / live 实盘推演声明 / 免责声明）；
  - 硬断言 live 模式下调用预算严格 $\le 5$ 次，Mock 生产字典返回安全提取并融合，融合后 GRI 随新 $P$ 联动全量重算；
  - 硬断言 live 模式中途异常时 100% 完整回滚纯沙箱快照；
  - 硬断言 API 鉴权拦截（未授权 401）与 `/report` 无文件返回 404。
- [ ] 5.2 运行全库单元测试，确保 100% 通过（当前已有 108 组，新增后预期 $\ge 115$ 组全绿）。
- [ ] 5.3 在 `review-log.md` 记录提案自评，提请另一个 IDE（Cursor）进行独立初审签署 `[已达成共识]`。
