<template>
  <!-- [2026-09-27] [阶段一 3 竖列工作区] 商业转化诊断专属工作台 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step1-header-card"
      :stage-title="STAGE_1_META.name"
      :mode-tag="STAGE_1_META.tag"
      :is-ready="currentStep >= 3"
      :target-text="STAGE_1_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_1_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业交付工作台 (左资源树 + 中编辑打磨区 + 右 SOP 动线) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[700px] min-h-[580px]">
      <!-- 左栏：文件资源树 -->
      <StudioFileTree
        :categories="STAGE_1_META.categories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        :allow-new-file="false"
        :allow-refresh="true"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @refresh-files="handleRefreshFiles"
      />

      <!-- 中间：多 Tab 在线打磨区 (Markdown源码 / HTML 视觉大屏实时预览) -->
      <StudioEditor
        :open-tabs="openTabs"
        :active-file-name="activeFileName"
        :files="files"
        :render-mode="currentRenderMode"
        @select-tab="handleSelectTab"
        @close-tab="handleCloseTab"
        @update-content="handleUpdateContent"
        @copy-content="handleCopyContent"
        @save-file="handleSaveActiveFile"
        @fullscreen="fullscreenVisible = true"
      />

      <!-- 右栏：SOP 交付流水线 (步骤 1: 抓底座+门禁 -> 步骤 2: 出初稿润色 -> 步骤 3: 最终多版本报告) -->
      <!-- [2026-09-28] [阶段一底座抓取动线视线引导优化] 绑定 action-completed-map 与 action-loading-map 状态映射 -->
      <StudioSop
        :stage-meta="STAGE_1_META"
        :current-step="currentStep"
        :gate="selectedGate"
        :action-completed-map="{ crawlMetrics: crawledMetrics }"
        :action-loading-map="{ crawlMetrics: isCrawling }"
        @update:gate="handleGateChange"
        @proceed="handleProceed"
        @skip="handleSkip"
        @action="handleAction"
        @goto-step="handleGotoStep"
      />
    </div>

    <!-- 3. 麦肯锡 V-W-W-H 商业诊断与促单避坑手册抽屉 -->
    <MckinseyDrawer
      :visible="mckinseyVisible"
      :title="STAGE_1_META.mckinsey.title"
      :value-desc="STAGE_1_META.mckinsey.valueDesc"
      :value-business="STAGE_1_META.mckinsey.valueBusiness"
      :what-title="STAGE_1_META.mckinsey.whatTitle"
      :what-desc="STAGE_1_META.mckinsey.whatDesc"
      :why-title="STAGE_1_META.mckinsey.whyTitle"
      :why-desc="STAGE_1_META.mckinsey.whyDesc"
      :how-title="STAGE_1_META.mckinsey.howTitle"
      :how-steps="STAGE_1_META.mckinsey.howSteps"
      @close="mckinseyVisible = false"
    />

    <!-- 4. 全屏高保真 HTML 视觉大屏演示弹窗 -->
    <teleport to="body">
      <div
        v-if="fullscreenVisible"
        class="fixed inset-0 bg-slate-950/80 backdrop-blur-xs z-[60] flex items-center justify-center p-6"
        @click.self="fullscreenVisible = false"
      >
        <div class="w-full max-w-6xl h-full max-h-[92vh] bg-slate-900 rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-700">
          <div class="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 text-white">
            <div class="flex items-center gap-2.5 min-w-0">
              <i data-lucide="maximize-2" class="w-4 h-4 text-[#7c5bf5]"></i>
              <span class="text-sm font-bold truncate">商业转化大屏全屏沉浸演示 · {{ activeFileName }}</span>
            </div>
            <button
              type="button"
              class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition text-xs font-semibold cursor-pointer"
              @click="fullscreenVisible = false"
            >
              关闭全屏 (ESC)
            </button>
          </div>
          <div class="flex-1 overflow-hidden bg-slate-950">
            <iframe
              v-if="currentRenderMode === 'html'"
              :srcdoc="activeFile?.content || ''"
              class="w-full h-full border-0 bg-transparent"
              sandbox="allow-scripts allow-same-origin"
              title="老板全屏决策大屏"
            ></iframe>
            <div v-else class="h-full overflow-y-auto p-10 bg-white text-slate-900 geo-md max-w-4xl mx-auto">
              <pre class="font-mono text-xs whitespace-pre-wrap">{{ activeFile?.content }}</pre>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import StageHeader from './components/StageHeader.vue';
import StudioFileTree from './components/studio/StudioFileTree.vue';
import StudioEditor from './components/studio/StudioEditor.vue';
import StudioSop from './components/studio/StudioSop.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import { useStep1 } from './useStep1.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  STAGE_1_META,
  files,
  activeCategory,
  activeFileName,
  activeFile,
  openTabs,
  currentStep,
  selectedGate,
  crawledMetrics, // [2026-09-28] 解构底座抓取状态用于动线绑定
  isCrawling,     // [2026-09-28] 解构底座真抓 loading 状态用于动线绑定
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
} = useStep1(props.bridge?.projectData || {});
</script>
