## 1. 准备工作与规范对齐

- [ ] 1.1 核对 `AGENTS.md` 生产隔离与 8088 开发端口规范，锁定 `tools/geo/llm.py` 底座复用与 API Key 链式查找规则。

## 2. 研发大模型品牌声誉排查与危机清洗引擎 (`tools/geo/sentiment_guard.py`)

- [ ] 2.1 构建 5 大维度对抗性负面探针模板库与确定性高保真沙箱模拟器 `SentimentSandboxSimulator`。
- [ ] 2.2 实现情感极性与负面毒性审计算法 `audit_negative_sentiment`，测算严密分母口径的 BRS 声誉健康度得分与负面暴露率。
- [ ] 2.3 复用 `tools/geo/probing.py` 的 `extract_citations_and_sources`，实现脏信源捕获与归因标记。
- [ ] 2.4 实现公关事实澄清与正向压制包生成器 `generate_crisis_suppression_pack`（生成 `outputs/crisis_suppression_pack/` 下 3 份澄清声明、选型白皮书与资质集），并规范落盘 `outputs/19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md` 与 `negative_sentiment_suppression.json`。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [ ] 3.1 在 `tools/geo/cli.py` 中注册 `geo guard-clean <project_id> [--models M] [--live] [--suppress] [--report]` 子命令并输出 ANSI 红黄绿大盘。
- [ ] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/sentiment/status`、`/api/projects/{id}/sentiment/scan`、`/api/projects/{id}/sentiment/suppress` 与 `/api/projects/{id}/sentiment/report`（管理端鉴权拦截）。

## 4. Web 控制台声誉排查工作台升级 (`web/index.html`)

- [ ] 4.1 在向导第五阶段新增「🛡️ 品牌声誉排查与危机清洗 (19)」独立卡片与操作入口，顶部 Header 增加入口。
- [ ] 4.2 开发全屏模态窗口 `sentiment-guard-modal`，展示 BRS 仪表盘、5 大对抗性探针流水表、脏信源列表与澄清声明一键复制。
- [ ] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御，并支持 19 号报告在线 Markdown 预览。

## 5. 自动化测试与跨 IDE 联合审查

- [ ] 5.1 编写 `tests/test_sentiment_guard.py`，全量覆盖沙箱降级、5 类对抗性探针、情感极性判断、BRS 分母公式、`outputs/crisis_suppression_pack/` 压制包生成及 19 号报告落盘。
- [ ] 5.2 运行全库单元测试，确保 100% 通过（66+ 组单测全绿）。
- [ ] 5.3 在 `review-log.md` 记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
