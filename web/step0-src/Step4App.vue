<template>
  <!-- [2026-09-27] [阶段四 3 竖列工作区] GEO 核心答题卡与向量问答库专属工作台 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step4-header-card"
      :stage-title="STAGE_4_META.name"
      :mode-tag="STAGE_4_META.tag"
      :is-ready="currentStep >= 3"
      :target-text="STAGE_4_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_4_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业工作台 (左意图资产树 + 中四要素精修区 + 右 SOP 与向量仿真) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[780px] min-h-[660px]">
      <!-- 左栏：答题卡三层意图资产树 (280px) -->
      <QaCardTree
        :cards="filteredCards"
        :active-card-id="activeCardId"
        :layers="QA_LAYERS"
        :stats="layerStats"
        :search-keyword="searchKeyword"
        :active-filter-layer="activeFilterLayer"
        @select-card="handleSelectCard"
        @create-card="handleCreateCard"
        @update:search-keyword="searchKeyword = $event"
        @select-filter-layer="activeFilterLayer = $event"
      />

      <!-- 中间：四要素答题卡精修工作台 -->
      <QaCardEditor
        :card="activeCard"
        :layers="QA_LAYERS"
        :audit-result="currentAuditResult"
        @toggle-approve="handleToggleApprove"
        @delete-card="handleDeleteCard"
        @add-variant="handleAddVariant"
        @remove-variant="handleRemoveVariant"
        @add-evidence="handleAddEvidence"
        @remove-evidence="handleRemoveEvidence"
        @add-redline="handleAddRedLine"
        @remove-redline="handleRemoveRedLine"
      />

      <!-- 右栏：SOP 动线与向量仿真测试仪 (320px) -->
      <QaVectorSimulator
        :current-step="currentStep"
        :sop-steps="STAGE_4_META.sopSteps"
        :retrieval-query="retrievalQuery"
        :retrieval-results="retrievalResults"
        :latency="retrievalLatency"
        :is-retrieving="isRetrieving"
        @set-step="handleSetSubStep"
        @update:retrieval-query="retrievalQuery = $event"
        @simulate-retrieval="handleSimulateRetrieval"
        @select-card="handleSelectCard"
        @open-export="exportDrawerOpen = true"
        @reset-preset="handleResetToPreset"
      />
    </div>

    <!-- 3. 辅助抽屉与弹窗组件 -->
    <QaExportModal
      :visible="exportDrawerOpen"
      :content="pureCorpusContent"
      @close="exportDrawerOpen = false"
    />

    <MckinseyDrawer
      :visible="mckinseyVisible"
      title="老赵哥 GEO 答题卡认知与麦肯锡交付手册"
      :handbooks="STAGE_4_META.mckinseyHandbooks"
      @close="mckinseyVisible = false"
    />

    <!-- 轻量操作反馈 Toast -->
    <div
      v-if="toastVisible"
      class="fixed bottom-6 right-6 px-4 py-2.5 bg-slate-900/90 text-white text-xs font-medium rounded-xl shadow-xl z-50 transition flex items-center gap-2 border border-slate-700"
    >
      <i data-lucide="info" class="w-4 h-4 text-purple-400"></i>
      <span>{{ toastMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { onMounted, nextTick, watch } from 'vue';
import StageHeader from './components/StageHeader.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import QaCardTree from './components/qacard/QaCardTree.vue';
import QaCardEditor from './components/qacard/QaCardEditor.vue';
import QaVectorSimulator from './components/qacard/QaVectorSimulator.vue';
import QaExportModal from './components/qacard/QaExportModal.vue';
import { useStep4 } from './useStep4.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  STAGE_4_META,
  QA_LAYERS,
  currentStep,
  isHeaderCollapsed,
  mckinseyVisible,
  notes,
  exportDrawerOpen,
  cards,
  activeCardId,
  activeCard,
  searchKeyword,
  activeFilterLayer,
  layerStats,
  filteredCards,
  retrievalQuery,
  retrievalResults,
  retrievalLatency,
  isRetrieving,
  currentAuditResult,
  toastMessage,
  toastVisible,
  pureCorpusContent,
  handleSelectCard,
  handleCreateCard,
  handleDeleteCard,
  handleAddVariant,
  handleRemoveVariant,
  handleAddEvidence,
  handleRemoveEvidence,
  handleAddRedLine,
  handleRemoveRedLine,
  handleToggleApprove,
  handleSimulateRetrieval,
  handleResetToPreset,
  handleSaveNotes,
  handleSetSubStep,
} = useStep4(props.bridge?.projectData || {});

const refreshIcons = () => {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
};

onMounted(() => {
  refreshIcons();
});

watch(
  [activeCardId, currentStep, retrievalResults],
  () => {
    refreshIcons();
  },
  { deep: true }
);

defineExpose({
  refresh: () => refreshIcons(),
  setSubStep: (step) => handleSetSubStep(step),
});
</script>
