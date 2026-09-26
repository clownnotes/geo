# Proposal: 工作台字体对齐反重力IDE与布局修复

## Why (为什么做)
1. **字号偏小费眼**：当前阶段零工作台界面字号普遍在 10px～12px，交付专家在长时间打磨题目与核对实录时容易视觉疲劳。
2. **视觉基准对齐**：反重力 IDE 聊天界面展示了清晰舒适的现代工作台标准（正文 14px、行高 1.6、标题加粗、平滑抗锯齿）。产品要求将 Geo 控制台的字体栈与字号完全对齐反重力 IDE。
3. **修复三栏挤压变形 Bug**：此前在调整样式时，右侧 SOP 面板误写了不存在的 Tailwind 类名 `lg:w-84`，导致属性失效回退为 `w-full shrink-0` 霸占全宽，将中间代码编辑器（StudioEditor）挤压至 0 像素隐身，右侧按钮也被拉扯成怪异大长框。需要从根源彻底修复。

## What Changes (改动了什么)
1. **P0 三栏布局防挤压（本轮必改）**：
   - 修复右侧 `StudioSop.vue`：无效类名 `lg:w-84` → 标准 `w-full lg:w-80 shrink-0`（固定 320px）。
   - 中间 `StudioEditor.vue` 根节点补 `min-w-0`（与 `flex-1` 并用），防止 Flex 子项被压到 0 宽。
2. **字体栈与字号（主工程多已落地，apply 以核对为主）**：
   - 全局苹方栈 + `-webkit-font-smoothing`、等宽栈：已在 `geo-admin.css` / `index.html` 存在则只核对。
   - 目标矩阵：编辑器正文 **14px**、行号 12px、Tab 13px；资源树文件名/分类 **13px**；SOP 正文 13px、标题 15px、主按钮 14px；侧栏 0.1/0.2 为 **13px**。缺项才改，禁止无差异重写。
3. **构建与验收**：`web/step0-src` 重编 → 产物进主工程；Safari 打开 `http://127.0.0.1:8088` 验三栏与字号。

## Capabilities (新增或修改的对外能力)
- 交付专家在阶段零打磨提问清单和录入回答时，拥有与反重力 IDE 一致的清晰字体与舒适字号。
- 三栏工作台（资源管理器 240px + 中间编辑器自适应 + 右侧 SOP 面板 320px）在任何分辨率下均保持稳健三栏对齐。

## Impact (受影响的部分)
- 源码组件（本轮）：`web/step0-src/components/studio/StudioSop.vue`（P0：`lg:w-84`→`lg:w-80`）、`StudioEditor.vue`（补 `min-w-0`）；`StudioFileTree.vue` 仅字号核对。
- 全局样式：`web/geo-admin.css`, `web/index.html`（字体栈已存在则核对，不重复堆叠）。
- 静态产物：在 `web/step0-src` 重编后同步 `web/assets/step0/`。
- 验收入口：本机 Safari → `http://127.0.0.1:8088` 阶段零工作台（沙盒端口另注，不以 5188 为默认真源）。
- 非目标：`MckinseyDrawer.vue` 本轮不改。
