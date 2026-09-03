# Design: GEO全景16维资产大一统商业验收门户与结案交付中枢

## 一、双轨制履约评估模型 (Dual-Track Model)

为坚决维护既有合同商务严肃性，本系统确立**双轨并行**的验收评估体系，禁止用文件齐套替代商业履约：

1. **轨 A：合同商业履约达成率评分 (`total_fulfillment_score`, 0~100 分)**
   - **严格沿用既有 6 维加权算法与接口契约**：
     - S1 商业意图与体检诊断 (15%)
     - S2 站点技术底座改造 (15%)
     - S3 普林斯顿 9 因子语料重构 (20%)
     - S4 全渠道矩阵分发完成率 (15%)
     - S5 真实声量占有率 SOV (20%)
     - S6 商业 ROI 与企业数字资产估值 (15%)
   - **结案判定红线**：`≥ 90.0 分` 为“全额结案回款标准”，`70.0~89.9 分` 为“基本交付标准”。
   - **输出字段**：`total_fulfillment_score`, `is_passed`, `status_text`, `breakdown` (保持完全向下兼容)。

2. **轨 B：16 维交付成果齐套率 (`generation_rate_pct`, 0~100%)**
   - **唯一口径分母**：**锁定为 01~16 号共 16 项主交付报告**；
   - `00` 验收单、`00` Pitch 标书、结案移交证书 HTML 及配套 JSON/SVG 作为交付衍生品，不计入分母，彻底杜绝首次运行自指循环依赖；
   - **输出字段**：`manifest_summary` (`total_dimensions: 16`, `fulfilled_dimensions`, `generation_rate_pct`, `missing_dimensions`)。

---

## 二、唯一 16 维主交付报告清单与回退规范 (`DELIVERABLES_MANIFEST`)

| 编号 | Key (白名单键) | 主报告文件名 | 别名与回退文件 | 阶段与分类 |
| :---: | :--- | :--- | :--- | :--- |
| **01** | `audit` | `01_企业AI可见度现状体检与商业诊断报告.md` | - | S1 调研诊断 |
| **02** | `scaffold` | `02_站点技术底座改造交付包.md` | `llms.txt`, `schema.jsonld`, `robots.txt` | S2 站点底座 |
| **03** | `rewrite` | `03_普林斯顿9因子高权威语料库.md` | `03_普林斯顿9因子企业语料库.md` | S3 内容工程 |
| **04** | `distribute` | `04_全网分发渠道执行与存活台账.md` | `04_多平台矩阵借壳分发包.md` | S4 矩阵分发 |
| **05** | `monitor` | `05_企业AI可见度与声量追踪周报.md` | - | S5 运维归因 |
| **06** | `evaluator` | `06_大模型真实API评测与Citation捕获报告.md` | `06_大模型真实API评测与Citation捕获报告.json` | S5 真实评测 |
| **07** | `guard` | `07_大模型事实幻觉纠偏与信源反击策略.md` | `llms-truth.txt` | S4/S5 事实防守 |
| **08** | `visual` | `08_企业技术全景架构图.svg` | `08_技术架构与选型图.svg`, `07_选型差异化对比图.svg` | S3 多模态资产 |
| **09** | `video` | `09_60秒短视频高转化口播脚本.md` | - | S3 多模态资产 |
| **10** | `graph` | `10_企业行业实体关系知识图谱.md` | `entity_graph.json` | S3 知识工程 |
| **11** | `intent` | `11_三级搜索意图挖掘与长尾关键词裂变拓扑.md` | `keywords_intent_matrix.json`, `02_企业商业意图与5维提问挖掘词库.json` | S1/S3 意图拓扑 |
| **12** | `rag_diag` | `12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md` | `rag_chunks_diagnostic.json` | S2/S3 命中诊断 |
| **13** | `compliance`| `13_多渠道内容合规与广告法风控审查报告.md` | `compliance_inspection.json` | S4 内容合规 |
| **14** | `competitor`| `14_竞对大模型声量差距深度逆向与反超作战沙盘.md`| `competitor_gap_analysis.json` | S1/S5 竞争对抗 |
| **15** | `citation_auth`| `15_大模型Citation信源权威度与外链信任度评分报告.md`| `citation_authority_matrix.json` | S4/S5 信源权重 |
| **16** | `injection_guard`| `16_大模型提示词注入防御与品牌隔离盾牌报告.md`| `prompt_injection_guard.json` | S4/S5 品牌安全 |

*注：旧版 `06_竞品权威信源反向包抄策略.md` 仅归入 S5 defense 历史包抄，不抢占 `06_evaluator`；07 对比图仅作为 08 视觉多模态候选，不与 07 幻觉纠偏混淆。*

---

## 三、门户指标与真实落盘 JSON 字段绑定映射表

禁止在门户中胡乱捏造默认高分，严格从落盘 JSON 中安全提取：

| 模块 | 真实落盘文件 | 绑定字段 | 界面展示定义 | 缺省回退 |
| :--- | :--- | :--- | :--- | :--- |
| **16 提示词注入盾** | `prompt_injection_guard.json` | `immunity_score` | 品牌安全免疫度 (0~100 分) | 100.0 分 (未检出) |
| **15 Citation 权威度** | `citation_authority_matrix.json` | `overall_authority_score` | 权威总分 (0~100 分) | 90.0 分 |
| **14 竞对反超沙盘** | `competitor_gap_analysis.json` | `radar_comparison.overall_gap_lead` | 综合领先优势分 (+XX 分) | — / 待分析 |
| **13 广告法合规** | `compliance_inspection.json` | `compliance_rate_pct` | 广告合规率 (0~100%) | 100.0% |
| **12 RAG 命中诊断** | `rag_chunks_diagnostic.json` | `rag_readiness_score` | **RAG 向量就绪度评分** (非命中率) | — / 待诊断 |
| **11 意图裂变拓扑** | `keywords_intent_matrix.json` | `total_keywords` 或 `len(keywords)` | 真实意图词库规模 (条) | 30~45 条 |
| **06 真实 API 评测** | `06_...报告.json` | `overall_sov_pct` | 真实线上实测 SOV (%) | 与周报 SOV 一致 |

---

## 四、接口与安全白名单契约

1. **现有函数与端点保持完全一致**：
   - 沿用 `generate_acceptance_report(project_id)`、`calculate_fulfillment_score(project_id)`、`export_project_archive_zip(project_id)`；
   - 沿用 `GET /api/share/{token}/download-zip`（兼容 `/archive`）；
2. **按需只读报告端点安全约束 (`GET /api/share/{token}/file?key={key}`)**：
   - **严格白名单限制**：`key` 必须属于 `DELIVERABLES_MANIFEST` 声明的 16 个键之一，外加 `acceptance`；
   - **物理路径穿透防御**：提取的目标路径通过 `os.path.realpath` 必须以该项目的 `outputs/` 绝对路径开头；
   - **绝对机密隔离**：严禁读取 `project.yaml`、提取码 PIN、`roi_settings.json` 等敏感数据。
3. **ZIP 打包白名单与去敏感化**：
   - 打包涵盖：01~16 主交付物、00 结案确认单、SVG、HTML 移交证书、各渠道分发排版稿；
   - 显式排除：`roi_settings.json`、`.git`、`.compliance_backup`、临时 `.zip` 文件。


