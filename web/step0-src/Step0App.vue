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
      />

      <!-- 右栏：SOP 交付动线面板 (原右侧列，按步骤展示专属操作与前进按钮) -->
      <StudioSop
        :current-step="currentSubStep"
        :is-ready="isReady"
        @switch-step="goToSubStep"
        @refresh-questions="handleRefreshQuestions"
        @confirm-apply="handleConfirmApply"
        @proceed-to-next="handleProceedToNext"
        @go-stage1="handleGoStage1"
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
      :how-title="'极简三步闭环（约 3 分钟）'"
      :how-steps="[
        '<strong>1. 出题</strong>：在 0.1 页面打磨 5 道核心题；',
        '<strong>2. 真问</strong>：在 0.2 页面前往豆包提问并贴回回答；',
        '<strong>3. 写入</strong>：在 0.3 页面确认存入底牌，正式完成阶段零。'
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

// 三个子步骤专属元数据
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
    title: '0.2 去豆包实测：真机提问贴回答',
    modeTag: '实测阶段',
    target: '带着提问清单前往豆包网页版提问，把豆包真实回答贴回中间文件存档。',
    placeholder: '记录实测备忘（如：第2题豆包识别准确，第4题答得偏泛...）',
    category: 'answers',
    notesField: 'stage0_a_notes',
  },
  3: {
    title: '0.3 确认存入底牌：核验体检结论',
    modeTag: '核验终审',
    target: '核验 4 项健康体检结论（存在感、推荐度、竞争位、舆情面），确认后永久存入项目底牌。',
    placeholder: '记录体检结论备忘（如：已收录品牌，但缺少深度技术参数...）',
    category: 'reports',
    notesField: 'stage0_r_notes',
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
  { id: 'reports', name: '阶段零体检结论' },
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
  showToast('已进入：0.2 去豆包实测！', 'info');
}

function proceedToSub3() {
  handleSaveActiveFile();
  goToSubStep(3);
  showToast('已进入：0.3 确认存入底牌！', 'info');
}

function handleProceedToNext(target) {
  if (target === 2) proceedToSub2();
  else if (target === 3) proceedToSub3();
}

function handleGoStage1() {
  if (typeof window !== 'undefined' && window.switchView) {
    window.switchView('step-1-diag');
  }
}

// 初始化默认文件
function initDefaultFiles(p = {}) {
  const brand = p.brand_name || p.name || '客户品牌';
  const category = p.category || '核心品类';
  const clientId = p.client_id || 'geo';

  const q1Name = '01_豆包提问清单_推荐版.txt';
  const ans1Name = '02_豆包实测回答记录_初测.txt';
  const rep1Name = '03_阶段零体检结论_最新.txt';

  const q1Text = [
    `=== 阶段零：豆包大白话提问清单 (标准版) ===`,
    `客户品牌：${brand} (${clientId})`,
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
    `=== 阶段零：豆包真实回答实录 ===`,
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
    `说明：实测完成，回答已暂存。请前往右侧第 3 步确认存入项目。`
  ].join('\n');

  const rep1Text = [
    `=== 阶段零：豆包大白话体检结论 (基线底牌) ===`,
    `评估客户：${brand} (${clientId})`,
    `所属品类：${category}`,
    `出具时间：${new Date().toLocaleString()}`,
    ``,
    `1. 【存在感 (认不认识)】：大模型已有基础收录`,
    `   - 判定：豆包底座已有品牌基础词条，未发生严重幻觉。`,
    ``,
    `2. 【推荐度 (推不推我)】：本地入选，全国待推`,
    `   - 判定：垂直场景可匹配，通用大词仍由头部品牌占据。`,
    ``,
    `3. 【竞争位 (对标同行)】：卖点突出，参数待补`,
    `   - 判定：对比同行认可度高，但具体工艺参数回答含糊。`,
    ``,
    `4. 【舆情面 (有没有坏话)】：清白健康无差评`,
    `   - 判定：全网清白，无消费纠纷或维权风险。`,
    ``,
    `------------------------------------------------`,
    `终局存盘状态：确认写入后将永久沉淀至 data/projects.json 底牌中。`
  ].join('\n');

  files.value = {
    [q1Name]: {
      category: 'questions',
      name: q1Name,
      dir: '豆包出的题目',
      content: q1Text,
      savedContent: q1Text,
      isDirty: false
    },
    [ans1Name]: {
      category: 'answers',
      name: ans1Name,
      dir: '豆包实测回答',
      content: ans1Text,
      savedContent: ans1Text,
      isDirty: false
    },
    [rep1Name]: {
      category: 'reports',
      name: rep1Name,
      dir: '阶段零体检结论',
      content: rep1Text,
      savedContent: rep1Text,
      isDirty: false
    }
  };

  const initialCat = subMetaMap[currentSubStep.value].category;
  activeCategory.value = initialCat;
  const initialFiles = Object.keys(files.value).filter(fn => files.value[fn].category === initialCat);
  const initialFile = initialFiles[0] || q1Name;

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
    dir: categories.find(c => c.id === activeCategory.value)?.name || '自定义文件',
    content: `# ${cleanName}\n\n在此开始编写内容...`,
    savedContent: '',
    isDirty: true
  };

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
      await fetch(`/api/projects/${pId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [`file_${f.name}`]: f.content })
      });
    } catch (_) {}
  }
  showToast(`文件【${f.name}】已成功保存！`, 'success');
}

// 子步骤专属业务操作
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
    isDirty: false
  };

  handleOpenFile(newName);
  showToast(`已生成新题目文件【${newName}】！`, 'success');
}


async function handleConfirmApply() {
  const pId = projectData.value?.client_id || (typeof window !== 'undefined' && window.currentProjectId);
  if (!pId) return;

  try {
    const res = await fetch(`/api/projects/${pId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ probe_status: 'baseline_ready' })
    });
    const data = await res.json();
    if (data.success) {
      projectData.value.probe_status = 'baseline_ready';
      showToast('恭喜！阶段零摸底已正式确认存入项目底牌！', 'success');
    }
  } catch (err) {
    showToast('确认写入失败: ' + err.message, 'error');
  }
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

defineExpose({ setSubStep, refresh });

onMounted(() => {
  setupGlobalListeners();
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
});
</script>
