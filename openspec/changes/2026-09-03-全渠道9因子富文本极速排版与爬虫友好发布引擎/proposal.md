# Proposal: 全渠道 9 因子富文本极速排版与爬虫友好发布引擎 (第 27 维·修订版)

## Why (为什么做)
1. **大模型爬虫解析断层，直接破坏搜索召回质量**：
   - 系统前期（03/04/17 维）已能产出极高信息密度的普林斯顿 9 因子语料（包含精确量化数据表、权威信源引用、三元组对照）；
   - 但在向今日头条、微信公众平台、知乎专栏等外部渠道分发时，手动复制或简陋排版会导致公网 HTML 结构混乱；
   - 当主流大模型爬虫（字节 Bytespider、百度 Baiduspider 等）抓取并提纯 Clean Markdown 时，无序的 HTML 会导致表格瓦解、引用角标丢失，严重破坏普林斯顿 9 因子在大模型 RAG 召回与重排阶段的权重。
2. **一线代运营发稿 SOP 效率与保真度脱节**：
   - 现有系统在 `publisher.py` 中虽有部分渠道排版，但缺少统一的“发稿后大模型爬虫保真度逆向验证（Crawler Fidelity）”；
   - 运营人员无法确切知晓发布到外部平台的富文本在被 AI 爬虫抓取后，结构化数据还能保留多少百分比，急需在发稿中心集成“保真度即时雷达”与“一键富文本复制”。
3. **消除重复建设，深度复用既有工程底座**：
   - 严格遵循 Cursor 审查意见（P0 #1~#4）：**禁止另起炉灶建立平行的发稿引擎或新 CLI 命令**；
   - 全面依托并增强现有 `tools/geo/publisher.py` 与 `tools/geo/crawler.py`，打通“语料编译 ➔ 爬虫逆向保真度自检 ➔ 原生剪贴板复制 ➔ 既有发稿包落盘”的高内聚闭环。

## What Changes (改动了什么)
1. **增强大模型爬虫清洗引擎 (`tools/geo/crawler.py`)**：
   - 升级 `html_to_clean_markdown()` 函数，增加对 `<table>`、`<tr>`、`<th>`、`<td>` 结构化表格标签的清洗与原生 Markdown 表格转换支持，确保爬虫仿真能精确提纯表格数据。
2. **升级全渠道发稿引擎 (`tools/geo/publisher.py`)**：
   - **新增爬虫保真度逆向检验器** `verify_crawler_fidelity(html_or_md, project_id, channel)`：
     - 调用 `crawler.html_to_clean_markdown` 逆向提纯 Clean Markdown；
     - 量化评估：表格结构完整度（Table Integrity）、引用角标留存率（Citation Retention）、9 因子关键语义密度（Semantic Density）；
     - 输出综合评分 `Crawler Fidelity Score`（≥90 分为黄金级高保真）；
   - **增强各渠道富文本构建器**：
     - 在微信 (`build_wechat_article_html`)、头条 (`build_toutiao_article_html`) 编译中增强 9 因子高对比度卡片与角标；
     - 新增知乎专栏学术风富文本构建器 `build_zhihu_rich_article_html()`（与现网知乎 Markdown 资产互补并存）；
   - **升级既有打包流程**：
     - 在 `package_*_assets()` 中自动嵌入 `fidelity_report.json`，落盘于既有 `outputs/*_pack/` 目录中。
3. **扩展现有 CLI 命令 (`tools/geo/cli.py`)**：
   - 在现有 `geo publish` 子命令上追加 `--verify`（或 `--fidelity`）选项：
     - `./geo publish <id> --channel all --verify`
     - 打印全渠道爬虫保真度质量评估卡，评分低于 90 分给出明确优化告警。
4. **扩展 Web API 与现有发稿中心交互 (`tools/geo/server.py` & `web/index.html`)**：
   - API 遵循复数规范：
     - 在现有 `/api/projects/{id}/wechat/preview` 与 `/toutiao/preview` 响应中直接附加 `fidelity` 评估数据；
     - 新增统一预览入口 `/api/projects/{id}/publish/preview?channel=`；
   - 前端 Web 升级：
     - 升级既有的【Step 4 全生态发稿中心】，嵌入爬虫保真度健康评分徽标与【Clean MD 逆向透视】对比抽屉；
     - 复用现有的 `navigator.clipboard.write` 机制，保持单一界面入口，绝不新增重复模态框。
5. **单元测试与质量验证 (`tests/test_rich_publisher.py`)**：
   - 测试覆盖：`crawler.py` 的 HTML 表格清洗提纯、`publisher.py` 保真度评分算法、各渠道富文本内联样式断言、CLI `--verify` 与 API 返回。

## Capabilities (新增或修改的对外能力)
- `geo publish <id> [--channel all] [--verify]`：增强的既有发稿命令，支持可选爬虫保真度深度自检；
- `GET /api/projects/{id}/publish/preview?channel=wechat|toutiao|zhihu`：统一获取渠道富文本与保真度评分；
- 现网发稿中心前端直接显示“爬虫高保真度（如 96.8%）”与“逆向提纯 Markdown 视图”。

## Impact (受影响的部分)
- **核心修改**：`tools/geo/crawler.py`（增强表格提纯）、`tools/geo/publisher.py`（新增保真度核验与知乎富文本）、`tools/geo/cli.py`（增强 publish 参数）、`tools/geo/server.py`（扩展 publish API）、`web/index.html`（增强现有 Step 4 发稿中心）；
- **新增测试**：`tests/test_rich_publisher.py`；
- **完全兼容性**：绝不破坏原有 122 组单测；绝不创建平行的 `rich-pub` 命令与独立目录，资产落盘依然在既有的 `outputs/*_pack/` 中。
