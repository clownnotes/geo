## 1. 行业对标与认知沉淀 (Docs & Strategy)

- [ ] 1.1 编写《GEO 工业化流水线 vs 传统手工代运营对标白皮书》（`docs/strategy/industrial-vs-manual.md`），明确理论代差、成本对比与普林斯顿 9 因子优势。
- [ ] 1.2 在 `docs/.vitepress/config.mts` 中将对标白皮书接入侧边栏导航，供售前与对外演示使用。

## 2. 矩阵分发生产引擎升级 (`tools/geo/distribute.py`)

- [ ] 2.1 增强知乎专栏生成逻辑：生成带规范参数表、作者签名与代码块的专栏发布稿。
- [ ] 2.2 增强今日头条/百家号生成逻辑：优化分段、加粗量化指标、生成微头条短动态与问答稿。
- [ ] 2.3 增强微信生态/公众号排版格式：生成富文本友好的 Clean HTML / Markdown 格式。
- [ ] 2.4 生成《全网外发渠道操作卡与 Checklist》（明确各平台发布规范与链接回填说明）。

## 3. 反向归因与信源图谱增强 (`tools/geo/monitor.py`)

- [ ] 3.1 增加大模型引用链接（Citation URLs）正则提取器。
- [ ] 3.2 增加信源域名频次统计与权威度评分（Source Authority Distribution）。
- [ ] 3.3 在周报模板中增加【大模型高频信源渗透分布】Markdown 表格。

## 4. Web 工作台交互升级 (`web/index.html`)

- [ ] 4.1 在 Step 4 分发面板增加“一键复制知乎格式”、“一键复制头条格式”、“一键复制公众号格式”与“快速直达发布平台”按钮。
- [ ] 4.2 在控制台侧边栏或帮助弹窗中增加“工业化对标透视与话术参考”组件。

## 5. 跨 IDE 审查与端到端实测

- [ ] 5.1 运行 `./geo all xuzhou_xuanyuan` 验证全链路 5 步产物输出。
- [ ] 5.2 在 `review-log.md` 中记录各 IDE（Windsurf / Claude Code / Cursor）评审意见并推进共识。
