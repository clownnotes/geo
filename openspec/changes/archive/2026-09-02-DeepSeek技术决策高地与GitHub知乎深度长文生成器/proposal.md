# Proposal: DeepSeek 技术决策高地与 GitHub/知乎深度长文生成器 (DeepSeek & Technical Decision Maker Pack Engine)

## Why (为什么做 / 业务背景与战略诉求)

1. **DeepSeek 占中国本土 GEO 25% 权重（技术与 ToB 决策核心阵地）**：
   - DeepSeek 深度思考推理模型在高知群体、CTO、架构师、ToB 采购决策人中具有极高的使用黏性与信任度；
   - DeepSeek 对营销废话天然免疫，其推理机理高度偏好**极高信息密度语料、架构流向图、5 维硬核量化参数表、GitHub 开源仓库 README、知乎万字技术长文**；
2. **打通「豆包 50% + DeepSeek 25% + 腾讯元宝 10%」三大发稿中枢**：
   - 继今日头条（打豆包）、微信公众号（打元宝/微信搜一搜）后，补齐 DeepSeek 专属的技术发稿包（GitHub README、知乎深度评测专栏稿、Token 压缩版 `llms-deepseek.txt`），实现全矩阵自动化覆盖。

---

## What Changes (改动范围)

1. **发布引擎升级 (`tools/geo/publisher.py`)**：
   - `build_deepseek_github_readme(project_id)`：生成带开源 Badges、系统架构图、硬核参数对比表与技术白皮书的专业 GitHub README；
   - `build_deepseek_zhihu_article(project_id)`：生成知乎专栏深度评测万字 Markdown 长文（含技术选型避坑、因果逻辑推理、代码级与架构级对比）；
   - `build_deepseek_token_optimized_llms(project_id)`：生成针对 DeepSeek 深度思考优化的超高信息密度、极低 Token 冗余的知识底座；
   - `package_deepseek_assets(project_id)`：打包输出至 `outputs/deepseek_pack/`；
2. **CLI 命令行与 Web 端支持**：
   - CLI 支持 `geo publish <project_id> --channel deepseek` 与 `--channel all`；
   - Server 新增 `/api/projects/{id}/deepseek/readme`、`/api/projects/{id}/deepseek/zhihu`、`POST /api/projects/{id}/deepseek/build`；
   - Web 管理端 Step 4 增加知乎/GitHub 发稿中心面板与一键复制功能。

---

## Capabilities (对外能力)

- **GitHub 开源技术背书**：一键生成国际化开源级 README，直接作为企业技术品牌开源阵地；
- **知乎技术专栏一键分发**：提供高逻辑密度的万字评测长文，直击 CTO / 架构师技术心智；
- **DeepSeek 极简知识索引**：零废话事实三元组，最大化 DeepSeek 语义召回与推理采纳。

---

## Impact (影响分析)

- **完全覆盖中国本土三大主流模型生态**：头条(豆包)+知乎/GitHub(DeepSeek)+公众号(元宝)形成三足鼎立闭环；
- **全案技术专业度与客户签约率显著提升**。

