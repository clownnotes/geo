# Design: 阶段一体检真抓后千问解读

## 数据流

```
run_audit
  → inspect_website (urllib)
  → compute_tech_score
  → write audit_metrics.json
  → load_probe_snapshot (optional)
  → call_llm_api (optional, narrative only)
  → generate_audit_report(metrics, narrative|fallback)
  → 01_…报告.md
```

## audit_metrics.json

```json
{
  "project_id": "nextgeo",
  "probed_at": "ISO8601",
  "url": "https://www.baicl.cc",
  "is_online": true,
  "status_code": 200,
  "html_size_kb": 35.6,
  "has_ssr": true,
  "has_llms_txt": true,
  "has_json_ld": true,
  "clean_text_length": 2519,
  "text_density_ratio": 6.91,
  "robots_status": "…",
  "warnings": [],
  "tech_score": 85,
  "llm_status": "ok|skipped|failed",
  "llm_provider": "nextdoor|none",
  "probe_baseline_id": "probe:doubao:…"
}
```

## LLM 约束

- 输入：metrics JSON + business_one_liner + 竞品/词库摘要 + probe briefs（若有）。
- 输出：Markdown 片段（结论 / 缺口优先级 / 四步建议）；禁止改写 has_* 布尔与 tech_score。
- 超时：60s；失败不阻断技术报告。

## UI

- 阶段一文案：技术分来自真抓；商业段来自小毛驴或「未接通」。
- 「一键复制给 IDE」：metrics 摘要 + 报告路径 + 润色提示词。
