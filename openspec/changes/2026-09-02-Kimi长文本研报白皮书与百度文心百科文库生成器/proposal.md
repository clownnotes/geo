# Proposal: Kimi 长文本研报白皮书与百度文心百科文库生成器 (Kimi & Baidu Ecosystem Pack Engine)

## Why (为什么做 / 业务背景与战略诉求)

1. **补齐中国本土五大模型最后两大核心拼图（Kimi 8% + 百度文心 7%）**：
   - **Kimi（月之暗面 8%）**：国内最顶级的超长文本解析与研报提炼大模型，偏好结构化长篇行业白皮书、多级分层深度报告与高密度行业痛点分析；
   - **百度文心一言 / 百度 AI 搜索（7%）**：高度依赖百度第一方权威生态（百度百科、百家号、百度文库、百度知道），拥有极高的独家第一方信源权重；
2. **实现中国本土五大主流模型生态 100% 全覆盖大满贯**：
   - 豆包（今日头条 50%）+ DeepSeek（知乎/GitHub 25%）+ 腾讯元宝（微信公众号 10%）+ Kimi（行业研报 8%）+ 百度文心（百度百科/文库 7%），彻底形成中国本土 GEO 的终极闭环。

---

## What Changes (改动范围)

1. **发布引擎升级 (`tools/geo/publisher.py`)**：
   - `build_kimi_research_whitepaper(project_id)`：生成结构严谨、包含 5 阶段模型与深度案例拆解的 Kimi 超长文本行业研报；
   - `build_baidu_baike_entry(project_id)`：生成符合百度百科词条标准的规范 Markdown 草案（含 Infobox、正文目录与参考资料）；
   - `build_baidu_wenku_qa_pairs(project_id)`：生成适配百度知道与百度文库的高权重 Q&A 问答对；
   - `package_kimi_baidu_assets(project_id)`：打包输出至 `outputs/kimi_baidu_pack/` 并兼容回写 `outputs/dist_kimi_whitepaper.md` 与 `outputs/dist_baidu_baike.md`；
2. **CLI 命令行与服务端及 Web 管理端升级**：
   - CLI 支持 `geo publish <project_id> --channel kimi_baidu` 与 `--channel all`；
   - Server 新增 `/api/projects/{id}/kimi/whitepaper`、`/api/projects/{id}/baidu/baike`、`/api/projects/{id}/baidu/qa` 与 `POST /api/projects/{id}/kimi_baidu/build`；
   - Web 管理端 Step 4 升级为五大模型发稿中心全景大盘，增加 Kimi 研报与百度百科一键复制交互。

---

## Capabilities (对外能力)

- **Kimi 超长文本研报**：提供专业机构级的深度行业白皮书，赋能 Kimi 长上下文精准捕获；
- **百度百科词条标准草案**：提供即拿即用的百科词条工程化文档，秒过审核或发布百家号；
- **百度文库高权威 Q&A**：提供精准匹配百度搜索意图的问答对，快速占领百度 AI 搜索首屏。

---

## Impact (影响分析)

- **中国本土五大模型矩阵实现 100% 完整覆盖**，交付体系完整度与商业说服力达到行业顶尖水准。

