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

- 允许空选题、空竞品；**空比瞎填好**。创建时不要灌「意图词库」。
- 新建后默认进入管理台 **阶段零：侦察建档**（不直达阶段一体检）。
- 探活 = 基线体检：用少量真人长问摸清 AI 认不认识你们、推谁；问句确认后可晋升为**第一波选题**。
- 未侦察也可进阶段一～五，但会强确认提示；**批量生成草稿**在未侦察、或无已确认合格长问时硬拦截。
- **一句话业务**（15～80 字）新建必填；高质量出题与模板保底都会用到。
- 无客户官网时勾选托管：固定 `https://{client_id}.baicl.cc` 且 `site_pending: true`（此时剧本跳过官网/URL 题）。
- 规范真源：OpenSpec `2026-09-16-创建与阶段零先探活再长问选题/design.md`。

## 2. 角色分工

1. **Cursor / IDE（出题优先）**：读 `project.yaml` 与既有探针结果，写出**真人会搜的**必测题 JSON（自然口语、覆盖维度、复测针对失败点）。管理台提供「复制高质量出题提示词」。  
2. **管理台阶段 0**：扫描 `outputs/`、预览/确认回填；**模板一键出题**（`probe-script`）仅作断网/赶工保底，质量一般。  
3. **反重力**：用**已登录** Safari 打开豆包，按剧本提问并落盘结果 JSON。  
4. **产品**：确认预览中的竞品与监测问句后点确认回填。

人机原则：**题单质量优先于一键速度**；回填与文件扫描由管理台完成；人只处理登录态豆包实战与确认回填。管理台**不**驱动 Safari。


## 3. 第二步闭环（反重力 × 豆包）——勿漏步

> 一句话：开工要交**两样**（说明书 + 剧本文件）；问完再交**第二次**（收工说明书）才会写文件；管理台「检查有没有落盘」只是看文件在不在，再去做第 3 步回填。  
> 只粘贴开工说明书就让反重力开跑、不附剧本，经常题不全；不问完就落盘、或不点检查看徽章，会以为「状态已更新」等于成功。

### 3.1 你交给反重力的到底是什么

| 交付物 | 够不够单独用 | 说明 |
|--------|--------------|------|
| 仅剧本文件 | **不够** | 缺执行规则与落盘路径 |
| 仅「①开工说明书」 | **不够** | 必须再 @ 剧本文件，且问完还要贴「②收工说明书」 |
| ①+剧本 + 问完后②收工 | **完整** | 与管理台 C+D、F 对应 |

### 3.2 操作清单（与管理台一一对应）

| 序 | 动作 | 管理台 |
|----|------|--------|
| A | 反重力已开；Safari 豆包已登录；豆包**新开聊天** | （自检） |
| B | 确认本轮题单 | （只读） |
| C+D | 粘贴①开工说明书，并立刻 @/附上剧本文件；**两样齐了再让它问** | **复制①开工说明书** + **复制剧本路径** |
| E | 等待反重力按题问完并汇总（此时还不写结果文件） | （等待） |
| F | 粘贴②收工说明书 → 等反重力写完 JSON → 点「检查有没有落盘」，看徽章「已生成/尚未生成」 | **复制②收工说明书** + **检查有没有落盘** |
| 回填 | 第 3 步选已有结果 → 预览 → 确认回填 | 预览 / 确认 |

「检查有没有落盘」= 重新扫磁盘并刷新徽章；**不是**替你写文件。Toast 会明确说「落盘成功」或「尚未落盘」。

### 3.3 结果 JSON 最小骨架

```json
{
  "probed_at": "2026-09-12T18:00:00+08:00",
  "operator": "antigravity",
  "browser": "safari",
  "model_ui": "doubao",
  "items": [
    {
      "query": "……",
      "follow_up": "……",
      "mentioned_self": false,
      "url_present": false,
      "citation_to_self": false,
      "standpoint": "不认识",
      "hallucination_detected": false,
      "competitors_extracted": [
        { "name": "……", "url": "……", "is_real": true }
      ],
      "doubao_verdict": "一句话摘要"
    }
  ]
}
```

`standpoint` 取值：`推荐` | `中性` | `负面` | `不认识` | `误解`（可写更细，但勿空）。

## 4. 落盘两层

1. **讨论层**：`openspec/changes/<变更>/probes/probe_<模型>_YYYYMMDD.md` + `.json`  
2. **真源层（共识后）**：`projects/{id}/raw_materials/evidence/`（`upsert_evidence`）+ 可选 `outputs/competitor_probe_*.json`

未互评的 probes **不要**直接当 yaml 真理；晋升时保留原 probes 不覆盖。

## 5. 每条记录必填字段

- `query` / 可选 `follow_up`  
- `mentioned_self` / `url_present` / `citation_to_self`  
- `standpoint`：推荐 | 中性 | 负面 | 不认识 | 误解  
- `competitors_extracted[]`：`name` / `url` / `is_real`（人工抽查）  
- `hallucination_detected`（如有）

## 6. 回填到项目（CLI；阶段 0 可复制）

```bash
# 1) 生成必测题（首轮不问自带竞品名；site_pending 时无官网题）
python3 -m tools.geo probe-script <project_id>

# 2) 反重力按剧本在豆包实战，落盘 competitor_probe_*.json（见第 3 节）

# 3) 预览候选竞品与建议问句
python3 -m tools.geo probe-preview <project_id> --file path/to/competitor_probe_*.json

# 4) 确认后写入 keywords / competitors，并置 baseline
# 有精修词库时务必 --merge，避免覆盖
python3 -m tools.geo probe-apply <project_id> --file path/to/competitor_probe_*.json --merge --yes
```

管理台等价路径：阶段零第三步 **A→E**（选取结果 JSON → 预览 → 确认回填 → 刷新状态）。CLI 仅备用。

### 6.1 第三步（管理台读盘，推荐）

| 序 | 动作 |
|----|------|
| A | 在列表中点选已存在的 `competitor_probe_*.json`（刷新列表可检测新落盘） |
| B | 预览回填（服务端直接读磁盘，无需访达） |
| C | 确认回填 |
| D | 刷新状态 → 进入阶段一 |

备用：本机上传文件或 CLI。

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

## 7. 与 GEO 效果的关系

探测本身不提高排名；它告诉你该补名片段、消幻觉、对打谁；无复测的「只爬一次」不能证明有效。阶段一体检看官网技术可见性，与侦察互补、不可互相替代。

## 8. 安全

只用产品已登录会话；不自动化账密；不绕过平台风控；名单人工抽假。
