<template>
  <!-- 左栏：选题任务库 (300px) -->
  <aside class="w-full lg:w-72 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 1. 顶部统计看板与新建按钮 -->
    <div class="p-3 border-b border-slate-100 bg-slate-50/70 space-y-2.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <i data-lucide="list-todo" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="font-bold text-slate-800 text-[13px]">选题任务库</span>
        </div>
        <button
          type="button"
          class="px-2 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[11px] font-semibold rounded-lg shadow-xs transition flex items-center gap-1 cursor-pointer"
          @click="showAddModal = true"
        >
          <i data-lucide="plus" class="w-3.5 h-3.5"></i>
          <span>新选题</span>
        </button>
      </div>

      <!-- 快速指标条 -->
      <div class="grid grid-cols-4 gap-1 text-center text-[10px]">
        <div class="bg-indigo-50/80 border border-indigo-100/80 rounded py-1 px-0.5">
          <span class="text-indigo-600 block">首次打样</span>
          <span class="font-bold text-indigo-900">{{ stats.firstSampleCount }}</span>
        </div>
        <div class="bg-slate-100/80 border border-slate-200/80 rounded py-1 px-0.5">
          <span class="text-slate-600 block">日常运营</span>
          <span class="font-bold text-slate-800">{{ stats.dailyOpsCount }}</span>
        </div>
        <div class="bg-emerald-50/80 border border-emerald-100/80 rounded py-1 px-0.5">
          <span class="text-emerald-600 block">已写打勾</span>
          <span class="font-bold text-emerald-800">{{ stats.completedCount }}</span>
        </div>
        <div
          class="border rounded py-1 px-0.5 transition"
          :class="stats.deadCount > 0 ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-slate-50 border-slate-200 text-slate-500'"
        >
          <span class="block">404失效</span>
          <span class="font-bold">{{ stats.deadCount }}</span>
        </div>
      </div>

      <!-- 搜索过滤输入框 -->
      <div class="relative">
        <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2"></i>
        <input
          :value="searchKeyword"
          type="text"
          placeholder="搜索题目、关键词或目的..."
          class="w-full pl-8 pr-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-[#7c5bf5] focus:ring-1 focus:ring-[#7c5bf5]"
          @input="$emit('update:searchKeyword', $event.target.value)"
        />
      </div>

      <!-- 首次打样 vs 日常运营 Tab 切换 -->
      <div class="flex items-center gap-1 bg-slate-200/60 p-0.5 rounded-lg text-[11px]">
        <button
          v-for="tab in groupTabs"
          :key="tab.key"
          type="button"
          class="flex-1 py-1 rounded font-medium transition cursor-pointer"
          :class="activeGroupTab === tab.key ? 'bg-white text-slate-900 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
          @click="$emit('select-group-tab', tab.key)"
        >
          {{ tab.name }}
        </button>
      </div>
    </div>

    <!-- 2. 选题卡片列表 -->
    <div class="flex-1 min-h-0 overflow-y-auto p-2 space-y-1.5 divide-y-0">
      <div
        v-for="topic in topics"
        :key="topic.id"
        class="p-2.5 rounded-lg border transition cursor-pointer text-left relative group select-none"
        :class="activeTopicId === topic.id
          ? 'bg-purple-50/70 border-[#7c5bf5] ring-1 ring-[#7c5bf5]/30'
          : 'bg-white hover:bg-slate-50 border-slate-200/80'"
        @click="$emit('select-topic', topic.id)"
      >
        <div class="flex items-center justify-between gap-1 mb-1">
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded font-bold bg-slate-100 text-slate-700 border border-slate-200">
              {{ topic.id }}
            </span>
            <span
              class="text-[9px] px-1.5 py-0.2 rounded font-medium border"
              :class="topic.group === 'first_sample' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-50 text-slate-600 border-slate-200'"
            >
              {{ topic.group === 'first_sample' ? '首次打样' : '日常运营' }}
            </span>
          </div>

          <!-- 状态标签 -->
          <div class="flex items-center gap-1">
            <span
              v-if="topic.status === 'invalid_404'"
              class="text-[10px] px-1.5 py-0.2 rounded font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-0.5"
            >
              <i data-lucide="alert-triangle" class="w-3 h-3 text-rose-600"></i>
              404失效
            </span>
            <span
              v-else-if="topic.status === 'published'"
              class="text-[10px] px-1.5 py-0.2 rounded font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
            >
              已上线
            </span>
            <span
              v-else-if="topic.status === 'finalized'"
              class="text-[10px] px-1.5 py-0.2 rounded font-medium bg-blue-50 text-blue-700 border border-blue-200"
            >
              已定稿
            </span>
            <span
              v-else
              class="text-[10px] px-1.5 py-0.2 rounded font-medium bg-amber-50 text-amber-700 border border-amber-200"
            >
              草稿待写
            </span>

            <!-- 打勾标记 -->
            <button
              type="button"
              class="p-0.5 text-slate-400 hover:text-emerald-600 transition"
              :title="topic.isCompleted ? '取消打勾' : '标记已写完发布'"
              @click.stop="$emit('toggle-complete', topic.id)"
            >
              <i
                :data-lucide="topic.isCompleted ? 'check-circle-2' : 'circle'"
                class="w-4 h-4"
                :class="topic.isCompleted ? 'text-emerald-600' : 'text-slate-300 group-hover:text-slate-400'"
              ></i>
            </button>
          </div>
        </div>

        <h4 class="text-xs font-semibold text-slate-800 line-clamp-2 leading-relaxed">
          {{ topic.title }}
        </h4>

        <div class="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
          <span class="truncate max-w-[170px]">
            关联答题卡: {{ topic.relatedQaId || 'P01' }}
          </span>
          <span class="font-mono text-slate-400 shrink-0">
            {{ topic.targetPlatforms?.join('/') }}
          </span>
        </div>
      </div>

      <div v-if="topics.length === 0" class="text-center py-10 text-slate-400 text-xs">
        <i data-lucide="file-question" class="w-8 h-8 mx-auto text-slate-300 mb-2"></i>
        <span>没有找到符合条件的选题</span>
      </div>
    </div>

    <!-- 3. 新增选题极简弹窗/抽屉 -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-2xs flex items-center justify-center p-4"
      @click.self="showAddModal = false"
    >
      <div class="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md p-4 space-y-3">
        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
          <div class="flex items-center gap-1.5">
            <i data-lucide="plus-circle" class="w-4 h-4 text-[#7c5bf5]"></i>
            <span class="font-bold text-slate-900 text-xs">添加新选题到任务库</span>
          </div>
          <button type="button" class="text-slate-400 hover:text-slate-600 cursor-pointer" @click="showAddModal = false">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <div class="space-y-2">
          <label class="block text-[11px] font-semibold text-slate-700">选题标题（用户搜索意图主问句）</label>
          <textarea
            v-model="newTopicTitle"
            rows="3"
            placeholder="例如：徐州本地哪家GEO服务更落地靠谱？本地实体企业真实选型指南"
            class="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-[#7c5bf5] focus:outline-none"
          ></textarea>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            class="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg transition"
            @click="showAddModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="px-4 py-1.5 bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-semibold rounded-lg shadow-xs transition"
            @click="handleSubmitNewTopic"
          >
            确认加入选题池
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  topics: { type: Array, default: () => [] },
  activeTopicId: { type: String, default: '' },
  searchKeyword: { type: String, default: '' },
  activeGroupTab: { type: String, default: 'all' },
  stats: {
    type: Object,
    default: () => ({
      total: 0,
      firstSampleCount: 0,
      dailyOpsCount: 0,
      completedCount: 0,
      deadCount: 0,
    }),
  },
});

const emit = defineEmits([
  'select-topic',
  'create-topic',
  'toggle-complete',
  'delete-topic',
  'update:searchKeyword',
  'select-group-tab',
]);

const groupTabs = [
  { key: 'all', name: '全部选题' },
  { key: 'first_sample', name: '首次打样' },
  { key: 'daily_ops', name: '日常运营池' },
];

const showAddModal = ref(false);
const newTopicTitle = ref('');

const handleSubmitNewTopic = () => {
  if (newTopicTitle.value.trim()) {
    emit('create-topic', newTopicTitle.value.trim());
    newTopicTitle.value = '';
    showAddModal.value = false;
  }
};
</script>
