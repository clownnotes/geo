## 1. 战略与认知底座升级 (`docs/strategy/` & `docs/`)

- [x] 1.1 升级 `docs/strategy/overview.md`，定版中国本土 5 大 AI 大模型生态分类与差异化渗透矩阵。
- [x] 1.2 升级 `docs/index.md` 首页 tagline 与大模型生态导航，收敛至本土主流大模型（豆包/DeepSeek/Kimi/元宝）。
- [x] 1.3 更新 `docs/public/llms.txt` 与 `docs/public/robots.txt`，置顶放行本土 AI 爬虫（Bytespider 第一位）。

## 2. 站点底座与体检引擎代码本土化 (`tools/geo/`)

- [x] 2.1 重构 `tools/geo/scaffold.py` 的 `build_robots_txt`，明确放行 Bytespider / Baiduspider / Sogouspider / Yisouspider。
- [x] 2.2 重构 `tools/geo/audit.py`，模拟 Bytespider / Baiduspider / Sogouspider 抓取并评估本土可见度。
- [x] 2.3 升级 `tools/geo/pitch.py`，标书与 10 页全屏 Pitch Deck 全面切换为国内 5 大主流模型。

## 3. SOP 交付标准与全流程闭环验证

- [x] 3.1 更新 `docs/sop/02-scaffold-sop.md` 与 `docs/sop/delivery-sop.md`，统一本土爬虫与大模型映射标准。
- [x] 3.2 运行全流程 CLI 工具（`audit`、`scaffold`、`guard`），验证国内规则产物落盘正常。
- [x] 3.3 严格执行规范：仅在开发端验证，提交并推送到远端 Git 仓库，在 `review-log.md` 记录对抗评审结论。

