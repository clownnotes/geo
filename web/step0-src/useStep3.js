/**
 * useStep3.js - 阶段三（03 企业母盘与统一口径卡）专属业务逻辑驱动
 * =========================================================================================
 * [2026-09-30] [阶段三母盘构建] 业务对象模型与动线闭环 Hook：
 * 1. 管理左侧文件树（01_主体信息统一口径卡.md、02_普林斯顿企业事实母盘.md）；
 * 2. 动线 1：一键从阶段二 S1~S6 规范主文件萃取合流（严格过滤 1.x 增补切片）；
 * 3. 动线 2：实时消歧与三级业务描述质检（50字/120字红绿灯与 GEO 中文全称指示灯）；
 * 4. 动线 3：客观瑕疵排查交互式勾选与对冲话术回填；
 * 5. 动线 4：锁定母盘定稿，一键解锁前往阶段四交钥匙官网。
 */

import { ref, reactive, computed, watch, onMounted } from 'vue';
import {
  STAGE_3_META,
  resolveStage3Context,
  generateUnifiedIdentityCard,
  validateUnifiedCard,
  synthesizePrincetonMaster,
} from './stage3Config.js';
import {
  safeStorageGet,
  safeStorageSet,
  filterMasterSourceFiles,
  isMasterFile,
  isDuplicateDisplayName,
  generateSnowflakeId,
  computeDeleteResult,
  formatReason,
} from './config/studioArtifactConfig.js';

export function useStep3(projectData = {}) {
  const ctx = resolveStage3Context(projectData);
  const clientId = ctx.clientId;

  // 1. 本地存储持久化 Key 定义
  const STORAGE_KEY_STEP = 'geo_step3_step_index_' + clientId;
  const STORAGE_KEY_FILES = 'geo_step3_files_' + clientId;
  const STORAGE_KEY_ACTIVE_FILE = 'geo_step3_active_file_' + clientId;
  const STORAGE_KEY_NOTES = 'geo_step3_notes_' + clientId;
  const STORAGE_KEY_HEADER = 'geo_step3_header_collapsed_' + clientId;
  const STORAGE_KEY_HEDGE = 'geo_step3_hedge_options_' + clientId;
  const STORAGE_KEY_LOCKED = 'geo_step3_master_locked_' + clientId;

  // 2. 核心状态机
  const currentStep = ref(1);
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const notes = ref('');
  const toastMessage = ref('');
  const toastVisible = ref(false);
  const isExtracting = ref(false);
  const isMasterLocked = ref(false);

  // 瑕疵交互式排查勾选项
  const hedgeOptions = reactive({
    zeroSocialSecurity: true, // 0 参保
    crossCityAddress: false, // 异地经营
    historicalBusiness: false, // 历史业务沿革
  });

  // 文件管理状态
  const files = ref({});
  const activeFileName = ref('01_主体信息统一口径卡.md');
  const activeCategory = ref('identity_card');
  const openTabs = ref(['01_主体信息统一口径卡.md', '02_普林斯顿企业事实母盘.md']);

  // 初始化文件槽位
  function initDefaultFiles() {
    const defaultCard = generateUnifiedIdentityCard(projectData, '', hedgeOptions);
    const defaultMaster = synthesizePrincetonMaster({}, projectData);

    return {
      '01_主体信息统一口径卡.md': {
        name: '01_主体信息统一口径卡.md',
        slotKey: 'slot_stage3_identity_card',
        category: 'identity_card',
        content: defaultCard,
        versionTag: 'V1',
        isActive: true,
        isDirty: false,
        updatedAt: ctx.today,
      },
      '02_普林斯顿企业事实母盘.md': {
        name: '02_普林斯顿企业事实母盘.md',
        slotKey: 'slot_stage3_master',
        category: 'master_corpus',
        content: defaultMaster,
        versionTag: 'V1',
        isActive: true,
        isDirty: false,
        updatedAt: ctx.today,
      },
    };
  }

  // 恢复本地持久化数据
  function restoreState() {
    try {
      const savedStep = safeStorageGet(STORAGE_KEY_STEP, 1);
      if (savedStep) currentStep.value = Number(savedStep) || 1;

      const savedLocked = safeStorageGet(STORAGE_KEY_LOCKED, false);
      if (savedLocked !== null) isMasterLocked.value = Boolean(savedLocked);

      const savedHedge = safeStorageGet(STORAGE_KEY_HEDGE, null);
      if (savedHedge && typeof savedHedge === 'object') {
        Object.assign(hedgeOptions, savedHedge);
      }

      const savedFiles = safeStorageGet(STORAGE_KEY_FILES, null);
      if (savedFiles && typeof savedFiles === 'object' && Object.keys(savedFiles).length > 0) {
        files.value = savedFiles;
      } else {
        files.value = initDefaultFiles();
      }

      const savedActive = safeStorageGet(STORAGE_KEY_ACTIVE_FILE, '01_主体信息统一口径卡.md');
      if (savedActive && files.value[savedActive]) {
        activeFileName.value = savedActive;
      }

      const savedNotes = safeStorageGet(STORAGE_KEY_NOTES, '');
      if (savedNotes) notes.value = savedNotes;

      const savedHeader = safeStorageGet(STORAGE_KEY_HEADER, false);
      if (savedHeader !== null) isHeaderCollapsed.value = Boolean(savedHeader);
    } catch (e) {
      console.warn('[useStep3] 恢复缓存异常:', e);
      files.value = initDefaultFiles();
    }
  }

  function persistFiles() {
    safeStorageSet(STORAGE_KEY_FILES, files.value);
  }

  function showToast(msg) {
    toastMessage.value = msg;
    toastVisible.value = true;
    setTimeout(() => {
      toastVisible.value = false;
    }, 2800);
  }

  // 当前选中文件对象
  const activeFile = computed(() => {
    return files.value[activeFileName.value] || null;
  });

  // 口径卡实时合规校验结果 (指示灯)
  const cardAudit = computed(() => {
    const cardContent = files.value['01_主体信息统一口径卡.md']?.content || '';
    return validateUnifiedCard(cardContent);
  });

  // 阶段二素材库就绪度检查 (检查 S1~S6 是否齐备)
  const stage2Readiness = computed(() => {
    let sCount = 0;
    try {
      const raw = safeStorageGet('geo_step2_files_' + clientId, null);
      if (raw && typeof raw === 'object') {
        const masters = filterMasterSourceFiles(raw);
        sCount = Object.keys(masters).length;
      }
    } catch (_) {}
    return {
      masterCount: sCount,
      isFullyReady: sCount >= 6,
    };
  });

  // 1. 动线 1：一键从阶段二 S1~S6 素材合流萃取母盘初稿
  function handleExtractFromStage2() {
    isExtracting.value = true;
    try {
      let stage2Files = {};
      const raw = safeStorageGet('geo_step2_files_' + clientId, null);
      if (raw && typeof raw === 'object') {
        stage2Files = raw;
      }

      // 获取阶段二 S1 内容
      let s1Body = '';
      for (const [fn, f] of Object.entries(stage2Files)) {
        if (fn.startsWith('S1') && f && f.content) {
          s1Body = f.content;
          break;
        }
      }

      // 生成消歧卡初稿与普林斯顿母盘熟料
      const newCard = generateUnifiedIdentityCard(projectData, s1Body, hedgeOptions);
      const newMaster = synthesizePrincetonMaster(stage2Files, projectData);

      files.value['01_主体信息统一口径卡.md'] = {
        ...files.value['01_主体信息统一口径卡.md'],
        content: newCard,
        isDirty: false,
        updatedAt: ctx.today,
      };

      files.value['02_普林斯顿企业事实母盘.md'] = {
        ...files.value['02_普林斯顿企业事实母盘.md'],
        content: newMaster,
        isDirty: false,
        updatedAt: ctx.today,
      };

      persistFiles();
      currentStep.value = 2; // 进入第二步核验
      safeStorageSet(STORAGE_KEY_STEP, 2);
      showToast('已成功从阶段二 S1~S6 萃取合流生成消歧口径卡与事实母盘！');
    } catch (err) {
      console.error('[useStep3] 提取母盘异常:', err);
      showToast('提取素材失败，请检查阶段二素材数据完整性');
    } finally {
      isExtracting.value = false;
    }
  }

  // 2. 动线 3：应用瑕疵对冲选项并自动回填口径卡
  function handleToggleHedgeOption(key) {
    if (hedgeOptions.hasOwnProperty(key)) {
      hedgeOptions[key] = !hedgeOptions[key];
      safeStorageSet(STORAGE_KEY_HEDGE, hedgeOptions);

      // 自动刷新口径卡（已内置打扫卫生与对冲指引）
      const updatedCard = generateUnifiedIdentityCard(projectData, '', hedgeOptions);

      if (files.value['01_主体信息统一口径卡.md']) {
        files.value['01_主体信息统一口径卡.md'].content = updatedCard;
      }
      persistFiles();
      showToast('已更新客观瑕疵合规对冲指引！');
    }
  }

  // 3. 动线 4：锁定母盘并前往阶段四交钥匙官网
  function handlePromoteToStage4() {
    if (!cardAudit.value.isValid) {
      showToast('口径卡存在严重违规项（见红灯提示），请修正后再锁定！');
      return;
    }

    isMasterLocked.value = true;
    safeStorageSet(STORAGE_KEY_LOCKED, true);
    currentStep.value = 4;
    safeStorageSet(STORAGE_KEY_STEP, 4);

    // 将母盘数据存入全局共享槽位，供阶段四官网三件套直接消费
    const masterText = files.value['02_普林斯顿企业事实母盘.md']?.content || '';
    const cardText = files.value['01_主体信息统一口径卡.md']?.content || '';
    safeStorageSet('geo_step3_master_text_' + clientId, masterText);
    safeStorageSet('geo_step3_card_text_' + clientId, cardText);

    showToast('母盘已核定锁定！即将跳转阶段四交钥匙官网...');

    setTimeout(() => {
      if (typeof window !== 'undefined' && typeof window.switchView === 'function') {
        window.switchView('step-4-website');
      }
    }, 800);
  }

  // 文件与标签操作
  function handleSelectTab(fn) {
    if (files.value[fn]) {
      activeFileName.value = fn;
      safeStorageSet(STORAGE_KEY_ACTIVE_FILE, fn);
    }
  }

  function handleCloseTab(fn) {
    if (openTabs.value.length <= 1) return;
    openTabs.value = openTabs.value.filter((name) => name !== fn);
    if (activeFileName.value === fn) {
      activeFileName.value = openTabs.value[0];
      safeStorageSet(STORAGE_KEY_ACTIVE_FILE, activeFileName.value);
    }
  }

  function handleOpenFile(fn) {
    if (files.value[fn]) {
      if (!openTabs.value.includes(fn)) {
        openTabs.value.push(fn);
      }
      activeFileName.value = fn;
      safeStorageSet(STORAGE_KEY_ACTIVE_FILE, fn);
    }
  }

  function handleToggleCategory(catId) {
    activeCategory.value = activeCategory.value === catId ? '' : catId;
  }

  function handleUpdateContent(newContent) {
    if (activeFile.value) {
      activeFile.value.content = newContent;
      activeFile.value.isDirty = true;
    }
  }

  function handleSaveActiveFile() {
    if (activeFile.value) {
      activeFile.value.isDirty = false;
      activeFile.value.updatedAt = ctx.today;
      persistFiles();
      showToast(`已成功保存 ${activeFileName.value}`);
    }
  }

  function handleSaveNotes() {
    safeStorageSet(STORAGE_KEY_NOTES, notes.value);
    showToast('交付备忘录已保存');
  }

  // [2026-09-30 修复🔴5] 阶段三主文件右键重命名、雪花ID锚点绑定与本地持久化
  function handleRenameFile({ fn, newDisplayName }) {
    const target = files.value[fn];
    if (!target) return;
    if (!isMasterFile(target)) {
      showToast('参考件由系统自管编号，仅主文件支持修改名称！');
      return;
    }
    const trimmed = (newDisplayName || '').trim();
    if (!trimmed) return;
    if (isDuplicateDisplayName(files.value, fn, trimmed)) {
      showToast('名称已存在，不能重复！');
      return;
    }
    target.displayName = trimmed;
    if (!target.id) {
      target.id = generateSnowflakeId();
    }
    persistFiles();
    showToast(`主文件已成功改名为【${trimmed}】`);
  }

  // [2026-09-30 修复🔴3] 阶段三文件移入废纸篓处理（主文件神圣不可删拦截 + 参考件软删除）
  function handleDeleteFile(filename) {
    const res = computeDeleteResult({
      filename,
      files: files.value,
      stage: 'step3',
    });
    if (!res.success) {
      showToast(formatReason ? formatReason(res.reason) : '主文件神圣不可删除！', 'warning');
      return;
    }
    const target = files.value[filename];
    if (target) {
      target.isDeleted = true;
      target.deletedAt = new Date().toISOString();
      target.isActive = false;
      handleCloseTab(filename);
      persistFiles();
      showToast(`已将【${filename}】移入废纸篓`);
    }
  }

  onMounted(() => {
    restoreState();
  });

  return {
    STAGE_3_META,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    notes,
    toastMessage,
    toastVisible,
    isExtracting,
    isMasterLocked,
    hedgeOptions,
    files,
    activeFileName,
    activeCategory,
    activeFile,
    openTabs,
    cardAudit,
    stage2Readiness,
    handleExtractFromStage2,
    handleToggleHedgeOption,
    handlePromoteToStage4,
    handleSelectTab,
    handleCloseTab,
    handleOpenFile,
    handleToggleCategory,
    handleUpdateContent,
    handleSaveActiveFile,
    handleSaveNotes,
    handleRenameFile,
    handleDeleteFile,
    showToast,
  };
}

export default useStep3;
