# Design: 新建客户侦察后回填竞品与意图词

## 0. 分期锁定（Antigravity × Cursor 共识）

| 期次 | 做 | 不做 |
| :--- | :--- | :--- |
| **一期** | 拆创建假占位；空壳建档；`probe_*` 字段 + profile 读写；列表/弹窗文案与徽章；CLI 剧本与回填 | Web JSON 上传；专用 `/probe/*` HTTP |
| **二期** | 管理台上传 probe → 预览 → 确认写入 | 内嵌 Safari/豆包自动化 |

## 1. 架构原则

```
【管理台·一期】建壳 + 侦察状态展示 + 文案引导
     │
     ▼
【Cursor + CLI】probe-script → 反重力×豆包实战 → probe-preview / apply
     │
     ▼
【人】删假竞品、选定主靶与 8～15 条监测问句
     │
     ▼
【profile API】写入 keywords / competitors / probe_status=baseline_ready
```

管理台**不**驱动 Safari。

## 2. 数据模型（project.yaml）

```yaml
probe_status: unprobed          # unprobed | baseline_ready | awaiting_retest
probe_baseline_id: ""           # 如 probe:doubao:20260910
probe_baseline_at: ""           # ISO 日期，可选
keywords: []                    # 允许创建时为空；回填后建议 8～15 起步
competitors: []                 # 允许为空；回填后主靶 2～3 + 可选标杆
```

兼容：缺省字段读作 `unprobed`；已有真实词库/竞品的老项目可不强制改状态（UI「未标记」可接受）。

### 2.1 经现有 profile 写入（一期）

`tools/geo/utils.py` → `update_project_profile` 的 `scalar_keys` **追加**：

- `probe_status`
- `probe_baseline_id`
- `probe_baseline_at`

`keywords` / `competitors` 已有列表更新路径则复用；无则一期由 CLI `probe-apply` 直接改 yaml，二期再统一。

**不新增** `PATCH /probe/status` 之类接口。

### 2.2 探测回填预览结构（CLI 中间态；二期可变 API body）

```json
{
  "project_id": "nextgeo",
  "source_probe": "probe:doubao:YYYYMMDD",
  "competitor_candidates": [
    {"name": "徐州东昊", "url": "", "is_real": "pending", "mentioned_in_queries": ["..."]}
  ],
  "keyword_suggestions": [
    {"query": "...", "priority": "P0", "reason": "品类选型且竞品占位"}
  ],
  "hallucinations": ["老白串到安徽短视频公司"]
}
```

确认写入：仅人勾选 / `is_real=true` 的竞品进 `competitors`；人勾选问句进 `keywords`。

## 3. 必测题模板（首轮）

输入：`brand_name`、`industry`、`city?`、`person_anchor?`、`official_url?`

| # | 维度 | 模板意图 |
|---|------|----------|
| 1～2 | 品类选型 | `{city}{industry/GEO} 找谁 / 哪家靠谱` |
| 3 | 价格套路 | 报价区间、常见坑 |
| 4 | 品牌认知 | `{brand} 是做什么的` |
| 5 | URL | `{brand} 官网`（观察 `url_present`） |
| 6 | 人物（可选） | `{person} 与 {brand}/{legal} 关系`（禁止人名裸奔） |
| 7+ | 扩展 | 全国名单等；**首轮不带竞品名对比题** |

字段对齐 SOP：`query` / `follow_up` / `mentioned_self` / `url_present` / `citation_to_self` / `standpoint` / `competitors_extracted[]` / `hallucination_detected`。

## 4. 接口与脚本

### 一期

| 能力 | 落点 | 作用 |
| :--- | :--- | :--- |
| 空壳创建 | `POST /api/projects` | 空列表保持 `[]`；写入 `probe_status: unprobed`；**删除** `or ["行业核心推荐词"…]` / `or ["竞品A"…]` 兜底 |
| 状态与主档 | `POST /api/projects/{id}/profile` | 经扩展后的 `scalar_keys` 写 `probe_*`；列表字段按现有 profile 逻辑 |
| 必测题 | CLI `geo probe-script <id>` | 输出 6～10 题 JSON/Markdown 到 stdout 或 `outputs/` |
| 回填 | CLI `geo probe-preview` / `geo probe-apply` | 读 probe 文件 → 预览 → 确认写入 yaml |

### 二期（本变更不实现）

| 方法 | 路径 | 作用 |
| :--- | :--- | :--- |
| POST | `/api/projects/{id}/probe/script` | 同 CLI |
| POST | `/api/projects/{id}/probe/preview` | 上传 JSON |
| POST | `/api/projects/{id}/probe/apply` | Web 确认写入 |

## 5. 前端交互（一期）

### 5.1 新建弹窗

- 去掉意图词 `required`；竞品保持可选。
- 说明：「可空着创建；建议 Cursor×反重力豆包侦察后用 CLI 回填。空比瞎填好。」
- 「AI 推演 50」→「必测题草稿（6～10）」或隐藏/降级；长尾扩写提示「基线后用 geo intent」。
- 0 Emoji；Lucide + Tag。
- 成功 toast：提示下一步 IDE 侦察 SOP 路径。

### 5.2 企业管理表

- **侦察**角标：未侦察 / 已有基线 / 待复测（读 `probe_status`）。
- 词库 0 →「待回填」。

### 5.3 资料抽屉（一期）

- 展示 `probe_status`、`probe_baseline_id`。
- 文案指引 CLI 回填路径；**不做**文件上传控件（二期）。

## 6. 与现有模块边界

| 现有 | 关系 |
| :--- | :--- |
| `llm-browser-probe-sop.md` | 建档触发 + `probe_status` + CLI 回填 |
| `geo intent` / 推演 50 | 时机后移到 `baseline_ready` 后 |
| `geo monitor` | `unprobed` 可跑，报告提醒未经侦察 |
| OpenSpec probes 两层 | 不改变 |

## 7. 风险与约束

- 豆包名单幻觉 → `is_real` 人工抽查。
- 空词库进流水线 → 不得静默写假占位。
- 严禁管理台存豆包账密或自动登录。
- 视觉：0 Emoji。

## 8. 验收标准（一期）

1. 仅填四壳字段可创建；词库=0、竞品空、`probe_status=unprobed`；磁盘 yaml **不含**「竞品A/B」「行业核心推荐词」。
2. CLI 可生成必测题；对样例 probe 可 preview/apply 后状态为 `baseline_ready`。
3. 列表可见未侦察徽章；新建无 Emoji、无「必须 50 问」诱导。
4. 本地 `127.0.0.1:8088`；不推生产。
