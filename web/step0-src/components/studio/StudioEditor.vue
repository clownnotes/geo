<template>
  <!-- [2026-09-28] [中栏双行架构与正交只读] 中间多 Tab 编辑打磨区：
       第一行：状态与操作工具栏 (徽章/字数/时间/恢复/采纳/视图/全屏/复制/保存)
       第二行：独立 Tab 标签栏 (支持废纸篓预览标识与平滑切换) -->
  <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden relative">
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
    <div class="bg-slate-50 border-b border-slate-200 px-3 py-2 flex items-center justify-between gap-3 select-none flex-wrap">
      <!-- 左侧：状态与元数据区 -->
      <div class="flex items-center gap-2.5 min-w-0">
        <!-- 状态徽章 (严格对齐 AGENTS §3.3 / §3.5，0 Emoji，阶段条件化) -->
        <span
          v-if="currentFile"
          class="text-[11px] px-2.5 py-0.5 rounded-full font-mono font-bold flex items-center gap-1.5 shrink-0 shadow-2xs border"
          :class="badgeClass"
        >
          <i :data-lucide="badgeIcon" class="w-3 h-3"></i>
          <span>{{ badgeText }}</span>
        </span>

        <!-- 字数与时间戳 -->
        <span class="text-[12px] text-slate-500 shrink-0 font-mono">
          {{ (currentFile?.content || '').length }} 字符
        </span>
        <span class="text-[12px] text-slate-400 truncate hidden sm:inline">
          生成时间: {{ currentFile?.generatedAt || '未知' }}
        </span>
      </div>

      <!-- 右侧：快捷功能按钮组 (偏右对齐排布) -->
      <div class="flex items-center gap-2 shrink-0">
        <!-- 废纸篓文件专属：一键恢复按钮 (遵循 AGENTS §3.3 视觉红线，采用主色紫，严禁红色) -->
        <button
          v-if="isTrashFile"
          type="button"
          class="px-3 py-1.5 rounded-md bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[12px] font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          title="一键将此文件从废纸篓恢复"
          @click="$emit('restoreFile', activeFileName)"
        >
          <i data-lucide="rotate-cw" class="w-3.5 h-3.5"></i>
          <span>一键恢复此文件</span>
        </button>

        <!-- 采纳按钮 (仅候选草稿且符合采纳守卫时展示) -->
        <button
          v-else-if="canAdoptCurrentFile"
          type="button"
          class="text-[12px] px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-md font-medium transition cursor-pointer flex items-center gap-1 shadow-2xs"
          title="将此候选草稿设为客户采纳底牌"
          @click="$emit('adoptFile', activeFileName)"
        >
          <i data-lucide="star" class="w-3.5 h-3.5 text-amber-600"></i>
          <span>设为客户采纳</span>
        </button>

        <!-- 视图切换：仅 Markdown 与 HTML 支持预览态 -->
        <div v-if="canPreview" class="flex items-center bg-white border border-slate-200 rounded-md overflow-hidden shadow-2xs">
          <button
            type="button"
            class="px-2.5 py-1 text-[12px] font-semibold transition cursor-pointer"
            :class="viewMode === 'edit' ? 'bg-[#7c5bf5] text-white' : 'text-slate-600 hover:bg-slate-50'"
            @click="viewMode = 'edit'"
          >
            源码
          </button>
          <button
            type="button"
            class="px-2.5 py-1 text-[12px] font-semibold transition cursor-pointer"
            :class="viewMode === 'preview' ? 'bg-[#7c5bf5] text-white' : 'text-slate-600 hover:bg-slate-50'"
            @click="viewMode = 'preview'"
          >
            预览
          </button>
        </div>

        <!-- 全屏按钮 -->
        <button
          v-if="canPreview"
          type="button"
          class="p-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 transition shadow-2xs cursor-pointer"
          title="全屏预览当前文件"
          @click="$emit('fullscreen')"
        >
          <i data-lucide="maximize-2" class="w-4 h-4"></i>
        </button>

        <!-- 一键复制 -->
        <button
          type="button"
          class="px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[12px] font-medium flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          title="一键复制当前文件内容"
          @click="$emit('copyContent')"
        >
          <i data-lucide="copy" class="w-3.5 h-3.5 text-slate-500"></i>
          <span class="hidden md:inline">一键复制</span>
        </button>

        <!-- 保存按钮 (只读态下隐藏，生效底牌/最新候选草稿/手建草稿展示) -->
        <button
          v-if="!isReadOnly"
          type="button"
          class="px-3 py-1.5 rounded-md bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[12px] font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          title="保存修改 (Ctrl+S / Cmd+S)"
          @click="onSaveClick"
        >
          <i data-lucide="save" class="w-3.5 h-3.5"></i>
          <span>保存文件</span>
        </button>
      </div>
    </div>

    <!-- ===== 第二行：文件 Tab 标签栏 ===== -->
    <div class="bg-slate-100/90 border-b border-slate-200 flex items-center px-2 pt-1.5 gap-1.5 overflow-x-auto select-none scrollbar-none">
      <div
        v-for="fn in openTabs"
        :key="fn"
        class="flex items-center gap-2 px-3 py-1.5 rounded-t-lg text-[13px] font-medium cursor-pointer transition border border-b-0 shrink-0"
        :class="fn === activeFileName ? 'bg-white text-[#7c5bf5] border-slate-200 font-bold -mb-[1px]' : 'bg-slate-200/60 hover:bg-slate-200 text-slate-600 border-transparent'"
        @click="$emit('selectTab', fn)"
      >
        <span class="truncate max-w-[160px]">{{ fn }}</span>
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

    <!-- ===== 主体区域：源码编辑 / Markdown 预览 / HTML 实时预览 ===== -->
    <!-- 1. 源码编辑态：行号 + 文本区域 (支持只读拦截与快捷键守卫) -->
    <div
      v-if="viewMode === 'edit'"
      class="flex-1 flex overflow-hidden relative font-mono text-sm"
      @keydown.meta.s.prevent="handleKeySave"
      @keydown.ctrl.s.prevent="handleKeySave"
    >
      <div
        ref="lineNumbersRef"
        class="w-12 bg-slate-50/80 border-r border-slate-200/80 text-slate-400 p-3 select-none text-right font-mono text-[12px] leading-relaxed overflow-hidden shrink-0"
      >
        <div v-for="n in lineCount" :key="n">{{ n }}</div>
      </div>
      <textarea
        :key="activeFileName"
        ref="textareaRef"
        :value="activeFile?.content || ''"
        :readonly="isReadOnly"
        class="flex-1 p-3 text-slate-800 bg-white focus:outline-none leading-relaxed resize-none overflow-y-auto font-mono text-[14px] border-none"
        :class="isReadOnly ? 'bg-slate-50/60 text-slate-600 cursor-not-allowed select-text' : ''"
        :placeholder="isReadOnly ? '当前文件处于只读归档状态，仅供预览查验。' : '当前文件暂无内容，请在左侧选择文件或开始输入...'"
        @input="onTextareaInput"
        @scroll="syncScroll"
      ></textarea>
    </div>

    <!-- 2. Markdown 渲染预览态 -->
    <div
      v-else-if="renderMode === 'markdown'"
      class="flex-1 overflow-y-auto bg-white"
    >
      <div class="max-w-3xl mx-auto px-10 py-8 geo-md" v-html="markdownHtml"></div>
    </div>

    <!-- 3. HTML 实时预览态 -->
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

    <!-- ===== 底部状态栏 ===== -->
    <div class="px-3.5 py-1.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[12px] text-slate-500 select-none">
      <div class="flex items-center gap-3">
        <span class="font-medium text-slate-700">
          {{ activeFile ? `${activeFile.dir || ''}/${activeFile.name}` : '未打开文件' }}
        </span>
        <span>共 {{ lineCount }} 行</span>
        <span>{{ (activeFile?.content || '').length }} 字符</span>
        <span class="px-1.5 py-0.5 rounded bg-slate-200/70 text-slate-600 font-medium">
          {{ renderModeLabel }}
        </span>
        <span v-if="isReadOnly" class="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-medium">
          只读模式
        </span>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="activeFile?.versionTag"
          class="px-1.5 py-0.5 rounded text-[11px] font-mono border"
          :class="activeFile?.isActive ? 'bg-[#7c5bf5]/15 text-[#7c5bf5] border-[#7c5bf5]/30 font-semibold' : 'bg-slate-100 text-slate-600 border-slate-200'"
        >
          {{ activeFile.versionTag }}
        </span>
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
import {
  isReadOnlyFile,
  getActiveBadgeText,
  getCoreFilesByStage,
} from '../../config/studioArtifactConfig.js';

const props = defineProps({
  openTabs: { type: Array, required: true },
  activeFileName: { type: String, default: '' },
  files: { type: Object, required: true },
  /** 由父组件按扩展名算出的渲染模式：markdown / html / code */
  renderMode: { type: String, default: 'code' },
  /** 当前阶段标识：'step0' 或 'step1'，默认空串，未传时安全降级不崩溃 (解决 P1-7) */
  stage: { type: String, default: '' },
  /** 当前阶段允许采纳的有效槽位清单，未传默认空数组 */
  validAdoptSlots: { type: Array, default: () => [] },
});

// 锁定标准事件契约 (解决 P1-11)
const emit = defineEmits([
  'selectTab',
  'closeTab',
  'updateContent',
  'copyContent',
  'saveFile',
  'fullscreen',
  'adoptFile',
  'restoreFile',
]);

const textareaRef = ref(null);
const lineNumbersRef = ref(null);
const viewMode = ref('edit');

const currentFile = computed(() => props.files[props.activeFileName] || null);
const activeFile = currentFile;

// 废纸篓文件状态判定
const isTrashFile = computed(() => {
  return Boolean(currentFile.value?.isDeleted || currentFile.value?.is_deleted);
});

// 正交只读判定：利用纯函数判定当前文件是否只读 (解决 P0-1, P0-3, P0-4)
const isReadOnly = computed(() => {
  return isReadOnlyFile(currentFile.value, props.files, props.stage);
});

// 状态徽章文本与样式
const badgeText = computed(() => {
  return getActiveBadgeText(currentFile.value, props.stage);
});

const badgeClass = computed(() => {
  const f = currentFile.value;
  if (!f) return 'bg-slate-100 text-slate-500 border-slate-200';
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
  if (f.isActive) return 'check';
  if (f.isProtectedArchive) return 'archive';
  if (f.isCanonicalMirror) return 'shield';
  if (f.isRetired) return 'clock';
  if (f.isDeleted || f.is_deleted) return 'trash';
  if (f.isManual || f.slotKey === 'slot_manual') return 'file-edit';
  return 'file-text';
});

/**
 * 采纳守卫：仅允许合格的候选草稿或已淘汰历史旧版回滚 (解决 P0-3 & P1-7)
 */
const canAdoptCurrentFile = computed(() => {
  if (!currentFile.value) return false;
  if (currentFile.value.isActive) return false;
  // 手建自定义草稿与杂项草稿不可作为核心工序底牌被采纳
  if (currentFile.value.isManual || currentFile.value.slotKey === 'slot_manual' || currentFile.value.slotKey === 'slot_misc') {
    return false;
  }
  // 废纸篓文件禁止采纳
  if (currentFile.value.isDeleted || currentFile.value.is_deleted) return false;
  // 首版留档母版禁止采纳
  if (currentFile.value.isProtectedArchive) return false;
  // 规范骨干镜像禁止直接采纳自身
  if (currentFile.value.isCanonicalMirror) return false;
  const coreFiles = getCoreFilesByStage(props.stage);
  if (coreFiles.includes(currentFile.value.name)) return false;

  // 必须在当前阶段有效采纳槽位内 (Fail-Closed 关闸)
  if (props.validAdoptSlots && props.validAdoptSlots.length > 0) {
    return props.validAdoptSlots.includes(currentFile.value.slotKey);
  }
  return false;
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

// 友好浮动通知 (防 alert 红线)
const noticeMessage = ref('');
let noticeTimer = null;
function showNotice(msg) {
  noticeMessage.value = msg;
  if (noticeTimer) clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    noticeMessage.value = '';
  }, 3200);
}

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

function onTextareaInput(e) {
  if (isReadOnly.value) return;
  emit('updateContent', e.target.value);
}

function syncScroll() {
  if (textareaRef.value && lineNumbersRef.value) {
    lineNumbersRef.value.scrollTop = textareaRef.value.scrollTop;
  }
}

function onSaveClick() {
  if (isReadOnly.value) {
    handleReadOnlySaveBlocked();
    return;
  }
  const content = textareaRef.value ? textareaRef.value.value : (currentFile.value?.content || '');
  emit('saveFile', {
    filename: props.activeFileName,
    content,
  });
}

function handleKeySave() {
  if (isReadOnly.value) {
    handleReadOnlySaveBlocked();
    return;
  }
  onSaveClick();
}

function handleReadOnlySaveBlocked() {
  if (isTrashFile.value) {
    showNotice('该文件在废纸篓中，只读不可修改！如需修改请点击上方【一键恢复此文件】。');
  } else if (currentFile.value?.isProtectedArchive) {
    showNotice('首版母版留档受系统终身保护，只读不可修改！');
  } else if (currentFile.value?.isCanonicalMirror) {
    showNotice('规范主干已自动镜像生效底牌，由程序单向写入，只读不可直接覆盖！');
  } else if (currentFile.value?.isRetired) {
    showNotice('当前为已淘汰历史版本，只读归档！如需以此版本为准修改，请点击【设为客户采纳】执行回滚。');
  } else {
    showNotice('当前文件处于只读锁定状态，禁止保存修改！');
  }
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

watch([() => currentFile.value?.isActive, () => currentFile.value?.versionTag, () => currentFile.value?.isRetired, isTrashFile], () => {
  refreshIcons();
});

watch(() => activeFile.value?.content, (newContent) => {
  if (textareaRef.value && textareaRef.value.value !== (newContent || '')) {
    textareaRef.value.value = newContent || '';
  }
});
</script>

<style scoped>
/* 浮动提示淡入淡出动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

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
