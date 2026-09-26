<template>
  <!-- [2026-09-23] [阶段零组件化] 中间多 Tab 代码与文本编辑器子组件 -->
  <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- Tab 标签栏 + 右侧快捷操作 -->
    <div class="bg-slate-50 border-b border-slate-200 flex items-center justify-between px-2 pt-2 gap-2 overflow-x-auto select-none">
      <!-- 打开的文件标签列表 -->
      <div class="flex items-center gap-1.5 overflow-x-auto flex-1 scrollbar-none">
        <div
          v-for="fn in openTabs"
          :key="fn"
          class="flex items-center gap-2 px-3.5 py-1.5 rounded-t-lg text-[13px] font-medium cursor-pointer transition border border-b-0 shrink-0"
          :class="fn === activeFileName ? 'bg-white text-[#7c5bf5] border-slate-200 font-bold -mb-[1px]' : 'bg-slate-100/80 hover:bg-slate-200/80 text-slate-600 border-transparent'"
          @click="$emit('selectTab', fn)"
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
            @click.stop="$emit('closeTab', fn)"
          >
            ×
          </span>
        </div>
      </div>

      <!-- 右侧快捷按钮：复制 / 保存 -->
      <div class="flex items-center gap-1.5 shrink-0 pb-1">
        <button
          type="button"
          class="px-3 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-medium flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          title="一键复制当前文件内容"
          @click="$emit('copyContent')"
        >
          <i data-lucide="copy" class="w-4 h-4 text-slate-500"></i>
          <span>一键复制内容</span>
        </button>
        <button
          type="button"
          class="px-3 py-1.5 rounded-md bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[13px] font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          title="保存修改至项目"
          @click="$emit('saveFile')"
        >
          <i data-lucide="save" class="w-4 h-4"></i>
          <span>保存文件</span>
        </button>
      </div>
    </div>

    <!-- 文本编辑工作区：行号 + 文本区域 (字号对齐反重力 IDE：正文 14px，行号 12px) -->
    <div class="flex-1 flex overflow-hidden relative font-mono text-sm">
      <!-- 动态行号栏 -->
      <div
        ref="lineNumbersRef"
        class="w-12 bg-slate-50/80 border-r border-slate-200/80 text-slate-400 p-3 select-none text-right font-mono text-[12px] leading-relaxed overflow-hidden shrink-0"
      >
        <div v-for="n in lineCount" :key="n">{{ n }}</div>
      </div>

      <!-- 文本输入区 -->
      <textarea
        ref="textareaRef"
        :value="activeFile?.content || ''"
        class="flex-1 p-3 text-slate-800 bg-white focus:outline-none leading-relaxed resize-none overflow-y-auto font-mono text-[14px] border-none"
        placeholder="当前文件暂无内容，请在左侧选择文件或开始输入..."
        @input="onTextareaInput"
        @scroll="syncScroll"
      ></textarea>
    </div>

    <!-- 底部状态栏 -->
    <div class="px-3.5 py-1.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[12px] text-slate-500 select-none">
      <div class="flex items-center gap-3">
        <span class="font-medium text-slate-700">{{ activeFile ? `${activeFile.dir}/${activeFile.name}` : '未打开文件' }}</span>
        <span>共 {{ lineCount }} 行</span>
        <span>{{ (activeFile?.content || '').length }} 字符</span>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="activeFile?.isDirty" class="flex items-center gap-1 text-amber-700 font-medium">
          <span class="w-2 h-2 rounded-full bg-amber-500"></span>
          <span>有未保存修改 ●</span>
        </span>
        <span v-else class="flex items-center gap-1 text-emerald-700 font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>已保存在 projects.json</span>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
});

const emit = defineEmits([
  'selectTab',
  'closeTab',
  'updateContent',
  'copyContent',
  'saveFile',
]);

const textareaRef = ref(null);
const lineNumbersRef = ref(null);

const activeFile = computed(() => props.files[props.activeFileName] || null);

const lineCount = computed(() => {
  const text = activeFile.value?.content || '';
  return text ? text.split('\n').length : 1;
});

function onTextareaInput(e) {
  emit('updateContent', e.target.value);
}

function syncScroll() {
  if (textareaRef.value && lineNumbersRef.value) {
    lineNumbersRef.value.scrollTop = textareaRef.value.scrollTop;
  }
}

watch(() => props.activeFileName, () => {
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
    syncScroll();
  });
});
</script>
