# Design: 多版本生成采纳与草稿废纸篓安全回档

> **目标定界**：本方案服务于 PC 浏览器桌面端交付工作台（纯 Web 单目标，运行于 NE1 8088 端口），非微信小程序或移动端，交互使用标准鼠标悬停（Hover）与浏览器本地持久化（`localStorage`）。
> **消费方全仓排查实据**：经全仓 grep 检索，`StudioEditor.vue` 与 `StudioFileTree.vue` 的真实消费方仅有 `Step0App.vue`（阶段零）与 `Step1App.vue`（阶段一）；`web/index.html` 中阶段二至六采用原生 JS 函数，完全不加载此 Vue 组件，架构改动天然具备零污染隔离性。

---

## 一、架构设计与单一真相源 (SSOT)

### 1. 核心工序槽位与共享配置模块 (`GEO/web/step0-src/config/studioArtifactConfig.js`)
为杜绝“Step0App 与 useStep1 重复面条代码”及“StudioEditor 跨阶段污染与硬编码”，所有槽位字典、阶段收窄器、版本正则与双重锁统一收敛于单一共享配置模块：

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

/**
 * 按阶段收窄有效采纳槽位白名单 (彻底解决跨阶段污染)
 * @param {'step0'|'step1'} stage
 * @returns {string[]}
 */
export function getSlotsByStage(stage) {
  return Object.keys(CANONICAL_SLOT_DICT).filter(
    (slotKey) => CANONICAL_SLOT_DICT[slotKey].stage === stage
  );
}

/**
 * 按阶段获取受系统终身保护的规范骨干文件名集合
 * @param {'step0'|'step1'} stage
 * @returns {string[]}
 */
export function getCoreFilesByStage(stage) {
  return Object.values(CANONICAL_SLOT_DICT)
    .filter((item) => !stage || item.stage === stage)
    .map((item) => item.canonicalName);
}

/**
 * 动态根据槽位前缀构建严格版本提取正则
 * @param {string} slotKey
 * @returns {RegExp}
 */
export function buildSlotRegex(slotKey) {
  const item = CANONICAL_SLOT_DICT[slotKey];
  const prefix = item?.prefix || 'V';
  return new RegExp(`^${prefix}(\\d+)`, 'i');
}
```

### 2. 反向推导与确定性槽位映射
反向解析任意文件所属工序槽位：
1. 若已有 `file.slotKey`，直接使用；
2. 查字典比对规范骨干文件名：若某槽位 `item.canonicalName === filename`，命中返回该 `slotKey`；
3. 遍历 `CANONICAL_SLOT_DICT`（**严格按 `baseSlotName` 字符长度降序匹配**）：若 `filename.startsWith(item.baseSlotName)`，长前缀优先返回对应 `slotKey`（杜绝 `好看大屏` 与 `文字版` 互串）；
4. 若均未命中，派生为专属独立槽位 `'slot_' + filename.replace(/\.[^/.]+$/, '')`（非核心工序槽位不可采纳为生效底牌）。

### 3. 版本号受控提取与防重名防覆盖算法
重新生成时，扫描工作区全量文件（包含 `isDeleted: true` 在废纸篓中的文件）：
1. 找出属于该 `slotKey` 的全量文件；
2. **提取版本序号**：
   - 文件名：严格提取 `/第(\d+)版/` 正则捕获组；
   - 标签：调用 `buildSlotRegex(slotKey)` 动态提取标签数字；
   - **安全铁律**：严禁松散 `\d+` 提取，杜绝将 `01_`、`02_` 等前缀编号误读为版本序号！
3. 提取有效数值并过滤 `filter(Number.isFinite)`，计算最大序号：`maxVer = Math.max(...versions, 1)`；
4. 新文件命名：`${baseSlotName}_第${maxVer + 1}版.${ext}`；
5. 新草稿标签：`${item.prefix}${maxVer + 1}-Draft`；`isActive: false`。

---

## 二、状态正交性、只读防护与主干镜像模型

### 1. 正交的文件生命周期与只读判定表 (彻底解决 🔴1 与 C1)
为彻底杜绝“`!isActive` 导致新建文件和待打磨候选草稿无法编辑”，并消除“规范主干退级后双向篡改分叉”的致命漏洞，确立清晰的只读判定模型：

| 文件类型 | `isActive` | 是否废纸篓 | 是否淘汰旧版 | 是否只读 (`isReadOnly`) | 顶栏徽章显示 (文字+主题色) | 保存文件按钮 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **客户生效底牌** (当前活跃版) | `true` | `false` | `false` | **可编辑 (`false`)** | [徽章: 客户生效底牌 `Vn`] | 展示（保存并联动镜像主干） |
| **最新候选工作草稿** (如重抓第2版) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 候选工作草稿 `V2-Draft`] | 展示（点击保存本地工作副本） |
| **手动新建文件** (`newFile`) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 自定义工作草稿] | 展示（点击保存本地工作副本） |
| **规范主干(自动镜像)** (已采纳新版后) | `false` | `false` | - | **只读 (`true` · 单向镜像)** | [徽章: 规范主干 · 自动镜像] | **隐藏** (仅程序自动镜像写入) |
| **已淘汰历史版本** (同槽存在更新生效版) | `false` | `false` | `true` | **强制只读 (`true`)** | [徽章: 历史版本 · 只读归档] | **隐藏** (拦截 Cmd+S，防错版覆盖) |
| **废纸篓归档文件** | `false` | `true` | - | **强制只读 (`true`)** | [徽章: 废纸篓归档 · 只读状态] | **隐藏** (提示一键恢复) |

- **只读判定函数 (`isReadOnlyFile`)**：
  ```javascript
  export function isReadOnlyFile(file, files, stage) {
    if (!file) return false;
    // 1. 废纸篓必定只读
    if (Boolean(file.isDeleted || file.is_deleted)) return true;
    // 2. 属于规范主干且当前槽位已有更新的活跃采纳版：强制只读（仅接受程序镜像，禁止用户直接修改骨干产生分叉）
    const coreFiles = getCoreFilesByStage(stage);
    if (coreFiles.includes(file.name) && !file.isActive) {
      return true;
    }
    // 3. 属于某槽位的更旧被淘汰历史版本：强制只读
    if (!file.isActive && isHistoricalRetired(file, files)) {
      return true;
    }
    // 4. 当前生效底牌、最新候选工作草稿、新建文件：完全可编辑打磨
    return false;
  }
  ```

### 2. 活动文件保存与主干自动镜像契约 (彻底解决 C2 & C3)
- **前端工作台单一规范真相源**：
  - 各工序的规范主干文件（如 `01_网络底座指标_待对照.md`）是全交付流程与下游消费的唯一基准文件；
  - **初版骨干留档机制 (解决 🟡D)**：初次采纳新版本（从初始骨干升级为第 2 版）时，系统自动将原骨干内容克隆留档为 `${baseSlotName}_第1版.${ext}`，确保首版内容 100% 完整留存；
  - **单向镜像更新机制**：
    - 交付人员在当前生效版本（`file.isActive === true`，如 `第2版`）上编辑打字并点击【保存文件】（或按 Cmd+S）时，系统在保存该文件自身的同时，**自动将最新 content 与 versionTag 同步单向镜像覆盖到对应槽位的规范骨干文件对象中**；
    - 同步更新快照 `geo_step1_active_slots_${clientId}` 的 `updatedAt` 时间戳；
    - 规范主干文件始终维持当前采纳生效内容的 100% 镜像，下游阶段读取该规范文件名时绝对是最新数据，彻底消灭错版覆盖与断链！

### 3. 一键恢复的确定性生命周期与单槽单一 Active (彻底解决 🔴3)
从废纸篓点击【恢复】时的确定性状态收敛算法：
```javascript
export function handleRestoreFileAction(filename, files, slotKey) {
  const target = files[filename];
  if (!target) return;
  // 1. 移出废纸篓
  target.isDeleted = false;
  target.is_deleted = false;
  
  // 2. 判定该槽位是否已有活跃生效版本
  const hasActive = Object.values(files).some(
    f => f.slotKey === slotKey && f.isActive === true && f.name !== filename
  );
  
  if (!hasActive) {
    // 若当前槽位无任何 active（例如原 active 被误删后恢复），顺理成章恢复为生效底牌
    target.isActive = true;
  } else {
    // 严格保持 isActive: false，绝不抢占 active，绝对守住单槽单一 active 不变量！
    target.isActive = false;
  }
}
```
恢复后的只读属性自动重新求值：若为未采纳的新草稿，恢复后即为可编辑工作草稿；若为被淘汰旧版，恢复后作为历史旧版存留，提示【历史版本 · 只读归档】，右侧提供【设为客户采纳】供用户需要时反悔转正。

### 4. 双重不可删除安全锁与死按钮根除 (彻底解决 C4 与 🔴2)
- **删除按钮在左栏树中的渲染判定 (`canDeleteFile`)**：
  ```javascript
  export function canDeleteFile(file, stage) {
    if (!file) return false;
    // ① 正在生效的底牌终身不可删
    if (file.isActive) return false;
    // ② 对应阶段的规范骨干文件即使退级也受系统终身保护，禁止删除
    const coreFiles = getCoreFilesByStage(stage);
    if (coreFiles.includes(file.name)) return false;
    // ③ 已经在废纸篓中的不可重复点删除
    if (file.isDeleted || file.is_deleted) return false;
    return true;
  }
  ```
  在 `StudioFileTree.vue` 中仅当 `canDeleteFile(files[fn], props.stage)` 为 `true` 时才 hover 浮现垃圾桶图标，逻辑层执行相同校验，规范骨干永远不出现垃圾桶，彻底杜绝死按钮！

---

## 三、中栏双行独立解耦架构 (`StudioEditor.vue`)

### 1. 顶栏双行解耦排布
彻底解决单行同时承载多 Tab 标签与快捷操作按钮导致的拥挤与遮挡：
1. **第一行（状态与操作工具栏）**：
   - **左侧状态区**：展示文件状态徽章（生效底牌 / 候选工作草稿 / 规范主干镜像 / 历史只读 / 废纸篓只读）、字数、生成时间（如 `生成时间: 2026-09-28 20:01:25`，缺失时友好展示 `生成时间: 未知`）；
   - **右侧操作区（偏右对齐）**：
     - 若为废纸篓文件：提供醒目的【一键恢复此文件】高亮按钮（触发 `@restore-file`，**严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色**）；直接隐藏【设为采纳】与【保存文件】；
     - 若为历史淘汰只读版本或规范主干镜像：展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】，直接隐藏【保存文件】；
     - 若为候选工作草稿（未采纳）：展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】、【保存文件】；
     - 若为当前生效底牌：展示【客户生效底牌】、【源码/预览】、【全屏】、【一键复制】、【保存文件】。
2. **第二行（文件 Tab 标签栏）**：
   - 独立一行专门承载 `openTabs` 多文件切换与关闭；
   - 若该 Tab 属于废纸篓文件，在文件名后标注 `[废纸篓]` 浅色标识；
   - 点击 Tab 正常切换；点击 `×` 正常关闭。

### 2. 只读保护与快捷键守卫
- 当 `isReadOnlyFile(currentFile, files, stage)` 为 `true` 时，`<textarea>` 自动置为 `:readonly="true"` 并应用只读浅色背景；
- 监听文本框键盘事件，在只读态下拦截 `Ctrl+S / Cmd+S`：
  - 若为废纸篓文件，提示：“当前文件处于废纸篓只读状态，不可保存；请先点击【一键恢复】”；
  - 若为规范主干镜像或历史淘汰版本，提示：“当前为只读归档版本，不可直接覆盖保存；如需以此为准，请先点击【设为客户采纳】”。

### 3. 组件 Props 防污染与槽位阶段收窄 (彻底解决 🔴2)
`StudioEditor.vue` 不再以全量 8 槽作默认值，而是要求由父 App 显式传入本阶段有效槽位子集：
```javascript
const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
  renderMode: { type: String, default: 'code' },
  /** 由父组件按阶段显式传入：Step0App 传入 getSlotsByStage('step0')，Step1App 传入 getSlotsByStage('step1') */
  validAdoptSlots: { type: Array, default: () => [] },
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

### 1. 纯前端工作区持久化体系
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

### 2. 存量兼容与健壮性保障
- **命名兼容**：统一使用驼峰 `isDeleted`，反序列化时兼容旧键：
  `file.isDeleted = file.isDeleted ?? file.is_deleted ?? false`；
- **无效 openTabs 过滤**：运行时打开废纸篓文件查验仅存内存；页面反序列化时一律剔除 `isDeleted: true` 或在 `files` 中不存在的无效 Tab；
- **时间戳标准化**：`generatedAt` 统一记录 ISO 字符串，UI 展示层通过 `new Date(iso).toLocaleString('zh-CN')` 格式化，缺失时兜底显示“未知生成时间”。
