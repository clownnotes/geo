# Tasks: 阶段一体检真抓后千问解读

- [x] 1. `audit.py`：`compute_tech_score` + `save_audit_metrics` 落盘 `audit_metrics.json`
- [x] 2. `audit.py`：报告技术表只读 metrics；去掉假关键词排名；引用 probe 摘要
- [x] 3. `audit.py`：接通 `call_llm_api` 解读；失败/未配置降级标注
- [x] 4. `web/index.html`：阶段一文案 +「一键复制给 IDE」
- [x] 5. `docs/sop/01-audit-sop.md`：同步真抓 + 小毛驴分层说明
- [x] 6. 单测 `tests/test_audit.py`：metrics / LLM mock 成功失败 / 无假排名
- [x] 7. nextgeo 本地 `geo audit` 验收（真抓成功；JWT 401 时降级）
