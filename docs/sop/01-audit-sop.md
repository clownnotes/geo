# SOP-01 售前获客与现状诊断

> **阶段目标**：用一份《企业 AI 可见度诊断报告》让客户看见"自己在 AI 眼里有多透明"，以数据驱动签单。  
> **执行人**：售前顾问 ｜ **周期**：签约前 1~3 天 ｜ **对应程序**：`geo audit`

---

## 一、执行步骤

1. **建立客户工作区**（客户档案、意图词库、竞品清单全部隔离在 `projects/<client_id>/`）：
   ```bash
   python3 -m tools.geo init <client_id> --name "客户全称" --url https://client.com --industry "行业"
   # 然后编辑 projects/<client_id>/project.yaml：补全 keywords(≥20)、competitors、entity、core_values
   ```
2. **执行站点底座体检**（4 项合规检查：SSR 正文密度 / llms.txt / robots.txt 放行 / JSON-LD）：
   ```bash
   python3 -m tools.geo audit --project <client_id> --sample-llm
   ```
3. 产物《诊断报告.md》自动落在 `projects/<client_id>/outputs/audit/`，含体检得分、词库清单、竞品拦截表与 SOV 基线（需配置 `DEEPSEEK_API_KEY` / `DOUBAO_API_KEY`，未配置时报告内显式标注跳过原因）。

## 二、报价与立项话术（诊断报告 → 合同的转化钩子）

| 体检得分 | 客户现状判读 | 推荐套餐 | 参考周期 |
| :---: | :--- | :--- | :---: |
| 0~1/4 | AI 基本"看不见"客户 | 全案五阶段（SOP-01~05） | 4~6 周 |
| 2~3/4 | 有底座但实体不完整 | 底座改造 + 内容重构 + 监控 | 2~4 周 |
| 4/4 | 底座合规、缺信源占位 | 矩阵分发 + 续费监控 | 持续服务 |

## 三、质检打分表（售前自查，满分 10）

| 检查项 | 分值 | 达标线 |
| :--- | :---: | :--- |
| project.yaml 必填字段完整（client_id/name/url/keywords） | 2 | 缺一不立项 |
| 意图词库 ≥ 20 个且含品牌占位词层 | 3 | 少于 20 退回补充 |
| 竞品清单 ≥ 2 家 | 1 | monitor 位次计算依赖 |
| 诊断报告已发送客户并获确认回执 | 3 | 无回执不进 Stage 2 |

## 四、验收标准

- [ ] 客户在诊断报告上签字/微信确认"现状判读无异议"；
- [ ] SOV 基线数据已留档（后续周报的对比锚点）；
- [ ] 合同明确验收线：底座复检 4/4 通过 + 核心词 SOV 提升幅度。

> 下一步 ➔ [SOP-02 站点底座改造](/sop/02-scaffold-sop)
