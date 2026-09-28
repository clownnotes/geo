# Design: 多版本生成采纳与草稿废纸篓安全回档

## Architecture (面向对象模型与架构设计)

### 1. 面向对象三问
- **【对象是什么】**：交付流水线文件项（`FileItem`）与废纸篓管理对象。
- **【属性有哪些】**：
  - `name`: 文件名（唯一键，如 `01_网络底座指标_待对照.md` 或 `01_网络底座指标_V2.md`）；
  - `category`: 分类（如 `materials` / `drafts` / `reports`）；
  - `content`: 文件文本内容；
  - `isActive`: **布尔值，是否为当前工序已采纳生效底牌**（`true` 时受系统保护，不可删除）；
  - `versionTag`: 版本标签（如 `V1`、`V2` 或 `QA-V1`）；
  - `generatedAt`: 生成时间戳（格式化文本，如 `2026-09-28 19:28`）；
  - `is_deleted`: **布尔值，是否已移入废纸篓归档**（`true` 时从主树隐藏，移入底部废纸篓）。
- **【行为是什么】**：
  - `adopt(file)`：将候选草稿标记为生效底牌，原同类生效文件退级为普通草稿；
  - `delete(file)`：仅允许对未采纳草稿执行软删除，置 `is_deleted = true`，移入废纸篓；
  - `restore(file)`：从废纸篓一键原位回档，置 `is_deleted = false`；
  - `refreshVersion(file)`：重新生成时更新内容并打上最新时间戳与版本号。

---

## State Diagram (状态流转与安全防呆)

```
[新生成 / 初始文件]
       │
       ▼
   ┌─────────┐   点击【采纳生效底牌】    ┌────────────────┐
   │  草稿态 │ ─────────────────────▶ │   已采纳底牌   │
   │  (可删) │ ◀───────────────────── │  (受保护禁止删) │
   └─────────┘     同类新版本采纳后     └────────────────┘
       │           自动退回普通草稿
       │
       │ 点击【删除】
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
- **草稿文件删除按钮交互**：
  在文件列表中，仅当 `!files[fn]?.isActive` 时，hover 浮现 Lucide `trash-2` 图标，点击阻止冒泡并触发 `emit('deleteFile', fn)`；已采纳文件受到保护，不渲染删除按钮。
- **底部废纸篓抽屉交互**：
  计算属性 `trashFiles = computed(() => Object.keys(props.files).filter(fn => props.files[fn].is_deleted))`。
  若 `trashFiles.length > 0`，在左栏底部展示：
  - 头部折叠条：【已归档 / 废纸篓 (`trashFiles.length`)】；
  - 展开列表：展示被删草稿名，右侧提供【恢复】按钮（使用项目既有先例的 Lucide `rotate-cw` 图标），点击触发 `emit('restoreFile', fn)`。

### 2. 中栏编辑器采纳判定与胶水层 (`StudioEditor.vue` & `Step1App.vue`)
- **放宽采纳守卫条件 (`StudioEditor.vue:191-196`)**：
  将原本仅限阶段零的 `questions/answers` 扩展为全阶段兼容白名单：
  ```js
  const canAdoptCurrentFile = computed(() => {
    if (!currentFile.value) return false;
    if (currentFile.value.isActive) return false;
    const cat = currentFile.value.category;
    // 阶段零：questions/answers；阶段一：materials/drafts/reports；或只要定义了 versionTag 均支持采纳
    return ['questions', 'answers', 'materials', 'drafts', 'reports'].includes(cat) || !!currentFile.value.versionTag;
  });
  ```
- **采纳按钮文案与事件**：
  按钮文案沿用既有标准【设为客户采纳】（配 Lucide `star` 图标），点击派发 `emit('adopt-file', activeFileName)` 与 `emit('adoptFile', activeFileName)`。
- **胶水层串联 (`Step1App.vue`)**：
  - `<StudioFileTree :show-status-badge="true" @delete-file="handleDeleteFile" @restore-file="handleRestoreFile" ... />`
  - `<StudioEditor @adopt-file="handleAdoptFile" @adoptFile="handleAdoptFile" ... />`

### 3. 阶段一业务逻辑 (`GEO/web/step0-src/useStep1.js`)
- **采纳逻辑 (`handleAdoptFile`)**：
  将目标文件设为 `isActive: true`，将同一分类或同一前缀的旧生效底牌置为 `isActive: false`，调用 `saveState()` 并 Toast 提示“已成功将该版本设为生效底牌！”；
- **软删除逻辑 (`handleDeleteFile`)**：
  严格校验 `if (files.value[filename]?.isActive) return;` 杜绝误删底牌。设置 `files.value[filename].is_deleted = true`。若当前打开的文件是被删文件，自动平滑切换至当前分类下首个有效文件，调用 `saveState()` 并提示“已移入废纸篓，可在左栏底部随时恢复”；
- **恢复逻辑 (`handleRestoreFile`)**：
  设置 `files.value[filename].is_deleted = false`，调用 `saveState()` 并自动选中该文件。

---

## Data Structure & Storage (持久化规范)

- 本地存储键：`` `geo_step1_state_${clientId}` ``
- 存储字典结构：
  ```json
  {
    "files": {
      "01_网络底座指标_待对照.md": {
        "category": "materials",
        "content": "...",
        "isActive": true,
        "versionTag": "V1",
        "generatedAt": "2026-09-28 19:28",
        "is_deleted": false
      },
      "01_网络底座指标_候选试算.md": {
        "category": "materials",
        "content": "...",
        "isActive": false,
        "versionTag": "V2-Draft",
        "generatedAt": "2026-09-28 19:35",
        "is_deleted": true
      }
    },
    "activeFileName": "01_网络底座指标_待对照.md"
  }
  ```
- 刷新页面后，文件采纳状态、版本号、生成时间戳与废纸篓软删除标记完全保持。
