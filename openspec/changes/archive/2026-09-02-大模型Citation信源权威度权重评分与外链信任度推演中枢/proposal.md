# Proposal: 大模型 Citation 信源权威度权重评分与外链信任度推演中枢 (Citation Source Authority & Backlink Trust Engine)

## Why (为什么做 / 业务背景与痛点)

1. **不同大模型对信源渠道的引用权重存在巨大生态偏好差**：
   - 豆包 (50%+) 极度偏好今日头条/微头条与抖音图文；
   - DeepSeek (25%+) 高度采纳知乎专栏技术长文与 GitHub 开源仓库；
   - 腾讯元宝 (10%+) 独占微信公众号与搜一搜文章；
   - Kimi 与百度文心更青睐长文档白皮书、百度百科与百家号；
2. **缺乏单条外链的权威度权重评级与被引用概率推演**：
   - 客户在各大平台发布外链后，无法量化判断该外链的“域名权重 (Domain Authority)”、“大模型亲和度 (Model Affinity)”以及“预估被采纳率 (Estimated Citation Rate)”；
3. **缺少交付级信源权威度矩阵大盘与提权优化建议**：
   - 亟需一套能够自动对项目回填的全部外链计算 5 维权威分、五大模型亲和度矩阵并输出提权行动方案的中枢。

---

## What Changes (改动范围)

1. **Citation 信源权威度与外链信任度推演核心引擎 (`tools/geo/citation_authority.py`)**：
   - `CHANNEL_AUTHORITY_DB`：维护各大平台（头条、知乎、微信、GitHub、百家号、CSDN、企业官网等）的基础域名权威分与五大模型生态偏好权重；
   - `score_single_backlink(link_item: dict) -> dict`：对单条外链计算域名权重 (0~100)、结构完备度、五大模型亲和度与预估被采纳率；
   - `evaluate_project_citation_authority(project_id: str) -> dict`：扫描项目台账中全部外链，汇总全案信源权威总分、五大模型生态覆盖度与提权建议；
   - `render_citation_authority_markdown(project_id: str, auth_data: dict) -> str`：自动输出 `outputs/15_大模型Citation信源权威度与外链信任度评分报告.md` 与 `outputs/citation_authority_matrix.json`；
2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
   - `geo citation-auth <pid>`
3. **服务端 API 与 Web 端大一统集成 (`tools/geo/server.py`, `web/index.html`)**：
   - 挂载 `GET/POST /api/projects/{id}/citation/authority`；
   - Web 端 Step 5 持续运营面板增加「🏆 信源权威度与 Citation 矩阵」弹窗与全景权重看板。

---

## Capabilities (对外能力)

- **外链域名权威度与五大模型生态偏好度量化透视**；
- **单条外链被大模型采纳率 (Estimated Citation Rate) 反向推演**；
- **全案外链提权与补齐渠道短板策略指引**。

---

## Impact (影响分析)

- 让企业客户清晰理解外链分发布局的科学依据与各大模型的偏好权重，显著提升续费率与运营黏性。

