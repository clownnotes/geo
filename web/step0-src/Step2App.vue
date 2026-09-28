<template>
  <!-- [2026-09-27] [阶段二 3 竖列工作区] 普林斯顿 9 因子素材库与唯一真相母盘专属工作台 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step2-header-card"
      :stage-title="STAGE_2_META.name"
      :mode-tag="STAGE_2_META.tag"
      :is-ready="currentStep >= 5"
      :target-text="STAGE_2_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_2_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业交付工作台 (左资源树 + 中母盘与博文打磨区 + 右 SOP 动线) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[760px] min-h-[640px]">
      <!-- 左栏：文件资源树 (260px) -->
      <StudioFileTree
        :categories="STAGE_2_META.categories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        :allow-new-file="false"
        :allow-refresh="true"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @refresh-files="handleInitMaster"
      />

      <!-- 中间：母盘与博文在线打磨与冲突对比工作区 -->
      <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
        <!-- 顶部标签栏与工具条 -->
        <div class="bg-slate-50 border-b border-slate-200 flex items-center justify-between px-2 pt-2 gap-2 overflow-x-auto select-none">
          <!-- Tab 标签列表 -->
          <div class="flex items-center gap-1.5 overflow-x-auto flex-1 scrollbar-none">
            <div
              v-for="fn in openTabs"
              :key="fn"
              class="flex items-center gap-2 px-3.5 py-1.5 rounded-t-lg text-[13px] font-medium cursor-pointer transition border border-b-0 shrink-0"
              :class="fn === activeFileName ? 'bg-white text-[#7c5bf5] border-slate-200 font-bold -mb-[1px]' : 'bg-slate-100/80 hover:bg-slate-200/80 text-slate-600 border-transparent'"
              @click="handleSelectTab(fn)"
            >
              <span class="truncate max-w-[160px]">{{ fn }}</span>
              <span
                v-if="files[fn]?.isDirty"
                class="w-2 h-2 rounded-full bg-amber-500 shrink-0"
                title="有未保存修改"
              ></span>
              <span
                class="text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded p-0.5 text-xs"
                title="关闭标签"
                @click.stop="handleCloseTab(fn)"
              >
                ×
              </span>
            </div>
          </div>

          <!-- 顶部快捷操作 -->
          <div class="flex items-center gap-1.5 pb-1.5 shrink-0 pr-1">
            <button
              type="button"
              class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              title="一键复制当前文件内容"
              @click="handleCopyContent"
            >
              <i data-lucide="copy" class="w-3.5 h-3.5 text-slate-500"></i>
              <span>复制内容</span>
            </button>
            <button
              type="button"
              class="px-2.5 py-1 bg-[#7c5bf5] hover:bg-[#6a48e6] text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition shadow-xs cursor-pointer"
              title="保存当前文件"
              @click="handleSaveActiveFile"
            >
              <i data-lucide="save" class="w-3.5 h-3.5"></i>
              <span>保存修改</span>
            </button>
          </div>
        </div>

        <!-- 中栏主体内容区 -->
        <div class="flex-1 min-h-0 flex flex-col relative bg-slate-50/50">
          <!-- 1. 专属事实冲突直观对比卡（当触发比对或处于冲突文件时高亮展开） -->
          <div
            v-if="showConflictCard || activeFileName.includes('冲突')"
            class="m-3 p-4 bg-amber-50/90 border border-amber-200 rounded-xl space-y-3 shadow-xs shrink-0"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="p-1 rounded bg-amber-200/80 text-amber-900">
                  <i data-lucide="alert-triangle" class="w-4 h-4"></i>
                </span>
                <span class="font-bold text-slate-900 text-sm">事实冲突直观裁决卡</span>
                <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="conflictData.status === 'accepted' ? 'bg-emerald-100 text-emerald-800' : conflictData.status === 'aligned' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'">
                  {{ conflictData.status === 'accepted' ? '已合流升级 v1.1' : conflictData.status === 'aligned' ? '素材已对齐母盘' : '待裁决' }}
                </span>
              </div>
              <button
                type="button"
                class="text-xs text-slate-400 hover:text-slate-600"
                @click="showConflictCard = false"
              >
                收起对比卡
              </button>
            </div>

            <!-- 并排对比网格 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <!-- 左侧：母盘现有法定事实 -->
              <div class="p-3 bg-white rounded-lg border border-slate-200 space-y-1.5">
                <div class="flex items-center justify-between font-bold text-slate-700">
                  <span>母盘现有法定事实 (SSOT)</span>
                  <span class="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono">{{ masterVersion }}</span>
                </div>
                <div class="p-2 bg-slate-50 rounded border border-slate-100 font-medium text-slate-800">
                  {{ conflictData.masterValue }}
                </div>
                <div class="text-[11px] text-slate-500">
                  地位：当前全网唯一最高基准，所有渠道发文的基石。
                </div>
              </div>

              <!-- 右侧：新素材提取说法 -->
              <div class="p-3 bg-white rounded-lg border border-amber-300 space-y-1.5">
                <div class="flex items-center justify-between font-bold text-amber-900">
                  <span>新素材提取提议值</span>
                  <span class="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded">老官网语料</span>
                </div>
                <div class="p-2 bg-amber-50/70 rounded border border-amber-200 font-medium text-amber-950">
                  {{ conflictData.materialValue }}
                </div>
                <div class="text-[11px] text-amber-700">
                  建议：{{ conflictData.suggestion }}
                </div>
              </div>
            </div>

            <!-- 裁决操作按钮条 -->
            <div class="flex items-center justify-end gap-2 pt-1 border-t border-amber-200/60">
              <button
                type="button"
                class="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                @click="handleResolveConflict('keep_master')"
              >
                <i data-lucide="check" class="w-3.5 h-3.5 text-blue-600"></i>
                <span>保持母盘不变，按母盘修正素材</span>
              </button>
              <button
                type="button"
                class="px-3 py-1.5 bg-[#7c5bf5] hover:bg-[#6a48e6] text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
                @click="handleResolveConflict('accept')"
              >
                <i data-lucide="git-merge" class="w-3.5 h-3.5"></i>
                <span>采纳新素材，合流升级母盘 (v1.1)</span>
              </button>
            </div>
          </div>

          <!-- 2. 在线打磨编辑器主体 -->
          <div class="flex-1 min-h-0 flex flex-col p-3">
            <div class="flex-1 bg-white rounded-lg border border-slate-200 shadow-2xs flex flex-col overflow-hidden">
              <!-- 编辑区头部说明 -->
              <div class="bg-slate-50/80 px-3 py-1.5 border-b border-slate-200 flex items-center justify-between text-xs text-slate-500">
                <span class="font-mono text-slate-700 truncate max-w-[300px]">
                  {{ activeFileName || '未打开文件' }}
                </span>
                <span class="text-[11px] text-slate-400">
                  {{ activeFile?.content ? activeFile.content.split('\n').length : 0 }} 行 · Markdown 高保真纯文本
                </span>
              </div>
              <textarea
                :value="activeFile?.content || ''"
                class="flex-1 p-4 font-mono text-xs text-slate-800 bg-white resize-none outline-none leading-relaxed overflow-y-auto"
                placeholder="在此查看或编辑内容..."
                @input="handleUpdateContent($event.target.value)"
              ></textarea>
            </div>
          </div>
        </div>
      </section>

      <!-- 右栏：SOP 交付动线流水线 (320px) -->
      <StudioSop
        :sop-steps="STAGE_2_META.sopSteps"
        :current-step="currentStep"
        @goto-step="handleGotoStep"
        @proceed="handleProceed"
        @skip="handleSkip"
        @action="handleAction"
      />
    </div>

    <!-- 3. 抽屉与模态层 -->
    <!-- 麦肯锡认知手册抽屉 -->
    <MckinseyDrawer
      v-if="STAGE_2_META.mckinsey"
      :visible="mckinseyVisible"
      :mckinsey-data="STAGE_2_META.mckinsey"
      @close="mckinseyVisible = false"
    />

    <!-- 按需派生博文弹窗抽屉 -->
    <div
      v-if="blogDrawerOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full p-5 space-y-4 border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="p-1.5 bg-[#7c5bf5]/10 text-[#7c5bf5] rounded-lg">
              <i data-lucide="file-text" class="w-4 h-4"></i>
            </span>
            <span class="font-bold text-slate-900 text-sm">按需派生高权威行业博文</span>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-600 text-sm font-bold p-1 cursor-pointer"
            @click="blogDrawerOpen = false"
          >
            ×
          </button>
        </div>

        <p class="text-xs text-slate-600 leading-relaxed">
          基于当前最新母盘 ({{ masterVersion }}) 的知识三元组与参数对比表，选择高频长尾主题，精准派生权威问答博文，直接扩充 GEO 检索抓取语料：
        </p>

        <!-- 推荐高频主题单选列表 -->
        <div class="space-y-2">
          <label
            v-for="(t, idx) in suggestedTopics"
            :key="idx"
            class="flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition text-xs"
            :class="selectedTopic === t ? 'border-[#7c5bf5] bg-[#7c5bf5]/5 text-slate-900 font-semibold' : 'border-slate-200 hover:bg-slate-50 text-slate-700'"
          >
            <input
              v-model="selectedTopic"
              type="radio"
              :value="t"
              class="mt-0.5 text-[#7c5bf5] focus:ring-[#7c5bf5]"
            />
            <span class="flex-1">{{ t }}</span>
          </label>
        </div>

        <!-- 底部操作按钮 -->
        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-medium cursor-pointer"
            @click="blogDrawerOpen = false"
          >
            取消
          </button>
          <button
            type="button"
            class="px-4 py-1.5 bg-[#7c5bf5] hover:bg-[#6a48e6] text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            @click="confirmDeriveBlog"
          >
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            <span>一键基于母盘精准派生</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue';
import StageHeader from './components/StageHeader.vue';
import StudioFileTree from './components/studio/StudioFileTree.vue';
import StudioSop from './components/studio/StudioSop.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import { useStep2 } from './useStep2.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  ctx,
  STAGE_2_META,
  files,
  masterVersion,
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
  handleResolveConflict,
  handleDeriveBlog,
  handleCopyContent,
} = useStep2(props.bridge?.projectData || {});

const suggestedTopics = ref([
  `${ctx.city}实体商家做大模型SEO必须要知道的5大硬核三元组`,
  `传统网络建站与普林斯顿GEO大模型优化的本质区别在哪里？`,
  `${ctx.city}本地企业如何避免网站被大模型判定为不可信实体？`,
]);

const selectedTopic = ref(suggestedTopics.value[0]);

function confirmDeriveBlog() {
  handleDeriveBlog(selectedTopic.value);
  blogDrawerOpen.value = false;
}

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

watch([activeFileName, showConflictCard, blogDrawerOpen, currentStep], () => {
  refreshIcons();
});

onMounted(() => {
  refreshIcons();
});
</script>
