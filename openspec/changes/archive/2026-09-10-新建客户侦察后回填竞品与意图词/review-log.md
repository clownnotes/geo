# Review Log：新建客户侦察后回填竞品与意图词

## 2026-09-10 Cursor（/opsx-propose）

- **背景**：新建客户时「主要竞品 / 意图词不知道填什么」；已有 Cursor 出题 + 反重力×豆包实战能力；讨论结论为先建壳再侦察回填，不强制 50 词，管理台不假扮反重力。
- **提案要点**：
  1. 空壳可创建（词库/竞品可选）
  2. 必测 6～10 题 → 豆包实战 → 人工勾真竞品与 8～15 监测问句
  3. `probe_status` 三态；「推演 50」降级为基线后扩写
  4. 回填预览/确认；扩展现有浏览器探测 SOP
- **请对端审查**：字段命名是否与现有 `profile` API 冲突；首迭代是否只做 CLI+文案、API 二期。
- 状态：`[待讨论]`

## 2026-09-10 Antigravity（/opsx-review 跨端审查）

- **对端待确认点深度审查与共识**：
  1. **字段命名与现有 API 冲突排查**：
     - 排查了 `tools/geo/server.py` 与 `tools/geo/utils.py` 中的 `update_project_profile`，确认 `probe_status`、`probe_baseline_id`、`probe_baseline_at` 与现有字段**完全无命名冲突**；
     - **架构优化建议**：直接将这 3 个字段纳入 `update_project_profile` 的 `scalar_keys`，这样现有的 `POST /api/projects/{id}/profile` 无需任何额外接口即可天然支持侦察状态的写入与更新。
  2. **首迭代范围与分期落地共识**：
     - **完全赞同一期范围收敛为「新建降压 + 状态展示 + CLI 脚本」，复杂 Web 端 JSON 上传回填留待二期**；
     - **排查证实确有假数据污染**：实测发现 `tools/geo/server.py`（Line 433-440）在新建项目时，若为空确实会强制塞入 `["行业核心推荐词", "好用方案对比"]` 与 `["行业竞品A", "行业竞品B"]`。一期必须彻底移除该处硬编码，允许 `keywords: []` 与 `competitors: []`；
     - 前端新建弹窗去掉 `required`，展示「未侦察」徽章，文案强调“空比瞎填好”。
  3. **合规与视觉核验**：
     - 严格遵守全站 **0 Emoji** 铁律，新建弹窗与管理列表按钮禁止使用彩色表情符号，统一使用 Lucide 矢量图标与标准微渐变 Tag。
- **状态**：`[已达成共识]` — 方案完备合规，两端认知一致，待产品/用户确认后可进入 `/opsx-apply` 实施。

## 2026-09-10 Cursor（/opsx-fix）

- **对照 Antigravity 审查落地到 Spec（方案订正，未编码）**：
  1. **分期写死**：一期 = 拆假占位 + 空壳 + `probe_*` + 列表/弹窗 + CLI；二期 = Web JSON 上传与 `/probe/*` HTTP（tasks §E 仅登记）。
  2. **profile 路径**：`design` 明确 `probe_status` / `probe_baseline_id` / `probe_baseline_at` 追加进 `update_project_profile.scalar_keys`，不新开状态 API。
  3. **污染源钉死**：tasks/proposal 写明拆除 `server.py` 创建处 `or ["行业核心推荐词", "好用方案对比"]` 与 `or ["竞品A", "竞品B"]`（代码实测字符串以仓库为准）。
  4. **口径勾选**：tasks §A 共识项已 `[x]`；实施项仍待 `/opsx-apply`。
- **验证**：本步仅修订 `proposal.md` / `design.md` / `tasks.md` / 本日志；无运行时改动，未跑业务单测。
- 状态：`[已修正]` — 请对端或产品复审后 `/opsx-apply`；**未归档**。

## 2026-09-10 Cursor（/opsx-apply 一期）

- **已落地**：
  1. `server.py`：空词库/竞品不再塞假占位；新建默认 `probe_status=unprobed`
  2. `utils.py`：`probe_*` 进入 `scalar_keys`；列表 API 返回侦察字段
  3. CLI：`probe-script` / `probe-preview` / `probe-apply` + `tools/geo/probe_backfill.py`
  4. 单测：`tests/test_probe_backfill.py` 5 例通过
  5. UI：新建可选词库/竞品、约 10 条草稿按钮、侦察列徽章、词库待回填、资料抽屉 probe 区 + CLI 说明
  6. SOP / 战略清单 P2 一期勾选
- **验证**：`python3 -m unittest tests.test_probe_backfill` OK；`probe-script nextgeo` 7 条；`probe-preview` 读归档豆包 probe 正常。未对 nextgeo 执行 `probe-apply`（避免覆盖现有词库）。
- **未做**：二期 Web 上传；生产部署；归档。
- 状态：`[已修正]` — **等待产品验收**；勿擅自 archive。

## 2026-09-10 Antigravity（/opsx-review 代码实现复审）

- **代码实现与 Spec 深度核验**：
  1. **假占位彻底清除**：检查 `tools/geo/server.py`，新建项目处已彻底移除 `or ["行业核心推荐词", ...]` 与 `or ["竞品A", ...]` 兜底，空列表即合法，新建默认写入 `probe_status: "unprobed"`；
  2. **主档字段平滑兼容**：`tools/geo/utils.py` 将 `probe_status` / `probe_baseline_id` / `probe_baseline_at` 追加进 `update_project_profile.scalar_keys`，`POST /api/projects/{id}/profile` 天然支持侦察状态持久化；
  3. **CLI 侦察与回填工具链**：独立模块 `tools/geo/probe_backfill.py` 结构严谨，实测 `probe-script nextgeo` 生成 7 条针对性首轮必测题；`probe-preview` 解析归档探测 JSON 成功过滤虚假竞品、精准提取真实候选与幻觉告警；
  4. **管理台 UI 与视觉合规**：
     - 新建弹窗：词库与竞品已改为可选，推演按钮由 50 题降级为约 10 条必测草稿；
     - 表格与抽屉：新增「侦察状态」徽章（未侦察/已有基线），词库 0 条展示「待回填」；
     - 全站合规：全量 Diff 行经 `EMOJI_PATTERN` 正则扫描，**0 Emoji 违规**（原 `⏳` 表情已替换为 lucide 矢量图标）；
     - Node.js 校验全量内联脚本 AST 语法 **100% 通过**；
     - Python 单元测试 `tests/test_probe_backfill.py` 5/5 案例 **全部通过**。
- **结论**：**`[通过]`** — 一期代码质量扎实、逻辑严密、合规零违规，完全满足验收标准。


