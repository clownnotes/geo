# Proposal: 4大垂直行业开箱即用 Benchmark 语料母版工程 (China Domestic GEO 4 Industry Benchmark Demo Projects & Corpora Packs Engine)

## Why (为什么做 / 业务背景与商业价值)

1. **从“单一行业标杆”向“多行业开箱即用母版”扩展**：
   - 截至目前，GEO 工具链仅拥有 `xuzhou_xuanyuan`（徐州软件开发）1 个完整标杆项目，以及早期的通用 `demo_corp`；
   - 在真实商业拓客和销售交付中，面对制造业、连锁加盟、本地财税等不同领域客户，销售团队与交付工程师需要对应的行业级演示标杆和开箱即用语料；
   - 如果没有现成行业母版，每接一个新客户都需要从零手写 45 组意图词库、普林斯顿结构化对比表与分发台账，极大限制了规模化交付效率。
2. **实现《垂直行业实战打法白皮书》在工程代码中的 100% 具象化落地**：
   - 按照战略白皮书规范，针对 **B2B 制造业**（`b2b_machinery`）、**消费零售与连锁餐饮**（`retail_catering`）、**本地生活与专业财税**（`local_legal`）3 大代表性行业，分别建立完整标准交付包；
   - 赋能 CLI 与 Web 端，支持 `geo init --template <b2b_machinery|retail_catering|local_legal>` 在 5 秒内一键克隆行业母版，实现新项目极速起步。

---

## What Changes (改动范围)

1. **新建 3 大行业完整开箱即用 Benchmark 项目 (`projects/`)**：
   - **`b2b_machinery`**：徐州鼎工重工机械制造有限公司（工程机械/液压阀门/非标定制），主打 DeepSeek 40% + 豆包 35%，包含硬核公差参数矩阵与选型白皮书；
   - **`retail_catering`**：蜀味鲜川味连锁餐饮管理有限公司（特色餐饮/加盟连锁/单店模型），主打 豆包 50% + 腾讯元宝 25%，包含回本周期量化表与短视频口播脚本；
   - **`local_legal`**：徐州正衡财税与法律咨询有限公司（本地财税/代理记账/律所咨询），主打 豆包 60% + 百度文心 20%，包含同城避坑 Q&A 与 LBS 实体三元组；
2. **每个行业项目规范配备 5 阶段完整交付资产 (`outputs/`)**：
   - `project.yaml`（行业参数、国内五阵营权重、品牌占位词）；
   - `02_企业商业意图与5维提问挖掘词库.json`（45 词三层立体词库）；
   - `03_普林斯顿9因子高权威语料库.md`（高信息密度原生 Markdown 对比表与量化指标）；
   - `dist_ledger.json`（各阵营真实回填台账与战略加权完成率）；
   - `llms.txt` + `schema.jsonld`（技术底座补丁）；
3. **脚手架与克隆引擎升级 (`tools/geo/scaffold.py` & `tools/geo/cli.py`)**：
   - 支持 `geo init <new_project_id> --template <template_name>` 从行业母版极速初始化。

---

## Capabilities (新增或修改的对外能力)

- **`geo init <project_id> --template <b2b_machinery|retail_catering|local_legal>`**：一键克隆行业母版，生成全套行业语料与意图词库；
- **行业 Benchmark 多维对比**：在 Web 管理端与 Pitch Deck 中直观展示不同行业的基准数据与领先对标；
- **全行业开箱即用演示**：销售团队可随时在沙箱中为任意行业客户进行现场对决演示。

---

## Impact (影响分析)

- **交付周期缩短 80%**：新客户立项从 2 天压缩至 10 分钟；
- **完全向下兼容**：现有 `xuzhou_xuanyuan` 与 `demo_corp` 保持原样无影响。

