# Tasks: 全网主流AI爬虫真实访问捕获与真机抓取日志审计中枢 (第 31 维)

## 1. 爬虫特征库与通用日志解析引擎 (`tools/geo/spider_auditor.py`)

- [ ] 1.1 复用并扩充 `tools/geo/crawler.py` 的 UA 库，建立包含 10+ 厂商特征指纹的 `AI_SPIDER_REGISTRY`。
- [ ] 1.2 实现 `parse_access_log_line(line)` 与 `parse_access_log_file(filepath)`，支持标准 Nginx Combined 与常用日志格式提取 IP、时间、状态码、路径、User-Agent。
- [ ] 1.3 实现 `identify_ai_spider(user_agent)`，基于正则快速匹配大模型爬虫厂商及分类。

## 2. 确定性沙箱回放与指标审计算法 (`tools/geo/spider_auditor.py`)

- [ ] 2.1 实现 `SandboxLogGenerator` 确定性沙箱回放器：无日志文件时，基于项目配置生成覆盖各爬虫的确定性合规模拟访问日志流，保证单测 100% 毫秒级稳定。
- [ ] 2.2 实现 `audit_spider_access(project_id, log_file=None)` 核心审计算法：计算总命中数、独立厂商数、200/403/404 状态码分布、核心资产（`/llms.txt`、`/schema.jsonld`）抓取覆盖率与健康度评级。

## 3. 公文 31 号生成与结构化落盘 (`tools/geo/spider_auditor.py`)

- [ ] 3.1 编写 `generate_report_31_markdown(audit_data)`：遵循普林斯顿 9 因子标准排版，包含结论先行、各厂商爬虫分布表格、核心资产抓取矩阵、阻断风险排查建议与电子防伪签署。
- [ ] 3.2 审计完成后自动原子落盘：`outputs/spider_access_audit.json` 与 `outputs/31_全网主流AI爬虫真实访问捕获与真机抓取日志审计报告.md`。

## 4. CLI 扩展与 Web 后端 API (`tools/geo/cli.py` & `tools/geo/server.py`)

- [ ] 4.1 在 `tools/geo/cli.py` 中注册 `spider-audit` 子命令，支持 `--log-file` 与 `--report` 参数，提供高保真终端彩色输出大屏。
- [ ] 4.2 在 `tools/geo/server.py` 中挂载 `POST /api/projects/{id}/spider-audit/run` 路由（Bearer Token 强鉴权）与 `GET .../spider-audit/status`、`GET .../spider-audit/report`。

## 5. 高管只读交付门户联动 (`tools/geo/share.py` & `web/share.html`)

- [ ] 5.1 在 `tools/geo/share.py` 的 `compile_portal_data()` 中挂载 `spider_access_summary` 字典；无数据时严格以 `status: "never_run"` 优雅降级，并在 `files_to_read` 挂载 31 号报告。
- [ ] 5.2 在 `web/share.html` 新增【全网主流 AI 爬虫真实到访心跳流与资产抓取大屏】卡片与技术明细抽屉中的 ⑦ 爬虫日志审计 Tab。

## 6. 自动化单元测试与全量回归 (`tests/test_spider_auditor.py`)

- [ ] 6.1 编写 `test_spider_identification`：覆盖主流 10 大模型爬虫 User-Agent 识别测试。
- [ ] 6.2 编写 `test_log_parsing_and_metrics`：验证 Nginx Combined 格式解析、状态码计算与核心资产覆盖率。
- [ ] 6.3 编写 `test_sandbox_fallback`：验证无日志文件时沙箱自动降级并秒级产出结构化审计账本。
- [ ] 6.4 编写 `test_portal_integration_and_never_run`：验证高管门户联动与 `never_run` 降级契约。
- [ ] 6.5 编写 `test_api_auth_gate`：验证 Web 端路由的 Bearer Token 强鉴权保护。
- [ ] 6.6 运行全库单元测试，确保全库测试 100% 秒绿（0 errors, 0 failures），并验证 VitePress SSG 构建零报错。

