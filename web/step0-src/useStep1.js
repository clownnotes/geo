/**
 * useStep1.js - 阶段一业务逻辑与状态管理 Composable
 * [2026-09-27] 支持本地持久化（步骤前进保存、文件打磨保存、备注保存、门禁选项保存）
 * [2026-09-27] 支持联动顶栏折叠/展开「概览卡片」
 */
import { ref, computed, onUnmounted } from 'vue';
import { resolveContext, buildStage1Files, STAGE_1_META, buildCrawledMetricsMarkdown } from './stage1Config.js';
import {
  resolveSlotKey,
  computeNextVersion,
  computeBranchVersion,
  computeSaveResult,
  computeAdoptResult,
  computeRestoreResult,
  computeDeleteResult,
  migrateAndNormalizeFiles,
  formatReason,
  activateTabInStack,
  isMasterFile,
  isDuplicateDisplayName,
  generateSnowflakeId,
} from './config/studioArtifactConfig.js';

export function getSlotKey(filename) {
  return resolveSlotKey(filename, 'step1');
}

export function useStep1(projectData = {}) {
  const ctx = resolveContext(projectData);
  const clientId = projectData.client_id || projectData.id || 'default';
  const storageKey = `geo_step1_state_${clientId}`;

  // 1. 尝试从 localStorage 恢复阶段一历史进度与打磨保存的内容
  let savedState = null;
  if (typeof localStorage !== 'undefined') {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) savedState = JSON.parse(raw);
    } catch (_) {}
  }

  const initialFiles = buildStage1Files(ctx);
  const mergedFiles = { ...initialFiles };
  // 如果之前编辑并保存了文件，恢复保存的内容与多版本状态
  if (savedState && savedState.files) {
    Object.keys(savedState.files).forEach((fn) => {
      const sf = savedState.files[fn];
      if (initialFiles[fn]) {
        // [2026-09-27] [底牌溯源继承] 阶段零问答素材属于上游交付物底牌，始终采用最新生效血统章
        if (fn !== '01_阶段零豆包实测问答素材.md') {
          let content = sf.content;
          // 如果历史初稿未打上溯源血统章，自动补齐
          if (fn === '01_商业诊断与转化初稿.md' && content && !content.includes('[溯源血统]')) {
            const stamp = `> [溯源血统]：本报告基于阶段零生效底牌【${ctx.activeQaVersion}】（${ctx.activeQuestionFile} + ${ctx.activeAnswerFile}）直出\n\n`;
            content = content.replace(/^#\s+[^\n]+\n\n?/, (match) => match + stamp);
          }
          mergedFiles[fn].content = content;
          mergedFiles[fn].savedContent = content;
          mergedFiles[fn].isDirty = false;
        }
        // [2026-09-28] 恢复槽位、采纳状态、版本标签、生成时间戳与废纸篓软删除标记
        if (sf.slotKey) mergedFiles[fn].slotKey = sf.slotKey;
        if (sf.isActive !== undefined) mergedFiles[fn].isActive = sf.isActive;
        if (sf.versionTag) mergedFiles[fn].versionTag = sf.versionTag;
        if (sf.generatedAt) mergedFiles[fn].generatedAt = sf.generatedAt;
        if (sf.isDeleted !== undefined) mergedFiles[fn].isDeleted = sf.isDeleted;
        else if (sf.is_deleted !== undefined) mergedFiles[fn].isDeleted = sf.is_deleted;
        if (sf.isRetired !== undefined) mergedFiles[fn].isRetired = sf.isRetired;
        if (sf.isCanonicalMirror !== undefined) mergedFiles[fn].isCanonicalMirror = sf.isCanonicalMirror;
        if (sf.isProtectedArchive !== undefined) mergedFiles[fn].isProtectedArchive = sf.isProtectedArchive;
        if (sf.isManual !== undefined) mergedFiles[fn].isManual = sf.isManual;
        if (sf.displayName) mergedFiles[fn].displayName = sf.displayName;
        if (sf.id) mergedFiles[fn].id = sf.id;
      } else if (sf && typeof sf === 'object') {
        // 动态派生的草稿文件（如新版本候选试算草稿），恢复至工作区
        mergedFiles[fn] = {
          name: fn,
          category: sf.category || 'materials',
          slotKey: sf.slotKey || resolveSlotKey(fn, 'step1', sf.isManual),
          renderMode: fn.endsWith('.html') ? 'html' : 'markdown',
          content: sf.content || '',
          savedContent: sf.content || '',
          isDirty: false,
          isActive: sf.isActive || false,
          isRetired: sf.isRetired || false,
          isCanonicalMirror: sf.isCanonicalMirror || false,
          isProtectedArchive: sf.isProtectedArchive || false,
          isManual: sf.isManual || false,
          displayName: sf.displayName || '',
          id: sf.id || '',
          versionTag: sf.versionTag || 'V2-Draft',
          generatedAt: sf.generatedAt || '',
          isDeleted: sf.isDeleted !== undefined ? sf.isDeleted : Boolean(sf.is_deleted),
        };
      }
    });
  }

  // [2026-09-28] [SSOT收敛] 统一经过 migrateAndNormalizeFiles 清洗存量数据与收敛单一 active
  const files = ref(migrateAndNormalizeFiles(mergedFiles, 'step1'));
  const activeCategory = ref(savedState?.activeCategory || 'materials');
  const activeFileName = ref(savedState?.activeFileName || '01_网络底座指标_待对照.md');
  const openTabs = ref(savedState?.openTabs || ['01_网络底座指标_待对照.md', '01_阶段零豆包实测问答素材.md']);
  const currentStep = ref(savedState?.currentStep || 1); // 1: 对照, 2: 润色初稿, 3: 出具报告
  const selectedGate = ref(savedState?.selectedGate || 'confirmed');
  // [2026-09-28] [阶段一底座抓取动线视线引导优化] 增加底座抓取完成态响应式状态，消除断层感
  const crawledMetrics = ref(savedState?.crawledMetrics || false);
  const isCrawling = ref(false); // [2026-09-28] 真机底座指标网络探测 loading 状态
  const mckinseyVisible = ref(false);
  const fullscreenVisible = ref(false);

  // 2. 顶栏阶段概览看板折叠状态：跟随全局偏好
  const isHeaderCollapsed = ref(
    typeof localStorage !== 'undefined' ? localStorage.getItem('geo_step0_overview_collapsed') === '1' : false
  );

  // [2026-09-27] [生命周期规范] 监听顶栏收纳/展开全局事件，并在组件卸载时彻底移除防内存泄漏
  function handleOverviewToggle(e) {
    isHeaderCollapsed.value = Boolean(e.detail?.collapsed);
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('geo-toggle-step-overview', handleOverviewToggle);
  }
  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('geo-toggle-step-overview', handleOverviewToggle);
    }
  });

  // 交付备注状态（优先从本地存储恢复，其次从 projectData 恢复）
  const notes = ref(savedState?.notes ?? (projectData.stage1_notes || projectData.delivery_notes || ''));

  // 3. 统一持久化状态到 localStorage
  function saveState() {
    if (typeof localStorage === 'undefined') return;
    try {
      const stateToSave = {
        currentStep: currentStep.value,
        activeFileName: activeFileName.value,
        activeCategory: activeCategory.value,
        openTabs: openTabs.value,
        selectedGate: selectedGate.value,
        notes: notes.value,
        crawledMetrics: crawledMetrics.value, // [2026-09-28] 持久化底座抓取完成态
        files: Object.fromEntries(
          Object.entries(files.value).map(([k, v]) => [
            k,
            {
              content: v.content,
              isDirty: v.isDirty,
              isActive: v.isActive,
              isRetired: v.isRetired,
              isCanonicalMirror: v.isCanonicalMirror,
              isProtectedArchive: v.isProtectedArchive,
              isManual: v.isManual,
              versionTag: v.versionTag,
              generatedAt: v.generatedAt,
              isDeleted: Boolean(v.isDeleted),
              category: v.category,
              displayName: v.displayName || '',
              id: v.id || '',
              slotKey: v.slotKey || resolveSlotKey(k, 'step1', v.isManual),
            },
          ])
        ),
      };
      localStorage.setItem(storageKey, JSON.stringify(stateToSave));
    } catch (err) {
      // [2026-09-27] [日志可观测性] 异常不静默吞掉，输出结构化 warn 告警
      console.warn('[useStep1] 本地持久化保存失败，可能超出存储限额:', err);
    }
  }

  // 当前激活文件与渲染模式
  const activeFile = computed(() => files.value[activeFileName.value] || null);
  const currentRenderMode = computed(() => {
    const fn = (activeFileName.value || '').toLowerCase();
    if (fn.endsWith('.html') || fn.endsWith('.htm')) return 'html';
    if (fn.endsWith('.md')) return 'markdown';
    return 'code';
  });

  // [2026-09-29] [智能Tab栈] 新激活Tab首置到最左侧(索引0)，超量6个自动关闭最右侧干净Tab
  function handleSelectTab(fn) {
    if (!fn) return;
    const { newOpenTabs, warningDirty } = activateTabInStack(
      openTabs.value,
      fn,
      files.value,
      6
    );
    openTabs.value = newOpenTabs;
    activeFileName.value = fn;
    const cat = files.value[fn]?.category;
    if (cat) activeCategory.value = cat;
    if (warningDirty) {
      showStudioToast('已有 6 个修改未保存的标签页，请先保存部分文件', 'warning');
    }
    saveState();
  }

  function handleCloseTab(fn) {
    const idx = openTabs.value.indexOf(fn);
    if (idx !== -1) {
      openTabs.value.splice(idx, 1);
      if (activeFileName.value === fn) {
        activeFileName.value = openTabs.value[Math.max(0, idx - 1)] || '';
      }
      saveState();
    }
  }

  function handleToggleCategory(catId) {
    activeCategory.value = activeCategory.value === catId ? '' : catId;
    saveState();
  }

  function handleOpenFile(fn) {
    handleSelectTab(fn);
  }

  function handleUpdateContent(newVal) {
    if (files.value[activeFileName.value]) {
      files.value[activeFileName.value].content = newVal;
      files.value[activeFileName.value].isDirty = true;
    }
  }

  // [2026-09-28] [SSOT收敛] 保存文件统一接入 computeSaveResult
  function handleSaveActiveFile() {
    const currentFn = activeFileName.value;
    const currentF = files.value[currentFn];
    if (!currentF) return;

    const res = computeSaveResult({
      targetName: currentFn,
      content: currentF.content,
      files: files.value,
      stage: 'step1',
    });
    if (!res.success) {
      if (res.reason === 'READ_ONLY_LOCKED') {
        showStudioToast('该文件为只读状态，无法保存！', 'warning');
      } else {
        showStudioToast(`保存失败: ${formatReason(res.reason)}`, 'error');
      }
      return;
    }
    files.value = res.files;
    saveState();
    showStudioToast('文件保存成功！(已保存至本地)');
  }

  // [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 设为客户采纳版本（工序槽位精准隔离）
  function handleAdoptFile(filename) {
    const res = computeAdoptResult({
      candidateName: filename,
      files: files.value,
      stage: 'step1',
    });
    if (!res.success) {
      if (res.reason === 'EMPTY_CONTENT') {
        showStudioToast('候选版本内容为空，拒绝采纳！', 'warning');
      } else {
        showStudioToast(`采纳失败: ${formatReason(res.reason)}`, 'error');
      }
      return;
    }
    files.value = res.files;
    saveState();
    showStudioToast(`已将【${filename}】设为客户采纳生效版本！`);
  }

  // [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 软删除草稿文件（Fail-Closed 保护与平滑回退）
  function handleDeleteFile(filename) {
    const res = computeDeleteResult({
      filename,
      files: files.value,
      stage: 'step1',
      currentSelected: activeFileName.value,
      openTabs: openTabs.value,
    });
    if (!res.success) {
      if (res.reason === 'FILE_PROTECTED_CANNOT_DELETE') {
        showStudioToast('已采纳底牌或核心规范骨干受系统保护，无法删除！', 'warning');
      } else {
        showStudioToast(`删除失败: ${formatReason(res.reason)}`, 'error');
      }
      return;
    }
    files.value = res.files;
    openTabs.value = res.newOpenTabs;
    if (res.nextSelected) {
      handleSelectTab(res.nextSelected);
    } else {
      activeFileName.value = '';
    }
    saveState();
    showStudioToast(`已将草稿【${filename}】移入废纸篓，可在左侧底部展开恢复`);
  }

  // [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 从废纸篓还原文件
  function handleRestoreFile(filename) {
    const res = computeRestoreResult({
      filename,
      files: files.value,
      stage: 'step1',
    });
    if (!res.success) {
      showStudioToast(`恢复失败: ${formatReason(res.reason)}`, 'error');
      return;
    }
    files.value = res.files;
    handleSelectTab(filename);
    saveState();
    showStudioToast(`已成功恢复草稿【${filename}】并打开`);
  }

  function handleGateChange(gateVal) {
    selectedGate.value = gateVal;
    saveState();
  }

  // [2026-09-27] [动线一致性] 点击步骤头部跳转时，联动切换打开该步骤对应的 activeFile
  function handleGotoStep(stepNum) {
    currentStep.value = stepNum;
    const targetStep = STAGE_1_META.sopSteps && STAGE_1_META.sopSteps[stepNum - 1];
    if (targetStep && targetStep.activeFile) {
      handleSelectTab(targetStep.activeFile);
    } else {
      saveState();
    }
  }

  async function handleSaveNotes(newNotes) {
    notes.value = newNotes;
    saveState();
    showStudioToast('交付情况备注已保存！');
    return true;
  }

  function handleCopyContent() {
    const text = activeFile.value?.content || '';
    if (!text) {
      showStudioToast('当前文件内容为空', 'warning');
      return;
    }
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        showStudioToast('内容已复制到剪贴板，可粘贴至外部 IDE / 豆包');
      }).catch(() => {
        showStudioToast('复制失败，请手动选取复制', 'error');
      });
    } else {
      showStudioToast('当前环境不支持剪贴板API，请手动选取复制', 'warning');
    }
  }

  async function handleAction(actionType) {
    if (actionType === 'crawlMetrics') {
      if (isCrawling.value) return;
      isCrawling.value = true;
      try {
        const token = typeof window !== 'undefined' ? window.currentAuthToken || '' : '';
        const pid = typeof window !== 'undefined' ? window.currentProjectId || ctx.clientId : ctx.clientId;

        const res = await fetch(`/api/projects/${encodeURIComponent(pid)}/run/audit`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ mode: 'crawl' }),
        });
        const data = await res.json();
        if (data.success) {
          // [2026-09-28] [阶段一底座抓取动线视线引导优化] 根据后端真机探测指标实时重构并回填中栏
          const freshMarkdown = buildCrawledMetricsMarkdown(ctx, data.metrics || {});
          const nowStr = new Date().toLocaleString('zh-CN', { hour12: false });
          const baseFile = files.value['01_网络底座指标_待对照.md'];
          // 若此前从未抓取过（crawledMetrics 为 false 且待对照文件未有生成时间戳），作为初次抓取填充基线底座
          const isReCrawl = crawledMetrics.value || Boolean(baseFile?.generatedAt);

          if (!isReCrawl && baseFile) {
            crawledMetrics.value = true;
            baseFile.content = freshMarkdown;
            baseFile.savedContent = freshMarkdown;
            baseFile.isDirty = false;
            baseFile.generatedAt = nowStr;
            baseFile.isActive = true;
            baseFile.versionTag = 'V1';
            baseFile.slotKey = 'slot_metrics';
            handleSelectTab('01_网络底座指标_待对照.md');
            saveState();
            showStudioToast('已完成抓取：真实底座指标已就绪！请核对中栏数据，确认无误后点击下方【前往出具初稿】');
          } else {
            // [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 重新抓取：扫描全量历史（含废纸篓）递增生成新版本候选草稿
            crawledMetrics.value = true;
            const { nextVer, nextFileName, nextVersionTag } = computeNextVersion(files.value, 'slot_metrics');
            const newName = nextFileName;
            files.value[newName] = {
              name: newName,
              category: 'materials',
              dir: 'materials',
              renderMode: 'markdown',
              slotKey: 'slot_metrics',
              content: freshMarkdown,
              savedContent: freshMarkdown,
              isDirty: false,
              isActive: false, // 候选草稿，原底牌继续保持生效受保护
              versionTag: nextVersionTag,
              generatedAt: nowStr,
              isDeleted: false,
            };
            handleSelectTab(newName);
            saveState();
            showStudioToast(`已完成重新抓取！已生成新候选版本【${newName}】，可核对后设为采纳`);
          }
        } else {
          showStudioToast(`探测失败: ${data.message || '网络连接超时'}`, 'error');
        }
      } catch (err) {
        showStudioToast(`请求失败: ${err.message}`, 'error');
      } finally {
        isCrawling.value = false;
      }
    } else if (actionType === 'generateDraft') {
      const nowStr = new Date().toLocaleString('zh-CN', { hour12: false });
      // [2026-09-29] [初稿成套版本生成] 提取版本号（优先匹配阶段零生效版本，如 QA-V3 -> 3，若无则从底座指标提取）
      const mQa = (ctx.activeQaVersion || '').match(/(\d+)/);
      const metricsFile = Object.values(files.value).find(f => f.slotKey === 'slot_metrics' && f.isActive);
      const mMetrics = (metricsFile?.versionTag || '').match(/(\d+)/);
      const verNum = mQa ? parseInt(mQa[1], 10) : (mMetrics ? parseInt(mMetrics[1], 10) : 1);
      const masterDraftName = verNum <= 1 ? '01_商业诊断与转化初稿.md' : `01_商业诊断与转化初稿_第${verNum}版.md`;

      const existingMaster = files.value[masterDraftName];
      // [2026-09-29] [解决 🟡2] 显式基于 isGenerated 判定是否此前已出具过主版本，避免模板自带 generatedAt 误触发分支生成
      const hasGeneratedBefore = Boolean(existingMaster?.isGenerated);

      // [2026-09-29] [初稿派生分支] 若该主版本初稿此前已出具过，再次点击表示对当前稿件不满意，自动派生 V1.1/Vx.1 微调分支
      if (hasGeneratedBefore && existingMaster) {
        const { nextFileName, nextVersionTag, majorNum, nextBranch } = computeBranchVersion(
          files.value,
          masterDraftName,
          'slot_draft'
        );
        const baseContent = existingMaster.content || '';
        const bloodStamp = `> [溯源血统]：本报告基于阶段零生效底牌【${ctx.activeQaVersion || `QA-V${verNum}`}】出具微调分支 (版本: V${majorNum}.${nextBranch})\n\n`;
        const branchContent = baseContent.includes('[溯源血统]')
          ? baseContent.replace(/> \[溯源血统\][^\n]+\n\n?/, bloodStamp)
          : bloodStamp + baseContent;

        files.value[nextFileName] = {
          name: nextFileName,
          category: 'drafts',
          dir: '过程草稿',
          renderMode: 'markdown',
          slotKey: 'slot_draft',
          content: branchContent,
          savedContent: branchContent,
          isDirty: false,
          isActive: false, // 灵感分支不抢占主版本采纳状态，保持主干干净
          isRetired: false,
          isBranchDraft: true, // 核心分支标记
          isGenerated: true,
          versionTag: nextVersionTag,
          generatedAt: nowStr,
          isDeleted: false,
        };

        handleSelectTab(nextFileName);
        saveState();
        showStudioToast(`已在 V${majorNum} 基础上派生微调分支【${nextFileName}】！可对比打磨或复制到外部大模型`);
      } else {
        // 首次出具该套主版本初稿（不论是初版 V1 还是新版 Vn，统一通过 computeAdoptResult 收敛执行采纳）
        const targetDraftName = verNum <= 1 ? '01_商业诊断与转化初稿.md' : `01_商业诊断与转化初稿_第${verNum}版.md`;
        let targetDraft = files.value[targetDraftName];
        if (!targetDraft) {
          const baseContent = files.value['01_商业诊断与转化初稿.md']?.content || '';
          // 注入新版血统章
          const bloodStamp = `> [溯源血统]：本报告基于阶段零生效底牌【${ctx.activeQaVersion || `QA-V${verNum}`}】直出 (版本: V${verNum})\n\n`;
          const stampedContent = baseContent.includes('[溯源血统]')
            ? baseContent.replace(/> \[溯源血统\][^\n]+\n\n?/, bloodStamp)
            : bloodStamp + baseContent;

          files.value[targetDraftName] = {
            name: targetDraftName,
            category: 'drafts',
            dir: '过程草稿',
            renderMode: 'markdown',
            slotKey: 'slot_draft',
            content: stampedContent,
            savedContent: stampedContent,
            isDirty: false,
            isActive: false, // 先作为候选草稿，随后交由 computeAdoptResult 严格执行采纳流转
            isRetired: false,
            isGenerated: true,
            versionTag: `V${verNum}`,
            generatedAt: nowStr,
            isDeleted: false,
          };
        } else {
          targetDraft.generatedAt = nowStr;
          targetDraft.isGenerated = true;
          targetDraft.versionTag = `V${verNum}`;
        }

        // [2026-09-29] [SSOT纯函数收口] 统一接入 computeAdoptResult，彻底消除手写退级与镜像，自证单槽 active 唯一
        const adoptRes = computeAdoptResult({
          candidateName: targetDraftName,
          files: files.value,
          stage: 'step1',
        });
        if (adoptRes.success) {
          files.value = adoptRes.files;
          files.value[targetDraftName].isGenerated = true;
        } else {
          console.warn('[generateDraft] computeAdoptResult 采纳流转失败:', adoptRes.reason);
        }
        handleSelectTab(targetDraftName);

        saveState();
        showStudioToast(`商业诊断与转化初稿 (V${verNum}) 已就绪！可复制去外部润色`);
      }
    } else if (actionType === 'generateFinalReports') {
      const nowStr = new Date().toLocaleString('zh-CN', { hour12: false });
      const currentDraft = Object.values(files.value).find(f => f.slotKey === 'slot_draft' && f.isActive);
      const mDraft = (currentDraft?.versionTag || '').match(/(\d+)/);
      const verNum = mDraft ? parseInt(mDraft[1], 10) : 1;

      const screenName = verNum <= 1 ? '01_老板商业诊断报告_好看大屏.html' : `01_老板商业诊断报告_好看大屏_第${verNum}版.html`;
      const textName = verNum <= 1 ? '01_老板商业诊断报告_文字版.md' : `01_老板商业诊断报告_文字版_第${verNum}版.md`;

      const baseScreenContent = files.value['01_老板商业诊断报告_好看大屏.html']?.content || '';
      if (!files.value[screenName]) {
        files.value[screenName] = {
          name: screenName,
          category: 'reports',
          dir: '最终交付报告',
          renderMode: 'html',
          slotKey: 'slot_report_screen',
          content: baseScreenContent,
          savedContent: baseScreenContent,
          isDirty: false,
          isActive: false, // 先作为候选草稿
          isRetired: false,
          versionTag: `V${verNum}`,
          generatedAt: nowStr,
          isDeleted: false,
        };
      } else {
        files.value[screenName].generatedAt = nowStr;
        files.value[screenName].versionTag = `V${verNum}`;
      }

      const baseTextContent = files.value['01_老板商业诊断报告_文字版.md']?.content || '';
      if (!files.value[textName]) {
        files.value[textName] = {
          name: textName,
          category: 'reports',
          dir: '最终交付报告',
          renderMode: 'markdown',
          slotKey: 'slot_report_text',
          content: baseTextContent,
          savedContent: baseTextContent,
          isDirty: false,
          isActive: false, // 先作为候选草稿
          isRetired: false,
          versionTag: `V${verNum}`,
          generatedAt: nowStr,
          isDeleted: false,
        };
      } else {
        files.value[textName].generatedAt = nowStr;
        files.value[textName].versionTag = `V${verNum}`;
      }

      // [2026-09-29] [SSOT纯函数收口] 统一调用 computeAdoptResult 纯函数执行采纳流转与主干镜像，彻底消除手写 isActive
      const resScreen = computeAdoptResult({
        candidateName: screenName,
        files: files.value,
        stage: 'step1',
      });
      if (resScreen.success) {
        files.value = resScreen.files;
      } else {
        console.warn('[generateFinalReports] screen 采纳流转失败:', resScreen.reason);
      }

      const resText = computeAdoptResult({
        candidateName: textName,
        files: files.value,
        stage: 'step1',
      });
      if (resText.success) {
        files.value = resText.files;
      } else {
        console.warn('[generateFinalReports] text 采纳流转失败:', resText.reason);
      }

      // [2026-09-29] [解决 🟡7] 统一走 handleSelectTab (接入 activateTabInStack) 保障 6 个 Tab 上限
      handleSelectTab(textName);
      handleSelectTab(screenName);

      saveState();
      showStudioToast(`多版本商业诊断报告 (V${verNum}) 已就绪！`);
    } else if (actionType === 'openFullscreen') {
      fullscreenVisible.value = true;
    } else if (actionType === 'copyClientLink') {
      const origin = typeof window !== 'undefined' ? window.location.origin : '';
      const link = origin + '/conversion_report.html?brand=' + encodeURIComponent(ctx.brand);
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        navigator.clipboard.writeText(link).then(() => {
          showStudioToast('对客报告链接已复制！可直接发微信发给老板');
        });
      } else {
        showStudioToast('对客报告链接: ' + link);
      }
    }
  }

  function handleProceed() {
    if (currentStep.value === 1) {
      currentStep.value = 2;
      handleSelectTab('01_商业诊断与转化初稿.md');
      saveState();
      showStudioToast('第 1 步已确认并保存，进入第 2 步初稿润色');
    } else if (currentStep.value === 2) {
      currentStep.value = 3;
      handleSelectTab('01_老板商业诊断报告_好看大屏.html');
      saveState();
      showStudioToast('初稿润色已保存，进入第 3 步多版本交付报告');
    } else if (currentStep.value === 3) {
      saveState();
      showStudioToast('阶段一商业转化诊断顺利通关！即将进入阶段二...');
      setTimeout(() => {
        if (typeof window !== 'undefined') {
          if (typeof window.switchStep === 'function') {
            window.switchStep(2);
          } else if (typeof window.switchView === 'function') {
            window.switchView('step-2-scaffold');
          }
        }
      }, 800);
    }
  }

  function handleSkip() {
    currentStep.value = 3;
    handleSelectTab('01_老板商业诊断报告_好看大屏.html');
    saveState();
    showStudioToast('已跳过润色并保存进度，直接生成最终交付报告');
  }

  // [2026-09-27] [安全合并刷新] 增量合并底座模板，只补齐缺失文件或更新未打磨项，严格保留用户已保存的打磨成果
  function handleRefreshFiles() {
    const latestTemplates = buildStage1Files(ctx);
    const currentFiles = files.value;
    let preservedCount = 0;

    Object.keys(latestTemplates).forEach((fn) => {
      const templateItem = latestTemplates[fn];
      const existing = currentFiles[fn];
      if (!existing) {
        // 1. 缺失文件：直接增量补齐
        currentFiles[fn] = templateItem;
      } else {
        // 2. 已有文件：检查用户是否进行过个性化打磨并保存
        const isUserModified = existing.isDirty || (existing.savedContent !== undefined && existing.savedContent !== templateItem.content);
        if (isUserModified) {
          preservedCount++;
          // 保留现有打磨内容，仅更新分类、目录与渲染模式等元数据
          existing.category = templateItem.category;
          existing.dir = templateItem.dir;
          existing.renderMode = templateItem.renderMode;
        } else {
          // 未打磨项：同步最新底座模板
          existing.content = templateItem.content;
          existing.savedContent = templateItem.content;
          existing.category = templateItem.category;
          existing.dir = templateItem.dir;
          existing.renderMode = templateItem.renderMode;
          existing.isDirty = false;
        }
      }
    });

    files.value = { ...currentFiles };
    saveState();
    if (preservedCount > 0) {
      showStudioToast(`资产目录已同步最新底座（已安全保留 ${preservedCount} 个打磨文件）！`);
    } else {
      showStudioToast('阶段一商业资产目录已同步最新底座！');
    }
  }

  function showStudioToast(msg, type = 'success') {
    if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
      window.showToast(msg, type);
    } else {
      console.log(`[Toast ${type}] ${msg}`);
    }
  }

  // [2026-09-30 修复🔴5] 阶段一主文件右键重命名、雪花ID锚点绑定与本地持久化
  function handleRenameFile({ fn, newDisplayName }) {
    const target = files.value[fn];
    if (!target) return;
    if (!isMasterFile(target)) {
      showStudioToast('参考件由系统自管编号，仅主文件支持修改名称！', 'warning');
      return;
    }
    const trimmed = (newDisplayName || '').trim();
    if (!trimmed) return;
    if (isDuplicateDisplayName(files.value, fn, trimmed)) {
      showStudioToast('名称已存在，不能重复！', 'warning');
      return;
    }
    target.displayName = trimmed;
    if (!target.id) {
      target.id = generateSnowflakeId();
    }
    saveState();
    showStudioToast(`主文件已成功改名为【${trimmed}】`, 'success');
  }

  return {
    STAGE_1_META,
    files,
    activeCategory,
    activeFileName,
    activeFile,
    openTabs,
    currentStep,
    selectedGate,
    crawledMetrics, // [2026-09-28] 暴露底座指标抓取完成状态
    isCrawling,     // [2026-09-28] 暴露底座指标真机探测 loading 状态
    currentRenderMode,
    isHeaderCollapsed,
    mckinseyVisible,
    fullscreenVisible,
    notes,
    handleSelectTab,
    handleCloseTab,
    handleToggleCategory,
    handleOpenFile,
    handleUpdateContent,
    handleSaveActiveFile,
    handleSaveNotes,
    handleGateChange,
    handleGotoStep,
    handleCopyContent,
    handleAction,
    handleProceed,
    handleSkip,
    handleRefreshFiles,
    handleAdoptFile,
    handleDeleteFile,
    handleRestoreFile,
    handleRenameFile,
  };
}
