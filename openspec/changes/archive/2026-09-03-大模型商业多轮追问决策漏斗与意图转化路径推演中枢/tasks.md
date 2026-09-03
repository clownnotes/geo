## 1. 准备工作与规范对齐

- [x] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定导入并复用 `tools.geo.causal_auditor.score_brand_recommendation_confidence` 与 `_build_attribution_source_pool`（严禁编写第三套 Top-3 实现；锁定 Query 填槽算法依赖 `load_project_config`；严格物理隔离 12、22、23 号与 24 号输出文件）。

## 2. 研发多轮决策漏斗与意图转化推演引擎 (`tools/geo/funnel_simulator.py`)

- [x] 2.1 构建确定性四阶商业决策链条生成器（$S_1$ 认知 ➔ $S_2$ 评估 ➔ $S_3$ 决策 ➔ $S_4$ 行动），基于填槽模板确定性输出 4 组追问 Query，复用防饱和 Top-3 推荐概率模型计算各阶段得分 $P(S_k)$。
- [x] 2.2 实现漏斗状态转移留存率 $T(S_k \to S_{k+1})$、端到端转化率 $FCR$ 与阶段跌幅风险指数 $HRI_k$（Hijacking Proxy 代理指标）计算公式。
- [x] 2.3 实现关键断流脆弱拐点 (Hijacking Turning Point) 判定逻辑与漏斗健康度三档评级（`smooth_conversion` / `mid_funnel_leakage` / `severe_dropoff`）。
- [x] 2.4 实现四维漏斗雷达指标计算与拦截加固包生成器 `generate_funnel_defense_pack`（在 `outputs/funnel_defense_pack/` 下物理落盘 3 份加固文件）。
- [x] 2.5 实现公文报告生成与独立落盘：落盘 `outputs/24_大模型商业多轮追问决策漏斗与意图转化路径推演报告.md`（含沙箱推演与 live 实盘多轮声明，注明沙箱多轮推演非真实用户线上会话日志，竞品消融 Out of Scope）与 `outputs/conversational_funnel_simulation.json`。
- [x] 2.6 实现有限预算 Live 模式（至多 4 次 API 调用硬限制，深拷贝快照防御，中途异常 100% 完整回滚纯沙箱，4 阶段融合完成后必须基于最新 $P$ 全量重算 $T$/FCR/$HRI_k$/断点/雷达）。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [x] 3.1 在 `tools/geo/cli.py` 中注册 `geo funnel <project_id> [--models M] [--live] [--defend] [--report]` 子命令并输出 ANSI 终端漏斗转化大盘。
- [x] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/funnel/status`、`/api/projects/{id}/funnel/simulate`、`/api/projects/{id}/funnel/defend` 与 `/api/projects/{id}/funnel/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404）。

## 4. Web 控制台决策漏斗推演升级 (`web/index.html`)

- [x] 4.1 在向导第五阶段新增「🌪️ 多轮决策漏斗与意图转化推演 (24)」独立卡片与操作入口，顶部 Header 增加入口。
- [x] 4.2 开发全屏模态窗口 `funnel-sim-modal`，展示 FCR 仪表盘、四阶漏斗转化流失图、断流拐点预警、四维漏斗雷达与报告在线 Markdown 预览。
- [x] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御。

## 5. 自动化测试与跨 IDE 联合审查

- [x] 5.1 编写 `tests/test_funnel_simulator.py`，全量覆盖：
  - 固定数值夹具 1：$P(S_1)=80.0, P(S_2)=72.0, P(S_3)=64.0, P(S_4)=60.0 \implies FCR = 75.0\%$ (`smooth_conversion` 🟢 丝滑转化)；
  - 固定数值夹具 2：$P(S_1)=80.0, P(S_2)=56.0, P(S_3)=48.0, P(S_4)=44.0 \implies FCR = 55.0\%$ (`mid_funnel_leakage` 🟡 中段泄漏)；
  - 固定数值夹具 3：$P(S_1)=80.0, P(S_2)=40.0, P(S_3)=32.0, P(S_4)=24.0 \implies FCR = 30.0\%$ (`severe_dropoff` 🔴 严重断流)；
  - 固定数值夹具 4：$P(S_1)=80.0, P(S_2)=48.0 \implies T(S_1 \to S_2) = 60.0\%, HRI_2 = 40.0\%$；
  - 固定数值夹具 5：$P(S_3)=60.0, P(S_4)=15.0 \implies \Delta_{\text{drop}} = 45.0 \ge 20.0 \implies$ 命中高危断点；
  - 固定数值夹具 6：$v_{(1)}=1.0, v_{(2)}=0.8, v_{(3)}=0.6 \implies P = 89.0$ 分；
  - 断言确定性四阶意图填槽算法输出内容；
  - 断言四维雷达数学计算公式；
  - 断言 `outputs/funnel_defense_pack/` 下 3 份拦截文案物理存在；
  - 断言自适应报告话术（沙箱推演声明 / live 实盘推演声明 / 免责声明）；
  - 断言 live 模式下调用预算严格 $\le 4$ 次，Mock 生产字典返回安全提取并融合，融合后 FCR 随新 $P$ 联动全量重算；
  - 断言 live 模式中途异常时 100% 完整回滚纯沙箱快照；
  - 断言 API 鉴权拦截（未授权 401）与 `/report` 无文件返回 404。
- [x] 5.2 运行全库单元测试，确保 100% 通过（当前已有 101 组，新增后达 108 组全绿）。
- [x] 5.3 在 `review-log.md` 记录实现自评，提请另一个 IDE（Cursor）进行独立代码终审打出 `[通过]` 并由其归档。
