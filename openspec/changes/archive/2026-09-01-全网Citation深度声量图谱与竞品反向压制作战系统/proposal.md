# Proposal: 全网 Citation 深度声量图谱与竞品反向压制作战系统

## Why (为什么做 / 业务痛点)

1. **痛点：Step 5 监控结果缺乏高层直观图表与商业归因展示**
   - 当前 Step 5 仅输出长篇 Markdown 周报，在 Web 工作台缺乏直观的图形化仪表盘（如 SOV 渗透率、权威信源权重分布、命中 vs 丢失问句对比）；
   - 企业老板与销售团队在查看报告时，需要一眼能看懂的量化指标卡片与可视化图谱。
2. **痛点：大模型推荐竞品时缺乏自动化反击与包抄手段**
   - 当大模型在某些用户提问中优先推荐了竞品时，传统团队只能盲目发文；
   - 需要一个能够**自动反解竞品被大模型引用的权威阵地**，并一键生成**《竞品权威信源反向包抄策略 (`06_竞品权威信源反向包抄策略.md`)》**与针对性压制语料的自动化作战引擎。
3. **商业交付闭环：一键导出美化版交付报表**
   - 交付团队需要能一键导出带品牌标识、排版优雅的独立报告页面，直接发送给甲方决策层。

---

## What Changes (改动范围)

1. **新建竞品反解与压制作战引擎 (`tools/geo/defense.py`)**：
   - 结合探测结果中的竞品拦截词，分析大模型引用的信源偏好；
   - 自动生成针对竞品的 5 维差异化压制话术与信源占位包抄清单（输出 `06_竞品权威信源反向包抄策略.md`）。
2. **CLI 工具链扩展 (`tools/geo/cli.py`)**：
   - 增加 `geo defense <project_id>` 子命令。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/monitor/metrics`：解析周报与监控数据，返回结构化的 SOV、大模型首推率、权威信源渗透权重与问句对决状态 JSON；
   - `POST /api/projects/{id}/defense/generate`：触发竞品反向压制策略生成；
   - `GET /api/projects/{id}/report/print`：提供美化版、可直接打印或转存 PDF 的独立交付周报页面。
4. **Web 交付工作台 Step 5 交互重构 (`web/index.html`)**：
   - 将 Step 5 升级为 **「📊 AI 声量大盘与 Citation 权威图谱」**：
     - 4 大核心指标卡（整体 SOV、DeepSeek 首推率、豆包首推率、权威信源覆盖度）；
     - 信源权威度加权分布条形图；
     - 问句级命中/拦截/丢失状态矩阵筛选器；
     - 「⚔️ 一键生成竞品反向包抄策略」与「🖨️ 导出美化交付报告」快捷按钮。
5. **SOP 知识库更新 (`docs/sop/05-monitor-sop.md`)**：
   - 将 Citation 声量图谱解读与竞品反向包抄纳入 SOP-05。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/monitor/metrics`
- `POST /api/projects/{id}/defense/generate`
- `GET /api/projects/{id}/report/print`
- CLI: `python3 -m tools.geo defense <project_id>`

---

## Impact (影响分析)

- **完全向下兼容**：原有 5 步流水线产物与格式不变，新增第 6 份高级战略交付物 `06_竞品权威信源反向包抄策略.md`；
- **售前后端说服力拉满**：直观图表与针对竞品的降维压制策略，让企业客户清晰看到投入产出比与竞争优势。
