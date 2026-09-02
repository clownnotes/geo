# Proposal: 豆包（今日头条与微头条）一键发稿排版助手与图文打包器 (Doubao & Toutiao Rich Publisher & Media Packager)

## Why (为什么做 / 业务背景与商业痛点)

1. **豆包第一主战阵地（头条系权重 50%）发稿人效瓶颈**：
   - 战略白皮书明确指出：豆包最核心的数据索引源来自今日头条长文（2000 字深度白皮书）、微头条短动态（150 字金句）与抖音图文；
   - 目前系统虽然生成了 Markdown 文档与短文本，但运营人员在向今日头条创作者后台（mp.toutiao.com）发稿时，Markdown 中的表格容易变形、标题层级丢失、引用样式单调；
   - 运营人员需要花费 15~20 分钟进行手动排版、配图与格式整理，严重制约了规模化分发和存活台账的持续回填。
2. **需要一个“10秒极速发稿”的富文本排版与图文打包引擎**：
   - 将普林斯顿 9 因子语料自动编译为符合今日头条后台编辑器格式的现代化富文本（带呼吸感卡片、自适应表格、加粗金句）；
   - 支持一键打包 150 字微头条文本与配套 1:1/4:3 高清信息图，提供 Web 端一键复制富文本和 ZIP 下载能力。

---

## What Changes (改动范围)

1. **新增发稿排版与图文打包中枢 (`tools/geo/publisher.py`)**：
   - `build_toutiao_article_html(project_id)`：将 9 因子语料编译为头条专属兼容富文本 HTML；
   - `build_toutiao_micro_post(project_id)`：生成 3 组不同角度的 150 字强观点微头条文案；
   - `package_toutiao_assets(project_id)`：自动将文章 HTML、微头条文本与 SVG/PNG 对比图打包至 `outputs/toutiao_pack/`；
2. **CLI 与 Web 端功能集成**：
   - CLI 新增 `geo publish <project_id> --channel toutiao`；
   - Web 端交付管理界面新增“头条极速发稿中心”模块，支持富文本一键复制到剪贴板。

---

## Capabilities (新增或修改的对外能力)

- **`geo publish <project_id> --channel toutiao`**：一键生成头条发稿富文本与图文包；
- **Web 端一键 Copy Rich HTML**：运营人员点击按钮直接粘贴到今日头条后台，排版完美保真；
- **微头条 150 字三维攻防文案**：自动输出决策人篇、价格透明篇、同城避坑篇 3 组微头条。

---

## Impact (影响分析)

- **发稿人效提升 10 倍**：单篇头条发稿从 15 分钟缩短至 15 秒；
- **豆包大模型收录率大幅提升**：富文本表格与结构化标题利于头条爬虫秒级解析。

