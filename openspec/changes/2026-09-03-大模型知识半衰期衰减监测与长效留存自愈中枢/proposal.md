# Proposal: 大模型知识半衰期衰减监测与长效留存自愈中枢 (LLM Knowledge Decay & Memory Retention Monitor)

## Why (为什么做 / 商业痛点与代运营核心刚需)

1. **破除「GEO 优化一劳永逸」误区，建立长效代运营商业收费的底层支柱**：
   - 很多企业客户误以为：“GEO 只要做一次优化、模型收录了，就能永久维持推荐”。
   - 但在真实商业实践中，主流大模型的联网搜索索引与 RAG 切片权重具有明显的**「时间衰减效应（Temporal Knowledge Decay）」**：随着全网新内容涌现、竞品持续发稿冲淡、以及大模型微调周期迭代，受测品牌的推荐位次与 Citation 引用通常会在 14~30 天内发生显著衰退（记忆半衰期）。
   - 研发该中枢，能用真实量化数据向客户直观证明：“上月的知识留存率从 90% 下滑到了 58%，触发了黄色衰减警报”，从而为企业客户**持续按月/按季续约代运营服务**提供不可辩驳的商业依据。

2. **从「单点静态探测」到「时间序列衰减追踪（Time-Series Tracking）」**：
   - 现有的 18 号中枢完成了单次并发联网探测与 Citation 溯源，但缺乏时间序列对比能力；
   - 本中枢建立**知识留存衰减时间序列模型（Day 1 / Day 7 / Day 14 / Day 30）**，测算「知识留存率 (Knowledge Retention Rate, KRR)」、「衰减速率系数 ($\lambda$)」与「预估半衰期 ($t_{1/2}$)」，定位哪些长尾词正在被大模型逐渐遗忘。

3. **从「被动发现遗忘」到「自愈式智能补量与增量刷新（Decay Auto-Healing）」**：
   - 发现衰减不仅是告警，更需给出战术动作：一旦某组核心意图 Query 的留存率跌破安全阈值（< 60%），系统**自动化生成自愈式补量发稿推荐清单与增量刷新语料包**，精准向 04 台账阵地进行自愈式补量注入，形成良性循环闭环。

---

## What Changes (改动范围与复用策略)

1. **研发大模型知识半衰期衰减监测与长效留存自愈引擎 (`tools/geo/decay_monitor.py`)**：
   - **底层复用**：强制直接复用 `tools/geo/llm.py`（统一使用 `call_model_raw` 与 Key 链式读取）、`tools/geo/probing.py` 的 `extract_citations_and_sources` 与 `tools/geo/dist_bot.py` 的 `get_distribution_ledger`；
   - **时间序列对比与衰减模型**：记录并比对基线期（Baseline）与当期探测的有效提及率与台账命中数，精准测算留存率与半衰期天数；
   - **红黄绿三级衰减预警机制**：
     - 🟢 留存良好 (KRR $\ge 80\%$)：知识记忆鲜活稳定；
     - 🟡 预警衰减 ($60\% \le \text{KRR} < 80\%$)：部分长尾词被冲淡，建议自愈补量；
     - 🔴 严重遗忘 ($\text{KRR} < 60\%$)：核心词位次严重下滑，触发紧急自愈刷新；
   - **自愈刷新包生成器 (`generate_decay_healing_pack`)**：自动针对衰减严重的 Query 生成补充发稿任务建议与高权重自愈语料，落盘至 `outputs/decay_healing_pack/`；
   - **规范交付物落盘**：生成公文标准规范的 `outputs/20_大模型知识半衰期衰减监测与长效留存自愈报告.md` 与 `outputs/knowledge_decay_retention.json`。

2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo decay <project_id>` 子命令：
     - 支持 `--models doubao,deepseek,kimi` 指定探测模型；
     - 支持 `--live` 启用真实联网（未设 Key 自动走高保真沙箱）；
     - 支持 `--heal` 自动生成自愈补量刷新包；
     - 输出终端高保真 ANSI 衰减时间序列对照大盘。

3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/decay/status`：获取当前知识留存率、半衰期预估与时间序列历史；
   - `POST /api/projects/{id}/decay/track`：触发时间序列衰减追踪计算；
   - `POST /api/projects/{id}/decay/heal`：触发自愈补量语料包生成；
   - `GET /api/projects/{id}/decay/report`：获取 20 号公文报告（无文件返回 404，禁止自动 scan）。

4. **Web 管理工作台界面升级 (`web/index.html`)**：
   - 向导 Step 5 新增「⏳ 知识半衰期衰减与长效自愈 (20)」独立卡片与入口，顶部 Header 增加入口；
   - 开发全屏模态窗口 `decay-monitor-modal`：KRR 留存仪表盘、半衰期预测卡、各意图 Query 衰减流水表与自愈补量一键生成（全量通过 `escapeHtmlSafe` 转义）。

5. **自动化测试套件 (`tests/test_decay_monitor.py`)**：
   - 全量覆盖沙箱降级、时间序列留存率计算、半衰期公式、自愈包生成及 20 号报告落盘。

---

## Out of Scope (范围排除声明)

- 本规范专注于公域内容的大模型 RAG 记忆留存与自愈刷新策略，不涉及企业私有微调模型的底层权重篡改；
- 模型范围专注中国本土主流大模型（豆包、DeepSeek、Kimi）与确定性沙箱，海外模型不列入本次范围。

---

## Impact (影响分析)

- **纯增量无侵入开发**：复用既有模块，不影响 01~19 号已有成果与数据；
- **全自动 CI/CD 兼容**：内置 `DecaySandboxSimulator`，测试套件毫秒级全绿；
- **最高协同协议遵循**：本地测试锁定 8088 端口，绝不私自推向生产；归档操作全权交由 Cursor 在独立复审后执行。
