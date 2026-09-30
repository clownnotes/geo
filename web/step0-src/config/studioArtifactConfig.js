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

  // --- 阶段二（6个核心素材主文件） ---
  slot_stage2_s1: {
    canonicalName: 'S1_企业主体与法定边界.md',
    baseSlotName: 'S1_企业主体与法定边界',
    category: 'source_identity',
    stage: 'step2',
    prefix: 'S1.',
  },
  slot_stage2_s2: {
    canonicalName: 'S2_核心产品与价格承诺.md',
    baseSlotName: 'S2_核心产品与价格承诺',
    category: 'source_products',
    stage: 'step2',
    prefix: 'S2.',
  },
  slot_stage2_s3: {
    canonicalName: 'S3_目标客户与典型场景.md',
    baseSlotName: 'S3_目标客户与典型场景',
    category: 'source_scenarios',
    stage: 'step2',
    prefix: 'S3.',
  },
  slot_stage2_s4: {
    canonicalName: 'S4_对标竞品参数对比表_优搜网络.md',
    baseSlotName: 'S4_对标竞品参数对比表',
    category: 'source_competitors',
    stage: 'step2',
    prefix: 'S4.',
  },
  slot_stage2_s5: {
    canonicalName: 'S5_经典案例故事_本地实体GEO突围.md',
    baseSlotName: 'S5_经典案例故事',
    category: 'source_cases',
    stage: 'step2',
    prefix: 'S5.',
  },
  slot_stage2_s6: {
    canonicalName: 'S6_权威背书与资质凭据.md',
    baseSlotName: 'S6_权威背书与资质凭据',
    category: 'source_credentials',
    stage: 'step2',
    prefix: 'S6.',
  },

  // --- 阶段三（母盘与统一口径卡） ---
  slot_stage3_identity_card: {
    canonicalName: '01_主体信息统一口径卡.md',
    baseSlotName: '01_主体信息统一口径卡',
    category: 'identity_card',
    stage: 'step3',
    prefix: 'V',
  },
  slot_stage3_master: {
    canonicalName: '02_普林斯顿企业事实母盘.md',
    baseSlotName: '02_普林斯顿企业事实母盘',
    category: 'master_corpus',
    stage: 'step3',
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
  // 阶段二映射与前缀容错
  'S1_企业主体与法定边界.md': 'slot_stage2_s1',
  'S1_企业主体与法定边界': 'slot_stage2_s1',
  'S1_': 'slot_stage2_s1',
  'S2_核心产品与价格承诺.md': 'slot_stage2_s2',
  'S2_核心产品与价格承诺': 'slot_stage2_s2',
  'S2_': 'slot_stage2_s2',
  'S3_目标客户与典型场景.md': 'slot_stage2_s3',
  'S3_目标客户与典型场景': 'slot_stage2_s3',
  'S3_': 'slot_stage2_s3',
  'S4_对标竞品参数对比表_优搜网络.md': 'slot_stage2_s4',
  'S4_对标竞品参数对比表': 'slot_stage2_s4',
  'S4_': 'slot_stage2_s4',
  'S5_经典案例故事_本地实体GEO突围.md': 'slot_stage2_s5',
  'S5_经典案例故事': 'slot_stage2_s5',
  'S5_': 'slot_stage2_s5',
  'S6_权威背书与资质凭据.md': 'slot_stage2_s6',
  'S6_权威背书与资质凭据': 'slot_stage2_s6',
  'S6_': 'slot_stage2_s6',
  // 阶段三映射与前缀容错
  '01_主体信息统一口径卡.md': 'slot_stage3_identity_card',
  '01_主体信息统一口径卡': 'slot_stage3_identity_card',
  '02_普林斯顿企业事实母盘.md': 'slot_stage3_master',
  '02_普林斯顿企业事实母盘': 'slot_stage3_master',
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
export function normalizeVersionTag(tag = '', slotKey, filename = '') {
  // [2026-09-30] [解决 🟡1] 参考候选件（含 _参考 或 参考）直接保留原样标签，绝不篡改为 QA-V1
  if ((tag && tag.includes('参考')) || (filename && filename.includes('_参考'))) {
    return tag || '参考';
  }

  const item = CANONICAL_SLOT_DICT[slotKey];
  const prefix = item?.prefix || 'V';

  // 1. 优先从文件名中提取标准版本号（文件名是绝对真实凭据）
  if (filename) {
    const mChunk = filename.match(/_增补_1\.(\d+)/);
    if (mChunk && mChunk[1]) {
      return `${prefix}${mChunk[1]}`;
    }
    const mVer = filename.match(/_第(\d+(?:\.\d+)?)版/);
    if (mVer && mVer[1]) {
      return `${prefix}${mVer[1]}`;
    }
  }

  // 2. 从 tag 中安全提取：先剥离已有 prefix 与 Draft 标记，杜绝前缀二次拼接膨胀
  let cleanTag = (tag || '').replace(/-Draft$/i, '').trim();
  if (!cleanTag) return `${prefix}1`;

  if (cleanTag.startsWith(prefix)) {
    cleanTag = cleanTag.slice(prefix.length);
  } else if (/^S\d+\./i.test(cleanTag)) {
    cleanTag = cleanTag.replace(/^S\d+\./i, '');
  } else if (/^V/i.test(cleanTag)) {
    cleanTag = cleanTag.replace(/^V/i, '');
  }

  const mNum = cleanTag.match(/^(\d+(?:\.\d+)?)/);
  const num = mNum ? mNum[1] : '1';
  return `${prefix}${num}`;
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

  // 3. 别名容错表匹配 (精确命中 或 剥离版本后缀后命中 或 别名前缀匹配)
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

// [2026-09-30] [主文件雪花ID与去V1纯净改名] 生成雪花 ID、隐藏技术扩展名、计算用户纯净展示名称
let lastTimestamp = -1;
let snowflakeSequence = 0;

/**
 * 生成雪花 ID (Snowflake ID) 唯一编号
 * 符合 4.11 绝对禁止自增 ID 铁律，纯数字唯一标识
 */
export function generateSnowflakeId() {
  let timestamp = Date.now();
  if (timestamp === lastTimestamp) {
    snowflakeSequence = (snowflakeSequence + 1) & 4095;
    if (snowflakeSequence === 0) {
      while (timestamp <= lastTimestamp) {
        timestamp = Date.now();
      }
    }
  } else {
    snowflakeSequence = 0;
  }
  lastTimestamp = timestamp;
  const epoch = 1767225600000n; // 2026-01-01 起始纪元
  const tsDiff = BigInt(Math.max(0, timestamp - Number(epoch)));
  const workerId = 1n;
  const seqBig = BigInt(snowflakeSequence);
  const snowflake = (tsDiff << 22n) | (workerId << 12n) | seqBig;
  return snowflake.toString();
}

/**
 * 剥离技术扩展名 (.txt, .md, .json 等)
 * 界面彻底隐藏后缀，交付人员只看到纯净主名称
 */
export function stripExtension(fn) {
  if (!fn) return '';
  // [2026-09-30 修复R1] 仅剥离白名单技术扩展名，严禁截断 1.1 / V2.0 等小数点业务版本号
  return fn.replace(/\.(txt|md|markdown|json|html|htm|css|js|yaml|yml)$/i, '');
}

/**
 * 格式化文件名展示：剥离冗余的数字序号前缀 (如 01_、02_)，并将 第N版 转为极简 VN 短标
 * 示例：01_豆包实测提问清单_第1版.txt → 豆包实测提问清单_V1.txt
 */
export function formatDisplayName(fn) {
  if (!fn) return '';
  return fn
    .replace(/^(?:\d+|S\d+)_/g, '')
    .replace(/_第(\d+(?:\.\d+)?)版/g, '_V$1')
    .replace(/_增补_1\.(\d+)/g, '_增补_V1.$1');
}

/**
 * 格式化纯净展示标题 (不含扩展名)
 * 优先读取用户人工修改的 displayName，其次使用原生名称清洗并隐藏后缀
 */
export function formatDisplayTitle(fn, fileObj = null) {
  if (!fn) return '';
  if (fileObj && fileObj.displayName) {
    return stripExtension(fileObj.displayName);
  }
  return stripExtension(formatDisplayName(fn));
}

/**
 * 校验文件名在工作区是否重名 (忽略已删除文件，对比去除扩展名后的纯净标题)
 * 供 StudioFileTree 与各阶段 App 共享使用，确保单一定义 (SSOT)
 */
export function isDuplicateDisplayName(files = {}, currentFn = '', newName = '') {
  const trimmed = (newName || '').trim().toLowerCase();
  if (!trimmed) return false;
  return Object.keys(files || {}).some((fn) => {
    if (fn === currentFn) return false;
    if (files[fn]?.isDeleted || files[fn]?.is_deleted) return false;
    const title = formatDisplayTitle(fn, files[fn]).toLowerCase();
    return title === trimmed;
  });
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
 * 分支灵感草稿版本生成算法 (如 V3 → V3.1)
 * [2026-09-29] 允许在现有主版本基础上派生临时灵感分支，便于挑词合入主版本后清理
 * @param {Object} files
 * @param {string} baseFilename
 * @param {string} slotKey
 */
export function computeBranchVersion(files = {}, baseFilename, slotKey) {
  const item = CANONICAL_SLOT_DICT[slotKey];
  if (!item || !baseFilename) return { nextFileName: '', nextVersionTag: '', majorNum: '1', nextBranch: 1 };

  const baseFile = files[baseFilename];
  let majorNum = '1';
  if (baseFile?.versionTag) {
    const mTag = baseFile.versionTag.match(/(\d+)/);
    if (mTag) majorNum = mTag[1];
  } else {
    const mName = baseFilename.match(/第(\d+)版/);
    if (mName) majorNum = mName[1];
  }

  const slotFiles = Object.values(files).filter((f) => f.slotKey === slotKey && !f.isManual);
  const branchNums = [];
  const branchRegex = new RegExp(`第${majorNum}\\.(\\d+)版`);
  const tagBranchRegex = new RegExp(`${item.prefix}${majorNum}\\.(\\d+)`);

  for (const f of slotFiles) {
    const mb1 = (f.name || '').match(branchRegex);
    if (mb1 && mb1[1]) branchNums.push(parseInt(mb1[1], 10));
    const mb2 = (f.versionTag || '').match(tagBranchRegex);
    if (mb2 && mb2[1]) branchNums.push(parseInt(mb2[1], 10));
  }

  const nextBranch = branchNums.length > 0 ? Math.max(...branchNums) + 1 : 1;
  const ext = (item.canonicalName.split('.').pop()) || 'md';
  const nextFileName = `${item.baseSlotName}_第${majorNum}.${nextBranch}版.${ext}`;
  const nextVersionTag = `${item.prefix}${majorNum}.${nextBranch}-Draft`;

  return { nextFileName, nextVersionTag, majorNum, nextBranch };
}

/**
 * 阶段二增量分片版本计算函数 (S1~S6)
 * [2026-09-30] 师弟定规：每个分类只有 1 个主文件，盖板内确认切片时，单调递增派生 1.1, 1.2 独立增补卡片
 * @param {Object} files
 * @param {string} targetSlotKey (如 'slot_stage2_s2')
 * @returns {{ nextFileName: string, nextVersionTag: string, nextBranch: number, category: string, slotKey: string }}
 */
export function computeStage2ChunkVersion(files = {}, targetSlotKey) {
  const item = CANONICAL_SLOT_DICT[targetSlotKey];
  if (!item) return null;

  const slotFiles = Object.values(files).filter(
    (f) => (f.slotKey === targetSlotKey || resolveSlotKey(f.name, 'step2', f.isManual) === targetSlotKey)
  );

  const branchNums = [];
  const branchRegex = /_增补_1\.(\d+)/;
  for (const f of slotFiles) {
    // [2026-09-30] 核心守卫 (解决 🔴2): 排除主文件，主文件不是增量分片，绝不误计入分支
    if (isMasterSourceFile(f.name)) continue;

    const m = (f.name || '').match(branchRegex);
    if (m && m[1]) branchNums.push(parseInt(m[1], 10));

    // tag 精准匹配：剥离 item.prefix 后提取纯数字分支号
    if (f.versionTag && f.versionTag.startsWith(item.prefix)) {
      const tagBranch = f.versionTag.slice(item.prefix.length).replace(/-Draft$/i, '');
      const parsed = parseInt(tagBranch, 10);
      if (Number.isFinite(parsed)) branchNums.push(parsed);
    }
  }

  const validBranches = branchNums.filter(Number.isFinite);
  const maxBranch = validBranches.length > 0 ? Math.max(...validBranches) : 0;
  const nextBranch = maxBranch + 1;

  const ext = (item.canonicalName.split('.').pop()) || 'md';
  const nextFileName = `${item.baseSlotName}_增补_1.${nextBranch}.${ext}`;
  const nextVersionTag = `${item.prefix}${nextBranch}`;

  return {
    nextFileName,
    nextVersionTag,
    nextBranch,
    category: item.category,
    slotKey: targetSlotKey,
  };
}

/**
 * 识别是否为 S 素材库的主版本标准文件 (S1, S2, S3, S4_xxx, 排除 S1.1, S1.2 等草稿分支)
 * [2026-09-29] 人机两分契约：系统组装母盘与外部喂 AI 时，只读取消费 S 主版本
 * @param {string} filename
 * @returns {boolean}
 */
export function isMasterSourceFile(filename = '') {
  if (!filename) return false;
  const base = filename.replace(/\.[^.]+$/, '');
  // [2026-09-30] 人机两分核心契约：增补切片 (含 _增补_ 或 .x 编号) 绝对属于 1.x 人机增量，不得视为主文件
  if (/_增补_/i.test(base) || /\d+\.\d+/.test(base)) return false;
  return /^S\d+(_|$)/i.test(base);
}

/**
 * 过滤出仅供 AI/母盘消费的素材库主版本标准文件 (人机两分契约)
 * @param {Object} files
 * @returns {Object}
 */
export function filterMasterSourceFiles(files = {}) {
  const result = {};
  for (const [fn, file] of Object.entries(files)) {
    if (file && !file.isDeleted && !file.is_deleted && isMasterSourceFile(fn)) {
      result[fn] = file;
    }
  }
  return result;
}

/**
 * 历史淘汰旧版判定 (持久化标记优先 + 存量版本比对兜底)
 */
export function isHistoricalRetired(file, files = {}) {
  if (!file || !file.slotKey || file.isActive || file.isManual || file.slotKey === 'slot_manual') return false;
  // [2026-09-29] 灵感分支草稿（如 V1.1, S1.1）可自由打磨，绝不误判为历史淘汰
  if (file.isBranchDraft) return false;
  // 1. 优先依据采纳动作退级时显式持久化的 isRetired 标记
  if (file.isRetired === true) return true;

  // 2. 存量老数据未持久化标记时的兜底推导：仅当同槽活跃版本的序号明确高于自身时才算淘汰
  const activeBrother = Object.values(files).find(
    (f) => f.slotKey === file.slotKey && f.isActive === true && f.name !== file.name && !f.isManual
  );
  if (activeBrother) {
    const mSelf = (file.name || '').match(/第(\d+(?:\.\d+)?)版/);
    const mActive = (activeBrother.name || '').match(/第(\d+(?:\.\d+)?)版/);
    if (mSelf && mActive) {
      const parts1 = String(mSelf[1]).split('.').map((n) => parseInt(n, 10) || 0);
      const parts2 = String(mActive[1]).split('.').map((n) => parseInt(n, 10) || 0);
      const maxLen = Math.max(parts1.length, parts2.length);
      for (let i = 0; i < maxLen; i++) {
        const p1 = parts1[i] || 0;
        const p2 = parts2[i] || 0;
        if (p1 < p2) return true;
        if (p1 > p2) return false;
      }
    }
  }
  return false;
}

/**
 * 只读判定函数
 * [2026-09-30 师弟立规 · 裁决11] 彻底解绑非主文件的生硬只读限制！
 * 全系统除移入废纸篓 (isDeleted === true) 的文件强制只读外，
 * 所有主文件、参考候选件、历史归档件、草稿全域开放自由输入编辑打磨与存盘！
 */
export function isReadOnlyFile(file, files = {}, stage = '') {
  if (!file) return false;
  // 1. 废纸篓必定只读
  if (Boolean(file.isDeleted || file.is_deleted)) return true;

  // 2. [2026-09-30 裁决11] 其他所有主文件、参考件、历史母版、草稿全域可自由编辑打磨
  return false;
}

/**
 * 判定文件是否为主文件 (Master File)
 * [2026-09-30 师弟立规] 主文件只能修改保存，物理锁定禁止删除！
 * [2026-09-30 修复🔴4] 严密排除镜像、留档、已淘汰版本及参考件，保证单槽唯一真相源
 */
export function isMasterFile(file) {
  if (!file) return false;
  // 显式排除参考件、废纸篓、骨干镜像、留档与已淘汰版本
  if (file.isReference === true || file.isDeleted === true || file.is_deleted === true) return false;
  if (file.isCanonicalMirror === true || file.isProtectedArchive === true || file.isRetired === true) return false;
  const vTag = String(file.versionTag || '');
  if (vTag.startsWith('参考') || (file.name && file.name.includes('_参考'))) return false;

  // 1. 显式打标为 Master
  if (file.isMaster === true) return true;
  if (file.isMaster === false) return false;

  // 2. 活跃生效且非手工无归属草稿
  if (file.isActive === true && !file.isManual) return true;

  // 3. 初始预置规范槽位骨干文件（在未被标记为非 active / 未被退役时生效）
  const allCanonicalNames = Object.values(CANONICAL_SLOT_DICT).map((item) => item.canonicalName);
  if (allCanonicalNames.includes(file.name) && file.isActive !== false) {
    return true;
  }
  return false;
}

/**
 * 重新生成文件的命名与版本计算纯函数
 * [2026-09-30 师弟立规] 废除 1.1/1.2，生成参考件时按主题命名，同名多次生成后缀加数字 1, 2, 3...
 * @param {Object} files
 * @param {string} slotKey
 * @param {string} topic 主题标识 (默认 '参考')
 */
export function computeReferenceVersion(files = {}, slotKey, topic = '参考') {
  const item = CANONICAL_SLOT_DICT[slotKey];
  if (!item) return null;

  const slotFiles = Object.values(files).filter(
    (f) => (f.slotKey === slotKey || resolveSlotKey(f.name, item.stage, f.isManual) === slotKey)
  );

  const nums = [];
  const refRegex = new RegExp(`_${topic}(\\d+)`);
  for (const f of slotFiles) {
    if (f.isMaster) continue;
    const m = (f.name || '').match(refRegex);
    if (m && m[1]) nums.push(parseInt(m[1], 10));
  }

  const nextNum = nums.length > 0 ? Math.max(...nums) + 1 : 1;
  const ext = (item.canonicalName.split('.').pop()) || 'txt';
  const nextFileName = `${item.baseSlotName}_${topic}${nextNum}.${ext}`;
  const nextVersionTag = `${topic}${nextNum}`;

  return { nextFileName, nextVersionTag, nextNum, item };
}

/**
 * 获取某个槽位的主文件
 * [2026-09-30 修复🔴4] 优先级收敛，确保单槽 Master 解析确定且唯一
 */
export function getMasterFileForSlot(files = {}, slotKey) {
  if (!slotKey) return null;
  const list = Object.values(files);
  // 1. 优先寻找明确打标 isMaster === true 的生效文件
  const explicitMaster = list.find((f) => f.slotKey === slotKey && f.isMaster === true && !f.isDeleted);
  if (explicitMaster) return explicitMaster;

  // 2. 寻找该槽位当前唯一的活跃生效主版本（排除镜像与归档）
  const activeMaster = list.find(
    (f) => f.slotKey === slotKey && f.isActive === true && !f.isCanonicalMirror && !f.isProtectedArchive && !f.isDeleted
  );
  if (activeMaster) return activeMaster;

  // 3. 寻找匹配 canonicalName 且满足 isMasterFile 的初始文件
  const item = CANONICAL_SLOT_DICT[slotKey];
  if (item && files[item.canonicalName] && isMasterFile(files[item.canonicalName])) {
    return files[item.canonicalName];
  }
  return null;
}

/**
 * 空模板哨兵常量列表 (SSOT 唯一真相源 · 解决 🔴2)
 * 用于统一判定文件是否脱离了初始占位提示
 */
export const TEMPLATE_SENTINEL_SNIPPETS = [
  '说明：复制上方题目',
  '说明：实测完成，回答已暂存',
  '待实测填入：请前往豆包网页版提问',
  '请在左侧选择文件或开始输入',
  '当前文件暂无内容',
  '在此开始编写内容',
];

// [2026-09-30] [SSOT收敛] 主文件有效内容最小字符数常量
export const MIN_MASTER_CONTENT_LENGTH = 50;

/**
 * 标准 5 点核心质检模型
 * 判定主文件是否真正就绪，供全流水线门禁和指示灯消费
 */
export function evaluate5PointCheck(masterFile, projectData = {}, options = {}) {
  const minLength = options.minLength || MIN_MASTER_CONTENT_LENGTH;
  const content = (masterFile && masterFile.content) || '';

  // 1. 主文件存在
  const point1 = {
    key: 'point_exists',
    name: '主文件存在',
    pass: Boolean(masterFile && masterFile.name),
    msg: masterFile ? '主文件底牌已就绪' : '主文件缺失',
  };

  // 2. 脱离初始空模版 (复用 TEMPLATE_SENTINEL_SNIPPETS 统一常量)
  const hasTemplateSnippet = TEMPLATE_SENTINEL_SNIPPETS.some((s) => content.includes(s));
  const point2 = {
    key: 'point_not_template',
    name: '脱离初始空模版',
    pass: Boolean(content.trim() && !hasTemplateSnippet),
    msg: !hasTemplateSnippet ? '已填写真实业务内容' : '仍包含初始待填说明模版',
  };

  // 3. 真实字数达标
  const charCount = Array.from(content.trim()).length;
  const point3 = {
    key: 'point_length',
    name: '真实字数达标',
    pass: charCount >= minLength,
    msg: charCount >= minLength ? `字数充足 (${charCount}/${minLength}字)` : `字数不足 (${charCount}/${minLength}字)`,
  };

  // 4. 消歧四要素齐备 (品牌名、企业主体名、统一社会信用代码、核心官网 · 解决 🔴2)
  const brand = (projectData.brand_name || projectData.client_name || '').trim();
  const company = (projectData.company_name || projectData.company || '').trim();
  const creditCode = (projectData.credit_code || projectData.tax_id || '').trim();
  const url = (projectData.official_url || projectData.site || '').trim();

  const missingElements = [];
  if (!brand || !content.includes(brand)) missingElements.push(`品牌名[${brand || '未设定'}]`);
  if (!company || !content.includes(company)) missingElements.push(`企业主体[${company || '未设定'}]`);
  if (!creditCode || !content.includes(creditCode)) missingElements.push(`统一代码[${creditCode || '未设定'}]`);
  const domain = extractDomain(url);
  if (!url || (!content.includes(url) && (!domain || !content.includes(domain)))) {
    missingElements.push(`核心官网[${url || '未设定'}]`);
  }

  const passElements = missingElements.length === 0;
  const point4 = {
    key: 'point_elements',
    name: '消歧四要素齐备',
    pass: passElements,
    msg: passElements ? '四要素要素齐备一致' : `缺少消歧要素: ${missingElements.join('、')}`,
    missingElements,
  };

  // 5. 人工标记确认就绪
  const point5 = {
    key: 'point_confirmed',
    name: '人工确认就绪',
    pass: Boolean(masterFile && (masterFile.isConfirmed || masterFile.isReady || masterFile.isActive)),
    msg: masterFile && (masterFile.isConfirmed || masterFile.isActive) ? '交付人员已确认就绪' : '待人工确认就绪',
  };

  const points = [point1, point2, point3, point4, point5];
  const ready = points.every((p) => p.pass);
  return { ready, points };
}

/**
 * 删除按钮在左栏树中的渲染判定 (Fail-Closed 关闸保护)
 */
export function canDeleteFile(file, stage = '') {
  // [Fail-Closed 关闸保护 · 解决 🔴3]: 空引用一律拒绝删除，杜绝 TypeError 崩溃
  if (!file || !file.name) return false;
  // [2026-09-30 师弟立规 · 主文件神圣不可删] 主文件终身物理锁定禁止删除！只能修改保存！
  if (isMasterFile(file)) return false;
  // ① 阶段二 S1~S6 规范主版本文件受系统终身保护不可删；增补分片与草稿允许删入废纸篓
  if (isMasterSourceFile(file.name)) return false;
  // ② 正在生效的底牌/版本终身不可删
  if (file.isActive) return false;
  // ③ 规范主干镜像载体终身不可删 (Fail-Closed 关闸保护)
  if (file.isCanonicalMirror) return false;
  // ④ 首版留档母版受系统终身保护不可删
  if (file.isProtectedArchive) return false;
  // ⑤ 全局所有工序槽位的规范骨干文件名一律终身不可删 (脱钩外部 stage)
  const allCanonicalNames = Object.values(CANONICAL_SLOT_DICT).map((item) => item.canonicalName);
  if (allCanonicalNames.includes(file.name)) return false;
  // ⑥ 手建草稿与杂项草稿只要不在废纸篓且非 active 即可删除 (解决 🟡3：优先统一 resolveSlotKey)
  const resolvedSlot = file.slotKey || resolveSlotKey(file.name, stage, file.isManual);
  if (file.isManual || resolvedSlot === 'slot_manual' || resolvedSlot === 'slot_misc') {
    return !Boolean(file.isDeleted || file.is_deleted);
  }
  // ⑦ 已经在废纸篓中的不可重复点删除
  if (Boolean(file.isDeleted || file.is_deleted)) return false;
  // ⑧ 阶段白名单与槽位 Fail-Closed 保护：只有明确归属于支持槽位的草稿版本才允许删除
  if (!CANONICAL_SLOT_DICT[resolvedSlot]) return false;
  if (stage && CANONICAL_SLOT_DICT[resolvedSlot].stage !== stage) return false;

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

  if (content === undefined) {
    console.warn(`[computeSaveResult] 缺少保存内容`);
    return { files, success: false, reason: 'MISSING_CONTENT' };
  }

  const safeContent = content;
  const slotKey = target.slotKey || resolveSlotKey(targetName, stage, target.isManual);
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;
  const hasValidContent = typeof safeContent === 'string' && safeContent.trim().length > 0;

  // 活跃生效底牌/规范骨干严禁保存空内容，防止数据洗白与底牌骨干分叉 (彻底解决 🔴2)
  if (target.isActive && !hasValidContent) {
    console.warn(`[computeSaveResult] 尝试用空内容保存生效底牌 [${targetName}]，已被安全拦截！`);
    return { files, success: false, reason: 'EMPTY_CONTENT' };
  }

  const newFiles = { ...files };

  // 1. 更新目标文件自身工作区草稿 (显式持久化 slotKey 回填)
  newFiles[targetName] = {
    ...target,
    name: targetName,
    slotKey,
    content: safeContent,
    savedContent: safeContent,
    isDirty: false,
    updatedAt: nowIso,
  };

  // 2. 活跃文件自动单向镜像契约 (带非空内容守卫)
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
  const slotItem = CANONICAL_SLOT_DICT[slotKey];
  const canonicalName = slotItem?.canonicalName;

  // 1. 候选自身类型自证守卫：受限类型（规范镜像/手建草稿/杂项草稿/规范骨干自身）不可作为核心采纳候选
  // [2026-09-29] [解除母版采纳死锁] 允许 isProtectedArchive 母版作为采纳候选，支持一键回滚生效
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
        slotKey,
        isActive: false,
        isRetired: true, // 首版母版留档作为历史版本归档 (与迁移算法及断言 5 严格对齐)
        isCanonicalMirror: false, // 显式清除镜像标记，母版与镜像互斥！
        versionTag: `${slotItem.prefix}1`,
        isProtectedArchive: true, // 永久受保护不可删除、不可修改
      };
    }
  }

  // 6. 同 slotKey 其他文件全部退级并显式打上 isRetired 标记 (豁免规范骨干镜像与手建文件)
  for (const fn of Object.keys(newFiles)) {
    const sibSlot = newFiles[fn].slotKey || resolveSlotKey(fn, stage, newFiles[fn].isManual);
    if (sibSlot === slotKey && !newFiles[fn].isManual && fn !== candidateName) {
      const isCanonical = Boolean(fn === canonicalName || newFiles[fn].isCanonicalMirror || newFiles[fn].isBranchDraft);
      newFiles[fn] = {
        ...newFiles[fn],
        slotKey,
        isActive: false,
        isRetired: isCanonical ? false : true,
      };
    }
  }

  // 7. 候选草稿（或回滚的历史版本）升格为客户生效底牌
  newFiles[candidateName] = {
    ...target,
    name: candidateName,
    slotKey,
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
      slotKey,
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

  // 1. 移出废纸篓 (统一只写 isDeleted，确保 name 字段存在，回填 slotKey)
  const restoredItem = {
    ...target,
    name: filename,
    slotKey,
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

  // 2. 标记软删除 (统一只写 isDeleted，强制失活 isActive，彻底清理 is_deleted，回填 slotKey)
  newFiles[filename] = {
    ...target,
    name: filename,
    slotKey,
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

    // 2. 回填槽位 slotKey 与手建归一化 (解决 🟡1 & 🟡2)
    if (item.isManual) {
      item.slotKey = 'slot_manual';
    } else if (!item.slotKey || item.slotKey === 'slot_misc') {
      item.slotKey = resolveSlotKey(fn, stage, false);
    } else if (!validSlots.includes(item.slotKey)) {
      // 跨阶段非法槽位纠偏为 slot_misc 并强制失活 (解决 🟡1)
      item.slotKey = 'slot_misc';
      item.isActive = false;
    }

    // 3. 识别并回填首版母版留档标记 (收紧为仅核心槽位标准母版打标，杜绝污染手建笔记 · 解决 🟡4)
    if (
      !item.isManual &&
      item.slotKey !== 'slot_manual' &&
      item.slotKey !== 'slot_misc' &&
      validSlots.includes(item.slotKey)
    ) {
      const slotDef = CANONICAL_SLOT_DICT[item.slotKey];
      if (slotDef?.baseSlotName && fn.startsWith(`${slotDef.baseSlotName}_第1版`)) {
        item.isProtectedArchive = true;
      }
    }

    // 纠偏存量脏数据：母版与规范镜像终身受保护，绝不可处于已删除状态
    if (item.isProtectedArchive || item.isCanonicalMirror) {
      item.isDeleted = false;
    }

    // 4. versionTag 归一化 (解决 🔴4: 前缀与数值一致性归一)
    if (item.versionTag && item.slotKey && item.slotKey !== 'slot_manual' && item.slotKey !== 'slot_misc') {
      const isDraft = /-Draft$/i.test(item.versionTag);
      const clean = normalizeVersionTag(item.versionTag, item.slotKey, fn);
      item.versionTag = isDraft ? `${clean}-Draft` : clean;
    } else if (!item.versionTag) {
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

  // 辅助提取版本数值（支持浮点型微调分支，如 1.1）
  const getVerNum = (f) => {
    const m = (f.name || '').match(/第(\d+(\.\d+)?)版/);
    if (m) return parseFloat(m[1]);
    const m2 = (f.versionTag || '').match(/\d+(\.\d+)?/);
    if (m2) return parseFloat(m2[0]);
    return 1;
  };

  // 第二轮：工序槽位 Active 强制收敛与存量 isRetired 回填
  for (const sk of validSlots) {
    // 过滤出该槽位下所有未删除且非手建的正式交付物
    const slotFiles = Object.values(normalized).filter(
      (f) => f.slotKey === sk && !f.isDeleted && !f.isManual
    );
    // 预过滤掉镜像，允许合法处于 active 的母版参与收敛 (解决 🔴-1)
    const activeList = slotFiles.filter((f) => f.isActive === true && !f.isCanonicalMirror);
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
      // 槽位无任何 active：优先激活非镜像候选草稿中最高版本的草稿，若无草稿且规范骨干非镜像，则激活规范骨干
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

    // 若非骨干被激活，同步确保规范骨干打上镜像标记并等价同步 content，杜绝骨干落入可改半保护态或镜像失步 (解决 🔴-1)
    if (chosen && chosen.name !== canonicalName) {
      const canonical = slotFiles.find((f) => f.name === canonicalName);
      if (canonical) {
        canonical.isCanonicalMirror = true;
        canonical.isActive = false;
        canonical.isRetired = false;
        if (chosen.content && chosen.content.trim().length > 0) {
          canonical.content = chosen.content;
        }
      }
    }

    // 为老数据同槽已被淘汰的历史旧版补充 isRetired: true
    if (chosen) {
      for (const f of slotFiles) {
        // 当前生效的唯一活跃文件绝对不打淘汰标记 (解决 🔴-1)
        if (f.name === chosen.name || f.isActive) {
          f.isRetired = false;
          continue;
        }
        // 显式豁免规范骨干与镜像，绝对不打淘汰标记
        if (f.isCanonicalMirror || f.name === canonicalName) {
          f.isRetired = false;
          continue;
        }
        // 显式豁免分支微调草稿 (isBranchDraft)，分支可自由打磨，绝对不打淘汰标！(解决 🟡3)
        if (f.isBranchDraft) {
          f.isRetired = false;
          continue;
        }
        // 未生效的历史母版留档打上 isRetired
        if (f.isProtectedArchive) {
          f.isRetired = true;
          continue;
        }
        if (!f.isActive) {
          // 仅当版本严格低于当前活跃版本时才回填 isRetired，绝不误伤最新未采纳草稿！
          if (getVerNum(f) < getVerNum(chosen)) {
            f.isRetired = true;
          }
        }
      }
    }
  }

  // 收敛后终检：
  // 1. 确保任何镜像文件绝不持有 isRetired 或 isActive
  // 2. 确保规范骨干终身不打 isRetired 淘汰标记
  // 3. 确保非本阶段有效工序槽位 (slot_misc, slot_manual 或跨阶段槽位) 的文件绝不持有 isActive = true
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

/**
 * 顶栏徽章文案格式化器 (严格对齐 AGENTS §3.3 / §3.5，0 Emoji，阶段条件化)
 * @param {Object} file
 * @param {string} stage
 * @returns {string}
 */
export function getActiveBadgeText(file, stage = '') {
  if (!file) return '';
  if (stage === 'step2' || file.category?.startsWith('source_')) {
    return file.dir ? file.dir.split('(')[0].trim() : '素材档案';
  }
  if (file.isActive) {
    if (stage === 'step0') {
      return `生效版本 ${file.versionTag || 'QA-V1'}`;
    }
    return `客户生效底牌 ${file.versionTag || 'V1'}`;
  }
  if (file.isProtectedArchive) return '第 1 版 (原始母版)';
  if (file.isCanonicalMirror) return '规范主干 · 自动镜像';
  if (file.isRetired) return '历史版本 · 只读归档';
  if (file.isDeleted || file.is_deleted) return '废纸篓归档 · 只读状态';
  if (file.isManual || file.slotKey === 'slot_manual') return '自定义工作草稿';
  return `候选工作草稿 ${file.versionTag || 'Draft'}`;
}

/**
 * 统一纯函数错误原因平实中文映射器 (解决 🟡4)
 * @param {string} reason
 * @returns {string}
 */
export function formatReason(reason) {
  const map = {
    EMPTY_CONTENT: '内容为空，无法操作！请先编写或贴入内容',
    FILE_NOT_FOUND: '未找到指定文件',
    NOT_ADOPTABLE_TARGET: '该文件属于受保护类型，无法设为生效版本',
    STAGE_SLOT_MISMATCH: '当前阶段槽位不匹配，无法采纳',
    READ_ONLY_LOCKED: '该文件为只读状态，无法修改保存',
    FILE_PROTECTED_CANNOT_DELETE: '系统核心文件终身受保护，禁止删除',
    MISSING_CONTENT: '缺少保存内容',
    CONVERGENCE_VERIFICATION_FAILED: '单槽生效收敛校验失败，操作已取消',
  };
  return map[reason] || `操作失败，请刷新后重试（排查码: ${reason}）`;
}

/**
 * 智能 Tab 栈管理（首置插入与上限 6 个智能淘汰 · 师弟立规）
 * @param {string[]} openTabs 当前打开的标签数组
 * @param {string} fileName 要激活/打开的目标文件名
 * @param {Record<string, any>} files 文件字典
 * @param {number} [maxTabs=6] 最大标签数量上限
 * @returns {{ newOpenTabs: string[], activeFileName: string, warningDirty: boolean, dirtyFileNames: string[] }}
 */
export function activateTabInStack(openTabs = [], fileName, files = {}, maxTabs = 6) {
  if (!fileName) {
    return {
      newOpenTabs: Array.isArray(openTabs) ? [...openTabs] : [],
      activeFileName: (openTabs && openTabs[0]) || '',
      warningDirty: false,
      dirtyFileNames: [],
    };
  }

  const currentTabs = Array.isArray(openTabs) ? [...openTabs] : [];
  // 1. 若已存在则先剔除旧位置，重新首置插入到第 1 个位置 (索引 0)
  const filtered = currentTabs.filter((fn) => fn !== fileName);
  filtered.unshift(fileName);

  // 2. 超量淘汰检查
  let warningDirty = false;
  let dirtyFileNames = [];

  while (filtered.length > maxTabs) {
    // 从最右侧（最老末尾）向前寻找未修改的干净 Tab 自动关闭
    let cleanIdx = -1;
    for (let i = filtered.length - 1; i >= 0; i--) {
      const fn = filtered[i];
      if (fn === fileName) continue; // 刚激活的当前文件绝不淘汰
      const file = files[fn];
      if (!file || !file.isDirty) {
        cleanIdx = i;
        break;
      }
    }

    if (cleanIdx !== -1) {
      filtered.splice(cleanIdx, 1);
    } else {
      // 候选待淘汰的 Tab 全部有未保存修改，拒绝静默关闭，标记警告并保持 openTabs 严控在上限内 (解决 🟡4)
      warningDirty = true;
      dirtyFileNames = filtered.filter((fn) => fn !== fileName && files[fn]?.isDirty);
      filtered.shift(); // 撤销新加入的标签，确保 newOpenTabs 数量严格 <= maxTabs
      break;
    }
  }

  return {
    newOpenTabs: filtered,
    activeFileName: fileName,
    warningDirty,
    dirtyFileNames,
  };
}

/**
 * [2026-09-30] [官网网址真相源] 将用户输入的任意 URL 规范化为干净、唯一的完整网址
 * 1. 自动彻底消除 https://https:// 等重复前缀
 * 2. 补齐缺省的协议（若无 http/https 则补齐 https://）
 * 3. 移除末尾多余斜杠
 */
export function normalizeOfficialUrl(raw) {
  if (!raw || typeof raw !== 'string') return '';
  let u = raw.trim();
  if (!u) return '';
  // 消除所有连续的协议重复，比如 https://https://、http://https://
  u = u.replace(/^(https?:\/\/)+/gi, (match) => {
    return match.toLowerCase().startsWith('http://') && !match.toLowerCase().includes('https://') ? 'http://' : 'https://';
  });
  if (!/^https?:\/\//i.test(u)) {
    u = 'https://' + u;
  }
  // 去除多余的尾部斜杠
  u = u.replace(/(https?:\/\/[^\/]+)\/+$/, '$1');
  return u;
}

/**
 * [2026-09-30] 从规范网址中提取干净的主机名/域名 (如 www.baicl.cc)
 */
export function extractDomain(raw) {
  const norm = normalizeOfficialUrl(raw);
  if (!norm) return '';
  try {
    const urlObj = new URL(norm);
    return urlObj.hostname;
  } catch (_) {
    return norm.replace(/^https?:\/\//i, '').split('/')[0] || '';
  }
}

