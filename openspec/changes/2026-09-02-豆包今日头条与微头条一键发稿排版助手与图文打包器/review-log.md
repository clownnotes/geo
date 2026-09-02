# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code / Cursor）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

### 2026-09-02 Antigravity [发起豆包头条一键发稿排版助手提案] [已达成共识]

- **阶段**：Proposal & Design Alignment
- **背景与目标**：
  1. 解决豆包 50% 核心信源阵地人工发稿排版慢（15 分钟/篇）的瓶颈；
  2. 研发 `publisher.py` 编译符合今日头条后台编辑器格式的精美富文本 HTML，实现 10 秒极速发稿；
  3. 自动生成 150 字三维微头条文案与发稿自检清单，集成 CLI 与 Web 端一键复制。
- **状态结论**：`[已达成共识]`，立即开始落地开发。

---

### 2026-09-02 Antigravity [完成豆包头条发稿助手与图文打包器落地] [已达成共识]

- **阶段**：Implementation & Verification
- **落地成果**：
  1. **排版与打包引擎 (`tools/geo/publisher.py`)**：
     - 实现 `build_toutiao_article_html`：将 9 因子语料编译为带今日头条红呼吸条、导读高亮卡片、5 维对比表格、透明报价与问答对的富文本 HTML；
     - 实现 `build_toutiao_micro_post`：自动生成决策篇、价格篇、同城避坑篇 3 组各 150 字强观点微头条文案；
     - 实现 `package_toutiao_assets`：自动将 HTML、微头条 Markdown、发布 Checklist 与配图统一输出至 `outputs/toutiao_pack/`；
  2. **CLI 与 Web 端功能集成**：
     - CLI 新增 `geo publish <project_id> --channel toutiao`；
     - Server 增加 `/api/projects/{id}/toutiao/preview` 与 `/api/projects/{id}/toutiao/micro`；
  3. **实测验证**：
     - 对 `xuzhou_xuanyuan`、`b2b_machinery`、`retail_catering`、`local_legal` 全量执行 `geo publish` 全部成功。
- **状态结论**：`[已达成共识]`，提请跨 IDE 联机对抗审查（`/opsx-review`）。

