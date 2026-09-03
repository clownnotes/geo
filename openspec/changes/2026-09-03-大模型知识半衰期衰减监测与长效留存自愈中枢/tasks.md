## 1. 准备工作与规范对齐

- [ ] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定 `tools/geo/llm.py` 底座复用、`tools/geo/probing.py` 的 `is_ledger_asset_eligible` 与 `projects/{id}/outputs/factual_anchors.json` 真实档案读取规则（杜绝虚构模块路径）。

## 2. 研发大模型知识半衰期衰减监测与自愈引擎 (`tools/geo/decay_monitor.py`)

- [ ] 2.1 构建确定性时间序列仿真沙箱 `DecaySandboxSimulator`（支持模拟 Day 1、Day 7、Day 14、Day 30 召回衰减，掺入衰减下滑 Query 与非台账信源）。
- [ ] 2.2 实现知识留存率算法 `calculate_krr` 与指数半衰期预测模型 `estimate_half_life`（锁定以 KRR 为单一决策轴判定 Safe/Warning/Danger，严禁历史最高分漂移，消除双口径冲突）。
- [ ] 2.3 复用 `tools/geo/probing.py` 的 `is_ledger_asset_eligible` 与 `dist_bot.get_distribution_ledger`，严格过滤非 published/verified 链接，计算有效得分。
- [ ] 2.4 实现自愈补量刷新包生成器 `generate_decay_healing_pack`（生成 `outputs/decay_healing_pack/` 下 3 份强化清单、自愈草稿与推荐计划），并规范落盘 `outputs/20_大模型知识半衰期衰减监测与长效留存自愈报告.md`（强制包含沙箱免责话术）与 `knowledge_decay_retention.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo decay <project_id> [--models M] [--live] [--heal] [--report]` 子命令并输出 ANSI 衰减时间序列大盘。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/decay/status`、`/api/projects/{id}/decay/track`、`/api/projects/{id}/decay/heal` 与 `/api/projects/{id}/decay/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404，禁止自动后台计算）。

## 4. Web 控制台知识衰减与自愈工作台升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「⏳ 知识半衰期衰减与长效自愈 (20)」独立卡片与操作入口，顶部 Header 增加入口。
- [ ] 4.2 开发全屏模态窗口 `decay-monitor-modal`，展示 KRR 留存大字仪表盘、半衰期预测卡、各意图词衰减流水与一键自愈生成。
- [ ] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御，并支持 20 号报告在线 Markdown 预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_decay_monitor.py`，全量覆盖：
  - 固定数值夹具 1：$S_{\text{current}} = 12.0, S_{\text{baseline}} = 12.0 \implies \text{KRR} = 100.0\%, t_{1/2} = 90.0$ 天（Safe）；
  - 固定数值夹具 2：$S_{\text{current}} = 9.0, S_{\text{baseline}} = 12.0 \implies \text{KRR} = 75.0\%, \Delta t = 14 \implies t_{1/2} = 33.7$ 天（Warning）；
  - 固定数值夹具 3：$S_{\text{current}} = 6.0, S_{\text{baseline}} = 12.0 \implies \text{KRR} = 50.0\%, \Delta t = 14 \implies t_{1/2} = 14.0$ 天（Danger）；
  - 断言 `outputs/decay_healing_pack/` 下 3 份自愈文件物理存在；
  - 断言 20 号报告包含沙箱免责话术「沙箱仿真不可替代真实大模型联网 API 实盘审计」；
  - 断言 API 鉴权拦截（未授权 401）与 `/report` 无文件返回 404。
- [ ] 5.2 运行全库单元测试，确保 100% 通过（当前已有 73 组，新增后将达 79+ 组单测全绿）。
- [ ] 5.3 在 `review-log.md` 记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
