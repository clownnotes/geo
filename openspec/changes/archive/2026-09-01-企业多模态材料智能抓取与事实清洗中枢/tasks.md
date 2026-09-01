## 1. 抓取与事实提纯核心引擎开发 (`tools/geo/ingest.py`)

- [x] 1.1 编写网页 Clean HTML 抓取与 Markdown 转换器（`clean_html_to_markdown` / `fetch_and_clean_url`）。
- [x] 1.2 编写多格式文档提取器（`extract_text_from_file`，支持 TXT / Markdown / 基础 PDF/Doc 文本）。
- [x] 1.3 编写事实密度提纯算法（`distill_knowledge_facts`），生成 5 维知识三元组清单（支持大模型与离线规则双模式）。
- [x] 1.4 实现 `ingest_project_materials(project_id, url, file_path)` 主流程，自动将清洗结果和事实清单落盘至 `projects/<id>/raw_materials/`。

## 2. CLI 命令与工具库集成 (`tools/geo/`)

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `ingest_project_materials`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo ingest <project_id>` 子命令（支持 `--url` 与 `--file` 参数）。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `POST /api/projects/{id}/ingest/url` 抓取并提纯官网接口。
- [x] 3.2 实现 `POST /api/projects/{id}/ingest/text` 补充文本素材接口。
- [x] 3.3 实现 `GET /api/projects/{id}/raw_materials` 素材列表与统计接口。

## 4. Web 工作台 Step 3 交互升级 (`web/index.html`)

- [x] 4.1 在 Step 3 普林斯顿内容重构面板上方新增「📥 原始素材智能抓取与事实清洗中枢」交互卡片。
- [x] 4.2 提供「官网一键抓取」与「手动粘贴补充素材」操作表单与加载动效。
- [x] 4.3 渲染已就绪素材文件列表徽标与事实摘要预览。

## 5. SOP 文档更新与端到端实测

- [x] 5.1 更新 `docs/sop/03-rewrite-sop.md`，规范化素材清洗与事实提纯流程。
- [x] 5.2 运行 CLI 与 Web 接口实测：抓取真实/模拟企业官网并提纯入库。
- [x] 5.3 运行 `pipeline` 验证 Step 3 普林斯顿重构是否成功消费抓取到的原始事实素材。
- [x] 5.4 在 `review-log.md` 记录评审与实测结论。
