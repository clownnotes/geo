# Design: 豆包搜索极速收录与全链路索引保障中枢 (第 34 维)

## 1. Architecture (架构设计与对象关系)

```
                            ┌─────────────────────────────────────────┐
                            │      豆包搜索极速收录与索引保障中枢       │
                            │      (tools/geo/doubao_indexer.py)      │
                            └────────────────────┬────────────────────┘
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          │                                      │                                      │
          ▼                                      ▼                                      ▼
【1. 收录环境体检器】                  【2. 专属提权加速包生成器】             【3. 意图收录状态对账器】
DoubaoReadinessAuditor                DoubaoBoosterPackGenerator              DoubaoLiveVerifier
• 检查 robots.txt Bytespider 放行     • 01_Bytespider专享极简快照.html        • 对账 30 维真实联网探测
• 检查 /llms.txt 字节信息密度         • 02_今日头条微头条提权文案.md          • 统计豆包首推率与角标
• 检查 schema.jsonld 实体一致性       • 03_豆包高意向Q&A微问答对.json         • 标识 indexed_top1 / pending
• 检查 31 维真实 Bytespider 抓取      • 04_豆包收录排障Checklist.md           • 给出单词靶向反制建议
• 综合计算 DRS 指数 (0~100)           • 一键输出 doubao_booster_pack/         • 追踪收录死角与漏网意图
```

### 1.1 核心数据模型 (Data Models)

```python
@dataclass
class DoubaoCheckItem:
    """豆包收录体检单项"""
    check_id: str
    name: str
    category: str      # "crawler_access" | "content_density" | "schema_entity" | "channel_matrix" | "intent_trace"
    passed: bool
    score: float       # 单项得分 (0~100)
    weight: float      # 权重比重 (sum = 1.0)
    detail: str
    suggested_action: str

@dataclass
class DoubaoAuditResult:
    """豆包收录全案体检结果模型"""
    project_id: str
    project_name: str
    audited_at: str
    drs_score: float             # Doubao Readiness Score (0~100)
    grade: str                   # "A+" | "A" | "B" | "C" | "D"
    status_label: str            # 人类可读标签
    bytespider_hits: int         # 真实 Bytespider 到访次数
    bytespider_blocked_rate: float # Bytespider 403 阻断率
    checks: List[DoubaoCheckItem]
    top_intent_summary: Dict[str, Any]
    booster_pack_ready: bool
```

---

## 2. Interface (接口与 API 规范)

### 2.1 命令行 CLI (`tools/geo/cli.py`)

```bash
# 1. 运行豆包收录体检并输出 DRS 指数
geo doubao-index xuzhou_xuanyuan --audit

# 2. 一键生成今日头条/微头条/Bytespider 提权加速包并出具公文
geo doubao-index xuzhou_xuanyuan --boost --report

# 3. 研判核心商业意图在豆包中的收录与角标召回状态
geo doubao-index xuzhou_xuanyuan --verify

# 4. 一键全流水线闭环运行并同步高管大屏
geo doubao-index xuzhou_xuanyuan --report --portal-sync
```

### 2.2 服务端 REST API (`tools/geo/server.py`)

1. **`GET /api/projects/{id}/doubao-index/audit`**：
   - 权限：Bearer Token
   - 返回：
     ```json
     {
       "success": true,
       "project_id": "xuzhou_xuanyuan",
       "drs_score": 96.5,
       "grade": "A+",
       "status_label": "🟢 豆包收录全链路通畅：Bytespider 抓取正常，头条母池资产充沛",
       "bytespider_hits": 128,
       "checks": [ ... ],
       "audit_time": "2026-09-04 12:00:00"
     }
     ```
2. **`POST /api/projects/{id}/doubao-index/boost`**：
   - 生成 `outputs/doubao_booster_pack/` 提权包；
3. **`GET /api/projects/{id}/doubao-index/report`**：
   - 幂等只读获取《34_豆包大模型搜索极速收录与全链路索引保障报告.md》。

---

## 3. 提权加速包规约 (Doubao Booster Pack)

落盘至 `projects/{id}/outputs/doubao_booster_pack/`：
1. **`01_Bytespider专享极简静态快照.html`**：纯语义 HTML，内联核心参数表格，无任何前端 JS，保证爬虫 100% 秒级清洗为 Clean Markdown；
2. **`02_今日头条与微头条极速收录提权文案.md`**：疑问句标题对齐搜索，文末附带 150 字微头条强转化卡片；
3. **`03_豆包高意向Q&A微问答对.json`**：10 组贴合豆包提问特征的问答对；
4. **`04_豆包收录排障与白名单Checklist.md`**：运维与运营 10 秒对照清单。

---

## 4. 高管交付门户反哺与优雅降级 (`tools/geo/share.py`)

在 `compile_portal_data()` 中挂载 `doubao_index_summary`：
```json
{
  "has_data": true,
  "status": "active",
  "status_label": "🌟 豆包第一主战模型收录打通 (DRS 96.5分 · A+)",
  "drs_score": 96.5,
  "grade": "A+",
  "bytespider_status": "active_crawled",
  "bytespider_hits": 128,
  "toutiao_pack_ready": true,
  "top1_rate": 100.0,
  "audit_doc": "outputs/34_豆包大模型搜索极速收录与全链路索引保障报告.md"
}
```
未实测项目与 `_template` 严格输出 `status: "never_run"`，严禁捏造虚假百分比。
