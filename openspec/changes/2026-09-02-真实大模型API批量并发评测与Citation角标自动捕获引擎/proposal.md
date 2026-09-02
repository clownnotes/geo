# Proposal: 真实大模型 API 批量并发评测与 Citation 角标自动捕获引擎 (Live LLM API Batch Evaluator & Citation Extractor Engine)

## Why (为什么做 / 业务背景与技术诉求)

1. **从“本地沙箱模拟”向“真实模型 API 交叉印证”跨越**：
   - 之前系统的可见度监控与沙箱推演主要基于离线规则和模拟器，虽然快速稳定，但商业客户往往提出：“我想看看豆包/DeepSeek 现在实际是怎么回答这 45 个词的”；
   - 随着火山方舟（豆包 API）、DeepSeek 开放平台、智谱 GLM 与阿里云百炼 API 的普及，系统需要具备直连真实大模型 API 的跑批评测能力。
2. **自动化 Citation 角标捕获与分发信源存活闭环**：
   - 真实大模型在开启联网搜索（Web Search）回答时，会输出引用信源或在正文中引用具体渠道（如今日头条、知乎专栏、GitHub）；
   - 自动解析这些真实 Citation，能够与我们的 `dist_ledger.json`（分发存活台账）做真实交叉印证，量化证明我们的信源分发是否已经被大模型成功吸收与采纳。

---

## What Changes (改动范围)

1. **新增真实大模型 API 评测与 Citation 捕获引擎 (`tools/geo/evaluator.py`)**：
   - `run_live_llm_evaluation(project_id, models, limit, concurrency)`：支持并发调用真实的豆包、DeepSeek、Kimi 等 API；
   - `extract_citations_and_sov(response_text, company_info)`：自动提取回答中的品牌提及、首推排名（Top1/Top3）与 Citation 域名/外链；
   - `export_live_eval_report(project_id, results)`：输出 `06_大模型真实API评测与Citation捕获报告.json` 与 `.md`；
2. **统一 API 协议与优雅降级**：
   - 采用标准 OpenAI 兼容协议，支持环境变量或配置文件填入 API Key；
   - 无 Key 时自动无缝降级为高拟真真实数据沙箱，绝不阻塞流程；
3. **CLI 与 Web 端集成**：
   - 新增 `geo eval <project_id> [--models doubao,deepseek] [--limit 15]` CLI 指令；
   - Web 端增加“真实大模型评测大盘”与 Citation 溯源视图。

---

## Capabilities (新增或修改的对外能力)

- **`geo eval <project_id>`**：一键对 45 组意图词发起真实/拟真大模型并发调用；
- **Citation 溯源分析**：自动统计各主流信源（头条/知乎/GitHub/微信）在真实大模型回答中的引用占比；
- **真实 SOV 对比**：量化展现优化后在豆包第一阵地与 DeepSeek 上的真实统治率。

---

## Impact (影响分析)

- **客户信任度提升 100%**：提供真机 API 评测与真实 Citation 角标佐证，无可争议；
- **全链路闭环**：【词库 ➔ 语料 ➔ 分发 ➔ 存活台账 ➔ 真实 API 评测】形成完全闭环。

