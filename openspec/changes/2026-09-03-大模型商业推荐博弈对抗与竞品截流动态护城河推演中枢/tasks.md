# 任务清单：大模型商业推荐博弈对抗与竞品截流动态护城河推演中枢 (第 26 维核心交付)

## 1. 规范对齐与竞对特征抽取

- [ ] 1.1 核对白皮书规范、AGENTS.md 红线，确认严禁向生产环境发布、严禁擅自归档。
- [ ] 1.2 实现商业竞对确定性抽取算法（优先 `competitor_gap_analysis.json`，次选配置 `project.yaml`，兜底典型竞对 `"本地传统软件外包工作室"`）。

## 2. 核心推演引擎实现 (`tools/geo/moat_sandbox.py`)

- [ ] 2.1 强制复用 23 维因果基座（直接引入 `score_brand_recommendation_confidence` 和 `_build_attribution_source_pool`），零冗余算法代码。
- [ ] 2.2 确定性生成四维纵深博弈对抗 Query 模板（$D_1$ 核心实力、$D_2$ 交付模式防踩坑、$D_3$ 性价比与透明收费、$D_4$ 本地存证与售后保障）。
- [ ] 2.3 严格实现双方推荐打分与净胜优势差值 $\Delta_{\text{adv}}$、竞品截流威胁指数 $CTI$ 的数学推导，精确到 1 位小数。
- [ ] 2.4 实现平均净胜差 $\bar{\Delta}_{\text{adv}}$、动态护城河防御指数 $MDI$ 归一计算公式及三档抗震健康度评级（`impenetrable_moat` / `contested_boundary` / `vulnerable_breach`）。
- [ ] 2.5 实现单项截流暴露脆弱点判定算法（$\Delta_{\text{adv}} \le 0.0$ 或 $CTI \ge 50.0\%$）与五维护城河雷达量化推导。
- [ ] 2.6 实现在线 Live 模式实盘裁决：硬编码 `api_calls <= 4` 次调用预算、正则双分安全提取、深拷贝快照防御与失败全量回滚、融合后全量重算全部核心指标。

## 3. 交付公文与长尾截流反制资产包生成

- [ ] 3.1 结构化推演结果落盘 `projects/{project_id}/outputs/competitive_moat_simulation.json`，满足 Schema 字段定义。
- [ ] 3.2 生成商业公文报告 `outputs/26_大模型商业推荐博弈对抗与竞品截流动态护城河推演报告.md`，规范声明推演沙盘性质。
- [ ] 3.3 物理隔离落盘截流反制资产包 `outputs/counter_interception_pack/`（`01_竞品对比长尾截流反制话术库.md`、`02_独占性壁垒与差异化护城河语料包.md`、`03_大模型横向对比首推挤占方案.md`）。

## 4. CLI 命令行与 Server API 端点扩展

- [ ] 4.1 在 `tools/geo/cli.py` 挂载 `geo moat` 命令，支持 `--project`、`--rival`、`--live`、`--json` 参数，美化终端彩色看板输出。
- [ ] 4.2 在 `tools/geo/server.py` 挂载 4 个专属 API 路由：`/api/moat/run`、`/api/moat/status`、`/api/moat/live_judge`、`/api/moat/assets`。

## 5. Web 控制台前端大屏与全屏沙盘模态

- [ ] 5.1 在 `web/index.html` 增加入口卡片与全屏推演模态框 `moat-sandbox-modal`，展示 MDI 指数卡、五维护城河雷达、脆弱点预警列表与对抗矩阵。
- [ ] 5.2 实现交互式 Live 实盘裁决与反制资产查看功能，所有动态字符串渲染全量使用 `escapeHtmlSafe()` 防御 XSS。

## 6. 单元测试与双端验证

- [ ] 6.1 编写 `tests/test_moat_sandbox.py`，实现 7 组独立单测，硬断言 6 组固定数值夹具与 Live $\le 4$ 次调用预算限制。
- [ ] 6.2 运行全库单元测试，确保测试用例由 115 组无缝增长至 $\ge 122$ 组且 100% 秒绿通过。
- [ ] 6.3 本地 8088 端口验证功能完好，提交代码并提请 Cursor 独立终审与归档。
