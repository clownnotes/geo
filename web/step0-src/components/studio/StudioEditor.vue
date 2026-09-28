<template>
  <!-- [2026-09-27] [全阶段通用化] 中间多 Tab 编辑打磨区：
       按文件扩展名自动切换「源码编辑 / Markdown 渲染 / HTML 实时预览」三种形态 -->
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

      <!-- 右侧快捷按钮：采纳状态与操作 / 视图切换 / 全屏 / 复制 / 保存 -->
      <div class="flex items-center gap-2 shrink-0 pb-1">
        <!-- [2026-09-27] [血统溯源与采纳操作] 采纳状态与切换按钮 (严格按规范使用 Lucide 专业图标，零 Emoji) -->
        <div class="flex items-center gap-2">
          <span
            v-if="currentFile?.isActive"
            class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-1"
          >
            <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600"></i>
            <span>客户生效底牌 [{{ currentFile?.versionTag || 'QA-V1' }}]</span>
          </span>
          <button
            v-else-if="canAdoptCurrentFile"
            type="button"
            @click="$emit('adoptFile', activeFileName)"
            class="text-[12px] px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded font-medium transition cursor-pointer flex items-center gap-1"
          >
            <i data-lucide="star" class="w-3.5 h-3.5 text-amber-600"></i>
            <span>设为客户采纳</span>
          </button>
        </div>

        <!-- 视图切换：仅 Markdown 与 HTML 支持预览态 -->
        <div v-if="canPreview" class="flex items-center bg-white border border-slate-200 rounded-md overflow-hidden shadow-2xs">
          <button
            type="button"
            class="px-2.5 py-1.5 text-[12px] font-semibold transition cursor-pointer"
            :class="viewMode === 'edit' ? 'bg-[#7c5bf5] text-white' : 'text-slate-600 hover:bg-slate-50'"
            @click="viewMode = 'edit'"
          >源码</button>
          <button
            type="button"
            class="px-2.5 py-1.5 text-[12px] font-semibold transition cursor-pointer"
            :class="viewMode === 'preview' ? 'bg-[#7c5bf5] text-white' : 'text-slate-600 hover:bg-slate-50'"
            @click="viewMode = 'preview'"
          >预览</button>
        </div>

        <button
          v-if="canPreview"
          type="button"
          class="p-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 transition shadow-2xs cursor-pointer"
          title="全屏预览当前文件"
          @click="$emit('fullscreen')"
        >
          <i data-lucide="maximize-2" class="w-4 h-4"></i>
        </button>

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
          title="保存修改"
          @click="onSaveClick"
        >
          <i data-lucide="save" class="w-4 h-4"></i>
          <span>保存文件</span>
        </button>
      </div>
    </div>

    <!-- 源码编辑态：行号 + 文本区域 -->
    <div v-if="viewMode === 'edit'" class="flex-1 flex overflow-hidden relative font-mono text-sm">
      <div
        ref="lineNumbersRef"
        class="w-12 bg-slate-50/80 border-r border-slate-200/80 text-slate-400 p-3 select-none text-right font-mono text-[12px] leading-relaxed overflow-hidden shrink-0"
      >
        <div v-for="n in lineCount" :key="n">{{ n }}</div>
      </div>
      <!-- [2026-09-27] [视图同步保障] 绑定 :key="activeFileName"，杜绝数据脱节假象 -->
      <textarea
        :key="activeFileName"
        ref="textareaRef"
        :value="activeFile?.content || ''"
        class="flex-1 p-3 text-slate-800 bg-white focus:outline-none leading-relaxed resize-none overflow-y-auto font-mono text-[14px] border-none"
        placeholder="当前文件暂无内容，请在左侧选择文件或开始输入..."
        @input="onTextareaInput"
        @scroll="syncScroll"
      ></textarea>
    </div>

    <!-- Markdown 渲染预览态 -->
    <div
      v-else-if="renderMode === 'markdown'"
      class="flex-1 overflow-y-auto bg-white"
    >
      <div class="max-w-3xl mx-auto px-10 py-8 geo-md" v-html="markdownHtml"></div>
    </div>

    <!-- HTML 实时预览态 -->
    <div v-else class="flex-1 bg-slate-100 relative">
      <iframe
        v-if="activeFile?.content"
        :srcdoc="activeFile.content"
        class="w-full h-full border-0 bg-white"
        sandbox="allow-scripts allow-same-origin"
        title="HTML 实时预览"
      ></iframe>
      <div v-else class="p-6 text-sm text-slate-400">当前文件暂无内容，无法预览。</div>
    </div>

    <!-- 底部状态栏 -->
    <div class="px-3.5 py-1.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[12px] text-slate-500 select-none">
      <div class="flex items-center gap-3">
        <span class="font-medium text-slate-700">{{ activeFile ? `${activeFile.dir}/${activeFile.name}` : '未打开文件' }}</span>
        <span>共 {{ lineCount }} 行</span>
        <span>{{ (activeFile?.content || '').length }} 字符</span>
        <span class="px-1.5 py-0.5 rounded bg-slate-200/70 text-slate-600 font-medium">{{ renderModeLabel }}</span>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="activeFile?.isDirty" class="flex items-center gap-1 text-amber-700 font-medium">
          <span class="w-2 h-2 rounded-full bg-amber-500"></span>
          <span>有未保存修改 ●</span>
        </span>
        <span v-else class="flex items-center gap-1 text-emerald-700 font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>已是最新</span>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';

const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
  /** 由父组件按扩展名算出的渲染模式：markdown / html / code */
  renderMode: { type: String, default: 'code' },
});

const emit = defineEmits([
  'selectTab',
  'closeTab',
  'updateContent',
  'copyContent',
  'saveFile',
  'fullscreen',
  'adoptFile',
]);

const textareaRef = ref(null);
const lineNumbersRef = ref(null);
const viewMode = ref('edit');

const currentFile = computed(() => props.files[props.activeFileName] || null);
const activeFile = currentFile;

/** [2026-09-27] [采纳操作判定] 仅当文件未采纳且属于 questions 或 answers 分类时可被设为生效底牌 */
const canAdoptCurrentFile = computed(() => {
  if (!currentFile.value) return false;
  if (currentFile.value.isActive) return false;
  return currentFile.value.category === 'questions' || currentFile.value.category === 'answers';
});

const canPreview = computed(() => props.renderMode === 'markdown' || props.renderMode === 'html');

const renderModeLabel = computed(() => {
  if (props.renderMode === 'markdown') return 'Markdown';
  if (props.renderMode === 'html') return 'HTML 大屏';
  return '纯代码';
});

const lineCount = computed(() => {
  const text = activeFile.value?.content || '';
  return text ? text.split('\n').length : 1;
});

/** 用宿主页面已加载的 marked 做 Markdown 渲染；未加载时退回等宽纯文本 */
const markdownHtml = computed(() => {
  const raw = activeFile.value?.content || '';
  if (typeof window !== 'undefined' && window.marked && window.marked.parse) {
    return window.marked.parse(raw);
  }
  return `<pre class="whitespace-pre-wrap font-mono text-[13px]">${raw.replace(/</g, '&lt;')}</pre>`;
});

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

function onTextareaInput(e) {
  emit('updateContent', e.target.value);
}

function syncScroll() {
  if (textareaRef.value && lineNumbersRef.value) {
    lineNumbersRef.value.scrollTop = textareaRef.value.scrollTop;
  }
}

function onSaveClick() {
  if (textareaRef.value) {
    emit('updateContent', textareaRef.value.value);
  }
  emit('saveFile');
}

onMounted(() => {
  refreshIcons();
});

// 换文件时：纯代码类强制回到源码态，HTML 文件默认直接展示预览大屏，Markdown 保留用户偏好
watch(() => props.activeFileName, () => {
  if (!canPreview.value) {
    viewMode.value = 'edit';
  } else if (props.renderMode === 'html') {
    viewMode.value = 'preview';
  }
  refreshIcons();
  nextTick(() => {
    syncScroll();
  });
});

watch(() => props.renderMode, (mode) => {
  if (mode === 'code') viewMode.value = 'edit';
  else if (mode === 'html') viewMode.value = 'preview';
  refreshIcons();
});

// [2026-09-27] [采纳状态视觉联动] 监听生效状态与版本号变动，即时刷新 Lucide 图标
watch([() => currentFile.value?.isActive, () => currentFile.value?.versionTag], () => {
  refreshIcons();
});

// [2026-09-27] [编辑器数据同步保障] 监听当前激活文件内容变更，确保外部重载或重置时 textarea DOM 实时同步
watch(() => activeFile.value?.content, (newContent) => {
  if (textareaRef.value && textareaRef.value.value !== (newContent || '')) {
    textareaRef.value.value = newContent || '';
  }
});
</script>

<style scoped>
/* Markdown 预览排版：对齐交付文档的正式观感 */
.geo-md :deep(h1) { font-size: 26px; font-weight: 700; color: #0f172a; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
.geo-md :deep(h2) { font-size: 20px; font-weight: 700; color: #0f172a; margin: 22px 0 10px; }
.geo-md :deep(h3) { font-size: 16px; font-weight: 700; color: #1e293b; margin: 18px 0 8px; }
.geo-md :deep(p)  { font-size: 14px; line-height: 1.85; color: #334155; margin: 10px 0; }
.geo-md :deep(ul), .geo-md :deep(ol) { margin: 10px 0 10px 22px; font-size: 14px; line-height: 1.85; color: #334155; }
.geo-md :deep(ul) { list-style: disc; }
.geo-md :deep(ol) { list-style: decimal; }
.geo-md :deep(li) { margin: 4px 0; }
.geo-md :deep(strong) { color: #0f172a; font-weight: 700; }
.geo-md :deep(blockquote) { border-left: 3px solid #7c5bf5; background: #f8fafc; padding: 10px 14px; margin: 12px 0; color: #475569; font-size: 13px; }
.geo-md :deep(code) { background: #f1f5f9; color: #7c5bf5; padding: 1px 5px; border-radius: 4px; font-size: 13px; }
.geo-md :deep(pre) { background: #0f172a; color: #e2e8f0; padding: 14px 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; }
.geo-md :deep(pre code) { background: transparent; color: inherit; padding: 0; }
.geo-md :deep(table) { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 13px; }
.geo-md :deep(th) { background: #f8fafc; font-weight: 700; text-align: left; padding: 8px 12px; border: 1px solid #e2e8f0; color: #0f172a; }
.geo-md :deep(td) { padding: 8px 12px; border: 1px solid #e2e8f0; color: #334155; }
.geo-md :deep(hr) { border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0; }
.geo-md :deep(a) { color: #7c5bf5; text-decoration: underline; }
</style>
