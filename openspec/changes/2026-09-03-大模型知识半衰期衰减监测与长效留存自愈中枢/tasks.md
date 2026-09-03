## 1. 准备工作与规范对齐

- [ ] 1.1 核对 `AGENTS.md` 生产隔离与 8088 端口规范，锁定 `tools/geo/llm.py` 底座复用、`tools/geo/probing.py` Citation 提取与 `factual_anchors.json` 真实档案读取规则。

## 2. 研发大模型知识半衰期衰减监测与自愈引擎 (`tools/geo/decay_monitor.py`)

- [ ] 2.1 构建确定性时间序列仿真沙箱 `DecaySandboxSimulator`（支持模拟 Day 1、Day 7、Day 14、Day 30 召回衰减，掺入衰减下滑 Query）。
- [ ] 2.2 实现知识留存率算法 `calculate_krr` 与指数半衰期预测模型 `estimate_half_life`（包含分母与边界安全防范，测算 KRR、$\lambda$ 与 $t_{1/2}$）。
- [ ] 2.3 复用 `tools/geo/probing.py` 与 `tools/geo/dist_bot.py`，实现当期意图探测与台账比对，判定红黄绿三级预警状态。
- [ ] 2.4 实现自愈补量刷新包生成器 `generate_decay_healing_pack`（生成 `outputs/decay_healing_pack/` 下 3 份强化清单、自愈草稿与推荐计划），并规范落盘 `outputs/20_大模型知识半衰期衰减监测与长效留存自愈报告.md` 与 `knowledge_decay_retention.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo decay <project_id> [--models M] [--live] [--heal] [--report]` 子命令并输出 ANSI 衰减时间序列大盘。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/decay/status`、`/api/projects/{id}/decay/track`、`/api/projects/{id}/decay/heal` 与 `/api/projects/{id}/decay/report`（管理端鉴权拦截；`/report` 无文件时严格返回 404，禁止自动后台计算）。

## 4. Web 控制台知识衰减与自愈工作台升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「⏳ 知识半衰期衰减与长效自愈 (20)」独立卡片与操作入口，顶部 Header 增加入口。
- [ ] 4.2 开发全屏模态窗口 `decay-monitor-modal`，展示 KRR 留存大字仪表盘、半衰期预测卡、各意图词衰减流水与一键自愈生成。
- [ ] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御，并支持 20 号报告在线 Markdown 预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_decay_monitor.py`，全量覆盖沙箱降级、KRR 留存率计算、半衰期公式边界断言、`outputs/decay_healing_pack/` 3 份自愈文件物理存在、20 号报告落盘及 API 鉴权/404 语义。
- [ ] 5.2 运行全库单元测试，确保 100% 通过（当前已有 73 组，新增后将达 79+ 组单测全绿）。
- [ ] 5.3 在 `review-log.md` 记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
