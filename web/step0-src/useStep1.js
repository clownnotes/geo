/**
 * useStep1.js - 阶段一业务逻辑与状态管理 Composable
 * [2026-09-27] 支持本地持久化（步骤前进保存、文件打磨保存、备注保存、门禁选项保存）
 * [2026-09-27] 支持联动顶栏折叠/展开「概览卡片」
 */
import { ref, computed, onUnmounted } from 'vue';
import { resolveContext, buildStage1Files, STAGE_1_META, buildCrawledMetricsMarkdown } from './stage1Config.js';

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
  // 如果之前编辑并保存了文件，恢复保存的内容
  if (savedState && savedState.files) {
    Object.keys(savedState.files).forEach((fn) => {
      if (initialFiles[fn]) {
        // [2026-09-27] [底牌溯源继承] 阶段零问答素材属于上游交付物底牌，始终采用最新生效血统章
        if (fn === '01_阶段零豆包实测问答素材.md') {
          return;
        }
        let content = savedState.files[fn].content;
        // 如果历史初稿未打上溯源血统章，自动补齐
        if (fn === '01_商业诊断与转化初稿.md' && content && !content.includes('[溯源血统]')) {
          const stamp = `> [溯源血统]：本报告基于阶段零生效底牌【${ctx.activeQaVersion}】（${ctx.activeQuestionFile} + ${ctx.activeAnswerFile}）直出\n\n`;
          content = content.replace(/^#\s+[^\n]+\n\n?/, (match) => match + stamp);
        }
        initialFiles[fn].content = content;
        initialFiles[fn].savedContent = content;
        initialFiles[fn].isDirty = false;
      }
    });
  }

  const files = ref(initialFiles);
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
          Object.entries(files.value).map(([k, v]) => [k, { content: v.content, isDirty: v.isDirty }])
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

  // Tab 切换与关闭
  function handleSelectTab(fn) {
    activeFileName.value = fn;
    if (!openTabs.value.includes(fn)) {
      openTabs.value.push(fn);
    }
    const cat = files.value[fn]?.category;
    if (cat) activeCategory.value = cat;
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

  function handleSaveActiveFile() {
    if (files.value[activeFileName.value]) {
      files.value[activeFileName.value].savedContent = files.value[activeFileName.value].content;
      files.value[activeFileName.value].isDirty = false;
      saveState();
      showStudioToast('文件保存成功！(已保存至本地)');
    }
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
          crawledMetrics.value = true;
          // [2026-09-28] [阶段一底座抓取动线视线引导优化] 根据后端真机探测指标实时重构并回填中栏
          const freshMarkdown = buildCrawledMetricsMarkdown(ctx, data.metrics || {});
          if (files.value['01_网络底座指标_待对照.md']) {
            files.value['01_网络底座指标_待对照.md'].content = freshMarkdown;
            files.value['01_网络底座指标_待对照.md'].savedContent = freshMarkdown;
            files.value['01_网络底座指标_待对照.md'].isDirty = false;
          }
          handleSelectTab('01_网络底座指标_待对照.md');
          saveState();
          showStudioToast('已完成抓取：真实底座指标已就绪！请核对中栏数据，确认无误后点击下方【前往出具初稿】');
        } else {
          showStudioToast(`探测失败: ${data.message || '网络连接超时'}`, 'error');
        }
      } catch (err) {
        showStudioToast(`请求失败: ${err.message}`, 'error');
      } finally {
        isCrawling.value = false;
      }
    } else if (actionType === 'generateDraft') {
      handleSelectTab('01_商业诊断与转化初稿.md');
      saveState();
      showStudioToast('商业诊断与转化初稿已生成！可复制去外部润色');
    } else if (actionType === 'generateFinalReports') {
      handleSelectTab('01_老板商业诊断报告_好看大屏.html');
      if (!openTabs.value.includes('01_老板商业诊断报告_文字版.md')) {
        openTabs.value.push('01_老板商业诊断报告_文字版.md');
      }
      saveState();
      showStudioToast('多版本商业诊断报告已就绪！');
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
  };
}
