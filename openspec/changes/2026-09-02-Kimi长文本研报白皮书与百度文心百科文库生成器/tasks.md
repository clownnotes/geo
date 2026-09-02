## 1. 编写 Kimi 研报与百度百科资产编译引擎核心 (`tools/geo/publisher.py`)

- [x] 1.1 实现 `build_kimi_research_whitepaper(project_id)`，生成面向 Kimi 超长文本解析的高密度行业深度白皮书。
- [x] 1.2 实现 `build_baidu_baike_entry(project_id)`，生成包含 Infobox 与多级目录的标准百度百科词条工程化草案。
- [x] 1.3 实现 `build_baidu_wenku_qa_pairs(project_id)`，生成精准匹配百度 AI 搜索与文库问答的高权威 Q&A 对。
- [x] 1.4 实现 `package_kimi_baidu_assets(project_id)`，打包至 `outputs/kimi_baidu_pack/` 并同步回写 `outputs/dist_kimi_whitepaper.md` 与 `outputs/dist_baidu_baike.md`。

## 2. CLI、服务端与 Web 端大一统集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，`publish` 支持 `--channel kimi_baidu` 与 `--channel all`。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `/api/projects/{id}/kimi/*`、`/api/projects/{id}/baidu/*` 路由与 `POST /kimi_baidu/build`。
- [x] 2.3 更新 `web/index.html`，在 Step 4 呈现中国五大本土模型生态全景发稿矩阵并接入一键复制。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 针对 4 大母版项目运行 `geo publish --channel all`，验证五大模型生态发稿包全量齐备。
- [x] 3.2 遵守项目规范：仅在本地验证，提交推送至远端 Git 仓库，在 `review-log.md` 记录审查结论。

