<template>
  <li class="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-2.5 list-none">
    <div class="flex flex-wrap items-center gap-2">
      <div class="font-semibold text-slate-900">
        {{ isDeveloper ? '1. 让 Cursor 写出要问的题' : '1. 准备要问豆包的题' }}
      </div>
      <span
        class="px-1.5 py-0.5 rounded text-[10px] font-semibold border"
        :class="
          isRetest
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
            : 'bg-slate-100 text-slate-600 border-slate-200'
        "
      >
        {{ isRetest ? '再测一遍' : '第一次问' }}
      </span>
    </div>

    <p class="text-[11px] text-slate-500">{{ step1BlurbText }}</p>

    <!-- 开发者专属视角：复制出题提示词给 Cursor 与终端命令行 -->
    <template v-if="isDeveloper">
      <div class="flex flex-wrap items-center gap-2 text-[10px] text-slate-500">
        <span class="font-semibold text-slate-600">当前项目</span>
        <code class="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono">
          {{ projectId || '…' }}
        </code>
      </div>

      <button
        type="button"
        class="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 shadow-sm"
        @click="$emit('copy-quality-prompt')"
      >
        <i data-lucide="copy" class="w-3.5 h-3.5"></i>
        <span>{{ copyPromptLabel }}</span>
      </button>

      <p class="text-[10px] text-slate-400" v-html="scriptHintText"></p>

      <details class="bg-white border border-dashed border-slate-200 rounded-lg p-3">
        <summary class="text-[11px] font-semibold text-slate-600 cursor-pointer select-none">
          备用：模板一键出题（质量一般，断网/赶工用）
        </summary>
        <div class="mt-2 space-y-2">
          <p class="text-[10px] text-slate-500">
            服务端按固定模板填空，适合没空开 IDE 时先有一份能跑的题。模板句常偏短、不像真人——<strong>实战前建议改成角色场景长问</strong>（如「我在徐州开厂，想找靠谱做 GEO 的该找谁」）。
          </p>
          <button
            type="button"
            class="px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold disabled:opacity-50"
            :disabled="generatingScript"
            @click="$emit('generate-script')"
          >
            {{ generatingScript ? '正在生成…' : '一键模板出题（保底）' }}
          </button>

          <div class="flex flex-wrap items-stretch gap-2">
            <span class="shrink-0 w-14 self-center text-[10px] font-bold text-slate-500">① 进目录</span>
            <div class="flex-1 min-w-[12rem] flex items-center font-mono text-[11px] bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
              <code class="flex-1 break-all select-all">{{ cdCmdText }}</code>
            </div>
            <button
              type="button"
              class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold"
              @click="$emit('copy-cmd', cdCmdText)"
            >
              复制
            </button>
          </div>

          <div class="flex flex-wrap items-stretch gap-2">
            <span class="shrink-0 w-14 self-center text-[10px] font-bold text-slate-500">② 出题</span>
            <div class="flex-1 min-w-[12rem] flex items-center font-mono text-[11px] bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
              <code class="flex-1 break-all select-all">{{ scriptCmdText }}</code>
            </div>
            <button
              type="button"
              class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold"
              @click="$emit('copy-cmd', scriptCmdText)"
            >
              复制
            </button>
          </div>

          <button
            type="button"
            class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold"
            @click="$emit('copy-cursor-prompt')"
          >
            复制「跑模板命令」给 Cursor
          </button>
        </div>
      </details>
    </template>

    <!-- 写文同事专属视角：纯网页生成题目，无 IDE 概念 -->
    <template v-else>
      <p class="text-[10px] text-slate-400" v-html="scriptHintText"></p>
      <button
        type="button"
        class="px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold disabled:opacity-50"
        :disabled="generatingScript"
        @click="$emit('generate-script')"
      >
        {{ generatingScript ? '正在生成…' : '在本页生成问题清单' }}
      </button>
    </template>
  </li>
</template>

<script setup>
defineProps({
  isDeveloper: { type: Boolean, default: true },
  projectId: { type: String, default: '' },
  isRetest: { type: Boolean, default: false },
  step1BlurbText: { type: String, default: '' },
  copyPromptLabel: { type: String, default: '' },
  scriptHintText: { type: String, default: '' },
  generatingScript: { type: Boolean, default: false },
  cdCmdText: { type: String, default: '' },
  scriptCmdText: { type: String, default: '' },
});

defineEmits([
  'copy-quality-prompt',
  'generate-script',
  'copy-cmd',
  'copy-cursor-prompt',
]);
</script>
