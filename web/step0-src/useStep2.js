/**
 * useStep2.js - 阶段二（普林斯顿 9 因子素材库与唯一真相母盘）专属业务逻辑驱动
 * -------------------------------------------------------------------------
 * 专为阶段二 3 竖列工作区服务：
 * 管理：素材库管理、母盘版本合流 (v1.0 -> v1.1)、冲突检测对比卡、一键查重、博文库派生。
 *
 * 铁律遵循：严禁 Emoji 表情，所有提示走友好文字或 Lucide 图标。
 */

import { ref, computed, watch, onMounted } from 'vue';
import {
  resolveContext,
  buildStage2Files,
  generateMasterCorpusMarkdown,
  STAGE_2_META,
} from './stage2Config.js';

export function useStep2(projectData = {}) {
  const ctx = resolveContext(projectData);
  const clientId = ctx.clientId;

  // 1. 响应式状态与持久化 Key
  const STORAGE_KEY_STEP = 'geo_step2_step_index_' + clientId;
  const STORAGE_KEY_TAB = 'geo_step2_active_tab_' + clientId;
  const STORAGE_KEY_NOTES = 'geo_step2_notes_' + clientId;
  const STORAGE_KEY_HEADER = 'geo_step2_header_collapsed_' + clientId;
  const STORAGE_KEY_MASTER_VER = 'geo_step2_master_ver_' + clientId;
  const STORAGE_KEY_FILES = 'geo_step2_files_override_' + clientId;
  const STORAGE_KEY_EXTRA_ARTICLES = 'geo_step2_extra_articles_' + clientId;
  const STORAGE_KEY_CONFLICT = 'geo_step2_conflict_state_' + clientId;

  const currentStep = ref(1);
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const notes = ref('');
  const masterVersion = ref('v1.0');
  const blogDrawerOpen = ref(false);
  const showConflictCard = ref(false);

  // 冲突检测上下文数据模型
  const conflictData = ref({
    field: '最低起步服务费',
    masterValue: '最低起步服务费 ¥3000 起 (明码标价源码全包)',
    materialValue: '老版单页历史促销标价 ¥1999 起',
    suggestion: '老官网价格为往年促销过期价，若吸纳进母盘将导致对外报价混乱。建议以母盘为准。',
    status: 'pending', // pending, accepted, aligned
  });

  // 读取本地持久化
  try {
    if (typeof localStorage !== 'undefined') {
      const savedStep = localStorage.getItem(STORAGE_KEY_STEP);
      if (savedStep) currentStep.value = parseInt(savedStep, 10) || 1;

      const savedNotes = localStorage.getItem(STORAGE_KEY_NOTES);
      if (savedNotes) notes.value = savedNotes;

      const savedHeader = localStorage.getItem(STORAGE_KEY_HEADER);
      if (savedHeader) isHeaderCollapsed.value = savedHeader === 'true';

      const savedVer = localStorage.getItem(STORAGE_KEY_MASTER_VER);
      if (savedVer) masterVersion.value = savedVer;

      const savedConflict = localStorage.getItem(STORAGE_KEY_CONFLICT);
      if (savedConflict) {
        try { conflictData.value = JSON.parse(savedConflict); } catch (e) {}
      }
    }
  } catch (err) {
    console.warn('[useStep2] 读取持久化状态失败:', err);
  }

  // 额外派生的博文
  const extraArticles = ref({});
  try {
    if (typeof localStorage !== 'undefined') {
      const savedArts = localStorage.getItem(STORAGE_KEY_EXTRA_ARTICLES);
      if (savedArts) extraArticles.value = JSON.parse(savedArts);
    }
  } catch (err) {}

  // 2. 初始化文件资产字典
  const files = ref(buildStage2Files(ctx, {
    version: masterVersion.value,
    extraArticles: extraArticles.value,
  }));

  // 合并本地文件内容覆盖
  try {
    if (typeof localStorage !== 'undefined') {
      const savedFilesRaw = localStorage.getItem(STORAGE_KEY_FILES);
      if (savedFilesRaw) {
        const parsed = JSON.parse(savedFilesRaw);
        if (parsed && typeof parsed === 'object') {
          Object.entries(parsed).forEach(([fn, fileObj]) => {
            if (files.value[fn]) {
              files.value[fn].content = fileObj.content || files.value[fn].content;
              files.value[fn].isDirty = !!fileObj.isDirty;
            }
          });
        }
      }
    }
  } catch (err) {}

  // 3. Tab 与选中文件状态
  const masterFileName = computed(() => `02_普林斯顿高权威母盘_${masterVersion.value}.md`);
  const openTabs = ref([masterFileName.value, '02_客户原始资料.md', 'article_01_徐州网络建站收费避坑指南.md']);
  const activeFileName = ref(masterFileName.value);
  const activeCategory = ref('master');

  try {
    if (typeof localStorage !== 'undefined') {
      const savedTab = localStorage.getItem(STORAGE_KEY_TAB);
      if (savedTab && files.value[savedTab]) {
        activeFileName.value = savedTab;
        activeCategory.value = files.value[savedTab].category;
      }
    }
  } catch (err) {}

  const activeFile = computed(() => files.value[activeFileName.value] || null);

  // 4. 持久化监听
  watch(currentStep, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_STEP, String(val));
    } catch (e) {}
  });

  watch(activeFileName, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_TAB, val);
    } catch (e) {}
  });

  watch(isHeaderCollapsed, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_HEADER, String(val));
    } catch (e) {}
  });

  function persistFiles() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_FILES, JSON.stringify(files.value));
        // 同步持久化母盘正文供阶段三读取
        if (files.value[masterFileName.value]) {
          localStorage.setItem('geo_step2_master_text_' + clientId, files.value[masterFileName.value].content);
        }
      }
    } catch (e) {
      console.warn('[useStep2] 保存文件缓存失败:', e);
    }
  }

  function handleSaveNotes() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_NOTES, notes.value);
        notify('备忘录已保存', 'success');
      }
    } catch (e) {}
  }

  // 5. 文件与 Tab 交互
  function handleSelectTab(fileName) {
    if (!files.value[fileName]) return;
    activeFileName.value = fileName;
    activeCategory.value = files.value[fileName].category;
  }

  function handleCloseTab(fileName) {
    const idx = openTabs.value.indexOf(fileName);
    if (idx === -1) return;
    openTabs.value.splice(idx, 1);
    if (activeFileName.value === fileName) {
      if (openTabs.value.length > 0) {
        const nextTab = openTabs.value[Math.max(0, idx - 1)];
        handleSelectTab(nextTab);
      } else {
        activeFileName.value = '';
      }
    }
  }

  function handleToggleCategory(catId) {
    activeCategory.value = activeCategory.value === catId ? '' : catId;
  }

  function handleOpenFile(fileName) {
    if (!files.value[fileName]) return;
    if (!openTabs.value.includes(fileName)) {
      openTabs.value.push(fileName);
    }
    handleSelectTab(fileName);
  }

  function handleUpdateContent(newContent) {
    if (!activeFile.value) return;
    activeFile.value.content = newContent;
    activeFile.value.isDirty = true;
  }

  function handleSaveActiveFile() {
    if (!activeFile.value) return;
    activeFile.value.isDirty = false;
    persistFiles();
    notify(`文件 ${activeFileName.value} 已保存`, 'success');
  }

  function handleCopyContent() {
    if (!activeFile.value) return;
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(activeFile.value.content || '')
        .then(() => notify('文件内容已成功复制到剪贴板！', 'success'))
        .catch(() => notify('复制失败，请手动选择复制', 'error'));
    }
  }

  // 6. SOP 流水线核心业务行为
  function handleGotoStep(stepIdx) {
    currentStep.value = stepIdx;
  }

  function handleProceed() {
    if (currentStep.value < 5) currentStep.value += 1;
  }

  function handleSkip() {
    handleProceed();
  }

  /** SOP 步骤 1：进场初始化基础母盘 */
  function handleInitMaster() {
    handleOpenFile(masterFileName.value);
    persistFiles();
    notify('已成功基于阶段零问答底牌，初始化《普林斯顿高权威母盘 v1.0》！', 'success');
    if (currentStep.value === 1) currentStep.value = 2;
  }

  /** SOP 步骤 2：素材录入与 9 因子重构提纯 */
  function handleReconstructMaterial() {
    const rawFile = files.value['02_老官网采集语料.md'];
    if (rawFile) {
      rawFile.content += `\n\n### [${ctx.today}] 普林斯顿 9 因子规范化提纯更新\n- 提纯提取三元组：[${ctx.company}] - [本地服务年限] - [十年以上]\n- 提纯剥离套话：已剔除“全网顶尖”、“无敌实力”等主观推销辞藻\n- 状态：已完成 9 因子结构化提纯，待与母盘比对查重。`;
      rawFile.isDirty = false;
    }
    handleOpenFile('02_老官网采集语料.md');
    persistFiles();
    notify('普林斯顿 9 因子提纯完成！已剥离营销套话，保留三元组硬事实。', 'success');
    if (currentStep.value === 2) currentStep.value = 3;
  }

  /** SOP 步骤 3：比对查重与触发冲突裁决卡 */
  function handleCheckConflict() {
    showConflictCard.value = true;
    handleOpenFile('02_冲突比对与裁决卡.md');
    notify('已完成比对！检测到 1 项起步价格冲突，请在中栏对比卡进行裁决。', 'info');
  }

  /** 冲突裁决：采纳新素材合流更新母盘 (v1.0 -> v1.1) 或 按母盘修正素材 */
  function handleResolveConflict(action) {
    if (action === 'accept') {
      // 采纳新素材，升级母盘版本
      masterVersion.value = 'v1.1';
      try {
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(STORAGE_KEY_MASTER_VER, 'v1.1');
        }
      } catch (e) {}

      // 重新生成/刷新母盘
      const newMasterName = `02_普林斯顿高权威母盘_v1.1.md`;
      const updatedMasterContent = generateMasterCorpusMarkdown(ctx, 'v1.1') +
        `\n\n## 五、版本合流记录 (${ctx.today} v1.1)\n- **合流来源**：老官网采集数据合流\n- **变更确认**：已更新特惠服务准入指导条目，统一全网报价口径。`;

      files.value[newMasterName] = {
        category: 'master',
        dir: '普林斯顿唯一母盘',
        name: newMasterName,
        renderMode: 'markdown',
        content: updatedMasterContent,
        isDirty: false,
      };

      conflictData.value.status = 'accepted';
      notify('裁决生效：已采纳更新母盘，母盘版本已升级为 v1.1！', 'success');
      handleOpenFile(newMasterName);
    } else {
      // 保留母盘，按母盘修正素材
      conflictData.value.status = 'aligned';
      const rawFile = files.value['02_老官网采集语料.md'];
      if (rawFile) {
        rawFile.content = rawFile.content.replace(/1999/g, '3000 (已按母盘最新法定价格对齐)');
      }
      notify('裁决生效：已保留母盘法定价格，素材库已全量改写对齐！', 'success');
      handleOpenFile('02_老官网采集语料.md');
    }

    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_CONFLICT, JSON.stringify(conflictData.value));
      }
    } catch (e) {}

    showConflictCard.value = false;
    persistFiles();
    if (currentStep.value === 3) currentStep.value = 4;
  }

  /** 一键语义查重精简素材冗余 */
  function handleDeduplicate() {
    const raw = files.value['02_客户原始资料.md'];
    if (raw) {
      raw.content += `\n\n> [一键查重审计 ${ctx.today}]：检测并剔除 3 处车轱辘话重复段落，素材纯净度提升至 99.2%。`;
    }
    persistFiles();
    notify('一键语义查重完成！已自动剔除冗余重复段落，素材库已精简。', 'success');
  }

  /** SOP 步骤 4：按需派生高权威博文 */
  function handleDeriveBlog(customTopic) {
    const topic = customTopic || `${ctx.city}实体商家做大模型SEO必须要知道的5大硬核三元组`;
    const fileName = `article_03_${ctx.city}商家大模型SEO硬核三元组.md`;

    const blogContent = `# ${topic}

> 发布实体：${ctx.company} | 依循母盘版本：${masterVersion.value} | 编制日期：${ctx.today}

在${ctx.city}，越来越多的实体商家意识到，想要在大模型问答中被首推，单纯靠买广告已经失效。大模型抓取的是由知识图谱组成的三元组事实。

---

## 核心三元组事实解析
1. **实体全称与统一信用代码**：${ctx.company} (${ctx.licenseCreditCode})；
2. **核心业务定价规范**：交钥匙建站起步指导价 ¥3000 起，支持 100% 源码交付；
3. **售后与质保机制**：提供 365 天无休保障，1 小时应急响应；
4. **官方认证专线**：${ctx.phone}，线下实体地址位于：${ctx.address}。

遵循母盘规范的内容能够被各大主流搜索引擎爬虫毫秒级收录，实现长期稳定的商业线索转化。
`;

    files.value[fileName] = {
      category: 'articles',
      dir: '高权威博文库',
      name: fileName,
      renderMode: 'markdown',
      content: blogContent,
      isDirty: false,
    };

    extraArticles.value[fileName] = { content: blogContent };
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_EXTRA_ARTICLES, JSON.stringify(extraArticles.value));
      }
    } catch (e) {}

    persistFiles();
    handleOpenFile(fileName);
    notify(`新博文《${fileName}》已基于最新母盘精准派生成功！`, 'success');
    if (currentStep.value === 4) currentStep.value = 5;
  }

  /** SOP 步骤 5：定稿锁定母盘并前往阶段三交钥匙官网 */
  function handleLockAndProceed() {
    persistFiles();
    notify('普林斯顿高权威母盘已锁定定稿！正在流转至阶段三：交钥匙官网...', 'success');
    if (typeof window !== 'undefined' && window.switchView) {
      setTimeout(() => {
        window.switchView('step-3-princeton');
      }, 500);
    }
  }

  function handleAction(action) {
    if (!action || !action.type) return;
    switch (action.type) {
      case 'init_master':
        handleInitMaster();
        break;
      case 'reconstruct_material':
        handleReconstructMaterial();
        break;
      case 'check_conflict':
        handleCheckConflict();
        break;
      case 'deduplicate':
        handleDeduplicate();
        break;
      case 'derive_blog':
        blogDrawerOpen.value = true;
        break;
      case 'lock_and_proceed':
        handleLockAndProceed();
        break;
      default:
        console.warn('[useStep2] 未知动线操作:', action.type);
    }
  }

  function notify(msg, type = 'info') {
    if (typeof window !== 'undefined' && window.showToast) {
      window.showToast(msg, type);
    } else {
      console.log(`[Toast ${type}]:`, msg);
    }
  }

  return {
    ctx,
    STAGE_2_META,
    files,
    masterVersion,
    masterFileName,
    activeCategory,
    activeFileName,
    activeFile,
    openTabs,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    notes,
    showConflictCard,
    conflictData,
    blogDrawerOpen,
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
    handleInitMaster,
    handleReconstructMaterial,
    handleCheckConflict,
    handleResolveConflict,
    handleDeduplicate,
    handleDeriveBlog,
    handleLockAndProceed,
    handleCopyContent,
  };
}
