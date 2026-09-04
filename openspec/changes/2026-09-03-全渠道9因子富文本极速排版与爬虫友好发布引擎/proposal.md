# Proposal: 全渠道 9 因子富文本极速排版与爬虫友好发布引擎

## Why (为什么做)
1. **大模型爬虫解析断层，直接破坏搜索召回质量**：
   - 系统前期（03/04/17 维）已能产出极高信息密度的普林斯顿 9 因子语料（包含精确量化数据表、权威信源引用、三元组对照）；
   - 但在向今日头条、知乎专栏、微信公众平台等外部渠道分发时，手动复制 Markdown 会导致表格破损、引用角标格式丢失；
   - 尤为致命的是：各平台公网渲染后的 HTML 若混乱无序，主流大模型爬虫（字节 Bytespider、百度 Baiduspider 等）提取 Clean Markdown 时就会变成碎片散乱文本，使得普林斯顿 9 因子在大模型 RAG 召回阶段彻底降权失效。
2. **一线代运营发稿 SOP 效率低下（最后一公里严重堵塞）**：
   - 代运营团队在分发语料时，若逐个平台手动微调排版、设置内联样式，每篇耗时 30~60 分钟；
   - 必须提供“10 秒内一键将 9 因子 Markdown 转换为各大内容平台原生富文本，一键写入剪贴板（Ctrl+V 完美粘贴）”的杀手级工具。
3. **多平台差异化排版规范缺乏统一编译器**：
   - 微信公众平台需要纯 Inlined CSS（不支持外部 `<style>`）；
   - 知乎专栏需要高对比度引用块与学术感强烈的参数对比表；
   - 今日头条需要微头条短动态胶囊与头条号文章排版结构。市面上通用 Markdown 转换工具完全不具备 GEO 领域的“爬虫逆向保真度”验证能力。

## What Changes (改动了什么)
1. **研发 `RichPublisherEngine` 核心引擎 (`tools/geo/rich_publisher.py`)**：
   - **全渠道内联样式编译器**：内置针对 `wechat`（微信公众平台）、`zhihu`（知乎专栏）、`toutiao`（今日头条）的三大差异化 Inlined CSS 样式系统；
   - **9 因子语义结构增强**：自动为量化数据注入高对比度卡片、为权威信源注入角标锚点、为专家观点注入权威引言卡、为对比矩阵注入移动端自适应表格；
   - **大模型爬虫保真度逆向检验器**：内置 AI 爬虫清洗仿真算法，检验生成的富文本在经过 `html2text` 清洗后是否能 100% 还原高保真数据表格与引用，计算输出 `Crawler Fidelity Score`；
   - **全渠道资产一键导出**：一键生成全渠道排版资产包落盘至 `projects/<id>/outputs/rich_publish_pack/`。
2. **新增 CLI 命令 (`tools/geo/cli.py`)**：
   - 新增 `geo rich-pub` 命令，支持 `--project <id>`、`--channel wechat|zhihu|toutiao|all` 与 `--verify`。
3. **扩展 Web 控制台与一键富文本复制工作台 (`tools/geo/server.py` & `web/index.html`)**：
   - 新增 API 路由：`GET /api/project/:id/rich-publish-preview` 与 `POST /api/project/:id/rich-publish-compile`；
   - Web 界面新增【全渠道 9 因子富文本极速发布工作台】模态弹窗，提供三端实时手机/桌面双模预览，并支持通过浏览器 Clipboard API 一键将带内联样式的 Rich HTML 写入剪贴板，代运营直接在各平台后台 Ctrl+V 粘贴即可无损发布。
4. **单元测试与质量验证**：
   - 新建 `tests/test_rich_publisher.py`，全量覆盖各平台内联编译、9 因子增强识别、爬虫保真度算法及 CLI/API。

## Capabilities (新增或修改的对外能力)
- `geo rich-pub --project <id> [--channel all] [--verify]`：一键全渠道排版并验证爬虫保真度；
- `GET /api/project/:id/rich-publish-preview?channel=wechat`：获取微信/知乎/头条内联 HTML 预览与保真度元数据；
- `POST /api/project/:id/rich-publish-compile`：触发全渠道发布资产重构编译；
- Web 端极速富文本复制（`navigator.clipboard.write([new ClipboardItem({'text/html': ...})])`），10 秒完成专业发稿准备。

## Impact (受影响的部分)
- **新增模块**：`tools/geo/rich_publisher.py`，`tests/test_rich_publisher.py`；
- **修改模块**：`tools/geo/cli.py`（增加 `rich-pub` 命令），`tools/geo/server.py`（增加预览与编译 API），`web/index.html`（增加富文本发布工作台模态框及对应 CSS/JS）；
- **基线影响**：原有 122 组单元测试完全兼容不受影响，新增 6~8 组单测，测试基线扩充至 128+ 组且秒绿。
