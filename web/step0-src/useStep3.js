/**
 * useStep3.js - 阶段三（交钥匙官网与大模型三件套）专属业务逻辑驱动
 * -----------------------------------------------------------------
 * 专为阶段三 3 竖列工作台服务：
 * 管理：企业底牌响应式状态、5 大交付物编译产物、本地持久化、多端视口切换、动线闭环。
 *
 * 铁律遵循：严禁 Emoji 表情，所有提示走友好文字或 Lucide 图标。
 */

import { ref, computed, watch, onMounted } from 'vue';
import {
  resolveContext,
  getDefaultSiteInfo,
  buildStage3Files,
  STAGE_3_META,
} from './stage3Config.js';

export function useStep3(projectData = {}) {
  const ctx = resolveContext(projectData);
  const clientId = ctx.clientId;

  // 1. 企业底牌对象持久化
  const siteInfo = ref(getDefaultSiteInfo(ctx));
  const STORAGE_KEY_SITE = 'geo_step3_site_info_' + clientId;
  const STORAGE_KEY_STEP = 'geo_step3_step_index_' + clientId;
  const STORAGE_KEY_TAB = 'geo_step3_active_tab_' + clientId;
  const STORAGE_KEY_NOTES = 'geo_step3_notes_' + clientId;
  const STORAGE_KEY_HEADER = 'geo_step3_header_collapsed_' + clientId;
  const STORAGE_KEY_FILES = 'geo_step3_files_override_' + clientId;

  try {
    if (typeof localStorage !== 'undefined') {
      // 优先读 step3 站点底牌信息（已清理历史无写入方的 geo_step2_site_info_ 死引用，R8-6）
      const savedInfo = localStorage.getItem(STORAGE_KEY_SITE);
      if (savedInfo) {
        const parsed = JSON.parse(savedInfo);
        if (parsed && typeof parsed === 'object') {
          siteInfo.value = Object.assign(getDefaultSiteInfo(ctx), parsed);
        }
      }
    }
  } catch (err) {
    console.warn('[useStep3] 读取本地底牌数据异常:', err);
  }

  // 2. 5 大交付物文件字典
  const files = ref(buildStage3Files(ctx, siteInfo.value));

  // 恢复之前微调保存的文件内容（若有）
  try {
    if (typeof localStorage !== 'undefined') {
      const savedFiles = localStorage.getItem(STORAGE_KEY_FILES);
      if (savedFiles) {
        const parsed = JSON.parse(savedFiles);
        if (parsed && typeof parsed === 'object') {
          Object.keys(parsed).forEach(fn => {
            if (files.value[fn]) {
              files.value[fn].content = parsed[fn];
            }
          });
        }
      }
    }
  } catch (err) {
    console.warn('[useStep2] 恢复持久化文件内容异常:', err);
  }

  // 3. Tab 与视图状态
  const openTabs = ref(['index.html', 'llms.txt', 'schema.jsonld']);
  const activeFileName = ref('index.html');
  const activeCategory = ref('sites');
  const currentStep = ref(1);
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const fullscreenVisible = ref(false);
  const drawerOpen = ref(false);
  const isCompiling = ref(false);
  const notes = ref('');

  // 视口与预览模式：'desktop' | 'mobile'
  const viewportMode = ref('desktop');
  // 'preview' | 'code'
  const dualViewMode = ref('preview');

  // 初始化持久化恢复
  try {
    if (typeof localStorage !== 'undefined') {
      const savedStep = localStorage.getItem(STORAGE_KEY_STEP);
      if (savedStep) currentStep.value = Math.min(Math.max(parseInt(savedStep, 10) || 1, 1), 3);

      const savedTab = localStorage.getItem(STORAGE_KEY_TAB);
      if (savedTab && files.value[savedTab]) {
        activeFileName.value = savedTab;
        activeCategory.value = files.value[savedTab].category;
      }

      const savedNotes = localStorage.getItem(STORAGE_KEY_NOTES);
      if (savedNotes) notes.value = savedNotes;

      const savedH = localStorage.getItem(STORAGE_KEY_HEADER);
      if (savedH !== null) isHeaderCollapsed.value = savedH === 'true';
    }
  } catch (err) {
    console.warn('[useStep3] 读取界面持久化状态异常:', err);
  }

  watch(isHeaderCollapsed, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_HEADER, String(val));
    } catch (e) {}
  });

  const activeFile = computed(() => files.value[activeFileName.value] || null);

  const currentRenderMode = computed(() => {
    if (!activeFile.value) return 'code';
    if (activeFileName.value === 'index.html') {
      return dualViewMode.value === 'preview' ? 'html' : 'code';
    }
    return activeFile.value.renderMode || 'code';
  });

  // 4. 操作与事件
  function handleSelectTab(fn) {
    if (!files.value[fn]) return;
    activeFileName.value = fn;
    activeCategory.value = files.value[fn].category;
    if (!openTabs.value.includes(fn)) {
      openTabs.value.push(fn);
    }
    try {
      localStorage.setItem(STORAGE_KEY_TAB, fn);
    } catch (_) {}
  }

  function handleCloseTab(fn) {
    const idx = openTabs.value.indexOf(fn);
    if (idx === -1) return;
    openTabs.value.splice(idx, 1);
    if (activeFileName.value === fn) {
      if (openTabs.value.length > 0) {
        handleSelectTab(openTabs.value[Math.max(0, idx - 1)]);
      } else {
        activeFileName.value = '';
      }
    }
  }

  function handleToggleCategory(catId) {
    activeCategory.value = activeCategory.value === catId ? '' : catId;
  }

  function handleOpenFile(fn) {
    handleSelectTab(fn);
  }

  function handleUpdateContent(newVal) {
    if (!activeFile.value) return;
    activeFile.value.content = newVal;
    activeFile.value.isDirty = true;
  }

  function handleSaveActiveFile() {
    if (!activeFile.value) return;
    activeFile.value.isDirty = false;
    persistFilesOverride();
    showToast(`文件 [${activeFileName.value}] 已保存至本地！`);
  }

  function persistFilesOverride() {
    try {
      const overrides = {};
      Object.keys(files.value).forEach(k => {
        overrides[k] = files.value[k].content;
      });
      localStorage.setItem(STORAGE_KEY_FILES, JSON.stringify(overrides));
    } catch (e) {
      console.warn('[useStep2] 持久化文件覆盖内容失败:', e);
    }
  }

  function handleSaveNotes(val) {
    notes.value = val;
    try {
      localStorage.setItem(STORAGE_KEY_NOTES, val);
      showToast('阶段二备忘录已保存！');
    } catch (_) {}
  }

  function handleGotoStep(stepNum) {
    currentStep.value = stepNum;
    try {
      localStorage.setItem(STORAGE_KEY_STEP, String(stepNum));
    } catch (_) {}
  }

  function handleProceed() {
    if (currentStep.value < 3) {
      handleGotoStep(currentStep.value + 1);
    }
  }

  function handleSkip() {
    handleProceed();
  }

  // 一键重新编译交钥匙整站
  function handleCompile() {
    isCompiling.value = true;
    setTimeout(() => {
      // 重新生成 5 大交付物
      files.value = buildStage3Files(ctx, siteInfo.value);
      persistFilesOverride();
      // 持久化底牌
      try {
        localStorage.setItem(STORAGE_KEY_SITE, JSON.stringify(siteInfo.value));
      } catch (_) {}

      isCompiling.value = false;
      showToast('交钥匙极速官网与大模型三件套编译完成！');

      // 动线前进到步骤 2 或 3
      if (currentStep.value === 1) {
        handleGotoStep(2);
      } else if (currentStep.value === 2) {
        handleGotoStep(3);
      }
    }, 450);
  }

  // 动作路由
  function handleAction(type) {
    if (type === 'open_drawer') {
      drawerOpen.value = true;
    } else if (type === 'compile_site') {
      handleCompile();
    } else if (type === 'open_pure_site') {
      handleOpenPureSite();
    } else if (type === 'copy_nginx') {
      handleCopyNginx();
    }
  }

  // 独立新窗口打开纯净官网
  function handleOpenPureSite() {
    const html = files.value['index.html']?.content || '';
    if (!html) {
      showToast('暂无生成的官网内容，请先点击编译！', 'error');
      return;
    }
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  }

  // 复制 VPS Nginx 配置
  function handleCopyNginx() {
    const conf = files.value['nginx.conf']?.content || '';
    copyTextToClipboard(conf, 'VPS Nginx 反代配置已复制到剪贴板！');
  }

  // 复制当前激活文件内容
  function handleCopyContent() {
    if (!activeFile.value) return;
    copyTextToClipboard(activeFile.value.content, `[${activeFileName.value}] 内容已复制到剪贴板！`);
  }

  // 导出源码包
  function handleExportZip() {
    // 纯前端下载 index.html
    const html = files.value['index.html']?.content || '';
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${siteInfo.value.brandName}_交钥匙官网_index.html`;
    a.click();
    showToast('交钥匙官网单页已开始下载！');
  }

  // 重置底牌至默认
  function handleResetSiteInfo() {
    siteInfo.value = getDefaultSiteInfo(ctx);
    files.value = buildStage3Files(ctx, siteInfo.value);
    persistFilesOverride();
    try {
      localStorage.removeItem(STORAGE_KEY_SITE);
    } catch (_) {}
    showToast('已重置为智能预填默认底牌！');
  }

  function copyTextToClipboard(text, successMsg) {
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg);
      }).catch(() => {
        fallbackCopy(text, successMsg);
      });
    } else {
      fallbackCopy(text, successMsg);
    }
  }

  function fallbackCopy(text, successMsg) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast(successMsg);
    } catch (e) {
      showToast('复制失败，请手动选取代码复制', 'error');
    } finally {
      document.body.removeChild(ta);
    }
  }

  function showToast(msg, type = 'success') {
    if (typeof window !== 'undefined' && window.showToast) {
      window.showToast(msg, type);
    } else {
      console.log(`[Toast ${type}]:`, msg);
    }
  }

  return {
    ctx,
    STAGE_3_META,
    STAGE_2_META: STAGE_3_META,
    siteInfo,
    files,
    activeCategory,
    activeFileName,
    activeFile,
    openTabs,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    fullscreenVisible,
    drawerOpen,
    isCompiling,
    notes,
    viewportMode,
    dualViewMode,
    currentRenderMode,
    handleSelectTab,
    handleCloseTab,
    handleToggleCategory,
    handleOpenFile,
    handleUpdateContent,
    handleSaveActiveFile,
    handleSaveNotes,
    handleGotoStep,
    handleProceed,
    handleSkip,
    handleAction,
    handleCompile,
    handleOpenPureSite,
    handleCopyNginx,
    handleCopyContent,
    handleExportZip,
    handleResetSiteInfo,
  };
}
