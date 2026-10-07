<template>
  <!-- 左栏：答题卡三层意图资产树 (280px) -->
  <aside class="w-full lg:w-72 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 1. 顶部统计看板与新建按钮 -->
    <div class="p-3 border-b border-slate-100 bg-slate-50/70 space-y-2.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <i data-lucide="layers" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="font-bold text-slate-800 text-[13px]">答题卡意图资产树</span>
        </div>
        <span class="text-[11px] text-slate-500 font-mono">共 {{ stats.total }} 张卡</span>
      </div>

      <!-- 三层意图快速指标条 -->
      <div class="grid grid-cols-3 gap-1.5 text-center text-[11px]">
        <div class="bg-blue-50/80 border border-blue-100/80 rounded py-1 px-1.5">
          <span class="text-blue-600 block text-[10px]">入池探索</span>
          <span class="font-bold text-blue-800">{{ stats.pool }} 题</span>
        </div>
        <div class="bg-purple-50/80 border border-purple-100/80 rounded py-1 px-1.5">
          <span class="text-purple-600 block text-[10px]">品牌验证</span>
          <span class="font-bold text-purple-800">{{ stats.verify }} 题</span>
        </div>
        <div class="bg-emerald-50/80 border border-emerald-100/80 rounded py-1 px-1.5">
          <span class="text-emerald-600 block text-[10px]">行动转化</span>
          <span class="font-bold text-emerald-800">{{ stats.convert }} 题</span>
        </div>
      </div>

      <!-- 搜索过滤输入框 -->
      <div class="relative">
        <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2"></i>
        <input
          :value="searchKeyword"
          type="text"
          placeholder="搜索问题、问法或编号..."
          class="w-full pl-8 pr-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-[#7c5bf5] focus:ring-1 focus:ring-[#7c5bf5]"
          @input="$emit('update:searchKeyword', $event.target.value)"
        />
      </div>

      <!-- 意图层级筛选 Tab -->
      <div class="flex items-center gap-1 bg-slate-200/60 p-0.5 rounded-lg text-[11px]">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          type="button"
          class="flex-1 py-1 rounded font-medium transition cursor-pointer"
          :class="activeFilterLayer === tab.key ? 'bg-white text-slate-900 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
          @click="$emit('select-filter-layer', tab.key)"
        >
          {{ tab.name }}
        </button>
      </div>
    </div>

    <!-- 2. 答题卡卡片列表 -->
    <div class="flex-1 min-h-0 overflow-y-auto p-2 space-y-1.5 divide-y-0">
      <div
        v-for="card in cards"
        :key="card.id"
        class="p-2.5 rounded-lg border transition cursor-pointer text-left relative group select-none"
        :class="activeCardId === card.id
          ? 'bg-purple-50/70 border-[#7c5bf5] ring-1 ring-[#7c5bf5]/30'
          : 'bg-white hover:bg-slate-50 border-slate-200/80'"
        @click="$emit('select-card', card.id)"
      >
        <div class="flex items-center justify-between gap-1 mb-1">
          <div class="flex items-center gap-1.5">
            <span
              class="text-[10px] font-mono px-1.5 py-0.5 rounded font-bold border"
              :class="layers[card.layer]?.badgeClass || 'bg-slate-100 text-slate-700 border-slate-200'"
            >
              {{ card.id }}
            </span>
            <span class="text-[10px] text-slate-500 font-medium">
              {{ layers[card.layer]?.name }}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span
              class="text-[10px] px-1 py-0.2 rounded font-mono"
              :class="card.completenessScore >= 80 ? 'text-emerald-700 bg-emerald-50' : 'text-amber-700 bg-amber-50'"
            >
              {{ card.completenessScore }}分
            </span>
            <i
              v-if="card.isApproved"
              data-lucide="check-circle-2"
              class="w-3.5 h-3.5 text-emerald-600"
              title="已通过复核"
            ></i>
          </div>
        </div>

        <h4 class="text-xs font-semibold text-slate-800 line-clamp-2 leading-relaxed">
          {{ card.title }}
        </h4>

        <div class="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
          <span>覆盖 {{ card.variants?.length || 0 }} 种搜索问法</span>
          <span>{{ card.supportingEvidence?.length || 0 }} 项证据</span>
        </div>
      </div>

      <div v-if="cards.length === 0" class="py-8 text-center text-xs text-slate-400">
        没有匹配的答题卡
      </div>
    </div>

    <!-- 3. 底部快捷操作 -->
    <div class="p-2.5 border-t border-slate-100 bg-slate-50/50 flex items-center gap-1.5">
      <button
        type="button"
        class="flex-1 py-1.5 bg-[#7c5bf5] hover:bg-[#6a48e6] text-white rounded-lg text-xs font-medium flex items-center justify-center gap-1 transition shadow-2xs cursor-pointer"
        @click="showCreateMenu = !showCreateMenu"
      >
        <i data-lucide="plus" class="w-3.5 h-3.5"></i>
        <span>新建答题卡</span>
      </button>

      <!-- 快速新建层级下拉 -->
      <div v-if="showCreateMenu" class="absolute bottom-12 left-3 right-3 bg-white border border-slate-200 shadow-lg rounded-xl p-1.5 space-y-1 z-20">
        <button
          v-for="(layer, key) in layers"
          :key="key"
          type="button"
          class="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-slate-100 flex items-center justify-between transition cursor-pointer"
          @click="$emit('create-card', key); showCreateMenu = false"
        >
          <span class="font-medium text-slate-800">{{ layer.name }}</span>
          <span class="text-[10px] text-slate-400">{{ layer.prefix }}系列</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  cards: { type: Array, default: () => [] },
  activeCardId: { type: String, default: '' },
  layers: { type: Object, default: () => ({}) },
  stats: { type: Object, default: () => ({}) },
  searchKeyword: { type: String, default: '' },
  activeFilterLayer: { type: String, default: 'all' },
});

defineEmits([
  'select-card',
  'create-card',
  'update:searchKeyword',
  'select-filter-layer',
]);

const showCreateMenu = ref(false);

const filterTabs = [
  { key: 'all', name: '全部' },
  { key: 'pool', name: '入池' },
  { key: 'verify', name: '验证' },
  { key: 'convert', name: '转化' },
];
</script>
