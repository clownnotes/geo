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
  
  // 3. 别名容错表匹配 (精确命中 或 剥离版本后缀后命中 或 别名前缀匹配 · 解决 🟡5)
  if (ALIAS_SLOT_MAP[cleanName]) {
    const mappedSlot = ALIAS_SLOT_MAP[cleanName];
    if (validSlots.includes(mappedSlot)) return mappedSlot;
  }
  const cleanBase = cleanName.replace(/_第\d+版.*$/, '').replace(/\.[^.]+$/, '');
  if (ALIAS_SLOT_MAP[cleanBase]) {
    const mappedSlot = ALIAS_SLOT_MAP[cleanBase];
    if (validSlots.includes(mappedSlot)) return mappedSlot;
  }
  const sortedAliases = Object.keys(ALIAS_SLOT_MAP).sort((a, b) => b.length - a.length);
  for (const aliasKey of sortedAliases) {
    if (cleanName.startsWith(aliasKey)) {
      const mappedSlot = ALIAS_SLOT_MAP[aliasKey];
      if (validSlots.includes(mappedSlot)) return mappedSlot;
    }
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
| **客户生效底牌** (当前活跃版，含母版回滚) | `true` | `false` | `false` | **可编辑 (`false` · 享有最高可编辑权)** | [徽章: 客户生效底牌 `Vn`（阶段零对齐 AGENTS §3.5 显示为 `生效版本 QA-Vn`，严禁自造底牌报告）] | 展示（保存自身；若具备非空内容联动镜像主干） |
| **最新候选工作草稿** (如重抓第2版) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 候选工作草稿 `V2-Draft`] | 展示（点击保存本地草稿，不触发镜像） |
| **灵感分支草稿** (如 V1.1 / S1.1) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 灵感分支草稿 `V1.1-Draft`] | 展示（可自由打磨或合回主干） |
| **手动新建文件** (`newFile` / `isManual`) | `false` | `false` | `false` | **可编辑 (`false`)** | [徽章: 自定义工作草稿] | 展示（点击保存本地草稿，不可采纳，永不只读） |
| **规范主干(自动镜像)** (已采纳新版后) | `false` | `false` | - | **只读 (`true` · 自动镜像)** | [徽章: 规范主干 · 自动镜像] | **隐藏** (仅程序自动单向镜像写入) |
| **首版母版留档** (`_第1版` 未激活时) | `false` | `false` | `true` | **未激活时只读 (`true`)；采纳后可编辑** | [徽章: 第 1 版 (原始母版)] | **未激活隐藏；采纳后展示** |
| **已淘汰历史版本** (同槽存在更新生效版) | `false` | `false` | `true` | **强制只读 (`true`)** | [徽章: 历史版本 · 只读归档] | **隐藏** (拦截 Cmd+S，防错版覆盖) |
| **废纸篓归档文件** | `false` | `true` | - | **强制只读 (`true`)** | [徽章: 废纸篓归档 · 只读状态] | **隐藏** (提示一键恢复) |

- **历史淘汰旧版判定 (`isHistoricalRetired` · 持久化标记优先 + 存量版本比对兜底 · 彻底解决 🔴1 & 🟡6)**：
  ```javascript
  export function isHistoricalRetired(file, files = {}) {
    if (!file || !file.slotKey || file.isActive || file.isManual || file.slotKey === 'slot_manual') return false;
    // 灵感分支草稿（如 V1.1, S1.1）可自由打磨，绝不误判为历史淘汰
    if (file.isBranchDraft) return false;
    // 1. 优先依据采纳动作退级时显式持久化的 isRetired 标记 (彻底解决 🔴1)
    if (file.isRetired === true) return true;
    
    // 2. 存量老数据未持久化标记时的兜底推导 (解决 🟡6)：仅当同槽活跃版本的序号明确高于自身时才算淘汰
    const activeBrother = Object.values(files).find(
      (f) => f.slotKey === file.slotKey && f.isActive === true && f.name !== file.name && !f.isManual
    );
    if (activeBrother) {
      const mSelf = (file.name || '').match(/第(\d+(?:\.\d+)?)版/);
      const mActive = (activeBrother.name || '').match(/第(\d+(?:\.\d+)?)版/);
      if (mSelf && mActive && parseFloat(mSelf[1]) < parseFloat(mActive[1])) {
        return true;
      }
    }
    return false;
  }
  ```

- **只读判定函数 (`isReadOnlyFile` · 解决 🔴1, 🔴3, 🔴4)**：
  ```javascript
  export function isReadOnlyFile(file, files, stage) {
    if (!file) return false;
    // 1. 废纸篓必定只读
    if (Boolean(file.isDeleted || file.is_deleted)) return true;
    
    // 2. 规范主干镜像载体或非活跃状态的规范骨干：终身保持强制只读 (防骨干内容分叉)
    if (file.isCanonicalMirror) return true;
    const canonicalName = CANONICAL_SLOT_DICT[file.slotKey]?.canonicalName;
    if (canonicalName && file.name === canonicalName && !file.isActive) return true;
    
    // 3. [2026-09-29] [解决 🔴4] 客户当前生效底牌：必须享有最高可编辑权！母版回滚采纳后依然允许打磨编辑与保存！
    if (file.isActive) return false;
    
    // 4. 首版母版留档文件：当未被激活生效时，作为历史母版归档保持只读受保护
    if (file.isProtectedArchive) return true;
    
    // 5. 手建自定义文件与灵感分支草稿：只要不在废纸篓，永远保持自由编辑打磨
    if (file.isManual || file.slotKey === 'slot_manual' || file.isBranchDraft) return false;
    
    // 6. 属于某槽位的更旧被淘汰历史版本 (具备 isRetired: true)：强制只读
    if (!file.isActive && isHistoricalRetired(file, files)) {
      return true;
    }
    
    // 7. 最新候选工作草稿 (未采纳)、新建文件：完全可编辑打磨保存！
    return false;
  }
  ```

### 2. 统一保存与单向主干镜像纯函数 (`computeSaveResult` · 彻底解决 🔴1 内容守卫 & 🟡4 只读守卫)
用户在编辑器点击【保存文件】或按 Cmd+S 时，由纯函数统一计算新状态与主干镜像：

```javascript
export function computeSaveResult({ targetName, content, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[targetName];
  if (!target) return { files, mirrored: false, success: false, reason: 'FILE_NOT_FOUND' };
  
  // 纯函数内部自证只读不变量 (防线不外置 · 解决 🟡4)
  if (isReadOnlyFile(target, files, stage)) {
    console.warn(`[computeSaveResult] 目标文件处于只读锁定状态 [${targetName}]，拒绝保存！`);
    return { files, mirrored: false, success: false, reason: 'READ_ONLY_LOCKED' };
  }
  
  if (content === undefined) {
    return { files, mirrored: false, success: false, reason: 'MISSING_CONTENT' };
  }

  const safeContent = content;
  const slotKey = target.slotKey || resolveSlotKey(targetName, stage, target.isManual);
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  const hasValidContent = typeof safeContent === 'string' && safeContent.trim().length > 0;

  // 活跃生效底牌/规范骨干严禁保存空内容，防止数据洗白与底牌骨干分叉 (彻底解决 🔴2)
  if (target.isActive && !hasValidContent) {
    console.warn(`[computeSaveResult] 尝试用空内容保存生效底牌 [${targetName}]，已被安全拦截！`);
    return { files, mirrored: false, success: false, reason: 'EMPTY_CONTENT' };
  }

  const newFiles = { ...files };

  // 1. 保存目标文件自身内容 (持久化回写 slotKey · 解决 🟡16)
  newFiles[targetName] = {
    ...target,
    name: targetName,
    slotKey,
    content: safeContent,
    savedContent: safeContent,
    isDirty: false,
    updatedAt: nowIso,
  };
  
  // 2. 活跃文件自动单向镜像契约 (带非空内容守卫 · 彻底解决 🔴1)
  let mirrored = false;
  if (target.isActive && canonicalName && canonicalName !== targetName && newFiles[canonicalName]) {
    if (hasValidContent) {
      newFiles[canonicalName] = {
        ...newFiles[canonicalName],
        name: canonicalName,
        slotKey,
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
  
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  
  // 1. 候选自身类型自证守卫：受限类型绝不可作为采纳候选，防自锁矛盾态
  // [2026-09-29] [解除母版采纳死锁] 放开 isProtectedArchive，支持第 1 版历史母版一键回滚生效
  if (
    target.isCanonicalMirror ||
    target.isManual ||
    slotKey === 'slot_manual' ||
    slotKey === 'slot_misc' ||
    (canonicalName && candidateName === canonicalName && !target.isProtectedArchive)
  ) {
    console.warn(`[computeAdoptResult] 目标文件 [${candidateName}] 属于受限类型（规范镜像/手建草稿/杂项草稿/规范骨干自身），禁止作为采纳候选！`);
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
  // [2026-09-29] 放开 isProtectedArchive：允许第 1 版历史母版被点击【设为客户采纳】，支持一键回滚生效
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
      // 存在多个 active 脏数据：按【最高版本 > 规范骨干 > 其余】显式排序选取唯一 active (彻底解决 🔴2)
      activeList.sort((a, b) => {
        const vDiff = getVerNum(b) - getVerNum(a);
        if (vDiff !== 0) return vDiff;
        const isA = a.name === canonicalName;
        const isB = b.name === canonicalName;
        if (isA && !isB) return -1;
        if (!isA && isB) return 1;
        return 0;
      });
      chosen = activeList[0];
      for (const f of activeList) {
        if (f.name !== chosen.name) f.isActive = false;
      }
    } else if (activeList.length === 1) {
      chosen = activeList[0];
    } else if (activeList.length === 0 && slotFiles.length > 0) {
      // 槽位无任何 active：优先激活非镜像候选草稿中最高版本的草稿，若无草稿且规范骨干非镜像，则激活规范骨干 (彻底解决 🔴1, 🔴2)
      // 兜底候选必须严格三重排除 isCanonicalMirror, isProtectedArchive, isManual，严禁激活母版！
      const candidateList = slotFiles.filter((f) => !f.isCanonicalMirror && !f.isProtectedArchive && !f.isManual);
      if (candidateList.length > 0) {
        candidateList.sort((a, b) => getVerNum(b) - getVerNum(a));
        chosen = candidateList[0];
        chosen.isActive = true;
      } else {
        const canonical = slotFiles.find((f) => f.name === canonicalName);
        if (canonical && !canonical.isCanonicalMirror && !canonical.isProtectedArchive) {
          chosen = canonical;
          chosen.isActive = true;
        } else {
          console.warn(`[migrateAndNormalizeFiles] 槽位 [${sk}] 仅存镜像或母版，无合法可激活底牌，保持零 active 态`);
        }
      }
    }

    // 若非骨干被激活，同步确保规范骨干打上镜像标记，杜绝骨干落入可改半保护态 (彻底解决 🔴2)
    if (chosen && chosen.name !== canonicalName) {
      const canonical = slotFiles.find((f) => f.name === canonicalName);
      if (canonical) {
        canonical.isCanonicalMirror = true;
        canonical.isActive = false;
        canonical.isRetired = false;
      }
    }
    
    // 为老数据同槽已被淘汰的历史旧版补充 isRetired: true (彻底解决 🔴1 误伤)
    if (chosen) {
      for (const f of slotFiles) {
        // 显式豁免规范骨干、镜像与母版，绝对不打淘汰标记！(彻底解决 🔴2)
        if (f.isCanonicalMirror || f.isProtectedArchive || f.name === canonicalName) {
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

  // 收敛后终检：
  // 1. 确保任何镜像文件绝不持有 isRetired 或 isActive (彻底解决 🔴1)
  // 2. 确保规范骨干终身不打 isRetired 淘汰标记 (彻底解决 🔴2)
  // 3. 确保非本阶段有效工序槽位 (slot_misc, slot_manual 或跨阶段槽位) 的文件绝不持有 isActive = true (解决 🟡11)
  const coreFiles = getCoreFilesByStage(stage);
  for (const fn of Object.keys(normalized)) {
    if (normalized[fn].isCanonicalMirror) {
      normalized[fn].isRetired = false;
      normalized[fn].isActive = false;
    }
    if (coreFiles.includes(fn)) {
      normalized[fn].isRetired = false;
    }
    if (!validSlots.includes(normalized[fn].slotKey)) {
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

---

## 七、成套版本套餐体系与素材库独立 S 体系设计 (Grill-Me 迭代沉淀)

### 7.1 全链路成套版本套餐 (Version Set) 与自由回滚架构

#### 1. 面向对象三问
- **对象是什么**：版本套餐（`VersionPackage`），由主版本号（如 `V1`, `V2`, `V3`）统领的交付物集合。
- **属性有哪些**：
  - `packageVersion`: 套餐版本号（如 `V1`, `V2`, `V3`）；
  - `questionnaireFile`: 对应版本的提问清单（如 `豆包提问清单_V1.txt`）；
  - `answerFile`: 对应版本的实测回答（如 `豆包实测回答_V1.txt`）；
  - `draftReportFile`: 对应版本的商业诊断初稿（如 `商业诊断初稿_V1.md`）；
  - `finalReports`: 对应版本的最终交付物（如 `对客决策大屏_V1.html` 与 `对客文字报告_V1.md`）。
- **行为是什么**：
  - `adoptPackageVersion(version)`: 将某一版本设为全局生效套餐，全链路下游自动对齐；
  - `rollbackToMaster()`: 误点采纳后一键回滚切回原始母版 V1，后续各环节无需推倒重来。

#### 2. 解除母版采纳死锁与回退逻辑
在 `studioArtifactConfig.js` 与 `StudioEditor.vue` 中彻底解开历史母版的采纳限制：
- `isProtectedArchive: true` 仅代表**【不可删除】**（`canDeleteFile` 拦截返回 false），保护底座不丢失；
- **允许自由采纳**：`canAdoptCurrentFile` 针对 `isProtectedArchive` 返回 true，允许用户随时点击【设为客户采纳】；
- 当母版（如第 1 版）被点击采纳时：
  - 母版恢复 `isActive = true`；
  - 规范主干同步镜像母版内容；
  - 之前采纳的高版本（如 V3）降级为草稿（`isActive = false`，`isRetired = true`）；
  - 跨阶段缓存 `geo_step0_active_qa_${clientId}` 恢复指向 V1，全链路下游自动归正。

---

### 7.2 分支灵感草稿微调优化流转 (如 V3 ➔ V3.1)

#### 1. 业务痛点与流转机制
交付人员在主版本（如 V3）基础上需要微调或再让 AI 激发灵感，但不想污染干净的主版本：
1. **生成分支草稿**：点击【重试/分支生成】，生成带有小数点的灵感分支（如 `豆包提问清单_V3.1.txt`），标记 `isBranchDraft: true`；
2. **自由编辑与打磨**：分支草稿与主版本均允许打字编辑，并支持快捷键/点击保存；
3. **人类挑词合入**：交付人员对比后，将 V3.1 的优质内容手工复制粘贴回 V3 主版本并保存；
4. **清理归档**：将临时分支 V3.1 移入废纸篓（或保留不删），主版本 V3 依然干净整洁。

---

### 7.3 阶段 0.2 实测回答成套生成与问答成对呈现

#### 1. 多版本跟随生成
当在阶段零 0.1 采纳 `豆包提问清单_V${N}.txt` 后，阶段 0.2 实测生成的回答文件必须以对应版本号命名：
- 生成文件名：`豆包实测回答_V${N}.txt`；
- 各版本回答文件独立共存，**严禁使用单一固定文件名覆盖**。

#### 2. 问答成对 (Q&A) 规范排版结构
回答文件正文必须包含完整的测试题目与豆包原始回答成对呈现，格式如下：
```text
==================================================
【测试题目 1】什么是你公司的核心业务？
【豆包实测回答】
根据公开信息检索...（豆包实际回答内容）
==================================================
【测试题目 2】你公司的主要优势是什么？
【豆包实测回答】
...
```

---

### 7.4 左侧文件树视觉瘦身与极简小绿勾规范

#### 1. 展示层视觉瘦身与底层存储兼容契约（解决 🔴3）
为防止直接物理改名破坏存量用户 `localStorage` 历史数据与底层工序槽位映射（`CANONICAL_SLOT_DICT`）：
- **底层物理存储**：保持规范命名体系与槽位键（`slot01`~`slot08`）强绑定，确保向下兼容与确定性持久化；
- **展示层（UI）视觉瘦身**：在左侧文件列表与顶栏 Tab 标题处，动态剥离 `01_`、`02_` 等数字序号前缀与冗余中缀，以极简语义短名呈现：
  - `01_豆包实测提问清单_第1版.txt` ➔ UI 显示为 **`豆包提问清单_V1.txt`**
  - `02_豆包实测回答_第1版.txt` ➔ UI 显示为 **`豆包实测回答_V1.txt`**
  - `商业诊断转化初稿_第1版.md` ➔ UI 显示为 **`商业诊断初稿_V1.md`**
  - `对客决策大屏_第1版.html` ➔ UI 显示为 **`对客决策大屏_V1.html`**
  - `对客交付文字版报告_第1版.md` ➔ UI 显示为 **`对客文字报告_V1.md`**

#### 2. 极简小绿勾与版本标 (`✓ V1`)
- **废弃**：原先长达数十像素的胶囊徽章 `[已采纳 QA-V3]`；
- **采用**：直接在条目最左侧显示绿色勾选与版本号：**`✓ V1`**（绿色高亮）；未采纳的草稿显示灰色版本号（如 `V2`）。左栏大幅减负。

---

### 7.5 阶段二 企业素材库独立 S 体系与 6 大 RAG 黄金分类

#### 1. 素材库独立抽取与 S 体系编号
素材库作为企业长期数据资产独立抽离，不与 V 流水线混杂，采用 **`S` (Source)** 编号体系：
- **主版本标准库**：`S1`, `S2`, `S3`, `S4`, `S5`, `S6`...
- **分支草稿**：`S1.1`, `S1.2`...

#### 2. 人机两分核心硬约束契约 (防 AI 幻觉)
- **人类视角**：可在界面上查看、编辑所有 S1、S1.1 等文件，随时对比调整；
- **系统/AI 消费视角**：系统在组装母盘、喂给大模型写博文或进行 RAG 检索时，**仅过滤并读取 S 主版本（正则表达式 `^S\d+(_|\.)` 中不含小数点的标准主文件）**，所有 `.x` 分支草稿一律屏蔽不读取，保证喂给 AI 的事实 100% 干净唯一！

#### 3. 6 大 RAG 黄金检索分类模型

| 分类标识 | 分类名称 | 核心资产内容 | 聚合与删除规则 |
|:---|:---|:---|:---|
| **Category 1** | **主体与法定边界** | 公司工商全称、统一社会信用代码、法定注册与办公地址、官方权威网站、官方服务专线、**坚决不做的负面清单** | 唯一标准版 S1 |
| **Category 2** | **产品与价格标准** | 标准交付流程、分阶段交付物明细、明码标价价格区间（如建站 ¥3000 起）、**明确不承诺的结果** | 唯一标准版 S2 |
| **Category 3** | **客户画像与场景** | 适合的目标行业（如 B2B 制造、实体门店）、客户触发时机、典型痛点场景 | 唯一标准版 S3 |
| **Category 4** | **同行策略与参数对比** | 与普通网络公司、模板建站的参数硬对比表 | 按对标竞品公司聚合（如 `S4_优搜网络`）；若放弃对标该公司，整组删除（包含 `S4.1` 等） |
| **Category 5** | **真实故事化案例库** | 真实客户案例（拟定故事化标题，包含原始问题、我方动作、首推率量化提升结果） | 按标杆客户聚合为单条标准故事，作为 AI 撰写行业博文的权威故事背书 |
| **Category 6** | **权威凭据与背书** | 细分子分类：<br>① `证书资质`：国家标准认证 (GB/T)、电信实名备案、软著专利；<br>② `合同业绩`：标杆客户合作合同扫描件脱敏记录、SLA 服务保障协议 | 支持整理修改，生成标准事实凭证供 AI 引用 |

#### 4. 阶段二全新流水线动线 (5 步交付动线)
重构阶段二 3 竖列工作区 SOP 动线：
```text
【第 1 步：素材录入与分类归集】(继承上游问答+手动录入+老官网清洗)
           ↓
【第 2 步：9 因子结构化提炼萃取】(剥离夸张推销词，提取 6 大类标准事实 S1~S6)
           ↓
【第 3 步：成套出具普林斯顿唯一母盘】(生成 母盘_V1.md，版本与流水线成套对齐)
           ↓
【第 4 步：按需派生高权威博文】(基于母盘和故事案例派生对外博文)
           ↓
【第 5 步：全渠道内容分发与封版交付】(确认素材底座与衍生博文就绪，封版进入下一阶段)
```

---

## 八、第四阶段：智能 Tab 栈管理、初稿微调分支与素材 8K 降噪分拣台架构

### 8.1 智能 Tab 栈管理算法（首置插入与 6 标签智能淘汰）

#### 1. 痛点与交互模型
在实际作业中，交付专家经常在多个文件间穿梭对比。如果新打开的文件总是排在最后，Tab 栏过长时极难辨识当前打开的是什么。
- **首置插入**：每次打开新文件，或者从左栏树点击已有文件，统一将目标文件移到 `openTabs` 数组的**第 0 位（最左端）**：
  ```javascript
  function activateTab(fileName) {
    const idx = openTabs.value.indexOf(fileName);
    if (idx > -1) {
      openTabs.value.splice(idx, 1);
    }
    openTabs.value.unshift(fileName);
    activeFileName.value = fileName;
    
    // 超量 6 个智能淘汰
    pruneTabsIfOverflow();
  }
  ```

#### 2. 超量 6 个智能淘汰契约
当 `openTabs.value.length > 6` 时：
1. 从最右侧（最老末尾）向左扫描；
2. 找到第一个**未修改（`!files[fn].isDirty`）**的干净 Tab，自动将其从 `openTabs` 移除关闭；
3. 若所有 6 个 Tab 均持有未保存修改（`isDirty === true`），则不执行静默关闭，而是弹出安全确认浮层：
   『检测到已有 6 个未保存标签页，是否保存末尾文件【XXX】后关闭？』，支持【保存并关闭】或【放弃修改并关闭】。

---

### 8.2 阶段一商业初稿派生分支 (V1.1) 与 Markdown 语法保留

#### 1. 出具初稿派生分支机制
当交付专家处于阶段一第 2 步点击【直出商业诊断与转化初稿】：
- 若当前没有 V1 初稿，生成 `商业诊断初稿_V1.md`；
- 若已有生效中的 `商业诊断初稿_V1.md`，点击出具初稿意味着交付专家对现有稿件不满意，希望获取备选方案：
  - 自动调用 `computeBranchVersion` 派生 `商业诊断初稿_V1.1.md`（或 `V1.2.md`）；
  - 新分支打上 `isBranchDraft: true`，与主版本 V1 并列出现在左侧与 Tab 栏；
  - 交付专家可在两份初稿间切换对比、手工挑词合并。合并满意后可将分支删入废纸篓。

#### 2. 原生 Markdown 结构全面保留
师弟拍板裁决：给外部大模型优化润色时，**100% 保留原生 Markdown 格式**。
- 大模型本身受过海量 Markdown 预训练，能深刻理解 `#`、`##` 标题层级、`-` 列表项以及 `|` 参数对比表格；
- 剥离 Markdown 语法反而会变成失去排版结构的扁平纯文本，降低大模型的上下文理解深度；
- 因此中栏复制按钮保持高保真 Markdown 复制。

---

### 8.3 阶段二素材库：官网抓取 8K 降噪与【素材分拣台】架构

#### 1. 本地模型 8K Token (约 8500 汉字) 输入墙挑战与破局解
- **痛点**：客户官网整站 HTML 或长页面往往包含海量 JS、CSS、导航、通用页脚、版权声明，动辄数万字符。若不加筛选直接一股脑塞给本地小毛驴模型，会直接撞爆 8K Token 上限，或导致关键业务事实被生硬截断。
- **解法（两级清洗萃取流水线）**：
  ```text
  【客户官网 URL 或微信老资料】
               ↓
  [Step 1 本地轻量正文降噪] (Python BeautifulSoup 剥离 DOM 噪声，提取 3000 字事实骨架)
               ↓
  [Step 2 素材智能分拣台] (交付专家核对/手工粘贴补充，控制在 8500 汉字以内)
               ↓
  [Step 3 本地大模型分拣] (一次性提取并智能分发至 S1~S6 对应文件)
  ```

#### 2. 素材分拣台交互设计（动线第 1 步）
修正 `Step2App.vue` 动线传参（由 `:sop-steps` 纠正为 `:stage-meta="STAGE_2_META"`），阶段二第 1 步展示真正的【素材分类归集与萃取】卡片：
- 卡片集成【一键抓取官网】按钮（输入网址，后端执行文本降噪后填入分拣台）；
- 卡片集成【资料粘贴框】：支持交付专家把客户口述、微信聊天记录、合同片段直接粘贴进来；
- 点击【AI 智能分发到 6 大素材库】：本地大模型提取后自动更新写入 `S1_企业主体与法定边界.md`、`S2_核心产品与价格承诺.md`、`S4_对标竞品参数对比表_*.md` 等标准主文件，完成素材进场。

---

## 九、第五阶段：【02 客户素材资产管理库】独立整页化、6分类结构化资产台与时序拨乱反正（本次 Grill-Me 深度对齐架构设计）

### 9.1 宏观交付阶段重组（8 大阶段）
彻底废除将素材、母盘、博文三者混杂在同一页面的混乱设计，左侧大导航重组为职责单一的 8 个独立大阶段：
1. **`00 豆包提问查现状`**（0.1 出题打磨 ➔ 0.2 网页真机提问贴回回答）；
2. **`01 诊断现状并出具报告`**（抓取底座指标 ➔ 出具商业初稿 V1/V1.1 ➔ 交付对客决策大屏与文字报告）；
3. **`02 客户素材资产管理库`**（★独立大阶段：既负责素材多源收集录入，又负责长期结构化资产管理）；
4. **`03 普林斯顿高权威唯一母盘`**（★独立大阶段：纯粹专注 9 因子法定事实提纯、版本合流与冲突裁决）；
5. **`04 交钥匙官网与三件套`**（静态秒开建站、知识图谱与反代通道）；
6. **`05 GEO 答题卡与向量问答库`**（标准 Q&A 题卡与向量知识库）；
7. **`06 矩阵发帖与高权威博文分发`**（基于【03 母盘事实 + 05 答题卡题目】批量派生高权威博文并分发检查）；
8. **`07 首次交付与资产交接单`**（全套交付资产归档交接）。

### 9.2 【02 客户素材资产管理库】面向对象模型设计 (Rule 4.2 面向对象三问)

| 分类标识 | 业务对象 (Entity) | 核心业务属性 (Attributes) | 交互与维护行为 (Behaviors) | 对应底层文件 |
|:---|:---|:---|:---|:---|
| **Category 1** | **主体与法定边界**<br>`CompanyEntity` | 公司工商全称 (`company_name`)<br>品牌简称/字号 (`brand_name`)<br>统一社会信用代码 (`credit_code`)<br>法定代表人 / 负责人 (`legal_person`)<br>官方服务专线 (`service_phone`)<br>实际办公地址 (`business_address`)<br>官方权威网址 (`official_website`)<br>业务红线与负面清单 (`negative_list`) | ① 专属卡片展示核心法定事实<br>② 点击【编辑主体信息】弹出结构化表单修改<br>③ 抓取官网骨架自动回填电话/地址/备案号<br>④ 自动编译并同步写入底层标准文件 | `S1_企业主体与法定边界.md` |
| **Category 2** | **产品与价格标准**<br>`ServiceProductCatalog` | 标准交付流程列表 (`delivery_process`)<br>交付物明细清单 (`deliverables_list`)<br>明码标价阶梯 (`price_tiers`: 档位名、价格、包含范围)<br>明确不承诺的结果 (`explicit_non_commitments`) | ① 卡片直观展示服务流程与明码标价阶梯<br>② 点击【+ 新增服务套餐/价目档位】<br>③ 点击【编辑价格标准与不承诺清单】<br>④ 自动编译并同步写入底层标准文件 | `S2_核心产品与价格承诺.md` |
| **Category 3** | **客户画像与痛点场景**<br>`TargetAudienceProfile` | 适合的目标行业标签 (`target_industries`)<br>客户触发时机 (`trigger_moments`)<br>典型痛点场景列表 (`pain_points`: 场景名、典型症状、解决策略) | ① 标签化管理适合的目标行业与触发时机<br>② 卡片列表管理痛点场景，支持快速增删<br>③ 点击【+ 添加典型痛点场景】<br>④ 自动编译并同步写入底层标准文件 | `S3_目标客户与典型场景.md` |
| **Category 4** | **同行策略与参数对比**<br>`CompetitorComparisonList` | 对标竞品公司列表 (`competitors`)，每项包含：<br>- 竞品名称 (`name`)<br>- 竞品常规收费与套路 (`price_and_pitfalls`)<br>- 我方正规军差异化优势与参数对比 (`our_advantages`) | ① 并排卡片展示各个对标竞品<br>② 点击【+ 添加对标同行】，输入竞品优劣参数<br>③ 支持逐家编辑或整组删除某家竞品<br>④ 自动编译并对应生成 `S4_对标竞品参数对比表_${name}.md` | `S4_对标竞品参数对比表_*.md` |
| **Category 5** | **真实故事化案例库**<br>`CaseStoryCollection` | 客户案例故事列表 (`cases`)，每项包含：<br>- 故事化标题 (`story_title`)<br>- 客户行业与原始痛点 (`client_pain`)<br>- 我方关键动作 (`our_actions`)<br>- 量化提升结果 (`quantified_result`) | ① 瀑布流展示真实案例故事卡片<br>② 点击【+ 添加客户案例故事】弹出标准三段式表单<br>③ 支持查看详情、编辑内容、废纸篓软删除<br>④ 自动编译并对应生成 `S5_经典案例故事_${name}.md` | `S5_经典案例故事_*.md` |
| **Category 6** | **权威凭据与背书**<br>`AuthorityCredentials` | 细分为两大维度的凭证列表：<br>① 证书资质 (`certifications`: 名称、发证机关、有效期限、编号)<br>② 合同业绩脱敏 (`contracts`: 标杆客户名、合同性质、脱敏凭据说明、SLA服务保障条款) | ① 双标签卡片：【资质证书】与【合同业绩凭据】<br>② 点击【+ 添加资质/合同凭据】录入凭证<br>③ 支持修改与删除<br>④ 自动编译并同步写入底层标准文件 | `S6_权威背书与资质凭据.md` |

### 9.3 双轨整理动线与素材工作台布局设计

#### 1. 双轨素材整理机制
- **轨道一（全局粗筛与 AI 智能分流）**：
  - 顶栏常驻【资料自由粘贴 AI 分流】入口与抽屉；
  - 交付专家把客户的一大堆微信聊天记录、宣传册文本、历史合同摘录直接贴进来；
  - 本地规则/大模型解析后，给出分发建议，并向 6 大分类卡片标记“待核验新素材（N项）”；
- **轨道二（卡片专属精细维护与日常管理）**：
  - 6 大分类卡片各自拥有专职的【+ 新增】与【编辑】抽屉；
  - 交付专家拿到单项材料（如一张竞品报价单、一个新合作客户案例、一个统一社会信用代码），可直接点进对应卡片精准录入与维护。

#### 2. 工作台三栏布局
- **顶栏（页面概览与进场）**：
  - 客户名称与行业标签；
  - 【一键抓取官网骨架】输入框与降噪抓取按钮；
  - 【资料自由粘贴 AI 分流】抽屉入口；
- **中左主体区（6 大分类结构化资产面板）**：
  - 6 块专属资产卡片网格布局，清晰展现每个分类的核心指标（如：S1 统一代码已验证、S2 包含 2 档明码标价、S4 已对标 1 家同行、S5 沉淀 2 个标杆故事）；
  - 点击卡片上的【管理/编辑】按钮，滑出该分类的专职结构化抽屉，进行逐项增删改查；
- **右侧栏（素材资产健康度自检与推进）**：
  - 素材资产健康度得分雷达（6 项必备事实已填数量，直观展示绿黄红灯）；
  - 推进按钮：【素材整理完毕，一键生成普林斯顿母盘 ➔】，点击平滑跳转进入阶段 03。

### 9.4 普林斯顿母盘阶段（03）与博文矩阵阶段（06）时序彻底拨乱反正

#### 1. 痛点根因分析
此前版本在阶段 02 页面内部硬塞了“高权威博文库”，直接导致：
- 阶段 02 界面杂乱无章，中间放博文，顶上放分拣台，左边放素材库，视觉极度混乱；
- **时序颠倒**：博文的撰写必须严格依托“普林斯顿法定母盘（提供事实约束与背书）”+“GEO 答题卡（提供真实搜索问题靶心）”。在连母盘都没定稿、题卡还没做的情况下，凭空在第 2/3 步写博文完全是幻觉与空转。

#### 2. 彻底拨乱反正实施契约
- **普林斯顿母盘阶段（03 普林斯顿高权威唯一母盘）**：
  - **彻底剔除博文库（`article_*.md`）及博文派生逻辑**；
  - **彻底移除中间上方素材分拣台卡片**；
  - 页面彻底纯化为：母盘文本审阅打磨、事实冲突直观裁决卡（对比新老素材与母盘差异），以及母盘多版本成套生成（母盘_V1.md / 母盘_V2.md）；
- **博文生成阶段后置到 06（矩阵发帖与高权威博文分发）**：
  - 在第 06 阶段，系统自动基于【03 母盘事实】+【05 答题卡题目】，批量派生高权威行业博文（`article_*.md`），并无缝衔接矩阵链接分发与收录检查！全链路因果关系严密清晰。

---

## 十、第十阶段：【02 客户素材资产工作台】真实双场景与 RAG 语义去重深度架构（师弟立规与终局契约）

### 10.1 核心业务对象模型 (Rule 4.2 面向对象三问)

```typescript
/** 客户原始素材大文字稿对象 (SSOT) */
export interface RawMaterialDraft {
  clientId: string;                // 当前客户唯一 ID (严格归属当前客户项目库)
  textContent: string;             // 中间文字稿正文
  charCount: number;               // 当前字数
  maxLimit: 8500;                  // 最大字符限制 (契合本地模型 8K Token 安全水位)
  sourceType: 'web_scrape' | 'manual_paste'; // 来源通道
  sourceUrl?: string;              // 抓取的网址 (若为网页抓取)
  updatedAt: string;               // 最近修改时间戳
}

/** AI 语义切块与审核片段对象 */
export interface MaterialChunkCandidate {
  chunkId: string;                 // 切片唯一标识
  targetCategory: 'S1' | 'S2' | 'S3' | 'S4' | 'S5' | 'S6'; // 建议归属分类
  categoryLabel: string;           // 分类中文名
  suggestedTitle: string;          // 建议标题
  content: string;                 // 切片正文字文 (人工可自由编辑)
  isEdited: boolean;               // 人工是否进行了手工修改
  isDiscarded: boolean;            // 人工是否标记丢弃
  similarityClusterId?: string;    // RAG 语义去重聚类组 ID (若存在高相似度素材)
  similarExistingChunkId?: string; // 关联的已有相似存量素材 ID
  similarityScore?: number;        // 相似度得分 (0~1)
}

/** RAG 语义去重聚合组 */
export interface DuplicateClusterGroup {
  clusterId: string;
  category: string;
  existingMaterial: { id: string; title: string; content: string; updatedAt: string };
  newCandidate: MaterialChunkCandidate;
  similarity: number;              // 语义相似度
  mergeStatus: 'pending' | 'merged' | 'kept_both' | 'discarded_new';
}
```

### 10.2 真实双场景进场与中间大文字稿交互流
拒绝空中楼阁式的全自动大黑盒，严格围绕操作员的真实打字与整理场景：
1. **场景一（单一网址抓取）**：
   - 操作员在工作台顶部输入一个客户现有网址（如官网、公众号文章、落地页）；
   - 点击【一键抓取网页骨架】➔ 后端通过清洗过滤剥离前端 HTML 样式与 JS 噪音，提纯出纯文本正文；
   - 自动回填进中间的**大文字书写稿**中；
   - 界面实时计算字数：
     - 若 `<= 8500` 字：字数指示器显示绿色正常；
     - 若 `> 8500` 字：字数指示器变红并弹出友好提示：*“当前网页抓取字数已超 8500 字（目前 ${N} 字），大模型将拒绝处理，请在下方编辑器中人工删减无用段落后再行分拣”*。
2. **场景二（人工复制粘贴）**：
   - 操作员直接打开微信聊天记录、企业宣传折页 Word/TXT、历史合同，选中文字并复制；
   - 直接在中间的大文字书写稿区域粘贴；
   - 操作员可以随时在光标处敲字、修饰、删改，同样受到 8500 字上限的实时保护与字数变色监控。

### 10.3 AI 语义切块输出协议与人工终审工作台 (Human-in-the-loop)
1. **AI 语义分拣协议 (Prompt 契约)**：
   - 将这篇不超过 8500 字的完整文字送入本地模型（如 DeepSeek 或豆包）；
   - Prompt 注入 6 大黄金分类定义（S1 主体、S2 价格、S3 痛点、S4 竞品、S5 案例、S6 资质）；
   - AI 输出标准 JSON 数组，将混杂的长文拆解为 3~4 篇（或若干篇）独立的切块片段。
2. **人工终审工作台（四项绝对权力）**：
   - 页面右侧/弹层呈现切块卡片流水席，绝不暗箱操作直接落库；
   - **操作一（预览展开）**：点击卡片展开全部正文与字数；
   - **操作二（手工修改）**：在卡片文本框内直接打字修改，改动时实时标记 `isEdited = true`；
   - **操作三（分类纠偏）**：若 AI 判断错误，操作员通过下拉框把“分类 2”手工改为“分类 3”；
   - **操作四（垃圾桶丢弃）**：点击切片右上角垃圾桶，该片段直接标记废弃；
   - **操作五（一键采纳入库）**：全部检查完毕后，点击【确认采纳入库】，被采纳的切片进入 RAG 语义去重阶段。

### 10.4 RAG 语义聚类去重机制（师弟立规 · 拒绝假大空标题匹配）
1. **去重第一性原理**：
   - 客户碎片材料不具备标准化规范标题，严禁通过“标题一模一样”进行判断；
   - 去重必须基于**正文语义相似度向量检索（RAG）**。
2. **RAG 语义聚类处理流**：
   ```text
   [新审核采纳的切片]
          ↓
   [向量化 Embedding] ➔ 在当前客户的项目知识库中进行向量语义检索
          ↓
   [相似度阈值判定]
          ├─ 相似度 < 0.50 ➔ 无冲突新素材 ➔ 直接安全入库并归入对应分类抽屉
          └─ 相似度 ≥ 0.50 ➔ 发现高度重叠素材 ➔ 触发【RAG 语义去重聚类】（实测中文 Bigram Jaccard 黄金阈值 0.50）
   ```
3. **去重对比文件夹/二级子目录呈现**：
   - 在界面中自动归入【待去重合并组】；
   - 左右双栏高亮并排对比：
     - 左栏：当前库中的【存量老素材】；
     - 右栏：本次提取的【新待入库素材】；
   - 中间提供【人工文案合并器】：
     - 操作员一眼看出新素材比老素材多了哪些细节（例如老素材只有价格，新素材多了售后条款）；
     - 操作员直接在合并编辑器中合成出一篇最完整、最精确的文案；
     - 点击【完成合并并更新库】：以合并后的终稿替换旧版，彻底解决知识库内容膨胀与自我矛盾。

### 10.5 存储归宿与零歧义原则
- 所有清洗、审核与合并后的素材资产，**100% 自动归入当前选中的客户项目库**（如 `currentProjectId: "nextgeo"`）；
- 本地存储与数据库记录以 `client_id` 为天然隔离分区，严禁向操作员提出“存入哪个库”等脱离业务常识的问题。

---

## 11. 中栏双行标准头部组件 (StudioHeader) 抽象与跨阶段复用契约 (师弟立规)

### 11.1 痛点成因与设计目标
- **现状痛点**：第一页（`StudioEditor.vue`）中栏顶栏采用了“双行架构”——第一行放状态徽章、字符数、时间戳与操作按钮，第二行独立放 Tab 标签栏，布局极其整洁专业；而第二页（`Step2App.vue`）因为直接手写内联标签栏，把 Tab 标签与操作按钮塞在同一行，导致视觉严重拥挤变形。
- **设计目标**：提取一个通用的公共 Vue 组件 `web/step0-src/components/studio/StudioHeader.vue`，第一页和第二页彻底消除重复模板，第二页直接继承第一页成熟的双行标准。

### 11.2 StudioHeader 组件接口契约

```typescript
// StudioHeader.vue Props & Emits 定义
interface StudioHeaderProps {
  stage: 'step0' | 'step1' | 'step2' | 'step3'; // 当前所处阶段
  files: Record<string, StudioFileItem>;        // 全量文件映射字典
  openTabs: string[];                          // 当前打开的 Tab 文件名列表
  activeFileName: string;                      // 当前激活的文件名
  noticeMessage?: string;                      // 顶部轻量浮动通知（防原生 alert 红线）
  isReadOnly?: boolean;                        // 当前文件是否处于正交只读态
}

interface StudioHeaderEmits {
  (e: 'selectTab', fileName: string): void;    // 切换激活 Tab
  (e: 'closeTab', fileName: string): void;     // 关闭指定 Tab
}

interface StudioHeaderSlots {
  actions?: () => VNode[];                     // 第一行右侧快捷操作插槽
  'meta-extra'?: () => VNode[];                // 第一行左侧扩展元数据插槽
}
```

### 11.3 双行排布结构与 CSS 样式规范
1. **第一行：状态元数据与操作工具栏**：
   - 容器类名：`bg-slate-50 border-b border-slate-200 px-3 py-2 flex items-center justify-between gap-3 select-none flex-wrap`
   - 左侧：
     - 文件状态徽章：阶段一显示【客户生效底牌 V1】/【候选版本 V2】；阶段二显示【S1·主体边界】等分类标；
     - 字符数统计：`{{ (currentFile?.content || '').length }} 字符`；
     - 生成时间：`生成时间: {{ currentFile?.generatedAt || '刚刚' }}`；
   - 右侧：
     - `<slot name="actions">`：由调用方根据阶段需求传入专属按钮：
       - 第一页：`源码/预览/全屏` + `一键复制` + `保存文件`；
       - 第二页：`素材采集与蒸馏工作台 / Markdown源码` + `一键复制` + `保存修改`。
2. **第二行：独立文件 Tab 标签栏**：
   - 容器类名：`bg-slate-100/90 border-b border-slate-200 flex items-center px-2 pt-1.5 gap-1.5 overflow-x-auto select-none scrollbar-none`
   - 标签类名：
     - 激活项：`bg-white text-[#7c5bf5] border-slate-200 font-bold -mb-[1px]`
     - 未激活项：`bg-slate-200/60 hover:bg-slate-200 text-slate-600 border-transparent`
     - 废纸篓标：`[废纸篓]` (仅当被软删除时渲染)
     - 脏标记：琥珀色小圆点 `w-2 h-2 rounded-full bg-amber-500` (仅当 `isDirty` 为 true 时渲染)
     - 关闭叉号：`text-slate-400 hover:text-slate-700 hover:bg-slate-300/60 rounded p-0.5 text-xs transition`

### 11.4 跨阶段消费流向 (SSOT)
```text
           ┌──────────────────────────────────────┐
           │     StudioHeader.vue (公用双行头)     │
           │  - Row 1: 状态徽章/字数/时间 + actions 槽 │
           │  - Row 2: 独立 Tab 标签栏 (高亮/脏标/关闭) │
           └──────────────────┬───────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌─────────────────────────┐             ┌─────────────────────────┐
│ 第一页: StudioEditor.vue │             │  第二页: Step2App.vue   │
│  - slot: 源码/预览/全屏  │             │  - slot: 工作台/源码模式 │
│  - 下接: CodeMirror/HTML │             │  - 下接: 网页蒸馏/大字板 │
└─────────────────────────┘             └─────────────────────────┘
```




