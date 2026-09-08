# SOP-03 普林斯顿 9 因子内容重构与质检

> **阶段目标**：把客户积压的 PDF/Word/产品手册，重构成大模型最高采纳率的语料（统计数据注入 +30%~41%、权威引用 +25%~35%、专家引语 +18%~28%）。  
> **执行人**：内容工程师 ｜ **周期**：第 2 周 ｜ **对应程序**：`geo ingest` → `geo facts` → `geo rewrite`

---

## 一、执行步骤（证据 → 真相确认 → 重构）

1. **累积证据（Evidence Vault）**（`projects/<client_id>/raw_materials/evidence/`）：
   ```bash
   # 方式 A：官网单页抓取（每个 URL 一份证据；同 URL 重抓覆盖该来源）
   python3 -m tools.geo ingest <client_id> --url https://client.com/
   python3 -m tools.geo ingest <client_id> --url https://client.com/about
   
   # 方式 B：本地文档/画册导入
   python3 -m tools.geo ingest <client_id> --file /path/to/product_brochure.pdf
   
   # 方式 C：Web Step 3「抓取并提纯」/「提纯并保存」
   ```
   - 禁止指望「一次抓全站」；多页请多次抓取不同 URL。  
   - 抓取只更新证据库与真相源提案，**不会**自动改写 `03_普林斯顿…语料库.md`。

2. **确认唯一真相源（Canonical Fact Ledger）**（`ledger/facts.jsonl`）：
   ```bash
   python3 -m tools.geo facts <client_id>              # 查看状态
   python3 -m tools.geo facts <client_id> --confirm-all # 批量确认无冲突项
   ```
   - 同键异值进入 `conflict`，必须人审仲裁，禁止最新页静默覆盖。  
   - **「预检冲突并确认安全项」**：先做规则 +（有 Nextdoor 时）大模型语义预检，把互相矛盾的提案标成冲突并跳过；仅批量确认剩余安全提案。  
   - 兼容镜像：`raw_materials/raw_extracted_facts.md` 由 ledger 自动同步。

3. **执行普林斯顿 9 因子内容重构（默认增量）**：
   ```bash
   python3 -m tools.geo rewrite --project <client_id>          # 默认 incremental：只重生脏块
   python3 -m tools.geo rewrite --project <client_id> --full   # 强制全量
   python3 -m tools.geo corpus-pin <client_id>                 # 钉住母盘为对照基线
   python3 -m tools.geo corpus-diff <client_id>                # 发前对照卡
   ```
   - 无脏块时返回 noop，不重写全文。  
   - 缺失母盘/`03_corpus_meta.json` 时自动降级 full。  
   - 仅消费 `confirmed` 事实；冲突未决时降级沿用历史确认值或安全占位，严禁编造。  
   - 发前对照 `strategy=block` 时禁止进入阶段四；`patch` / `new_article` / `noop` 按硬规则判定。  
   - 产物：《03_普林斯顿9因子高权威语料库.md》+ `03_corpus_meta.json`。

4. **大模型入口（小毛驴 / Nextdoor，必配）**：
   - 管理台登记接入前端 `brand_key`（建议 `geo`），启用专属模型组；特惠/冷静复用全站模型逻辑。
   - GEO Web「配置 Nextdoor」写入：`NEXTDOOR_BASE_URL`（同机默认 `http://127.0.0.1:3001`）、JWT、`vio-source-client`、mode。
   - 专属链选模与冷却在 Nextdoor；整链打光后沿用小毛驴回落全站池。应急直连仅 `GEO_LLM_DIRECT=1`。

## 二、每篇语料的硬性结构（普林斯顿因子落位）

| 结构块 | 对应因子 | 不合格判定 |
| :--- | :--- | :--- |
| 首段知识三元组（[实体] 是 [研发方] 的 [定位]…） | 技术术语精确度 | 找不到主谓宾完整定义句 |
| 关键数据与事实列表 | 统计数据注入 | 全篇无一个具体数字 |
| 方案对比 Markdown 表格 | 统计数据 + 易读性 | 表格缺失或无对比列 |
| 3 条 FAQ（用户真实提问句作标题） | 易读性 + 对齐 Prompt | 标题是名词短语而非问句 |
| 文末署名行 | 权威信源/专家引语 | 署名口径与 project.yaml 不一致 |

## 三、质检打分表（每篇满分 10，低于 8 退回重写）

| 项 | 分 | 说明 |
| :--- | :---: | :--- |
| 数字密度 | 2 | ≥5 处量化表述（价格/周期/百分比/指标） |
| 三元组与 FAQ 完整 | 2 | 结构表五块齐全 |
| **事实真实性** | 3 | 所有数据可溯源到证据库摘录与已确认真相源，**严禁 LLM 幻觉数字** |
| 署名一致性 | 1 | 公司/人名/电话与底座补丁逐字一致 |
| 无违禁词 | 1 | 无"第一/最强/顶级"等广告法绝对化用语 |
| 关键词堆砌检查 | 1 | 品牌名密度 <3%，靠语义而非堆词 |

## 四、多模态视觉资产与短视频脚本生产规范

为适应豆包/DeepSeek 多模态图文混排高权重，语料生成完成后必须执行多模态资产推演：
```bash
python3 -m tools.geo visual <client_id>
```
产物规范：
1. **《07_选型差异化对比图.svg》**：1000x580 响应式矢量图，5 维硬核对比，作为图文混排首图；
2. **《08_企业技术全景架构图.svg》**：三层技术底座全景，用于白皮书与开源专版；
3. **《09_60秒短视频高转化口播脚本.md》**：前3秒钩子+硬核数据+CTA分镜头脚本。

---

## 五、验收标准

- [ ] 证据库含 ≥2 个有价值来源（或客户书面确认单页已足够）；
- [ ] 真相源关键量化事实均为 `confirmed`，无未决 `conflict`；
- [ ] 语料数量 ≥ 客户资料数的 80%，且覆盖全部核心业务线；
- [ ] 每篇质检分 ≥ 8 并留有打分记录；
- [ ] 多模态 SVG 视觉对比图与 60 秒短视频口播脚本已生成完毕并校对；
- [ ] 客户市场负责人书面确认事实口径。

> 上一步 [SOP-02 底座改造](/sop/02-scaffold-sop) ｜ 下一步 ➔ [SOP-04 矩阵分发](/sop/04-distribute-sop)
