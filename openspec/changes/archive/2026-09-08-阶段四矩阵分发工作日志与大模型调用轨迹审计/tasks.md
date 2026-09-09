## 1. 准备工作与规范对齐

- [x] 1.1 核对 AGENTS.md 规范（0 Emoji 违规、DOM 标签完全闭合、阶段隔离与单步停步铁律）。

## 2. 后端数据采集与接口开发

- [x] 2.1 在 `tools/geo/distribute.py` 中构建 `DistributeRunTracker` 审计收集器，对各平台文案生成进行精细计时（毫秒级），捕获完整 System/User 提示词、小毛驴模型标识（Nextdoor `provider/brand/mode`，**不含 JWT / 完整 base_url**）及大模型原生回复；LLM 失败走 fallback 时 `status=fallback`。
- [x] 2.2 完善产物元数据收集（文件名、大小、字符数）；在 `server.py` 的 `distribute` 级联 `package_all_channels` **之后**补记 `*_pack` 就绪态，并将单次执行数据安全落盘至 `outputs/distribute_run_log.json`（`try-except` 容错隔离，失败不挡主流程）。
- [x] 2.3 在 `tools/geo/server.py` 中新增 `GET /api/projects/{id}/distribute/latest-log` API 端点，支持前端异步按需读取；响应中的 `llm_runtime.base_url_host` 必须脱敏。
- [x] 2.4 （安全）审计落盘与 API 输出禁止包含 `NEXTDOOR_JWT_TOKEN` 或任何 Bearer 密钥明文。

## 3. 前端界面与模态弹窗开发

- [x] 3.1 在 `web/index.html` 阶段四标题栏下方（红框区域）新增 `#distribute-run-status-bar` 状态指示条，支持展示最新运行概要（总耗时、模型、产物数与查看日志按钮）。
- [x] 3.2 在 `web/index.html` 构建沉浸式模态弹窗 `#distribute-log-modal`，划分 3 大核心区域（运行度量概览、生成资产列表、大模型调用详情与提示词复盘）；长文本默认截断预览。
- [x] 3.3 实现交互逻辑（`loadDistributeRunLog`、`openDistributeLogModal`、`closeDistributeLogModal`、复制按钮提示），并绑定**幂等**全局 `ESC` 键盘事件与遮罩点击关闭机制。
- [x] 3.4 在阶段四切换与生成完成回调中自动联动刷新日志指示条。

## 4. 验证与回归测试

- [x] 4.1 编写并运行自动化测试验证 `distribute_run_log.json` 写入及 API 响应正确性。
- [x] 4.2 执行 DOM 闭合检查（`open_divs == close_divs`）与 Emoji 违规排查。
- [x] 4.3 在本地开发环境（8088 端口）进行端到端全链路真实点击验证。
