# Review Log — 管理端企业管理按合作方侧栏与合作方一级菜单

## 2026-09-09 | Cursor | propose 阶段

### 产品共识（用户口述）

1. **企业管理**单独拉成**一级类目**。
2. 其下**二级**按各个**代理渠道/合作方**下拉，点击分类查看。
3. **合作方管理**也升为**一级类目**（常用；后续再慢慢加功能）。

### 草案侧栏

- 工作台：仪表盘 / 商业洞察 / 运维告警 / 系统设置  
- 企业管理：全部企业 / 未分配 / {各 active 合作方}  
- 合作方管理：合作方名册（+ 二期扩展位）

### 请对端或产品确认

- [x] 「未分配」是否必须出现在二级 → **要，固定二级项**（用户 2026-09-09 确认）。
- [x] 已归档合作方是否在侧栏隐藏（建议隐藏，名册页仍可看）→ 维持建议，未反对。
- [x] 合作方管理本期是否只做名册一页 → **按推荐：只做名册一页**，不放空二级占位（用户确认）。

---

## 2026-09-09 | Cursor | 产品拍板落档

1. 企业管理二级：**全部企业** + **未分配（固定）** + 各 active 合作方。
2. 合作方管理一级下本期仅 **合作方名册**；扩展功能二期再加。

**结论**：`[已达成共识]`

> 停步：未进入 apply。待用户下达 `/opsx-apply` 或编码指令。

---

## 2026-09-09 | QwenWork | review 阶段（propose 审查，回真实代码定位风险）

### 阶段与越界核查

- 本变更为**纯 propose 阶段**：`tasks.md` 全 `- [ ]`，`review-log` 前序结论为 `[已达成共识]` 且注明未 apply。
- 越界核查：`home-partners` / `renderHomeEnterpriseNav` / `openEnterprisesByPartner` / `sidebar-group-enterprises` / `refreshPartnersAndNav` 在 `web/index.html` 命中均为 **0**；`git diff HEAD` 对 `partners.py`、`geo_partners.yaml`、`index.html` 为空（其 mtime 系上一变更 apply 遗留，已随 `cda4d89` 提交）。**确认无提前写码，无 🔴 越阶段问题。**

### 对照现状核验（`web/index.html`）

- 现网侧栏为 `data-group="home-main"` 下 **5 个平铺一级项**（仪表盘/企业管理/商业洞察/运维告警/系统设置，行 73-77）；`合作方名册` 确在系统设置 Tab（行 252）。→ proposal「Why」所称"塞在工作台平铺二级"与现状略有出入（实为平铺一级 + 设置 Tab），属措辞问题，不影响方案。

### 发现并已订正进规范（方案类）

- 🟡 **接口签名冲突（关键）**：现网 `switchHomeView(viewId, skipRoute)` 第二参已是布尔 `skipRoute`（定义 4906、调用 4880 传 `true`）。proposal 原写 `switchHomeView('home-enterprises', { partnerId })` 会与之撞车。已统一订正为专用入口 `openEnterprisesByPartner(partnerId)`（proposal Capabilities + design 风险）。
- 🟡 **归档当前正筛选合作方的空态**：补入 design 风险 + 新增 task 2.4——需自动切「未分配/全部」并重绘。
- 🟡 **父级风琴落点未定义**：补入 design + 新增 task 2.5——企业管理父级→全部企业，合作方管理父级→名册。
- 🟢 **动态 nav id 安全**：显式传入的 partner id 不强制 `agent_` 前缀（可能数字开头），但 nav id 带固定前缀故选择器安全；已在 design 风险注明。

### 结论

- 方案 IA 与已归档的上一变更衔接自洽，复用现有 `/api/partners`，无数据迁移、无新色板、无 Emoji。核心风险（接口签名）已消除。

**结论**：`[已达成共识]`（方案可进入 apply；上述 🟡/🟢 已并入 design/tasks，编码时须落实 task 2.4、2.5 与 `openEnterprisesByPartner` 入口）

> 停步：本轮仅审查与规范订正，未编码、未归档。等待用户下达 `/opsx-apply`。

---

## 2026-09-09 | Cursor | apply 阶段

### 落地

1. 侧栏三级风琴：工作台 / 企业管理（全部企业·未分配·动态合作方）/ 合作方管理（名册）。
2. `openEnterprisesByPartner` 专用入口（不占用 `switchHomeView` 第二参）；顶栏筛选与侧栏高亮双向同步。
3. 名册迁至 `panel-home-partners`；系统设置仅 LLM + 导出说明。
4. 归档当前筛选合作方 → 自动切「未分配」；父级点击落点按 design；hash `&partner=`。
5. `#home-sidebar .home-ent-submenu` 可滚动。

### 验证

- `python3 -m unittest tests.test_partners -v` → OK
- 请产品在 `:8088` 点验侧栏分类与归档联动。

**结论**：`[已修正]`（待验收，不归档）

---

## 2026-09-09 | QwenWork | review 阶段（apply 后代码复核，回真实代码 + 跑测试）

### 核验方式

不采信 Cursor 的 `[已修正]` 口头结论，逐项回 `web/index.html` 真实实现 + 运行 `python3 -m unittest tests.test_partners`（**4 项全 OK**）+ Emoji 码位扫描（**0 命中**）。

### 前轮方案风险点落实情况（全部闭环）

- ✅ **接口签名冲突已规避**：`openEnterprisesByPartner(partnerId, skipRoute)` 内部 `switchHomeView('home-enterprises', true)` 仍按老语义传布尔 `skipRoute`，未把对象塞进第二参（`index.html:4981-4989`）。
- ✅ **父级风琴落点（task 2.5）**：`onHomeEnterprisesGroupClick`→展开+`openEnterprisesByPartner('')`（全部企业）；`onHomePartnersGroupClick`→展开+`switchHomeView('home-partners')`（`4952-4960`）。
- ✅ **归档当前筛选方空态（task 2.4）**：`refreshPartnersAndNav` 检测当前筛选合作方已非 active → 自动置 `__none__`（未分配）并重绘（`5009-5020`）。
- ✅ **系统设置移除名册 Tab（task 1.4）**：无 `data-home-set="partners"`；`switchHomeSettingsTab` 加 `if (tab==='partners') tab='llm'` 兜底。
- ✅ **双向同步（task 2.2）**：`syncHomeNavHighlight` 读 `#ent-filter-partner` 反推高亮；`onEnterprisePartnerFilterChange` 联动。
- ✅ **动态 nav 安全（🟢）**：`renderHomeEnterpriseNav` 过滤 archived、`safeId` 正则清洗、`escapeHtmlSafe(name)` 防注入（`4997-5006`）。
- ℹ️ 容器 id 用 `home-group-enterprises`（非 design 字面的 `sidebar-group-enterprises`），折叠/展开走专用 `toggleHomeSidebarGroup`/`expandHomeSidebarGroup`，功能正确，属命名微调，无需改。

### 附带确认

- Cursor 同步修复了上一变更对 `partners.py` 的两条非阻断建议：YAML 引号/换行往返（`test_dump_roundtrip_with_quotes_and_newline`）、中文同名同秒 ID 唯一（`test_slug_chinese_unique_same_second`），均有单测覆盖。

### 结论

- 实现与规范一致，前轮全部 🟡/ 已闭环，无  阻断项；测试绿、无 Emoji、复用现有 `/api/partners` 无契约破坏。

**结论**：`[通过]`（代码审查通过，可进入产品验收。建议产品在 `:8088` 点验：点侧栏合作方→企业列表按方筛选；顶栏下拉与侧栏高亮双向同步；归档当前正筛合作方后自动落「未分配」）

> 停步：本轮仅审查，未编码、未归档。是否归档由用户显式下达 `/opsx-archive`。

---

## 2026-09-09 | Cursor | archive 阶段

用户显式下达 `/opsx-archive`。tasks 全部完成；对端审查结论为 `[通过]`。

**结论**：`[通过]`
