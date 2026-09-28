/**
 * smoke_studio_artifacts.mjs
 * 阶段零与阶段一 多版本生成采纳与草稿废纸篓安全回档 12 项核心断言冒烟测试脚本
 * 严格遵照 tasks.md 4.6 规范执行
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
} from '../web/step0-src/config/studioArtifactConfig.js';

console.log('>>> 开始执行多版本生成采纳与草稿废纸篓安全回档 12 项自动化断言自检...');

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
  console.log('  [PASS] 断言 1（正则防误读）：前缀 01_ 不被误读为版本 1');
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

  // ④ 空内容保存不洗白骨干
  const emptySave = computeSaveResult({
    targetName: '01_网络底座指标_第2版.md',
    content: '   ',
    files: saveResult.files,
    stage: 'step1',
  });
  assert.equal(emptySave.success, true);
  assert.equal(emptySave.files['01_网络底座指标_待对照.md'].content, '修改后的生效内容', '空内容保存坚决不洗白规范骨干');
  console.log('  [PASS] 断言 6（骨干单向自动镜像等价与内容守卫）：内容守卫严密防洗白');
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
  assert.equal(isReadOnlyFile(files['01_网络底座指标_待对照.md'], files, 'step1'), true, '规范主干镜像强制只读');

  // ② 采纳第 3 版
  const adoptV3 = computeAdoptResult({ candidateName: '01_网络底座指标_第3版.md', files, stage: 'step1' });
  files = adoptV3.files;
  assert.equal(files['01_网络底座指标_第2版.md'].isRetired, true, '被淘汰的第 2 版被打上 isRetired');
  assert.equal(isReadOnlyFile(files['01_网络底座指标_第2版.md'], files, 'step1'), true, '被淘汰版本强制只读');

  // ③ 将第 2 版删入废纸篓
  const delV2 = computeDeleteResult({ filename: '01_网络底座指标_第2版.md', files, stage: 'step1' });
  files = delV2.files;
  assert.equal(files['01_网络底座指标_第2版.md'].isDeleted, true);
  assert.equal(isReadOnlyFile(files['01_网络底座指标_待对照.md'], files, 'step1'), true, '镜像骨干状态绝不漂移，依旧只读');
  assert.equal(isReadOnlyFile(files['01_网络底座指标_第1版.md'], files, 'step1'), true, '首版母版依旧强制只读');
  console.log('  [PASS] 断言 8（规范骨干持久化标记与正交只读科学验证）：生命周期正交状态不漂移');
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
      is_deleted: 'false',
    },
  };

  const migrated1 = migrateAndNormalizeFiles(dirtyData, 'step1');
  assert.equal(migrated1['01_网络底座指标_待对照.md'].name, '01_网络底座指标_待对照.md');
  assert.equal(migrated1['01_网络底座指标_第2版.md'].name, '01_网络底座指标_第2版.md');
  assert.equal(migrated1['04_手建草稿.md'].name, '04_手建草稿.md');

  // active 收敛判定：高版本 (第2版) 保留 active，第1版退级
  assert.equal(migrated1['01_网络底座指标_第2版.md'].isActive, true);
  assert.equal(migrated1['01_网络底座指标_待对照.md'].isActive, false);

  // 幂等性：对已迁移数据再次迁移，结果完全一致
  const migrated2 = migrateAndNormalizeFiles(migrated1, 'step1');
  assert.deepEqual(migrated1, migrated2, '多次迁移必须完全幂等');
  console.log('  [PASS] 断言 10（存量旧数据迁移收敛、不变式与幂等性）：不变式与幂等性满足');
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

console.log('=============================================================================');
console.log('  🎉 12/12 项自动化断言全部 PASS！多版本生成采纳与草稿废纸篓安全回档 逻辑 100% 闭环！');
console.log('=============================================================================');
