<template>
  <!-- [2026-09-30] [00~07 全流水线顺延] 阶段六 3 竖列工作区：GEO 文章选题撰写与矩阵分发专属工作台 -->
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

    <!-- 2. 主区域：IDE 3 竖列专业工作台 (左选题任务库 + 中S7文章定稿 + 右分发与404监测) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[780px] min-h-[660px]">
      <!-- 左栏：选题任务库 (300px) -->
      <TopicLibrary
        :topics="filteredTopics"
        :active-topic-id="activeTopicId"
        :search-keyword="searchKeyword"
        :active-group-tab="activeGroupTab"
        :stats="topicStats"
        @select-topic="handleSelectTopic"
        @create-topic="handleCreateTopic"
        @toggle-complete="handleToggleComplete"
        @delete-topic="handleDeleteTopic"
        @update:search-keyword="searchKeyword = $event"
        @select-group-tab="activeGroupTab = $event"
      />

      <!-- 中间：S7 字典式文章撰写与在线定稿编辑器 -->
      <ArticleStudio
        :topic="activeTopic"
        :article="currentArticle"
        :audit-result="currentAuditResult"
        @generate-draft="handleGenerateDraft"
        @save-final="handleSaveArticleFinal"
        @update-markdown="handleUpdateArticleMarkdown"
      />

      <!-- 右栏：矩阵分发与 404 存活监测仪 (340px) -->
      <DistributionMonitor
        :channels="DIST_CHANNELS"
        :channel-data-map="channelDataMap"
        :overall-stats="overallDistStats"
        :is-checking-urls="isCheckingUrls"
        :active-topic="activeTopic"
        @copy-richtext="handleCopyRichText"
        @save-channel-url="handleSaveChannelUrl"
        @check-url-alive="handleCheckUrlAlive"
        @check-all-urls="handleCheckAllUrls"
        @regenerate-topic="handleRegenerateDeadTopic"
      />
    </div>

    <!-- 3. 麦肯锡交付手册抽屉 -->
    <MckinseyDrawer
      :visible="mckinseyVisible"
      title="老赵哥 GEO 字典式长文与信源发布作战手册"
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
import TopicLibrary from './components/distribute/TopicLibrary.vue';
import ArticleStudio from './components/distribute/ArticleStudio.vue';
import DistributionMonitor from './components/distribute/DistributionMonitor.vue';
import { useStep6 } from './useStep6.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  STAGE_6_META,
  DIST_CHANNELS,
  currentStep,
  isHeaderCollapsed,
  mckinseyVisible,
  notes,
  topics,
  activeTopicId,
  activeTopic,
  searchKeyword,
  activeGroupTab,
  filteredTopics,
  topicStats,
  currentArticle,
  currentAuditResult,
  channelDataMap,
  overallDistStats,
  isCheckingUrls,
  toastMessage,
  toastVisible,
  handleSelectTopic,
  handleCreateTopic,
  handleDeleteTopic,
  handleToggleComplete,
  handleGenerateDraft,
  handleUpdateArticleMarkdown,
  handleSaveArticleFinal,
  handleCopyRichText,
  handleSaveChannelUrl,
  handleCheckUrlAlive,
  handleCheckAllUrls,
  handleRegenerateDeadTopic,
  handleSaveNotes,
  handleSetSubStep,
} = useStep6(props.bridge?.projectData || {});

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
  [activeTopicId, currentStep, isCheckingUrls, activeGroupTab],
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
