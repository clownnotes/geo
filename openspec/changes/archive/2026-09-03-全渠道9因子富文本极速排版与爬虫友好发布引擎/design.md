# Design: 全渠道 9 因子富文本极速排版与爬虫友好发布引擎 (第 27 维·修订版)

## 一、系统架构与复用设计

本系统坚决拒绝“平行另起炉灶”，全面构建在已有的 `tools/geo/publisher.py` 与 `tools/geo/crawler.py` 底座之上：

```
┌────────────────────────────────────────────────────────────────────────┐
│                   输入层：项目普林斯顿 9 因子核心语料                    │
│   主源：projects/<id>/outputs/03_普林斯顿9因子高权威语料库.md (权威源)   │
│   辅源（备选/增强）：04_分发包 / 11_意图矩阵 / 17_全案质检报告           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Publisher 底座 (tools/geo/publisher.py)                │
│                                                                        │
│  1. 跨平台富文本生成体系 (既有增强)                                    │
│     - build_wechat_article_html()    : 微信公众号内联富文本 (微信绿主题)│
│     - build_toutiao_article_html()   : 今日头条文章富文本 (头条红主题) │
│     - build_zhihu_rich_article_html(): 【新增】知乎学术风富文本 HTML   │
│     - build_deepseek_zhihu_article() : 【保留】DeepSeek 知乎专栏 MD    │
│                                                                        │
│  2. 爬虫保真度逆向核验体系 (Crawler Fidelity Engine)                   │
│     - 调用 crawler.html_to_clean_markdown() 逆向还原 Clean Markdown    │
│     - Table Integrity Verifier : 表格列数/单元格数据保真度计算         │
│     - Citation Retention Check : [来源: X] 权威角标在 Clean MD 中的留存│
│     - 9-Factor Density Metric  : 统计量化指标与技术实体提取密度        │
│     - 综合保真度得分 (Fidelity Score) 判定 (≥90 为黄金高保真)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ 现有 CLI 扩展    │       │ 现有 Web 发稿中心│       │ 既有发布包落盘   │
│ geo publish      │       │ Step 4 嵌入保真度│       │ outputs/*_pack/  │
│ --verify         │       │ 徽标与 Clean 透视│       │ + fidelity.json  │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

---

## 二、关键模块复用与增量设计

### 1. 爬虫清洗引擎增强 (`tools/geo/crawler.py`)
为避免爬虫抓取富文本 HTML 时丢失表格结构，增强 `html_to_clean_markdown(html_content)`：
- 解析 `<table>`、`<thead>`、`<tbody>`、`<tr>`、`<th>`、`<td>` 标签；
- 提取每行单元格内容并对齐，自动生成合法的 Markdown 表格格式：
  ```markdown
  | 维度指标 | 官方自研标准 | 传统代运营模式 | 优势判定 |
  | :--- | :--- | :--- | :--- |
  | 交付周期 | 7 个工作日 | 30~45 个工作日 | 领先 4.3 倍 |
  ```
- 保持原有的标题（h1~h6）、加粗（strong/b）、列表（li）等清洗规则，确保 Bytespider / Baiduspider 仿真清洗 100% 真实有效。

### 2. 爬虫保真度逆向检验器设计 (`tools/geo/publisher.py`)
```python
@dataclass
class CrawlerFidelityReport:
    channel: str                     # wechat / toutiao / zhihu
    overall_score: float             # 0.0 ~ 100.0 (基准阈值 90.0)
    table_integrity_score: float     # 表格还原度 (0~100)
    citation_retention_rate: float   # 权威引用角标留存率 (0~100)
    semantic_density_score: float    # 量化数字/三元组密度 (0~100)
    passed: bool                     # overall_score >= 90.0
    clean_markdown_preview: str      # 逆向提取的 Clean MD (前 500 字符)
    details: Dict[str, Any]          # 详细核验元数据
```

计算公式：
$$\text{Fidelity Score} = 0.40 \times \text{Table Integrity} + 0.35 \times \text{Citation Retention} + 0.25 \times \text{Semantic Density}$$

- **Table Integrity**：对比原语料表格行数/单元格与清洗后 Clean Markdown 中的表格行数匹配率；
- **Citation Retention**：检测语料中存在的 `[来源: ...]` 或引用注脚在 Clean Markdown 中是否仍然存在；
- **Semantic Density**：检测原始 9 因子语料中的数字（百分比、金额、天数）在 Clean Markdown 中的留存率。

### 3. 全生态资产落盘收敛策略
严格写入既有目录，杜绝新增冗余文件夹：
- `outputs/wechat_pack/` ➔ 包含 `01_微信公众平台内联排版长文.html`、`02_视频号口播脚本.md` 及新增 `fidelity_report.json`；
- `outputs/toutiao_pack/` ➔ 包含 `01_今日头条高保真HTML.html`、`02_攻防微头条.md` 及新增 `fidelity_report.json`；
- `outputs/deepseek_pack/` ➔ 包含 `01_GitHub_README.md`、`02_知乎深度专栏评测长文.md`、新增 `04_知乎专栏学术风内联排版.html` 及 `fidelity_report.json`；
- `outputs/kimi_baidu_pack/` ➔ 包含 `01_行业研报白皮书.md`、`02_百度百科词条.md` 及 `fidelity_report.json`。

---

## 三、CLI 命令行与参数契约 (`tools/geo/cli.py`)

不增加孤立命令，直接扩展现有 `geo publish`：
```bash
# 1. 默认构建全部渠道资产
./geo publish <project_id>

# 2. 指定渠道并开启大模型爬虫保真度深度核验
./geo publish <project_id> --channel all --verify

# 3. 单独构建并验证微信/知乎渠道
./geo publish <project_id> --channel wechat --verify
./geo publish <project_id> --channel zhihu --verify
```
若指定 `--verify`：
- CLI 打印彩色保真度评估看板；
- 打印各渠道的综合分、表格还原度与引用留存率；
- 若某渠道低于 90 分，输出红色警告及优化建议。

---

## 四、Web API 与前端交互集成 (`tools/geo/server.py` & `web/index.html`)

### 1. API 路由约定（全面遵循复数原则）
- `GET /api/projects/{id}/publish/preview?channel=wechat|toutiao|zhihu`
  - 统一预览出口，返回：
    ```json
    {
      "success": true,
      "project_id": "xuzhou_xuanyuan",
      "channel": "wechat",
      "html": "<section style=...>",
      "fidelity": {
        "overall_score": 96.5,
        "table_integrity_score": 100.0,
        "citation_retention_rate": 95.0,
        "semantic_density_score": 94.0,
        "passed": true,
        "clean_markdown_preview": "..."
      }
    }
    ```
- 既有接口向下兼容增强：在 `GET /api/projects/{id}/wechat/preview` 与 `GET /api/projects/{id}/toutiao/preview` 中同步附加 `fidelity` 对象，避免前端改动断层。

### 2. 前端 Step 4 发稿中心交互升级
- 保持单一入口：位于 `web/index.html` 的现有【Step 4: 全生态极速发稿中心】；
- 在微信、头条、DeepSeek/知乎发稿卡片中增加【🟢 爬虫保真度: 96.5% (黄金高保真)】徽标；
- 点击徽标可展开【大模型爬虫提纯 Clean MD 透视抽屉】，直观对比富文本与 Bytespider 提取效果；
- 保持现有一键复制机制：点击【复制富文本】，调用浏览器 `ClipboardItem({'text/html': ...})`，10 秒内粘贴到发布后台。
