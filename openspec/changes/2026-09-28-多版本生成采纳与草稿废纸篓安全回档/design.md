# Design: 多版本生成采纳与草稿废纸篓安全回档

> **目标定界**：本方案服务于 PC 浏览器桌面端交付工作台（纯 Web 单目标，运行于 NE1 8088 端口），非微信小程序或移动端，交互使用标准鼠标悬停（Hover）与浏览器本地持久化（`localStorage`）。
> **消费方全仓排查实据**：经全仓 grep 检索，`StudioEditor.vue` 与 `StudioFileTree.vue` 的真实消费方仅有 `Step0App.vue`（阶段零）与 `Step1App.vue`（阶段一）；`web/index.html` 中阶段二至六采用原生 JS 函数，完全不加载此 Vue 组件，架构改动天然具备零污染隔离性。

---

## 一、架构设计与单一真相源 (SSOT)

### 1. 核心工序槽位与共享配置模块 (`GEO/web/step0-src/config/studioArtifactConfig.js`)
为彻底消除“Step0App 与 useStep1 重复面条代码”及“StudioEditor 跨阶段污染与硬编码”，所有槽位字典、阶段收窄器、版本正则、采纳互斥纯函数、双重锁及存量数据迁移算法统一定义于独立共享配置模块：

```javascript
/**
 * 8 大核心工序槽位字典与规范骨干配置
 * 分布：阶段零 2 槽，阶段一 6 槽
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
  if (!stage) throw new Error('[studioArtifactConfig] stage 参数必传！');
  return Object.keys(CANONICAL_SLOT_DICT).filter(
    (slotKey) => CANONICAL_SLOT_DICT[slotKey].stage === stage
  );
}

/**
 * 按阶段获取受系统终身保护的规范骨干文件名集合 (严格无兜底，杜绝反向漏洞)
 * @param {'step0'|'step1'} stage
 * @returns {string[]}
 */
export function getCoreFilesByStage(stage) {
  if (!stage) throw new Error('[studioArtifactConfig] stage 参数必传！');
  return Object.values(CANONICAL_SLOT_DICT)
    .filter((item) => item.stage === stage)
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

/**
 * 规整版本标签，剥离 -Draft 标记
 * @param {string} tag
 * @param {string} slotKey
 * @returns {string}
 */
export function normalizeVersionTag(tag, slotKey) {
  if (!tag) {
    const item = CANONICAL_SLOT_DICT[slotKey];
    return item?.prefix ? `${item.prefix}1` : 'V1';
  }
  return tag.replace(/-Draft$/i, '');
}

/**
 * 反向推导文件所属工序槽位
 * @param {string} filename
 * @param {'step0'|'step1'} stage
 * @returns {string}
 */
export function resolveSlotKey(filename, stage) {
  if (!filename) return 'slot_misc';
  const validSlots = getSlotsByStage(stage);
  
  // 1. 规范骨干精确命中
  for (const sk of validSlots) {
    if (CANONICAL_SLOT_DICT[sk].canonicalName === filename) return sk;
  }
  
  // 2. 长前缀优先匹配
  const sortedSlots = [...validSlots].sort(
    (a, b) => CANONICAL_SLOT_DICT[b].baseSlotName.length - CANONICAL_SLOT_DICT[a].baseSlotName.length
  );
  for (const sk of sortedSlots) {
    if (filename.startsWith(CANONICAL_SLOT_DICT[sk].baseSlotName)) return sk;
  }
  
  // 3. 杂项派生槽位
  return 'slot_' + filename.replace(/\.[^/.]+$/, '');
}
```

### 2. 版本号受控提取与防重名防覆盖算法
重新生成时，扫描工作区全量文件（包含 `isDeleted: true` 在废纸篓中的文件）：
```javascript
export function computeNextVersion(files = {}, slotKey) {
  const item = CANONICAL_SLOT_DICT[slotKey];
  if (!item) return { nextFileName: '', nextVersionTag: 'V2-Draft' };
  
  const slotFiles = Object.values(files).filter((f) => f.slotKey === slotKey);
  const regex = buildSlotRegex(slotKey);
  
  const versions = [];
  for (const f of slotFiles) {
    // 文件名提取
    const mName = (f.name || '').match(/第(\d+)版/);
    if (mName && mName[1]) versions.push(parseInt(mName[1], 10));
    // 标签提取
    const mTag = (f.versionTag || '').match(regex);
    if (mTag && mTag[1]) versions.push(parseInt(mTag[1], 10));
  }
  
  const validVersions = versions.filter(Number.isFinite);
  const maxVer = validVersions.length > 0 ? Math.max(...validVersions) : 1;
  const nextVer = maxVer + 1;
  
  const ext = (item.canonicalName.split('.').pop()) || 'md';
  const nextFileName = `${item.baseSlotName}_第${nextVer}版.${ext}`;
  const nextVersionTag = `${item.prefix}${nextVer}-Draft`;
  
  return { nextFileName, nextVersionTag, nextVer };
}
```

---

## 二、状态正交性、只读防护与主干镜像模型

### 1. 正交的文件生命周期与只读判定表 (彻底解决 🔴1 与 C1)
为彻底杜绝“`!isActive` 导致新建文件和待打磨候选草稿无法编辑”，并消除“规范主干退级后双向篡改分叉”的致命漏洞，确立清晰的正交判定准则：

| 文件类型 | `isActive` | 是否废纸篓 | 是否淘汰旧版 | 是否只读 (`isReadOnly`) | 顶栏徽章显示 (文字+主题色) | 保存文件按钮 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **客户生效底牌** (当前活跃版) | `true` | `false` | `false` | **可编辑 (`false`)** | [徽章: 客户生效底牌 `Vn`] | 展示（保存并联动镜像主干） |
| **最新候选工作草稿** (如重抓第2版) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 候选工作草稿 `V2-Draft`] | 展示（点击保存本地工作副本） |
| **手动新建文件** (`newFile`) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 自定义工作草稿] | 展示（点击保存本地工作副本） |
| **规范主干(自动镜像)** (已采纳新版后) | `false` | `false` | - | **只读 (`true` · 单向镜像)** | [徽章: 规范主干 · 自动镜像] | **隐藏** (仅程序自动镜像写入) |
| **已淘汰历史版本** (同槽存在更新生效版) | `false` | `false` | `true` | **强制只读 (`true`)** | [徽章: 历史版本 · 只读归档] | **隐藏** (拦截 Cmd+S，防错版覆盖) |
| **废纸篓归档文件** | `false` | `true` | - | **强制只读 (`true`)** | [徽章: 废纸篓归档 · 只读状态] | **隐藏** (提示一键恢复) |

- **历史淘汰旧版判定 (`isHistoricalRetired`)**：
  ```javascript
  export function isHistoricalRetired(file, files) {
    if (!file || !file.slotKey || file.isActive) return false;
    // 必须有 slotKey 守卫，杜绝 undefined 误判同槽
    return Object.values(files).some(
      (f) => f.slotKey === file.slotKey && f.isActive === true && f.name !== file.name
    );
  }
  ```

- **只读判定函数 (`isReadOnlyFile` · 解决 🔴1 核心闭环)**：
  ```javascript
  export function isReadOnlyFile(file, files, stage) {
    if (!file) return false;
    // 1. 废纸篓必定只读
    if (Boolean(file.isDeleted || file.is_deleted)) return true;
    
    // 2. 规范骨干：仅当同槽位确实已有更新的活跃生效版时，骨干才作为镜像只读；未采纳新版时骨干自身就是可编辑主干！
    const coreFiles = getCoreFilesByStage(stage);
    if (coreFiles.includes(file.name) && !file.isActive) {
      const hasActiveOther = Object.values(files).some(
        (f) => f.slotKey === file.slotKey && f.isActive === true && f.name !== file.name
      );
      if (hasActiveOther) return true;
    }
    
    // 3. 属于某槽位的更旧被淘汰历史版本：强制只读
    if (!file.isActive && isHistoricalRetired(file, files)) {
      return true;
    }
    
    // 4. 当前生效底牌、最新候选工作草稿、新建文件：完全可编辑打磨
    return false;
  }
  ```

### 2. 统一采纳互斥纯函数与主干单向镜像 (`computeAdoptResult` · 彻底解决 🔴3 与 C2/C3)
消除 Step0App 与 useStep1 重复实现的“采纳互斥”逻辑，由共享纯函数统一调度：

```javascript
export function computeAdoptResult({ candidateName, files, stage }) {
  const target = files[candidateName];
  if (!target) throw new Error(`[computeAdoptResult] 文件不存在: ${candidateName}`);
  
  const slotKey = target.slotKey || resolveSlotKey(candidateName, stage);
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  const canonicalFile = canonicalName ? files[canonicalName] : null;
  
  // 1. 规整版本标签（剥离 -Draft）
  const adoptedVersionTag = normalizeVersionTag(target.versionTag, slotKey);
  
  // 2. 首版留档保障 (解决 🟡D)：若当前生效的是规范骨干且首采纳新版本，留档 _第1版
  const newFiles = { ...files };
  if (canonicalFile && canonicalFile.isActive && canonicalName !== candidateName) {
    const ext = canonicalName.split('.').pop() || 'md';
    const archiveV1Name = `${slotItem.baseSlotName}_第1版.${ext}`;
    if (!newFiles[archiveV1Name]) {
      newFiles[archiveV1Name] = {
        ...canonicalFile,
        name: archiveV1Name,
        isActive: false,
        versionTag: `${slotItem.prefix}1`,
        isProtectedArchive: true, // 永久受保护不可删除
      };
    }
  }
  
  // 3. 同 slotKey 其他文件全部退级
  for (const fn of Object.keys(newFiles)) {
    if (newFiles[fn].slotKey === slotKey) {
      newFiles[fn] = { ...newFiles[fn], isActive: false };
    }
  }
  
  // 4. 候选草稿升格为客户生效底牌
  newFiles[candidateName] = {
    ...target,
    isActive: true,
    versionTag: adoptedVersionTag,
  };
  
  // 5. 单向镜像到规范主干 (自镜像短路守卫 · 解决 🟡8)
  if (canonicalFile && canonicalName !== candidateName) {
    newFiles[canonicalName] = {
      ...newFiles[canonicalName],
      content: target.content,
      versionTag: adoptedVersionTag,
      isActive: false, // 骨干作为镜像载体退级
      isCanonicalMirror: true,
    };
  }
  
  const nowIso = new Date().toISOString();
  return {
    files: newFiles,
    slotKey,
    canonicalName,
    adoptedDraftName: candidateName,
    versionTag: adoptedVersionTag,
    updatedAt: nowIso,
  };
}
```

### 3. 一键恢复的确定性生命周期与单槽单一 Active (彻底解决 🔴3)
从废纸篓点击【恢复】时的确定性状态收敛算法：
```javascript
export function computeRestoreResult({ filename, files, stage }) {
  const target = files[filename];
  if (!target) return files;
  
  const slotKey = target.slotKey || resolveSlotKey(filename, stage);
  const newFiles = { ...files };
  
  // 1. 移出废纸篓
  const restoredItem = {
    ...target,
    isDeleted: false,
    is_deleted: false,
  };
  
  // 2. 判定该槽位是否已有活跃生效版本
  const hasActive = Object.values(newFiles).some(
    (f) => f.slotKey === slotKey && f.isActive === true && f.name !== filename
  );
  
  if (!hasActive) {
    // 若当前槽位无任何 active（例如原 active 被误删后恢复），顺理成章恢复为生效底牌
    restoredItem.isActive = true;
  } else {
    // 严格保持 isActive: false，绝不抢占 active，绝对守住单槽单一 active 不变量！
    restoredItem.isActive = false;
  }
  
  newFiles[filename] = restoredItem;
  return newFiles;
}
```

### 4. 双重不可删除安全锁与死按钮根除 (彻底解决 C4 与 🟡7)
- **删除按钮在左栏树中的渲染判定 (`canDeleteFile`)**：
  ```javascript
  export function canDeleteFile(file, stage) {
    if (!file) return false;
    // ① 正在生效的底牌终身不可删
    if (file.isActive) return false;
    // ② 本阶段规范骨干文件即使退级也受系统终身保护，禁止删除
    const coreFiles = getCoreFilesByStage(stage);
    if (coreFiles.includes(file.name)) return false;
    // ③ 首版留档文件受保护不可删 (解决 🟡7)
    if (file.isProtectedArchive) return false;
    // ④ 已经在废纸篓中的不可重复点删除
    if (file.isDeleted || file.is_deleted) return false;
    return true;
  }
  ```
  在 `StudioFileTree.vue` 中仅当 `canDeleteFile(files[fn], props.stage)` 为 `true` 时才 hover 浮现垃圾桶图标，规范骨干与归档母版永远不出现垃圾桶，彻底杜绝死按钮！

---

## 三、中栏双行独立解耦架构 (`StudioEditor.vue`)

### 1. 顶栏双行解耦排布
彻底解决单行同时承载多 Tab 标签与快捷操作按钮导致的拥挤与遮挡：
1. **第一行（状态与操作工具栏）**：
   - **左侧状态区**：展示文件状态徽章（文字说明 + 主题色，无彩色 Emoji）、字数、生成时间（如 `生成时间: 2026-09-28 20:01:25`，缺失时统一展示 `生成时间: 未知`）；
   - **右侧操作区（偏右对齐）**：
     - 若为废纸篓文件：提供醒目的【一键恢复此文件】高亮按钮（触发 `@restore-file`，**严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色**）；直接隐藏【设为采纳】与【保存文件】；
     - 若为历史淘汰只读版本或规范主干镜像：展示【设为客户采纳】（镜像骨干除外，解决 🟡5）、【源码/预览】、【全屏】、【一键复制】，直接隐藏【保存文件】；
     - 若为候选工作草稿（未采纳）：展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】、【保存文件】；
     - 若为当前生效底牌：展示【客户生效底牌】、【源码/预览】、【全屏】、【一键复制】、【保存文件】。
2. **第二行（文件 Tab 标签栏）**：
   - 独立一行专门承载 `openTabs` 多文件切换与关闭；
   - 若该 Tab 属于废纸篓文件，在文件名后标注 `[废纸篓]` 浅色标识；
   - 点击 Tab 正常切换；点击 `×` 正常关闭。

### 2. 采纳守卫条件 (`canAdoptCurrentFile` · 解决 🟡2/🟡5)
```javascript
const canAdoptCurrentFile = computed(() => {
  if (!currentFile.value) return false;
  if (currentFile.value.isActive) return false;
  // 废纸篓文件禁止采纳 (双键兼容)
  if (currentFile.value.isDeleted || currentFile.value.is_deleted) return false;
  // 规范主干镜像禁止自身被点采纳 (解决 🟡5)
  const coreFiles = getCoreFilesByStage(props.stage);
  if (coreFiles.includes(currentFile.value.name)) return false;
  // 严格在当前阶段有效槽位内
  return props.validAdoptSlots.includes(currentFile.value.slotKey);
});
```

### 3. 组件 Props 显式声明 (彻底解决 🔴2)
```javascript
const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
  renderMode: { type: String, default: 'code' },
  /** 当前阶段标识：'step0' 或 'step1'，必传！ */
  stage: { type: String, required: true },
  /** 由父组件按阶段显式传入：Step0App 传入 getSlotsByStage('step0')，Step1App 传入 getSlotsByStage('step1') */
  validAdoptSlots: { type: Array, default: () => [] },
});
```

---

## 四、存量数据迁移与工作区持久化 (彻底解决 🔴4)

### 1. 存量 localStorage 数据迁移契约 (`migrateAndNormalizeFiles`)
用户升级后首次从本地存储恢复时，自动对存量文件执行数据规整，确保升级零故障：

```javascript
export function migrateAndNormalizeFiles(rawFiles = {}, stage) {
  const coreFiles = getCoreFilesByStage(stage);
  const normalized = {};
  const nowIso = new Date().toISOString();
  
  for (const fn of Object.keys(rawFiles)) {
    const item = { ...rawFiles[fn] };
    
    // 1. 统一为 camelCase isDeleted 并兼容旧键
    item.isDeleted = Boolean(item.isDeleted ?? item.is_deleted ?? false);
    delete item.is_deleted;
    
    // 2. 回填槽位 slotKey
    if (!item.slotKey) {
      item.slotKey = resolveSlotKey(fn, stage);
    }
    
    // 3. 规范骨干初始 active 判定与默认版本号
    if (coreFiles.includes(fn)) {
      if (item.isActive === undefined) {
        // 若当前槽位无任何 active 文件，赋予骨干 isActive: true
        const hasOtherActive = Object.values(rawFiles).some(
          (f) => f !== item && f.slotKey === item.slotKey && Boolean(f.isActive) === true
        );
        item.isActive = !hasOtherActive;
      }
      if (!item.versionTag) {
        const slotItem = CANONICAL_SLOT_DICT[item.slotKey];
        item.versionTag = slotItem?.prefix ? `${slotItem.prefix}1` : 'V1';
      }
    } else {
      if (item.isActive === undefined) item.isActive = false;
      if (!item.versionTag) item.versionTag = 'V1';
    }
    
    // 4. 时间戳归一化为 ISO
    if (!item.generatedAt) item.generatedAt = nowIso;
    
    normalized[fn] = item;
  }
  
  return normalized;
}
```

### 2. 纯前端工作区持久化体系
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
- **无效 openTabs 过滤**：页面反序列化时一律过滤剔除 `isDeleted: true` 或在 `files` 字典中不存在的无效 Tab。
