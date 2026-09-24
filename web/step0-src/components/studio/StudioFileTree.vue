<template>
  <!-- [2026-09-23] [阶段零组件化] 左侧资源管理器子组件 -->
  <aside class="w-full lg:w-60 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 资源管理器顶栏 -->
    <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <i data-lucide="folder-git-2" class="w-4 h-4 text-[#7c5bf5]"></i>
        <span class="text-[13px] font-bold text-slate-800 uppercase tracking-wider">资源管理器</span>
      </div>
      <div class="flex items-center gap-1">
        <button
          type="button"
          title="新建文件"
          class="p-1 hover:bg-slate-200 rounded text-slate-500 hover:text-slate-800 transition cursor-pointer"
          @click="$emit('newFile')"
        >
          <i data-lucide="file-plus" class="w-4 h-4"></i>
        </button>
        <button
          type="button"
          title="刷新目录"
          class="p-1 hover:bg-slate-200 rounded text-slate-500 hover:text-slate-800 transition cursor-pointer"
          @click="$emit('refreshFiles')"
        >
          <i data-lucide="refresh-cw" class="w-4 h-4"></i>
        </button>
      </div>
    </div>

    <!-- 目录与文件树 (手风琴独占展开，字号对齐反重力 IDE 侧栏) -->
    <div class="flex-1 overflow-y-auto p-2 space-y-2 text-sm">
      <div
        v-for="cat in categories"
        :key="cat.id"
        class="rounded-lg border overflow-hidden transition-all duration-200"
        :class="cat.id === activeCategory ? 'border-indigo-200 bg-white shadow-2xs' : 'border-slate-200/80 bg-slate-50/70'"
      >
        <!-- 文件夹头部 -->
        <div
          class="flex items-center justify-between p-2.5 cursor-pointer select-none"
          :class="cat.id === activeCategory ? 'bg-indigo-50/80 text-indigo-950 font-bold border-b border-indigo-100' : 'hover:bg-slate-100/80 text-slate-700 font-medium'"
          @click="$emit('toggleCategory', cat.id)"
        >
          <div class="flex items-center gap-2 truncate">
            <i
              :data-lucide="cat.id === activeCategory ? 'chevron-down' : 'chevron-right'"
              class="w-4 h-4"
              :class="cat.id === activeCategory ? 'text-[#7c5bf5]' : 'text-slate-400'"
            ></i>
            <i
              :data-lucide="cat.id === activeCategory ? 'folder-open' : 'folder'"
              class="w-4 h-4"
              :class="cat.id === activeCategory ? 'text-[#7c5bf5]' : 'text-slate-500'"
            ></i>
            <span class="truncate text-[13px]">{{ cat.name }}</span>
          </div>
          <span
            class="text-[11px] px-2 py-0.5 rounded font-mono font-medium"
            :class="cat.id === activeCategory ? 'bg-white text-[#7c5bf5] border border-[#7c5bf5]/30' : 'bg-slate-200/70 text-slate-500'"
          >
            {{ getFilesInCat(cat.id).length }}
          </span>
        </div>

        <!-- 文件列表 -->
        <div v-show="cat.id === activeCategory" class="p-1.5 space-y-1 bg-white">
          <div
            v-if="getFilesInCat(cat.id).length === 0"
            class="text-[12px] text-slate-400 py-1.5 px-2.5 italic"
          >
            暂无文件
          </div>
          <div
            v-for="fn in getFilesInCat(cat.id)"
            :key="fn"
            class="flex items-center justify-between p-2 rounded-md cursor-pointer transition select-none group"
            :class="fn === activeFileName ? 'bg-[#7c5bf5]/10 text-[#7c5bf5] font-bold border border-[#7c5bf5]/20' : 'hover:bg-slate-100 text-slate-700 border border-transparent'"
            @click="$emit('openFile', fn)"
          >
            <div class="flex items-center gap-2 truncate">
              <i data-lucide="file-text" class="w-4 h-4 shrink-0"></i>
              <span class="truncate text-[13px]">{{ fn }}</span>
            </div>
            <span
              v-if="files[fn]?.isDirty"
              class="w-2 h-2 rounded-full bg-amber-500 shrink-0"
              title="有未保存修改"
            ></span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { nextTick, watch } from 'vue';

const props = defineProps({
  categories: { type: Array, required: true },
  files: { type: Object, required: true },
  activeCategory: { type: String, default: 'questions' },
  activeFileName: { type: String, default: '' },
});

defineEmits(['toggleCategory', 'openFile', 'newFile', 'refreshFiles']);

function getFilesInCat(catId) {
  return Object.keys(props.files).filter(
    (fn) => props.files[fn].category === catId && !props.files[fn].is_deleted
  );
}

watch([() => props.activeCategory, () => props.files], () => {
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
});
</script>
