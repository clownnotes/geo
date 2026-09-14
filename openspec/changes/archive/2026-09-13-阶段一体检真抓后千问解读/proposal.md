# Proposal: 阶段一体检真抓后千问解读

## Why

阶段一「执行测算体检」已能用 Python 真抓官网技术指标，但客户报告仍混有模板套话与历史 Day 0 离线叙事；商业解读层未接小毛驴，质量与可信度不足。需要「硬指标真抓 + 大模型只写解读」分层，避免模型伪造技术检测结果。

## What

- 落盘 `outputs/audit_metrics.json` 作为技术真源（SSR / llms.txt / JSON-LD / 文本密度 / robots / tech_score）。
- `01_企业AI可见度现状体检与商业诊断报告.md`：技术表只读 metrics；结论与建议由小毛驴（Nextdoor LLM）生成；失败则降级为「仅真抓」报告并明示。
- 可见度表引用阶段零 probe（若有），禁止假排名。
- 管理台阶段一：执行 = 真抓 +（可选）解读；增加「一键复制给 IDE」二次精修。

## Capabilities

- `geo audit` / 管理台 `run/audit` 产出 metrics + 报告双层产物。
- 配置沿用 `NEXTDOOR_JWT_TOKEN` + `NEXTDOOR_BASE_URL`（小毛驴）。

## Impact

- `tools/geo/audit.py`、阶段一 UI、SOP-01、单测。
- 不改阶段零探测逻辑；不推生产。
