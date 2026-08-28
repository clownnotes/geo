## 1. 准备工作与项目脚手架

- [ ] 1.1 确认 Python 环境依赖配置（`requirements.txt`），规划 `tools/geo` 目录架构。
- [ ] 1.2 创建客户项目模板工作区 `projects/_template/` 与基础配置文件规范。

## 2. 商业化交付核心程序开发 (`tools/geo/`)

- [ ] 2.1 编写 CLI 总调度入口 `tools/geo/cli.py` 与 `tools/geo/__main__.py`。
- [ ] 2.2 编写阶段一【诊断体检器】`tools/geo/audit.py`：实现爬虫视角抓取体检、基准词搜索比对并自动输出《企业 AI 可见度诊断报告》。
- [ ] 2.3 编写阶段二【底座脚手架】`tools/geo/scaffold.py`：实现一键自动生成合规 `llms.txt`、Schema.org (JSON-LD) 实体元数据与 `robots.txt` 放行配置。
- [ ] 2.4 编写阶段三【内容重构流水线】`tools/geo/rewrite.py`：支持批量文档解析与普林斯顿 9 因子结构化重构（三元组/数据对比表/Q&A 对）。
- [ ] 2.5 编写阶段四【矩阵分发适配器】`tools/geo/distribute.py`：实现今日头条、知乎、掘金、微信公众号与 GitHub 专属 Markdown 发布包导出。
- [ ] 2.6 编写阶段五【自动化监控引擎】`tools/geo/monitor.py`：实现主流 LLM 并发检索、品牌提及与引用分析、周报/月报 Markdown 导出。

## 3. 标准化商用交付 SOP 手册与模版建设 (`docs/sop/`)

- [ ] 3.1 编写 `docs/sop/01-audit-sop.md`（售前获客与现状诊断 SOP，含报价与立项模板）。
- [ ] 3.2 编写 `docs/sop/02-scaffold-sop.md`（站点底座改造交付 SOP，含技术交接与验收标准）。
- [ ] 3.3 编写 `docs/sop/03-rewrite-sop.md`（普林斯顿 9 因子内容重构与质检打分 SOP）。
- [ ] 3.4 编写 `docs/sop/04-distribute-sop.md`（全网高权重渠道借壳分发 SOP 与规范）。
- [ ] 3.5 编写 `docs/sop/05-monitor-sop.md`（AI 可见度监控与续费周报交付 SOP）。

## 4. 体系测试与端到端实操演练

- [ ] 4.1 使用示例客户项目（`projects/demo_corp`）端到端跑通从 `audit`、`scaffold`、`rewrite`、`distribute` 到 `monitor` 的完整五步流水线。
- [ ] 4.2 验证生成报告、底座补丁与重构语料的合规性与实用性。

