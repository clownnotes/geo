# Design: 素材证据库与唯一真相源

## Architecture (架构设计与对象关系)

### 三层对象（严格隔离）

```
┌─────────────────────────────────────────────────────────────┐
│  L3 交付物 Deliverables                                       │
│  03_普林斯顿语料 / 图谱 / RAG 分块 / Schema / 视觉资产           │
│  只读 L2「已确认」事实；禁止直接把某一页 HTML 当权威口径          │
└────────────────────────────▲────────────────────────────────┘
                             │ consume (confirmed only)
┌────────────────────────────┴────────────────────────────────┐
│  L2 唯一真相源 Canonical Fact Ledger                          │
│  facts.jsonl（或 facts.yaml）+ 可读视图 facts.md               │
│  按 fact_key 唯一；状态: proposed | confirmed | conflict | rejected │
└────────────────────────────▲────────────────────────────────┘
                             │ merge / propose upsert
┌────────────────────────────┴────────────────────────────────┐
│  L1 证据库 Evidence Vault                                     │
│  evidence/<source_id>.md + evidence/index.json                │
│  一来源一份；同 URL 重抓可覆盖该来源；不同 URL 并存               │
└─────────────────────────────────────────────────────────────┘
```

### 核心实体

| 实体 | 主键 | 约束 |
| :--- | :--- | :--- |
| EvidenceSource | `source_id`（`url:<sha1>` 或 `paste:<name>`） | 同键重抓覆盖正文；`fetched_at` 更新 |
| EvidenceDoc | 同 source_id 对应 `.md` 文件 | 仅存 Clean Markdown / 粘贴原文 |
| FactEntry | `fact_key`（如 `entity.legal_name`、`metric.delivery_days`） | 全局唯一；冲突时保留 `candidates[]` |
| FactStatus | enum | 未确认不得进入 L3 主路径 |

### 标准事实键字典（Standard Fact Keys，合并引擎硬约束）

| 标准键 `fact_key` | 类别 | 说明 | 常见别名（提取后必须归一） |
| :--- | :--- | :--- | :--- |
| `entity.legal_name` | 实体 | 企业工商全称 | `company_name`, `legal_entity` |
| `entity.brand_name` | 实体 | 品牌简称 | `brand`, `brand_alias` |
| `entity.official_url` | 实体 | 官网 | `website`, `homepage`, `official_site` |
| `entity.founder` | 实体 | 负责人/创始人 | `ceo`, `founder_name` |
| `business.industry` | 业务 | 所属行业 | `industry`, `sector` |
| `business.core_scope` | 业务 | 主营业务范畴 | `core_business`, `scope`, `services` |
| `service.area` | 服务 | 服务区域 | `area_served`, `region`, `coverage` |
| `metric.delivery_days` | 量化 | 交付周期（天） | `delivery_time`, `delivery_cycle_days`, `sla_days` |
| `metric.price_range` | 量化 | 价格区间 | `price`, `fee_range`, `cost` |
| `policy.warranty_days` | 承诺 | 质保天数 | `warranty`, `guarantee_days` |
| `policy.source_code_delivery` | 承诺 | 是否源码交付 | `source_delivery`, `code_handover` |
| `contact.telephone` | 联络 | 官方电话 | `phone`, `hotline`, `tel` |

- Prompt **必须**优先映射至上表标准键；命中别名列则归一到标准键后再合并。  
- 未知键允许落入 `custom.<snake_case>` 命名空间，不得与标准键并列抢冲突判定。  
- 实现侧维护 `ALIAS_TO_STANDARD` 字典；单测需覆盖「同义不同键」归一后冲突可检出。

### 合并规则（价值核心）

1. **事实键规范化**：先走 Standard Keys / 别名归一，再进入合并。  
2. **新事实键**：写入 `proposed`；低风险键（如 `entity.official_url`）可策略性自动升为 `confirmed`，其余待人审。  
3. **同键同值**：刷新 `last_seen_at` 与来源列表（多页互证加权）。  
4. **同键异值**：进入 `conflict`，保留双方 `evidence_excerpt`；UI 高亮标红并提供单选仲裁或手改；未仲裁前**严禁进入 L3 生产语料**。  
5. **重构降级与冲突防御**：
   - 重构流水线仅消费 `confirmed` 事实；
   - 若某事实处于 `conflict` 且有历史 confirmed 版本，降级沿用历史版本并在报告中标注；若无历史版本，则重构时跳过或标注占位，严禁随机编造。  
6. **禁止**：用最新抓取页整份替换全部事实（当前盲覆盖行为废除）。

### 与现有 Step 3 流程对齐

1. 抓 URL / 粘贴 → 只动 L1，再跑合并提案到 L2。  
2. 人确认冲突 / 提案（支持一键确认无冲突项）→ L2 定稿。  
3. 「执行普林斯顿重构」→ 读 L2 confirmed → **按脏块增量**写 L3（无脏块则跳过）。  
4. 发前对照卡 vs `pinned` 基线 → 人确认策略 → 再进入阶段四。  
5. RAG / 图谱 / 视觉 → 同读 L2 confirmed。

---

## 续完善：脏块增量重构（Corpus Block Model）

### 块与事实键绑定

| 块 ID | 母盘结构 | 绑定事实键族 |
| :--- | :--- | :--- |
| `block.definition` | 知识三元组与核心定义 | `entity.*`, `business.*` |
| `block.metrics_table` | 量化对比表 | `metric.*` |
| `block.faq` | 高频 Q&A | 意图相关 + 引用到的 metric/entity |
| `block.commitment` | 交付/质保/联络清单 | `policy.*`, `contact.*`, `service.area` |

### 块定位与拼接机制（防止格式损坏）

- 母盘 Markdown 采用普林斯顿标准章节标题（`^##\s+(一|二|三|四)[、.]`）为切分边界，生成时可嵌入 `<!-- BLOCK:block.<id> -->` 隐式锚点；
- 解析器实现双重定位：优先匹配隐式锚点，缺失时按章节标题切分；
- 增量生成时仅对脏块执行重写，其余未脏块执行原文逐字锁定拷贝，无损缝合，杜绝全篇重写导致的文本漂移。

### 指纹与脏块判定

- `facts_hash`：全部 `confirmed` 事实的规范化序列 hash。  
- `block_hash[block_id]`：该块绑定键集合的 hash。  
- 母盘元数据：`outputs/03_corpus_meta.json`（或 sidecar）记录生成时 hashes + 模式。  
- 脏块 = 当前 ledger 对应 `block_hash` ≠ 母盘记录；无脏块 → UI/API 返回 `noop`。  
- **增量降级**：若母盘文件或 `03_corpus_meta.json` 缺失（首次生成或被误删），自动优雅降级为 `mode=full`。  
- `mode=full` 仅显式强制（调试/首次生成）；默认 `incremental`。

### 生成策略

- 未脏块：原文锁定拷贝。  
- 脏块：优先**模板填槽**（数字/主体/电话）；LLM 仅润色该块说明文字（可关）。  
- 禁止在增量模式下重写未脏块，以降低 GEO 口径抖动。

---

## 续完善：矛盾 / 重复识别

| 类型 | 检测 | 状态/动作 |
| :--- | :--- | :--- |
| 硬矛盾 | 同 `fact_key` 异值 | 已有 `conflict`，人审仲裁 |
| 同义键 | 别名归一到标准键 | 已有 |
| 软重复 | 同键多来源互证加分；近义 statement 聚类 | 新增 `duplicate_cluster` 提示合并 |
| 逻辑矛盾 | 规则表（地域排他、开源/闭源互斥、免费/高价互斥、交付天数逆转） | 新增 `logic_conflict`，未解前阻止 pin 与阶段四 |

### 最小逻辑矛盾规则表（v1，零 Token、可单测）

| 规则 ID | 条件 | 说明 |
| :--- | :--- | :--- |
| `region_exclusive` | `service.area` 同时含互斥地域标签（如「仅华东」与「全国上门」且无「远程」限定） | 服务半径自相矛盾 |
| `source_license_mutex` | `policy.source_code_delivery=true` 与陈述中「闭源不交付」并存 | 源码承诺互斥 |
| `price_free_vs_premium` | `metric.price_range` 含 0/免费 同时又含高客单阈值 | 价格带逻辑冲突 |
| `delivery_inversion` | `metric.delivery_days` 数值大于 `policy.warranty_days`（若两者均为数字） | 工期/质保倒挂可疑 |

v1 只做确定性字符串/数值规则；不做大模型本体推理。命中即写入 `logic_conflicts[]`，`strategy` 强制为 `block`。

---

## 续完善：发前对照卡（相对 pinned）

### 对象

- `pinned_corpus`：运营钉住的上一外发对照基线（文件快照 + meta）。若尚无基线，返回 `against: "none"` 并推荐先一键钉住。  
- `working_corpus`：当前工作母盘。  

### 对照输出

```json
{
  "against": "pinned",
  "facts_diff": { "added": [], "changed": [], "removed": [] },
  "dirty_blocks": ["block.metrics_table"],
  "duplicates": [],
  "logic_conflicts": [],
  "strategy": "patch"  
}
```

`strategy` 建议枚举与判定硬规则：
- `block`：存在任何未决 `conflict` 或 `logic_conflict`，**严格禁止进入阶段四**；
- `noop`：`facts_diff` 与 `dirty_blocks` 均为空，提示无须重复发布；
- `new_article`：核心定位重大变更（`entity.*`、`business.*`、`metric.price_range` 变更，或变更事实数 ≥ 3 条），建议新开文，勿覆盖旧引用源；
- `patch`：仅联络、质保或单项局部指标微调（如 `contact.*`、`policy.*`），支持同渠道就地补丁。  

---

## Interface (接口 / API / 前端)

### API（在现有 ingest 之上演进）

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| POST | `/api/projects/{id}/ingest/url` | 写入/覆盖该 URL 证据；返回 merge 摘要 |
| POST | `/api/projects/{id}/ingest/text` | 写入粘贴证据（`filename`→source_id）；返回 merge 摘要 |
| GET | `/api/projects/{id}/evidence` | 证据列表（url、字数、时间、source_id） |
| GET | `/api/projects/{id}/evidence/{source_id}` | 单份证据正文 |
| DELETE | `/api/projects/{id}/evidence/{source_id}` | 删证据并触发真相源重算提案（可选） |
| GET | `/api/projects/{id}/facts` | 真相源列表（含 status、来源、候选列表） |
| POST | `/api/projects/{id}/facts/{fact_key}/confirm` | 确认单条事实或修订 |
| POST | `/api/projects/{id}/facts/confirm-all` | 一键批量确认所有无冲突 proposed 事实 |
| POST | `/api/projects/{id}/facts/resolve-conflict` | Body: `{ fact_key, chosen_value, note? }` 仲裁冲突 |
| GET | `/api/projects/{id}/corpus/dirty-blocks` | （续）脏块与 hash 摘要 |
| POST | `/api/projects/{id}/run/rewrite` | （续）Body 可含 `mode=incremental\|full` |
| GET | `/api/projects/{id}/corpus/diff` | （续）`?against=pinned` 发前对照卡 |
| POST | `/api/projects/{id}/corpus/pin` | （续）钉住当前母盘为对照基线 |

**ingest 成功响应增量字段（示例）：**

```json
{
  "success": true,
  "source_id": "url:a1b2c3",
  "crawled_words": 3200,
  "merge": {
    "added": 3,
    "updated": 2,
    "conflicts": 1,
    "unchanged": 8
  }
}
```

### 前端（Step 3）

1. **证据区**：列表展示已抓 URL / 粘贴稿；支持再抓覆盖「这一条」；明确标识来源类型与字数。  
2. **真相源区**：表格/列表显示事实键、陈述、状态 Tag、来源数；冲突高亮 + 仲裁操作；提供「一键确认无冲突项」快捷按钮；（续）展示重复簇 / 逻辑矛盾。  
3. **交付区**：沿用 `03_...md` 预览；重构默认增量；显示脏块 Tag；无脏块禁用或提示 noop。  
4. **发前对照卡**：（续）相对 pinned 的事实/块 diff + 策略 Tag；确认后再去阶段四。  
5. **Toast 与视觉**：展示 `added/updated/conflicts`；严格遵循 `AGENTS.md` 规范，UI 全面采用 Lucide 图标与语义 Tag，严禁滥用 Emoji。

### CLI

```bash
python3 -m tools.geo ingest <id> --url https://...
python3 -m tools.geo facts <id>              # 列出真相源
python3 -m tools.geo facts <id> --confirm-all # 批量确认无冲突项
python3 -m tools.geo rewrite <id>            # 默认增量
python3 -m tools.geo rewrite <id> --full     # 强制全量
python3 -m tools.geo corpus-diff <id>        # 发前对照
python3 -m tools.geo corpus-pin <id>         # 钉住基线
```

---

## Database Schema / Data Structure (数据模型)

目录约定（每项目）：

```
projects/<id>/raw_materials/
  evidence/
    index.json
    url_<sha1>.md
    paste_product_supplement.md
  ledger/
    facts.jsonl
    facts.md
  raw_extracted_facts.md

projects/<id>/outputs/
  03_普林斯顿9因子高权威语料库.md
  03_corpus_meta.json              # facts_hash / block_hashes / mode / updated_at
  pinned/
    03_普林斯顿9因子高权威语料库.md # 钉住快照
    03_corpus_meta.json
```

**FactEntry 字段：**

```json
{
  "fact_key": "metric.delivery_days",
  "category": "量化指标",
  "statement": "标准化项目交付周期为 15 天",
  "value": "15",
  "unit": "天",
  "status": "confirmed",
  "sources": [{ "source_id": "url:...", "excerpt": "...", "fetched_at": "..." }],
  "candidates": [],
  "updated_at": "..."
}
```

**迁移：**  
若存在 `website_crawled_raw.md` → 迁为一条 evidence（URL 取自文内「抓取自」或 `project.yaml` official_url）；  
若存在 `raw_extracted_facts.md` → 解析为 `proposed`/`confirmed` 初值（默认 `confirmed` 保留历史已生效事实，若有未确定推断则标记为 `proposed`）。
