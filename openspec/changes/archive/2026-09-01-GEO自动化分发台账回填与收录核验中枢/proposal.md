# Proposal: GEO 自动化分发台账回填与收录核验中枢 (Distribution Bot & Verification Hub)

## Why (为什么做 / 商业与业务痛点)

1. **矩阵分发落地的最后 1 公里堵点**：
   - 目前 Step 4 生成了 5 大平台（知乎、今日头条、微信公众号、GitHub、掘金）的分发包，但后续发布状态、外链 URL 回填与核验依赖纯手工文本记录；
   - 容易出现运营人员漏发、错发或发布后被下架/404 但未被察觉的问题，导致大模型无法抓取 Citation。
2. **自动化收录探测与健康度闭环**：
   - 发布后需要自动化检测外链是否存活（HTTP 200）、是否可被 Clean Markdown 提取，并在管理端与只读门户呈现真实的 **分发完成率（0~100%）** 与真实外部链接。
3. **富文本一键格式化复制（剪贴板优化）**：
   - 微信公众号/知乎对纯 Markdown 粘贴支持不佳，系统需提供预编译带样式的富文本 HTML，实现一键无损粘贴，保留标题层级、对比表格与高亮花字。

---

## What Changes (改动范围)

1. **研发分发台账与收录核验引擎 (`tools/geo/dist_bot.py`)**：
   - `record_distributed_url(project_id, channel, url)`：记录或更新指定渠道的发布外链；
   - `verify_distribution_url(url)`：检测 URL 存活状态与内容连通性；
   - `get_distribution_ledger(project_id)`：获取 5 大渠道发布台账、收录状态与完成率；
   - `format_rich_text_copy(project_id, channel)`：生成带样式 HTML 富文本供一键复制。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo record <project_id> --channel <channel> --url <url>` 与 `geo verify-dist <project_id>`。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/distribution/ledger`
   - `POST /api/projects/{id}/distribution/record`
   - `POST /api/projects/{id}/distribution/verify`
   - 在 `tools/geo/share.py` 门户数据中注入 `distribution_ledger` 真实外链。
4. **Web 管理端与专属交付门户前端升级 (`web/index.html` & `web/share.html`)**：
   - Step 4（矩阵分发）增加「🚀 全渠道发布台账与自动化回填」交互模块，支持 URL 快速填报、存活状态打标与富文本复制；
   - 专属交付门户（`web/share.html`）Tab 4 自动展示每个平台的真实已发布外链与收录证明徽章。
5. **SOP 文档更新 (`docs/sop/04-distribute-sop.md` & `delivery-sop.md`)**。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/distribution/ledger`
- `POST /api/projects/{id}/distribution/record`
- `POST /api/projects/{id}/distribution/verify`
- CLI: `python3 -m tools.geo record <project_id> --channel <ch> --url <url>`
- CLI: `python3 -m tools.geo verify-dist <project_id>`
- 渠道覆盖：`toutiao`、`zhihu`、`juejin`、`github`、`wechat`

---

## Impact (影响分析)

- **完全向下兼容**：数据保存在各项目 `outputs/dist_ledger.json`，不影响已有流水线；
- **交付透明度升级**：客户在专属门户可直接点击跳转查看已落地的 5 大外网真实文章。
