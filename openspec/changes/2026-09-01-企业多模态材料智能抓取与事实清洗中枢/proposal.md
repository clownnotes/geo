# Proposal: 企业多模态材料智能抓取与事实清洗中枢

## Why (为什么做 / 业务痛点)

1. **真实商业交付中的素材断层痛点**：
   - 在向企业交付 GEO 服务的真实场景中，客户很少能提供结构化整洁的 Markdown 文档；
   - 客户通常只给一个**官网域名**（如 `https://example.com`）或发来一份 **PDF 产品画册 / Word 企业简介 / PPT 方案**；
   - 传统代运营需要文案人工花数小时去网页和文档中逐字复制、剔除导航栏与广告噪音；
2. **核心目标**：
   - 研发一站式**「企业素材智能抓取与事实提纯中枢 (`tools/geo/ingest.py`)」**；
   - 支持**官网 URL 一键递归抓取清洗（Clean Markdown）**与**多格式原始文档解析**；
   - 自动提纯为高事实密度的「企业核心知识事实清单（Entity-Attribute-Value Triples）」并持久化存入 `projects/<id>/raw_materials/`，为 Step 3 普林斯顿 9 因子流水线提供源源不断的高质量底层输入。

---

## What Changes (改动范围)

1. **新建素材抓取与事实提纯引擎 (`tools/geo/ingest.py`)**：
   - **官网 Clean 抓取器 (`ingest_website_url`)**：支持清洗 HTML 标签、移除导航栏/页脚/JS 噪音，提取正文内容；
   - **多格式文档解析器 (`ingest_document_file`)**：支持 PDF、TXT、Markdown、DOCX 原始文档文本提取；
   - **事实密度提纯器 (`distill_knowledge_facts`)**：调用大模型（带离线规则兜底）从长篇素材中浓缩提炼出 10 条高确定性的企业参数、资质、价格与承诺事实清单，写入 `raw_materials/raw_extracted_facts.md`。
2. **CLI 工具链扩展 (`tools/geo/cli.py`)**：
   - 增加 `geo ingest <project_id> [--url URL] [--file PATH]` 子命令。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `POST /api/projects/{id}/ingest/url`：抓取指定 URL 并提纯入库；
   - `POST /api/projects/{id}/ingest/text`：接收文本素材并提纯入库；
   - `GET /api/projects/{id}/raw_materials`：获取项目所有原始素材文件列表与字数统计。
4. **Web 交付工作台升级 (`web/index.html`)**：
   - 在 Step 3 面板上方新增 **「📥 原始素材智能抓取与清洗中枢」** 卡片；
   - 支持一键从官网抓取、直接粘贴素材文本，并实时展示已沉淀的素材文件列表与提纯事实预览。
5. **SOP 知识库更新 (`docs/sop/03-rewrite-sop.md`)**：
   - 将素材抓取与事实提纯标准纳入 SOP-03 规范。

---

## Capabilities (对外能力)

- `POST /api/projects/{id}/ingest/url` (Body: `{ "url": str }`)
- `POST /api/projects/{id}/ingest/text` (Body: `{ "filename": str, "content": str }`)
- `GET /api/projects/{id}/raw_materials`
- CLI: `python3 -m tools.geo ingest <project_id> --url https://example.com`

---

## Impact (影响分析)

- **完全向下兼容**：若项目 `raw_materials/` 为空，Step 3 原有生成逻辑保持兼容兜底；
- **生产人效倍增**：将企业基础信息整理时间从 2 小时压缩至 15 秒内；
- **重构语料质量大幅提升**：普林斯顿 9 因子语料库将拥有真正来自客户官网与画册的真实参数支撑。
