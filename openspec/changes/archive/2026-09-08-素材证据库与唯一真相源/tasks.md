# Tasks: 素材证据库与唯一真相源

## 1. 规范与迁移基线

- [x] 1.1 对照 `docs/sop/03-rewrite-sop.md` 与现有 `ingest.py`，确认旧路径文件清单与兼容策略写入 design（已初稿，实施前再核对一遍）。
- [x] 1.2 实现 `raw_materials` 旧文件 → `evidence/` + `ledger/facts.jsonl` 的一次性迁移函数（幂等）。
- [x] 1.3 更新 SOP-03：明确「证据累积 / 真相确认 / 再重构」三步验收标准。

## 2. 后端：证据库与合并引擎

- [x] 2.1 改造 `ingest_project_materials`：URL/文本按 `source_id` 写入 `evidence/`，禁止再写单一 `website_crawled_raw.md` 作为唯一官网稿。
- [x] 2.2 实现 `merge_facts_from_evidence`：内置 Standard Fact Keys + `ALIAS_TO_STANDARD` 别名归一；按标准 `fact_key` 判定新增 / 更新 / 冲突；写出 `ledger/facts.jsonl` + 生成 `facts.md` 视图，并同步刷新根目录 `raw_extracted_facts.md` 兼容镜像。
- [x] 2.3 扩展 API：`GET evidence`、`GET/DELETE evidence/{id}`、`GET facts`、`POST facts/.../confirm`、`POST facts/confirm-all`、`POST facts/resolve-conflict`；升级 ingest 响应含 `merge` 摘要。
- [x] 2.4 CLI：`geo ingest` 行为对齐；新增 `geo facts` 列表/确认（最小可用，支持 `--confirm-all`）。

## 3. 下游消费对齐

- [x] 3.1 `rewrite.py` 优先读 `ledger` 中 `confirmed` 事实；冲突未决时降级沿用历史版本或安全占位，禁止静默编造。
- [x] 3.2 RAG 诊断 / 实体图谱读取路径对齐真相源（至少不覆盖回旧盲文件优先）。
- [x] 3.3 回归：无证据、仅证据未确认、有确认三种项目状态均可跑通。

## 4. 前端 Step 3

- [x] 4.1 证据列表 UI（来源、字数、时间、重抓/删除，0 Emoji 纯 Lucide 图标与专业排版）。
- [x] 4.2 真相源面板（状态 Tag、冲突仲裁单选、一键确认所有无冲突项、确认事实计数）。
- [x] 4.3 抓取/粘贴 Toast 展示 merge 摘要；语料预览区文案澄清「需执行重构才更新交付物」。
- [x] 4.4 复制/空态：新项目零证据时的引导文案（先抓首页，再抓关于我们/产品页）。

## 5. 验证

- [x] 5.1 同项目连续抓两个不同 URL：证据为 2 份，非覆盖成 1 份。
- [x] 5.2 构造同键异值：出现 `conflict`，确认前 rewrite 不把冲突值当唯一口径。
- [x] 5.3 确认后执行普林斯顿重构：语料数字可溯源到证据摘录。
- [x] 5.4 存量 nextgeo / 样例项目迁移后 Step 3 可打开且列表非空（或明确空态）。
- [x] 5.5 别名归一单测：`delivery_time` / `delivery_cycle_days` 均映射为 `metric.delivery_days`，异值可检出 conflict。
- [x] 5.6 兼容镜像：ledger 更新后根目录 `raw_extracted_facts.md` 存在且内容与 `facts.md` 视图一致。

## 6. 续完善：脏块增量重构（待实现）

- [x] 6.1 定义母盘块模型与事实键绑定表；落盘 `03_corpus_meta.json`（facts_hash / block_hashes）。
- [x] 6.2 实现脏块计算；无脏块时 rewrite 返回 noop；默认 `incremental`，保留 `--full`；**缺失母盘或 meta 时优雅降级 full**。
- [x] 6.3 双重定位切块：`<!-- BLOCK:block.<id> -->` 优先，回退 `## 一/二/三/四`；脏块模板直出 + 未脏块锁定拷贝；更新 SOP-03。
- [x] 6.4 单测：只改 `metric.delivery_days` 时仅 metrics（及相关 FAQ）变脏；缺 meta 首次跑走 full。

## 7. 续完善：重复 / 逻辑矛盾（待实现）

- [x] 7.1 近义重复簇检测（同键多陈述或高相似 statement）API + UI Tag。
- [x] 7.2 落地最小规则表 v1（`region_exclusive` / `source_license_mutex` / `price_free_vs_premium` / `delivery_inversion`）→ `logic_conflict`；未解决阻止 pin 与阶段四。
- [x] 7.3 单测：互斥区域与工期倒挂可检出。

## 8. 续完善：发前对照卡（待实现）

- [x] 8.1 `corpus/pin` 快照工作母盘到 `outputs/pinned/`。
- [x] 8.2 `corpus/diff`：无 pinned 时 `against: "none"`（不 500）；有基线时输出 facts_diff + dirty_blocks + strategy 硬规则（block > new_article > patch > noop）。
- [x] 8.3 Step 3/4 衔接 UI：对照卡 + 四色语义 Tag；`block` 禁用分发入口；0 Emoji / Lucide。
- [x] 8.4 CLI：`corpus-diff` / `corpus-pin`；端到端：改一数 → 增量重构 → diff 策略为 patch。
