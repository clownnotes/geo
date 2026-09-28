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
        :categories="currentStepCategories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @new-file="handlePromptNewFile"
        @refresh-files="handleRefreshFiles"
      />

      <!-- 中间：多 Tab 编辑打磨区 -->
      <StudioEditor
        :open-tabs="openTabs"
        :active-file-name="activeFileName"
        :files="files"
        @select-tab="handleSelectTab"
        @close-tab="handleCloseTab"
        @update-content="handleUpdateContent"
        @copy-content="handleCopyContent"
        @save-file="handleSaveActiveFile"
        @adopt-file="handleAdoptFile"
      />

      <!-- 右栏：SOP 交付动线面板 (原右侧列，按步骤展示专属操作与前进按钮) -->
      <StudioSop
        :current-step="currentSubStep"
        :is-ready="isReady"
        @switch-step="goToSubStep"
        @refresh-questions="handleRefreshQuestions"
        @proceed-to-next="handleProceedToNext"
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
      (fn) => files.value[fn].category === targetCat && !files.value[fn].is_deleted
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

function proceedToSub2() {
  handleSaveActiveFile();
  goToSubStep(2);
  showToast('已进入：0.2 网页提问拿答案！', 'info');
}

function handleProceedToNext(target) {
  if (target === 2) proceedToSub2();
}

// [2026-09-27] [阶段零生效底牌封版与通关] 封版当前激活的题目与回答，将最新 activeQaVersion、activeQuestionFile、activeAnswerFile 持久化至 localStorage
async function handleFinishStage0() {
  await handleSaveActiveFile();

  const pId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';

  // 1. 查找当前生效的题目与回答文件
  const activeQFile = Object.values(files.value).find(f => f.category === 'questions' && f.isActive)
    || Object.values(files.value).find(f => f.category === 'questions');
  const activeAFile = Object.values(files.value).find(f => f.category === 'answers' && f.isActive)
    || Object.values(files.value).find(f => f.category === 'answers');

  const activeQaVersion = (activeQFile && activeQFile.versionTag)
    || (activeAFile && activeAFile.versionTag)
    || 'QA-V1';

  const activeQuestionFile = activeQFile ? activeQFile.name : '01_豆包提问清单_推荐版.txt';
  const activeAnswerFile = activeAFile ? activeAFile.name : '02_豆包实测回答记录_初测.txt';

  // 确保状态闭环互指
  if (activeQFile) {
    activeQFile.isActive = true;
    activeQFile.versionTag = activeQaVersion;
    activeQFile.pairFile = activeAnswerFile;
  }
  if (activeAFile) {
    activeAFile.isActive = true;
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
      } else {
        showToast(data.message || '更新探针状态失败', 'error');
        return;
      }
    } catch (err) {
      showToast('更新探针状态异常：' + err.message, 'error');
      return;
    }
  }

  showToast(`豆包真实回答已存入底牌 [${activeQaVersion}]，阶段零顺利通关！`, 'success');

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

// 提取当前项目中最大的 QA 版本号（例如从 'QA-V1', 'QA-V2' 中提取最大数字）
function getMaxQaVersionNumber() {
  let maxVer = 1;
  Object.values(files.value).forEach(f => {
    if (f.versionTag) {
      const match = f.versionTag.match(/QA-V(\d+)/i);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num > maxVer) maxVer = num;
      }
    }
  });
  return maxVer;
}

// 为已采纳文件盖上标准元数据头（严禁 Emoji，规范见 design.md 1.3 节）
function stampActiveQaHeader(content, { versionTag, brand, clientId, pairFile }) {
  const header = [
    `=== 阶段零生效底牌 (基线标识: ${versionTag}) ===`,
    `客户品牌：${brand} (${clientId})`,
    `当前状态: 客户采纳生效中`,
    `配对文件: ${pairFile || '待配对'}`,
    `------------------------------------------------`
  ].join('\n');

  // 若已有生效底牌头或带有分隔线的元数据块，直接精准替换
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

// 采纳切换函数：实现单底牌互斥、版本号自动递增、首行元数据头更新及本地持久化
function handleAdoptFile(fileName) {
  const targetFile = files.value[fileName];
  if (!targetFile) {
    showToast(`未找到文件【${fileName}】`, 'error');
    return;
  }

  const clientId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';
  const brand = projectData.value?.brand_name || projectData.value?.name || '客户品牌';

  // 1. 版本号逻辑：若当前文件已有 versionTag 则沿用，若为新文件/草稿则从当前项目最大版本号自动递增
  let versionTag = targetFile.versionTag;
  if (!versionTag) {
    const maxVer = getMaxQaVersionNumber();
    versionTag = `QA-V${maxVer + 1}`;
    targetFile.versionTag = versionTag;
  }

  // 2. 单底牌互斥原则：遍历同 category 文件，将其 isActive 设为 false
  Object.values(files.value).forEach(f => {
    if (f.category === targetFile.category) {
      f.isActive = false;
    }
  });
  targetFile.isActive = true;

  // 3. 确定配对文件 pairFile 与版本号联动
  const pairCategory = targetFile.category === 'questions' ? 'answers' : 'questions';
  const pairFileObj = Object.values(files.value).find(f => f.category === pairCategory && f.isActive)
    || Object.values(files.value).find(f => f.category === pairCategory);
  const pairFileName = pairFileObj ? pairFileObj.name : '';
  targetFile.pairFile = pairFileName;

  if (pairFileObj) {
    pairFileObj.versionTag = versionTag;
    pairFileObj.pairFile = targetFile.name;
  }

  // 4. 更新文件首行元数据头（严禁 Emoji，规范见 design.md 1.3 节）
  const updatedContent = stampActiveQaHeader(targetFile.content || '', {
    versionTag,
    brand,
    clientId,
    pairFile: pairFileName
  });
  targetFile.content = updatedContent;
  targetFile.savedContent = updatedContent;
  targetFile.isDirty = false;

  // 5. 更新本地存储 localStorage
  const activeQuestionFile = targetFile.category === 'questions' ? targetFile.name : pairFileName;
  const activeAnswerFile = targetFile.category === 'answers' ? targetFile.name : pairFileName;

  const storageKey = `geo_step0_active_qa_${clientId}`;
  const qaPayload = {
    clientId,
    activeQaVersion: versionTag,
    activeQuestionFile,
    activeAnswerFile,
    updatedAt: new Date().toISOString()
  };

  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(qaPayload));
    }
  } catch (err) {
    console.warn('[Step0App] 保存阶段零底牌本地存储异常:', err);
  }

  // 同步持久化文件字典至本地存储
  saveStep0FilesToStorage();

  // 6. 派发组件间/全局联动事件并提示 Toast
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('geo-step0-file-adopted', {
      detail: { fileName: targetFile.name, versionTag, qaPayload }
    }));
  }

  showToast(`已成功将【${targetFile.name}】设为客户采纳底牌（版本: ${versionTag}）！`, 'success');

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
    `=== 阶段零生效底牌 (基线标识: QA-V1) ===`,
    `客户品牌：${brand} (${clientId})`,
    `当前状态: 客户采纳生效中`,
    `配对文件: ${ans1Name}`,
    `------------------------------------------------`,
    `核心品类：${category}`,
    `版本标识：初测基线出题 (5 题)`,
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
    `=== 阶段零生效底牌 (基线标识: QA-V1) ===`,
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

  // 1. 初始化基础模版文件
  const defaultFiles = {
    [q1Name]: {
      category: 'questions',
      name: q1Name,
      dir: '豆包出的题目',
      content: q1Text,
      savedContent: q1Text,
      isDirty: false,
      isActive: false,
      versionTag: 'QA-V1',
      pairFile: ans1Name
    },
    [ans1Name]: {
      category: 'answers',
      name: ans1Name,
      dir: '豆包实测回答',
      content: ans1Text,
      savedContent: ans1Text,
      isDirty: false,
      isActive: false,
      versionTag: 'QA-V1',
      pairFile: q1Name
    }
  };

  files.value = { ...defaultFiles };

  // 2. 尝试从 localStorage (geo_step0_files_${clientId}) 读取历史文件列表并合并恢复到 files.value
  const filesStorageKey = `geo_step0_files_${clientId}`;
  try {
    if (typeof localStorage !== 'undefined') {
      const rawFiles = localStorage.getItem(filesStorageKey);
      if (rawFiles) {
        const parsedFiles = JSON.parse(rawFiles);
        if (parsedFiles && typeof parsedFiles === 'object') {
          // 合并恢复：保留基础模版属性，同时恢复用户新增或修改的历史文件（如 01_豆包题目_第2版.txt）
          files.value = {
            ...defaultFiles,
            ...parsedFiles
          };
          // 重置未保存脏标记，保证状态纯净
          Object.values(files.value).forEach(f => {
            if (f) {
              f.isDirty = false;
              if (typeof f.savedContent === 'undefined') {
                f.savedContent = f.content || '';
              }
            }
          });
        }
      }
    }
  } catch (err) {
    console.warn('[Step0App] 读取阶段零文件字典本地缓存异常:', err);
  }

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
    const isQValid = !!files.value[candidateQ];
    const isAValid = !!files.value[candidateA];

    if (isQValid && isAValid) {
      // 题目与回答均真实存在于 files 中：正常采纳生效
      finalActiveQ = candidateQ;
      finalActiveA = candidateA;
      finalVer = savedQa.activeQaVersion || 'QA-V1';
    } else {
      // 引用了不存在的文件：立即执行【校验纠偏与回退】，回退到默认 q1Name 与 ans1Name，版本号重置为 QA-V1
      console.warn(`[Step0App] 检测到底牌引用不存在的文件(Q: ${candidateQ}存在=${isQValid}, A: ${candidateA}存在=${isAValid})，立即执行纠偏回退至默认底牌`);
      finalActiveQ = q1Name;
      finalActiveA = ans1Name;
      finalVer = 'QA-V1';
      needsFixRewrite = true;
    }
  } else {
    // 首次进入或未设置过，回写默认底牌
    needsFixRewrite = true;
  }

  // 4. 应用生效状态并保证单底牌互斥原则
  Object.values(files.value).forEach(f => {
    if (f.category === 'questions') {
      if (f.name === finalActiveQ) {
        f.isActive = true;
        f.versionTag = finalVer;
        f.pairFile = finalActiveA;
      } else {
        f.isActive = false;
      }
    } else if (f.category === 'answers') {
      if (f.name === finalActiveA) {
        f.isActive = true;
        f.versionTag = finalVer;
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

  if (openTabs.value.includes(fn)) {
    activeFileName.value = fn;
    return;
  }
  if (openTabs.value.length >= MAX_TABS) {
    showToast(`最多同时打开 ${MAX_TABS} 个标签！请先关闭不用的标签。`, 'warning');
    return;
  }
  openTabs.value.push(fn);
  activeFileName.value = fn;
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
    pairFile: ''
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

// 编辑器交互
function handleSelectTab(fn) {
  activeFileName.value = fn;
  if (files.value[fn]) {
    activeCategory.value = files.value[fn].category;
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

async function handleSaveActiveFile() {
  const f = files.value[activeFileName.value];
  if (!f) return;
  f.savedContent = f.content;
  f.isDirty = false;

  const pId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId);
  if (pId) {
    try {
      const res = await fetch(`/api/projects/${pId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [`file_${f.name}`]: f.content })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.success === false) {
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
  showToast(`文件【${f.name}】已成功保存！`, 'success');
}

// [2026-09-27] [血统溯源机制] 新生成的第 N 版题目默认为草稿态（isActive: false），由交付专家打磨满意后手动点击顶栏【设为客户采纳】生效
function handleRefreshQuestions() {
  const qCount = Object.keys(files.value).filter(fn => files.value[fn].category === 'questions').length;
  const newName = `01_豆包题目_第${qCount + 1}版.txt`;
  const brand = projectData.value.brand_name || '客户品牌';

  const content = [
    `=== 阶段零：豆包大白话提问清单 (第 ${qCount + 1} 版) ===`,
    `客户品牌：${brand}`,
    `生成时间：${new Date().toLocaleString()}`,
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
    versionTag: '',
    pairFile: ''
  };

  // 持久化文件字典至本地存储
  saveStep0FilesToStorage();

  handleOpenFile(newName);
  showToast(`已生成第 ${qCount + 1} 版草稿题目【${newName}】，打磨满意后可点击顶栏【设为客户采纳】生效！`, 'info');

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

defineExpose({ setSubStep, refresh, handleAdoptFile });

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
