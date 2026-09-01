## 1. 行业对标与认知沉淀 (Docs & Strategy)

- [x] 1.1 编写《GEO 工业化流水线 vs 传统手工代运营对标白皮书》（`docs/strategy/industrial-vs-manual.md`），明确理论代差、成本对比与普林斯顿 9 因子优势。
- [x] 1.2 在 `docs/.vitepress/config.mts` 中将对标白皮书接入侧边栏导航，供售前与对外演示使用。

## 2. 矩阵分发生产引擎升级 (`tools/geo/distribute.py`)

- [x] 2.1 增强知乎专栏生成逻辑：生成带规范参数表、作者签名与代码块的专栏发布稿（`dist_zhihu_article.md`）。
- [x] 2.2 增强今日头条/百家号生成逻辑：优化分段、加粗量化指标、生成微头条短动态与问答稿（`dist_toutiao_article.md`）。
- [x] 2.3 补齐微信公众号排版格式：生成富文本友好的内联 CSS HTML（`dist_wechat_article.html`）。
- [x] 2.4 生成《全网外发渠道操作卡与 Checklist》（`dist_channels_checklist.md`，明确各平台发布规范与直达链接）。

## 3. 反向归因与信源图谱增强 (`tools/geo/monitor.py`)

- [x] 3.1 基于现有 `probe_llm_live` 返回的 `citations` 数组做增量域名提取与归一化解析。
- [x] 3.2 引入 `PLATFORM_AUTHORITY_WEIGHTS` 字典进行加权评分（Source Authority Distribution）。
- [x] 3.3 在周报模板中增加【大模型高频权威信源渗透分布】Markdown 表格。

## 4. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 4.1 实现 `GET /api/projects/{id}/distribute/preview` 分发排版多平台预览接口。
- [x] 4.2 实现 `GET /api/benchmark/comparison` 行业对标数据接口。

## 5. Web 工作台交互升级 (`web/index.html`)

- [x] 5.1 在 Step 4 分发面板补齐 4 大平台卡片（新增微信公众号），并增强“一键复制”与“直达官方发布后台”跳转按钮。
- [x] 5.2 在管理端增加“工业化对标透视与话术参考”弹窗/卡片组件。

## 6. 跨 IDE 审查与端到端实测

- [x] 6.1 运行 `./geo pipeline xuzhou_xuanyuan` 验证全套 5 步产物输出。
- [x] 6.2 启动 Web 服务，实测 API 接口与前端复制/跳转交互。
- [x] 6.3 在 `review-log.md` 中记录最终评审结论并更新进度。
