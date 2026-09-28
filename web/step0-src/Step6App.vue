<template>
  <!-- [2026-09-27] [首次交付验收与日常运营复测解耦] 阶段六 3 竖列工作区总装组件 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step6-header-card"
      :stage-title="STAGE_6_META.name"
      :mode-tag="STAGE_6_META.tag"
      :is-ready="currentStep >= 3"
      :target-text="STAGE_6_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_6_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业工作台 (左S11资产盘点 + 中核心3问改口抽测 + 右结项验收凭单) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[780px] min-h-[660px]">
      <!-- 左栏：七项验收资产盘点 (320px) -->
      <AssetChecklist :checklist="checklist" />

      <!-- 中间：首轮核心 3 问改口真机抽测工作台 -->
      <FirstProbeVerifier
        :probe-questions="probeQuestions"
        :active-question-id="activeQuestionId"
        :active-question="activeQuestion"
        @select-question="handleSelectQuestion"
        @copy-question="handleCopyQuestion"
        @update-answer="handleUpdateActualAnswer"
        @toggle-corrected="handleToggleCorrected"
      />

      <!-- 右栏：首期工程移交与结项验收单凭据 (350px) -->
      <SignoffDocket
        :project-context="projectContext"
        :signoff-form="signoffForm"
        @save-signoff="handleSaveSignoff"
        @reset-signoff="handleResetSignoff"
        @print-signoff="handlePrintSignoff"
        @export-markdown="handleExportChecklistMarkdown"
      />
    </div>

    <!-- 3. 麦肯锡交付手册抽屉 -->
    <MckinseyDrawer
      :visible="mckinseyVisible"
      title="老赵哥 GEO 首次交付与验收归档作战手册"
      :handbooks="STAGE_6_META.mckinseyHandbooks"
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
import AssetChecklist from './components/acceptance/AssetChecklist.vue';
import FirstProbeVerifier from './components/acceptance/FirstProbeVerifier.vue';
import SignoffDocket from './components/acceptance/SignoffDocket.vue';
import { useStep6 } from './useStep6.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  STAGE_6_META,
  currentStep,
  isHeaderCollapsed,
  mckinseyVisible,
  toastMessage,
  toastVisible,
  projectContext,
  checklist,
  probeQuestions,
  activeQuestionId,
  activeQuestion,
  signoffForm,
  notes,
  handleSelectQuestion,
  handleCopyQuestion,
  handleUpdateActualAnswer,
  handleToggleCorrected,
  handleSaveSignoff,
  handleResetSignoff,
  handlePrintSignoff,
  handleExportChecklistMarkdown,
  handleSaveNotes,
} = useStep6(props.bridge);

function refreshLucideIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  });
}

onMounted(() => {
  refreshLucideIcons();
});

watch([activeQuestionId, toastVisible], () => {
  refreshLucideIcons();
});
</script>
