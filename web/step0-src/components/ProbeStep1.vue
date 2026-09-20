<template>
  <li class="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-2.5 list-none">
    <div class="flex flex-wrap items-center gap-2">
      <div class="font-semibold text-slate-900">1. 准备要问豆包的题</div>
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
    <p class="text-[10px] text-slate-400" v-html="scriptHintText"></p>

    <button
      type="button"
      class="px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold disabled:opacity-50"
      :disabled="generatingScript"
      @click="$emit('generate-script')"
    >
      {{ generatingScript ? '正在生成…' : '在本页生成问题清单' }}
    </button>
  </li>
</template>

<script setup>
defineProps({
  isRetest: { type: Boolean, default: false },
  step1BlurbText: { type: String, default: '' },
  scriptHintText: { type: String, default: '' },
  generatingScript: { type: Boolean, default: false },
});

defineEmits(['generate-script']);
</script>
