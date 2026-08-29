# Design: 商用GEO交付程序与全流程SOP系统

## 1. Architecture (架构设计与对象关系)

### 1.1 核心实体与面向对象抽象

```
┌─────────────────────────────────────────────────────────────┐
│                   ClientProject (客户项目)                   │
│ - id: str (如 client_001_xuzhou)                           │
│ - name: str (客户品牌名)                                    │
│ - domain: str (官网域名)                                    │
│ - competitors: list[str] (竞品清单)                         │
└──────────────────────────────┬──────────────────────────────┘
                               │ 1:N 聚合
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   AuditSession   │  │   ScaffoldPack   │  │   RewriteTask    │
│ (体检诊断会话)    │  │ (技术底座交付包)  │  │ (内容重构任务)   │
│ - crawl_result   │  │ - llms_txt       │  │ - source_docs    │
│ - baseline_sov   │  │ - json_ld_schema │  │ - princeton_md   │
│ - report_md      │  │ - robots_patch   │  │ - qa_pairs       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
┌──────────────────┐                        ┌──────────────────┐
│  DistributePack  │                        │  MonitorReport   │
│ (全渠道分发包)    │                        │ (周期监测报告)   │
│ - toutiao_md     │                        │ - sov_score      │
│ - zhihu_md       │                        │ - rank_positions │
│ - github_readme  │                        │ - citation_links │
└──────────────────┘                        └──────────────────┘
```

### 1.2 系统处理数据流 (Workflow Pipeline)

```
[原始客户输入] ──► [1. geo audit] ────► 生成《诊断报告.md》+ 签单
      │
      ├──► [2. geo scaffold] ─► 交付 llms.txt + JSON-LD + robots.txt
      │
      ├──► [3. geo rewrite] ──► 批量转换 PDF/Word ──► 普林斯顿 9 因子增强语料
      │
      ├──► [4. geo distribute]► 导出头条/知乎/掘金/GitHub 专用发布版本
      │
      └──► [5. geo monitor] ──► 定时调用 LLM API ──► 生成《可见度周报/月报》
```

---

## 2. Interface & CLI Design (命令行与调用接口)

### 2.1 CLI 总入口命令规范

统一通过 `python3 -m tools.geo <subcommand> [options]` 或 `./geo <subcommand>` 触发：

```bash
# 1. 客户现状诊断与体检
python3 -m tools.geo audit --project <client_id> [--url <url>] [--keywords <kw_file>]

# 2. 生成站点底座改造脚手架
python3 -m tools.geo scaffold --project <client_id>

# 3. 普林斯顿 9 因子内容重构流水线
python3 -m tools.geo rewrite --project <client_id> [--input-dir <dir>]

# 4. 多平台信源矩阵分发包导出
python3 -m tools.geo distribute --project <client_id>

# 5. 自动化 AI 可见度监控与周报生成
python3 -m tools.geo monitor --project <client_id> [--models deepseek,doubao]
```

### 2.2 核心模块职责划分

| 模块路径 | 职责定位 | 核心依赖 |
| :--- | :--- | :--- |
| `tools/geo/cli.py` | 命令行参数解析、项目生命周期调度、标准输出格式化 | `argparse`, `rich` / `tabulate` |
| `tools/geo/audit.py` | 网页抓取体检（SSR检测、正文提取）、基准词搜索、体检报告渲染 | `crawl4ai` / `requests`, `jinja2` |
| `tools/geo/scaffold.py` | 基于客户画像自动生成 `llms.txt`, `JSON-LD`, `robots.txt` | 纯 Python 模板引擎 |
| `tools/geo/rewrite.py` | 存量文档解析（PDF/Word/PPT）、普林斯顿 9 因子 Prompt 链 | `markitdown`, LLM API Client |
| `tools/geo/distribute.py` | 矩阵平台文案自适应格式化与排版适配 | 文本处理与 Markdown 渲染 |
| `tools/geo/monitor.py` | 多模型并发联网检索、正则匹配提及/排名/引用、周报图表生成 | LLM API (DeepSeek/豆包), SQLite |

---

## 3. Data Structure & Project Directory Layout (项目文件规范)

### 3.1 项目数据结构目录设计

```
GEO/
├── tools/
│   └── geo/                  # 商业交付程序包
│       ├── __init__.py
│       ├── __main__.py       # CLI 入口
│       ├── audit.py          # 阶段 1: 诊断体检
│       ├── scaffold.py       # 阶段 2: 底座生成
│       ├── rewrite.py        # 阶段 3: 内容重构
│       ├── distribute.py     # 阶段 4: 渠道分发
│       ├── monitor.py        # 阶段 5: 监测报表
│       ├── project.py        # 客户工作区加载/校验/初始化
│       ├── llm.py            # OpenAI 兼容 LLM 客户端（DeepSeek/豆包 Ark）
│       └── miniyaml.py       # 零依赖 YAML 子集解析器
│       # 注：报表/代码模板以函数级内联实现（scaffold/audit 等模块内），不单独建 templates/ 目录
├── projects/                 # 客户项目隔离工作区
│   └── _template/            # 客户模板配置
│       ├── project.yaml      # 客户基本信息与关键词配置
│       ├── raw_materials/    # 客户原始资料 (PDF/Word)
│       └── outputs/          # 阶段交付成果产物
├── docs/
│   └── sop/                  # 交付 SOP 规范库
│       ├── 01-audit-sop.md       # 售前诊断与获客 SOP
│       ├── 02-scaffold-sop.md    # 底座改造与交接 SOP
│       ├── 03-rewrite-sop.md     # 普林斯顿重构 SOP
│       ├── 04-distribute-sop.md  # 矩阵借壳分发 SOP
│       └── 05-monitor-sop.md     # 监控追踪与续费 SOP
```

### 3.2 客户配置文件 `project.yaml` 规范

```yaml
client_id: "demo_corp"
client_name: "示例科技"
official_url: "https://example.com"
industry: "企业级智能管理软件"
core_values:
  - "高并发处理能力，延迟降低 40%"
  - "支持全私有化部署"

keywords:
  - "2026年企业级管理系统推荐"
  - "国内好用的智能协同软件"
  - "高并发企业管理系统对比"

competitors:
  - "竞品A"
  - "竞品B"

models:
  - "deepseek"
  - "doubao"
```

