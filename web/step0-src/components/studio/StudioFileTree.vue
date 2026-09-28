<template>
  <!-- [2026-09-28] [出题草稿采纳流] 左侧资源管理器：四阶段统一拓宽至 lg:w-72 (288px)，杜绝文件名截断 -->
  <aside class="w-full lg:w-72 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 资源管理器顶栏 -->
    <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <i data-lucide="folder-git-2" class="w-4 h-4 text-[#7c5bf5]"></i>
        <span class="text-[13px] font-bold text-slate-800 uppercase tracking-wider">资源管理器</span>
      </div>
      <!-- [2026-09-27] [按阶段显隐控制] 支持 allowNewFile 与 allowRefresh prop，消除死按钮 -->
      <div class="flex items-center gap-1">
        <button
          v-if="allowNewFile"
          type="button"
          title="新建文件"
          class="p-1 hover:bg-slate-200 rounded text-slate-500 hover:text-slate-800 transition cursor-pointer"
          @click="$emit('newFile')"
        >
          <i data-lucide="file-plus" class="w-4 h-4"></i>
        </button>
        <button
          v-if="allowRefresh"
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
            <div class="flex items-center gap-2 truncate mr-1.5">
              <i data-lucide="file-text" class="w-4 h-4 shrink-0"></i>
              <span class="truncate text-[13px]">{{ fn }}</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <!-- [2026-09-28] [出题草稿采纳流] 仅在 showStatusBadge 为 true 时渲染二元状态徽章，防污染阶段一/二/三 -->
              <template v-if="showStatusBadge">
                <!-- 采纳生效底牌徽章 (系统主色紫) -->
                <span
                  v-if="files[fn]?.isActive"
                  class="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-[#7c5bf5]/15 text-[#7c5bf5] border border-[#7c5bf5]/30 flex items-center gap-1 shrink-0 shadow-2xs"
                >
                  <i data-lucide="check" class="w-3 h-3 text-[#7c5bf5]"></i>
                  <span>已采纳</span>
                  <span class="opacity-80">[{{ files[fn]?.versionTag || 'QA-V1' }}]</span>
                </span>
                <!-- 草稿未生效徽章 (中性灰) -->
                <span
                  v-else
                  class="text-[10px] px-1.5 py-0.5 rounded font-mono text-slate-400 bg-slate-100 border border-slate-200 shrink-0"
                >
                  草稿
                </span>

                <!-- [2026-09-28] [多版本生成采纳与草稿废纸篓] 草稿文件 hover 允许删除 (已采纳受保护不可删) -->
                <button
                  v-if="!files[fn]?.isActive"
                  type="button"
                  title="删除此草稿 (移入废纸篓)"
                  class="opacity-0 group-hover:opacity-100 p-1 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded transition cursor-pointer"
                  @click.stop="$emit('deleteFile', fn)"
                >
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
              </template>
              <span
                v-if="files[fn]?.isDirty"
                class="w-2 h-2 rounded-full bg-amber-500 shrink-0"
                title="有未保存修改"
              ></span>
            </div>
          </div>
        </div>
      </div>

      <!-- [2026-09-28] [多版本生成采纳与草稿废纸篓] 底部废纸篓/已归档折叠抽屉 -->
      <div
        v-if="trashFiles.length > 0"
        class="rounded-lg border border-slate-200 bg-slate-50/80 overflow-hidden text-xs transition"
      >
        <div
          class="flex items-center justify-between p-2 cursor-pointer select-none hover:bg-slate-100 text-slate-600 font-medium"
          @click="isTrashExpanded = !isTrashExpanded"
        >
          <div class="flex items-center gap-1.5 truncate">
            <i
              :data-lucide="isTrashExpanded ? 'chevron-down' : 'chevron-right'"
              class="w-3.5 h-3.5 text-slate-400"
            ></i>
            <i data-lucide="trash" class="w-3.5 h-3.5 text-slate-400"></i>
            <span>已归档 / 废纸篓</span>
          </div>
          <span class="text-[10px] px-1.5 py-0.2 rounded font-mono bg-slate-200 text-slate-600">
            {{ trashFiles.length }}
          </span>
        </div>
        <div v-show="isTrashExpanded" class="p-1 space-y-1 bg-white border-t border-slate-100">
          <div
            v-for="fn in trashFiles"
            :key="fn"
            class="flex items-center justify-between p-1.5 rounded hover:bg-slate-50 text-slate-500 text-[12px]"
          >
            <div class="truncate mr-1 flex items-center gap-1.5 text-slate-400 line-through">
              <i data-lucide="file-minus" class="w-3.5 h-3.5 shrink-0"></i>
              <span class="truncate">{{ fn }}</span>
            </div>
            <button
              type="button"
              title="一键恢复回档"
              class="px-2 py-0.5 text-[11px] font-medium text-[#7c5bf5] bg-[#7c5bf5]/10 hover:bg-[#7c5bf5]/20 rounded transition flex items-center gap-1 shrink-0 cursor-pointer"
              @click.stop="$emit('restoreFile', fn)"
            >
              <i data-lucide="rotate-cw" class="w-3 h-3"></i>
              <span>恢复</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';

const props = defineProps({
  categories: { type: Array, required: true },
  files: { type: Object, required: true },
  activeCategory: { type: String, default: 'questions' },
  activeFileName: { type: String, default: '' },
  /** 是否允许新建文件（阶段一固定交付物，传 false 隐藏按钮） */
  allowNewFile: { type: Boolean, default: true },
  /** 是否允许刷新目录 */
  allowRefresh: { type: Boolean, default: true },
  /** [2026-09-28] [出题草稿采纳流] 是否展示二元状态徽章（默认 false，防污染阶段二/三；阶段一显式传 true 开启） */
  showStatusBadge: { type: Boolean, default: false },
});

// [2026-09-28] [多版本生成采纳与草稿废纸篓] 派发 deleteFile 与 restoreFile 事件
defineEmits([
  'toggleCategory', 'openFile', 'newFile', 'refreshFiles',
  'deleteFile', 'restoreFile',
]);

const isTrashExpanded = ref(false);

const trashFiles = computed(() => {
  if (!props.files) return [];
  return Object.keys(props.files).filter(fn => props.files[fn]?.is_deleted);
});

function getFilesInCat(catId) {
  return Object.keys(props.files || {}).filter(
    (fn) => props.files[fn].category === catId && !props.files[fn].is_deleted
  );
}

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

onMounted(() => {
  refreshIcons();
});

watch([() => props.activeCategory, () => props.activeFileName, () => props.files, isTrashExpanded], () => {
  refreshIcons();
}, { deep: true });
</script>
