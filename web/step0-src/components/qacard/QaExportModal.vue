<template>
  <!-- 纯净版 AI 语料导出抽屉/弹窗 -->
  <div
    v-if="visible"
    class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 select-none"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full flex flex-col max-h-[85vh] overflow-hidden">
      <!-- 弹窗卡头 -->
      <div class="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div class="flex items-center gap-2">
          <span class="p-1.5 rounded-lg bg-purple-100 text-purple-700">
            <i data-lucide="file-check-2" class="w-4 h-4"></i>
          </span>
          <div>
            <h3 class="text-sm font-bold text-slate-900">GEO 答题卡向量语料库（AI 答案层纯净版）</h3>
            <p class="text-[11px] text-slate-500">已自动剥离人类约束与红线标记，符合老赵哥 S5.5 标准</p>
          </div>
        </div>
        <button
          type="button"
          class="text-slate-400 hover:text-slate-700 p-1 rounded-lg text-sm cursor-pointer"
          @click="$emit('close')"
        >
          ×
        </button>
      </div>

      <!-- 语料 Markdown 内容展示 -->
      <div class="flex-1 min-h-0 p-4 overflow-y-auto bg-slate-900 text-slate-100 font-mono text-xs leading-relaxed select-text">
        <pre class="whitespace-pre-wrap">{{ content }}</pre>
      </div>

      <!-- 底部操作按钮 -->
      <div class="p-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-2">
        <span class="text-xs text-slate-500">
          可直接投喂给向量知识库或外部 RAG 检索管线
        </span>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 cursor-pointer"
            @click="$emit('close')"
          >
            关闭
          </button>
          <button
            type="button"
            class="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#7c5bf5] hover:bg-[#6a48e6] text-white flex items-center gap-1.5 shadow-xs cursor-pointer"
            @click="handleCopy"
          >
            <i data-lucide="copy" class="w-3.5 h-3.5"></i>
            <span>{{ copied ? '已成功复制到剪贴板！' : '一键复制全部语料' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  content: { type: String, default: '' },
});

const emit = defineEmits(['close']);

const copied = ref(false);

const handleCopy = () => {
  if (!props.content) return;
  navigator.clipboard.writeText(props.content).then(() => {
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  }).catch(() => {
    // 降级兜底
    const ta = document.createElement('textarea');
    ta.value = props.content;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  });
};
</script>
