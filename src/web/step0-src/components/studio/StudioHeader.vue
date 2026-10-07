<template>
  <!-- [2026-09-29] [中栏双行标准头部组件 (StudioHeader)] 抽象与跨阶段复用：
       第一行：状态元数据 (徽章/字数/时间) + 自定义操作插槽 (actions)
       第二行：独立平铺文件 Tab 标签栏 (高亮/脏标/废纸篓/关闭) -->
  <div class="flex flex-col select-none relative shrink-0">
    <!-- 顶部轻量浮动通知 (防原生 alert 红线) -->
    <transition name="fade">
      <div
        v-if="noticeMessage"
        class="absolute top-3 left-1/2 -translate-x-1/2 z-50 px-3.5 py-1.5 bg-slate-900/95 text-white text-[12px] font-medium rounded-lg shadow-lg flex items-center gap-2 border border-slate-700/80 pointer-events-none"
      >
        <i data-lucide="info" class="w-3.5 h-3.5 text-amber-400 shrink-0"></i>
        <span>{{ noticeMessage }}</span>
      </div>
    </transition>

    <!-- ===== 第一行：状态与操作工具栏 ===== -->
    <div class="bg-slate-50 border-b border-slate-200 px-3 py-2 flex items-center justify-between gap-3 select-none flex-wrap min-h-[44px]">
      <!-- 左侧：状态与元数据区 -->
      <div class="flex items-center gap-2.5 min-w-0">
        <slot name="meta">
          <!-- 状态徽章 (严格对齐 AGENTS §3.3 / §3.5，0 Emoji，阶段条件化) -->
          <span
            v-if="currentFile"
            class="text-[11px] px-2.5 py-0.5 rounded-full font-mono font-bold flex items-center gap-1.5 shrink-0 shadow-2xs border"
            :class="badgeClass"
          >
            <i :data-lucide="badgeIcon" class="w-3 h-3"></i>
            <span>{{ badgeText }}</span>
          </span>

          <!-- 只读锁态透出 (解决 🟢9) -->
          <span
            v-if="isReadOnly"
            class="text-[11px] px-2 py-0.5 rounded-full font-mono bg-slate-100 text-slate-500 border border-slate-200 shrink-0"
            title="当前文件处于只读保护态"
          >
            只读
          </span>

          <!-- 字数与时间戳 -->
          <span class="text-[12px] text-slate-500 shrink-0 font-mono">
            {{ charCount }} 字符
          </span>
          <span class="text-[12px] text-slate-400 truncate hidden sm:inline">
            生成时间: {{ generatedAt }}
          </span>
        </slot>
        <slot name="meta-extra"></slot>
      </div>

      <!-- 右侧：快捷功能按钮组插槽 (各阶段根据自身动线灵活注入) -->
      <div class="flex items-center gap-2 shrink-0">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- ===== 第二行：独立文件 Tab 标签栏 ===== -->
    <div class="bg-slate-100/90 border-b border-slate-200 flex items-center px-2 pt-1.5 gap-1.5 overflow-x-auto select-none scrollbar-none min-h-[38px]">
      <div
        v-for="fn in openTabs"
        :key="fn"
        class="flex items-center gap-2 px-3 py-1.5 rounded-t-lg text-[13px] font-medium cursor-pointer transition border border-b-0 shrink-0"
        :class="fn === activeFileName ? 'bg-white text-[#7c5bf5] border-slate-200 font-bold -mb-[1px]' : 'bg-slate-200/60 hover:bg-slate-200 text-slate-600 border-transparent'"
        @click="$emit('selectTab', fn)"
      >
        <span class="truncate max-w-[160px]" :title="fn">{{ formatDisplayTitle(fn, files[fn]) }}</span>
        <!-- 废纸篓标识 -->
        <span
          v-if="files[fn]?.isDeleted || files[fn]?.is_deleted"
          class="text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-500 font-normal shrink-0"
        >
          [废纸篓]
        </span>
        <!-- 未保存改动圆点 -->
        <span
          v-if="files[fn]?.isDirty"
          class="w-2 h-2 rounded-full bg-amber-500 shrink-0"
          title="有未保存修改"
        ></span>
        <!-- 关闭标签 -->
        <span
          class="text-slate-400 hover:text-slate-700 hover:bg-slate-300/60 rounded p-0.5 text-xs transition"
          title="关闭标签"
          @click.stop="$emit('closeTab', fn)"
        >
          ×
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, nextTick, onMounted } from 'vue';
import { getActiveBadgeText, formatDisplayTitle } from '../../config/studioArtifactConfig.js';

const props = defineProps({
  files: { type: Object, required: true },
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  stage: { type: String, default: '' },
  noticeMessage: { type: String, default: '' },
  isReadOnly: { type: Boolean, default: false },
});

defineEmits(['selectTab', 'closeTab']);

const currentFile = computed(() => props.files[props.activeFileName] || null);

const charCount = computed(() => (currentFile.value?.content || '').length);

const generatedAt = computed(() => currentFile.value?.generatedAt || '刚刚');

const badgeText = computed(() => {
  return getActiveBadgeText(currentFile.value, props.stage);
});

const badgeClass = computed(() => {
  const f = currentFile.value;
  if (!f) return 'bg-slate-100 text-slate-500 border-slate-200';
  if (props.stage === 'step2' || f.category?.startsWith('source_')) {
    return 'bg-[#7c5bf5]/15 text-[#7c5bf5] border-[#7c5bf5]/30';
  }
  if (f.isActive) return 'bg-[#7c5bf5]/15 text-[#7c5bf5] border-[#7c5bf5]/30';
  if (f.isProtectedArchive) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (f.isCanonicalMirror) return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  if (f.isRetired) return 'bg-slate-100 text-slate-500 border-slate-200';
  if (f.isDeleted || f.is_deleted) return 'bg-slate-100 text-slate-500 border-slate-200';
  if (f.isManual || f.slotKey === 'slot_manual') return 'bg-sky-50 text-sky-700 border-sky-200';
  return 'bg-slate-100 text-slate-600 border-slate-200';
});

const badgeIcon = computed(() => {
  const f = currentFile.value;
  if (!f) return 'file-text';
  if (props.stage === 'step2' || f.category?.startsWith('source_')) {
    return 'layers';
  }
  if (f.isActive) return 'check';
  if (f.isProtectedArchive) return 'archive';
  if (f.isCanonicalMirror) return 'shield';
  if (f.isRetired) return 'clock';
  if (f.isDeleted || f.is_deleted) return 'trash';
  if (f.isManual || f.slotKey === 'slot_manual') return 'file-edit';
  return 'file-text';
});

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

watch([() => props.activeFileName, () => props.openTabs, () => props.files], () => {
  refreshIcons();
}, { deep: true });
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
