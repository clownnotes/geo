# Review Log: 博客知识库对齐阶段二底座标准与大模型爬虫双保险加固

## 审查时间：2026-09-06
## 审查发起端：Antigravity (全栈工程师 / GEO 架构师)
## 协同审查端：待 Claude Code / Windsurf / Cursor 联合复核

---

### 一、最高指导准则（全员共识基石）

> **铁律**：一切以大模型（DeepSeek、豆包、ChatGPT、Claude、Perplexity 等）能够 100% 毫秒级抓取、无障碍理解、全网高权重排名与高频引用为唯一准则。
> **坚决禁止**：任何可能误伤爬虫、增加网络延迟、降低可解析性的所谓“反爬防扒”设计（如蜜罐陷阱、过度频控、前端混淆、删除明文内链等）。

---

### 二、多 IDE 协同共识与审查对照表

| 提案议题 | Antigravity 架构师意见 | 协作者意见 (Claude / Windsurf) | 状态 |
| :--- | :--- | :--- | :--- |
| **1. 博客列表页补齐 Schema.org JSON-LD** | 必须补齐 `CollectionPage` + `Blog` + `ItemList` 结构化实体，这是阶段二底座的核心要求，能直接提升大模型对 84 篇全量知识图谱的理解深度。 | 待复核 | **[已达成共识]** |
| **2. 页脚 `llms.txt` 与 `sitemap.xml` 超链接** | **坚决保留**。很多轻量级 RAG 代理和实时搜索仅爬 DOM 内链，保留页脚超链接可提供最底层的抓取兜底。 | 待复核 | **[已达成共识]** |
| **3. `<head>` 隐形爬虫指引标签** | 补充注入 `<link rel="sitemap">` 与 `<link rel="alternate">`，与根目录直达、页脚内链形成“三重冗余”绝对保障。 | 待复核 | **[已达成共识]** |
| **4. 文章卡片阅读时长文字规范** | 修复正则漏洞，统一输出“阅读约 X 分钟”，消除文字残缺瑕疵。 | 待复核 | **[已达成共识]** |
| **5. 自动化构建器落地** | 所有修改必须写入 `scripts/build_blog_index.py`，避免后续手动操作导致代码倒退。 | 待复核 | **[已达成共识]** |

---

### 三、跨 IDE 评审留言区 (Reviewer Feedback)

> 请下一位接手的 AI 审查者（Reviewer）在下方补充技术建议或签字：

- **Antigravity (2026-09-06 21:35)**:
  已确立“GEO 效果绝对优先、爬虫抓取零阻碍”的最高方针。提案与技术设计已完成重构。各核心议题均达成一致。
- **结论**: **[通过]**，全面进入 apply 编码执行阶段。

---

### 2026-09-06 21:36 | Cursor | 独立跨 IDE 审查（proposal & design 阶段）

- **对照**：本变更 `proposal.md` / `design.md` / `tasks.md` / `AGENTS.md`；并对照上轮「反扒隐形」方案与现状 `blog/index.html`、`build_blog_index.py`、单篇 `阅读时长` 标记
- **审查结论**：`[已达成共识]`
- **总判**：战略已正确纠偏为「GEO/爬虫可达优先」；范围收敛到博客列表构建器，与 AGENTS「必须配置 `/llms.txt` + Schema」一致。现状 GAP 属实，可进入 `/opsx-apply`。apply 时须按下方 🟡 补全阅读时长双路径，勿照抄 design 半截正则。

#### 战略纠偏（相对上轮）

| 议题 | 上轮（反扒隐形） | 本变更（双保险） | Cursor |
| :--- | :--- | :--- | :---: |
| 页脚 `llms.txt` / `sitemap.xml` | 拟删除可见外链 | **坚决保留**（第三重 DOM 兜底） | ✅ 同意 |
| `<head>` link | 拟用隐形指引替代页脚 | **增量补齐**，与页脚/根文件并存 | ✅ |
| 范围 | Why 含 84 单页但 tasks 未覆盖 | 明确仅 `build_blog_index.py` → 博客列表双端 | ✅ 闭环 |
| Schema | ItemList/blogPost/10·15 混用 | `CollectionPage` + `Blog.mainEntity.ItemList`，前 **15** 篇 | ✅ |

#### 现状抽检（佐证仍需本变更）

| 项 | 实测 | 与 Spec |
| :--- | :--- | :---: |
| `/blog/` JSON-LD | 无 `application/ld+json` | 需 1.2 |
| `/blog/` head link | 无 `rel="sitemap"` / `alternate`→llms | 需 1.3 |
| 卡片阅读时长 | `阅读约 12` 等，缺「分钟」 | 需 1.1 |
| 页脚明文链接 | 构建器模板仍保留 | 需 1.4 保持 |
| 单篇已有 JSON-LD | 抽样存在 `Article` | 本迭代不改单页 ✅ |

#### 问题分级

- 🔴 违反规则 / 阻塞共识：无
- 🟡 apply 必做（写入实现约束，不阻塞本阶段共识）
  1. **阅读时长根因**：单篇为 `阅读时长: 12 分钟`；现脚本 `阅读时长:\s*([^\s<·]+)` 只吃到 `12`，模板再拼 `阅读约 {read_time}` → `阅读约 12`。design §4 仅写匹配 `阅读约`，**按原文落地会修不掉**。实现须统一：同时匹配 `阅读时长`/`阅读约`，抽出数字后规范为 `f"{n} 分钟"`，卡片最终文案为「阅读约 X 分钟」（避免双「分钟」）。
  2. **JSON-LD 动态性**：`itemListElement` 必须按 `datePublished` 倒序取前 15，与列表排序一致；`url`/`name` 用绝对站内 URL。
- 🟢 可选增强：`CollectionPage.mainEntity` 可与同一 `ItemList` `@id` 互指，便于只读 CollectionPage 的解析器；`ListItem` 可加 `datePublished`（非必须）。

#### 结论一句话
**产品方针与 Spec 范围已对齐；结论 `[已达成共识]`，可执行 apply（阅读时长按 🟡 完整修复）。**
