<template>
  <!-- [2026-09-23] [阶段概览与交付备注组件化] 通用阶段概览卡片，提供标题、状态标签、说明书入口、一句话目标与全文自适应备注 -->
  <div
    v-show="!collapsed"
    class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3 transition-all duration-300"
  >
    <!-- 第一行：标题 + 状态标签 + 右侧操作入口 (页面使用说明) -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2 flex-wrap">
        <h2 class="text-base font-bold text-slate-900">{{ stageTitle }}</h2>
        <span
          v-if="modeTag"
          class="px-2 py-0.5 rounded text-[10px] font-semibold border"
          :class="isReady ? 'bg-emerald-50 text-emerald-800 border-emerald-100' : 'bg-indigo-50 text-[#7c5bf5] border border-indigo-100'"
        >
          {{ modeTag }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="showMckinsey"
          type="button"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition shadow-xs cursor-pointer"
          title="点击查看本页麦肯锡 V-W-W-H 详细说明"
          @click="$emit('openMckinsey')"
        >
          <i data-lucide="book-open" class="w-3.5 h-3.5 text-[#7c5bf5]"></i>
          <span>页面使用说明</span>
        </button>
      </div>
    </div>

    <!-- 第二行：交付目标（一句话总结，麦肯锡核心价值） -->
    <div class="text-xs text-slate-600 bg-slate-50/80 px-3 py-2 rounded-lg border border-slate-100 flex items-start gap-2">
      <span class="font-bold text-slate-800 shrink-0">交付目标：</span>
      <span class="leading-relaxed">{{ targetText }}</span>
    </div>

    <!-- 第三行：交付情况备注（多行全文展示，随手记随时存，刷新永不丢） -->
    <div class="space-y-1.5 pt-0.5">
      <div class="flex items-center justify-between">
        <label class="text-xs font-bold text-slate-700 flex items-center gap-1">
          <span>交付情况备注</span>
          <span class="text-[11px] font-normal text-slate-400">（人工自由备忘，长文完整可见，刷新不丢失）</span>
        </label>
        <div class="flex items-center gap-2">
          <span
            v-if="notesTip"
            class="text-[11px] font-semibold"
            :class="notesTipSuccess ? 'text-emerald-600' : 'text-slate-400'"
          >
            {{ notesTip }}
          </span>
          <button
            type="button"
            class="px-3 py-1 rounded-md bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-semibold transition flex items-center gap-1 shadow-xs cursor-pointer disabled:opacity-50"
            :disabled="saving"
            @click="handleSave"
          >
            <i data-lucide="check" class="w-3 h-3"></i>
            <span>{{ saving ? '保存中...' : '保存备注' }}</span>
          </button>
        </div>
      </div>
      <textarea
        ref="textareaRef"
        :value="notes"
        rows="2"
        :placeholder="placeholderText"
        class="w-full text-xs text-slate-800 bg-white border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-[#7c5bf5]/20 focus:border-[#7c5bf5] leading-relaxed resize-y transition min-h-[52px]"
        @input="onInput"
      ></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue';

const props = defineProps({
  stageTitle: { type: String, required: true },
  modeTag: { type: String, default: '' },
  isReady: { type: Boolean, default: false },
  targetText: { type: String, required: true },
  notes: { type: String, default: '' },
  notesPlaceholder: { type: String, default: '' },
  showMckinsey: { type: Boolean, default: true },
  collapsed: { type: Boolean, default: false },
});

const emit = defineEmits(['update:notes', 'saveNotes', 'openMckinsey']);

const textareaRef = ref(null);
const saving = ref(false);
const notesTip = ref('');
const notesTipSuccess = ref(false);

const placeholderText = props.notesPlaceholder || '写下本阶段进展或客户特别要求（如：已测5题，第3题豆包答错，待明天复测...）';

function adjustHeight() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${Math.max(52, el.scrollHeight + 2)}px`;
}

function onInput(e) {
  emit('update:notes', e.target.value);
  adjustHeight();
}

watch(() => props.notes, () => {
  nextTick(() => adjustHeight());
});

watch(() => props.collapsed, (val) => {
  if (!val) {
    nextTick(() => {
      adjustHeight();
      if (window.lucide) window.lucide.createIcons();
    });
  }
});

async function handleSave() {
  if (saving.value) return;
  saving.value = true;
  notesTip.value = '保存中...';
  notesTipSuccess.value = false;

  try {
    const success = await emit('saveNotes', props.notes);
    if (success !== false) {
      notesTip.value = '已保存';
      notesTipSuccess.value = true;
      setTimeout(() => {
        if (notesTip.value === '已保存') notesTip.value = '';
      }, 2500);
    } else {
      notesTip.value = '保存失败';
    }
  } catch (_) {
    notesTip.value = '保存失败';
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  nextTick(() => {
    adjustHeight();
    if (window.lucide) window.lucide.createIcons();
  });
});
</script>
