# Design: 多版本生成采纳与草稿废纸篓安全回档

> **目标定界**：本方案服务于 PC 浏览器桌面端交付工作台（纯 Web 单目标，运行于 NE1 8088 端口），非微信小程序，交互使用标准鼠标悬停（Hover）与浏览器本地持久化（`localStorage`）。

## Architecture (面向对象模型与架构设计)

#### 1. 面向对象三问
- **【对象是什么】**：交付流水线文件项（`FileItem`）与废纸篓管理对象。
- **【属性有哪些】**：
  - `name`: 文件名（唯一主键，如 `01_网络底座指标_待对照.md` 或 `01_网络底座指标_第2版.md`）；
  - `category`: 分类（如 `materials` / `drafts` / `reports`）；
  - `slotKey`: **交付物工序槽位键**（用于多版本退级精确互斥，绝对不按全分类粗暴降级）；
  - `content`: 文件文本内容；
  - `isActive`: **布尔值，是否为当前工序已采纳生效版本**（`true` 时受系统保护，不可删除）；
  - `versionTag`: 版本标签（如 `V1`、`V2-Draft` 或采纳后的 `V2`）；
  - `generatedAt`: 生成时间戳（格式化文本，如 `2026-09-28 20:01:25`）；
  - `is_deleted`: **布尔值，是否已移入废纸篓归档**（`true` 时从主树隐藏，移入底部废纸篓）。
- **【行为是什么】**：
  - `adopt(file)`：将候选草稿升格为生效版本（`isActive: true`，`versionTag` 规整为正式版），仅将同 `slotKey` 的旧生效版本退级为普通草稿（`isActive: false`），绝不影响同分类下其他独立交付物；
  - `delete(file)`：仅允许对未采纳草稿执行软删除，置 `is_deleted = true`，移入废纸篓；
  - `restore(file)`：从废纸篓一键原位回档，置 `is_deleted = false`；
  - `refreshVersion(slotKey)`：重新生成时，基于全量历史（含废纸篓）最大序号递增生成新草稿，防重名覆盖。

---

### 2. 工序槽位映射与版本命名规则 (SlotKey & Naming Rules)

#### (1) 工序槽位映射字典 (slotKey)
为杜绝“同分类互斥导致其他交付物断链”的致命隐患，系统按**交付物工序槽位**独立隔离，并在字典中显式固化派生主干名前缀 `baseSlotName`（严格与 `stage1Config.js` 和阶段零真实配置对齐，共 8 大核心槽位）：
| 槽位键 (`slotKey`) | 初始核心文件名 (规范骨干名) | 派生主干名前缀 (`baseSlotName`) | 派生草稿统一命名规则 | 所属分类 | 阶段适用 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `slot_stage0_questions` | `01_豆包提问清单_推荐版.txt` | `01_豆包提问清单` | `01_豆包提问清单_第${N}版.txt` | `questions` | 阶段零 |
| `slot_stage0_answers` | `02_豆包实测回答记录_初测.txt` | `02_豆包实测回答` | `02_豆包实测回答_第${N}版.txt` | `answers` | 阶段零 |
| `slot_metrics` | `01_网络底座指标_待对照.md` | `01_网络底座指标` | `01_网络底座指标_第${N}版.md` | `materials` | 阶段一 |
| `slot_stage0_qa` | `01_阶段零豆包实测问答素材.md` | `01_阶段零豆包实测问答素材` | `01_阶段零豆包实测问答素材_第${N}版.md` | `materials` | 阶段一 |
| `slot_draft` | `01_商业诊断与转化初稿.md` | `01_商业诊断与转化初稿` | `01_商业诊断与转化初稿_第${N}版.md` | `drafts` | 阶段一 |
| `slot_report_screen` | `01_老板商业诊断报告_好看大屏.html` | `01_老板商业诊断报告_好看大屏` | `01_老板商业诊断报告_好看大屏_第${N}版.html` | `reports` | 阶段一 |
| `slot_report_text` | `01_老板商业诊断报告_文字版.md` | `01_老板商业诊断报告_文字版` | `01_老板商业诊断报告_文字版_第${N}版.md` | `reports` | 阶段一 |
| `slot_report_tech` | `01_工程师底座技术审计.md` | `01_工程师底座技术审计` | `01_工程师底座技术审计_第${N}版.md` | `reports` | 阶段一 |

#### (2) 版本号递增与防重名防覆盖算法 (Anti-Collision Counter)
重新生成时，扫描当前工作区内的**全量文件（包含 `is_deleted: true` 在废纸篓中的文件）**：
1. 找出所有属于该 `slotKey` 的文件；
2. **严格受控提取版本序号**：
   - 文件名提取：严格执行 `/第(\d+)版/` 正则捕获组；
   - 标签提取：严格执行 `/^QA-V(\d+)/i`（阶段零）或 `/^V(\d+)/i`（阶段一~六）正则捕获组；
   - **安全铁律**：严禁对文件名使用松散的 `\d+` 全词提取，杜绝将 `01_`、`02_` 等前缀编号误读为版本序号！
3. 计算最大序号：`maxVersion = Math.max(...versions, 1)`；
4. 查字典获取对应 `slotKey` 的 `baseSlotName`，新文件严格统一命名为：`${baseSlotName}_第${maxVersion + 1}版.${ext}`；
5. 新版本号规则：
   - 阶段零：`versionTag: 'QA-V${maxVersion + 1}-Draft'`；
   - 阶段一~六：`versionTag: 'V${maxVersion + 1}-Draft'`。
> **防冲突保障**：即便用户抓取生成了 `第2版` 并丢入废纸篓，下次抓取依然自动递增生成 `第3版`，绝对不会发生同名覆盖或废纸篓唯一键丢失！

#### (3) versionTag 状态流转与格式规整规则
- **生成态**：草稿文件创建时，带有 `-Draft` 标记（如阶段零 `QA-V2-Draft`，阶段一 `V2-Draft`），`isActive: false`；
- **采纳态**：交付专家点击【设为客户采纳】时，新文件升格为 `isActive: true`，且其 `versionTag` 自动规整剥离 `-Draft` 后缀（如 `QA-V2-Draft` -> `QA-V2`，`V2-Draft` -> `V2`），消除“已采纳”与“草稿”同时存在的自相矛盾；
- **退级态**：原同 `slotKey` 生效版本退回为草稿（`isActive: false`），保持其原有版本号（如 `V1` 或 `QA-V1`）。

#### (4) slotKey 确定性双向映射与派生算法 (Deterministic Slot Resolution)
- **反向推导算法**：
  1. 若文件已有 `file.slotKey`，直接使用；
  2. 查字典白名单精确匹配：`EXPLICIT_SLOT_MAP[filename]`；
  3. 遍历槽位字典（**严格按 `baseSlotName` 字符长度降序排序匹配**）：若 `filename.startsWith(item.baseSlotName)`，命中并返回其 `slotKey`（长前缀优先，杜绝 `好看大屏` 与 `文字版` 互串）；
  4. 若均未命中，派生为专属独立槽位 `'slot_' + filename.replace(/\.[^/.]+$/, '')`，该槽位不与任何既有槽位产生采纳互斥。

---

### 3. 同 slotKey 单一生效不变量与双重删除安全锁 (Single-Active & Dual-Lock)

- **核心不变量**：任何时刻，同一个 `slotKey` 下有且仅有最多 1 个文件处于 `isActive: true` 状态。
- **唯一确定性初始判定谓词 (Deterministic Bootstrap Predicate)**：
  从存储加载或初始化时，判断槽位是否需要赋予默认 active：
  ```javascript
  // 判据仅基于当前同槽位下是否存在活跃文件（严格布尔求值）
  const hasActiveInSlot = Object.values(files).some(
    f => f.slotKey === slotKey && Boolean(f.isActive) === true
  );
  const bootstrapNeeded = !hasActiveInSlot;
  ```
  - 当且仅当 `bootstrapNeeded === true` 时，该槽位的初始规范骨干文件才赋默认值 `isActive: true`；
  - 若槽位下已有任何文件为 `isActive === true`（说明用户此前已采纳了新版），则骨干文件**绝不强制复活为 true**，而是保持其实际退级状态（`isActive: false`），彻底消除歧义与同槽双 Active！
- **双重不可删除保护锁 (Dual-Lock Delete Protection 解决 R1 骨干丢失风险)**：
  为彻底防止采纳新版后旧主干退级为草稿导致规范文件名被误删丢失，删除机制实行双重锁定：
  1. **第一重锁（当前生效保护）**：任何文件的 `isActive === true`，属于正在生效版本，**禁止删除**；
  2. **第二重锁（初始规范骨干保护）**：属于 8 大核心主干的初始规范文件（`CANONICAL_CORE_FILES` 白名单），**即便其处于退级态（`isActive === false`），同样受系统终身保护，禁止删除**；
  3. **可删除范围**：仅允许对**派生出来的非生效草稿版本**（如 `_第2版.md`、`_第3版.md` 等，且 `isActive === false`）执行软删除移入废纸篓。
- **下游消费契约与生效版本快照体系 (Downstream Consumption Contract 解决 R1 下游断链)**：
  - **阶段零生效底牌快照**：`geo_step0_active_qa_${clientId}`（包含 `activeQaVersion`、`activeQuestionFile`、`activeAnswerFile`）；
  - **阶段一生效槽位快照**：新增 `geo_step1_active_slots_${clientId}`，数据格式：
    ```json
    {
      "slot_metrics": { "activeFileName": "01_网络底座指标_第2版.md", "versionTag": "V2", "updatedAt": "2026-09-28 22:00:00" },
      "slot_stage0_qa": { "activeFileName": "01_阶段零豆包实测问答素材.md", "versionTag": "V1", "updatedAt": "2026-09-28 20:00:00" },
      "slot_draft": { "activeFileName": "01_商业诊断与转化初稿.md", "versionTag": "V1", "updatedAt": "2026-09-28 20:00:00" },
      "slot_report_screen": { "activeFileName": "01_老板商业诊断报告_好看大屏.html", "versionTag": "V1", "updatedAt": "2026-09-28 20:00:00" },
      "slot_report_text": { "activeFileName": "01_老板商业诊断报告_文字版.md", "versionTag": "V1", "updatedAt": "2026-09-28 20:00:00" },
      "slot_report_tech": { "activeFileName": "01_工程师底座技术审计.md", "versionTag": "V1", "updatedAt": "2026-09-28 20:00:00" }
    }
    ```
  - **消费方解析规则**：阶段一后续步骤（如初稿出具、最终多版本报告）及阶段二脚本在读取前置交付物时，统一通过 `slotKey` 解析器优先从快照读取当前 `activeFileName`，若快照未命中则安全回退到该槽位规范骨干文件名。采纳时自动同步刷新该快照，下游绝不断链！

---

## State Diagram (状态流转与安全防呆)

```
[重新抓取 / 重新生成]
       │ (全量最大序号 + 1)
       ▼
   ┌─────────┐   点击【设为客户采纳】    ┌────────────────────────┐
   │  草稿态 │ ─────────────────────▶ │   客户生效版本         │
   │ V2-Draft│                        │   V2 (去除 -Draft)     │
   │  (可删) │ ◀───────────────────── │  (系统强制保护禁止删除) │
   └─────────┘    同 slotKey 新版本采纳 └────────────────────────┘
       │            旧版退回 V1 草稿
       │
       │ 点击【删除】(仅未采纳草稿允许)
       ▼
   ┌─────────┐
   │  废纸篓 │
   │ (可恢复)│
   └─────────┘
       │
       │ 点击【恢复】
       ▼
   [回归草稿列表]
```

---

## Interface (组件属性与事件定义)

### 1. 资源管理器树组件 (`GEO/web/step0-src/components/studio/StudioFileTree.vue`)
- **Props 属性声明（防污染边界设计）**：
  ```js
  const props = defineProps({
    categories: { type: Array, required: true },
    files: { type: Object, required: true },
    activeCategory: { type: String, default: 'materials' },
    activeFileName: { type: String, default: '' },
    allowNewFile: { type: Boolean, default: true },
    allowRefresh: { type: Boolean, default: true },
    /** 是否展示生效/草稿状态徽章与删除能力（保持默认 false 防污染阶段二/三；在 Step0App 与 Step1App 中显式传 :show-status-badge="true"） */
    showStatusBadge: { type: Boolean, default: false },
  });
  ```
- **Emits 事件声明**：
  ```js
  defineEmits([
    'toggleCategory', 'openFile', 'newFile', 'refreshFiles',
    'deleteFile',   // 参数：filename，触发软删除
    'restoreFile',  // 参数：filename，触发从废纸篓恢复
  ]);
  ```
- **草稿文件删除按钮交互（UI 层防御）**：
  在文件列表中，仅当 `!files[fn]?.isActive` 时，hover 浮现 Lucide `trash-2` 图标，点击阻止冒泡并触发 `emit('deleteFile', fn)`；已采纳版本受到系统保护，不渲染删除按钮。
- **底部废纸篓抽屉交互（查看与恢复）**：
  计算属性 `trashFiles = computed(() => Object.keys(props.files).filter(fn => props.files[fn].is_deleted))`。
  若 `trashFiles.length > 0`，在左栏底部展示：
  - 头部折叠条：【已归档 / 废纸篓 (`trashFiles.length`)】；
  - 展开列表：展示被删草稿名，**支持整行点击触发 `emit('openFile', fn)`**，在中栏打开进行只读查验；右侧提供【恢复】按钮（使用已有先例的 Lucide `rotate-cw` 图标），点击触发 `emit('restoreFile', fn)`。

### 2. 中栏编辑器双行架构与只读预览 (`GEO/web/step0-src/components/studio/StudioEditor.vue`)
- **消费方分析与向下兼容保障**：
  - 当前消费方为 `Step0App.vue` 与 `Step1App.vue`；
  - 顶栏双行解耦重构（第一行操作栏偏右对齐，第二行 Tab 标签栏）为纯 UI 空间优化，天然向下兼容各阶段。
- **顶栏解耦为双行独立架构**：
  为彻底解决单行同时承载多 Tab 标签与快捷操作按钮导致的拥挤与遮挡，中栏顶栏重构为双行排布：
  1. **第一行（状态与操作工具栏）**：
     - **左侧状态区**：若当前文件处于废纸篓中（`currentFile.is_deleted`），显示醒目的【废纸篓归档 · 只读状态】中性灰徽章提示（`bg-slate-100 text-slate-600 border-slate-200`）；若为正常文件，展示文件属性、字数或生成时间。
     - **右侧操作区（偏右对齐）**：
       - 若为废纸篓文件：提供醒目的【一键恢复此文件】高亮按钮（触发 `@restore-file`，**严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `bg-[#7c5bf5] text-white hover:bg-[#6c4be5]`，严禁使用红色**）；**直接隐藏**【设为客户采纳】与【保存文件】按钮；提供【源码/预览】切换、【全屏】、【一键复制】；
       - 若为正常文件：按原逻辑展示【客户生效底牌】/【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】与【保存文件】按钮。
  2. **第二行（文件 Tab 标签栏）**：
     - 独立一行专门承载 `openTabs` 各文件切换与关闭；
     - 若该 Tab 属于废纸篓文件（`files[fn]?.is_deleted`），在文件名后标注 `[废纸篓]` 浅灰/浅紫标识；
     - 点击 Tab 正常切换激活文件；点击 `×` 正常关闭标签页（文件依然安全留在废纸篓中）。
- **废纸篓内容只读保护与快捷键拦截**：
  - 当 `currentFile?.is_deleted` 为 `true` 时，源码编辑区域的 `<textarea>` 自动置为 `:readonly="true"`，背景调整为轻微只读灰底（`bg-slate-50/70`），防止误改已归档草稿；
  - **快捷键安全守卫**：监听全局或文本框键盘事件，在废纸篓只读态下拦截 `Ctrl+S / Cmd+S`，提示“当前文件处于废纸篓只读状态，不可保存；如需修改请先点击【一键恢复】”，彻底杜绝键盘快捷键误覆盖；
  - 交付人员查验内容确认需要后，点击第一行工具栏或左侧抽屉的【一键恢复】，即可将该文件解除只读，无缝转正为正常可编辑草稿。
- **采纳守卫条件 (`StudioEditor.vue` · 解决 Y3 防杂项误采纳)**：
  仅针对系统明确注册的核心工序槽位中的未采纳正常文件开放采纳动作，严格守住安全边界：
  ```js
  const canAdoptCurrentFile = computed(() => {
    if (!currentFile.value || currentFile.value.isActive || currentFile.value.is_deleted) return false;
    // 严格限制为系统已知工序槽位，派生杂项文件不开放采纳为核心底牌
    const validSlots = [
      'slot_stage0_questions', 'slot_stage0_answers',
      'slot_metrics', 'slot_stage0_qa', 'slot_draft',
      'slot_report_screen', 'slot_report_text', 'slot_report_tech',
    ];
    return validSlots.includes(currentFile.value.slotKey);
  });
  ```

### 3. 阶段零业务胶水与状态管理 (`GEO/web/step0-src/Step0App.vue`)
- **生效底牌真相源体系 (SSOT)**：
  - **唯一真相源**：`files[fileName].isActive: true` 是全系统判断该文件是否为当前生效底牌的唯一真相源；
  - **下游快照派生**：`geo_step0_active_qa_${clientId}` 仅为下游阶段（阶段一初稿血统溯源）提供只读派生快照（含 `activeQaVersion`、`activeQuestionFile`、`activeAnswerFile`），每次采纳动作完成时由 `Step0App` 自动同步刷新，严禁双头决策。
- **采纳逻辑 (`handleAdoptFile` · 解决 R4 对齐 slotKey 隔离并剥离 -Draft)**：
  1. 获取目标文件，若不存在则提示错误；
  2. **版本号规整与剥离草稿标记**：若为带 `-Draft` 的草稿版本（如 `QA-V2-Draft`），采纳时自动规整为正式版 `QA-V2`（`targetFile.versionTag = (targetFile.versionTag || 'QA-V1').replace(/-Draft$/i, '')`）；
  3. **精确 slotKey 单底牌互斥**：以 `targetFile.slotKey` 为准（严禁按全 category 粗暴遍历），遍历相同 `slotKey` 的所有其他文件将 `isActive` 设为 `false`；目标文件设为 `isActive = true`；
  4. **双底牌配对联动**：自动寻找对侧已生效的配对底牌，联动更新其版本号与 `pairFile` 引用；
  5. 重新盖上规范化生效底牌头（标准溯源元数据头）；
  6. 持久化阶段零文件字典 `geo_step0_files_${clientId}`，并同步更新下游快照 `geo_step0_active_qa_${clientId}`；
  7. 同步触发主仓 outputs 落盘（将生效内容同步写回主仓）；
  8. 派发 `geo-step0-file-adopted` 全局事件并 Toast 提示“已成功将【xxx】设为客户采纳底牌！”。
- **草稿软删除 (`handleDeleteFile` · 实行双重保护锁)**：
  1. 逻辑层严格双重校验：
     - ① 若当前 `files.value[filename]?.isActive === true`，拦截并弹出警告 Toast：“已采纳的生效底牌受系统保护，无法删除！如需删除请先采纳其他版本”；
     - ② 若当前文件属于初始规范骨干白名单（如 `01_豆包提问清单_推荐版.txt`），拦截并提示：“初始核心规范文件为系统基础骨干，终身受系统保护，不可删除！”；
  2. 置 `files.value[filename].is_deleted = true`；
  3. 平滑回退兜底：若当前打开文件是被删文件，先切到同 slotKey 或剩余未删除 Tab；若无则切到同分类首个未删除文件；若分类全空，切到下一个有效分类或置空态，并从 `openTabs` 清除；
  4. 调用 `saveStep0FilesToStorage()` 持久化；Toast 提示“已将草稿移入废纸篓”。
- **废纸篓恢复 (`handleRestoreFile`)**：
  置 `files.value[filename].is_deleted = false`；调用 `saveStep0FilesToStorage()`；自动定位打开该文件。
- **模板绑定**：
  `<StudioFileTree :show-status-badge="true" @delete-file="handleDeleteFile" @restore-file="handleRestoreFile" @open-file="handleOpenFile" ... />`
  `<StudioEditor @adopt-file="handleAdoptFile" @restore-file="handleRestoreFile" ... />`

### 4. 阶段一业务逻辑与状态管理 (`GEO/web/step0-src/useStep1.js`)
- **采纳逻辑 (`handleAdoptFile` · 解决 R1 & R3 下游消费契约与落盘同步)**：
  1. 获取目标文件的 `slotKey`（查字典反向推导）；
  2. 遍历全量文件，将所有相同 `slotKey` 且 `name !== filename` 的旧生效版本设为 `isActive = false`；
  3. 将目标文件设为 `isActive: true`，且 `versionTag` 剥离 `-Draft` 规整为正式版（如 `V2-Draft` -> `V2`）；
  4. **刷新阶段一生效槽位快照**：同步更新 `geo_step1_active_slots_${clientId}`，记录该 `slotKey` 当前激活的 `activeFileName` 与 `versionTag`；
  5. **主仓 outputs 规范同步写回**：当用户采纳新版时，除了本地保存状态外，将当前生效版本的最新内容同步覆盖写入主仓 outputs 对应的规范主干文件路径，确保服务器端离线读取/流水线构建时始终获得最新生效内容，彻底消灭双头真相源；
  6. 调用 `saveState()` 并 Toast 提示“已将【xxx】设为客户采纳生效版本！”；
- **重新抓取派生新版 (`handleAction('crawlMetrics')`)**：
  1. 扫描当前所有包含 `slot_metrics` 的文件（含废纸篓 `is_deleted: true`）；
  2. 提取并计算最大序号 `maxVersion = Math.max(...versions, 1)`；
  3. 查字典获取 `baseSlotName = '01_网络底座指标'`，动态生成新文件 `01_网络底座指标_第${maxVersion + 1}版.md`；
  4. 注入属性：`slotKey: 'slot_metrics'`、`category: 'materials'`、`isActive: false`（草稿态，原底牌保持受保护）、`versionTag: 'V${maxVersion + 1}-Draft'`、格式化最新生成时间戳；
  5. 自动在中栏打开新草稿；原有底牌完好保留，等待交付专家核对后手动采纳。
- **软删除逻辑 (`handleDeleteFile` · 实行双重保护锁)**：
  1. 逻辑层严格双重校验：
     - 若 `files.value[filename]?.isActive === true`，提示：“已采纳的底牌文件受系统保护，无法删除！如需删除请先采纳其他版本”；
     - 若 `filename` 属于 6 大阶段一规范骨干文件（在 `CANONICAL_CORE_FILES` 中），提示：“初始核心规范文件为系统基础骨干，不可删除！”；
  2. 设置 `files.value[filename].is_deleted = true`；
  3. 平滑回退兜底：① 剩余未删除 openTabs 首项；② 全局未删除文件首项；③ 空态；
  4. 调用 `saveState()` 并提示“已将草稿移入废纸篓，可在左侧底部展开恢复”；
- **恢复逻辑 (`handleRestoreFile`)**：
  设置 `files.value[filename].is_deleted = false`，调用 `saveState()` 并自动打开选中该文件。

---

## Data Structure & Storage (持久化与存量兼容规范)

- **本地存储键划分**：
  - 阶段零文件存储键：`` `geo_step0_files_${clientId}` ``（存储阶段零全部题单与回答文件字典，以及采纳底牌键 `geo_step0_active_qa_${clientId}`）；
  - 阶段一状态存储键：`` `geo_step1_state_${clientId}` ``（存储阶段一当前步骤、激活Tab、打开的Tabs列表、工序槽位文件字典、门禁状态与备注）；
  - 阶段一生效槽位快照键：`` `geo_step1_active_slots_${clientId}` ``（映射各 slotKey 对应的当前生效文件名与版本）。
- **两层持久化与主仓落盘机制 (Client Working Copy + Backend Sync · 解决 R3 双头决策)**：
  1. **前端工作副本层 (localStorage)**：交付人员在前端的高频输入、草稿切换、废纸篓移动、多版本派生均实时保存至本地存储，保障页面刷新零丢失、离线瞬时响应；
  2. **主仓落盘同步层 (Backend outputs Sync)**：
     - 当用户点击【保存文件】或按 Cmd+S（非废纸篓只读态）时，触发 API 将当前编辑文件保存回后端 `projects/{id}/outputs/`；
     - 当用户点击【设为客户采纳】时，系统自动将当前生效的文件内容同步覆盖写入服务端 `projects/{id}/outputs/` 的对应规范主干文件名（如 `outputs/01_网络底座指标_待对照.md`），保证无论前端选了第几版，磁盘上的规范主干文件与下游 Python 探测微服务、CLI 编译输出始终保持 100% 同步！
- **存量历史数据安全兜底机制 (Migration Fallback · 彻底防御断链与双 Active · 解决 R2 & R5)**：
  从本地存储恢复时，若历史文件未记录 `isActive`、`slotKey`、`versionTag`、`is_deleted`，严格遵循：
  1. **全阶段核心骨干文件白名单安全初始化（覆盖 8 个初始主干）**：
     - **白名单文件清单 (`CANONICAL_CORE_FILES`)**：
       - 阶段零（2个）：`01_豆包提问清单_推荐版.txt` (`slot_stage0_questions`), `02_豆包实测回答记录_初测.txt` (`slot_stage0_answers`);
       - 阶段一（6个）：`01_网络底座指标_待对照.md` (`slot_metrics`), `01_阶段零豆包实测问答素材.md` (`slot_stage0_qa`), `01_商业诊断与转化初稿.md` (`slot_draft`), `01_老板商业诊断报告_好看大屏.html` (`slot_report_screen`), `01_老板商业诊断报告_文字版.md` (`slot_report_text`), `01_工程师底座技术审计.md` (`slot_report_tech`)。
     - **唯一确定性初始判定谓词 (Deterministic Bootstrap Predicate · 解决 R5)**：
       ```javascript
       const isSlotActive = (f) => f.slotKey === slotKey && Boolean(f.isActive) === true;
       const bootstrapNeeded = !Object.values(files).some(isSlotActive);
       ```
       - 当且仅当某 `slotKey` 下全量文件均无任何处于 `isActive === true` 的文件时，该槽位的初始骨干文件才赋默认值 `isActive: true`, `is_deleted: false`, 对应 `slotKey`, 对应 `versionTag: 'V1'`；
       - 若本地存储中已有任何同 `slotKey` 文件为 `isActive: true`（说明用户此前已采纳了新版），则骨干文件**绝不强制复活为 true**，而是保持其退级后的真实状态（`isActive: false`），彻底根除同槽双 Active 的致命漏洞！
     - **双重删除保护锁 (解决 R1 骨干丢失隐患)**：
       - 骨干文件即使退级为 `isActive: false`，因其名在 `CANONICAL_CORE_FILES` 白名单中，依然终身不可删除；
       - 只有非白名单的派生新版（如 `第2版.md`）且 `isActive === false`，才允许删除移入废纸篓。
  2. **动态派生文件**：未指定则 `isActive: false`，`is_deleted: false`，`versionTag: 'V1'`。
- **openTabs 增删与多状态生命周期闭环**：
  - **软删除时**：将被删文件从 `openTabs` 中安全移除，激活文件平滑回退至剩余有效文件；
  - **废纸篓查看时**：将废纸篓条目追加进 `openTabs`，激活并以只读方式在中栏渲染，Tab 显示 `[废纸篓]` 标识；
  - **关闭废纸篓 Tab 时**：从 `openTabs` 移除，文件依然安全保存在底部废纸篓抽屉中；
  - **一键恢复时**：置 `is_deleted = false`，Tab 标签上的 `[废纸篓]` 移除，文本框自动解除 `:readonly`，无缝转为可正常打字保存的活动草稿。
- 存储字典结构：
  ```json
  {
    "files": {
      "01_网络底座指标_待对照.md": {
        "category": "materials",
        "slotKey": "slot_metrics",
        "content": "...",
        "isActive": true,
        "versionTag": "V1",
        "generatedAt": "2026-09-28 20:01:25",
        "is_deleted": false
      },
      "01_网络底座指标_第2版.md": {
        "category": "materials",
        "slotKey": "slot_metrics",
        "content": "...",
        "isActive": false,
        "versionTag": "V2-Draft",
        "generatedAt": "2026-09-28 21:20:00",
        "is_deleted": true
      }
    },
    "activeFileName": "01_网络底座指标_待对照.md",
    "openTabs": ["01_网络底座指标_待对照.md", "01_网络底座指标_第2版.md"]
  }
  ```
- 刷新页面后，文件采纳状态、工序槽位、版本号、生成时间戳与废纸篓软删除标记完全保持。
