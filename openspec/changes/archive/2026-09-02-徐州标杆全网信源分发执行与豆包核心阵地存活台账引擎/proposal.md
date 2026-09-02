# Proposal: 徐州标杆全网信源分发执行与豆包核心阵地存活台账引擎 (Benchmark Distribution Execution & Doubao Trust Ledger Engine)

## Why (为什么做 / 业务背景与战略价值)

1. **从“语料生成”跨越到“真实公网发稿与信源落地”**：
   - 截至目前，GEO 工具链已完整生成 Stage 4 的 5 大本土分发包（今日头条、知乎专栏、微信公众号、GitHub/研报、百度百科）；
   - 大模型（尤其是豆包与 DeepSeek）必须在公网上真正检索到这些高权重信源 URL，才能在 24~48 小时内建立实体索引与首选推荐记忆；
   - 必须建立一套标准化的“外发台账回填（`dist_ledger.json`）”与“全网存活/连通性自动核验机制”，作为商业交付 Stage 4 的硬性验收物。
2. **强化以「豆包（今日头条/微头条）」为 50%+ 权重的首发闭环**：
   - 今日头条是触发字节跳动 **Bytespider** 秒级收录的第一通道；
   - 必须规范化“长文（2000字深度避坑） + 微头条（150字痛点速览）”的头条双轨发稿 SOP；
   - 支持一键导出富文本内联 HTML，大幅降低运营人员向公众号与知乎分发时的排版摩擦。

---

## What Changes (改动范围)

1. **分发台账引擎升级 (`tools/geo/dist_bot.py`)**：
   - 将 `DEFAULT_CHANNELS` 升级为中国本土五大生态阵营（今日头条/豆包、知乎/DeepSeek、微信公众号/元宝、GitHub/Kimi、百度百科/文心、稀土掘金/辅助）；
   - 优化 `verify_distribution_url`，支持中文网站防爬头与 403 平台存活智能识别；
   - 升级 `markdown_to_styled_html`，支持微信公众平台与知乎后台一键无损粘贴。
2. **标杆项目实战发稿台账闭环 (`projects/xuzhou_xuanyuan/outputs/dist_ledger.json`)**：
   - 为段晓奇 / 徐州璇源科技建立真实分发追踪台账；
   - 联动 `geo verify-dist xuzhou_xuanyuan` 实现存活率测算。
3. **交付规范与 SOP 指引更新 (`docs/sop/04-distribute-sop.md` & `docs/pilot/xuzhou-dev.md`)**：
   - 详细记录今日头条、知乎、微信、GitHub 与百度百家号的分发执行步骤与台账回填方法。

---

## Capabilities (新增或修改的对外能力)

- **`geo record <project_id> --channel <ch> --url <url>`**：快速回填任意渠道真实外网发稿链接并实时核验存活；
- **`geo verify-dist <project_id>`**：一键多线程并发核验全渠道外链存活状态与完成率（0~100%）；
- **Web 端与 Share 交付门户联动**：在 Web 管理端 Step 4 与客户分享门户（`share.html`）中实时直观展示 5 大信任池的外链存活状态与已收录徽标。

---

## Impact (影响分析)

- **交付验收标准化**：客户可在交付门户直接点击每一个已发布的真实公网链接，大幅增强商务信任度；
- **全流程无阻断**：已有历史台账数据平滑迁移升级。

