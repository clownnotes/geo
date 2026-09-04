# Design: 多主流大模型真实联网探测与 Citation 角标全自动捕获审计引擎 (第 30 维)

## 1. 架构定位与基座复用原则 (No Parallel Engine)

第 30 维**绝不另起炉灶或新建第二套平行探测引擎 (`live_auditor.py`)**。本设计严格在现网第 18 维基座（`tools/geo/probing.py`）与底层大模型客户端（`tools/geo/llm.py`）之上进行**增量扩展**，并作为向第 28 维高管交付门户（`tools/geo/share.py`）反哺真实 Citation 战果的**闭环交付层**。

### 1.1 强制复用的现有核心函数清单

| 依赖模块 | 强制复用函数 / 资产 | 职责说明 |
|:---|:---|:---|
| **`tools.geo.probing`** | `run_live_probing(project_id, ...)` | 主流大模型并发调用、实时时延统计与结果聚合 |
| | `SandboxSimulator` | 离线确定性沙箱，无 API Key 时 100% 毫秒级稳定产出高保真模拟数据 |
| | `normalize_url(url)` | 协议/www/锚点/查询参数规范化 |
| | `extract_domain(url)` | 提取根域名 |
| | `is_ledger_asset_eligible(url, status)` | 校验 URL 是否非空且状态为 `("published", "verified")` |
| | `trace_citations_against_ledger(citations, project_id)` | **真实反向对账核心逻辑**（仅 `exact_hit` / 路径前缀 `domain_hit` 计入我方资产） |
| **`tools.geo.dist_bot`** | `get_distribution_ledger(project_id)` | 读取唯一的真实分发存活台账（`dist_ledger.json`） |
| **`tools.geo.llm`** | `call_model_raw(model, ...)` | OpenAI 兼容标准 HTTP 请求与超时保护 |
| | `resolve_api_key(model)` | 环境变量与多别名链式降级提取 |
| | `PROVIDERS` | 全局大模型配置字典（本案将元宝作为增量并入此字典） |

---

## 2. 第 30 维核心增量设计

### 2.1 增量 1：腾讯元宝纳入 `llm.py` PROVIDERS 矩阵

在 `tools/geo/llm.py` 的 `PROVIDERS` 字典中新增腾讯混元/元宝标准配置：
```python
"yuanbao": {
    "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
    "default_model": "hunyuan-standard",
    "api_key_envs": ["GEO_YUANBAO_API_KEY", "YUANBAO_API_KEY", "HUNYUAN_API_KEY"],
    "model_envs": ["YUANBAO_MODEL", "HUNYUAN_MODEL"],
}
```
通过统一的 `resolve_api_key("yuanbao")` 与 `call_model_raw("yuanbao", ...)` 调用，使探测矩阵从 3 厂商平滑扩展至 4 厂商。

### 2.2 增量 2：Citation 提取器正则补丁与本土化符号兼容

在 `tools/geo/probing.py` 的 `extract_citations_and_sources()` 中，增强通道 A 的角标正则匹配器，补全本土化模型特有符号：
1. **中文方头括号角标**：`【(?P<idx>\d+)】`；
2. **带前缀中文角标**：`\[注(?P<idx>\d+)\]`；
3. **Markdown 内联外链**：`\[(?P<title>[^\]]+)\]\((?P<url>https?://[^\)]+)\)`；
4. **裸 URL 引用**：`https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s\)\"\'<>]*)*`；
5. **尾部 Sources 清单**：兼容 `参考资料` / `参考信源` / `Sources` / `References`。

### 2.3 增量 3：严谨对账口径与分发台账字段对齐 (反假命中铁律)

- **严格继承 18 维对账口径**：
  - **`exact_hit`**：大模型引用 URL 的规范化形式，与 `dist_ledger.json` 中 `channels.*.url` 或 `custom_links[].url` 100% 精确相等，或者与 `official_url` 精确相等；
  - **`domain_hit`**：仅当域名属于我方官方域名，或者属于渠道域名（如 `zhuanlan.zhihu.com/p/xxx`）且**文章路径前缀或 ID 与我方台账资产完全一致**；
  - **🔴 铁律禁令**：**严禁将裸渠道域名（如只要出现 `zhihu.com`、`toutiao.com`）算作我方命中**。同站未匹配到我方具体资产的链接，一律判定为 `third_party_or_competitor`（或 `organic_same_channel`），**绝不计入 `dist_matched_count`，绝不虚抬命中率**。
- **真实台账字段对齐**：
  - 严格读取 `dist_bot.get_distribution_ledger(project_id)` 返回的真实结构：
    - `channels: { "<channel_id>": { "url": "...", "status": "published"|"verified", ... } }`
    - `custom_links: [ { "url": "...", "status": "published"|"verified", ... } ]`
  - 仅通过 `is_ledger_asset_eligible(url, status)` 过滤合格外链。

### 2.4 增量 4：极速重对账函数 `reconcile_existing_trace()`

在 `tools/geo/probing.py` 中新增独立对账函数：
```python
def reconcile_existing_trace(project_id: str, portal_sync: bool = True) -> Dict[str, Any]:
    """
    不调用大模型 API，直接读取已有 outputs/live_probing_trace.json，
    重新比对最新 outputs/dist_ledger.json，刷新对账统计并重新导出 18/30 号公文。
    """
```
- **使用场景**：代运营人员补充回填了分发外链，需要立刻刷新对账数据，耗时 < 100ms；
- **同步刷新**：更新 `live_probing_trace.json` 中的 `reconciliation_summary`，并触发公文与高管门户同步。

### 2.5 增量 5：公文 30 号生成 (`30_多主流大模型真实联网探测与Citation角标反查审计报告.md`)

在 `export_probing_report()` 中，除既有 18 号公文外，同步导出第 30 维高管专属审计公文：
- 产物路径：`projects/<id>/outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md`；
- 数据指标：与 `live_probing_trace.json` 100% 同源，包含：实测平均 SOV、Top1 首推率、真实 Citation 捕获总数、我方分发直接采纳命中数、采纳命中率。

---

## 3. 高管只读交付门户联动设计 (`tools/geo/share.py`)

### 3.1 `live_citation_summary` 数据契约

在 `tools/geo/share.py` 的 `compile_portal_data()` 中挂载高管级字段：
```python
# 1. 尝试读取 outputs/live_probing_trace.json
trace_file = os.path.join(out_dir, "live_probing_trace.json")
if os.path.isfile(trace_file):
    # 解析真实指标
    live_citation_summary = {
        "status": "audited",
        "last_audited_at": trace_data.get("probed_at", ""),
        "total_prompts": summary.get("total_prompts", 0),
        "avg_sov": summary.get("avg_sov", 0.0),
        "top1_rate": summary.get("top1_rate", 0.0),
        "total_citations": summary.get("total_citations", 0),
        "dist_matched_count": summary.get("dist_matched_count", 0),
        "citation_hit_rate": summary.get("citation_hit_rate", 0.0),
        "models_covered": list(trace_data.get("models_tested", {}).keys()),
        "audit_doc": "outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md"
    }
else:
    # 严格优雅降级，绝不捏造假数据
    live_citation_summary = {
        "status": "never_run",
        "avg_sov": 0.0,
        "citation_hit_rate": 0.0,
        "total_citations": 0
    }
```

### 3.2 门户前端战果呈现 (`web/share.html`)
在门户大屏第四板块新增【全网大模型真实引用与信源对账】卡片，动态展示：
- 真实首推率与角标捕获率；
- 真实命中外链列表（来源平台、标题、存活状态）。

---

## 4. 接口与命令行设计

### 4.1 CLI 命令行接口 (`tools/geo/cli.py`)

统一整合在 `geo probe` 命令体系下，并提供 `geo probe-audit` 作为语义别名：
```bash
# 1. 标准并发联网探测并导出 18/30 号公文与 trace.json
geo probe <project_id> --models doubao,deepseek,kimi,yuanbao --sample 10 --report

# 2. 离线快速对账（不调大模型 API，直接重算最新分发台账）
geo probe <project_id> --reconcile-only

# 3. 语义别名调用（帮助文案中明确标明底层基于 probing.py）
geo probe-audit <project_id> --reconcile-only
```

### 4.2 Web 后端 API (`tools/geo/server.py`)

| 路由端点 | HTTP 方法 | 鉴权约束 | 参数 / 请求体 | 响应说明 |
|:---|:---|:---|:---|:---|
| `/api/projects/{id}/probing/run` | `POST` | Bearer Token 强鉴权 | `{"models": [...], "sample": 5, "live": false}` | 触发联网探测，复用既有路由 |
| `/api/projects/{id}/probing/reconcile` | `POST` | Bearer Token 强鉴权 | 无 | 触发 `--reconcile-only` 极速重对账，返回最新对账指标 |
| `/api/projects/{id}/probing/trace` | `GET` | Bearer Token 强鉴权 | 无 | 获取 `live_probing_trace.json` 完整数据 |


