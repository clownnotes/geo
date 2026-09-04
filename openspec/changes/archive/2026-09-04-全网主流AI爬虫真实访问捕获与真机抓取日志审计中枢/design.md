# Design: 全网主流AI爬虫真实访问捕获与真机抓取日志审计中枢 (第 31 维)

## 1. 架构定位与基座复用原则 (No Parallel Engine)

本规范坚决杜绝从零建造第二套不相干的日志分析系统。本设计以“**主动抓取仿真 (第 12 维 `crawler.py`) ➔ 访问日志反向审计 (第 31 维 `spider_auditor.py`) ➔ 高管大屏战果反哺 (第 28 维 `share.py`)**”为闭环链条：

### 1.1 核心依赖与复用清单

| 依赖模块 | 强制复用资产 / 函数 | 职责说明 |
|:---|:---|:---|
| **`tools.geo.crawler`** | `SPIDER_USER_AGENTS` | 复用并增量扩充主流大模型爬虫标准指纹库 |
| **`tools.geo.utils`** | `load_project_config`、`PROJECTS_DIR`、`print_banner` 等 | 项目路径寻址、标准 CLI 格式化与公用日志输出 |
| **`tools.geo.share`** | `compile_portal_data` | 高管只读交付门户战果反哺与数据大屏组装 |
| **`tools.geo.server`** | `GeoWebHandler`、`require_auth` | 统一的 Web 路由分发与 Bearer Token 强鉴权机制 |

---

## 2. 爬虫特征指纹库与识别分类 (`spider_auditor.py`)

系统建立全面的 **AI 爬虫指纹注册表 (AI_SPIDER_REGISTRY)**，覆盖中国本土五大生态及国际顶尖通用大模型爬虫：

```python
AI_SPIDER_REGISTRY = {
    "bytespider": {
        "name": "字节跳动·豆包 / 头条爬虫",
        "family": "doubao",
        "patterns": [r"Bytespider", r"BytedanceDatabase"],
        "category": "domestic_primary",
        "weight": 0.40,
        "description": "国内市场份额第一，抓取频次与时效性最高，主要流入今日头条与豆包推荐池"
    },
    "baidu": {
        "name": "百度·文心一言爬虫",
        "family": "baidu",
        "patterns": [r"Baiduspider", r"Baiduspider-render"],
        "category": "domestic_primary",
        "weight": 0.20,
        "description": "百度百科与文心一言底座，偏好抓取官网结构化 Schema 与百科实体"
    },
    "deepseek": {
        "name": "DeepSeek·深度求索爬虫",
        "family": "deepseek",
        "patterns": [r"DeepSeek-Crawler", r"DeepSeekBot"],
        "category": "domestic_primary",
        "weight": 0.15,
        "description": "技术决策高地，主要抓取开源架构、/llms.txt 与 Markdown 参数技术长文"
    },
    "moonshot": {
        "name": "月之暗面·Kimi 爬虫",
        "family": "kimi",
        "patterns": [r"MoonshotBot", r"Kimi-Crawler"],
        "category": "domestic_primary",
        "weight": 0.10,
        "description": "长文本深度研报池，对万字行业白皮书与统计数据量化表格进行全网长文本抓取"
    },
    "hunyuan": {
        "name": "腾讯·混元 / 元宝爬虫",
        "family": "yuanbao",
        "patterns": [r"TencentHunyuanBot", r"HunyuanBot", r"mp_spider"],
        "category": "domestic_primary",
        "weight": 0.05,
        "description": "腾讯微信搜一搜独占阵营，抓取公众号图文与企鹅号资产"
    },
    "gptbot": {
        "name": "OpenAI·GPTBot / ChatGPT",
        "family": "openai",
        "patterns": [r"GPTBot", r"ChatGPT-User", r"OAI-SearchBot"],
        "category": "international",
        "weight": 0.05,
        "description": "全球通用大模型基座，抓取权重极高，优先访问 /llms.txt 与 robots.txt"
    },
    "claudebot": {
        "name": "Anthropic·ClaudeBot",
        "family": "claude",
        "patterns": [r"ClaudeBot", r"Claude-Web", r"anthropic-ai"],
        "category": "international",
        "weight": 0.02,
        "description": "逻辑推理与代码生成旗舰，极度重视 Clean Markdown 与语义连贯性"
    },
    "perplexity": {
        "name": "Perplexity AI 实时检索爬虫",
        "family": "perplexity",
        "patterns": [r"PerplexityBot"],
        "category": "international",
        "weight": 0.02,
        "description": "全球 AI Search 标杆，实时抓取外部事实并生成高密度 Citation 角标"
    },
    "google": {
        "name": "Google Gemini·扩展爬虫",
        "family": "google",
        "patterns": [r"Google-Extended", r"GoogleOther"],
        "category": "international",
        "weight": 0.01,
        "description": "Google Gemini 训练语料与 AI Overview 专用抓取爬虫"
    }
}
```

---

## 3. 日志解析器与审计算法模型 (`audit_access_logs`)

### 3.1 日志格式兼容与提取
支持工业级主流日志格式：
1. **Nginx Combined 格式**：`$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"`；
2. **Caddy / 简易日志格式**；
3. 解析正则表达式：
   `r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>[^"]+)"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)"'`。

### 3.2 确定性高保真沙箱 (`SandboxLogGenerator`)
当项目未提供外部 `access.log` 文件时，系统自动启动离线沙箱模拟器：
- 基于项目配置（官网域名、行业、已发布的页面清单），生成符合时间时序的真实高保真访问日志（覆盖 Bytespider、Baiduspider、DeepSeek 等的 200/304 正常访问与少量 404 探测）；
- **保障铁律**：零外部网络依赖，全库测试秒级通过，数据严谨确定，不漂移。

### 3.3 审计量化指标与算法定义
- **$TotalHits$**：识别出的大模型爬虫访问总行数；
- **$UniqueBots$**：成功捕获的独立 AI 爬虫厂商数；
- **$SuccessRate$**：HTTP 状态码为 200 或 304 的比例：
  $$\text{SuccessRate} = \frac{\text{Count}(\text{status} \in [200, 304])}{TotalHits} \times 100\%$$
- **$BlockedRate$**：HTTP 状态码为 403 的比例（WAF 误杀阻断风险）：
  $$\text{BlockedRate} = \frac{\text{Count}(\text{status} = 403)}{TotalHits} \times 100\%$$
- **$CoreAssetCoverage$**：核心事实资产抓取率：
  - 核心资产目标集：`["/llms.txt", "/llms-full.txt", "/schema.jsonld", "/robots.txt", "/"]`；
  - 统计实际被大模型爬虫抓取到的核心资产种类占总核心资产种类的百分比。
- **综合健康度评级 (Health Grade)**：
  - 🟢 `safe` (优秀): $\text{SuccessRate} \ge 90\%$，且 $\text{BlockedRate} = 0\%$，且 `/llms.txt` 被抓取过；
  - 🟡 `warning` (预警): $\text{SuccessRate} < 90\%$，或未抓取到 `/llms.txt`，或 $TotalHits < 10$；
  - 🔴 `danger` (高危): 存在 $\text{BlockedRate} > 0\%$（检测到大模型爬虫被 403 拦截）。

---

## 4. 产物与高管门户联动设计 (`share.py` & `web/share.html`)

### 4.1 数据结构契约 (`outputs/spider_access_audit.json`)
```json
{
  "project_id": "xuzhou_xuanyuan",
  "client_name": "徐州璇源网络科技有限公司",
  "audited_at": "2026-09-04 12:00:00",
  "is_sandbox": false,
  "summary": {
    "total_ai_hits": 128,
    "unique_spiders_count": 6,
    "success_rate_pct": 98.4,
    "blocked_rate_pct": 0.0,
    "core_assets_coverage_pct": 100.0,
    "health_grade": "safe",
    "health_status_label": "🟢 大模型爬虫抓取畅通（无阻断）",
    "llms_txt_hit_count": 42,
    "last_crawled_at": "2026-09-04 11:45:12"
  },
  "spider_breakdown": {
    "bytespider": { "name": "字节跳动·豆包 / 头条爬虫", "hits": 68, "pct": 53.1, "status_200": 68, "status_403": 0 },
    "baidu": { "name": "百度·文心一言爬虫", "hits": 28, "pct": 21.9, "status_200": 27, "status_403": 0 },
    "deepseek": { "name": "DeepSeek·深度求索爬虫", "hits": 16, "pct": 12.5, "status_200": 16, "status_403": 0 },
    "gptbot": { "name": "OpenAI·GPTBot / ChatGPT", "hits": 10, "pct": 7.8, "status_200": 10, "status_403": 0 },
    "moonshot": { "name": "月之暗面·Kimi 爬虫", "hits": 6, "pct": 4.7, "status_200": 5, "status_403": 0 }
  },
  "core_assets_audit": [
    { "path": "/llms.txt", "name": "大模型专享 Markdown 摘要清单", "hits": 42, "status": 200, "is_healthy": true },
    { "path": "/schema.jsonld", "name": "Schema.org 知识图谱三元组", "hits": 18, "status": 200, "is_healthy": true },
    { "path": "/robots.txt", "name": "爬虫放行与站点引流协议", "hits": 35, "status": 200, "is_healthy": true }
  ],
  "report_path": "projects/xuzhou_xuanyuan/outputs/31_全网主流AI爬虫真实访问捕获与真机抓取日志审计报告.md"
}
```

### 4.2 门户数据反哺与降级契约 (`tools/geo/share.py`)
在 `compile_portal_data()` 中挂载 `spider_access_summary` 字典：
- **存在物理账本时**：
  `status: "audited"`，`has_data: True`，映射真实 `total_ai_hits`、`success_rate_pct`、`llms_txt_hit_count`、`spider_breakdown`；
- **不存在物理账本时**：
  严格优雅降级为 `status: "never_run"`，`has_data: False`，各项指标为 0，前台卡片展示“待执行爬虫真机访问日志审计”。

### 4.3 门户前端卡片呈现 (`web/share.html`)
在第 5 部分（存活台账）与第 5.1 部分（30维 Citation 对账）之后，新增：
- **【全网主流 AI 爬虫真实到访心跳流与资产抓取大屏 (第 31 维)】**
- 展示：24 小时 AI 爬虫到访总频次、字节豆包/百度/DeepSeek 活跃状态、`/llms.txt` 入库正常指示灯、阻断预警指示灯。

---

## 5. 接口与命令行设计

### 5.1 CLI 命令行接口 (`tools/geo/cli.py`)
```bash
# 1. 对指定项目执行真实日志审计（若不传 --log-file，自动探测或调用确定性沙箱）
geo spider-audit <project_id> [--log-file /path/to/access.log] [--report]

# 示例:
python3 -m tools.geo spider-audit xuzhou_xuanyuan --report
```

### 5.2 Web 后端 API (`tools/geo/server.py`)
| 路由端点 | HTTP 方法 | 鉴权约束 | 参数 / 请求体 | 响应说明 |
|:---|:---|:---|:---|:---|
| `/api/projects/{id}/spider-audit/run` | `POST` | Bearer Token 强鉴权 | `{"log_file": "..."}` | 触发真机日志审计与报告落盘 |
| `/api/projects/{id}/spider-audit/status` | `GET` | Bearer Token 强鉴权 | 无 | 获取已有 `spider_access_audit.json` 数据 |
| `/api/projects/{id}/spider-audit/report` | `GET` | Bearer Token 强鉴权 | 无 | 获取 31 号 Markdown 报告内容 |

