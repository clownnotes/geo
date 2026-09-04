# Design: 多主流大模型真实联网探测与 Citation 角标全自动捕获审计引擎 (第 30 维)

## 1. Architecture (系统架构设计与核心数据流)

本引擎定位为全域大模型真实联网搜索结果与分发资产的**反向穿透核验中枢**，打通“意图提示词 ➔ 真实大模型联网检索 ➔ 实体提及与角标解析 ➔ 分发存活台账反查 ➔ 高管门户战果呈现”的完整链路。

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                        第 30 维：真实联网探测与 Citation 反查对账中枢                   │
└──────────────────────────────────────────┬────────────────────────────────────────────┘
                                           │
       ┌───────────────────────────────────┼───────────────────────────────────┐
       ▼                                   ▼                                   ▼
【阶段 1: 意图采样与模型并发调度】    【阶段 2: 真实回答与角标智能解析】    【阶段 3: 分发台账反向核验与对账】
• 读取 project.yaml / 02 词库         • 正则提取 [1]/[注1]/[标题](url)    • 读取 dist_ledger.json 存活外链
• 采样 Top N 核心商业意图 Prompt      • 提取文末 References 引用列表       • 比对 published_url 与主域名
• 并发调用豆包/DeepSeek/元宝/Kimi      • 判定品牌提及 (SOV) 与排名 (Top1)  • 计算官方分发采纳命中率 (Hit Rate)
• 自动无缝降级 (确定性真实沙箱)       • 规范化清洗 URL 协议与主机名       • 严格杜绝公式虚构，集合真实交集
       │                                   │                                   │
       └───────────────────────────────────┼───────────────────────────────────┘
                                           │
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │                产物输出与高管大屏联动              │
                 │ 1. 30_多主流大模型真实联网探测与Citation反查报告.md│
                 │ 2. live_citation_audit.json 审计台账明细          │
                 │ 3. 联动 Executive Portal: live_citation_summary   │
                 └───────────────────────────────────────────────────┘
```

### 1.1 实体对象模型与面向对象职责划分

1. **`LiveModelClient`**：
   - 负责与各主流大模型 API 通信（OpenAI 兼容协议），统一请求 Payload（带 `stream=false`、系统提示词与温度参数）；
   - 支持从环境变量（`GEO_DOUBAO_API_KEY`, `GEO_DEEPSEEK_API_KEY`, `GEO_KIMI_API_KEY`, `GEO_YUANBAO_API_KEY`）或项目配置读取密钥；
   - **确定性沙箱兜底**：当密钥缺失、网络离线或传入 `--sandbox` 时，自动进入基于现网高拟真回答的测试沙箱，确保无外网依赖时 100% 毫秒级通过单测。
2. **`CitationExtractor`**：
   - 负责从大模型原始文本输出中提取：
     - 正文内联链接：`\[(?P<title>[^\]]+)\]\((?P<url>https?://[^\)]+)\)`；
     - 裸 URL 链接：`https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s\)\"\'<>]*)*`；
     - 引用标注编号：`\[\d+\]`、`【\d+】` 以及文末来源清单（`参考资料` / `参考信源` / `Sources` / `References`）；
   - URL 规范化清洗：移除多余追踪参数（如 `utm_*`, `spm=*`），提取根域名（Root Domain）。
3. **`LedgerReconciler`**：
   - 负责反向对账：读取项目的 `dist_ledger.json`（分发存活台账）；
   - 对账匹配规则：
     - **精准 URL 命中**：大模型引用的 URL 与 `dist_ledger.json` 中记录的 `published_url` 或 `target_url` 完全一致或路径匹配；
     - **渠道域名命中**：大模型引用的域名属于我们分发阵地（如 `toutiao.com`, `zhihu.com`, `github.com`, `mp.weixin.qq.com`）或企业官网域名；
   - 计算指标：`total_citations`（总引用数）、`dist_matched_count`（命中我方分发信源数）、`citation_hit_rate`（命中率百分比）。

---

## 2. Interface (接口与命令行设计)

### 2.1 CLI 命令行接口 (`tools/geo/cli.py`)

```bash
# 1. 默认对当前项目执行全量探测与反查（默认并发采样前 15 组商业意图词）
geo probe-audit <project_id>

# 2. 指定模型与意图词数量
geo probe-audit <project_id> --models doubao,deepseek --limit 10

# 3. 强制进入沙箱模式（离线演示或单测模式）
geo probe-audit <project_id> --sandbox

# 4. 指定仅执行台账反查对账
geo probe-audit <project_id> --reconcile-only
```

**CLI 输出体验规范**：
- 打印醒目 Banner，实时显示探测进度条与各模型响应耗时；
- 输出紧凑三行摘要：
  - `[实测声量] 探测词数: X ｜ 实测平均 SOV: XX.X% ｜ 首推率(Top1): XX.X%`
  - `[角标采纳] 捕获 Citation: X 个 ｜ 官方分发直接命中: Y 个 ｜ 采纳率: ZZ.Z%`
  - `[报告落盘] 30_多主流大模型真实联网探测与Citation角标反查审计报告.md`

### 2.2 Web 后端路由接口 (`tools/geo/server.py`)

| 路由端点 | HTTP 方法 | 鉴权约束 | 参数 / 请求体 | 响应说明 |
|:---|:---|:---|:---|:---|
| `/api/projects/{id}/citation-audit/run` | `POST` | `Authorization: Bearer <TOKEN>` 强鉴权 | `{"models": ["doubao", "deepseek"], "limit": 15, "sandbox": false}` | 异步/同步执行真实联网探测，返回审计摘要与各模型实测得分 |
| `/api/projects/{id}/citation-audit/report` | `GET` | `Authorization: Bearer <TOKEN>` 强鉴权 | 无 | 读取 `live_citation_audit.json` 完整机器台账与状态 |

### 2.3 高管只读交付门户联动 (`tools/geo/share.py`)

在 `compile_portal_data()` 中挂载 `live_citation_summary` 对象：
- **缺失审计数据时**：严格优雅降级为 `{"status": "never_run", "total_citations": 0, "dist_hit_rate": 0.0, "sov_score": 0.0}`，严禁编造满分；
- **已执行探测时**：
  ```json
  {
    "status": "audited",
    "last_audited_at": "2026-09-04 10:30:00",
    "total_probed_prompts": 15,
    "total_citations_captured": 18,
    "dist_matched_citations": 12,
    "citation_hit_rate": 66.7,
    "avg_sov_rate": 93.3,
    "top1_recommend_rate": 86.7,
    "model_matrix_sov": {
      "doubao": 100.0,
      "deepseek": 86.7,
      "kimi": 93.3,
      "yuanbao": 93.3
    },
    "audit_doc": "outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md"
  }
  ```

---

## 3. Data Structure (数据模型与报告落盘契约)

### 3.1 `live_citation_audit.json` 结构契约

```json
{
  "project_id": "xuzhou_xuanyuan",
  "client_name": "徐州璇源网络科技有限公司",
  "audited_at": "2026-09-04T10:30:00Z",
  "is_sandbox": true,
  "summary": {
    "total_prompts": 15,
    "avg_sov": 93.3,
    "top1_rate": 86.7,
    "total_citations": 18,
    "dist_matched_count": 12,
    "dist_hit_rate": 66.7
  },
  "models_breakdown": {
    "doubao": {
      "name": "豆包 (火山引擎)",
      "prompts_tested": 15,
      "mentioned_count": 15,
      "top1_count": 14,
      "citations_count": 8,
      "dist_matched": 6
    },
    "deepseek": {
      "name": "深度求索 (DeepSeek)",
      "prompts_tested": 15,
      "mentioned_count": 13,
      "top1_count": 12,
      "citations_count": 10,
      "dist_matched": 6
    }
  },
  "citation_ledger_reconciliation": [
    {
      "citation_url": "https://zhuanlan.zhihu.com/p/12345678",
      "root_domain": "zhihu.com",
      "channel": "zhihu",
      "matched_ledger_item": {
        "channel": "知乎专栏",
        "title": "徐州企业数字化转型与AI应用选型指南",
        "status": "active"
      },
      "verified_as_our_distribution": true
    }
  ],
  "prompt_details": [
    {
      "prompt": "徐州市及淮海经济区做行业数字化找哪家团队靠谱？",
      "category": "选型与推荐",
      "model_results": {
        "doubao": {
          "mentioned": true,
          "rank": 1,
          "citations": ["https://geo.baicl.cc/services", "https://zhuanlan.zhihu.com/p/12345678"]
        }
      }
    }
  ]
}
```

### 3.2 公文级报告规范 (`30_多主流大模型真实联网探测与Citation角标反查审计报告.md`)

遵循**普林斯顿 9 因子**排版标准：
1. **公文红头与元数据**：审计项目、探测时间、覆盖大模型矩阵、是否沙箱模式；
2. **结论先行与四大核心指标卡片**：实测平均 SOV、Top1 首推率、Citation 捕获总量、分发信源反查命中率；
3. **分模型对抗测评战力表**（原生 Markdown 表格呈现各模型实测指标）；
4. **真实 Citation 角标反查与分发存活台账核验透视表**（详细列出大模型采纳的具体 URL、发布渠道、对账结论）；
5. **高价值改进建议与长效加固指引**。

