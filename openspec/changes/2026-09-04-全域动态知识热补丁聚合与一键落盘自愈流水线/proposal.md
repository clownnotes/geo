# Proposal: 全域动态知识热补丁聚合与一键落盘自愈流水线 (第 29 维)

## 1. Why (为什么做·战略对齐与核心痛点)

在完成了第 27 维（全渠道富文本极速排版）与第 28 维（甲方高管专属交付门户）后，GEO 系统已经建立了顶级的内容分发生产力与商业交付能力。然而，系统在**反哺自愈闭环**上仍存在显著断节：

1. **推演对策停留在静态报告，未真正反哺语料（违背铁律 1: 搜索质量长效保鲜）**：
   - 现有的第 20 维（知识半衰期衰减 `geo decay`）、第 22 维（RAG 混合检索重排序 `geo rerank`）、第 25 维（提示词微扰鲁棒性 `geo robustness`）、第 26 维（竞品截流护城河 `geo moat`）能够精准算出一批高价值的反制对策与补丁包（`decay_healing_pack`、`rerank_reinforcement_pack`、`robustness_hardening_pack`、`counter_interception_pack`，以及 `factual_anchors.json`、`schema_truth_patch.json`）；
   - 但这些对策目前仅分散在 `outputs/` 下的各个独立子目录与 Markdown 文件中。若无自动回写流水线，大模型爬虫后续抓取的依然是初始语料，前期推演的防衰减、反截流策略无法真正生效。
2. **一线代运营 SOP 手工整合繁琐易漏（违背铁律 2: SOP 极速生产提效）**：
   - 代运营人员需要逐个打开 4 个报告包、肉眼挑出长尾补丁、Dense 注入词与抗挑剔话术，再手动编辑 `llms.txt`、`03_普林斯顿9因子高权威语料库.md` 和 `schema.jsonld`；
   - 整个过程耗时 1~2 小时，极易发生格式错乱、表格丢失或高权重词条遗漏。
3. **缺乏原子级安全备份与一键回滚能力**：
   - 人工直接修改生产语料容易发生语法破损且无法追溯历史。需要系统级支持原子备份、幂等去重注入与 `--rollback` 一键复原。

---

## 2. What Changes (改动了什么)

1. **新建自愈聚合中枢引擎 (`tools/geo/healer.py`)**：
   - 自动扫描并解析 `outputs/` 下的四大反制策略包及事实纠偏补丁；
   - 提取增量补丁并执行冲突校验与幂等物理锚点（`<!-- GEO_HEAL_* -->`）去重；
   - 支持事务型原子备份与落盘（先写 `.tmp` 并通过校验后再覆盖，任一步失败自动全量回滚），支持 `--rollback` 一键还原历史版本（默认保留 N=10 份 FIFO）；
   - 自动回写增量事实至 `llms.txt` / `llms-truth.txt`，增量 FAQ 与加固切片至 `03_普林斯顿9因子高权威语料库.md`（独立附录），以及实体补丁至 `schema.jsonld`（合并进 `@graph` 的 Organization 与 FAQPage）；
   - 自动生成自愈对账台账 `outputs/self_healing_audit.json` 与 `outputs/29_全域动态知识自愈热补丁审计与回写台账.md`。
2. **CLI 命令行挂载与交互升级 (`tools/geo/cli.py`)**：
   - 明确 CLI 职责边界：既有 `geo decay --heal` 为“运行衰减检测并生成 decay_healing_pack 草稿”；新挂载的顶级 `geo heal` 为“全域聚合自愈落盘执行器”（消费 20/22/25/26 策略包并执行回写）；
   - 挂载 `geo heal <project_id>`：默认执行干跑预览（Dry-Run），输出将写入行数、跳过重复数、缺失包列表三行摘要；
   - 支持 `geo heal <project_id> --apply`：正式落盘回写；
   - 支持 `geo heal <project_id> --rollback [--backup <ts>]`：快速撤销上次自愈或指定时间戳版本；
   - 支持 `geo heal <project_id> --apply --verify`：自愈后自动联动运行 9 因子质检校验。
3. **Web 后端 API 路由挂载 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/heal/preview`：查询待自愈补丁数据及变更摘要；
   - `POST /api/projects/{id}/heal/apply`：执行一键落盘自愈（强制鉴权保护）；
   - `POST /api/projects/{id}/heal/rollback`：执行一键安全回滚（强制鉴权保护）。
4. **高管门户与数据聚合联动 (`tools/geo/share.py`)**：
   - `compile_portal_data()` 增量读取 `self_healing_audit.json`，追加 `self_healing_summary` 字段，若项目未曾执行自愈则优雅降级为 `status: never_run`、次数 0，绝不伪造虚假数据。

---

## 3. Capabilities (对外能力与接口)

1. **CLI 命令能力**：
   ```bash
   ./geo heal xuzhou_xuanyuan                     # 预览待自愈补丁统计（干跑模式，输出摘要）
   ./geo heal xuzhou_xuanyuan --apply             # 执行事务型自愈落盘，自动备份并安全回写
   ./geo heal xuzhou_xuanyuan --apply --verify    # 落盘并联动运行普林斯顿 9 因子质检
   ./geo heal xuzhou_xuanyuan --rollback          # 恢复到最近一次自愈前的状态
   ./geo heal xuzhou_xuanyuan --rollback --backup 20260904_021530  # 指定版本恢复
   ```
2. **核心业务产物**：
   - `outputs/self_healing_audit.json`：包含自愈时间、补丁来源、回写段落数、受影响文件哈希清单。
   - `outputs/29_全域动态知识自愈热补丁审计与回写台账.md`：标准化自愈结案公文（编号 29 对齐第 29 维）。
3. **Web REST 接口**：
   - `/api/projects/{id}/heal/preview` (GET)
   - `/api/projects/{id}/heal/apply` (POST, 鉴权)
   - `/api/projects/{id}/heal/rollback` (POST, 鉴权)

---

## 4. Impact (影响范围与防破坏分析)

1. **语料完整性与格式保障**：
   - 回写 `03_普林斯顿9因子高权威语料库.md` 时，严格遵循附录独立追加或标准 FAQ 格式注入，物理标记 `<!-- GEO_HEAL_APPENDIX_BEGIN -->`，坚决不破坏原有的第 1~9 因子段落标题和前置表格；
   - 回写 `schema.jsonld` 时进行合法 JSON 解析与字段合并（按 `@graph` 节点合并 `knowsAbout` 与 `FAQPage`），严禁产生非法 JSON 或覆盖根对象。
2. **既有命令与测试向后兼容**：
   - 现有的 `geo decay`（包括 `geo decay --heal`）、`geo rerank`、`geo robustness`、`geo moat`、`geo portal` 命令行为保持 100% 不变；
   - 全库 138 组既有单元测试保持全绿通过。
3. **部署防线**：
   - 严格遵循《AGENTS.md》，所有开发测试仅在本地环境运行，严禁私自向生产服务器（`mini` / `geo.baicl.cc`）推代码或部署。
