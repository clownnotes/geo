<template>
  <!-- [2026-09-23] [阶段零子步骤解耦] 阶段零 Vue3 根组件：一页只干一件事，去掉右侧拥挤SOP，工作台拉宽，底部提供通关动线 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 (根据当前子步骤动态展现专属标题、目标与备注) -->
    <StageHeader
      id="step0-header-card"
      :stage-title="currentSubMeta.title"
      :mode-tag="currentSubMeta.modeTag"
      :is-ready="isReady"
      :target-text="currentSubMeta.target"
      :notes="currentNotes"
      :notes-placeholder="currentSubMeta.placeholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="currentNotes = $event"
      @save-notes="handleSaveCurrentNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 专业交付工作台 (左资源树 + 中间编辑区 + 右侧 SOP 面板) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[700px] min-h-[580px]">
      <!-- 左栏：资源管理器 (纯粹化：仅展示当前子步骤对应的文件分类) -->
      <StudioFileTree
        :stage="'step0'"
        :categories="currentStepCategories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        :show-status-badge="true"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @new-file="handlePromptNewFile"
        @refresh-files="handleRefreshFiles"
        @delete-file="handleDeleteFile"
        @restore-file="handleRestoreFile"
        @rename-file="handleRenameFile"
      />

      <!-- 中间：多 Tab 编辑打磨区 -->
      <StudioEditor
        :stage="'step0'"
        :valid-adopt-slots="getSlotsByStage('step0')"
        :open-tabs="openTabs"
        :active-file-name="activeFileName"
        :files="files"
        @select-tab="handleSelectTab"
        @close-tab="handleCloseTab"
        @update-content="handleUpdateContent"
        @copy-content="handleCopyContent"
        @save-file="handleSaveActiveFile"
        @adopt-file="handleAdoptFile"
        @restore-file="handleRestoreFile"
      />

      <!-- 右栏：SOP 交付动线面板 (三级微动线指引，平铺展示当前小节操作) -->
      <StudioSop
        :current-step="currentSubStep"
        :stage-meta="currentStageMeta"
        :expand-all="true"
        :is-ready="isReady"
        @switch-step="goToSubStep"
        @refresh-questions="handleRefreshQuestions"
        @save-file="handleSaveActiveFile"
        @adopt-current-file="() => handleAdoptFile(activeFileName)"
        @finish-stage0="handleFinishStage0"
      />
    </div>

    <!-- 4. 麦肯锡 V-W-W-H 避坑手册抽屉组件 -->
    <MckinseyDrawer
      :visible="mckinseyVisible"
      :title="'阶段零：麦肯锡认知与避坑手册'"
      :value-desc="'做完后，项目里会有：<strong>① 一份提问清单</strong>；<strong>② 一份豆包真实回答记录</strong>。'"
      :value-business="'后面写什么文章、补什么官网，都拿这份真实回答当对照，不再凭感觉瞎写。'"
      :what-title="'提问查清现状，不是建词库'"
      :what-desc="'就像看病前先量个血压：挑 5 句客户行业里真人常问的话去问豆包。只管查清楚它认不认识你们、推谁、有没有说错。不改官网、不建正式词库。'"
      :why-title="'防止闭门造车与盲人摸象'"
      :why-desc="'很多客户以为大模型什么都懂，其实常把客户当竞品或根本搜不到。不查清现状就发文章 = 盲人摸象。先找出答错、漏答的地方，后面优化才有的放矢。'"
      :how-title="'极简两步闭环（约 2 分钟）'"
      :how-steps="[
        '<strong>1. 出题</strong>：在 0.1 页面打磨 5 道核心题；',
        '<strong>2. 真问并收口</strong>：在 0.2 页面前往豆包提问并贴回回答，一键完成阶段零！'
      ]"
      @close="mckinseyVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import StageHeader from './components/StageHeader.vue';
import StudioFileTree from './components/studio/StudioFileTree.vue';
import StudioEditor from './components/studio/StudioEditor.vue';
import StudioSop from './components/studio/StudioSop.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import {
  CANONICAL_SLOT_DICT,
  computeNextVersion,
  computeReferenceVersion,
  isMasterFile,
  computeSaveResult,
  computeAdoptResult,
  computeRestoreResult,
  computeDeleteResult,
  migrateAndNormalizeFiles,
  getSlotsByStage,
  formatReason,
  activateTabInStack,
  generateSnowflakeId,
  isDuplicateDisplayName,
  getMasterFileForSlot,
} from './config/studioArtifactConfig.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

// 状态管理
const mckinseyVisible = ref(false);
const isHeaderCollapsed = ref(false);
const currentSubStep = ref(1); // 1, 2, 3
const activeCategory = ref('questions');
const activeFileName = ref('');
const openTabs = ref([]);
const files = ref({});
const projectData = ref({});

const isReady = computed(() => projectData.value?.probe_status === 'baseline_ready');

// [2026-09-23] [阶段零子页面纯粹化] 阶段零仅包含出题打磨与提问拿答案两个子步骤
const subMetaMap = {
  1: {
    title: '0.1 准备题目：打磨提问清单',
    modeTag: '出题阶段',
    target: '由交付专家将 AI 出题从 60 分打磨至 80 分，产出真实可用的提问清单。',
    placeholder: '记录题目打磨备忘（如：徐州本地老牌客户，第3题避开低端营销词...）',
    category: 'questions',
    notesField: 'stage0_q_notes',
  },
  2: {
    title: '0.2 网页提问拿答案：真机提问贴回答',
    modeTag: '提问拿答案',
    target: '前往豆包网页版逐题提问，把豆包真实回答贴回中间文件，一键完成阶段零！',
    placeholder: '记录实测备忘（如：第2题豆包识别准确，第4题答得偏泛...）',
    category: 'answers',
    notesField: 'stage0_a_notes',
  },
};

const currentSubMeta = computed(() => subMetaMap[currentSubStep.value] || subMetaMap[1]);

// [2026-09-30] [全流水线版本统一步调与首版预置建档] 0.1 准备题目动线：建档即预置主文件，重新出题生成参考件，对比挑词吸收
const STAGE0_SUB1_META = {
  sopTitle: '0.1 准备题目动线',
  sopSteps: [
    {
      id: 'view_or_refresh',
      name: '1. 查看主文件或出参考题',
      desc: '建档即预置主文件清单。若需换一批激发灵感，可点击下方生成参考件。',
      extraAction: { label: '重新出题（生成参考件）', icon: 'sparkles', type: 'refreshQuestions' },
      hideProceed: true
    },
    {
      id: 'edit_in_editor',
      name: '2. 中间区润色打磨',
      desc: '交付专家可在中间编辑器直接润色修改主文件，修改后随时点击下方保存存盘。',
      action: { label: '保存当前润色修改', icon: 'save', type: 'saveCurrentFile' },
      hideProceed: true
    },
    {
      id: 'compare_and_polish',
      name: '3. 对比挑选打磨主文件',
      desc: '对比参考题与主文件，挑词吸收至主文件后保存，下游步骤将 100% 消费此主文件。',
      action: { label: '保存主文件修改', icon: 'check-circle-2', type: 'saveCurrentFile' },
      hideProceed: true
    }
  ]
};

const STAGE0_SUB2_META = {
  sopTitle: '0.2 网页提问动线',
  sopSteps: [
    {
      id: 'copy_questions',
      name: '1. 一键复制提问内容',
      desc: '点击中间编辑区的【一键复制内容】，获得打磨完毕的提问清单。',
      hideProceed: true
    },
    {
      id: 'ask_doubao_web',
      name: '2. 豆包网页版逐题提问',
      desc: '前往豆包网页版逐题提问，观察并记录 AI 推荐的服务商和排位。',
      linkAction: { label: '打开豆包网页版提问', icon: 'external-link', href: 'https://www.doubao.com' },
      hideProceed: true
    },
    {
      id: 'paste_and_save_answers',
      name: '3. 贴回实测回答并封版',
      desc: '将豆包的实测回答完整贴回中间的 02 回答记录文件，点击下方完成阶段零封版。',
      action: { label: '保存并封版完成阶段零', icon: 'check-circle-2', type: 'finishStage0' },
      hideProceed: true
    }
  ]
};

const currentStageMeta = computed(() => currentSubStep.value === 2 ? STAGE0_SUB2_META : STAGE0_SUB1_META);

// 交付备注计算与绑定
const currentNotes = computed({
  get() {
    const p = projectData.value;
    const f = currentSubMeta.value.notesField;
    return (p && p[f]) || p.delivery_notes || '';
  },
  set(val) {
    const p = projectData.value;
    const f = currentSubMeta.value.notesField;
    if (p) {
      p[f] = val;
      p.delivery_notes = val;
    }
  }
});

const allCategories = [
  { id: 'questions', name: '豆包出的题目' },
  { id: 'answers', name: '豆包实测回答' },
];

// [2026-09-23] [阶段零子页面纯粹化] 这一页只展示当前子步骤对应的文件分类，隐藏无关分类
const currentStepCategories = computed(() => {
  const catId = subMetaMap[currentSubStep.value]?.category || 'questions';
  return allCategories.filter((c) => c.id === catId);
});

const MAX_TABS = 6;

// 工具 Toast
function showToast(msg, type = 'success') {
  if (typeof window !== 'undefined' && window.showToast) {
    window.showToast(msg, type);
  } else {
    console.log(`[Toast ${type}]`, msg);
  }
}

// 切换子步骤并联动文件区与 Tab 纯粹化
function setSubStep(stepNum) {
  const n = parseInt(stepNum, 10);
  if (n >= 1 && n <= 3) {
    currentSubStep.value = n;
    const targetCat = subMetaMap[n].category;
    activeCategory.value = targetCat;

    // [2026-09-23] [阶段零子页面纯粹化] 编辑区 Tab 栏自动收敛为当前步骤分类，不混杂其他步骤的文件
    openTabs.value = openTabs.value.filter(
      (fn) => files.value[fn] && files.value[fn].category === targetCat
    );

    // 打开对应分类下的最新文件
    const catFiles = Object.keys(files.value).filter(
      (fn) => files.value[fn].category === targetCat && !files.value[fn].isDeleted
    );
    if (catFiles.length > 0) {
      handleOpenFile(catFiles[catFiles.length - 1]);
    } else {
      activeFileName.value = '';
    }

    nextTick(() => {
      if (window.lucide) window.lucide.createIcons();
    });
  }
}

function goToSubStep(n) {
  setSubStep(n);
  if (typeof window !== 'undefined' && window.switchStep0SubStep) {
    window.switchStep0SubStep(n);
  }
}

// [2026-09-27] [阶段零生效底牌封版与通关] 封版当前激活的题目与回答，将最新 activeQaVersion、activeQuestionFile、activeAnswerFile 持久化至 localStorage
async function handleFinishStage0() {
  await handleSaveActiveFile();

  const pId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';

  // 1. 查找当前生效的题目与回答文件（排除废纸篓文件）
  const activeQFile = Object.values(files.value).find(f => f.category === 'questions' && f.isActive && !f.isDeleted)
    || Object.values(files.value).find(f => f.category === 'questions' && !f.isDeleted);
  const activeAFile = Object.values(files.value).find(f => f.category === 'answers' && f.isActive && !f.isDeleted)
    || Object.values(files.value).find(f => f.category === 'answers' && !f.isDeleted);

  const activeQaVersion = (activeQFile && activeQFile.versionTag)
    || (activeAFile && activeAFile.versionTag)
    || 'QA-V1';

  const activeQuestionFile = activeQFile ? activeQFile.name : '01_豆包提问清单_推荐版.txt';
  const activeAnswerFile = activeAFile ? activeAFile.name : '02_豆包实测回答记录_初测.txt';

  // 确保状态闭环互指并标记 5 点质检 isConfirmed 确认状态
  if (activeQFile) {
    activeQFile.isActive = true;
    activeQFile.isConfirmed = true;
    activeQFile.versionTag = activeQaVersion;
    activeQFile.pairFile = activeAnswerFile;
  }
  if (activeAFile) {
    activeAFile.isActive = true;
    activeAFile.isConfirmed = true;
    activeAFile.versionTag = activeQaVersion;
    activeAFile.pairFile = activeQuestionFile;
  }

  // 2. 持久化最新生效底牌至纯前端 localStorage（严禁修改后端任何文件）
  const storageKey = `geo_step0_active_qa_${pId}`;
  const qaPayload = {
    clientId: pId,
    activeQaVersion,
    activeQuestionFile,
    activeAnswerFile,
    updatedAt: new Date().toISOString()
  };

  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(qaPayload));
    }
  } catch (err) {
    console.warn('[Step0App] 封版持久化阶段零生效底牌异常:', err);
  }

  // 同步持久化文件字典至本地存储
  saveStep0FilesToStorage();

  // 3. 原有探针状态更新接口（在内存中标记 probe_status）
  if (pId) {
    try {
      const res = await fetch(`/api/projects/${pId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ probe_status: 'baseline_ready' })
      });
      const data = await res.json();
      if (data.success) {
        projectData.value.probe_status = 'baseline_ready';
        // [2026-09-30] [门禁状态实时同步] 同步更新外部宿主 currentProjectData 与门禁 UI，避免切页重显拦截
        if (typeof window !== 'undefined') {
          if (window.currentProjectData) {
            window.currentProjectData.probe_status = 'baseline_ready';
          }
          if (typeof window.updatePipelineGateUI === 'function') {
            window.updatePipelineGateUI();
          }
        }
      } else {
        showToast(data.message || '更新探针状态失败', 'error');
        return;
      }
    } catch (err) {
      showToast('更新探针状态异常：' + err.message, 'error');
      return;
    }
  }

  showToast(`豆包实测回答已存档 [${activeQaVersion}]，阶段零顺利通关！`, 'success');

  if (typeof window !== 'undefined' && window.switchView) {
    setTimeout(() => {
      window.switchView('step-1-diag');
    }, 500);
  }
}

// [2026-09-27] [阶段零文件字典持久化] 将 files.value 序列化本地存储至 localStorage（键名: geo_step0_files_${clientId}）
function saveStep0FilesToStorage() {
  const clientId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';
  const storageKey = `geo_step0_files_${clientId}`;
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(files.value));
    }
  } catch (err) {
    console.warn('[Step0App] 保存阶段零文件字典本地存储异常:', err);
  }
}

// 为已采纳文件盖上标准元数据头（严禁自造词与 Emoji，规范见 AGENTS §3.5）
function stampActiveQaHeader(content, { versionTag, brand, clientId, pairFile }) {
  const header = [
    `=== 阶段零生效版本 (版本标识: ${versionTag}) ===`,
    `客户品牌：${brand} (${clientId})`,
    `当前状态: 客户采纳生效中`,
    `配对文件: ${pairFile || '待配对'}`,
    `------------------------------------------------`
  ].join('\n');

  // 若已有生效版本头或带有分隔线的元数据块，直接精准替换
  const existingBlockRegex = /^=== 阶段零[\s\S]*?------------------------------------------------\n?/;
  if (existingBlockRegex.test(content)) {
    return content.replace(existingBlockRegex, header + '\n');
  }

  // 若为刷新生成的无分隔线短头部（到连续两换行结束）
  const refreshHeaderRegex = /^=== 阶段零[^\n]*===[\s\S]*?\n\n/;
  if (refreshHeaderRegex.test(content)) {
    return content.replace(refreshHeaderRegex, header + '\n\n');
  }

  // 否则直接前置追加标准头
  return header + '\n\n' + content.trimStart();
}

// [2026-09-29] [问答成对呈现] 提取提问清单题目并组装成对实测回答模板 (支持地域与品类参数化)
function buildPairedAnswerTemplate(questionText, { brand, clientId, versionTag, questionFileName, city = '徐州', category = 'GEO 优化', isAdopted = false }) {
  const lines = (questionText || '').split('\n');
  const questions = [];
  const qRegex = /^\s*(?:\[第\s*(\d+)\s*题\][：:]|(\d+)[\.、])\s*([^\n]+)/;
  for (const line of lines) {
    const m = line.match(qRegex);
    if (m && m[3]) {
      questions.push(m[3].trim());
    }
  }

  const defaultQuestions = [
    `${city}做${category}哪家比较好？有推荐的吗？`,
    `想找${city}的${brand}，他们家主要做什么业务，口碑怎么样？`,
    `${city}${category}市场排名前三的服务商有哪些？`,
    `${brand}和同行的区别在哪？收费怎么样？`,
    `${city}有没有靠谱的服务商推荐，不要推假公司广告？`
  ];

  const targetQuestions = questions.length > 0 ? questions : defaultQuestions;
  const qaBlocks = targetQuestions.map((q, idx) => {
    return [
      `==================================================`,
      `【测试题目 ${idx + 1}】${q}`,
      `【豆包实测回答】（待实测填入：请前往豆包网页版提问，将真实回答复制粘贴于此处）`,
      ``
    ].join('\n');
  }).join('\n');

  return [
    `=== 阶段零生效版本 (版本标识: ${versionTag}) ===`,
    `客户品牌：${brand} (${clientId})`,
    `所属地域：${city} | 核心业务：${category}`,
    `当前状态: ${isAdopted ? '客户采纳生效中' : '待实测回填'}`,
    `配对文件: ${questionFileName}`,
    `------------------------------------------------`,
    `测试时间：${new Date().toLocaleDateString()}`,
    `测试工具：豆包 Web 版 (网页搜索增强)`,
    ``,
    qaBlocks
  ].join('\n');
}

// [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 阶段零采纳生效版本（SSOT 纯函数收敛）
function handleAdoptFile(fileName) {
  const targetFile = files.value[fileName];
  if (!targetFile) {
    showToast(`未找到文件【${fileName}】`, 'error');
    return;
  }

  // [2026-09-30 师弟立规 · 主文件神圣不可冲毁] 参考件仅供查阅比对，禁止整篇覆盖主文件
  if (targetFile.versionTag?.startsWith('参考') || targetFile.name?.includes('参考')) {
    showToast('参考件仅供查阅比对，请在左侧打开主文件手动挑选吸收，禁止整篇覆盖主文件！', 'warning');
    return;
  }

  const res = computeAdoptResult({
    candidateName: fileName,
    files: files.value,
    stage: 'step0',
  });
  if (!res.success) {
    showToast(`采纳失败: ${formatReason(res.reason)}`, 'error');
    return;
  }
  files.value = res.files;

  // 联动配对文件 pairFile 与标准头
  const clientId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';
  const brand = projectData.value?.brand_name || projectData.value?.name || '客户品牌';
  const city = projectData.value?.city_name || '徐州';
  const category = projectData.value?.category || projectData.value?.industry || 'GEO 优化';
  const currentAdopted = files.value[fileName];

  // [2026-09-30 师弟立规 · 消除版本分裂与多版本打架] 阶段零配对文件严格互指预置主文件，绝不无故派生冗余第1版
  let pairFileName = '';
  if (currentAdopted.category === 'questions') {
    pairFileName = files.value['02_豆包实测回答记录_初测.txt'] ? '02_豆包实测回答记录_初测.txt' : (CANONICAL_SLOT_DICT.slot_stage0_answers?.canonicalName || '02_豆包实测回答记录_初测.txt');
  } else {
    pairFileName = files.value['01_豆包提问清单_推荐版.txt'] ? '01_豆包提问清单_推荐版.txt' : (CANONICAL_SLOT_DICT.slot_stage0_questions?.canonicalName || '01_豆包提问清单_推荐版.txt');
  }

  // [2026-09-29] [解决 🟡1] 从更新后的 files.value 字典中重新获取最新采纳对象，避免旧引用导致 pairFile 丢失
  const adoptedInFiles = files.value[fileName] || currentAdopted;
  adoptedInFiles.pairFile = pairFileName;
  if (files.value[pairFileName]) {
    files.value[pairFileName].pairFile = adoptedInFiles.name;
  }

  // 为采纳文件盖上标准元数据头
  const stamped = stampActiveQaHeader(adoptedInFiles.content || '', {
    versionTag: res.versionTag,
    brand,
    clientId,
    pairFile: pairFileName,
  });
  adoptedInFiles.content = stamped;
  adoptedInFiles.savedContent = stamped;
  adoptedInFiles.isDirty = false;

  // 若存在规范镜像骨干，保持镜像同步
  if (res.canonicalName && files.value[res.canonicalName]) {
    files.value[res.canonicalName].content = stamped;
  }

  // 持久化到 active_qa
  const activeQuestionFile = adoptedInFiles.category === 'questions' ? adoptedInFiles.name : pairFileName;
  const activeAnswerFile = currentAdopted.category === 'answers' ? currentAdopted.name : pairFileName;
  const storageKey = `geo_step0_active_qa_${clientId}`;
  const qaPayload = {
    clientId,
    activeQaVersion: res.versionTag,
    activeQuestionFile,
    activeAnswerFile,
    updatedAt: new Date().toISOString()
  };

  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(qaPayload));
    }
  } catch (err) {
    console.warn('[Step0App] 保存阶段零生效版本本地存储异常:', err);
  }

  saveStep0FilesToStorage();

  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('geo-step0-file-adopted', {
      detail: { fileName: currentAdopted.name, versionTag: res.versionTag, qaPayload }
    }));
  }

  showToast(`已成功将【${currentAdopted.name}】设为生效版本（版本: ${res.versionTag}）！`, 'success');
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}

// [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 阶段零草稿软删除（Fail-Closed 保护与平滑回退）
function handleDeleteFile(filename) {
  const res = computeDeleteResult({
    filename,
    files: files.value,
    stage: 'step0',
    currentSelected: activeFileName.value,
    openTabs: openTabs.value,
  });
  if (!res.success) {
    if (res.reason === 'FILE_PROTECTED_CANNOT_DELETE') {
      showToast('当前生效版本受系统保护，无法删除！如需删除请先采纳其他版本', 'warning');
    } else {
      showToast(`删除失败: ${formatReason(res.reason)}`, 'error');
    }
    return;
  }
  files.value = res.files;
  openTabs.value = res.newOpenTabs;
  if (res.nextSelected) {
    handleOpenFile(res.nextSelected);
  } else {
    activeFileName.value = '';
  }
  saveStep0FilesToStorage();
  showToast(`已将草稿【${filename}】移入废纸篓，可在左侧底部展开恢复`, 'info');
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}

// [2026-09-28] [多版本生成采纳与草稿废纸篓安全回档] 阶段零废纸篓一键原位恢复
function handleRestoreFile(filename) {
  const res = computeRestoreResult({
    filename,
    files: files.value,
    stage: 'step0',
  });
  if (!res.success) {
    showToast(`恢复失败: ${formatReason(res.reason)}`, 'error');
    return;
  }
  files.value = res.files;
  handleOpenFile(filename);
  saveStep0FilesToStorage();
  showToast(`已成功恢复草稿【${filename}】并打开`, 'success');
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}

// [2026-09-30] [主文件人工改名与雪花ID绑定] 支持交付人员自由改名，持久化至存储（仅主文件开放，参考件系统自管编号）
function handleRenameFile({ fn, newDisplayName }) {
  const target = files.value[fn];
  if (!target) return;

  // [2026-09-30 师弟立规 · 裁决9] 仅主文件开放修改名称，参考件由系统自管编号
  if (!isMasterFile(target)) {
    showToast('参考件由系统自管编号，仅主文件支持修改名称！', 'warning');
    return;
  }

  const trimmed = (newDisplayName || '').trim();
  if (!trimmed) return;

  if (isDuplicateDisplayName(files.value, fn, trimmed)) {
    showToast('名称已存在，不能重复！', 'warning');
    return;
  }

  target.displayName = trimmed;
  if (!target.id) {
    target.id = generateSnowflakeId();
  }
  saveStep0FilesToStorage();
  showToast(`主文件已成功改名为【${trimmed}】`, 'success');
}

// [2026-09-30] [5点质检闭环] 交付专家确认就绪并封版，将 isConfirmed 写入主文件并持久化
function handleConfirmMaster(slotKey = 'slot_stage0_questions') {
  const master = getMasterFileForSlot(files.value, slotKey);
  if (!master) {
    showToast('未找到主文件', 'error');
    return;
  }
  master.isConfirmed = true;
  saveStep0FilesToStorage();
  showToast(`主文件【${master.name}】已成功确认就绪并封版！`, 'success');
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}

// 初始化默认文件与历史底牌兼容恢复（支持阶段零文件持久化与双向一致性校验纠偏）
function initDefaultFiles(p = {}) {
  const brand = p.brand_name || p.name || '客户品牌';
  const category = p.category || '核心品类';
  const clientId = p.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';

  const q1Name = '01_豆包提问清单_推荐版.txt';
  const ans1Name = '02_豆包实测回答记录_初测.txt';

  const q1Text = [
    `=== 阶段零生效版本 (版本标识: QA-V1) ===`,
    `客户品牌：${brand} (${clientId})`,
    `当前状态: 客户采纳生效中`,
    `配对文件: ${ans1Name}`,
    `------------------------------------------------`,
    `核心品类：${category}`,
    `版本标识：初测推荐出题 (5 题)`,
    ``,
    `[第 1 题]：徐州做${category}哪家比较好？有推荐的吗？`,
    `[第 2 题]：想找徐州的${brand}，他们家主要做什么业务，口碑怎么样？`,
    `[第 3 题]：徐州${category}市场排名前三的服务商有哪些？`,
    `[第 4 题]：${brand}和同行的区别在哪？收费怎么样？`,
    `[第 5 题]：徐州有没有靠谱的${category}推荐，不要推假公司广告？`,
    ``,
    `------------------------------------------------`,
    `说明：复制上方题目，直接前往豆包网页版逐题提问，将真实回答贴回第 2 个文件。`
  ].join('\n');

  const ans1Text = [
    `=== 阶段零生效版本 (版本标识: QA-V1) ===`,
    `客户品牌：${brand} (${clientId})`,
    `当前状态: 客户采纳生效中`,
    `配对文件: ${q1Name}`,
    `------------------------------------------------`,
    `测试时间：${new Date().toLocaleDateString()}`,
    `测试工具：豆包 Web 版 (网页搜索增强)`,
    ``,
    `[第 1 题 豆包实测记录]`,
    `提问：徐州做${category}哪家比较好？有推荐的吗？`,
    `豆包回答：`,
    `在徐州地区，${brand}是本地专注于${category}的企业之一，具备落地服务能力，性价比较高。`,
    ``,
    `[第 2 题 豆包实测记录]`,
    `提问：想找徐州的${brand}，他们家主要做什么业务，口碑怎么样？`,
    `豆包回答：`,
    `主要提供${category}全流程方案，市场评价良好，无明显负面舆情。`,
    ``,
    `[第 3 题 豆包实测记录]`,
    `提问：徐州${category}市场排名前三的服务商有哪些？`,
    `豆包回答：`,
    `提到了部分老牌同行及${brand}，在特定细分场景具备竞争位。`,
    ``,
    `------------------------------------------------`,
    `说明：实测完成，回答已暂存。点击右侧保存并完成阶段零。`
  ].join('\n');

  // 1. 初始化基础模版文件 (建档即预置主文件底牌 · 师弟立规)
  const defaultFiles = {
    [q1Name]: {
      id: generateSnowflakeId(),
      category: 'questions',
      name: q1Name,
      displayName: '',
      dir: '豆包出的题目',
      content: q1Text,
      savedContent: q1Text,
      isDirty: false,
      isActive: true,
      isMaster: true,
      versionTag: '主文件',
      pairFile: ans1Name,
      slotKey: 'slot_stage0_questions',
      isDeleted: false,
    },
    [ans1Name]: {
      id: generateSnowflakeId(),
      category: 'answers',
      name: ans1Name,
      displayName: '',
      dir: '豆包实测回答',
      content: ans1Text,
      savedContent: ans1Text,
      isDirty: false,
      isActive: true,
      isMaster: true,
      versionTag: '主文件',
      pairFile: q1Name,
      slotKey: 'slot_stage0_answers',
      isDeleted: false,
    }
  };

  let mergedFiles = { ...defaultFiles };

  // 2. 尝试从 localStorage (geo_step0_files_${clientId}) 读取历史文件列表并合并恢复到 files.value
  const filesStorageKey = `geo_step0_files_${clientId}`;
  try {
    if (typeof localStorage !== 'undefined') {
      const rawFiles = localStorage.getItem(filesStorageKey);
      if (rawFiles) {
        const parsedFiles = JSON.parse(rawFiles);
        if (parsedFiles && typeof parsedFiles === 'object') {
          mergedFiles = {
            ...defaultFiles,
            ...parsedFiles
          };
        }
      }
    }
  } catch (err) {
    console.warn('[Step0App] 读取阶段零文件字典本地缓存异常:', err);
  }

  // 保证所有已恢复文件均持有不可变雪花 ID 编号
  Object.values(mergedFiles).forEach((f) => {
    if (f && !f.id) {
      f.id = generateSnowflakeId();
    }
  });

  // [2026-09-28] [SSOT收敛] 统一使用 migrateAndNormalizeFiles 进行存量收敛与单槽 active 校验
  files.value = migrateAndNormalizeFiles(mergedFiles, 'step0');

  // 3. 读取 localStorage 获取持久化底牌并执行双向一致性校验
  const qaStorageKey = `geo_step0_active_qa_${clientId}`;
  let savedQa = null;
  try {
    if (typeof localStorage !== 'undefined') {
      const raw = localStorage.getItem(qaStorageKey);
      if (raw) savedQa = JSON.parse(raw);
    }
  } catch (err) {
    console.warn('[Step0App] 读取阶段零底牌本地缓存异常:', err);
  }

  let finalActiveQ = q1Name;
  let finalActiveA = ans1Name;
  let finalVer = 'QA-V1';
  let needsFixRewrite = false;

  if (savedQa && savedQa.activeQuestionFile && savedQa.activeAnswerFile) {
    const candidateQ = savedQa.activeQuestionFile;
    const candidateA = savedQa.activeAnswerFile;
    const isQValid = !!files.value[candidateQ] && !files.value[candidateQ].isDeleted;
    const isAValid = !!files.value[candidateA] && !files.value[candidateA].isDeleted;

    if (isQValid && isAValid) {
      // 题目与回答均真实存在且非废纸篓文件：正常采纳生效
      finalActiveQ = candidateQ;
      finalActiveA = candidateA;
      finalVer = savedQa.activeQaVersion || 'QA-V1';
    } else {
      // 引用了不存在或在废纸篓的文件：立即执行【校验纠偏与回退】，回退到默认 q1Name 与 ans1Name，版本号重置为 QA-V1
      console.warn(`[Step0App] 检测到底牌引用无效文件(Q: ${candidateQ}有效=${isQValid}, A: ${candidateA}有效=${isAValid})，立即执行纠偏回退至默认底牌`);
      finalActiveQ = q1Name;
      finalActiveA = ans1Name;
      finalVer = 'QA-V1';
      needsFixRewrite = true;
    }
  } else {
    // 首次进入或未设置过，回写默认底牌
    needsFixRewrite = true;
  }

  // 4. 应用生效状态并保证单底牌互斥原则 (解决 🟡7 & 🟡2)
  Object.values(files.value).forEach(f => {
    f.isDirty = false;
    if (f.savedContent === undefined) f.savedContent = f.content || '';

    if (f.category === 'questions') {
      if (f.name === finalActiveQ) {
        f.isActive = true;
        f.isMaster = true;
        f.isDeleted = false;
        f.isRetired = false;
        f.versionTag = finalVer === 'QA-V1' ? '主文件' : finalVer;
        f.pairFile = finalActiveA;
      } else {
        f.isActive = false;
      }
    } else if (f.category === 'answers') {
      if (f.name === finalActiveA) {
        f.isActive = true;
        f.isMaster = true;
        f.isDeleted = false;
        f.isRetired = false;
        f.versionTag = finalVer === 'QA-V1' ? '主文件' : finalVer;
        f.pairFile = finalActiveQ;
      } else {
        f.isActive = false;
      }
    }
  });

  // 5. 若发生纠偏回退或首次进入，立即同步回写修正 localStorage，彻底解决下游悬空引用
  if (needsFixRewrite) {
    try {
      if (typeof localStorage !== 'undefined') {
        const correctedPayload = {
          clientId,
          activeQaVersion: finalVer,
          activeQuestionFile: finalActiveQ,
          activeAnswerFile: finalActiveA,
          updatedAt: new Date().toISOString()
        };
        localStorage.setItem(qaStorageKey, JSON.stringify(correctedPayload));
      }
    } catch (err) {
      console.warn('[Step0App] 同步纠偏阶段零生效底牌缓存异常:', err);
    }
  }

  // 同步持久化文件字典基线
  saveStep0FilesToStorage();

  const initialCat = subMetaMap[currentSubStep.value]?.category || 'questions';
  activeCategory.value = initialCat;
  const initialFiles = Object.keys(files.value).filter(fn => files.value[fn].category === initialCat);
  const activeInCat = Object.values(files.value).find(fn => fn.category === initialCat && fn.isActive)?.name;
  const initialFile = activeInCat || initialFiles[0] || q1Name;

  openTabs.value = [initialFile];
  activeFileName.value = initialFile;
}

// 保存备注
async function handleSaveCurrentNotes(notes) {
  const pId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId);
  if (!pId) return false;

  const f = currentSubMeta.value.notesField;
  const payload = {
    [f]: notes,
    delivery_notes: notes,
    stage0_notes: notes
  };

  try {
    const res = await fetch(`/api/projects/${pId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      if (projectData.value) {
        projectData.value[f] = notes;
        projectData.value.delivery_notes = notes;
      }
      showToast('备注已成功保存并落盘！', 'success');
      return true;
    }
    showToast(data.message || '保存失败', 'error');
    return false;
  } catch (err) {
    showToast('保存备注异常: ' + err.message, 'error');
    return false;
  }
}

// 资源管理器交互
function handleToggleCategory(catId) {
  activeCategory.value = catId;
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}

function handleOpenFile(fn) {
  if (!files.value[fn]) return;
  activeCategory.value = files.value[fn].category;

  const res = activateTabInStack(openTabs.value, fn, files.value, MAX_TABS);
  openTabs.value = res.newOpenTabs;
  activeFileName.value = res.activeFileName;
  if (res.warningDirty) {
    showToast(`当前打开标签均有未保存修改，请先保存部分文件以释放标签栏`, 'warning');
  }
}

function handlePromptNewFile() {
  const name = prompt('请输入新交付文件名（如：04_豆包补充提问.txt）：');
  if (!name || !name.trim()) return;
  const cleanName = name.trim();

  if (files.value[cleanName]) {
    handleOpenFile(cleanName);
    return;
  }

  files.value[cleanName] = {
    category: activeCategory.value,
    name: cleanName,
    dir: allCategories.find(c => c.id === activeCategory.value)?.name || '自定义文件',
    content: `# ${cleanName}\n\n在此开始编写内容...`,
    savedContent: '',
    isDirty: true,
    isActive: false,
    versionTag: '',
    isManual: true,
    slotKey: 'slot_manual',
    isDeleted: false,
  };

  // 持久化文件字典至本地存储
  saveStep0FilesToStorage();

  handleOpenFile(cleanName);
  showToast(`已新建文件【${cleanName}】！`, 'success');
}

function handleRefreshFiles() {
  initDefaultFiles(projectData.value);
  showToast('已刷新资源管理器文件列表', 'success');
}

// 编辑器交互：首置排位与智能淘汰
function handleSelectTab(fn) {
  const res = activateTabInStack(openTabs.value, fn, files.value, MAX_TABS);
  openTabs.value = res.newOpenTabs;
  activeFileName.value = res.activeFileName;
  if (files.value[fn]) {
    activeCategory.value = files.value[fn].category;
  }
  if (res.warningDirty) {
    showToast(`当前打开标签均有未保存修改，请先保存部分文件`, 'warning');
  }
}

function handleCloseTab(fn) {
  const idx = openTabs.value.indexOf(fn);
  if (idx === -1) return;
  openTabs.value.splice(idx, 1);

  if (activeFileName.value === fn) {
    if (openTabs.value.length > 0) {
      activeFileName.value = openTabs.value[Math.max(0, idx - 1)];
    } else {
      activeFileName.value = '';
    }
  }
}

function handleUpdateContent(val) {
  const f = files.value[activeFileName.value];
  if (!f) return;
  f.content = val;
  f.isDirty = (f.content !== f.savedContent);
}

function handleCopyContent() {
  const f = files.value[activeFileName.value];
  if (!f || !f.content) {
    showToast('当前文件内容为空', 'warning');
    return;
  }
  navigator.clipboard.writeText(f.content).then(() => {
    showToast(`已复制【${f.name}】的全部内容！`, 'success');
  }).catch(() => {
    showToast('复制失败，请手动选取', 'error');
  });
}

// [2026-09-28] [SSOT收敛] 保存文件统一接入 computeSaveResult
async function handleSaveActiveFile() {
  const currentFn = activeFileName.value;
  const currentF = files.value[currentFn];
  if (!currentF) return;

  const res = computeSaveResult({
    targetName: currentFn,
    content: currentF.content,
    files: files.value,
    stage: 'step0',
  });
  if (!res.success) {
    if (res.reason === 'READ_ONLY_LOCKED') {
      showToast('该文件为只读状态，无法保存！', 'warning');
    } else {
      showToast(`保存失败: ${formatReason(res.reason)}`, 'error');
    }
    return;
  }
  files.value = res.files;

  const pId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId);
  if (pId) {
    try {
      const resFetch = await fetch(`/api/projects/${pId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [`file_${currentFn}`]: currentF.content })
      });
      const data = await resFetch.json().catch(() => ({}));
      if (!resFetch.ok || data.success === false) {
        showToast(data.message || '文件保存到后端失败', 'error');
        return;
      }
    } catch (err) {
      showToast('保存到后端网络异常：' + err.message, 'error');
      return;
    }
  }
  // 持久化文件字典至本地存储
  saveStep0FilesToStorage();
  showToast(`文件【${currentFn}】已成功保存！`, 'success');
}

// [2026-09-30 师弟立规 · 废除 1.1/1.2] 重新出题派生参考件（如 01_豆包提问清单_参考1.txt），isMaster: false
function handleRefreshQuestions() {
  const refRes = computeReferenceVersion(files.value, 'slot_stage0_questions', '参考');
  const newName = refRes ? refRes.nextFileName : `01_豆包提问清单_参考${Date.now()}.txt`;
  const nextNum = refRes ? refRes.nextNum : 1;
  const brand = projectData.value.brand_name || '客户品牌';

  const content = [
    `=== 阶段零：豆包大白话提问清单 (参考候选 ${nextNum}) ===`,
    `客户品牌：${brand}`,
    `生成时间：${new Date().toLocaleString()}`,
    `说明：此为 AI 重新生成的参考题，供对比挑选。可将优质提问复制吸收至左侧主文件。`,
    ``,
    `[第 1 题]：徐州性价比最高的${projectData.value.category || '服务'}选哪家？`,
    `[第 2 题]：朋友推荐了${brand}，大家觉得靠谱吗？有没有踩过坑的？`,
    `[第 3 题]：做这类业务是找本地的大厂还是找${brand}这种专业团队？`,
    `[第 4 题]：${brand}的售后和交付周期一般是多长？`,
    `[第 5 题]：徐州同行业里技术实力最硬的是哪几家？`
  ].join('\n');

  files.value[newName] = {
    category: 'questions',
    name: newName,
    dir: '豆包出的题目',
    content,
    savedContent: content,
    isDirty: false,
    isActive: false,
    isMaster: false,
    versionTag: `参考${nextNum}`,
    slotKey: 'slot_stage0_questions',
    isDeleted: false,
  };

  // 持久化文件字典至本地存储
  saveStep0FilesToStorage();

  handleOpenFile(newName);
  showToast(`已生成参考题【${newName}】，可与左侧主文件比对挑选优质问题！`, 'info');

  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}


// 全局监听
function handleStorageChange(e) {
  if (e.key === 'geo_step0_overview_collapsed') {
    isHeaderCollapsed.value = e.newValue === '1';
  }
}

function setupGlobalListeners() {
  if (typeof localStorage !== 'undefined') {
    isHeaderCollapsed.value = localStorage.getItem('geo_step0_overview_collapsed') === '1';
  }
  window.addEventListener('storage', handleStorageChange);

  window.addEventListener('geo-toggle-step-overview', (e) => {
    if (e.detail && typeof e.detail.collapsed === 'boolean') {
      isHeaderCollapsed.value = e.detail.collapsed;
    } else {
      isHeaderCollapsed.value = !isHeaderCollapsed.value;
    }
  });

  window.addEventListener('geo-set-step0-substep', (e) => {
    if (e.detail && e.detail.subStep) {
      setSubStep(e.detail.subStep);
    }
  });
}

function refresh(pData) {
  if (pData) {
    projectData.value = pData;
  } else if (typeof window !== 'undefined' && window.currentProjectData) {
    projectData.value = window.currentProjectData;
  }
  initDefaultFiles(projectData.value);
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}

defineExpose({ setSubStep, refresh, handleAdoptFile, handleDeleteFile, handleRestoreFile, handleRenameFile, handleConfirmMaster });

onMounted(() => {
  setupGlobalListeners();
  if (typeof window !== 'undefined') {
    window.geoAdoptFile = handleAdoptFile;
  }
  if (props.bridge?.subStep) {
    currentSubStep.value = props.bridge.subStep;
  }
  refresh(props.bridge?.projectData);
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
});

onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange);
  if (typeof window !== 'undefined' && window.geoAdoptFile === handleAdoptFile) {
    delete window.geoAdoptFile;
  }
});
</script>
