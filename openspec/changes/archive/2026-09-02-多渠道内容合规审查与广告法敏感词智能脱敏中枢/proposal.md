# Proposal: 多渠道内容合规审查与广告法敏感词智能脱敏中枢 (Multi-Channel Content Compliance & Auto-Sanitization Engine)

## Why (为什么做 / 业务背景与痛点)

1. **分发平台风控与广告法极限词封禁风险**：
   - 企业在知乎专栏、今日头条、微信公众号、百家号发稿时，极易因“国家级”、“首选”、“行业第一”、“绝对保真”、“100%包赢”等词汇触发平台违禁词审查，导致被删帖、限流、扣分甚至封号；
2. **大模型 RAG 采纳降权风险**：
   - 包含虚假夸大或绝对化承诺的文章会被大模型质量评估模块（LLM Judge / Content Quality Filter）识别为低质营销垃圾，直接降低 Citation 权重；
3. **缺少自动化风控体检与一键无损脱敏替换机制**：
   - 目前人工审查各渠道发稿文案耗时耗力，亟需建立覆盖 P0 (新广告法极限词)、P1 (平台引流风控词)、P2 (行业过度承诺词) 的合规审查与一键智能无损脱敏（Auto-Sanitize）中枢。

---

## What Changes (改动范围)

1. **内容合规与风控脱敏核心引擎 (`tools/geo/compliance.py`)**：
   - `AUDIT_RULES_DB`：维护 P0 (广告法绝对化禁用词)、P1 (高危引流/违规夸大词)、P2 (机械/法律/餐饮等垂直行业违规承诺词) 词典与合规安全替换映射表；
   - `inspect_content_compliance(project_id: str, text: str = None) -> dict`：对项目全部交付物或指定文本进行合规审查，返回违规总数、合规得分（0~100）、违规段落行号与建议；
   - `sanitize_content_text(text: str, level: str = "all") -> tuple[str, list[dict]]`：执行一键智能无损替换，安全替换敏感极限词；
   - `sanitize_project_deliverables(project_id: str)`：一键批量脱敏修复该项目所有渠道发稿资产；
   - `render_compliance_report_markdown(project_id: str, comp: dict) -> str`：输出 `outputs/13_多渠道内容合规与广告法风控审查报告.md` 与 `outputs/compliance_inspection.json`；
2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
   - `geo compliance <pid> [--file <path>] [--sanitize]`
3. **服务端 API 与 Web 端大一统集成 (`tools/geo/server.py`, `web/index.html`)**：
   - 挂载 `GET/POST /api/projects/{id}/compliance/inspect` 与 `POST /api/projects/{id}/compliance/sanitize`；
   - Web 端 Step 4 矩阵发稿中心接入「🛡️ 内容合规与广告法风控审查」弹窗与一键脱敏。

---

## Capabilities (对外能力)

- **多级别多行业敏感词扫描**：定位违规行号与敏感短语；
- **一键智能无损脱敏**：安全替换为符合广告法与大模型偏好的高权威表达；
- **全渠道发稿零违规保障**：确保各平台 100% 顺利过审与收录。

---

## Impact (影响分析)

- 保障多渠道借壳发稿 100% 安全合规，避免客户因发稿封号遭受商业损失。

