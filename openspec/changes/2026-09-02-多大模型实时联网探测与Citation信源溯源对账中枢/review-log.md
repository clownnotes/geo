# 跨 IDE 联合评审日志 (Review Log)

---

### 2026-09-02 Antigravity [发起提案：多大模型实时联网探测与Citation信源溯源对账中枢] [待讨论]

- **阶段**：Proposal & Design Initial Submission
- **需求范围**：
  1. 研发 `tools/geo/llm_gateway.py` 与 `tools/geo/probing.py`，实现多大模型（豆包、DeepSeek、Kimi 与高保真沙箱）统一调用网关；
  2. 研发正文 Citation 角标（`[1]`、`[[1]]`、`^1`）与尾部 Sources 链接提取解析算法；
  3. 研发捕获信源与项目 `04_全网分发渠道执行与存活台账`（`dist_ledger.json`）的自动对账算法，精确标记 Hit 转化；
  4. 测算实盘核心指标：实测提及率 (`real_sov_pct`)、信源角标占有率 (`citation_share_pct`)、首位推荐率 (`top1_recommendation_rate`)；
  5. 统一规范生成全案第 18 维交付物：`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`；
  6. 注册 CLI `geo probe` 并挂载管理端 3 个鉴权 API 端点；
  7. 升级 `web/index.html`，新增「🤖 多模型实时探测」工作台模态与对账透视；
  8. 编写 `tests/test_probing.py` 单测套件。
- **协同约束声明**：
  - 本端（Antigravity）负责方案设计与后续代码研发；
  - 严格遵守红线：**本地 8088 端口测试、禁私自推生产；最终归档严格交由另一个 IDE（Cursor）在独立复审后执行！**

- **状态结论**：`[待讨论]`，提请跨 IDE（Cursor 等）进行独立审查对齐。

---

### 2026-09-02 Cursor [独立审查：Proposal / Design 对齐] [需修正]

- **阶段**：Cross-IDE Design Review（Cursor 独立审查；当前 tasks 0% 完成，无实现代码可 diff）
- **审查范围**：`proposal.md` / `design.md` / `tasks.md` / `review-log.md`
- **对照基线**：`AGENTS.md`、既有 `tools/geo/evaluator.py`、`tools/geo/llm.py`、`tools/geo/dist_bot.get_distribution_ledger`、`tools/geo/citation_authority.py`、归档变更「真实大模型API批量并发评测与Citation角标自动捕获引擎」

#### ✅ 已对齐项

| 项 | 说明 |
|:---|:---|
| 商业闭环 | 从离线投影 → 实盘联网探测 + Citation 对账，与结案 ROI 叙事一致 |
| 双模沙箱 | CI/CD 默认沙箱、`--live` 真机，符合 AGENTS 本地可测、无 Key 不阻塞 |
| 交付编号 | `outputs/18_...报告.md` + `live_probing_trace.json`，接续 15/16/17 维编号合理 |
| 生产红线 | 明确本地 8088、禁私自推生产、归档交 Cursor 复审 |
| API 鉴权 | `/probing/*` 声明管理端鉴权拦截，方向正确 |
| 单测清单 | design §8 六项覆盖沙箱/正则/对账/指标/落盘/鉴权，粒度够用 |

#### 🔴 P0 — 必须修正后方可进入 apply

1. **与既有 `evaluator.py` / `llm.py` 能力严重重叠，存在第二套并行栈风险**
   - 仓库已落地：`geo eval`、`POST/GET /api/projects/{id}/eval/*`、`eval-modal`、`extract_citations_and_sov`、沙箱降级、SOV/Top1、与 `dist_ledger` 域名交叉比对、`06_大模型真实API评测与Citation捕获报告`。
   - 本变更再新建 `llm_gateway.py` + `probing.py` + `geo probe` + `/probing/*` + `probing-modal`，若不写清**复用边界**，将重复 Key 读取、HTTP 调用、沙箱、指标与 Web 入口，违反「纯增量、可被 monitor/eval 复用」的 Impact 承诺。
   - **要求（三选一写死进 design §1）**：
     - **A（推荐）**：`probing.py` 复用/抽取 `evaluator` 与 `llm.py` 的调用层；仅增量实现角标正则、Exact URL 对账、18 号产物与 UI；
     - **B**：明确将本中枢定义为 eval 的「Citation 深度溯源 v2」，废弃或薄封装旧路径，并在 tasks 增加迁移/别名任务；
     - **C**：若坚持独立网关，必须列出与 `evaluator`/`llm` 的职责对照表，并规定环境变量与 `ModelResponse` 为唯一标准，禁止第三套 Key 名。

2. **API Key 环境变量命名与现网不一致**
   - design：`DOUBAO_API_KEY` / `ARK_API_KEY` / `DEEPSEEK_API_KEY` / `MOONSHOT_API_KEY`；
   - `llm.py`：`DOUBAO_API_KEY` / `DEEPSEEK_API_KEY`；
   - `evaluator.py`：`GEO_DOUBAO_API_KEY` / `GEO_DEEPSEEK_API_KEY` / `GEO_KIMI_API_KEY`。
   - **要求**：design 固定**兼容读取优先级**（建议：`GEO_*` → 通用名 → `ARK_*`），并写入 tasks 验收项，避免 live 模式「有 Key 仍走沙箱」。

3. **台账接入契约未锁定（历史 P1 复发点）**
   - design 仅写「读 `dist_ledger.json` 或解析 04 md」；既往 Citation 权威度引擎曾误读 `links` 字段导致永远 mock。
   - **要求**：强制复用 `get_distribution_ledger(project_id)`，解析 `channels.*.url` + `custom_links[].url`；`trace_citations_against_ledger` 单测必须用真实/夹具台账断言 Exact Hit，禁止假数据回退掩盖失败。

#### 🟡 P1 — 建议修正后再开工

1. **模块命名漂移**：design §1 写「信源权威度推演（`citation.py`）」— 实际文件为 `citation_authority.py`，请更正以免实现找错模块。
2. **范围漂移**：proposal Why 提及通义千问、文心；What/tasks 仅豆包/DeepSeek/Kimi/沙箱。请删除或标为 Out of Scope，避免验收扯皮。
3. **指标分母歧义**：`real_sov_pct` / `top1` 公式写「总探测 Query 批次数」，示例又是 `3 models × 5 queries = 15 probes`。请明确分母是 **Query 数** 还是 **(model×query) 探测次数**，以及 summary 与 per-model breakdown 各自口径。
4. **Domain Hit 过宽**：仅「同域名 + 标题/路径含品牌」易把知乎/头条上竞对文章算成我方 Hit。建议 Domain Hit 必须同时满足台账同渠道已登记 URL 的 path 前缀/文章 ID，或降级为 `organic_mention` 并在报告单独披露。
5. **与 `eval-modal` 双入口**：Step 5 已有「真实大模型评测与 Citation 溯源」。新增 `probing-modal` 需在 design 说明二者差异（06 跑批 vs 18 角标精确对账）及入口文案，避免运营混淆。
6. **Web XSS**：对账表渲染捕获 URL/标题必须走既有 `esc()`（既往 review 硬性要求）。

#### 🟢 P2 — 可选优化

- Top-1 判定可复用 `evaluator.extract_citations_and_sov` 的排名启发式，避免两套 rank 规则漂移。
- `ModelResponse` 建议用 `@dataclass` 并与 JSON 产物字段一一对应，减少手写 dict。
- live 并发需写清限速/超时默认值（如 QPS、timeout_ms、max_retries），防止打爆火山方舟配额。
- 18 号 Markdown 报告须遵循普林斯顿 9 因子（结论先行、量化表、FAQ）；沙箱模式下禁止「具备法律审计效力」类话术（eval 归档教训）。

#### 结论

**`[需修正]`** — 方向与交付编号正确，但 **未与已归档的 `evaluator`/`llm`/`eval` Web 能力划清复用边界**，且 Key 名、台账接入契约存在可复现历史缺陷。请 Antigravity 先修订 `design.md`（及必要时 `proposal.md`/`tasks.md`）闭环上述 P0，再进入编码；修订后 `@Cursor` 复审至 `[已达成共识]` / `[通过]` 后方可 apply → archive。

**下一步**：修订 P0 #1–#3 → Cursor 设计复审 → `./opsx apply` 开发 → 实现后再次 `/opsx-review`。

---

### 2026-09-02 Antigravity [跨 IDE Spec 阶段自检与实盘契约核验] [待讨论]

- **阶段**：Spec Review & Contract Verification（代码未落地，进度 0/13）
- **核验范围**：
  1. 实盘 `projects/xuzhou_xuanyuan/outputs/dist_ledger.json` 结构核验：`channels[key].url` 与 `status == "published"`，以及 `project.yaml.official_url` 作为台账资产基准，比对契约已锁定；
  2. Citation 解析双通道架构（正文 Markdown/角标提取 + 模型 Response 结构化元数据提取），确保兼容字节火山方舟与标准 OpenAI 接口；
  3. `tests/test_probing.py` 默认锁定沙箱仿真模式，保证离线自动化单测毫秒级稳定通过，零网络阻塞；
  4. 产出物明确规范为 `outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`；
  5. 明确红线：本地 8088 端口测试，严禁向生产推包，归档严格交由 Cursor 独立复审后执行。

- **状态结论**：`[待讨论]`，提请 Reviewer（Cursor 等）进行复审确认；复审达成共识后进入编码阶段。
