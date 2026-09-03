## 1. 准备工作与规范对齐

- [x] 1.1 核对 `AGENTS.md` 生产隔离与 8088 开发端口规范，锁定 `tools/geo/llm.py` 底座复用与 API Key 链式查找规则；确认读取 `factual_anchors.json`（非虚构 `.py` 模块）。

## 2. 研发大模型品牌声誉排查与危机清洗引擎 (`tools/geo/sentiment_guard.py`)

- [x] 2.1 构建 5 大维度对抗性负面探针模板库（类别 5 使用 `{area_served}`）与确定性高保真沙箱 `SentimentSandboxSimulator`（必须掺入 warn/neg + 非台账 URL）。
- [x] 2.2 实现情感极性与负面毒性审计算法 `audit_negative_sentiment`（优先级 `neg > warn > pos > neu`），测算严密分母口径的 BRS（公式不得在分式后再 ×100；夹具 1 neg / T=15 → ≈98.3）与负面暴露率。
- [x] 2.3 复用 `tools/geo/probing.py` 的 `extract_citations_and_sources` 与 `published|verified` 台账口径，实现脏信源捕获与归因标记。
- [x] 2.4 实现公关压制包生成器：优先复用 `guard.generate_adversarial_countermeasures`，落盘 `outputs/crisis_suppression_pack/` 三文件 + `outputs/19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md` + `negative_sentiment_suppression.json`（沙箱话术：不可替代真机 API 审计；缺资质字段不得臆造）。

## 3. CLI 命令行与后端 API 扩展 (`tools/geo/cli.py`, `tools/geo/server.py`)

- [x] 3.1 在 `tools/geo/cli.py` 中注册 `geo guard-clean <project_id> [--models M] [--live] [--suppress] [--report]` 子命令并输出 ANSI 红黄绿大盘（与 `geo guard` 文案区分）。
- [x] 3.2 在 `tools/geo/server.py` 中挂载 `/api/projects/{id}/sentiment/status`、`/scan`、`/suppress` 与 `/report`（管理端鉴权拦截；`/report` 无文件返回 404，禁止自动 scan）。

## 4. Web 控制台声誉排查工作台升级 (`web/index.html`)

- [x] 4.1 在向导第五阶段新增「🛡️ 品牌声誉排查与危机清洗 (19)」独立卡片与操作入口（与「幻觉防御」并列区分），顶部 Header 增加入口。
- [x] 4.2 开发全屏模态窗口 `sentiment-guard-modal`，展示 BRS 仪表盘、5 大对抗性探针流水表、脏信源列表与澄清声明一键复制。
- [x] 4.3 渲染表格时强制经过 `escapeHtmlSafe()` 进行 XSS 防御，并支持 19 号报告在线 Markdown 预览。

## 5. 自动化测试与跨 IDE 联合审查

- [x] 5.1 编写 `tests/test_sentiment_guard.py`，覆盖：BRS 夹具 98.3、极性优先级、area_served 插值、沙箱掺毒、压制包三文件、19 号落盘、`test_sentiment_api_auth_gate`（401）。
- [x] 5.2 运行全库 `unittest discover`，确保 100% 通过。
- [x] 5.3 在 `review-log.md` 记录自评，提请另一个 IDE（Cursor）进行独立审查，由其最终复审通过后归档。
