/**
 * studioArtifactConfig.js - 全局工作台核心工序槽位、版本防重名与正交生命周期纯函数模块
 * =========================================================================================
 * [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 统一全仓 SSOT 共享配置与算法核心：
 * 1. 集中定义 8 大核心工序槽位字典 CANONICAL_SLOT_DICT 与别名容错字典 ALIAS_SLOT_MAP；
 * 2. 导出 stage 阶段收窄器 getSlotsByStage 与 getCoreFilesByStage (Fail-Closed 关闸保护)；
 * 3. 导出跨端安全的本地存储访问器 safeStorageGet / safeStorageSet；
 * 4. 导出动态版本正则与版本防重名递增算法 computeNextVersion；
 * 5. 导出正交只读判定 isReadOnlyFile 与 Fail-Closed 关闸删除判定 canDeleteFile；
 * 6. 导出统一保存 computeSaveResult、统一采纳 computeAdoptResult、统一恢复 computeRestoreResult、统一软删除 computeDeleteResult；
 * 7. 导出存量数据迁移与单槽 Active 强制收敛算法 migrateAndNormalizeFiles；
 * 8. 导出遵循 AGENTS §3.3 / §3.5 的状态徽章文案格式化器 getActiveBadgeText。
 */

/**
 * 8 大核心工序槽位字典 (唯一真相源 SSOT)
 */
export const CANONICAL_SLOT_DICT = {
  // --- 阶段零（2个初始主干） ---
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

  // --- 阶段一（6个初始主干） ---
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
 * 别名与历史存量文件名容错映射字典
 */
export const ALIAS_SLOT_MAP = {
  '01_网络底座指标_待对照.md': 'slot_metrics',
  '01_网络底座指标': 'slot_metrics',
  '01_豆包提问清单_推荐版.txt': 'slot_stage0_questions',
  '01_豆包提问清单': 'slot_stage0_questions',
  '01_豆包题目': 'slot_stage0_questions', // 阶段零历史生成新版本前缀容错
  '02_豆包实测回答记录_初测.txt': 'slot_stage0_answers',
  '02_豆包实测回答': 'slot_stage0_answers',
  '02_豆包回答': 'slot_stage0_answers', // 阶段零历史生成回答前缀容错
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
 * 按阶段收窄有效采纳槽位白名单 (Fail-Closed 关闸保护)
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
 * 按阶段获取受系统终身保护的规范骨干文件名集合 (Fail-Closed 关闸保护)
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
  const escaped = prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`^${escaped}(\\d+)`, 'i');
}

/**
 * 规整版本标签，剥离 -Draft 标记 (优先从文件名反推数值版本)
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
 * 反向推导文件所属工序槽位 (带手建隔离与去重告警)
 * @param {string} filename
 * @param {'step0'|'step1'} stage
 * @param {boolean} [isManual=false]
 * @returns {string}
 */
const warnedSlotMisc = new Set();
export function resolveSlotKey(filename, stage, isManual = false) {
  if (!filename) return 'slot_misc';
  // 1. 手建文件短路隔离：不走前缀推导，防止笔记误判为工序槽位
  if (isManual) return 'slot_manual';

  const cleanName = filename.trim();
  const validSlots = getSlotsByStage(stage);

  // 2. 规范骨干精确命中
  for (const sk of validSlots) {
    if (CANONICAL_SLOT_DICT[sk]?.canonicalName === cleanName) return sk;
  }

  // 3. 别名容错表精确命中
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

  // 5. 未匹配到工序槽位：去重安全告警并归为统一杂项草稿常量
  if (!warnedSlotMisc.has(cleanName)) {
    warnedSlotMisc.add(cleanName);
    console.debug(`[studioArtifactConfig] 文件名未匹配到工序槽位字典: ${cleanName}，已安全归为 slot_misc 杂项草稿。`);
  }
  return 'slot_misc';
}

/**
 * 跨端安全的本地存储访问器 (环境探测 + 内存安全兜底)
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

/**
 * 版本号受控提取与防重名防覆盖算法
 * 重新生成时，扫描工作区全量文件（包含 isDeleted: true 在废纸篓中的文件）
 */
export function computeNextVersion(files = {}, slotKey) {
  const item = CANONICAL_SLOT_DICT[slotKey];
  if (!item) return { nextFileName: '', nextVersionTag: '', nextVer: 0 };

  // 排除手动新建草稿，防止手建笔记污染版本编号
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

/**
 * 历史淘汰旧版判定 (持久化标记优先 + 存量版本比对兜底)
 */
export function isHistoricalRetired(file, files = {}) {
  if (!file || !file.slotKey || file.isActive || file.isManual || file.slotKey === 'slot_manual') return false;
  // 1. 优先依据采纳动作退级时显式持久化的 isRetired 标记
  if (file.isRetired === true) return true;

  // 2. 存量老数据未持久化标记时的兜底推导：仅当同槽活跃版本的序号明确高于自身时才算淘汰
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

/**
 * 只读判定函数
 */
export function isReadOnlyFile(file, files = {}, stage = '') {
  if (!file) return false;
  // 1. 废纸篓必定只读
  if (Boolean(file.isDeleted || file.is_deleted)) return true;

  // 2. 首版母版留档文件：终身强制只读
  if (file.isProtectedArchive) return true;

  // 3. 规范主干镜像载体：若带有 isCanonicalMirror 标记，终身保持强制只读
  if (file.isCanonicalMirror) return true;

  // 4. 手建自定义文件：只要不在废纸篓，永远保持自由编辑打磨
  if (file.isManual || file.slotKey === 'slot_manual') return false;

  // 5. 属于某槽位的更旧被淘汰历史版本 (具备 isRetired: true)：强制只读
  if (!file.isActive && isHistoricalRetired(file, files)) {
    return true;
  }

  // 6. 当前生效底牌、最新候选工作草稿 (未采纳)、新建文件：完全可编辑打磨保存！
  return false;
}

/**
 * 删除按钮在左栏树中的渲染判定 (Fail-Closed 关闸保护)
 */
export function canDeleteFile(file, stage = '') {
  if (!file) return false;
  // ① 正在生效的底牌终身不可删
  if (file.isActive) return false;
  // ② 规范主干镜像载体终身不可删 (Fail-Closed 关闸保护)
  if (file.isCanonicalMirror) return false;
  // ③ 首版留档母版受系统终身保护不可删
  if (file.isProtectedArchive) return false;
  // ④ 全局所有工序槽位的规范骨干文件名一律终身不可删 (脱钩外部 stage)
  const allCanonicalNames = Object.values(CANONICAL_SLOT_DICT).map((item) => item.canonicalName);
  if (allCanonicalNames.includes(file.name)) return false;
  // ⑤ 手建草稿与杂项草稿只要不在废纸篓且非 active 即可删除
  if (file.isManual || file.slotKey === 'slot_manual' || file.slotKey === 'slot_misc') {
    return !Boolean(file.isDeleted || file.is_deleted);
  }
  // ⑥ 已经在废纸篓中的不可重复点删除
  if (Boolean(file.isDeleted || file.is_deleted)) return false;
  return true;
}

/**
 * 统一保存与单向主干镜像纯函数
 */
export function computeSaveResult({ targetName, content, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[targetName];
  if (!target) return { files, success: false, reason: 'FILE_NOT_FOUND' };

  // 入口只读自证守卫：只读文件拒绝保存修改
  if (isReadOnlyFile(target, files, stage)) {
    console.warn(`[computeSaveResult] 尝试保存只读文件 [${targetName}]，已被纯函数内部拦截！`);
    return { files, success: false, reason: 'READ_ONLY_LOCKED' };
  }

  const safeContent = content ?? '';
  const newFiles = { ...files };

  // 1. 更新目标文件自身工作区草稿
  newFiles[targetName] = {
    ...target,
    name: targetName,
    content: safeContent,
    savedContent: safeContent,
    isDirty: false,
    updatedAt: nowIso,
  };

  // 2. 活跃文件自动单向镜像契约 (带非空内容守卫)
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
    success: true,
  };
}

/**
 * 统一采纳互斥纯函数
 */
export function computeAdoptResult({ candidateName, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[candidateName];
  if (!target) {
    console.warn(`[computeAdoptResult] 候选采纳文件不存在: ${candidateName}`);
    return { files, success: false, reason: 'FILE_NOT_FOUND' };
  }

  const slotKey = target.slotKey || resolveSlotKey(candidateName, stage, target.isManual);

  // 1. 候选自身类型自证守卫：受限类型绝不可作为采纳候选，防自锁矛盾态
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

  // 2. 阶段合法性 Fail-Closed 关闸守卫
  const validSlots = getSlotsByStage(stage);
  if (!stage || validSlots.length === 0 || !validSlots.includes(slotKey)) {
    console.warn(`[computeAdoptResult] 目标槽位 [${slotKey}] 在当前阶段 [${stage}] 下无效或未指定阶段，Fail-Closed 拒绝采纳！`);
    return { files, success: false, reason: 'STAGE_SLOT_MISMATCH' };
  }

  // 3. 内容有效性守卫：严禁采纳空内容文件，防止单向镜像击穿清空规范主干
  const candidateValid = typeof target.content === 'string' && target.content.trim().length > 0;
  if (!candidateValid) {
    console.warn(`[computeAdoptResult] 候选版本 [${candidateName}] 内容为空或未就绪，拒绝采纳以保护规范主干！`);
    return { files, success: false, reason: 'EMPTY_CONTENT' };
  }

  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  const canonicalFile = canonicalName ? files[canonicalName] : null;

  // 4. 规整版本标签（剥离 -Draft，缺失优先从文件名反推）
  const adoptedVersionTag = normalizeVersionTag(target.versionTag, slotKey, candidateName);

  // 5. 首版留档保障：若当前生效的是规范骨干且首采纳新版本，留档 _第1版
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
        isCanonicalMirror: false, // 显式清除镜像标记，母版与镜像互斥！
        versionTag: `${slotItem.prefix}1`,
        isProtectedArchive: true, // 永久受保护不可删除、不可修改
      };
    }
  }

  // 6. 同 slotKey 其他文件全部退级并显式打上 isRetired 标记 (手建文件除外 · 带 resolveSlotKey 兜底)
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

  // 7. 候选草稿（或回滚的历史版本）升格为客户生效底牌
  newFiles[candidateName] = {
    ...target,
    name: candidateName,
    isActive: true,
    isRetired: false, // 恢复生效，解除淘汰
    versionTag: adoptedVersionTag,
    updatedAt: nowIso,
  };

  // 8. 单向镜像到规范主干 (受前面 candidateValid 守卫保护，且复位 isRetired)
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

  // 9. 自证单槽单一 active 不变量：若发现多 active 脏数据则 Fail-Closed 拒绝
  const activeCount = Object.values(newFiles).filter(
    (f) => (f.slotKey || resolveSlotKey(f.name, stage, f.isManual)) === slotKey && f.isActive === true && !f.isManual
  ).length;
  if (activeCount !== 1) {
    console.error(`[computeAdoptResult] 槽位 [${slotKey}] 采纳后活跃文件数自证失败(期望 1，实际 ${activeCount})，Fail-Closed 拒绝！`);
    return { files, success: false, reason: 'CONVERGENCE_VERIFICATION_FAILED' };
  }

  return {
    success: true,
    files: newFiles,
    slotKey,
    canonicalName,
    adoptedDraftName: candidateName,
    versionTag: adoptedVersionTag,
    updatedAt: nowIso,
  };
}

/**
 * 统一恢复纯函数
 */
export function computeRestoreResult({ filename, files, stage, nowIso = new Date().toISOString() }) {
  const target = files[filename];
  if (!target) return { success: false, reason: 'FILE_NOT_FOUND', files };

  const slotKey = target.slotKey || resolveSlotKey(filename, stage, target.isManual);
  const newFiles = { ...files };

  // 1. 移出废纸篓 (统一只写 isDeleted，确保 name 字段存在)
  const restoredItem = {
    ...target,
    name: filename,
    isDeleted: false,
    updatedAt: nowIso,
  };
  delete restoredItem.is_deleted;

  // 2. 受限文件恢复后强制保持草稿，绝不抢占工序活跃槽位
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
    // 升格为 active 时必须同步复位 isRetired，彻底杜绝 active + retired 矛盾态！
    restoredItem.isActive = true;
    restoredItem.isRetired = false;
  } else {
    // 严格保持 isActive: false，绝不抢占 active，绝对守住单槽单一 active 不变量！
    restoredItem.isActive = false;
  }

  newFiles[filename] = restoredItem;
  return { success: true, files: newFiles, restoredName: filename, updatedAt: nowIso };
}

/**
 * 统一软删除纯函数 (带前置守卫、Tab 规整与平滑选中回退)
 */
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

/**
 * 存量 localStorage 数据迁移与单槽 Active 强制收敛算法
 */
export function migrateAndNormalizeFiles(rawFiles = {}, stage, nowIso = new Date().toISOString()) {
  // 阶段缺失守卫：Fail-Closed 保护，原样返回存量数据，禁止破坏性回填 slot_misc！
  if (!stage) {
    console.warn('[migrateAndNormalizeFiles] 缺少 stage 阶段标识，Fail-Closed 安全关闸，原样返回存量数据！');
    return rawFiles;
  }

  const validSlots = getSlotsByStage(stage);
  const normalized = {};

  // 第一轮：硬约束不变式回填与 slotKey 规整
  for (const fn of Object.keys(rawFiles)) {
    const item = { ...rawFiles[fn] };

    // 【硬约束不变式】显式保证 item.name 等价于字典键名
    item.name = fn;

    // 1. 统一为 camelCase isDeleted 并显式解析字符串布尔
    const rawDel = item.isDeleted ?? item.is_deleted;
    item.isDeleted = rawDel === true || rawDel === 'true';
    delete item.is_deleted;

    // 废纸篓中的文件绝对不可处于 active 状态
    if (item.isDeleted) {
      item.isActive = false;
    }

    // 2. 回填槽位 slotKey (手建草稿保留 slot_manual，对存量未匹配或误标为 slot_misc 且非手建的允许重新解析)
    if (!item.slotKey || (item.slotKey === 'slot_misc' && !item.isManual)) {
      item.slotKey = resolveSlotKey(fn, stage, item.isManual);
    }

    // 3. 识别并回填首版母版留档标记
    if (fn.includes('_第1版')) {
      item.isProtectedArchive = true;
    }

    // 纠偏存量脏数据：母版与规范镜像终身受保护，绝不可处于已删除状态
    if (item.isProtectedArchive || item.isCanonicalMirror) {
      item.isDeleted = false;
    }

    // 4. 初始 versionTag (优先从文件名反推版本号)
    if (!item.versionTag) {
      const slotItem = CANONICAL_SLOT_DICT[item.slotKey];
      const prefix = slotItem?.prefix || 'V';
      const mVer = fn.match(/第(\d+)版/);
      item.versionTag = mVer ? `${prefix}${mVer[1]}` : `${prefix}1`;
    }

    // 5. 时间戳归一化为 ISO
    if (!item.generatedAt) {
      item.generatedAt = nowIso;
    } else {
      const parsed = Date.parse(item.generatedAt);
      item.generatedAt = !isNaN(parsed) ? new Date(parsed).toISOString() : nowIso;
    }

    normalized[fn] = item;
  }

  // 辅助提取版本数值
  const getVerNum = (f) => {
    const m = (f.name || '').match(/第(\d+)版/);
    if (m) return parseInt(m[1], 10);
    const m2 = (f.versionTag || '').match(/\d+/);
    if (m2) return parseInt(m2[0], 10);
    return 1;
  };

  // 第二轮：工序槽位 Active 强制收敛与存量 isRetired 回填
  for (const sk of validSlots) {
    // 过滤出该槽位下所有未删除且非手建的正式交付物
    const slotFiles = Object.values(normalized).filter(
      (f) => f.slotKey === sk && !f.isDeleted && !f.isManual
    );
    // 预过滤掉镜像与母版，防止错误将镜像固化为 active
    const activeList = slotFiles.filter((f) => f.isActive === true && !f.isCanonicalMirror && !f.isProtectedArchive);
    const canonicalName = CANONICAL_SLOT_DICT[sk]?.canonicalName;

    let chosen = null;
    if (activeList.length > 1) {
      // 存在多个 active 脏数据：按【最高版本 > 规范骨干 > 其余】显式排序选取唯一 active
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
      // 槽位无任何 active：激活规范骨干（若无骨干则激活首个非镜像、非母版的候选草稿）
      const candidateList = slotFiles.filter((f) => !f.isCanonicalMirror && !f.isProtectedArchive);
      chosen = slotFiles.find((f) => f.name === canonicalName) || candidateList[0] || slotFiles[0];
      chosen.isActive = true;
    }

    // 为老数据同槽已被淘汰的历史旧版补充 isRetired: true
    if (chosen) {
      for (const f of slotFiles) {
        // 显式豁免镜像与母版，不打淘汰标记
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

  // 收敛后终检：确保任何镜像文件绝不持有 isRetired 或 isActive
  for (const fn of Object.keys(normalized)) {
    if (normalized[fn].isCanonicalMirror) {
      normalized[fn].isRetired = false;
      normalized[fn].isActive = false;
    }
  }

  return normalized;
}

/**
 * 顶栏徽章文案格式化器 (严格对齐 AGENTS §3.3 / §3.5，0 Emoji，阶段条件化)
 * @param {Object} file
 * @param {string} stage
 * @returns {string}
 */
export function getActiveBadgeText(file, stage = '') {
  if (!file) return '';
  if (file.isActive) {
    if (stage === 'step0') {
      return `生效版本 ${file.versionTag || 'QA-V1'}`;
    }
    return `客户生效底牌 ${file.versionTag || 'V1'}`;
  }
  if (file.isProtectedArchive) return '历史母版 · 终身留档';
  if (file.isCanonicalMirror) return '规范主干 · 自动镜像';
  if (file.isRetired) return '历史版本 · 只读归档';
  if (file.isDeleted || file.is_deleted) return '废纸篓归档 · 只读状态';
  if (file.isManual || file.slotKey === 'slot_manual') return '自定义工作草稿';
  return `候选工作草稿 ${file.versionTag || 'Draft'}`;
}
