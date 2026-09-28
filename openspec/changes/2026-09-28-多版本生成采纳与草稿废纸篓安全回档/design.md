# Design: 多版本生成采纳与草稿废纸篓安全回档

> **目标定界**：本方案服务于 PC 浏览器桌面端交付工作台（纯 Web 单目标，运行于 NE1 8088 端口），非微信小程序或移动端，交互使用标准鼠标悬停（Hover）与浏览器本地持久化（`localStorage`）。
> **消费方全仓排查实据**：经全仓 grep 检索，`StudioEditor.vue` 与 `StudioFileTree.vue` 的真实消费方仅有 `Step0App.vue`（阶段零）与 `Step1App.vue`（阶段一）；`web/index.html` 中阶段二至六采用原生 JS 函数，完全不加载此 Vue 组件，架构改动天然具备零污染隔离性。

---

## 一、架构设计与单一真相源 (SSOT)

### 1. 核心工序槽位与共享配置模块 (`GEO/web/step0-src/config/studioArtifactConfig.js`)
为杜绝“Step0App 与 useStep1 重复面条代码”及“StudioEditor 内部硬编码”，所有槽位字典、骨干清单、双重锁规则与版本算法统一定义于独立共享配置模块：

```javascript
/**
 * 8 大核心工序槽位字典与规范骨干配置
 */
export const CANONICAL_SLOT_DICT = {
  slot_stage0_questions: {
    canonicalName: '01_豆包提问清单_推荐版.txt',
    baseSlotName: '01_豆包提问清单',
    category: 'questions',
    stage: 'step0',
    prefix: 'QA-V',
  },
  slot_stage0_answers: {
    canonicalName: '02_豆包实测回答记录_初测.txt',
    baseSlotName: '02_豆包实测回答',
    category: 'answers',
    stage: 'step0',
    prefix: 'QA-V',
  },
  slot_metrics: {
    canonicalName: '01_网络底座指标_待对照.md',
    baseSlotName: '01_网络底座指标',
    category: 'materials',
    stage: 'step1',
    prefix: 'V',
  },
  slot_stage0_qa: {
    canonicalName: '01_阶段零豆包实测问答素材.md',
    baseSlotName: '01_阶段零豆包实测问答素材',
    category: 'materials',
    stage: 'step1',
    prefix: 'V',
  },
  slot_draft: {
    canonicalName: '01_商业诊断与转化初稿.md',
    baseSlotName: '01_商业诊断与转化初稿',
    category: 'drafts',
    stage: 'step1',
    prefix: 'V',
  },
  slot_report_screen: {
    canonicalName: '01_老板商业诊断报告_好看大屏.html',
    baseSlotName: '01_老板商业诊断报告_好看大屏',
    category: 'reports',
    stage: 'step1',
    prefix: 'V',
  },
  slot_report_text: {
    canonicalName: '01_老板商业诊断报告_文字版.md',
    baseSlotName: '01_老板商业诊断报告_文字版',
    category: 'reports',
    stage: 'step1',
    prefix: 'V',
  },
  slot_report_tech: {
    canonicalName: '01_工程师底座技术审计.md',
    baseSlotName: '01_工程师底座技术审计',
    category: 'reports',
    stage: 'step1',
    prefix: 'V',
  },
};

/** 8 大初始规范骨干文件名集合 (双重锁第二重基准) */
export const CANONICAL_CORE_FILES = Object.values(CANONICAL_SLOT_DICT).map(item => item.canonicalName);

/** 允许采纳的合法槽位白名单 */
export const VALID_ADOPT_SLOTS = Object.keys(CANONICAL_SLOT_DICT);
```

### 2. 反向推导与确定性槽位映射
反向解析任意文件所属工序槽位：
1. 若已有 `file.slotKey`，直接使用；
2. 匹配规范骨干字典：若 `CANONICAL_CORE_FILES.includes(filename)`，直接返回字典对应 `slotKey`；
3. 遍历 `CANONICAL_SLOT_DICT`（**严格按 `baseSlotName` 字符长度降序匹配**）：若 `filename.startsWith(item.baseSlotName)`，长前缀优先返回对应 `slotKey`（杜绝 `好看大屏` 与 `文字版` 互串）；
4. 若均未命中，派生为专属独立槽位 `'slot_' + filename.replace(/\.[^/.]+$/, '')`（杂项槽位不可被采纳为系统底牌）。

### 3. 版本号受控提取与防重名防覆盖算法
重新生成时，扫描工作区全量文件（包含 `isDeleted: true` 在废纸篓中的文件）：
1. 找出属于该 `slotKey` 的全量文件；
2. **提取版本序号**：
   - 文件名：严格提取 `/第(\d+)版/` 正则捕获组；
   - 标签：阶段零提取 `/^QA-V(\d+)/i`，阶段一提取 `/^V(\d+)/i`；
   - **安全铁律**：严禁松散 `\d+` 提取，杜绝将 `01_`、`02_` 等前缀编号误读为版本序号！
3. 计算最大序号：`maxVer = Math.max(...versions, 1)`；
4. 新文件命名：`${baseSlotName}_第${maxVer + 1}版.${ext}`；
5. 新草稿标签：阶段零 `QA-V${maxVer + 1}-Draft`，阶段一 `V${maxVer + 1}-Draft`；`isActive: false`。

---

## 二、状态正交性、只读防护与主干镜像模型

### 1. 正交的文件生命周期与可编辑性判定 (解决 C1)
为彻底杜绝“`!isActive` 导致新建文件和待打磨候选草稿无法编辑”的死角，系统将“生效状态”与“只读归档状态”完全解耦：

| 文件类型 | `isActive` | 是否废纸篓 | 是否淘汰旧版 | 是否只读 (`isReadOnly`) | 顶栏徽章显示 | 保存文件按钮 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **客户生效底牌** | `true` | `false` | `false` | **可编辑 (`false`)** | 🟢 客户生效底牌 [`Vn`] | 展示（可保存） |
| **最新候选草稿** (如重抓出第2版) | `false` | `false` | `false` | **可编辑 (`false`)** | ⚪ 候选工作草稿 [`V2-Draft`] | 展示（点击保存本地草稿） |
| **手动新建文件** (`newFile`) | `false` | `false` | `false` | **可编辑 (`false`)** | ⚪ 自定义工作草稿 | 展示（可保存） |
| **规范主干(自动镜像)** | `false` (若采纳了新版) | `false` | `false` | **可编辑 (`false`)** | 🟣 规范主干 · 自动镜像 | 展示（保存联动镜像） |
| **已淘汰历史版本** (同槽存在更新生效版) | `false` | `false` | `true` | **强制只读 (`true`)** | ⚪ 历史版本 · 只读归档 | **隐藏** (拦截 Cmd+S) |
| **废纸篓归档文件** | `false` | `true` | - | **强制只读 (`true`)** | ⚪ 废纸篓归档 · 只读状态 | **隐藏** (提示一键恢复) |

- **只读判定函数 (`isReadOnlyFile`)**：
  ```javascript
  export function isReadOnlyFile(file, files) {
    if (!file) return false;
    // 1. 废纸篓必定只读
    if (Boolean(file.isDeleted || file.is_deleted)) return true;
    // 2. 属于某槽位的更旧被取代历史版本，才强制只读
    if (!file.isActive && isHistoricalRetired(file, files)) return true;
    return false;
  }
  ```

### 2. 活动文件保存与主干自动镜像契约 (解决 C2 & C3)
- **前端工作台单一规范真相源**：
  - 各工序的规范主干文件（如 `01_网络底座指标_待对照.md`）是全交付流程与外部下游消费的唯一基准文件；
  - 无论交付人员在规范骨干上直接编辑保存，还是采纳了 `第2版` 并在 `第2版` 上编辑保存：
    - **当且仅当当前编辑文件是活跃生效文件（`isActive === true`）时**，点击【保存文件】或按 Cmd+S，系统在保存该文件自身的同时，**自动将最新内容镜像更新到同槽位的规范主干文件对象中**，并同步持久化到 `localStorage`；
    - 规范主干文件始终维持当前采纳生效内容的 100% 镜像，下游阶段读取该规范文件名时绝对是最新数据，彻底消灭错版覆盖与断链！

### 3. 双重不可删除安全锁与死按钮根除 (解决 C4)
- **删除按钮在左栏树中的渲染判定 (`canDeleteFile`)**：
  ```javascript
  export function canDeleteFile(file) {
    if (!file) return false;
    // ① 生效底牌不可删
    if (file.isActive) return false;
    // ② 8 大规范骨干文件即使退级也终身不可删
    if (CANONICAL_CORE_FILES.includes(file.name)) return false;
    // ③ 已经在废纸篓中的不可重复点删除
    if (file.isDeleted || file.is_deleted) return false;
    return true;
  }
  ```
  在 `StudioFileTree.vue` 中仅当 `canDeleteFile(file)` 为 `true` 时才 hover 浮现垃圾桶图标，逻辑层执行相同校验，彻底杜绝死按钮。

---

## 三、中栏双行独立解耦架构 (`StudioEditor.vue`)

### 1. 顶栏双行解耦排布
彻底解决单行同时承载多 Tab 标签与快捷操作按钮导致的拥挤与遮挡：
1. **第一行（状态与操作工具栏）**：
   - **左侧状态区**：展示文件状态徽章（生效底牌 / 候选工作草稿 / 规范主干镜像 / 历史只读 / 废纸篓只读）、字数、生成时间（如 `生成时间: 2026-09-28 20:01:25`）；
   - **右侧操作区（偏右对齐）**：
     - 若为废纸篓文件：提供醒目的【一键恢复此文件】高亮按钮（触发 `@restore-file`，**严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色**）；直接隐藏【设为采纳】与【保存文件】；
     - 若为历史淘汰只读版本：展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】，直接隐藏【保存文件】；
     - 若为可编辑草稿（未采纳）：展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】、【保存文件】；
     - 若为当前生效底牌：展示【客户生效底牌】、【源码/预览】、【全屏】、【一键复制】、【保存文件】。
2. **第二行（文件 Tab 标签栏）**：
   - 独立一行专门承载 `openTabs` 多文件切换与关闭；
   - 若该 Tab 属于废纸篓文件，在文件名后标注 `[废纸篓]` 浅色标识；
   - 点击 Tab 正常切换；点击 `×` 正常关闭。

### 2. 只读保护与快捷键守卫
- 当 `isReadOnlyFile(currentFile, files)` 为 `true` 时，`<textarea>` 自动置为 `:readonly="true"` 并应用只读浅色背景；
- 监听文本框键盘事件，在只读态下拦截 `Ctrl+S / Cmd+S`：
  - 若为废纸篓文件，提示：“当前文件处于废纸篓只读状态，不可保存；请先点击【一键恢复】”；
  - 若为历史淘汰版本，提示：“当前为历史归档版本，不可直接覆盖保存；如需以此为准，请先点击【设为客户采纳】”。

### 3. 组件 Props 防污染与槽位解耦 (解决 A2)
`StudioEditor.vue` 不再硬编码有效槽位，通过 prop 动态传入：
```javascript
const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
  renderMode: { type: String, default: 'code' },
  /** 允许采纳的合法槽位列表，默认使用共享配置 VALID_ADOPT_SLOTS */
  validAdoptSlots: { type: Array, default: () => VALID_ADOPT_SLOTS },
});
```
判定计算属性：
```javascript
const canAdoptCurrentFile = computed(() => {
  if (!currentFile.value || currentFile.value.isActive || currentFile.value.isDeleted) return false;
  return props.validAdoptSlots.includes(currentFile.value.slotKey);
});
```

---

## 四、数据持久化与下游消费契约

### 1. 纯前端工作区持久化体系 (解决 B3)
本工作台为纯 Web 交付专家沙盒，完全基于 `localStorage` 进行高性能持久化与跨阶段通信：
- **阶段零存储键**：`geo_step0_files_${clientId}`；
- **阶段一存储键**：`geo_step1_state_${clientId}`；
- **跨阶段生效底牌快照**：
  - 阶段零快照：`geo_step0_active_qa_${clientId}`（包含 `activeQaVersion`、`activeQuestionFile`、`activeAnswerFile`）；
  - 阶段一块照：`geo_step1_active_slots_${clientId}`，映射各 slotKey 对应的规范骨干名与采纳来源：
    ```json
    {
      "slot_metrics": {
        "canonicalFileName": "01_网络底座指标_待对照.md",
        "adoptedDraftName": "01_网络底座指标_第2版.md",
        "versionTag": "V2",
        "updatedAt": "2026-09-28T22:30:00.000Z"
      }
    }
    ```

### 2. 存量兼容与健壮性保障 (解决 C6, C9, C10)
- **命名兼容**：统一使用驼峰 `isDeleted`，反序列化时兼容旧键：
  `file.isDeleted = file.isDeleted ?? file.is_deleted ?? false`；
- **无效 openTabs 过滤**：反序列化恢复 `openTabs` 时，过滤掉在 `files` 中不存在或已移入废纸篓但未处于查验态的无效项；
- **时间戳标准化**：`generatedAt` 记录 ISO 字符串，UI 展示层通过 `new Date(iso).toLocaleString('zh-CN')` 格式化。
