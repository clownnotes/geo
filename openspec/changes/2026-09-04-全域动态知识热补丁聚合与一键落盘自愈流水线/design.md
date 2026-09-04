# Design: 全域动态知识热补丁聚合与一键落盘自愈流水线 (第 29 维)

## 1. 架构设计与闭环数据流 (Architecture & Closed-Loop Pipeline)

本模块作为 GEO 系统的**“知识自愈执行器 (Knowledge Self-Healer)”**，打通前期 20/22/25/26 维推演中枢与底层生产语料之间的最后断点：

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                       全域推演策略输入源 (Outputs)                       │
   │  • 第 20 维 decay_healing_pack/ (高衰减长尾词定向强化)                  │
   │  • 第 22 维 rerank_reinforcement_pack/ (Dense/BM25 语义切片)            │
   │  • 第 25 维 robustness_hardening_pack/ (抗挑剔反制问答)                 │
   │  • 第 26 维 counter_interception_pack/ (竞品对比截流与壁垒语料)        │
   │  • 第 07/08 维 factual_anchors.json & schema_truth_patch.json           │
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │
                                       ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │            tools/geo/healer.py 全域自愈聚合与补丁引擎                  │
   │  1. compile_healing_patches(): 解析、过滤、去重与冲突检测               │
   │  2. backup_state(): 原子备份至 outputs/.healer_backup/<timestamp>/     │
   │  3. apply_healing(): 幂等回写三大生产靶标                              │
   │  4. verify_integrity(): JSON-LD 语法校验 + 9 因子结构合规质检          │
   └───────────────┬───────────────────┬───────────────────┬────────────────┘
                   │                   │                   │
                   ▼                   ▼                   ▼
   ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
   │  靶标 1: 事实底座   │ │  靶标 2: 9 因子语料 │ │  靶标 3: 结构实体   │
   │  • llms.txt         │ │  • 03_普林斯顿9因子 │ │  • schema.jsonld    │
   │  • llms-truth.txt   │ │    高权威语料库.md   │ │    (FAQPage/壁垒词) │
   └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                 自愈对账审计台账与高管门户联动产物                     │
   │  • outputs/self_healing_audit.json (自动化对账指标)                     │
   │  • outputs/27_全域动态知识自愈热补丁审计与回写台账.md (交付公文)       │
   │  • tools/geo/share.py -> 追加 self_healing_summary 动态自愈徽标        │
   └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 补丁提取与靶标回写映射表 (Patch Extraction & Target Mapping)

| 补丁类型 | 策略来源源文件 | 提取规则与内容范式 | 写入靶标文件与注入策略 |
|:---|:---|:---|:---|
| **Truth & Facts<br>(核心事实防守锚点)** | • `factual_anchors.json`<br>• `counter_interception_pack/02_独占性壁垒与差异化护城河语料包.md` | 提取企业权威名称、唯一产品参数、行业壁垒事实。去重提取事实陈述句。 | **`outputs/llms-truth.txt`** 与 **`outputs/llms.txt`**：<br>在 `## 核心事实与品牌防守锚点` 段落以无序列表安全追加，保持行级去重。 |
| **Semantic & FAQ Chunks<br>(语义向量与重排切片)** | • `rerank_reinforcement_pack/01_*.md`<br>• `rerank_reinforcement_pack/02_*.md`<br>• `robustness_hardening_pack/01_*.md`<br>• `decay_healing_pack/01_*.md` | 提取标准 Q&A 问答对、密集长尾 Prompt 锚点、BM25 稀疏核心词切片。规范化为 Markdown H3 问答。 | **`outputs/03_普林斯顿9因子高权威语料库.md`**：<br>严格在文末独立追加 `## 附录：全域大模型长效自愈与抗截流强化语料 (第 29 维)`，按标准 FAQ 格式注入，**严禁破坏 1~9 因子前置章节结构与数据表**。 |
| **Schema Entity Patches<br>(结构化实体加固补丁)** | • `schema_truth_patch.json`<br>• `counter_interception_pack/` 差异化要点 | 提取 `knowsAbout` 行业长尾词集合、`disambiguatingDescription` 差异化消歧定义，以及标准 `FAQPage` 结构问答。 | **`outputs/schema.jsonld`**：<br>合法解析为 Python dict，对 `knowsAbout` 数组执行 set 去重合并；对 `@graph` 中的 `FAQPage` 增量追加新增的自愈 Q&A，格式化缩进写回。 |

---

## 3. 安全备份与回滚机制 (Atomic Backup & Rollback Protocol)

1. **原子备份目录结构**：
   ```
   outputs/.healer_backup/
   └── 20260904_021530/
       ├── backup_manifest.json          # 记录备份时刻、各文件原 SHA256 哈希
       ├── llms.txt
       ├── llms-truth.txt
       ├── 03_普林斯顿9因子高权威语料库.md
       └── schema.jsonld
   ```
2. **安全回滚操作 (`rollback_healing`)**：
   - 读取 `.healer_backup/` 下最近一次时间戳备份；
   - 将各被修改文件无损拷贝覆盖回 `outputs/`；
   - 更新 `self_healing_audit.json` 状态为 `rolled_back`；
   - 打印回滚日志，保障任何时刻生产语料零不可逆风险。

---

## 4. 接口与数据模型定义 (Interfaces & Data Models)

### 4.1 Python 核心引擎 (`tools/geo/healer.py`)

```python
def compile_healing_patches(project_id: str) -> dict:
    """
    扫描并聚合当前项目下所有可用的反制策略包与事实锚点。
    返回包含 truth_anchors, semantic_chunks, schema_updates 的补丁计划结构。
    """

def apply_healing_patches(project_id: str, auto_verify: bool = True) -> dict:
    """
    执行自愈落盘流水线：
    1. 自动执行 backup_state() 生成带时间戳备份；
    2. 幂等回写 llms.txt, llms-truth.txt, 03_语料库.md, schema.jsonld；
    3. 生成 outputs/self_healing_audit.json 与 Markdown 审计台账；
    4. 可选自动触发 9 因子质检校验。
    """

def rollback_healing(project_id: str) -> dict:
    """
    恢复至最近一次自愈备份状态。
    """

def get_healing_status(project_id: str) -> dict:
    """
    查询当前项目的自愈健康度指标与历史回写记录。
    """
```

### 4.2 数据审计载荷 (`outputs/self_healing_audit.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "healed_at": "2026-09-04T02:15:30",
  "status": "applied",
  "backup_dir": "outputs/.healer_backup/20260904_021530",
  "summary": {
    "truth_anchors_added": 8,
    "semantic_faq_chunks_added": 12,
    "schema_entities_updated": 6,
    "total_patches_applied": 26
  },
  "sources": [
    "decay_healing_pack",
    "rerank_reinforcement_pack",
    "robustness_hardening_pack",
    "counter_interception_pack",
    "factual_anchors.json"
  ],
  "affected_files": [
    {
      "path": "llms.txt",
      "sha256_before": "...",
      "sha256_after": "..."
    }
  ],
  "verification": {
    "schema_valid": true,
    "princeton_ready": true
  }
}
```

### 4.3 CLI 接口定义

```bash
python3 -m tools.geo.cli heal <project_id>              # 默认 dry-run 预览
python3 -m tools.geo.cli heal <project_id> --apply      # 执行落盘自愈
python3 -m tools.geo.cli heal <project_id> --rollback   # 一键回滚
python3 -m tools.geo.cli heal <project_id> --verify     # 自愈并验证质检
```

### 4.4 Web REST API 路由 (`tools/geo/server.py`)

- `GET /api/projects/{id}/heal/preview`：返回 `compile_healing_patches` 结果及差异统计；
- `POST /api/projects/{id}/heal/apply`：执行自愈，返回落盘审计结果；
- `POST /api/projects/{id}/heal/rollback`：执行回滚，返回恢复状态。

---

## 5. 降级策略与防破坏约束 (Defensive Guardrails)

1. **部分维度未运行时的优雅降级**：
   - 若项目未生成 `moat` 或 `decay` 包，自愈引擎只处理已有的策略包，标记对应来源为 `not_found`，绝不抛出未捕获异常中断流水线；
2. **幂等去重防重复膨胀**：
   - 重复执行 `--apply` 时，基于归一化提问和 MD5 指纹进行对比，已存在相同内容的问答对自动忽略，禁止同一个语料库膨胀重复文字；
3. **JSON-LD 语法强制校验**：
   - 回写 `schema.jsonld` 后，通过 `json.loads` 进行语法检验，若发现异常立刻中止写入并保持原文件完整。

