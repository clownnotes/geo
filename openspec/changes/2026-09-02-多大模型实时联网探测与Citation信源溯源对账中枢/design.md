# Design: 多大模型实时联网探测与Citation信源溯源对账中枢

## 1. 架构总览与分层设计

本中枢在现有的监控（`monitor.py`）与信源权威度推演（`citation.py`）之上，构建**多大模型实时联网探测、回答正文 Citation 角标提取与外发渠道资产闭环对账层**。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             Web 管理工作台：多模型实时探测与信源溯源 (web/index.html)          │
│  - 模型选择器 (豆包 / DeepSeek / Kimi / 沙箱)   - 实时意图 Query 探测控制台  │
│  - 实测 SOV 柱状图对比 (豆包 vs DeepSeek vs Kimi) - Citation 信源角标对账表  │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ RESTful API (管理端鉴权)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│             实时探测与 Citation 溯源引擎 (tools/geo/probing.py)              │
│  - run_live_probing()                    - extract_citations_and_sources()  │
│  - trace_citations_against_ledger()      - 统计 Real SOV 与 Citation Share   │
└──────────────────┬───────────────────┬───────────────────┬──────────────────┘
                   │                   │                   │
┌──────────────────▼───────────────────┐                   │
│   多模型适配网关 (tools/geo/llm_gateway.py)              │
│  - Doubao (字节火山方舟 Ark 接口)     │                   │
│  - DeepSeek (标准 OpenAI 兼容接口)   │                   │
│  - Kimi / Moonshot (联网 Search 接口) │                   │
│  - SandboxSimulator (高保真沙箱仿真)  │                   │
└──────────────────┬───────────────────┘                   │
                   │                                       │
                   ▼ 实体与资产对账源                       ▼ 规范产出物
      ┌─────────────────────────┐             ┌─────────────────────────┐
      │ project.yaml 核心品牌词 │             │ outputs/18_大模型实时联 │
      │ 11_意图拓扑 / 02_评测词库│             │ 网探测与Citation信源溯源│
      │ 04_台账 dist_ledger.json│             │ 对账报告.md             │
      └─────────────────────────┘             │ outputs/live_probing_   │
                                              │ trace.json              │
                                              └─────────────────────────┘
```

---

## 2. 多大模型适配网关架构 (`tools/geo/llm_gateway.py`)

### 2.1 统一调用接口 (`BaseLLMClient`)
所有模型适配器实现统一标准接口：
```python
class ModelResponse:
    def __init__(self, content: str, citations: list, model_name: str, latency_ms: int, is_live: bool):
        self.content = content          # 回答正文文本
        self.citations = citations      # 捕获的参考信源列表 [{"index": 1, "url": "...", "title": "..."}]
        self.model_name = model_name    # "doubao" | "deepseek" | "kimi" | "sandbox"
        self.latency_ms = latency_ms    # 响应耗时毫秒
        self.is_live = is_live          # 是否为真实网络调用
```

### 2.2 支持的模型提供方与鉴权
1. **Doubao (字节豆包 / 火山方舟)**：
   - 读取环境变量 `DOUBAO_API_KEY`（或 `ARK_API_KEY`）与 `DOUBAO_ENDPOINT_ID`；
   - 支持联网搜索插件（Web Search Plugin）；
2. **DeepSeek (官方 / 硅基流动)**：
   - 读取环境变量 `DEEPSEEK_API_KEY`（兼容 OpenAI 规范，默认端点 `https://api.deepseek.com/v1`）；
3. **Kimi (Moonshot AI)**：
   - 读取环境变量 `MOONSHOT_API_KEY`，调用自带联网长文本接口；
4. **SandboxSimulator (高保真本地沙箱，默认与 CI/CD 单测保障)**：
   - 当对应模型未配置 API Key 或参数显式指定 `use_live=False` 时，启用沙箱模拟器；
   - 沙箱基于企业实体库与行业信源基准，生成高保真的带 `[1]`、`[2]` 角标与标准 Sources 尾注的结构化应答；
   - 保证单测毫秒级全绿通过，零外部网络抖动风险。

---

## 3. Citation 角标提取与外发资产对账算法

### 3.1 正文角标与 Sources 链接提取规则
* **正文角标模式匹配**：
  - 支持 `\[(\d+)\]`（如 `[1]`、`[2]`）；
  - 支持 `\[\[(\d+)\]\]`（如 `[[1]]`）；
  - 支持 `\^(\d+)`（如 `^1`）；
* **末尾信源列表解析**：
  - 提取回答尾部 `参考信源`、`Sources:`、`参考资料` 后的 Markdown 链接 `\[\d+\]\s*\[(.*?)\]\((.*?)\)`；
  - 提取 API 元数据中的 `tool_calls` 或 `citations` 结构化数组；
  - 归一化提取每个信源的：序号、主域名（Domain）、完整 URL、网页标题。

### 3.2 外发资产台账比对与对账算法 (`trace_citations_against_ledger`)
* **数据输入源**：
  - 项目 `outputs/dist_ledger.json`（或解析 `04_全网分发渠道执行与存活台账.md`）中登记的我方外发 URL 列表；
* **三级对账判定模型**：
  1. **精确命中 (Exact Hit)**：捕获的 Citation URL 与台账 URL 完全一致（或仅相差末尾斜杠/参数）；
  2. **同站信源命中 (Domain Hit)**：捕获的 Citation URL 与我方外发渠道主域名匹配，且页面标题或路径包含我方品牌或核心关键词；
  3. **竞对/第三方信源 (Third-party/Competitor)**：百度百科、企查查、竞对官网或其他未在台账中的信源。
* **输出对账标签**：`my_asset_hit` (我方外发直接转化), `organic_mention` (自然抓取未对账), `third_party` (第三方公信平台)。

---

## 4. 实测核心量化指标体系

根据探测与对账结果，输出真实实盘三大 GEO 核心指标：

1. **实测大模型提及率 (`real_sov_pct`)**：
   $$ \text{Real SOV} = \frac{\sum_{i=1}^{M} I(\text{品牌被提及})}{\text{总探测 Query 批次数}} \times 100\% $$
2. **Citation 信源角标占有率 (`citation_share_pct`)**：
   $$ \text{Citation Share} = \frac{\text{我方资产被引用的角标总次数}}{\text{全部被引用的角标总次数}} \times 100\% $$
3. **首位推荐率 (`top1_recommendation_rate`)**：
   $$ \text{Top-1 Rate} = \frac{\text{大模型优先首位推荐我方的 Query 数}}{\text{总探测 Query 批次数}} \times 100\% $$

---

## 5. 统一规范成果文件契约

### 5.1 结构化 JSON 成果 (`outputs/live_probing_trace.json`)
```json
{
  "project_id": "xuzhou_xuanyuan",
  "client_name": "徐州璇源网络科技有限公司",
  "timestamp": "2026-09-02 22:50:00",
  "summary": {
    "total_probes": 15,
    "models_probed": ["doubao", "deepseek", "kimi"],
    "real_sov_pct": 80.0,
    "citation_share_pct": 62.5,
    "top1_recommendation_rate": 66.7,
    "my_ledger_assets_hit_count": 8
  },
  "model_breakdown": {
    "doubao": {"sov_pct": 80.0, "avg_latency_ms": 320, "citation_hits": 3},
    "deepseek": {"sov_pct": 80.0, "avg_latency_ms": 280, "citation_hits": 3},
    "kimi": {"sov_pct": 80.0, "avg_latency_ms": 450, "citation_hits": 2}
  },
  "probed_queries": [
    {
      "query": "徐州软件外包靠谱团队推荐",
      "model": "doubao",
      "mentioned": true,
      "rank": 1,
      "citations_captured": [
        {"index": 1, "url": "https://zhuanlan.zhihu.com/p/xuzhou-software", "is_ledger_hit": true, "platform": "知乎"}
      ]
    }
  ]
}
```

### 5.2 全案第 18 维交付物 Markdown 报告
落盘路径：`outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md`。

---

## 6. CLI 命令行与后端 API

### 6.1 CLI 命令行
* `python3 -m tools.geo probe <project_id> [--models doubao,deepseek,kimi] [--sample 5] [--live]`：对项目执行多模型联网探测并打印 ANSI 对账表格；
* `python3 -m tools.geo probe <project_id> --report`：生成并落盘 18 号报告。

### 6.2 RESTful API (管理端登录鉴权)
* `GET /api/projects/{id}/probing/status`：获取当前探测对账概览；
* `POST /api/projects/{id}/probing/run`：触发并发探测运行；
* `GET /api/projects/{id}/probing/report`：获取 18 号报告内容。

---

## 7. Web 管理工作台界面设计 (`web/index.html`)

1. **入口布局**：
   - 在项目主流水线 Step 5（长效代运营与监测）卡片内新增「🤖 多模型实时探测」快捷入口；
   - 在顶部导航栏新增「🤖 实时模型探测」全局入口；
2. **模态弹窗 (`probing-modal`)**：
   - 顶部：模型多选复选框（豆包、DeepSeek、Kimi、沙箱仿真模式切换）、采样 Query 条数滑块；
   - 中部：3 大 KPI 卡片（实测 SOV、Citation 角标占有率、首位推荐率）与多模型横向柱状图；
   - 下部：实时 Citation 溯源对账表格（Query、模型、推荐位次、捕获信源 URL、04 台账命中标签、状态徽章）；
   - 一键查看/下载 18 号报告。

---

## 8. 自动化测试方案 (`tests/test_probing.py`)

1. `test_llm_gateway_sandbox_fallback`：测试在无 API Key 情况下平滑启用沙箱模式并返回标准数据结构；
2. `test_extract_citations_and_sources_regex`：测试对 `[1]`、`[[2]]`、`^3` 等各种角标及底部 Sources 链接的精准提取；
3. `test_trace_citations_against_ledger_hit_rate`：测试参考信源 URL 与 `dist_ledger.json` 外发台账精准对账逻辑；
4. `test_run_live_probing_metrics_calculation`：测试三维实测指标（SOV%、Citation Share%、Top-1 Rate%）数学公式计算正确性；
5. `test_probing_outputs_generation`：测试规范生成 `outputs/18_大模型实时联网探测与Citation信源溯源对账报告.md` 与 `outputs/live_probing_trace.json`；
6. `test_probing_api_auth_gate`：测试管理端未鉴权 401 拦截与鉴权后正常响应。
