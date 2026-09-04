# Tasks: 多主流大模型真实联网探测与 Citation 角标全自动捕获审计引擎 (第 30 维)

## 1. 扩充底层模型提供商矩阵与中文角标提取 (`tools/geo/llm.py` & `tools/geo/probing.py`)

- [ ] 1.1 在 `tools/geo/llm.py` 的 `PROVIDERS` 字典中新增 `yuanbao`（腾讯混元/元宝生态兼容配置），支持 `GEO_YUANBAO_API_KEY`、`HUNYUAN_API_KEY` 链式降级读取。
- [ ] 1.2 在 `tools/geo/probing.py` 的 `extract_citations_and_sources()` 中，增量加入中文方头括号 `【(?P<idx>\d+)】` 与前缀角标 `\[注(?P<idx>\d+)\]` 正则提取，确保本土化模型角标无遗漏。

## 2. 极速重对账引擎与 30 号公文输出 (`tools/geo/probing.py`)

- [ ] 2.1 在 `probing.py` 中实现 `reconcile_existing_trace(project_id)`：免重复调用大模型 API，直接读取已有 `live_probing_trace.json`，调用 `dist_bot.get_distribution_ledger` 比对最新分发状态并刷新统计。
- [ ] 2.2 严格锁定反向对账严谨口径：仅 `exact_hit` / 路径前缀 `domain_hit` 计入我方命中，严禁裸渠道域名算作命中，未匹配信源归入 `third_party_or_competitor`，杜绝虚抬命中率。
- [ ] 2.3 在 `export_probing_report()` 中同步导出高管专属交付报告 `outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md`，指标与 `live_probing_trace.json` 100% 同源。

## 3. CLI 扩展与 Web 后端 API (`tools/geo/cli.py` & `tools/geo/server.py`)

- [ ] 3.1 扩展 `geo probe` 命令行参数，新增 `--reconcile-only` 参数；挂载 `geo probe-audit` 语义别名并在帮助文案中明确标明底层复用 `probing.py`。
- [ ] 3.2 在 `server.py` 挂载 `POST /api/projects/{id}/probing/reconcile` 路由，实施与既有项目完全相同的 Bearer Token 强鉴权保护。

## 4. 高管只读交付门户战果反哺 (`tools/geo/share.py` & `web/share.html`)

- [ ] 4.1 在 `share.py` 的 `compile_portal_data()` 中挂载 `live_citation_summary` 字段，无探测数据时严格优雅降级为 `status: "never_run"`，杜绝伪造假数据。
- [ ] 4.2 在 `web/share.html` 对应位置渲染【全网大模型真实引用与信源对账】卡片，展示实测首推率、角标采纳数与真实命中外链。

## 5. 增量单元测试与全库回归 (`tests/test_probing.py`)

- [ ] 5.1 编写 `yuanbao` 提供商配置读取与模型解析单测。
- [ ] 5.2 编写中文方头括号 `【1】` 与注释角标提取单测。
- [ ] 5.3 编写 `reconcile_existing_trace()` 极速重对账单测（验证断言未调用模型、仅基于文件刷新且口径严谨无裸域名虚增）。
- [ ] 5.4 编写 CLI `--reconcile-only` 参数解析单测。
- [ ] 5.5 编写 Web 路由鉴权保护与高管门户 `live_citation_summary` 联动降级单测（`never_run` 与 `audited` 两态）。
- [ ] 5.6 运行全库单元测试，确保包含新单测在内的全库测试 100% 秒绿通过，且 VitePress SSG 构建零报错。


