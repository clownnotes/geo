# Design: 多版本生成采纳与草稿废纸篓安全回档

> **目标定界**：本方案服务于 PC 浏览器桌面端交付工作台（纯 Web 单目标，运行于 NE1 8088 端口），非微信小程序或移动端，交互使用标准鼠标悬停（Hover）与浏览器本地持久化（`localStorage`）。
> **消费方全仓排查实据**：经全仓 grep 检索，`StudioEditor.vue` 与 `StudioFileTree.vue` 的真实消费方仅有 `Step0App.vue`（阶段零）与 `Step1App.vue`（阶段一）；`web/index.html` 中阶段二至六采用原生 JS 函数，完全不加载此 Vue 组件，架构改动天然具备零污染隔离性。

---

## 一、架构设计与单一真相源 (SSOT)

### 0. 数据模型核心不变式契约 (解决 🔴2)
为保证全仓判定逻辑健壮性，工作区所有文件对象必须遵守以下**硬约束不变式**：
1. **`name` 字段绝对等价性**：每一个进入 `files` 字典的文件对象，必须显式具备 `item.name` 属性，且其值必须与字典键名严格一致（`item.name === filename`）。存量迁移第一行必须保证 `item.name = fn`。
2. **单槽单一 Active 约束**：在任何有效工序槽位下，`isActive === true` 的未删除文件有且仅有 1 个。
3. **主干单向镜像约束**：规范骨干文件退级后打上 `isCanonicalMirror: true`，仅作为下游交付的稳定消费基线，其内容仅由生效底牌的采纳与保存单向镜像写入，不可直接覆盖。
4. **手建草稿隔离约束 (解决 🔴3)**：用户手动新建的文件必须标记 `isManual: true`，分配 `slotKey: 'slot_manual'`，独立于核心工序槽位，不参与版本递增扫描与淘汰只读判定。

### 1. 核心工序槽位与共享配置模块 (`GEO/web/step0-src/config/studioArtifactConfig.js`)
所有槽位字典、别名容错、阶段收窄器、版本正则、采纳与保存纯函数、双重锁及存量数据迁移算法统一定义于独立共享配置模块：

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
 * 别名与历史存量文件名容错映射字典 (解决 🔴3 & 🟡5)
 */
export const ALIAS_SLOT_MAP = {
  '01_网络底座指标_待对照.md': 'slot_metrics',
  '01_网络底座指标': 'slot_metrics',
  '01_豆包提问清单_推荐版.txt': 'slot_stage0_questions',
  '01_豆包提问清单': 'slot_stage0_questions',
  '01_豆包题目': 'slot_stage0_questions', // 阶段零历史生成新版本前缀容错 (解决 🟡2)
  '02_豆包实测回答记录_初测.txt': 'slot_stage0_answers',
  '02_豆包实测回答': 'slot_stage0_answers',
  '02_豆包回答': 'slot_stage0_answers', // 阶段零历史生成回答前缀容错 (解决 🟡2)
  '01_商业诊断与转化初稿.md': 'slot_draft',
  '01_商业诊断与转化初稿': 'slot_draft',
  '01_阶段零豆包实测问答素材.md': 'slot_stage0_qa',
  '01_阶段零豆包实测问答素材': 'slot_stage0_qa',
  '01_老板商业诊断报告_好看大屏.html': 'slot_report_screen',
  '01_老板商业诊断报告_好看大屏': 'slot_report_screen',
  '01_老板商业诊断报告_文字版.md': 'slot_report_text',
  '01_老板商业诊断报告_文字版': 'slot_report_text',
  '01_工程师底座技术审计.md': 'slot_report_tech',
  '01_工程师底座技术审计': 'slot_report_tech',
};

/**
 * 按阶段收窄有效采纳槽位白名单 (彻底解决跨阶段污染与白屏崩溃 · 解决 🔴5)
 * @param {'step0'|'step1'} stage
 * @returns {string[]}
 */
export function getSlotsByStage(stage) {
  if (!stage) {
    console.warn('[studioArtifactConfig] 缺少 stage 参数，安全降级为空集合！');
    return [];
  }
  return Object.keys(CANONICAL_SLOT_DICT).filter(
    (slotKey) => CANONICAL_SLOT_DICT[slotKey].stage === stage
  );
}

/**
 * 按阶段获取受系统终身保护的规范骨干文件名集合 (安全收窄 · 解决 🔴5)
 * @param {'step0'|'step1'} stage
 * @returns {string[]}
 */
export function getCoreFilesByStage(stage) {
  if (!stage) {
    console.warn('[studioArtifactConfig] 缺少 stage 参数，安全降级为空集合！');
    return [];
  }
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
  // 转义正则特殊字符 (解决 🟢1)
  const escaped = prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`^${escaped}(\\d+)`, 'i');
}

/**
 * 规整版本标签，剥离 -Draft 标记 (优先从文件名反推数值版本 · 解决 🟡4)
 * @param {string} tag
 * @param {string} slotKey
 * @param {string} [filename='']
 * @returns {string}
 */
export function normalizeVersionTag(tag, slotKey, filename = '') {
  const item = CANONICAL_SLOT_DICT[slotKey];
  const prefix = item?.prefix || 'V';
  if (!tag) {
    const m = (filename || '').match(/第(\d+)版/);
    if (m) return `${prefix}${m[1]}`;
    return `${prefix}1`;
  }
  return tag.replace(/-Draft$/i, '');
}

/**
 * 反向推导文件所属工序槽位 (带手建隔离与别名容错 · 彻底解决 🔴3 & 🟡5)
 * @param {string} filename
 * @param {'step0'|'step1'} stage
 * @param {boolean} [isManual=false]
 * @returns {string}
 */
const warnedSlotMisc = new Set();
export function resolveSlotKey(filename, stage, isManual = false) {
  if (!filename) return 'slot_misc';
  // 1. 手建文件短路隔离：不走前缀推导，防止笔记误判为工序槽位 (解决 🔴3)
  if (isManual) return 'slot_manual';
  
  const cleanName = filename.trim();
  const validSlots = getSlotsByStage(stage);
  
  // 2. 规范骨干精确命中
  for (const sk of validSlots) {
    if (CANONICAL_SLOT_DICT[sk]?.canonicalName === cleanName) return sk;
  }
  
  // 3. 别名容错表精确命中 (解决 🟡5)
  if (ALIAS_SLOT_MAP[cleanName]) {
    const mappedSlot = ALIAS_SLOT_MAP[cleanName];
    if (validSlots.includes(mappedSlot)) return mappedSlot;
  }
  
  // 4. 长前缀优先匹配 (按 baseSlotName 长度降序)
  const sortedSlots = [...validSlots].sort(
    (a, b) => (CANONICAL_SLOT_DICT[b]?.baseSlotName?.length || 0) - (CANONICAL_SLOT_DICT[a]?.baseSlotName?.length || 0)
  );
  for (const sk of sortedSlots) {
    if (cleanName.startsWith(CANONICAL_SLOT_DICT[sk].baseSlotName)) return sk;
  }
  
  // 5. 未匹配到工序槽位：去重安全告警并归为统一杂项草稿常量 (解决 🔴3, 🟡8 & 🟢1)
  if (!warnedSlotMisc.has(cleanName)) {
    warnedSlotMisc.add(cleanName);
    console.debug(`[studioArtifactConfig] 文件名未匹配到工序槽位字典: ${cleanName}，已安全归为 slot_misc 杂项草稿。`);
  }
  return 'slot_misc';
}

/**
 * 跨端安全的本地存储访问器 (环境探测 + 内存安全兜底 · 解决 🟢1)
 */
export function safeStorageGet(key, fallback = null) {
  try {
    if (typeof localStorage === 'undefined') return fallback;
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch (e) {
    console.warn(`[studioArtifactConfig] 读取本地存储失败: ${key}`, e);
    return fallback;
  }
}

export function safeStorageSet(key, value) {
  try {
    if (typeof localStorage === 'undefined') return false;
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    console.warn(`[studioArtifactConfig] 写入本地存储失败: ${key}`, e);
    return false;
  }
}
```

### 2. 版本号受控提取与防重名防覆盖算法
重新生成时，扫描工作区全量文件（包含 `isDeleted: true` 在废纸篓中的文件）：
```javascript
export function computeNextVersion(files = {}, slotKey) {
  const item = CANONICAL_SLOT_DICT[slotKey];
  if (!item) return { nextFileName: '', nextVersionTag: '', nextVer: 0 };
  
  // 排除手动新建草稿，防止手建笔记污染版本编号 (解决 🔴3)
  const slotFiles = Object.values(files).filter((f) => f.slotKey === slotKey && !f.isManual);
  const regex = buildSlotRegex(slotKey);
  
  const versions = [];
  for (const f of slotFiles) {
    const mName = (f.name || '').match(/第(\d+)版/);
    if (mName && mName[1]) versions.push(parseInt(mName[1], 10));
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

### 1. 正交的文件生命周期与只读判定表 (彻底解决 🔴1, 🔴3 与 🔴4)
通过持久化标记位 `isCanonicalMirror` 与 `isProtectedArchive` 消除状态漂移，确立清晰的正交判定准则：

| 文件类型 | `isActive` | 是否废纸篓 | 是否淘汰旧版 | 是否只读 (`isReadOnly`) | 顶栏徽章显示 (文字+主题色) | 保存文件按钮 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **客户生效底牌** (当前活跃版) | `true` | `false` | `false` | **可编辑 (`false`)** | [徽章: 客户生效底牌 `Vn`（阶段零对齐 AGENTS §3.5 显示为 `生效版本 QA-Vn`，严禁自造底牌报告）] | 展示（保存自身；若具备非空内容联动镜像主干） |
| **最新候选工作草稿** (如重抓第2版) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 候选工作草稿 `V2-Draft`] | 展示（点击保存本地草稿，不触发镜像） |
| **手动新建文件** (`newFile` / `isManual`) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 自定义工作草稿] | 展示（点击保存本地草稿，不可采纳，永不只读） |
| **规范主干(自动镜像)** (已采纳新版后) | `false` | `false` | - | **只读 (`true` · 自动镜像)** | [徽章: 规范主干 · 自动镜像] | **隐藏** (仅程序自动单向镜像写入) |
| **首版母版留档** (`_第1版`) | `false` | `false` | `true` | **终身只读 (`true`)** | [徽章: 历史母版 · 终身留档] | **隐藏** (受保护母版不可删不可改) |
| **已淘汰历史版本** (同槽存在更新生效版) | `false` | `false` | `true` | **强制只读 (`true`)** | [徽章: 历史版本 · 只读归档] | **隐藏** (拦截 Cmd+S，防错版覆盖) |
| **废纸篓归档文件** | `false` | `true` | - | **强制只读 (`true`)** | [徽章: 废纸篓归档 · 只读状态] | **隐藏** (提示一键恢复) |

- **历史淘汰旧版判定 (`isHistoricalRetired` · 持久化标记优先 + 存量版本比对兜底 · 彻底解决 🔴1 & 🟡6)**：
  ```javascript
  export function isHistoricalRetired(file, files = {}) {
    if (!file || !file.slotKey || file.isActive || file.isManual || file.slotKey === 'slot_manual') return false;
    // 1. 优先依据采纳动作退级时显式持久化的 isRetired 标记 (彻底解决 🔴1)
    // 关键点：新抓取生成的候选草稿（如第2版）绝不带 isRetired，因此恒返回 false，完全自由编辑打磨！
    if (file.isRetired === true) return true;
    
    // 2. 存量老数据未持久化标记时的兜底推导 (解决 🟡6)：仅当同槽活跃版本的序号明确高于自身时才算淘汰
    const activeBrother = Object.values(files).find(
      (f) => f.slotKey === file.slotKey && f.isActive === true && f.name !== file.name && !f.isManual
    );
    if (activeBrother) {
      const mSelf = (file.name || '').match(/第(\d+)版/);
      const mActive = (activeBrother.name || '').match(/第(\d+)版/);
      if (mSelf && mActive && parseInt(mSelf[1], 10) < parseInt(mActive[1], 10)) {
        return true;
      }
    }
    return false;
  }
  ```

- **只读判定函数 (`isReadOnlyFile` · 解决 🔴1, 🔴3 与 🔴4)**：
  ```javascript
  export function isReadOnlyFile(file, files, stage) {
    if (!file) return false;
    // 1. 废纸篓必定只读
    if (Boolean(file.isDeleted || file.is_deleted)) return true;
    
    // 2. 首版母版留档文件：终身强制只读 (不受后继草稿删入废纸篓影响)
    if (file.isProtectedArchive) return true;
    
    // 3. 规范主干镜像载体：若带有 isCanonicalMirror 标记，终身保持强制只读 (消除漂移 · 解决 🔴4)
    if (file.isCanonicalMirror) return true;
    
    // 4. 手建自定义文件：只要不在废纸篓，永远保持自由编辑打磨 (解决 🔴3)
    if (file.isManual || file.slotKey === 'slot_manual') return false;
    
    // 5. 属于某槽位的更旧被淘汰历史版本 (具备 isRetired: true)：强制只读 (但支持回滚采纳 · 解决 🟡7)
    if (!file.isActive && isHistoricalRetired(file, files)) {
      return true;
    }
    
    // 6. 当前生效底牌、最新候选工作草稿 (未采纳)、新建文件：完全可编辑打磨保存！
    return false;
  }
  ```

### 2. 统一保存与单向主干镜像纯函数 (`computeSaveResult` · 彻底解决 🔴1 内容守卫 & 🟡4 只读守卫)
用户在编辑器点击【保存文件】或按 Cmd+S 时，由纯函数统一计算新状态与主干镜像：

```javascript
export function computeSaveResult({ targetName, newContent, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[targetName];
  if (!target) return { files, mirrored: false, success: false, reason: 'FILE_NOT_FOUND' };
  
  // 纯函数内部自证只读不变量 (防线不外置 · 解决 🟡4)
  if (isReadOnlyFile(target, files, stage)) {
    console.warn(`[computeSaveResult] 目标文件处于只读锁定状态 [${targetName}]，拒绝保存！`);
    return { files, mirrored: false, success: false, reason: 'READ_ONLY_LOCKED' };
  }
  
  const newFiles = { ...files };
  const safeContent = newContent ?? '';
  
  // 1. 保存目标文件自身内容
  newFiles[targetName] = {
    ...target,
    name: targetName,
    content: safeContent,
    savedContent: safeContent,
    isDirty: false,
    updatedAt: nowIso,
  };
  
  // 2. 活跃文件自动单向镜像契约 (带非空内容守卫 · 彻底解决 🔴1)
  let mirrored = false;
  const slotKey = target.slotKey || resolveSlotKey(targetName, stage, target.isManual);
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  
  // 内容守卫：只有当保存内容为有效非空字符串时才覆盖镜像骨干，坚决杜绝空内容洗白主干！
  const hasValidContent = typeof safeContent === 'string' && safeContent.trim().length > 0;
  
  if (target.isActive && canonicalName && canonicalName !== targetName && newFiles[canonicalName]) {
    if (hasValidContent) {
      newFiles[canonicalName] = {
        ...newFiles[canonicalName],
        name: canonicalName,
        content: safeContent,
        versionTag: target.versionTag,
        isCanonicalMirror: true,
        updatedAt: nowIso,
      };
      mirrored = true;
    } else {
      console.warn(`[studioArtifactConfig] 尝试用空内容保存镜像规范骨干 [${canonicalName}]，已被安全拦截！保留骨干原有内容。`);
    }
  }
  
  return {
    files: newFiles,
    mirrored,
    canonicalName,
    updatedAt: nowIso,
    success: true, // 统一返回契约 · 解决 🟡5
  };
}
```

### 3. 统一采纳互斥纯函数 (`computeAdoptResult` · 解决 🔴1, 🔴4, 🟡4, 🟡5, 🟡6, 🟡7, 🟢1)
消除 Step0App 与 useStep1 重复实现的“采纳互斥”逻辑，由共享纯函数统一调度：

```javascript
export function computeAdoptResult({ candidateName, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[candidateName];
  // 安全降级返回，杜绝抛错白屏崩溃工作台 (解决 🟡6)
  if (!target) {
    console.warn(`[computeAdoptResult] 候选采纳文件不存在: ${candidateName}`);
    return { files, success: false, reason: 'FILE_NOT_FOUND' };
  }
  
  const slotKey = target.slotKey || resolveSlotKey(candidateName, stage, target.isManual);
  
  // 1. 候选自身类型自证守卫：受限类型绝不可作为采纳候选，防自锁矛盾态 (彻底解决 🔴1)
  if (
    target.isCanonicalMirror ||
    target.isProtectedArchive ||
    target.isManual ||
    slotKey === 'slot_manual' ||
    slotKey === 'slot_misc'
  ) {
    console.warn(`[computeAdoptResult] 目标文件 [${candidateName}] 属于受限类型（规范镜像/归档母版/手建草稿/杂项草稿），禁止作为采纳候选！`);
    return { files, success: false, reason: 'NOT_ADOPTABLE_TARGET' };
  }
  
  // 2. 阶段合法性 Fail-Closed 关闸守卫 (彻底解决 🟡5)
  const validSlots = getSlotsByStage(stage);
  if (!stage || validSlots.length === 0 || !validSlots.includes(slotKey)) {
    console.warn(`[computeAdoptResult] 目标槽位 [${slotKey}] 在当前阶段 [${stage}] 下无效或未指定阶段，Fail-Closed 拒绝采纳！`);
    return { files, success: false, reason: 'STAGE_SLOT_MISMATCH' };
  }
  
  // 3. 内容有效性守卫：严禁采纳空内容文件，防止单向镜像击穿清空规范主干 (彻底解决 🔴1)
  const candidateValid = typeof target.content === 'string' && target.content.trim().length > 0;
  if (!candidateValid) {
    console.warn(`[computeAdoptResult] 候选版本 [${candidateName}] 内容为空或未就绪，拒绝采纳以保护规范主干！`);
    return { files, success: false, reason: 'EMPTY_CONTENT' };
  }
  
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  const canonicalFile = canonicalName ? files[canonicalName] : null;
  
  // 4. 规整版本标签（剥离 -Draft · 解决 🟡4）
  const adoptedVersionTag = normalizeVersionTag(target.versionTag, slotKey, candidateName);
  
  // 5. 首版留档保障：若当前生效的是规范骨干且首采纳新版本，留档 _第1版 (解决 🟡5)
  const newFiles = { ...files };
  if (canonicalFile && canonicalFile.isActive && canonicalName !== candidateName) {
    const ext = canonicalName.split('.').pop() || 'md';
    const archiveV1Name = `${slotItem.baseSlotName}_第1版.${ext}`;
    if (!newFiles[archiveV1Name]) {
      newFiles[archiveV1Name] = {
        ...canonicalFile,
        name: archiveV1Name,
        isActive: false,
        isRetired: true,
        isCanonicalMirror: false, // 显式清除镜像标记，母版与镜像互斥！(解决 🟡5)
        versionTag: `${slotItem.prefix}1`,
        isProtectedArchive: true, // 永久受保护不可删除、不可修改
      };
    }
  }
  
  // 6. 同 slotKey 其他文件全部退级并显式打上 isRetired 标记 (手建文件除外 · 带 resolveSlotKey 兜底 · 彻底解决 🔴3)
  for (const fn of Object.keys(newFiles)) {
    const sibSlot = newFiles[fn].slotKey || resolveSlotKey(fn, stage, newFiles[fn].isManual);
    if (sibSlot === slotKey && !newFiles[fn].isManual && fn !== candidateName) {
      newFiles[fn] = {
        ...newFiles[fn],
        isActive: false,
        isRetired: true, // 关键：被采纳动作淘汰的历史版本，显式打上持久化标记！
      };
    }
  }
  
  // 7. 候选草稿（或回滚的历史版本）升格为客户生效底牌 (解决 🟡7 支持回滚)
  newFiles[candidateName] = {
    ...target,
    name: candidateName,
    isActive: true,
    isRetired: false, // 恢复生效，解除淘汰
    versionTag: adoptedVersionTag,
    updatedAt: nowIso,
  };
  
  // 8. 单向镜像到规范主干 (受前面 candidateValid 守卫保护，且复位 isRetired · 解决 🟢1)
  if (canonicalFile && canonicalName !== candidateName) {
    newFiles[canonicalName] = {
      ...newFiles[canonicalName],
      name: canonicalName,
      content: target.content,
      versionTag: adoptedVersionTag,
      isActive: false,
      isRetired: false, // 镜像骨干复位淘汰标记，保持干净
      isCanonicalMirror: true,
      updatedAt: nowIso,
    };
  }

  // 9. 自证单槽单一 active 不变量：若发现多 active 脏数据则 Fail-Closed (彻底解决 🔴3)
  const activeCount = Object.values(newFiles).filter(
    (f) => (f.slotKey || resolveSlotKey(f.name, stage, f.isManual)) === slotKey && f.isActive === true && !f.isManual
  ).length;
  if (activeCount !== 1) {
    console.error(`[computeAdoptResult] 槽位 [${slotKey}] 采纳后活跃文件数自证失败(期望 1，实际 ${activeCount})，Fail-Closed 拒绝！`);
    return { files, success: false, reason: 'CONVERGENCE_VERIFICATION_FAILED' };
  }
  
  return {
    success: true, // 统一返回契约 · 解决 🟡5
    files: newFiles,
    slotKey,
    canonicalName,
    adoptedDraftName: candidateName,
    versionTag: adoptedVersionTag,
    updatedAt: nowIso,
  };
}
```

### 4. 一键恢复的确定性生命周期与单槽单一 Active (解决 🔴2, 🔴3 与 🟢3/🟢5)
从废纸篓点击【恢复】时的确定性状态收敛算法：
```javascript
export function computeRestoreResult({ filename, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[filename];
  if (!target) return { success: false, reason: 'FILE_NOT_FOUND', files };
  
  const slotKey = target.slotKey || resolveSlotKey(filename, stage, target.isManual);
  const newFiles = { ...files };
  
  // 1. 移出废纸篓 (统一只写 isDeleted，确保 name 字段存在 · 解决 🔴2 & 🟡2)
  const restoredItem = {
    ...target,
    name: filename,
    isDeleted: false,
    updatedAt: nowIso,
  };
  delete restoredItem.is_deleted;
  
  // 2. 受限文件恢复后强制保持草稿，绝不抢占工序活跃槽位 (彻底解决 🔴4 & 🟢3)
  // 手建草稿、杂项草稿、首版留档母版、以及规范镜像载体，恢复后绝对强制保持 isActive: false！
  if (
    target.isManual ||
    target.isProtectedArchive ||
    target.isCanonicalMirror ||
    slotKey === 'slot_manual' ||
    slotKey === 'slot_misc'
  ) {
    restoredItem.isActive = false;
    newFiles[filename] = restoredItem;
    return { success: true, files: newFiles, restoredName: filename, updatedAt: nowIso };
  }
  
  // 3. 判定该槽位是否已有活跃生效版本
  const hasActive = Object.values(newFiles).some(
    (f) => f.slotKey === slotKey && f.isActive === true && f.name !== filename && !f.isManual
  );
  
  if (!hasActive) {
    // 升格为 active 时必须同步复位 isRetired，彻底杜绝 active + retired 矛盾态！(彻底解决 🔴2)
    restoredItem.isActive = true;
    restoredItem.isRetired = false;
  } else {
    // 严格保持 isActive: false，绝不抢占 active，绝对守住单槽单一 active 不变量！
    restoredItem.isActive = false;
  }
  
  newFiles[filename] = restoredItem;
  return { success: true, files: newFiles, restoredName: filename, updatedAt: nowIso };
}
```

### 5. 双重不可删除安全锁与死按钮根除 (解决 🔴3 与 🟡2/🟡3/🟡7)
- **删除按钮在左栏树中的渲染判定 (`canDeleteFile`)**：
  ```javascript
  export function canDeleteFile(file, stage) {
    if (!file) return false;
    // ① 正在生效的底牌终身不可删
    if (file.isActive) return false;
    // ② 规范主干镜像载体终身不可删 (不论 stage 是否传入，Fail-Closed 关闸保护 · 彻底解决 🟡3)
    if (file.isCanonicalMirror) return false;
    // ③ 首版留档母版受系统终身保护不可删 (不论 stage 是否传入 · 彻底解决 🟡3)
    if (file.isProtectedArchive) return false;
    // ④ 全局所有工序槽位的规范骨干文件名一律终身不可删 (不依赖外部 stage，彻底关闸 · 彻底解决 🟡2)
    const allCanonicalNames = Object.values(CANONICAL_SLOT_DICT).map((item) => item.canonicalName);
    if (allCanonicalNames.includes(file.name)) return false;
    // ⑤ 手建草稿与杂项草稿只要不在废纸篓且非 active 即可删除 (解决 🔴3)
    if (file.isManual || file.slotKey === 'slot_manual' || file.slotKey === 'slot_misc') {
      return !Boolean(file.isDeleted || file.is_deleted);
    }
    // ⑥ 已经在废纸篓中的不可重复点删除
    if (Boolean(file.isDeleted || file.is_deleted)) return false;
    return true;
  }
  ```
  在 `StudioFileTree.vue` 中仅当 `canDeleteFile(files[fn], props.stage)` 为 `true` 时才 hover 浮现垃圾桶图标，规范骨干与归档母版永远不出现垃圾桶，彻底杜绝死按钮！

- **统一软删除纯函数 (`computeDeleteResult` · 彻底闭环 🟡1 消除胶水层重复面条代码)**：
  ```javascript
  export function computeDeleteResult({
    filename,
    files,
    stage,
    currentSelected = '',
    openTabs = [],
    nowIso = new Date().toISOString(),
  }) {
    const target = files[filename];
    if (!target) return { success: false, reason: 'FILE_NOT_FOUND', files };
    
    // 1. 前置守卫：复用 canDeleteFile 进行 Fail-Closed 关闸保护
    if (!canDeleteFile(target, stage)) {
      console.warn(`[computeDeleteResult] 文件 [${filename}] 受系统安全保护，禁止删除！`);
      return { success: false, reason: 'FILE_PROTECTED_CANNOT_DELETE', files };
    }
    
    const slotKey = target.slotKey || resolveSlotKey(filename, stage, target.isManual);
    const newFiles = { ...files };
    
    // 2. 标记软删除 (统一只写 isDeleted，强制失活 isActive，彻底清理 is_deleted)
    newFiles[filename] = {
      ...target,
      name: filename,
      isDeleted: true,
      isActive: false,
      updatedAt: nowIso,
    };
    delete newFiles[filename].is_deleted;
    
    // 3. 规整 openTabs：将已删除文件从标签栏移除
    const newOpenTabs = openTabs.filter((fn) => fn !== filename);
    
    // 4. 平滑计算回退选中项：优先同槽剩余未删有效文件 -> openTabs 首项 -> 全局未删除首项 -> 空
    let nextSelected = currentSelected;
    if (currentSelected === filename) {
      const slotRemaining = Object.values(newFiles).filter(
        (f) => (f.slotKey || resolveSlotKey(f.name, stage, f.isManual)) === slotKey && !f.isDeleted
      );
      if (slotRemaining.length > 0) {
        const activeItem = slotRemaining.find((f) => f.isActive);
        nextSelected = activeItem ? activeItem.name : slotRemaining[0].name;
      } else if (newOpenTabs.length > 0) {
        nextSelected = newOpenTabs[0];
      } else {
        const globalRemaining = Object.values(newFiles).filter((f) => !f.isDeleted);
        nextSelected = globalRemaining.length > 0 ? globalRemaining[0].name : '';
      }
    }
    
    return {
      success: true,
      files: newFiles,
      deletedName: filename,
      nextSelected,
      newOpenTabs,
      updatedAt: nowIso,
    };
  }
  ```

---

## 三、中栏双行独立解耦架构与事件契约 (`StudioEditor.vue`)

### 1. 顶栏双行解耦排布
彻底解决单行同时承载多 Tab 标签与快捷操作按钮导致的拥挤与遮挡：
1. **第一行（状态与操作工具栏）**：
   - **左侧状态区**：展示文件状态徽章（文字说明 + 主题色，无彩色 Emoji）、字数、生成时间（如 `生成时间: 2026-09-28 20:01:25`，缺失时统一展示 `生成时间: 未知`）；
   - **右侧操作区（偏右对齐）**：
     - 若为废纸篓文件：提供醒目的【一键恢复此文件】高亮按钮（触发 `@restoreFile`，**严格遵循 AGENTS §3.3 视觉红线，采用系统主色紫 `var(--geo-primary, #7c5bf5)`，严禁使用红色**）；直接隐藏【设为采纳】与【保存文件】；
     - 若为历史淘汰只读版本、首版母版留档或规范主干镜像：展示【设为客户采纳】（主干镜像与母版除外）、【源码/预览】、【全屏】、【一键复制】，直接隐藏【保存文件】；
     - 若为候选工作草稿（未采纳）：展示【设为客户采纳】、【源码/预览】、【全屏】、【一键复制】、【保存文件】；
     - 若为当前生效文件：展示状态徽章（阶段零严格遵循 AGENTS §3.5 显示为【生效版本 `QA-Vn`】，阶段一及其他阶段显示为【客户生效底牌 `Vn`】，彻底杜绝自造『底牌报告』混用 · 解决 🟡7）、【源码/预览】、【全屏】、【一键复制】、【保存文件】。
2. **第二行（文件 Tab 标签栏）**：
   - 独立一行专门承载 `openTabs` 多文件切换与关闭；
   - 若该 Tab 属于废纸篓文件，在文件名后标注 `[废纸篓]` 浅色标识，允许用户在中栏进行只读查验预览（解决 🟡8）；
   - 点击 Tab 正常切换；点击 `×` 正常关闭。

### 2. 组件事件契约表 (锁定规范杜绝歧义 · 解决 🟡11)
为避免事件命名不一致导致“点击无反应”的伪死按钮回归，锁定组件与父级之间的标准事件契约：

| 组件名 | 事件名称 | 派发载荷 (Payload) | 业务行为说明 |
| :--- | :--- | :--- | :--- |
| `StudioFileTree.vue` | `@openFile` | `filename: string` | 切换中栏选中文件（支持工作区正常文件与废纸篓预览） |
| `StudioFileTree.vue` | `@deleteFile` | `filename: string` | 将未采纳候选草稿或手建草稿移入废纸篓 (`isDeleted: true`) |
| `StudioFileTree.vue` | `@restoreFile` | `filename: string` | 从废纸篓抽屉一键恢复文件至主列表并保证单槽单一 active |
| `StudioEditor.vue` | `@adoptFile` | `filename: string` | 将候选草稿升格为客户生效底牌，触发单向镜像与首版留档 |
| `StudioEditor.vue` | `@saveFile` | `{ filename: string, content: string }` | 保存文件正文修改（生效底牌联动镜像规范主干） |
| `StudioEditor.vue` | `@restoreFile` | `filename: string` | 中栏查验废纸篓文件时点击右侧紫色按钮触发恢复 |

### 3. 采纳守卫条件 (`canAdoptCurrentFile` · 解决 🔴3/🟡2/🟡5)
```javascript
const canAdoptCurrentFile = computed(() => {
  if (!currentFile.value) return false;
  if (currentFile.value.isActive) return false;
  // 手建文件与杂项文件不开放采纳为核心底牌 (解决 🔴3)
  if (currentFile.value.isManual || currentFile.value.slotKey === 'slot_manual') return false;
  // 废纸篓文件禁止采纳
  if (currentFile.value.isDeleted || currentFile.value.is_deleted) return false;
  // 首版母版留档禁止被点采纳
  if (currentFile.value.isProtectedArchive) return false;
  // 规范主干镜像禁止自身被点采纳
  const coreFiles = getCoreFilesByStage(props.stage);
  if (coreFiles.includes(currentFile.value.name)) return false;
  // 必须严格在当前阶段有效核心槽位内
  return props.validAdoptSlots.includes(currentFile.value.slotKey);
});
```

### 4. 组件 Props 显式声明与非致命安全兜底 (解决 🔴5 与 🟡7)
```javascript
const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
  renderMode: { type: String, default: 'code' },
  /** 当前阶段标识：'step0' 或 'step1'，默认空串，未传时安全降级不崩溃 */
  stage: { type: String, default: '' },
  /** 由父组件按阶段显式传入：Step0App 传入 getSlotsByStage('step0')，Step1App 传入 getSlotsByStage('step1') */
  validAdoptSlots: { type: Array, default: () => [] },
});
```
当 `!props.stage` 时，组件输出 `console.warn('[StudioEditor] 缺少 stage 属性，安全降级为空槽位保护模式')`，确保在任何测试或边界环境下绝不抛错白屏。

---

## 四、存量数据迁移与工作区持久化 (彻底解决 🔴2 与 🔴4)

### 1. 存量 localStorage 数据迁移与单槽 Active 强制收敛 (`migrateAndNormalizeFiles`)
用户升级后首次从本地存储恢复时，自动对存量文件执行数据规整与槽位 Active 强制收敛：

```javascript
export function migrateAndNormalizeFiles(rawFiles = {}, stage, nowIso = new Date().toISOString()) {
  // 阶段缺失守卫：Fail-Closed 保护，原样返回存量数据，禁止破坏性回填 slot_misc！(彻底解决 🔴2)
  if (!stage) {
    console.warn('[migrateAndNormalizeFiles] 缺少 stage 阶段标识，Fail-Closed 安全关闸，原样返回存量数据！');
    return rawFiles;
  }

  const validSlots = getSlotsByStage(stage);
  const normalized = {};
  
  // 第一轮：硬约束不变式回填与 slotKey 规整 (彻底解决 🔴2)
  for (const fn of Object.keys(rawFiles)) {
    const item = { ...rawFiles[fn] };
    
    // 【硬约束不变式】显式保证 item.name 等价于字典键名 (解决 🔴2)
    item.name = fn;
    
    // 1. 统一为 camelCase isDeleted 并显式解析字符串布尔 (解决 🟢3)
    const rawDel = item.isDeleted ?? item.is_deleted;
    item.isDeleted = rawDel === true || rawDel === 'true';
    delete item.is_deleted;
    
    // 废纸篓中的文件绝对不可处于 active 状态 (解决 🟢2)
    if (item.isDeleted) {
      item.isActive = false;
    }
    
    // 2. 回填槽位 slotKey (手建草稿保留 slot_manual，对存量未匹配或误标为 slot_misc 且非手建的允许重新解析 · 解决 🔴2)
    if (!item.slotKey || (item.slotKey === 'slot_misc' && !item.isManual)) {
      item.slotKey = resolveSlotKey(fn, stage, item.isManual);
    }
    
    // 3. 识别并回填首版母版留档标记 (解决 🟡1)
    if (fn.includes('_第1版')) {
      item.isProtectedArchive = true;
    }

    // 纠偏存量脏数据：母版与规范镜像终身受保护，绝不可处于已删除状态 (解决 🔴4)
    if (item.isProtectedArchive || item.isCanonicalMirror) {
      item.isDeleted = false;
    }
    
    // 4. 初始 versionTag (优先从文件名反推版本号 · 解决 🟡6)
    if (!item.versionTag) {
      const slotItem = CANONICAL_SLOT_DICT[item.slotKey];
      const prefix = slotItem?.prefix || 'V';
      const mVer = fn.match(/第(\d+)版/);
      item.versionTag = mVer ? `${prefix}${mVer[1]}` : `${prefix}1`;
    }
    
    // 5. 时间戳归一化为 ISO (解决 🟡3)
    if (!item.generatedAt) {
      item.generatedAt = nowIso;
    } else {
      // 存量时间戳格式清洗与合法性校验
      const parsed = Date.parse(item.generatedAt);
      item.generatedAt = !isNaN(parsed) ? new Date(parsed).toISOString() : nowIso;
    }
    
    normalized[fn] = item;
  }
  
  // 辅助提取版本数值 (解决 🟡2)
  const getVerNum = (f) => {
    const m = (f.name || '').match(/第(\d+)版/);
    if (m) return parseInt(m[1], 10);
    const m2 = (f.versionTag || '').match(/\d+/);
    if (m2) return parseInt(m2[0], 10);
    return 1;
  };
  
  // 第二轮：工序槽位 Active 强制收敛与存量 isRetired 回填 (解决 🔴1, 🔴2, 🟡1, 🟡2, 🟡6)
  for (const sk of validSlots) {
    // 过滤出该槽位下所有未删除且非手建的正式交付物
    const slotFiles = Object.values(normalized).filter(
      (f) => f.slotKey === sk && !f.isDeleted && !f.isManual
    );
    // 预过滤掉镜像与母版，防止错误将镜像固化为 active (解决 🟡6)
    const activeList = slotFiles.filter((f) => f.isActive === true && !f.isCanonicalMirror && !f.isProtectedArchive);
    const canonicalName = CANONICAL_SLOT_DICT[sk]?.canonicalName;
    
    let chosen = null;
    if (activeList.length > 1) {
      // 存在多个 active 脏数据：按【规范骨干 > 最高版本 > 其余】显式排序选取唯一 active (解决 🟡2)
      activeList.sort((a, b) => {
        const isA = a.name === canonicalName;
        const isB = b.name === canonicalName;
        if (isA && !isB) return -1;
        if (!isA && isB) return 1;
        return getVerNum(b) - getVerNum(a);
      });
      chosen = activeList[0];
      for (const f of activeList) {
        if (f.name !== chosen.name) f.isActive = false;
      }
    } else if (activeList.length === 1) {
      chosen = activeList[0];
    } else if (activeList.length === 0 && slotFiles.length > 0) {
      // 槽位无任何 active：激活规范骨干（若无骨干则激活首个非镜像、非母版的候选草稿 · 解决 🟢2）
      const candidateList = slotFiles.filter((f) => !f.isCanonicalMirror && !f.isProtectedArchive);
      chosen = slotFiles.find((f) => f.name === canonicalName) || candidateList[0] || slotFiles[0];
      chosen.isActive = true;
    }
    
    // 为老数据同槽已被淘汰的历史旧版补充 isRetired: true (彻底解决 🔴1 误伤)
    if (chosen) {
      for (const f of slotFiles) {
        // 显式豁免镜像与母版，不打淘汰标记 (彻底解决 🔴1)
        if (f.isCanonicalMirror || f.isProtectedArchive) {
          f.isRetired = false;
          continue;
        }
        if (f.name !== chosen.name && !f.isActive) {
          // 仅当版本严格低于当前活跃版本时才回填 isRetired，绝不误伤最新未采纳草稿！
          if (getVerNum(f) < getVerNum(chosen)) {
            f.isRetired = true;
          }
        }
      }
    }
  }

  // 收敛后终检：确保任何镜像文件绝不持有 isRetired 或 isActive (彻底解决 🔴1)
  for (const fn of Object.keys(normalized)) {
    if (normalized[fn].isCanonicalMirror) {
      normalized[fn].isRetired = false;
      normalized[fn].isActive = false;
    }
  }
  
  return normalized;
}
```

### 2. 纯前端工作区持久化体系
- **安全本地存储读写工具**：封装 `safeStorageGet / safeStorageSet`，自带 `typeof localStorage !== 'undefined'` 守卫；
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
- **openTabs 视图与过滤策略 (解决 🟡8)**：
  - 废纸篓条目在中栏点击查验时，允许临时放入 `openTabs`，Tab 标注浅色 `[废纸篓]` 标识，便于专家快速比对后决定是否恢复；
  - 仅在工作区全量初始化反序列化时，过滤清理掉已彻底丢失、不存在于 `files` 字典中的脏 Tab。

