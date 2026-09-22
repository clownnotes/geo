# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

<!-- 下面是实际记录，按时间顺序往下追加 -->

### 2026-09-21 21:55 | Antigravity（师兄/架构师） | 针对阶段：propose 需求提案
- **记录内容**：
  1. 与产品负责人（师弟）深度探讨并对齐了极简协同架构。
  2. 确立“一人一公司”责任田模式，专员账号作为固定岗位槽位，成果一眼可辨。
  3. 母盘独占且只读，确立 `X.Y.Z` 业务生命周期坐标系（X=战略代际与旧文归档，Y=产品线/业务板块，Z=事实细节微调）。
  4. 权限坚决防呆：专员只增不删，润色至 80 分后直接发布至群与多端，事后抽检。
  5. 产出规范文档：`proposal.md`、`design.md`、`tasks.md`。
- **结论**：`[已达成共识]`，等待产品负责人（师弟）或跨端 IDE 审阅确认。

---

## 记录 2 — 2026-09-21 22:01 · Cursor · 阶段：review

### 结论标签：`[已达成共识]`

`proposal.md` 后半段已经改对了：不新建岗位号、不写 `owner`、不新造删除按钮、品控不进程序。`design.md` 和 `tasks.md` 还停在旧稿（`writer_01`、`owner`、HTML 注释、藏删除按钮），和提案、现码都不一致。已按现码把设计和任务改到同一套。**未改业务代码。**

### 现码事实

| 事实 | 证据 |
| :--- | :--- |
| 母盘写入不区分读和写 | `rbac.py` 约 583 行 `("/raw_materials", "article:edit")`；`server.py` 约 1734 行 POST 会覆盖素材，约 4181 行 GET 是读 |
| 开发者后缀表不看方法 | `_is_developer_route` 对 `ROUTE_DEVELOPER_SUFFIXES` 只看路径。整段放进去，GET 也会 403 |
| 改稿靠同一权限 | `article:edit` 还挂着保存定稿、确认事实等。整段收走，写文同事不能改稿 |
| 没有「永久删除文章」按钮 | `web/index.html` 搜不到该按钮。删项目是另一条开发者接口 |
| 文章日期在 JSON-LD | `scripts/create_article.py` 的 `datePublished`。没有 `author_seat` |
| 模板没有负责人字段 | `projects/_template/project.yaml` 只有 `partner_id`（合作方） |

### 编码时必须守住

1. 母盘只拦非 GET 的 `/raw_materials`，写法比照现有 `/meta`。
2. 坐标写进现有发表日期那一块。没有坐标的旧文留在当前列表。
3. 不建岗位号，不写 `owner`，不新造删除按钮。

### 阶段状态

- 可按改过的 `tasks.md` 进入 `/opsx-apply`。
- **已停步**：未编码、未归档、未推生产。

---

## 记录 3 — 2026-09-22 10:00 · Cursor · 阶段：apply

### 结论标签：`[已修正]`

按记录 2 的订正完成编码与测试。未建岗位号、未写 `owner`、未新造删除按钮、未批量改客户项目文件。

1. **坐标**：模板增加 `master_version: "1.0.0"`；`load_project_config` 缺省或非法时当成 `1.0.0`，不回写文件。
2. **母盘只读**：`_is_developer_route` 对非 GET 的 `/raw_materials` 按方法拦截（比照 `/meta`）。未放进后缀表。`article:edit` 整段保留。现码前端没有 POST 保存母盘按钮，仅 GET 列表，无需再藏。
3. **文章**：`create_article.py` 把坐标写进 JSON-LD 的 `version`（紧挨 `datePublished`）。`build_blog_index.py` 按大版本 X 拆「当前 / 历史封存」；无坐标旧文留在当前列表。
4. **测试**：新增 `tests/test_master_version.py`（9 项）。连同写文视界与 `test_rbac` 共 83 项全绿。

### 阶段状态

- 请人工确认：写文同事仍能打开证据库；直接 POST 母盘应 403；新建文章头信息带坐标；升 X 后旧代际进「历史封存」。
- **已停步**：未归档，未推生产。

---

## 记录 4 — 2026-09-22 10:30 · Antigravity（师兄/架构师） · 阶段：fix / review 终审验证

### 结论标签：`[通过]`

对端 Cursor 在 apply 阶段的实现代码与测试已全面复核，无遗留缺陷，方案完全契合极简原则：

1. **母盘只读与权限收口**：`tools/geo/rbac.py` 准确针对非 GET 的 `/api/projects/{id}/raw_materials` 限制为开发者专属，写文同事依然可以正常 GET 证据库与母盘；`article:edit` 改稿权限保持完好。
2. **母盘坐标规范**：`projects/_template/project.yaml` 与 `load_project_config` 的缺省逻辑保证了存量项目平滑过渡到 `1.0.0`，杜绝破坏存量客户文件。
3. **文章坐标与世代隔离**：`scripts/create_article.py` 正确将坐标注入 JSON-LD `version` 字段；`scripts/build_blog_index.py` 成功实现跨代（X 变化）文章自动进入「历史封存」，旧无坐标文章保持在前台。
4. **自动化回归**：
   - `python3 -m unittest tests/test_master_version.py`：9 项全绿；
   - `python3 -m unittest tests/test_rbac.py`：67 项全绿；
   - `python3 scripts/check_article_styles.py`：全站 84 篇博文 100% 合规。

### 阶段状态
- 全部变更已验证通过。
- **已停步**：严格等待用户验收确认，未归档，未推生产。

