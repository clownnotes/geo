# Proposal: 全渠道分发链接智能解析回填与全网死链探活审计中枢 (Multi-Channel Link Auto-Backfill & Live Health Inspector Engine)

## Why (为什么做 / 业务背景与痛点)

1. **真实发稿链接入账繁琐，缺乏自动化解析**：
   - 运营人员在完成今日头条、知乎专栏、微信公众号、GitHub、百度百科等多渠道发布后，产生大量真实 URL；
   - 手动编辑 Markdown 表格容易产生格式错乱、渠道混淆与漏填问题，急需智能正则解析与渠道自动归类；
2. **缺乏全网链接存活与死链（404/屏蔽）自动化探活巡检**：
   - 各平台存在内容审核下架、违规屏蔽或链接失效风险，导致大模型抓取断链；
   - 缺少一键并发 HTTP 状态探活与存活率动态重算中枢，无法在商业交付结案前对资产进行健康度封版。

---

## What Changes (改动范围)

1. **全渠道链接智能识别与台账回填引擎 (`tools/geo/distributor.py` / `tools/geo/health_checker.py`)**：
   - `parse_mixed_links(raw_text: str) -> list[dict]`：从多行或混合文本中提取 URL，根据域名（`toutiao.com`、`zhihu.com`、`weixin.qq.com`、`github.com`、`baidu.com` 等）自动识别渠道、推断文章标题与发布时间；
   - `backfill_publication_ledger(project_id: str, links: list[dict]) -> dict`：无损增量回填至 `04_全网分发渠道执行与存活台账.md`；
   - `audit_channel_links_health(project_id: str, timeout: float = 3.0) -> dict`：并发探测台账中全部外链的 HTTP 响应码（200 / 404 / 302 等），标记存活状态并更新整体存活率；
2. **CLI 命令行增强 (`tools/geo/cli.py`)**：
   - `geo ledger add <pid> --links "<url1> <url2>..."`
   - `geo ledger audit <pid>`
3. **Server 路由与 Web 端 UI 深度集成**：
   - 新增 `POST /api/projects/{id}/ledger/batch-add`
   - 新增 `POST /api/projects/{id}/ledger/audit`
   - 新增 `GET /api/projects/{id}/ledger/summary`
   - Web 管理端 Step 4「全渠道分发台账看板」升级为「多链接智能一键粘贴解析入账」与「一键全网死链探活」。

---

## Capabilities (对外能力)

- **智能多格式链接解析**：粘贴任意包含 URL 的文本，自动识别渠道与元数据；
- **全网并发探活与死链拦截**：毫秒级探测全渠道真实存活率，提供异常链接警示；
- **高确定性资产移交保障**：确保交付客户的商业结案证书中的台账 100% 真实有效。

---

## Impact (影响分析)

- 极大提升运营团队发稿后回填台账效率（从几分钟缩短至 5 秒）；
- 闭环交付结案证书的真实外链存活审计。

