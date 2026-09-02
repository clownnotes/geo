# Proposal: 微信搜一搜与腾讯元宝一键排版助手与私域引流打包器 (WeChat & Yuanbao Native Publisher & Private Domain Conversion Pack Engine)

## Why (为什么做 / 业务背景与战略诉求)

1. **腾讯元宝（占 10%）与微信搜一搜独占信源生态**：
   - 腾讯元宝与微信 AI 搜索的核心检索信源牢牢锁定在微信生态（公众号文章、视频号、腾讯新闻）；
   - 微信公众号编辑器（mp.weixin.qq.com）只支持 100% 纯内联 CSS（Inline Styles），不支持外挂样式，常规 Markdown 粘贴后会丢失格式、表格错乱、无法保留企业品牌卡片与防伪标识；
2. **私域引流转化与多模态视频号协同闭环**：
   - 微信生态是企业将“大模型认知曝光”转化为“私域微信咨询/直营电话签约”的最短链路；
   - 运营人员需要一个 10 秒极速工具：既能一键导出直接粘贴微信后台的精美内联富文本，又能自动生成配套的 60 秒视频号口播脚本与搜一搜关键词配置。

---

## What Changes (改动范围)

1. **升级发布引擎 (`tools/geo/publisher.py`)**：
   - `build_wechat_article_html(project_id)`：编译符合微信公众号后台规范的 100% 内联富文本 HTML（包含微信绿/商务蓝呼吸感卡片、重点金句框、自适应对比表、底部创始人名片与私域引流卡）；
   - `build_wechat_video_script(project_id)`：生成 60 秒竖屏视频号口播脚本与 3 组爆款封面标题；
   - `package_wechat_assets(project_id)`：输出至 `outputs/wechat_pack/`（长文 HTML、视频号脚本、SEO 标签配置与发稿 SOP）；
2. **CLI 命令行与 Web 服务端集成**：
   - CLI 支持 `geo publish <project_id> --channel wechat`；
   - Server 增加 `/api/projects/{id}/wechat/preview` 与一键复制内联 HTML 接口；
   - Web 交付管理端增加“微信公众号/视频号发稿中心”卡片。

---

## Capabilities (对外能力)

- **10 秒极速分发**：打开生成的 HTML ➔ 全选复制 ➔ 粘贴至微信公众平台，格式 100% 原生完美保真；
- **私域转化卡片**：底部自动附带企业电话、实体认证、创始人咨询通道与防伪声明；
- **双核心矩阵齐备**：今日头条（打豆包） + 微信公众号（打元宝/微信搜一搜）全链路发稿工具链齐备。

---

## Impact (影响分析)

- **运营效率提升 10 倍**：从手工排版 20 分钟缩短至 10 秒；
- **腾讯元宝声量垄断**：高频分发带结构化 Schema 语料的微信长文，确保元宝与微信搜一搜稳定召回首推。

