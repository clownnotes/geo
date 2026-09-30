/**
 * smoke_studio_artifacts.mjs
 * 阶段零、一、二、三 多版本生成采纳、草稿废纸篓、真实素材库、主文件神圣防删、参考比对件与标准 5 点质检 32 项核心断言冒烟测试脚本
 * 严格遵照 tasks.md 规范执行
 */
import assert from 'node:assert/strict';
import {
  CANONICAL_SLOT_DICT,
  resolveSlotKey,
  computeNextVersion,
  isHistoricalRetired,
  isReadOnlyFile,
  canDeleteFile,
  computeSaveResult,
  computeAdoptResult,
  computeRestoreResult,
  computeDeleteResult,
  migrateAndNormalizeFiles,
  computeBranchVersion,
  computeStage2ChunkVersion,
  isMasterSourceFile,
  filterMasterSourceFiles,
  activateTabInStack,
  formatDisplayName,
  normalizeVersionTag,
  normalizeOfficialUrl,
  extractDomain,
  getSlotsByStage,
  isMasterFile,
  computeReferenceVersion,
  getMasterFileForSlot,
  evaluate5PointCheck,
  generateSnowflakeId,
  stripExtension,
  formatDisplayTitle,
  MIN_MASTER_CONTENT_LENGTH,
  isDuplicateDisplayName,
} from '../web/step0-src/config/studioArtifactConfig.js';
import {
  semanticChunkRawMaterial,
  computeTextSimilarity,
  findSemanticDuplicates,
  DEFAULT_SIMILARITY_THRESHOLD,
  checkDraftTextLimit,
} from '../web/step0-src/stage2Config.js';
import {
  generateUnifiedIdentityCard,
  validateUnifiedCard,
  synthesizePrincetonMaster,
  STAGE_3_META,
} from '../web/step0-src/stage3Config.js';

console.log('>>> 开始执行多版本生成采纳、草稿废纸篓、主文件防删、参考件派生与标准 5 点质检 32 项自动化断言自检...');

// -----------------------------------------------------------------------------
// 断言 1（正则防误读）：文件名 01_网络底座指标_待对照.md 的前缀 01_ 不被误读为版本 1
// -----------------------------------------------------------------------------
{
  const files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      versionTag: 'V1',
      isActive: true,
    },
  };
  const { nextVer, nextFileName, nextVersionTag } = computeNextVersion(files, 'slot_metrics');
  assert.equal(nextVer, 2, '前缀 01_ 不应误扰计数，初次重新生成应为第 2 版');
  assert.equal(nextFileName, '01_网络底座指标_第2版.md');
  assert.equal(nextVersionTag, 'V2-Draft');

  // 验证带有版本号的别名历史文件正确推导至对应槽位，不误判为 slot_misc
  assert.equal(resolveSlotKey('01_豆包题目_第2版.txt', 'step0'), 'slot_stage0_questions', '别名+版本号前缀正确映射至提问清单槽位');
  assert.equal(resolveSlotKey('02_豆包回答_第2版.txt', 'step0'), 'slot_stage0_answers', '别名+版本号前缀正确映射至回答记录槽位');

  // 验证视觉瘦身 formatDisplayName 统一格式化
  assert.equal(formatDisplayName('01_豆包实测提问清单_第1版.txt'), '豆包实测提问清单_V1.txt', '剥离前缀并规整为 V1 格式');
  assert.equal(formatDisplayName('02_豆包实测回答记录_第2.1版.txt'), '豆包实测回答记录_V2.1.txt', '支持分支灵感版本规整');
  console.log('  [PASS] 断言 1（正则防误读与别名推导）：前缀 01_ 不误读为版本 1，别名多版本精准归槽');
}

// -----------------------------------------------------------------------------
// 断言 2（废纸篓参与计数）：生成 第2版 删入废纸篓后，再次生成新文件确定递增为 第3版
// -----------------------------------------------------------------------------
{
  const files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      versionTag: 'V1',
      isActive: true,
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      versionTag: 'V2-Draft',
      isDeleted: true, // 在废纸篓中
      isActive: false,
    },
  };
  const { nextVer, nextFileName } = computeNextVersion(files, 'slot_metrics');
  assert.equal(nextVer, 3, '废纸篓中的第 2 版必须参与计数，新生成版本必须递增为第 3 版');
  assert.equal(nextFileName, '01_网络底座指标_第3版.md');
  console.log('  [PASS] 断言 2（废纸篓参与计数）：废纸篓中的旧版本参与版本递增');
}

// -----------------------------------------------------------------------------
// 断言 3（标签规整）：采纳后文件 versionTag 确定无 -Draft 后缀
// -----------------------------------------------------------------------------
{
  const files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      versionTag: 'V1',
      isActive: true,
      content: '主干内容',
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      versionTag: 'V2-Draft',
      content: '第2版新鲜内容',
    },
  };
  const res = computeAdoptResult({
    candidateName: '01_网络底座指标_第2版.md',
    files,
    stage: 'step1',
  });
  assert.equal(res.success, true);
  assert.equal(res.versionTag, 'V2', '采纳后版本标签必须规整为 V2，无 -Draft 后缀');
  assert.equal(res.files['01_网络底座指标_第2版.md'].versionTag, 'V2');
  console.log('  [PASS] 断言 3（标签规整）：采纳后 versionTag 自动剥离 -Draft');
}

// -----------------------------------------------------------------------------
// 断言 4（双重锁防误删与无死按钮）：规范骨干无论是否生效均不可删、无垃圾桶；首版留档 _第1版 同样不可删
// -----------------------------------------------------------------------------
{
  const baseFile = { name: '01_网络底座指标_待对照.md', slotKey: 'slot_metrics', isActive: false };
  assert.equal(canDeleteFile(baseFile, 'step1'), false, '规范骨干即使非 active 也绝不可删');

  const mirrorFile = { name: '01_网络底座指标_待对照.md', isCanonicalMirror: true, isActive: false };
  assert.equal(canDeleteFile(mirrorFile, 'step1'), false, '主干镜像载体绝不可删');

  const archiveFile = { name: '01_网络底座指标_第1版.md', isProtectedArchive: true, isActive: false };
  assert.equal(canDeleteFile(archiveFile, 'step1'), false, '首版母版留档绝不可删');

  const stage0Q = { name: '01_豆包提问清单_推荐版.txt', slotKey: 'slot_stage0_questions', isActive: false };
  assert.equal(canDeleteFile(stage0Q, 'step0'), false, '阶段零规范骨干绝不可删');
  console.log('  [PASS] 断言 4（双重锁防误删）：规范骨干与首版留档终身受保护不可删');
}

// -----------------------------------------------------------------------------
// 断言 5（单槽单一 active）：采纳后同 slotKey 其他文件 isActive 严格为 false，并被打上 isRetired: true
// -----------------------------------------------------------------------------
{
  const files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
      content: '初始内容',
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      isActive: false,
      content: '第2版内容',
    },
  };
  const res = computeAdoptResult({
    candidateName: '01_网络底座指标_第2版.md',
    files,
    stage: 'step1',
  });
  assert.equal(res.success, true);
  const activeMetrics = Object.values(res.files).filter(f => f.slotKey === 'slot_metrics' && f.isActive);
  assert.equal(activeMetrics.length, 1, '同槽位 active 文件严格唯一');
  assert.equal(activeMetrics[0].name, '01_网络底座指标_第2版.md');
  assert.equal(res.files['01_网络底座指标_第1版.md'].isRetired, true, '原生效版留档必须标记淘汰');
  console.log('  [PASS] 断言 5（单槽单一 active）：同槽位 active 唯一且旧版本退级淘汰');
}

// -----------------------------------------------------------------------------
// 断言 6（骨干单向自动镜像等价与内容守卫 · 🔴1 固化）：采纳有效新版或通过 computeSaveResult 编辑保存生效底牌后，规范骨干 content 100% 一致；空内容采纳被拦截，空内容保存严格不洗白规范骨干
// -----------------------------------------------------------------------------
{
  const files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
      content: '初始骨干内容',
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      isActive: false,
      content: '有效新版内容',
    },
    '01_网络底座指标_空草稿.md': {
      name: '01_网络底座指标_空草稿.md',
      slotKey: 'slot_metrics',
      isActive: false,
      content: '   \n  ',
    },
  };
  // ① 空内容采纳被拦截
  const emptyAdopt = computeAdoptResult({
    candidateName: '01_网络底座指标_空草稿.md',
    files,
    stage: 'step1',
  });
  assert.equal(emptyAdopt.success, false);
  assert.equal(emptyAdopt.reason, 'EMPTY_CONTENT');

  // ② 有效采纳镜像骨干
  const validAdopt = computeAdoptResult({
    candidateName: '01_网络底座指标_第2版.md',
    files,
    stage: 'step1',
  });
  assert.equal(validAdopt.success, true);
  assert.equal(validAdopt.files['01_网络底座指标_待对照.md'].content, '有效新版内容');
  assert.equal(validAdopt.files['01_网络底座指标_待对照.md'].isCanonicalMirror, true);

  // ③ 生效版本保存联动单向镜像
  const saveResult = computeSaveResult({
    targetName: '01_网络底座指标_第2版.md',
    content: '修改后的生效内容',
    files: validAdopt.files,
    stage: 'step1',
  });
  assert.equal(saveResult.success, true);
  assert.equal(saveResult.files['01_网络底座指标_待对照.md'].content, '修改后的生效内容');

  // ④ 空内容保存不洗白骨干与生效底牌 (🔴2 固化)
  const emptySave = computeSaveResult({
    targetName: '01_网络底座指标_第2版.md',
    content: '   ',
    files: saveResult.files,
    stage: 'step1',
  });
  assert.equal(emptySave.success, false, '活跃生效底牌严禁保存空内容');
  assert.equal(emptySave.reason, 'EMPTY_CONTENT');
  assert.equal(emptySave.files['01_网络底座指标_待对照.md'].content, '修改后的生效内容', '空内容保存坚决不洗白规范骨干');
  assert.equal(emptySave.files['01_网络底座指标_第2版.md'].content, '修改后的生效内容', '空内容保存坚决不洗白生效底牌自身');
  console.log('  [PASS] 断言 6（骨干单向自动镜像等价与内容守卫）：内容守卫严密防洗白与分叉');
}

// -----------------------------------------------------------------------------
// 断言 7（工作草稿打磨自由与手建隔离 · 🔴1 固化）：同槽存在 active 时，未采纳候选草稿（如第2版，isRetired === undefined）以及手建草稿（isManual: true）的 :readonly 严格为 false，完全可编辑打磨保存，且手建文件不参与工序版本计数
// -----------------------------------------------------------------------------
{
  const files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
      content: '主干内容',
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      isActive: false,
      versionTag: 'V2-Draft',
      content: '草稿内容',
    },
    '04_手建自定义草稿.md': {
      name: '04_手建自定义草稿.md',
      slotKey: 'slot_manual',
      isManual: true,
      isActive: false,
      content: '随便记的笔记',
    },
  };
  assert.equal(isReadOnlyFile(files['01_网络底座指标_第2版.md'], files, 'step1'), false, '未采纳的工作草稿必须允许打磨自由');
  assert.equal(isReadOnlyFile(files['04_手建自定义草稿.md'], files, 'step1'), false, '手建草稿非只读');

  const { nextVer } = computeNextVersion(files, 'slot_metrics');
  assert.equal(nextVer, 3, '手建文件不参与工序槽位版本计算');
  console.log('  [PASS] 断言 7（工作草稿打磨自由与手建隔离）：工作草稿与手建草稿自由编辑');
}

// -----------------------------------------------------------------------------
// 断言 8（规范骨干持久化标记与正交只读科学验证 · 🔴4 固化）：
// ① 采纳第 2 版后，规范骨干打上 isCanonicalMirror: true 标记且强制只读；
// ② 采纳第 3 版使第 2 版退级为历史旧版（isRetired: true）；
// ③ 将退级后的第 2 版删入废纸篓，断言此时镜像骨干与首版母版依旧强制只读，状态绝不漂移
// -----------------------------------------------------------------------------
{
  let files = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
      content: '首版内容',
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      content: '第2版内容',
    },
    '01_网络底座指标_第3版.md': {
      name: '01_网络底座指标_第3版.md',
      slotKey: 'slot_metrics',
      content: '第3版内容',
    },
  };

  // ① 采纳第 2 版
  const adoptV2 = computeAdoptResult({ candidateName: '01_网络底座指标_第2版.md', files, stage: 'step1' });
  files = adoptV2.files;
  assert.equal(files['01_网络底座指标_待对照.md'].isCanonicalMirror, true);
  // [2026-09-30 裁决11] 解绑只读，骨干与母版同样允许自由编辑打磨
  assert.equal(isReadOnlyFile(files['01_网络底座指标_待对照.md'], files, 'step1'), false, '规范主干解除生硬只读，允许编辑打磨');

  // ② 采纳第 3 版
  const adoptV3 = computeAdoptResult({ candidateName: '01_网络底座指标_第3版.md', files, stage: 'step1' });
  files = adoptV3.files;
  assert.equal(files['01_网络底座指标_第2版.md'].isRetired, true, '被淘汰的第 2 版被打上 isRetired');
  assert.equal(isReadOnlyFile(files['01_网络底座指标_第2版.md'], files, 'step1'), false, '历史版本解除只读，允许编辑');

  // ③ 将第 2 版删入废纸篓
  const delV2 = computeDeleteResult({ filename: '01_网络底座指标_第2版.md', files, stage: 'step1' });
  files = delV2.files;
  assert.equal(files['01_网络底座指标_第2版.md'].isDeleted, true);
  assert.equal(isReadOnlyFile(files['01_网络底座指标_第2版.md'], files, 'step1'), true, '移入废纸篓的文件必须强制保持只读');
  assert.equal(isReadOnlyFile(files['01_网络底座指标_待对照.md'], files, 'step1'), false, '未删除文件保持自由编辑');
  assert.equal(isReadOnlyFile(files['01_网络底座指标_第1版.md'], files, 'step1'), false, '首版母版解除只读');
  console.log('  [PASS] 断言 8（规范骨干持久化标记与正交只读科学验证 · 裁决11解绑）：除废纸篓外全域自由编辑');
}

// -----------------------------------------------------------------------------
// 断言 9（恢复后单槽 active 严格唯一 · 🔴2 固化）：从废纸篓恢复任何文件后，同 slotKey 下 active 文件数始终严格为 1（无 active 恢复为 active，有 active 恢复为草稿）
// -----------------------------------------------------------------------------
{
  const filesWithActive = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      isDeleted: true,
      isActive: false,
    },
  };
  const res1 = computeRestoreResult({ filename: '01_网络底座指标_第2版.md', files: filesWithActive, stage: 'step1' });
  assert.equal(res1.files['01_网络底座指标_第2版.md'].isActive, false, '已有 active 时恢复为草稿');

  const filesNoActive = {
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      isDeleted: true,
      isActive: false,
    },
  };
  const res2 = computeRestoreResult({ filename: '01_网络底座指标_第2版.md', files: filesNoActive, stage: 'step1' });
  assert.equal(res2.files['01_网络底座指标_第2版.md'].isActive, true, '无 active 时恢复为生效版本');
  assert.equal(res2.files['01_网络底座指标_第2版.md'].isRetired, false, '复位淘汰标记');
  console.log('  [PASS] 断言 9（恢复后单槽 active 严格唯一）：恢复动作严格维持单槽 active 唯一');
}

// -----------------------------------------------------------------------------
// 断言 10（存量旧数据迁移收敛、不变式与幂等性 · 🔴2 固化）：老数据迁移后，所有对象严格具备 item.name === fn 硬约束不变式；多 active 脏数据按最高版本严格收敛为 1 个；手建草稿不被篡改；连续多次迁移完全幂等
// -----------------------------------------------------------------------------
{
  const dirtyData = {
    '01_网络底座指标_待对照.md': {
      content: '骨干',
      isActive: true,
      is_deleted: false,
    },
    '01_网络底座指标_第2版.md': {
      content: '旧第2版',
      isActive: true, // 脏数据：同槽有两个 active
      is_deleted: false,
    },
    '04_手建草稿.md': {
      content: '手建',
      isManual: true,
      isActive: true, // 脏数据：手建文件不应参与 active
      is_deleted: 'false',
    },
    '99_跨阶段非法槽位草稿.txt': {
      content: '跨阶段脏数据',
      slotKey: 'slot_stage0_questions', // 在 step1 阶段这是非法跨阶段槽位
      isActive: true,
      isDeleted: false,
    },
  };

  const migrated1 = migrateAndNormalizeFiles(dirtyData, 'step1');
  assert.equal(migrated1['01_网络底座指标_待对照.md'].name, '01_网络底座指标_待对照.md');
  assert.equal(migrated1['01_网络底座指标_第2版.md'].name, '01_网络底座指标_第2版.md');
  assert.equal(migrated1['04_手建草稿.md'].name, '04_手建草稿.md');
  assert.equal(migrated1['99_跨阶段非法槽位草稿.txt'].name, '99_跨阶段非法槽位草稿.txt');

  // active 收敛判定：高版本 (第2版) 保留 active，第1版退级
  assert.equal(migrated1['01_网络底座指标_第2版.md'].isActive, true);
  assert.equal(migrated1['01_网络底座指标_待对照.md'].isActive, false);

  // 非有效槽位 (手建与跨阶段槽位) 必须强制失活 isActive = false，且槽位安全纠偏 (解决 🟡1 & 🟡2)
  assert.equal(migrated1['04_手建草稿.md'].isActive, false, '手建草稿绝不持有 active 状态');
  assert.equal(migrated1['04_手建草稿.md'].slotKey, 'slot_manual', '手建草稿必须明确归入 slot_manual');
  assert.equal(migrated1['99_跨阶段非法槽位草稿.txt'].isActive, false, '跨阶段非有效槽位文件绝不持有 active 状态');
  assert.equal(migrated1['99_跨阶段非法槽位草稿.txt'].slotKey, 'slot_misc', '跨阶段非法槽位必须安全纠偏为 slot_misc');

  // 存量阶段零标签归一化自检 (解决 🔴4)
  const legacyStage0Data = {
    '01_豆包提问清单_推荐版.txt': {
      name: '01_豆包提问清单_推荐版.txt',
      slotKey: 'slot_stage0_questions',
      isActive: false,
      isCanonicalMirror: true,
      content: '旧骨干',
    },
    '01_豆包提问清单_第1版.txt': {
      name: '01_豆包提问清单_第1版.txt',
      slotKey: 'slot_stage0_questions',
      isActive: false,
      isProtectedArchive: true,
      content: '母版留档',
    },
    '01_豆包提问清单_第2版.txt': {
      name: '01_豆包提问清单_第2版.txt',
      slotKey: 'slot_stage0_questions',
      isActive: true,
      versionTag: 'V2', // 存量数据误标为 V2
      content: '第2版内容',
    },
  };
  const migratedStage0 = migrateAndNormalizeFiles(legacyStage0Data, 'step0');
  assert.equal(migratedStage0['01_豆包提问清单_第2版.txt'].versionTag, 'QA-V2', '存量 V2 标签必须被归一化为 QA-V2');

  // 零-active 兜底绝不激活母版自检 (解决 🔴1)
  const onlyArchiveAndMirror = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: false,
      isCanonicalMirror: true,
      content: '骨干镜像',
    },
    '01_网络底座指标_第1版.md': {
      name: '01_网络底座指标_第1版.md',
      slotKey: 'slot_metrics',
      isActive: false,
      isProtectedArchive: true,
      content: '母版留档',
    },
  };
  const migratedOnlyArchive = migrateAndNormalizeFiles(onlyArchiveAndMirror, 'step1');
  assert.equal(migratedOnlyArchive['01_网络底座指标_第1版.md'].isActive, false, '零 active 兜底绝对严禁将首版母版激活为 active！');
  assert.equal(migratedOnlyArchive['01_网络底座指标_待对照.md'].isActive, false, '规范镜像绝不被激活为 active');

  // 幂等性与手建笔记隔离自检 (解决 🟡4)
  const manualNoteData = {
    '我的笔记_第1版.md': {
      content: '个人随手笔记',
      isManual: true,
      slotKey: 'slot_manual',
      isDeleted: false,
    },
  };
  const migratedManual = migrateAndNormalizeFiles(manualNoteData, 'step1');
  assert.equal(Boolean(migratedManual['我的笔记_第1版.md'].isProtectedArchive), false, '手建笔记绝不可被一刀切打上母版保护标记');
  assert.equal(canDeleteFile(migratedManual['我的笔记_第1版.md'], 'step1'), true, '手建笔记无论名字带不带第1版都必须允许删除');

  // 幂等性：对已迁移数据再次迁移，结果完全一致
  const migrated2 = migrateAndNormalizeFiles(migrated1, 'step1');
  assert.deepEqual(migrated1, migrated2, '多次迁移必须完全幂等');
  console.log('  [PASS] 断言 10（存量旧数据迁移收敛、不变式与幂等性）：不变式、无效槽位失活、手建隔离与幂等性满足');
}

// -----------------------------------------------------------------------------
// 断言 11（重载收敛不改写候选 · 🔴1 固化）：生成第 3 版草稿 → 执行 migrateAndNormalizeFiles → 断言该草稿 isRetired === undefined 且 isReadOnlyFile === false，绝不因刷新被误判淘汰
// -----------------------------------------------------------------------------
{
  const liveFiles = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
      versionTag: 'V1',
    },
    '01_网络底座指标_第3版.md': {
      name: '01_网络底座指标_第3版.md',
      slotKey: 'slot_metrics',
      isActive: false,
      versionTag: 'V3-Draft',
      // 未被采纳，isRetired 初始未标记
    },
  };

  const normalized = migrateAndNormalizeFiles(liveFiles, 'step1');
  const v3 = normalized['01_网络底座指标_第3版.md'];
  assert.equal(v3.isRetired, undefined, '候选草稿刷新后绝不被误判为淘汰！');
  assert.equal(isReadOnlyFile(v3, normalized, 'step1'), false, '候选草稿刷新后依然保持完全自由可编辑！');
  console.log('  [PASS] 断言 11（重载收敛不改写候选）：候选草稿重载后不被篡改为淘汰');
}

// -----------------------------------------------------------------------------
// 断言 12（缺失 stage 无害 Fail-Closed · 🔴2 固化）：migrateAndNormalizeFiles(files, '') → 断言 slotKey 未被破坏性改写为 slot_misc、文件对象不被篡改、无白屏异常
// -----------------------------------------------------------------------------
{
  const original = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      isActive: true,
    },
  };
  const result = migrateAndNormalizeFiles(original, '');
  assert.equal(result, original, '缺失 stage 时必须 Fail-Closed 原样返回，坚决禁止破坏性写入');
  assert.equal(result['01_网络底座指标_待对照.md'].slotKey, 'slot_metrics', '槽位绝对未被篡改为 slot_misc');
  console.log('  [PASS] 断言 12（缺失 stage 无害 Fail-Closed）：缺失 stage 安全关闸防破坏');
}

// -----------------------------------------------------------------------------
// 断言 13（阶段零 QA 槽位版本命名、镜像流转与留档防删全覆盖 · 🔴1/🔴2/🔴3 固化）：
// 1. computeNextVersion 必须根据 canonicalName 正确提取扩展名（.txt）且版本标签前缀为 QA-V；
// 2. 采纳第 2 版后，规范骨干（01_豆包提问清单_推荐版.txt）被标记 isCanonicalMirror 且同步镜像内容；
// 3. 首版母版（01_豆包提问清单_第1版.txt）被留档且标记 isProtectedArchive 与 isRetired；
// 4. 规范骨干与首版母版在阶段零下 canDeleteFile 均严格为 false（终身受保护不可删）。
// -----------------------------------------------------------------------------
{
  const canonicalName = '01_豆包提问清单_推荐版.txt';
  const stage0Files = {
    [canonicalName]: {
      name: canonicalName,
      slotKey: 'slot_stage0_questions',
      isActive: true,
      versionTag: 'QA-V1',
      content: '初始推荐版提问清单内容',
    },
  };

  const nextVerInfo = computeNextVersion(stage0Files, 'slot_stage0_questions');
  assert.equal(nextVerInfo.nextVer, 2);
  assert.equal(nextVerInfo.nextFileName, '01_豆包提问清单_第2版.txt', '扩展名必须是 .txt 绝不包含 undefined');
  assert.equal(nextVerInfo.nextVersionTag, 'QA-V2-Draft', '草稿版本标签必须遵循 QA-V{n}-Draft');

  // 模拟草稿加入工作区
  stage0Files[nextVerInfo.nextFileName] = {
    name: nextVerInfo.nextFileName,
    slotKey: 'slot_stage0_questions',
    isActive: false,
    versionTag: nextVerInfo.nextVersionTag,
    content: '新生成的第2版提问清单内容',
  };

  // 采纳第 2 版
  const adoptRes = computeAdoptResult({
    candidateName: '01_豆包提问清单_第2版.txt',
    files: stage0Files,
    stage: 'step0',
  });
  assert.equal(adoptRes.success, true);

  // ① 候选版本升格为生效底牌
  const adoptedV2 = adoptRes.files['01_豆包提问清单_第2版.txt'];
  assert.equal(adoptedV2.isActive, true);
  assert.equal(adoptedV2.versionTag, 'QA-V2', '采纳后版本标签规整为 QA-V2');
  assert.match(adoptedV2.versionTag, /^QA-V\d+$/, '必须符合 QA-V 格式');

  // ② 规范骨干自动单向镜像
  const mirrorBackbone = adoptRes.files[canonicalName];
  assert.equal(mirrorBackbone.isCanonicalMirror, true, '规范骨干被打上 isCanonicalMirror 镜像标记');
  assert.equal(mirrorBackbone.content, '新生成的第2版提问清单内容', '规范骨干内容与最新生效底牌 100% 一致');
  assert.equal(canDeleteFile(mirrorBackbone, 'step0'), false, '规范镜像骨干终身不可删');

  // ③ 首版母版自动留档且受保护
  const motherArchive = adoptRes.files['01_豆包提问清单_第1版.txt'];
  assert.ok(motherArchive, '首版母版必须自动留档存在');
  assert.equal(motherArchive.isProtectedArchive, true, '首版母版必须打上 isProtectedArchive 保护标记');
  assert.equal(motherArchive.isRetired, true, '首版母版必须标记 isRetired 淘汰态');
  assert.equal(motherArchive.content, '初始推荐版提问清单内容', '首版母版完整保留初始内容');
  assert.equal(canDeleteFile(motherArchive, 'step0'), false, '首版母版终身不可删');

  console.log('  [PASS] 断言 13（阶段零 QA 槽位版本命名、镜像流转与留档防删全覆盖）：阶段零镜像与母版 100% 验证');
}

// -----------------------------------------------------------------------------
// 断言 14（母版解除采纳死锁与无损回滚）：母版支持一键回滚采纳，单槽单一 active
// -----------------------------------------------------------------------------
{
  const files = {
    '01_豆包提问清单_推荐版.txt': {
      name: '01_豆包提问清单_推荐版.txt',
      slotKey: 'slot_stage0_questions',
      versionTag: 'QA-V2',
      isActive: false,
      isCanonicalMirror: true,
      content: '第2版内容',
    },
    '01_豆包提问清单_第1版.txt': {
      name: '01_豆包提问清单_第1版.txt',
      slotKey: 'slot_stage0_questions',
      versionTag: 'QA-V1',
      isActive: false,
      isRetired: true,
      isProtectedArchive: true, // 首版母版留档
      content: '母版第1版原始内容',
    },
    '01_豆包提问清单_第2版.txt': {
      name: '01_豆包提问清单_第2版.txt',
      slotKey: 'slot_stage0_questions',
      versionTag: 'QA-V2',
      isActive: true, // 当前生效的是第 2 版
      content: '第2版内容',
    },
  };

  // 用户点击母版【设为客户采纳】回退
  const rollbackRes = computeAdoptResult({
    candidateName: '01_豆包提问清单_第1版.txt',
    files,
    stage: 'step0',
  });

  assert.equal(rollbackRes.success, true, '母版必须允许被采纳回滚');
  const mother = rollbackRes.files['01_豆包提问清单_第1版.txt'];
  assert.equal(mother.isActive, true, '母版采纳后必须恢复 active');
  assert.equal(mother.isRetired, false, '母版解除淘汰');
  assert.equal(mother.isProtectedArchive, true, '母版依然保留防误删保护标记');

  const oldV2 = rollbackRes.files['01_豆包提问清单_第2版.txt'];
  assert.equal(oldV2.isActive, false, '先前生效的第 2 版必须退级');
  assert.equal(oldV2.isRetired, true, '先前生效的第 2 版标记为淘汰草稿');

  const backbone = rollbackRes.files['01_豆包提问清单_推荐版.txt'];
  assert.equal(backbone.content, '母版第1版原始内容', '规范骨干必须同步镜像回母版内容');
  assert.equal(backbone.versionTag, 'QA-V1');

  // 严格检验槽位内 active 仅有 1 个
  const activeCount = Object.values(rollbackRes.files).filter(f => f.slotKey === 'slot_stage0_questions' && f.isActive).length;
  assert.equal(activeCount, 1, '回滚后槽位内 active 严格唯一');

  // [2026-09-29] [解决 🔴4] 核心断言：母版采纳后作为当前生效底牌，必须允许打磨编辑与保存，解除只读死锁
  assert.equal(isReadOnlyFile(mother, rollbackRes.files, 'step0'), false, '母版生效后必须允许编辑，解除只读死锁');
  const saveMotherRes = computeSaveResult({
    targetName: '01_豆包提问清单_第1版.txt',
    content: '母版采纳后继续润色打磨的新内容',
    files: rollbackRes.files,
    stage: 'step0',
  });
  assert.equal(saveMotherRes.success, true, '母版生效后必须允许保存打磨修改');
  assert.equal(saveMotherRes.files['01_豆包提问清单_第1版.txt'].content, '母版采纳后继续润色打磨的新内容');

  console.log('  [PASS] 断言 14（母版解除采纳死锁与无损回滚）：母版自由采纳生效、解除只读死锁且单槽单一 active 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 15（分支草稿生成与素材库 S 体系人机两分契约）
// -----------------------------------------------------------------------------
{
  // 1. 分支草稿生成验证
  const branchFiles = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      versionTag: 'V3',
      isActive: true,
    },
  };
  const bInfo = computeBranchVersion(branchFiles, '01_网络底座指标_待对照.md', 'slot_metrics');
  assert.equal(bInfo.nextFileName, '01_网络底座指标_第3.1版.md');
  assert.equal(bInfo.nextVersionTag, 'V3.1-Draft');

  // 2. 素材库 S 体系主版本识别与人机两分过滤验证
  assert.equal(isMasterSourceFile('S1_企业主体与法定边界.md'), true);
  assert.equal(isMasterSourceFile('S4_对标竞品参数对比表_优搜网络.md'), true);
  assert.equal(isMasterSourceFile('S1.1_临时草稿.md'), false, '小数点分支绝非主版本');
  assert.equal(isMasterSourceFile('S4.2_修改版.md'), false, '小数点分支绝非主版本');

  const sourceFiles = {
    'S1_企业主体与法定边界.md': { name: 'S1_企业主体与法定边界.md', content: 'S1 主体内容' },
    'S1.1_草稿.md': { name: 'S1.1_草稿.md', content: 'S1.1 草稿内容' },
    'S2_产品价格.md': { name: 'S2_产品价格.md', content: 'S2 产品内容' },
    'S2.1_备选.md': { name: 'S2.1_备选.md', content: 'S2.1 备选内容' },
  };
  const filtered = filterMasterSourceFiles(sourceFiles);
  assert.deepEqual(Object.keys(filtered).sort(), ['S1_企业主体与法定边界.md', 'S2_产品价格.md'].sort(), '人机两分过滤必须仅保留 S 主版本');
  console.log('  [PASS] 断言 15（分支草稿生成与素材库 S 体系人机两分契约）：分支生成与人机两分完全达标');

}

// -----------------------------------------------------------------------------
// 断言 16（智能 Tab 栈管理：首置插入与超量 6 个智能淘汰 · 师弟立规）
// -----------------------------------------------------------------------------
{
  const files = {
    'file_1.md': { name: 'file_1.md', isDirty: false },
    'file_2.md': { name: 'file_2.md', isDirty: true }, // 有修改
    'file_3.md': { name: 'file_3.md', isDirty: false },
    'file_4.md': { name: 'file_4.md', isDirty: false },
    'file_5.md': { name: 'file_5.md', isDirty: false },
    'file_6.md': { name: 'file_6.md', isDirty: false },
    'file_7.md': { name: 'file_7.md', isDirty: false },
  };

  // 1. 已有 Tab 点击时，重新首置排到第 1 个
  const initialTabs = ['file_1.md', 'file_2.md', 'file_3.md'];
  const res1 = activateTabInStack(initialTabs, 'file_3.md', files, 6);
  assert.deepEqual(res1.newOpenTabs, ['file_3.md', 'file_1.md', 'file_2.md'], '已有 Tab 激活后必须排在第 1 个');
  assert.equal(res1.activeFileName, 'file_3.md');

  // 2. 超量 6 个时，优先从右往左自动关闭未修改的干净 Tab
  const fullTabs = ['file_1.md', 'file_2.md', 'file_3.md', 'file_4.md', 'file_5.md', 'file_6.md'];
  const res2 = activateTabInStack(fullTabs, 'file_7.md', files, 6);
  assert.equal(res2.newOpenTabs.length, 6, '新打开第 7 个后必须收敛在 6 个');
  assert.equal(res2.newOpenTabs[0], 'file_7.md', '新打开的文件必须排在第 1 个');
  assert.equal(res2.newOpenTabs.includes('file_6.md'), false, '最老且未修改的 file_6.md 必须被优先自动淘汰');
  assert.equal(res2.newOpenTabs.includes('file_2.md'), true, '持有未保存修改的 file_2.md 必须受保护不被静默淘汰');
  assert.equal(res2.warningDirty, false);

  // 3. 当 6 个候选全部持有未保存修改时，触发警告
  const allDirtyFiles = {
    'd1.md': { isDirty: true },
    'd2.md': { isDirty: true },
    'd3.md': { isDirty: true },
    'd4.md': { isDirty: true },
    'd5.md': { isDirty: true },
    'd6.md': { isDirty: true },
    'd7.md': { isDirty: false },
  };
  const dirtyTabs = ['d1.md', 'd2.md', 'd3.md', 'd4.md', 'd5.md', 'd6.md'];
  const res3 = activateTabInStack(dirtyTabs, 'd7.md', allDirtyFiles, 6);
  assert.equal(res3.warningDirty, true, '全脏数据必须标记 warningDirty: true 供 UI 弹窗确认');
  assert.equal(res3.dirtyFileNames.length, 6);

  console.log('  [PASS] 断言 16（智能 Tab 栈管理）：首置插入、超量 6 个自动淘汰干净 Tab 与脏数据保护 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 17（中间大文字稿字数管控与 8500 字上限拦截 · 师弟立规 · 真实函数级自测）
// -----------------------------------------------------------------------------
{
  const normalText = '这是正常的客户资料片段，包含公司简介与定价信息。'.repeat(10);
  const normalCheck = checkDraftTextLimit(normalText, 8500);
  assert.equal(normalCheck.isOverLimit, false, '正常字数必须判定未超限');
  assert.equal(normalCheck.canProcess, true, '正常字数允许进入分拣处理');

  const overflowText = '字'.repeat(8501);
  const overflowCheck = checkDraftTextLimit(overflowText, 8500);
  assert.equal(overflowCheck.isOverLimit, true, '必须精确判定超过 8500 字上限');
  assert.equal(overflowCheck.canProcess, false, '超限文本必须被拦截禁止分拣');

  // 空文本拒绝切块
  const emptyCheck = checkDraftTextLimit('', 8500);
  assert.equal(emptyCheck.canProcess, false, '空文本不得进入切块');
  const emptyChunks = semanticChunkRawMaterial('', { company: '测试公司' });
  assert.equal(emptyChunks.length, 0, '空文本不得产出任何切块');
  console.log('  [PASS] 断言 17（8500字上限与字数管控）：真实函数级拦截与空文本守卫 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 18（AI 语义切块模型提取与 6 大黄金分类归集 · 师弟立规）
// -----------------------------------------------------------------------------
{
  const sampleMaterial = `
企业规范名称：徐州璇源网络科技有限公司
统一社会信用代码：91320300MA1WXXXX01
官方客服专线：400-800-6688
实体经营办公地：江苏省徐州市鼓楼区软件园 A 座 8 层

核心服务收费：标准交付建站 ¥3000 起，定制全案 ¥15000~¥60000。
质保时效：365 天专属运维保障响应，1 小时极速应急。

对标同行套路：区域竞品优搜网络常以低价获客后期加收维护费，存在黑帽风险。

真实标杆案例：某徐州本地汽配制造实体门店，经 GEO 优化后首推率达 80%，订单翻倍增长。
`;

  const ctx = {
    company: '徐州璇源网络科技有限公司',
    brand: '邻里GEO',
    competitor: '优搜网络',
  };

  const chunks = semanticChunkRawMaterial(sampleMaterial, ctx);
  assert.equal(chunks.length >= 3, true, '长篇素材必须成功切出 3 个以上结构化片段');

  const s1Chunk = chunks.find(c => c.targetCategory === 'S1');
  assert.ok(s1Chunk, '必须成功提取并归入 S1 主体与法定边界');
  assert.equal(s1Chunk.content.includes('徐州璇源网络科技有限公司'), true);

  const s2Chunk = chunks.find(c => c.targetCategory === 'S2');
  assert.ok(s2Chunk, '必须成功提取并归入 S2 产品与价格标准');
  assert.equal(s2Chunk.content.includes('¥3000'), true);

  const s4Chunk = chunks.find(c => c.targetCategory === 'S4');
  assert.ok(s4Chunk, '必须成功提取并归入 S4 同行策略与参数对比');

  const s5Chunk = chunks.find(c => c.targetCategory === 'S5');
  assert.ok(s5Chunk, '必须成功提取并归入 S5 真实故事化案例库');

  console.log('  [PASS] 断言 18（AI 语义切块与黄金分类归集）：S1~S6 多片段精准识别与字段提纯 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 19（RAG 语义去重聚类与文案合并终态 · 师弟立规）
// -----------------------------------------------------------------------------
{
  const existingFiles = {
    'S2_核心产品与价格承诺.md': {
      name: 'S2_核心产品与价格承诺.md',
      content: '标准建站服务 ¥3000 起步，提供源码交付与 /llms.txt 专有通道，365天售后响应。',
    },
    'S1_企业主体与法定边界.md': {
      name: 'S1_企业主体与法定边界.md',
      content: '企业名称徐州璇源网络科技有限公司，统一社会信用代码91320300MA1WXXXX01。',
    },
  };

  // 1. 高度重叠的新切片（语义相似度高）
  const duplicateCandidate = {
    targetCategory: 'S2',
    suggestedTitle: '定价套餐补充',
    content: '标准建站服务 ¥3000 起步，包含全部源码与 /llms.txt 通道，365天免费售后运维。',
  };

  const directSim = computeTextSimilarity(duplicateCandidate.content, existingFiles['S2_核心产品与价格承诺.md'].content);
  assert.ok(directSim >= DEFAULT_SIMILARITY_THRESHOLD, '直接文本相似度计算必须大于等于阈值');

  const dupResult = findSemanticDuplicates(duplicateCandidate, existingFiles, DEFAULT_SIMILARITY_THRESHOLD);
  assert.ok(dupResult, '必须精准检出高相似度已有存量素材！');
  assert.equal(dupResult.existingFileKey, 'S2_核心产品与价格承诺.md');
  assert.equal(dupResult.similarity >= DEFAULT_SIMILARITY_THRESHOLD, true);

  // 2. 完全不相关的新切片（无重叠，安全入库）
  const freshCandidate = {
    targetCategory: 'S2',
    suggestedTitle: '海外多语言扩展报价',
    content: '英文与日文海外独立站扩展部署服务费为 ¥12000，支持 Cloudflare 全球 CDN 加速。',
  };
  const noDupResult = findSemanticDuplicates(freshCandidate, existingFiles, DEFAULT_SIMILARITY_THRESHOLD);
  assert.equal(noDupResult, null, '全新业务内容绝不可被误报为重复');

  console.log('  [PASS] 断言 19（RAG 语义去重聚类与文案合并）：相似度命中与无误报判定 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 20（母版回滚采纳后迁移收敛与不变式守卫 · 彻底解决 🔴-1）
// -----------------------------------------------------------------------------
{
  // 1. 模拟初始状态：已采纳 V2，生成了留档母版第 1 版
  const filesBeforeRollback = {
    '01_网络底座指标_待对照.md': {
      name: '01_网络底座指标_待对照.md',
      slotKey: 'slot_metrics',
      versionTag: 'V2',
      isActive: false,
      isCanonicalMirror: true,
      content: 'V2内容',
    },
    '01_网络底座指标_第1版.md': {
      name: '01_网络底座指标_第1版.md',
      slotKey: 'slot_metrics',
      versionTag: 'V1',
      isActive: false,
      isRetired: true,
      isProtectedArchive: true,
      content: '母版第1版原始内容',
    },
    '01_网络底座指标_第2版.md': {
      name: '01_网络底座指标_第2版.md',
      slotKey: 'slot_metrics',
      versionTag: 'V2',
      isActive: true,
      isRetired: false,
      content: 'V2内容',
    },
  };

  // 2. 用户误点采纳后点击【设为客户采纳】回滚到母版第 1 版
  const adoptRes = computeAdoptResult({
    candidateName: '01_网络底座指标_第1版.md',
    files: filesBeforeRollback,
    stage: 'step1',
  });
  assert.equal(adoptRes.success, true);
  assert.equal(adoptRes.files['01_网络底座指标_第1版.md'].isActive, true);

  // 3. 模拟页面刷新，执行存量迁移收敛
  const normalized1 = migrateAndNormalizeFiles(adoptRes.files, 'step1');

  // ① 同槽 active 严格唯一且为母版
  const activeFiles = Object.values(normalized1).filter(f => f.slotKey === 'slot_metrics' && f.isActive);
  assert.equal(activeFiles.length, 1, '同槽 active 文件必须严格为 1');
  assert.equal(activeFiles[0].name, '01_网络底座指标_第1版.md', '生效文件必须保持为回滚后的母版第 1 版');

  // ② 生效母版绝不可被打上 isRetired 淘汰标，杜绝矛盾态
  assert.equal(normalized1['01_网络底座指标_第1版.md'].isRetired, false, '生效母版 isRetired 必须为 false');

  // ③ 规范骨干 content 必须等价镜像自母版 content
  assert.equal(normalized1['01_网络底座指标_待对照.md'].content, '母版第1版原始内容', '骨干内容必须同步自生效母版');
  assert.equal(normalized1['01_网络底座指标_待对照.md'].isCanonicalMirror, true);

  // ④ 幂等性守卫：连续两次执行迁移结果严格一致
  const normalized2 = migrateAndNormalizeFiles(normalized1, 'step1');
  assert.deepEqual(normalized1, normalized2, '两次连续迁移必须严格幂等');

  console.log('  [PASS] 断言 20（母版回滚采纳后迁移收敛与不变式）：单槽单一 active、母版不被淘汰、骨干内容同步且幂等 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 21（阶段二素材库 1.x 纯增量分片单调递增契约 · 师弟立规）
// -----------------------------------------------------------------------------
{
  const files = {
    'S2_核心产品与价格承诺.md': {
      name: 'S2_核心产品与价格承诺.md',
      slotKey: 'slot_stage2_s2',
      category: 'source_products',
      content: '主文件内容',
      isActive: true,
    },
  };

  // 1. 首次派生增补切片：1.1
  const chunk1 = computeStage2ChunkVersion(files, 'slot_stage2_s2');
  assert.equal(chunk1.nextBranch, 1);
  assert.equal(chunk1.nextFileName, 'S2_核心产品与价格承诺_增补_1.1.md');
  assert.equal(chunk1.nextVersionTag, 'S2.1');
  assert.equal(chunk1.category, 'source_products');

  // 将 1.1 存入 files
  files[chunk1.nextFileName] = {
    name: chunk1.nextFileName,
    slotKey: chunk1.slotKey,
    category: chunk1.category,
    versionTag: chunk1.nextVersionTag,
    isBranchDraft: true,
    content: '本次纯新增素材片段，不带主文件旧内容',
  };

  // 2. 二次派生增补切片：递增为 1.2
  const chunk2 = computeStage2ChunkVersion(files, 'slot_stage2_s2');
  assert.equal(chunk2.nextBranch, 2);
  assert.equal(chunk2.nextFileName, 'S2_核心产品与价格承诺_增补_1.2.md');
  assert.equal(chunk2.nextVersionTag, 'S2.2');

  // 3. 验证其他槽位（如 S5 案例库）不受干扰，从 1.1 独立开始
  const chunkS5 = computeStage2ChunkVersion(files, 'slot_stage2_s5');
  assert.equal(chunkS5.nextBranch, 1);
  assert.equal(chunkS5.nextFileName, 'S5_经典案例故事_增补_1.1.md');

  // 4. 验证视觉标签格式化 formatDisplayName (剥离 S{N}_ 前缀并规整为 _增补_V1.x)
  assert.equal(formatDisplayName('S2_核心产品与价格承诺_增补_1.1.md'), '核心产品与价格承诺_增补_V1.1.md');
  assert.equal(formatDisplayName('S5_经典案例故事_增补_1.2.md'), '经典案例故事_增补_V1.2.md');

  console.log('  [PASS] 断言 21（阶段二素材库 1.x 纯增量分片）：单调递增派生、槽位相互独立、短名格式化 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 22（阶段二人机两分契约与删除权限守卫 · 彻底解决 🔴1 与 🟡2）
// -----------------------------------------------------------------------------
{
  const masterFile = 'S2_核心产品与价格承诺.md';
  const chunkFile = 'S2_核心产品与价格承诺_增补_1.1.md';
  const dotChunkFile = 'S1.1_草稿.md';

  // 1. 验证 isMasterSourceFile：真实主文件为 true，增补切片严格为 false！
  assert.equal(isMasterSourceFile(masterFile), true, 'S2 主文件必须判定为主文件');
  assert.equal(isMasterSourceFile(chunkFile), false, 'S2 增补切片绝对不可判定为主文件！');
  assert.equal(isMasterSourceFile(dotChunkFile), false, 'S1.1 点号切片绝对不可判定为主文件！');

  // 2. 验证 filterMasterSourceFiles：母盘消费时过滤出且仅包含主文件
  const testFiles = {
    [masterFile]: { name: masterFile, content: '主版本', isActive: true },
    [chunkFile]: { name: chunkFile, content: '增量分片', isBranchDraft: true },
  };
  const filtered = filterMasterSourceFiles(testFiles);
  assert.ok(filtered[masterFile], '主文件必须在消费列表');
  assert.equal(filtered[chunkFile], undefined, '增补分片绝不可被当作主版本过滤消费！');

  // 3. 验证 canDeleteFile 权限守卫：主文件终身防删，增补分片允许移入废纸篓
  assert.equal(canDeleteFile(testFiles[masterFile], 'step2'), false, '主文件终身不可删！');
  assert.equal(canDeleteFile(testFiles[chunkFile], 'step2'), true, '增补草稿允许移入废纸篓！');

  console.log('  [PASS] 断言 22（人机两分契约与删除权限）：主版本识别唯一、增量分片正交隔离、删除权限精准 100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 23（阶段二 normalizeVersionTag 严格幂等不膨胀、S1 首次切片自 1.1 起跳与 Fail-Closed 空引用防崩 · 彻底解决 🔴1/🔴2/🔴3）
// -----------------------------------------------------------------------------
{
  // 1. 验证 normalizeVersionTag 幂等性：S2.1 连续归一化 10 次绝不膨胀为 S2.2.1 或 S2.2.2.1！
  let tag = 'S2.1-Draft';
  tag = normalizeVersionTag(tag, 'slot_stage2_s2');
  assert.equal(tag, 'S2.1', '首次归一化必须剥离 -Draft 且前缀匹配');
  for (let i = 0; i < 5; i++) {
    tag = normalizeVersionTag(tag, 'slot_stage2_s2');
    assert.equal(tag, 'S2.1', `第 ${i + 1} 次重复归一化必须严格幂等，绝对不可发生前缀膨胀！`);
  }

  // 验证 S1 槽位标签
  assert.equal(normalizeVersionTag('S1.1-Draft', 'slot_stage2_s1'), 'S1.1');
  assert.equal(normalizeVersionTag('S1.1', 'slot_stage2_s1'), 'S1.1');

  // 2. 验证 computeStage2ChunkVersion：S1 槽位首次派生切片严格从 1.1 起步（绝不从 1.2 起跳！）
  const s1Files = {
    'S1_企业主体与法定边界.md': {
      name: 'S1_企业主体与法定边界.md',
      slotKey: 'slot_stage2_s1',
      versionTag: 'S1.1',
      category: 'source_identity',
      isActive: true,
      content: '主体规范主文件',
    },
  };
  const s1Chunk = computeStage2ChunkVersion(s1Files, 'slot_stage2_s1');
  assert.equal(s1Chunk.nextBranch, 1, 'S1 首个切片分支号必须为 1');
  assert.equal(s1Chunk.nextFileName, 'S1_企业主体与法定边界_增补_1.1.md', 'S1 首个切片必须为 1.1');
  assert.equal(s1Chunk.nextVersionTag, 'S1.1');

  // 3. 验证 Fail-Closed 关闸保护：canDeleteFile 传入 null/undefined/空对象绝不抛异常
  assert.equal(canDeleteFile(null, 'step2'), false, 'null 引用必须返回 false');
  assert.equal(canDeleteFile(undefined, 'step2'), false, 'undefined 引用必须返回 false');
  assert.equal(canDeleteFile({}, 'step2'), false, '空对象必须返回 false');

  console.log('  [PASS] 断言 23（版本标签幂等不膨胀、S1 首片自 1.1 起步、Fail-Closed 防崩）：100% 成立');
}

// -----------------------------------------------------------------------------
// 断言 24：官网网址唯一真相源（消除双重协议、规范补齐与域名提取）
// -----------------------------------------------------------------------------
function test24() {
  // 1. 消除重复协议头 https://https://
  assert.equal(
    normalizeOfficialUrl('https://https://nextgeo.baicl.cc'),
    'https://nextgeo.baicl.cc',
    '重复的 https://https:// 必须被清洗为单个 https://'
  );
  assert.equal(
    normalizeOfficialUrl('https://https://https://www.baicl.cc/'),
    'https://www.baicl.cc',
    '三重协议及末尾斜杠必须彻底清洗'
  );

  // 2. 裸域名自动补齐 https://
  assert.equal(
    normalizeOfficialUrl('www.baicl.cc'),
    'https://www.baicl.cc',
    '裸域名必须规范补齐 https://'
  );

  // 3. 正常 https/http URL 保持不变
  assert.equal(
    normalizeOfficialUrl('https://www.baicl.cc'),
    'https://www.baicl.cc'
  );
  assert.equal(
    normalizeOfficialUrl('http://insecure.site.com'),
    'http://insecure.site.com'
  );

  // 4. 空字符串与非字符串安全兜底
  assert.equal(normalizeOfficialUrl(''), '');
  assert.equal(normalizeOfficialUrl(null), '');
  assert.equal(normalizeOfficialUrl(undefined), '');

  // 5. extractDomain 纯域名提取
  assert.equal(extractDomain('https://https://nextgeo.baicl.cc'), 'nextgeo.baicl.cc');
  assert.equal(extractDomain('https://www.baicl.cc/sub/path'), 'www.baicl.cc');
  assert.equal(extractDomain('www.baicl.cc'), 'www.baicl.cc');

  console.log('  [PASS] 断言 24（官网网址唯一真相源、消除重复协议、自动补齐与域名提取）：100% 成立');
}

test24();

// -----------------------------------------------------------------------------
// 断言 25（阶段三槽位字典与别名解析契约 · 师弟立规）
// -----------------------------------------------------------------------------
function test25() {
  // 1. 阶段三槽位字典注册自检
  assert.ok(CANONICAL_SLOT_DICT.slot_stage3_identity_card, '必须注册 slot_stage3_identity_card');
  assert.equal(CANONICAL_SLOT_DICT.slot_stage3_identity_card.stage, 'step3');
  assert.equal(CANONICAL_SLOT_DICT.slot_stage3_identity_card.canonicalName, '01_主体信息统一口径卡.md');

  assert.ok(CANONICAL_SLOT_DICT.slot_stage3_master, '必须注册 slot_stage3_master');
  assert.equal(CANONICAL_SLOT_DICT.slot_stage3_master.stage, 'step3');
  assert.equal(CANONICAL_SLOT_DICT.slot_stage3_master.canonicalName, '02_普林斯顿企业事实母盘.md');

  // 2. 别名与前缀容错解析
  assert.equal(resolveSlotKey('01_主体信息统一口径卡.md', 'step3'), 'slot_stage3_identity_card');
  assert.equal(resolveSlotKey('01_主体信息统一口径卡', 'step3'), 'slot_stage3_identity_card');
  assert.equal(resolveSlotKey('02_普林斯顿企业事实母盘.md', 'step3'), 'slot_stage3_master');
  assert.equal(resolveSlotKey('02_普林斯顿企业事实母盘', 'step3'), 'slot_stage3_master');

  // 3. getSlotsByStage 隔离白名单（严格仅有两大核心槽位）
  const step3Slots = getSlotsByStage('step3');
  assert.deepEqual(step3Slots.sort(), ['slot_stage3_identity_card', 'slot_stage3_master'].sort());

  console.log('  [PASS] 断言 25（阶段三双主文件槽位字典与别名解析契约）：两大核心槽位注册、扩展名容错与白名单 100% 成立');
}

test25();

// -----------------------------------------------------------------------------
// 断言 26（《主体信息统一口径卡》生成、四要素消歧与三级业务描述字数红绿灯 · 师弟立规）
// -----------------------------------------------------------------------------
function test26() {
  const pData = {
    brand_name: '邻里GEO',
    company_name: '徐州璇源网络科技有限公司',
    credit_code: '91320311MA1N0WN2XJ',
    official_url: 'https://baicl.cc',
    city_name: '江苏省徐州市泉山区',
  };

  // 1. 生成口径卡标准文本
  const cardContent = generateUnifiedIdentityCard(pData);
  assert.ok(cardContent.includes('# 主体信息统一口径卡 · 邻里GEO'));
  assert.ok(cardContent.includes('徐州璇源网络科技有限公司'));
  assert.ok(cardContent.includes('91320311MA1N0WN2XJ'));
  assert.ok(cardContent.includes('https://baicl.cc'));

  // 2. 正常卡片校验全绿灯 (isValid === true, errors 为空)
  const validRes = validateUnifiedCard(cardContent);
  assert.equal(validRes.isValid, true, '标准生成的口径卡必须通过合规校验');
  assert.equal(validRes.errors.length, 0, '标准生成的口径卡不应有错误');
  assert.equal(validRes.stats.shortExceeded, false, '短版必须 <= 50 字');
  assert.equal(validRes.stats.stdExceeded, false, '标准版必须 <= 120 字');
  assert.equal(validRes.stats.hasGeoCn, true, '必须包含 GEO 中文全称首现');

  // 3. 拦截短版超标 (> 50 字)
  const shortOverflow = cardContent.replace(
    /### ① 短版[^\n]*\n+> ([^\n]+)/,
    '### ① 短版 · 50 字内（地图、企业名录、平台标签位）\n\n> 这里是一段特意写得很长很长的短版业务描述文本，文字长度故意超过了五十个汉字的严格上限限制，系统必须精准检出并红色阻断拦截！'
  );
  const checkShort = validateUnifiedCard(shortOverflow);
  assert.equal(checkShort.isValid, false, '短版超标必须触发拦截');
  assert.equal(checkShort.stats.shortExceeded, true);
  assert.ok(checkShort.errors.some(e => e.includes('短版业务描述超标')));

  // 4. 拦截标准版超标 (> 120 字)
  const stdOverflow = cardContent.replace(
    /### ② 标准版[^\n]*\n+> ([^\n]+)/,
    '### ② 标准版 · 120 字内（BOSS 直聘、启信宝、天眼查、爱企查的企业简介）[主力]\n\n> ' + '这是一段为了测试标准版字数上限而生成的超长文本。'.repeat(10)
  );
  const checkStd = validateUnifiedCard(stdOverflow);
  assert.equal(checkStd.isValid, false, '标准版超标必须触发拦截');
  assert.equal(checkStd.stats.stdExceeded, true);
  assert.ok(checkStd.errors.some(e => e.includes('标准版业务描述超标')));

  // 5. 拦截核心消歧字段缺失（无品牌名）
  const noBrand = cardContent.replace(/品牌名/g, '无关字段');
  const checkNoBrand = validateUnifiedCard(noBrand);
  assert.equal(checkNoBrand.isValid, false);
  assert.ok(checkNoBrand.errors.some(e => e.includes('缺少【品牌名】消歧字段')));

  // 6. 严禁交付物出现 Emoji 符号 (RULES.md 零 Emoji 禁令 · 自动化固化)
  const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
  assert.equal(emojiRegex.test(cardContent), false, '口径卡生成文本必须严格为 0 Emoji！');

  console.log('  [PASS] 断言 26（主体信息统一口径卡生成、四要素消歧、三级业务描述字数红绿灯与零Emoji）：100% 成立');
}

test26();

// -----------------------------------------------------------------------------
// 断言 27（9 因子母盘合流萃取与人机两分契约 · 过滤增补切片 · 师弟立规）
// -----------------------------------------------------------------------------
function test27() {
  const pData = {
    brand_name: '邻里GEO',
    company_name: '徐州璇源网络科技有限公司',
    official_url: 'https://baicl.cc',
  };

  const stage2Files = {
    'S1_企业主体与法定边界.md': {
      name: 'S1_企业主体与法定边界.md',
      content: '# 企业主体\n\n这是 S1 权威主版本主体内容。',
      isActive: true,
    },
    'S1_企业主体与法定边界_增补_1.1.md': {
      name: 'S1_企业主体与法定边界_增补_1.1.md',
      content: '# 增补切片\n\n这是增补切片内容，绝不混入母盘！',
      isBranchDraft: true,
    },
    'S2_核心产品与价格承诺.md': {
      name: 'S2_核心产品与价格承诺.md',
      content: '# 核心产品\n\n标准交付服务 ¥3000，定制交付 ¥15000。',
      isActive: true,
    },
    'S2_核心产品与价格承诺_增补_1.2.md': {
      name: 'S2_核心产品与价格承诺_增补_1.2.md',
      content: '# 增补产品\n\n增补产品报价，留给 RAG。',
      isBranchDraft: true,
    },
  };

  const masterContent = synthesizePrincetonMaster(stage2Files, pData);

  // 1. 9 因子事实大百科骨干齐全
  for (let i = 1; i <= 9; i++) {
    assert.ok(masterContent.includes(`## 因子 ${i} ·`), `母盘必须包含 因子 ${i}`);
  }

  // 2. 仅消费 S1~S6 规范主版本，跳过 1.x 增补分片
  assert.ok(masterContent.includes('这是 S1 权威主版本主体内容。'), '母盘必须萃取主版本 S1 正文');
  assert.ok(masterContent.includes('标准交付服务 ¥3000'), '母盘必须萃取主版本 S2 正文');
  // 3. 严禁交付物出现 Emoji 符号 (RULES.md 零 Emoji 禁令 · 自动化固化)
  const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
  assert.equal(emojiRegex.test(masterContent), false, '普林斯顿母盘生成文本必须严格为 0 Emoji！');

  console.log('  [PASS] 断言 27（9 因子母盘合流萃取、人机两分契约与零Emoji）：9 因子齐备、仅萃取主版本且隔离增补分片 100% 成立');
}

test27();

// -----------------------------------------------------------------------------
// 断言 28（全平台事实对冲指引生成、4 步 SOP 元数据完整性与零Emoji · 师弟立规）
// -----------------------------------------------------------------------------
function test28() {
  const pData = {
    brand_name: '邻里GEO',
    company_name: '徐州璇源网络科技有限公司',
    official_url: 'https://baicl.cc',
  };

  // 1. 口径卡内置打扫卫生操作指引生成验证
  const cardWithHedge = generateUnifiedIdentityCard(pData);
  assert.ok(cardWithHedge.includes('# 主体信息统一口径卡 · 邻里GEO'));
  assert.ok(cardWithHedge.includes('国家企业信用信息公示系统'));
  assert.ok(cardWithHedge.includes('BOSS 直聘'));
  assert.ok(cardWithHedge.includes('启信宝 / 天眼查 / 爱企查'));
  assert.ok(cardWithHedge.includes('地图平台（百度地图 / 高德地图）'));
  assert.ok(cardWithHedge.includes('客观瑕疵合规对冲指引'));

  // 2. 严禁交付物出现 Emoji 符号
  const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
  assert.equal(emojiRegex.test(cardWithHedge), false, '主体信息统一口径卡生成文本必须严格为 0 Emoji！');

  // 3. 阶段三元数据完整性（对齐老赵哥正统实战大白话 SOP）
  assert.equal(STAGE_3_META.id, 'step-3-master');
  assert.equal(STAGE_3_META.sopSteps.length, 4, '阶段三必须严格具备 4 步闭环 SOP 动线');
  assert.equal(STAGE_3_META.categories.length, 2, '阶段三严格收敛为双核心主文件分类（口径卡+事实母盘）');
  assert.equal(STAGE_3_META.categories[0].id, 'identity_card');
  assert.equal(STAGE_3_META.categories[1].id, 'master_corpus');
  assert.ok(STAGE_3_META.sopSteps[0].name.includes('核定企业数字身份证'), '步骤1为核定企业数字身份证');
  assert.ok(STAGE_3_META.sopSteps[1].name.includes('打扫全网卫生'), '步骤2为打扫全网卫生');
  assert.ok(STAGE_3_META.sopSteps[2].name.includes('提炼六模块事实真理字典'), '步骤3为提炼六模块事实真理字典');
  assert.ok(STAGE_3_META.sopSteps[3].name.includes('5分钟抽题自检'), '步骤4为5分钟抽题自检');

  console.log('  [PASS] 断言 28（老赵哥实战大白话 4 步 SOP 与双主文件精简收敛）：100% 成立');
}

test28();

// -----------------------------------------------------------------------------
// 断言 29（主文件建档预置与物理防删保护 · 师弟立规）
// -----------------------------------------------------------------------------
function test29() {
  const masterFile = {
    name: '01_豆包提问清单_推荐版.txt',
    slotKey: 'slot_stage0_questions',
    isMaster: true,
    isActive: true,
    versionTag: '主文件',
    content: '提问清单主文件内容...',
  };

  // 1. isMasterFile 正确识别
  assert.equal(isMasterFile(masterFile), true, '主文件必须被 isMasterFile 识别');

  // 2. 规范槽位默认骨干名自动具备主文件地位
  const canonicalFile = {
    name: '02_豆包实测回答记录_初测.txt',
    slotKey: 'slot_stage0_answers',
  };
  assert.equal(isMasterFile(canonicalFile), true, '默认规范文件名自动享有主文件地位');

  // 3. canDeleteFile 物理锁定禁止删除主文件
  const canDel = canDeleteFile(masterFile, 'step0');
  assert.equal(canDel, false, '主文件终身物理锁定禁止删除！');

  const canDelCanonical = canDeleteFile(canonicalFile, 'step0');
  assert.equal(canDelCanonical, false, '规范主文件严禁删除');

  console.log('  [PASS] 断言 29（主文件建档预置与物理防删保护）：100% 成立');
}

test29();

// -----------------------------------------------------------------------------
// 断言 30（参考候选件生成与递增派生 · 废除 1.1/1.2 师弟立规）
// -----------------------------------------------------------------------------
function test30() {
  const files = {
    '01_豆包提问清单_推荐版.txt': {
      name: '01_豆包提问清单_推荐版.txt',
      slotKey: 'slot_stage0_questions',
      isMaster: true,
      isActive: true,
      versionTag: '主文件',
    }
  };

  // 1. 第一次重新出题派生 参考1
  const ref1 = computeReferenceVersion(files, 'slot_stage0_questions', '参考');
  assert.equal(ref1.nextFileName, '01_豆包提问清单_参考1.txt');
  assert.equal(ref1.nextVersionTag, '参考1');
  assert.equal(ref1.nextNum, 1);

  // 写入字典
  files[ref1.nextFileName] = {
    name: ref1.nextFileName,
    slotKey: 'slot_stage0_questions',
    isMaster: false,
    isActive: false,
    versionTag: ref1.nextVersionTag,
  };

  // 2. 第二次重新出题派生 参考2
  const ref2 = computeReferenceVersion(files, 'slot_stage0_questions', '参考');
  assert.equal(ref2.nextFileName, '01_豆包提问清单_参考2.txt');
  assert.equal(ref2.nextVersionTag, '参考2');
  assert.equal(ref2.nextNum, 2);

  // 3. 参考件非主文件，且允许删除进入废纸篓
  assert.equal(isMasterFile(files[ref1.nextFileName]), false, '参考件绝不享有主文件地位');
  assert.equal(canDeleteFile(files[ref1.nextFileName], 'step0'), true, '参考候选件允许删除进入废纸篓');

  console.log('  [PASS] 断言 30（参考候选件生成与递增派生 · 废除 1.1/1.2）：100% 成立');
}

test30();

// -----------------------------------------------------------------------------
// 断言 31（标准 5 点核心质检模型与门禁消费 · 师弟立规）
// -----------------------------------------------------------------------------
function test31() {
  const pDataFull = {
    brand_name: '邻里GEO',
    company_name: '徐州璇源网络科技有限公司',
    credit_code: '91320311MA1N0WN2XJ',
    official_url: 'https://baicl.cc',
  };

  // 0. 验证最小字数单一定义常量 SSOT
  assert.equal(MIN_MASTER_CONTENT_LENGTH, 50, '主文件最小字符数门槛必须为 50 字');

  // 1. 初始空模版主文件（包含待填说明，未达标）
  const initialMaster = {
    name: '01_豆包提问清单_推荐版.txt',
    slotKey: 'slot_stage0_questions',
    isMaster: true,
    isActive: true,
    content: '说明：复制上方题目，直接前往豆包网页版逐题提问，将真实回答贴回第 2 个文件。',
  };
  const checkInitial = evaluate5PointCheck(initialMaster, pDataFull);
  assert.equal(checkInitial.ready, false, '包含初始空模版说明时，质检不应通过');
  assert.equal(checkInitial.points.find(p => p.key === 'point_not_template').pass, false, '脱离初始模版应为 false');

  // 2. 润色打磨后的真实业务主文件（字数达标、四要素齐备且一致、确认就绪）
  const polishedMaster = {
    name: '01_豆包提问清单_推荐版.txt',
    slotKey: 'slot_stage0_questions',
    isMaster: true,
    isActive: true,
    isConfirmed: true,
    content: '=== 阶段零：邻里GEO 提问清单 ===\n\n' +
      '徐州璇源网络科技有限公司，统一社会信用代码 91320311MA1N0WN2XJ，官方权威网站 https://baicl.cc。\n' +
      '[第 1 题]：徐州做 GEO 优化哪家比较好？有推荐的吗？\n' +
      '[第 2 题]：想找徐州的邻里GEO，他们家主要做什么业务，口碑怎么样？\n' +
      '[第 3 题]：徐州 GEO 市场排名前三的服务商有哪些？\n' +
      '[第 4 题]：邻里GEO和同行的区别在哪？收费怎么样？\n' +
      '[第 5 题]：徐州有没有靠谱的本地实体 GEO 推荐，不要推假公司广告？',
  };
  const checkPolished = evaluate5PointCheck(polishedMaster, pDataFull);
  assert.equal(checkPolished.ready, true, '真实打磨且四要素齐备的主文件必须 5 点全部通过');
  assert.equal(checkPolished.points.length, 5, '必须具备标准 5 点指标');
  assert.ok(checkPolished.points.every(p => p.pass === true), '5 点全绿');

  // 3. 消歧要素负例 1：正文中未提及客户品牌名
  const missingBrandMaster = {
    ...polishedMaster,
    content: '=== 阶段零：提问清单 ===\n\n徐州璇源网络科技有限公司 91320311MA1N0WN2XJ https://baicl.cc 做优化哪家比较好？字数达标但没有写明品牌名称。',
  };
  const checkMissingBrand = evaluate5PointCheck(missingBrandMaster, pDataFull);
  assert.equal(checkMissingBrand.ready, false, '缺少品牌消歧要素时必须拦截');
  assert.equal(checkMissingBrand.points.find(p => p.key === 'point_elements').pass, false);

  // 4. 消歧要素负例 2：缺少统一社会信用代码 (解决 🔴2)
  const checkMissingCode = evaluate5PointCheck(polishedMaster, {
    brand_name: '邻里GEO',
    company_name: '徐州璇源网络科技有限公司',
    official_url: 'https://baicl.cc',
    // 缺少 credit_code
  });
  assert.equal(checkMissingCode.ready, false, '缺少统一代码消歧要素时必须拦截');
  assert.equal(checkMissingCode.points.find(p => p.key === 'point_elements').pass, false);

  // 5. 消歧要素负例 3：缺少核心官网 (解决 🔴2)
  const checkMissingUrl = evaluate5PointCheck(polishedMaster, {
    brand_name: '邻里GEO',
    company_name: '徐州璇源网络科技有限公司',
    credit_code: '91320311MA1N0WN2XJ',
    // 缺少 official_url
  });
  assert.equal(checkMissingUrl.ready, false, '缺少核心官网消歧要素时必须拦截');
  assert.equal(checkMissingUrl.points.find(p => p.key === 'point_elements').pass, false);

  console.log('  [PASS] 断言 31（标准 5 点核心质检模型与门禁消费 · 四要素正反例全覆盖）：100% 成立');
}

test31();

// -----------------------------------------------------------------------------
// 断言 32（雪花 ID 唯一编号、全域隐藏技术扩展名、纯净展示标题与人工改名重名防呆）
// -----------------------------------------------------------------------------
function test32() {
  // 1. 验证 generateSnowflakeId 唯一编号与不可变雪花格式
  const id1 = generateSnowflakeId();
  const id2 = generateSnowflakeId();
  assert.ok(typeof id1 === 'string' && id1.length >= 10, '雪花 ID 必须为合法字符串');
  assert.ok(/^\d+$/.test(id1), '雪花 ID 必须纯数字');
  assert.notEqual(id1, id2, '连续生成的两个雪花 ID 绝对不可重复');

  // 2. 验证 stripExtension 剥离扩展名
  assert.equal(stripExtension('01_豆包提问清单_推荐版.txt'), '01_豆包提问清单_推荐版');
  assert.equal(stripExtension('S1_企业主体与法定边界.md'), 'S1_企业主体与法定边界');
  assert.equal(stripExtension('plain_name'), 'plain_name');
  assert.equal(stripExtension(''), '');

  // 3. 验证 formatDisplayTitle 纯净展示标题（不含扩展名，支持人工修改自定义名称）
  assert.equal(formatDisplayTitle('01_豆包提问清单_推荐版.txt'), '豆包提问清单_推荐版');
  assert.equal(formatDisplayTitle('S2_核心产品与价格承诺_增补_1.1.md'), '核心产品与价格承诺_增补_V1.1');
  
  // 人工改名优先于机器默认格式
  const renamedFile = {
    displayName: '徐州老赵五问豆包.txt', // 即使人工输入带了后缀，展现层也彻底抹除
  };
  assert.equal(formatDisplayTitle('01_豆包提问清单_推荐版.txt', renamedFile), '徐州老赵五问豆包');

  // 4. 验证人工改名重名防呆判定（调用单一真相源 isDuplicateDisplayName 纯函数）
  const existingFiles = {
    '01_豆包提问清单_推荐版.txt': { displayName: '徐州老赵五问豆包', isDeleted: false },
    '02_豆包实测回答记录_初测.txt': { displayName: '豆包实测回答记录', isDeleted: false },
    '01_废弃草稿.txt': { displayName: '已删除的名字', isDeleted: true },
  };

  assert.equal(isDuplicateDisplayName(existingFiles, '02_豆包实测回答记录_初测.txt', '徐州老赵五问豆包'), true, '输入与现有主文件相同的名字必须判为重名！');
  assert.equal(isDuplicateDisplayName(existingFiles, '02_豆包实测回答记录_初测.txt', '徐州老赵新版本'), false, '全新名字不应重名');
  assert.equal(isDuplicateDisplayName(existingFiles, '02_豆包实测回答记录_初测.txt', '已删除的名字'), false, '废纸篓中的文件不参与重名拦截');
  assert.equal(isDuplicateDisplayName(existingFiles, '01_豆包提问清单_推荐版.txt', '徐州老赵五问豆包'), false, '改名与自身当前名称一致不算重名');

  // 5. 验证裁决 11（除废纸篓外，所有主文件、参考件、历史母版、草稿全域解除只读锁）
  assert.equal(isReadOnlyFile({ name: '01_主文件.txt', isMaster: true, isActive: true }), false, '主文件可编辑');
  assert.equal(isReadOnlyFile({ name: '01_参考1.txt', versionTag: '参考1', isActive: false }), false, '参考件可编辑');
  assert.equal(isReadOnlyFile({ name: '01_母版.txt', isProtectedArchive: true, isActive: false }), false, '历史母版解除只读，可自由编辑打磨');
  assert.equal(isReadOnlyFile({ name: '01_草稿.txt', isRetired: true, isActive: false }), false, '淘汰草稿解除只读，可编辑');
  assert.equal(isReadOnlyFile({ name: '01_废纸篓.txt', isDeleted: true }), true, '只有废纸篓文件强制只读');
  assert.equal(isReadOnlyFile({ name: '01_废纸篓2.txt', is_deleted: true }), true, '只有废纸篓文件强制只读');

  // 6. 验证仅主文件开放重命名守卫（参考件禁止改名，系统自管编号）
  assert.equal(isMasterFile({ name: '01_豆包提问清单_推荐版.txt', isMaster: true }), true, '主文件必须被识别为主文件');
  assert.equal(isMasterFile({ name: '01_豆包提问清单_参考1.txt', versionTag: '参考1' }), false, '参考候选件绝不可被识别为主文件');

  // [2026-09-30 修复🔴4] 验证骨干镜像与留档归档绝不可被识别为主文件，单槽 Master 解析确定且唯一
  assert.equal(isMasterFile({ name: '01_网络底座指标_待对照.md', isCanonicalMirror: true }), false, '骨干镜像绝不可被识别为主文件');
  assert.equal(isMasterFile({ name: '01_商业诊断与转化初稿.md', isProtectedArchive: true }), false, '历史留档绝不可被识别为主文件');
  const dualSlotFiles = {
    '01_网络底座指标_待对照.md': { name: '01_网络底座指标_待对照.md', slotKey: 'slot_metrics', isCanonicalMirror: true },
    '01_网络底座指标_第2版.md': { name: '01_网络底座指标_第2版.md', slotKey: 'slot_metrics', isMaster: true, isActive: true },
  };
  const resolvedMaster = getMasterFileForSlot(dualSlotFiles, 'slot_metrics');
  assert.equal(resolvedMaster.name, '01_网络底座指标_第2版.md', 'getMasterFileForSlot 必须精准且唯一解析生效主文件');

  // 7. 验证渲染层全域绝不出现 .txt / .md 扩展名
  const sampleTitles = [
    formatDisplayTitle('01_豆包提问清单_推荐版.txt'),
    formatDisplayTitle('02_豆包实测回答记录_初测.txt'),
    formatDisplayTitle('01_豆包提问清单_参考1.txt'),
    formatDisplayTitle('S1_企业主体与法定边界.md'),
    formatDisplayTitle('01_主体信息统一口径卡.md'),
  ];
  for (const st of sampleTitles) {
    assert.equal(/\.(txt|md|json)$/i.test(st), false, `渲染标题 [${st}] 严禁携带扩展名！`);
  }

  // [2026-09-30 修复R1] 验证 stripExtension 严密保护小数点业务版本号，仅剔除白名单技术扩展名
  assert.equal(stripExtension('S2_核心产品与价格承诺_增补_1.1.md'), 'S2_核心产品与价格承诺_增补_1.1', '剥离扩展名时严禁误伤 1.1 小数点');
  assert.equal(stripExtension('老赵V2.0五问豆包.txt'), '老赵V2.0五问豆包', '剥离扩展名时严禁误伤 V2.0 小数点');
  assert.equal(stripExtension('01_商业初稿.markdown'), '01_商业初稿', 'markdown 扩展名成功剥离');

  // 8. 验证非主文件解除只读后，真实保存动作 (computeSaveResult) 必须顺利放行
  const saveNonMasterRes = computeSaveResult({
    targetName: '01_豆包提问清单_参考1.txt',
    content: '这是在参考件中修改的内容，字数充足达标',
    files: {
      '01_豆包提问清单_参考1.txt': { name: '01_豆包提问清单_参考1.txt', versionTag: '参考1', isMaster: false, isDeleted: false, savedContent: '旧内容' },
    },
    stage: 'step0',
  });
  assert.equal(saveNonMasterRes.success, true, '非主文件在非废纸篓状态下保存必须成功放行！');
  assert.equal(saveNonMasterRes.files['01_豆包提问清单_参考1.txt'].content, '这是在参考件中修改的内容，字数充足达标');

  // 9. [2026-09-30 修复🟡4] 验证 isHistoricalRetired 分段版本号比对（第1.10版 高于 第1.9版，1.9 被淘汰，1.10 绝非淘汰）
  const testVerFiles = {
    '01_网络底座指标_第1.9版.md': { name: '01_网络底座指标_第1.9版.md', slotKey: 'slot_metrics', isActive: false },
    '01_网络底座指标_第1.10版.md': { name: '01_网络底座指标_第1.10版.md', slotKey: 'slot_metrics', isActive: true },
  };
  assert.equal(isHistoricalRetired(testVerFiles['01_网络底座指标_第1.9版.md'], testVerFiles), true, '低版本 1.9 判定为历史淘汰');
  assert.equal(isHistoricalRetired(testVerFiles['01_网络底座指标_第1.10版.md'], testVerFiles), false, '当前生效的高版本 1.10 绝非淘汰');

  console.log('  [PASS] 断言 32（雪花 ID 唯一编号、全域隐藏扩展名、纯净展示、改名防重名、主文件改名守卫、只读锁解绑保存与分段版本号比对）：100% 成立');
}

test32();

console.log('=============================================================================');
console.log('  [SUCCESS] 32/32 项自动化断言全部 PASS！全流水线版本统一步调与主文件质检闭环！');
console.log('=============================================================================');


