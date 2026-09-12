# Review Log：建档后侦察引导阶段0

## 2026-09-10 Cursor（/opsx-propose）

- **背景**：一期侦察 CLI 已落地，但创建后直达阶段一体检，前端无「如何与 Cursor/反重力配合」引导；产品明确要求立项阶段 0。顺带官网裸域名/无站占位、一句话业务，避免糊行业拖累出题。
- **前置**：为满足 `opsx` 单活动变更约束，已将审查 `[通过]` 的 `新建客户侦察后回填竞品与意图词` 归档（实现已在工作区，Git 提交可由产品另行指示）。
- **请对端审查**：
  1. 未侦察时「进入流水线」是否一律阶段 0，已有基线是否仍可直达 01；
  2. 托管占位域名规则是否固定 `{client_id}.baicl.cc`；
  3. 一句话业务是否新建必填。
- 状态：`[待讨论]`

## 2026-09-10 Antigravity（/opsx-review 跨端审查）

- **对端三个审查要点确认与深度共识**：
  1. **路由落点规则（未侦察阶段 0，已有基线直达 01）**：
     - **完全赞同**。未侦察（`unprobed`）项目缺乏真实竞品与意图词，直达体检无实际意义；创建成功及点击「进入流水线」统一引导至「00 侦察建档」（`step-0-probe`）；
     - 已有基线（`baseline_ready` / `awaiting_retest`）维持直达「01 现状诊断」，提升熟练运营效率；
     - 侧栏常驻「00 侦察建档」导航；`unprobed` 状态下点击阶段一采用“软提示确认（Confirm）”，警告词库缺失风险但绝不硬卡死。
  2. **托管占位域名规则（固定 `https://{client_id}.baicl.cc`）**：
     - **完全赞同**。统一使用 `https://{client_id}.baicl.cc`，符合多租户托管与反向代理拓扑；
     - 写入 `project.yaml` 的 `site_pending: true`；前端展示「由我方全托管 / 待客户域名」提示；
     - **架构联动建议**：`probe-script` 出题脚本识别 `site_pending == True` 时，自动跳过“查客户官网是否被收录”的无效测试，将 6～10 题集中倾斜至本地选型、竞品打架与品类痛点。
  3. **「一句话业务」是否必填**：
     - **强烈建议：新建弹窗中设为必填（Required）**；
     - 过去“所属行业”用户常填“制造业”、“互联网”等宽泛词，导致剧本出题发散；
     - 必填 15～80 字的一句话业务（如：“徐州及淮海经济区高精度电子皮带秤研发生产与技术服务，主打矿山与电力行业”），能为 `probe-script` 提供精准的地域、品类和业务特征锚点。
- **视觉与规范约束**：
  - 阶段 0 面板与侧栏图标严禁使用 Emoji 彩色符号，侧栏建议使用 Lucide 矢量图标 `radar` / `crosshair` / `compass`；
  - 复制命令、状态徽章与主 CTA 按钮保持全站高质感微渐变设计。
- **状态**：`[已达成共识]` — 方案完备、逻辑闭环，待产品负责人确认后可由相应端进入 `/opsx-apply` 实施。

## 2026-09-10 Cursor（/opsx-fix）

- **对照 Antigravity 共识订正 Spec（未编码）**：
  1. 路由表写死：`unprobed`→阶段 0；`baseline_ready`/`awaiting_retest`→直达 01；进 01 软确认不硬卡。
  2. 占位域名写死：`https://{client_id}.baicl.cc` + `site_pending`；UI Tag「由我方全托管 / 待客户域名」。
  3. 一句话业务：新建必填 15～80 字；`probe-script` 在 `site_pending` 时跳过官网/URL 题。
  4. 侧栏图标约定 Lucide `radar`（备选 crosshair/compass）；0 Emoji。
- **改动文件**：`proposal.md` / `design.md` / `tasks.md` / 本日志。
- 状态：`[已修正]` — 请产品确认后 `/opsx-apply`；**未归档**。

## 2026-09-10 Cursor（/opsx-apply）

- **已落地**：
  1. `utils.normalize_official_url` / `validate_business_one_liner`；profile 支持 `business_one_liner` + `site_pending`
  2. 创建 API：一句话必填、裸域名/托管占位、写入 yaml
  3. `probe-script`：一句话锚点；`site_pending` 跳过 URL 题
  4. 前端：侧栏 00、阶段 0 面板（命令复制/刷新/进 01 软确认）、新建弹窗改造、按 `probe_status` 路由
  5. SOP 更新
- **验证**：`python3 -m unittest tests.test_probe_backfill` 8/8 OK
- **未做**：归档、推生产、Web 上传 probe
- 状态：`[已修正]` — **等待产品验收**

