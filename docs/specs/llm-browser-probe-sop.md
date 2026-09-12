# LLM 浏览器探测协作 SOP（Cursor 出题 × 反重力 Safari 执行）

> 目的：把「大模型现在怎么说」变成可对比的项目证据，指导配置与复测，而不是一次性聊天存档。

## 1. 何时触发（不要每一步全量爬）

| 触发点 | 做什么 | `probe_status` |
|--------|--------|----------------|
| **新公司建档完成后** | 管理台进入 **00 侦察建档**，再跑品类/品牌/人物基线 | `unprobed` → 回填后 `baseline_ready` |
| 官网/名片段/llms.txt 重大变更后 | 同题复测，对比提及/URL/立场 | → `awaiting_retest`，复测通过再回 `baseline_ready` |
| 周报或人工发现异常 | 加测相关问句 | 视情况 `awaiting_retest` |
| OpenSpec 策略讨论需要事实 | 先写 probes 互评，再晋升证据库 | 不强制改 yaml |

**建档原则**：

- 允许空词库、空竞品；**空比瞎填好**。
- 新建后默认进入管理台 **阶段零：侦察建档**（不直达阶段一体检）。
- 未侦察也可进阶段一～五，但会强确认提示；**批量生成草稿**在未侦察时硬拦截（CLI 可用 `--force` 仅内测）；已有基线「进入流水线」直达阶段一。
- **一句话业务**（15～80 字）新建必填，供 `probe-script` 出题。
- 无客户官网时勾选托管：固定 `https://{client_id}.baicl.cc` 且 `site_pending: true`（此时剧本跳过官网/URL 题）。

## 2. 角色分工

1. **管理台阶段 0**：展示状态、复制 CLI、**上传 probe JSON 预览/确认回填**（默认合并词库）。  
2. **Cursor**：`geo probe-script` / `probe-preview` / `probe-apply --merge`。  
3. **反重力**：用**已登录** Safari 打开豆包，按剧本提问并落盘。  
4. **产品**：确认真实竞品与监测问句。

管理台**不**驱动 Safari；回填可走 Web 上传或 CLI。

## 3. 落盘两层

1. **讨论层**：`openspec/changes/<变更>/probes/probe_<模型>_YYYYMMDD.md` + `.json`  
2. **真源层（共识后）**：`projects/{id}/raw_materials/evidence/`（`upsert_evidence`）+ 可选 `outputs/competitor_probe_*.json`

未互评的 probes **不要**直接当 yaml 真理；晋升时保留原 probes 不覆盖。

## 4. 每条记录必填字段

- `query` / 可选 `follow_up`  
- `mentioned_self` / `url_present` / `citation_to_self`  
- `standpoint`：推荐 | 中性 | 负面 | 不认识 | 误解  
- `competitors_extracted[]`：`name` / `url` / `is_real`（人工抽查）  
- `hallucination_detected`（如有）

## 5. 回填到项目（CLI；阶段 0 可复制）

```bash
# 1) 生成必测题（首轮不问自带竞品名；site_pending 时无官网题）
python3 -m tools.geo probe-script <project_id>

# 2) 反重力按剧本在豆包实战，落盘 probe_*.json

# 3) 预览候选竞品与建议问句
python3 -m tools.geo probe-preview <project_id> --file path/to/probe_*.json

# 4) 确认后写入 keywords / competitors，并置 baseline
# 有精修词库时务必 --merge，避免覆盖
python3 -m tools.geo probe-apply <project_id> --file path/to/probe_*.json --merge --yes
```

管理台等价路径：阶段零「上传 probe JSON → 预览回填 → 确认回填」（默认勾选合并）。

写入字段：

| yaml 字段 | 含义 |
|-----------|------|
| `probe_status` | `unprobed` \| `baseline_ready` \| `awaiting_retest` |
| `probe_baseline_id` | 如 `probe:doubao:20260910` |
| `probe_baseline_at` | ISO 日期 |
| `business_one_liner` | 一句话业务 |
| `site_pending` | 托管占位官网 |
| `competitors` / `keywords` | 回填结果 |

长尾扩写应在 `baseline_ready` 之后再用 `geo intent` / 演进工具。

## 6. 与 GEO 效果的关系

探测本身不提高排名；它告诉你该补名片段、消幻觉、对打谁；无复测的「只爬一次」不能证明有效。阶段一体检看官网技术可见性，与侦察互补、不可互相替代。

## 7. 安全

只用产品已登录会话；不自动化账密；不绕过平台风控；名单人工抽假。
