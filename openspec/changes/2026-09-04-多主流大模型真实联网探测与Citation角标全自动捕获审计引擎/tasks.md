# Tasks: 多主流大模型真实联网探测与 Citation 角标全自动捕获审计引擎 (第 30 维)

## 1. 核心探测与反查引擎实现 (`tools/geo/live_auditor.py`)

- [ ] 1.1 实现多模型客户端矩阵与确定性沙箱降级调度：支持豆包、DeepSeek、腾讯元宝、月之暗面 Kimi 的 OpenAI 兼容协议与超时重试，无密钥或 `--sandbox` 时自动启用高保真确定性测试数据。
- [ ] 1.2 实现 Citation 引用角标与来源提取器：正则解析正文 Markdown 链接 `[标题](URL)`、裸 URL、标注角标 `[1]` / `【1】` 及文末 Sources/References 来源列表，并规范化清洗 URL 协议与主机名。
- [ ] 1.3 实现分发存活台账 (`dist_ledger.json`) 反向核验与集合对账算法：精准匹配发布 URL、主阵地渠道域名（toutiao/zhihu/github/weixin/官网），输出 `dist_matched_count` 与真实采纳率 `citation_hit_rate`。
- [ ] 1.4 实现公文级报告与审计台账原子落盘：输出 `outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md` 与结构化 `outputs/live_citation_audit.json`。

## 2. CLI 命令挂载与交互实现 (`tools/geo/cli.py`)

- [ ] 2.1 注册顶级 `geo probe-audit` 子命令（别名 `geo citation-audit`），支持 `--models`、`--limit`、`--sandbox`、`--reconcile-only` 参数解析。
- [ ] 2.2 实现美观的终端控制台输出体验：包含启动 Banner、探测进度条、以及声量/角标采纳/报告落盘标准三行摘要。

## 3. Web 后端路由与高管门户数据联动 (`tools/geo/server.py` & `tools/geo/share.py`)

- [ ] 3.1 在 `server.py` 挂载 `POST /api/projects/{id}/citation-audit/run` 与 `GET /api/projects/{id}/citation-audit/report`，实施与既有项目相同的 Bearer Token 强鉴权保护。
- [ ] 3.2 在 `share.py` 的 `compile_portal_data()` 中挂载 `live_citation_summary` 字段，审计缺失时严格降级为 `status: "never_run"`，杜绝伪造数据。

## 4. 自动化单元测试与端到端回归 (`tests/test_live_auditor.py`)

- [ ] 4.1 编写模型调用与优雅降级单测：断言在无环境变量 API Key 时秒级平滑切入沙箱，数据结构完整无崩溃。
- [ ] 4.2 编写 Citation 正则解析与 URL 清洗单测：覆盖内联链接、角标注释、文末信源以及参数剥离。
- [ ] 4.3 编写分发台账对账单测：沙箱比对 `dist_ledger.json`，断言命中与未命中集合划分准确。
- [ ] 4.4 编写 CLI 子命令与参数解析单测。
- [ ] 4.5 编写 Web 路由鉴权保护与高管门户数据联动单测（覆盖 `never_run` 与 `audited` 两态）。
- [ ] 4.6 运行全库单元测试，确保包含新单测在内的全库测试 100% 秒绿通过，且 VitePress SSG 构建零报错。

