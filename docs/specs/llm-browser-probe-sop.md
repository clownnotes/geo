# LLM 浏览器探测协作 SOP（Cursor 出题 × 反重力 Safari 执行）

> 目的：把「大模型现在怎么说」变成可对比的项目证据，指导配置与复测，而不是一次性聊天存档。

## 1. 何时触发（不要每一步全量爬）

| 触发点 | 做什么 |
|--------|--------|
| 新公司建档完成后 | 品类选型 + 品牌名 + 关键人物锚点基线探测 |
| 官网/名片段/llms.txt 重大变更后 | 同题复测，对比提及/URL/立场 |
| 周报或人工发现异常（被骂、被串名、竞品占位突变） | 加测相关问句 |
| OpenSpec 策略讨论需要事实 | 先写 probes 互评，再晋升证据库 |

## 2. 角色分工

1. **Cursor**：写剧本、定字段、解析回传、更新竞品/名片段/监测词建议。  
2. **反重力**：用**已登录** Safari（或约定浏览器）打开目标模型网页，按剧本提问并落盘。  
3. **产品**：确认是否晋升为项目真源、是否进入 apply。

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

## 5. 与 GEO 效果的关系

探测本身不提高排名；它告诉你：

- 该补哪段名片段、该消哪类幻觉；  
- 本地该对打谁；  
- 改完有没有进步（复测对比）。

无复测的「只爬一次」不能证明有效。

## 6. 安全

只用产品已登录会话；不自动化账密；不绕过平台风控；名单人工抽假。
