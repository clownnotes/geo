<template>
  <!-- [2026-09-27] [首次交付验收与日常运营复测解耦] 阶段六中栏：首轮核心 3 问改口真机抽测 -->
  <div class="flex-1 bg-white rounded-xl border border-slate-200 flex flex-col h-full shadow-xs overflow-hidden">
    <!-- 1. 顶部 3 问切换选项卡与轻量说明 -->
    <div class="p-3.5 border-b border-slate-100 bg-slate-50/70">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-1.5">
          <i data-lucide="shield-alert" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="text-xs font-bold text-slate-800">首轮核心 3 问改口真机抽测</span>
        </div>
        <span class="text-[11px] text-slate-500 font-medium">
          做完几天后抽测主体口径，验证 AI 是否不再胡说
        </span>
      </div>

      <!-- 3 问切换胶囊 -->
      <div class="flex items-center gap-2">
        <button
          v-for="q in probeQuestions"
          :key="q.id"
          type="button"
          @click="$emit('select-question', q.id)"
          :class="[
            'flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-between border transition',
            activeQuestionId === q.id
              ? 'bg-violet-50 text-violet-800 border-violet-300 shadow-xs'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          ]"
        >
          <span class="truncate">Q{{ q.questionNumber }} {{ q.shortTitle }}</span>
          <span
            :class="[
              'w-2 h-2 rounded-full shrink-0 ml-1.5',
              q.corrected ? 'bg-emerald-500' : 'bg-amber-400'
            ]"
          ></span>
        </button>
      </div>
    </div>

    <!-- 2. 中间单题对比与回填工作台 -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3.5">
      <!-- 当前问句卡片 -->
      <div class="p-3.5 bg-violet-50/50 rounded-xl border border-violet-100 flex items-center justify-between gap-2">
        <div>
          <span class="text-[11px] font-bold text-violet-700 bg-violet-100/80 px-2 py-0.5 rounded">
            建议测试：{{ activeQuestion.targetBot }}
          </span>
          <h3 class="text-sm font-bold text-slate-900 mt-1">
            {{ activeQuestion.question }}
          </h3>
        </div>
        <button
          type="button"
          @click="$emit('copy-question', activeQuestion.question)"
          class="px-3 py-1.5 bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-semibold rounded-lg shrink-0 flex items-center gap-1 shadow-xs transition"
        >
          <i data-lucide="copy" class="w-3.5 h-3.5"></i>
          <span>复制去提问</span>
        </button>
      </div>

      <!-- S0 摸底错误回顾 vs 预期标准定位 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- 历史荒唐回答 (红) -->
        <div class="p-3 bg-red-50/70 border border-red-200/80 rounded-xl space-y-1">
          <div class="flex items-center gap-1 text-red-700 text-xs font-bold">
            <i data-lucide="x-circle" class="w-3.5 h-3.5"></i>
            <span>S0 摸底荒唐回答回顾</span>
          </div>
          <p class="text-xs text-red-800 leading-relaxed">
            {{ activeQuestion.baselineError }}
          </p>
        </div>

        <!-- 预期统一口径 (蓝) -->
        <div class="p-3 bg-blue-50/70 border border-blue-200/80 rounded-xl space-y-1">
          <div class="flex items-center gap-1 text-blue-700 text-xs font-bold">
            <i data-lucide="compass" class="w-3.5 h-3.5"></i>
            <span>S2 统一口径标准定位</span>
          </div>
          <p class="text-xs text-blue-800 leading-relaxed">
            {{ activeQuestion.standardAnswer }}
          </p>
        </div>
      </div>

      <!-- 真机实测回答回填区 -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between">
          <label class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <i data-lucide="terminal" class="w-3.5 h-3.5 text-slate-600"></i>
            <span>最新真机实测回答实录（支持粘贴修改）</span>
          </label>
          <button
            type="button"
            @click="$emit('toggle-corrected', activeQuestion.id)"
            :class="[
              'text-xs font-semibold px-2.5 py-0.5 rounded border transition flex items-center gap-1',
              activeQuestion.corrected
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                : 'bg-slate-100 text-slate-600 border-slate-300 hover:bg-slate-200'
            ]"
          >
            <i :data-lucide="activeQuestion.corrected ? 'check-check' : 'circle'" class="w-3.5 h-3.5"></i>
            <span>{{ activeQuestion.corrected ? '判定：已纠偏改口' : '标记为已改口' }}</span>
          </button>
        </div>

        <textarea
          :value="activeQuestion.defaultActual"
          @input="$emit('update-answer', activeQuestion.id, $event.target.value)"
          rows="4"
          class="w-full text-xs p-3 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7c5bf5]/20 focus:border-[#7c5bf5] text-slate-800 leading-relaxed resize-none font-mono"
          placeholder="前往豆包/DeepSeek提问后，把大模型回答直接粘贴在此处..."
        ></textarea>
      </div>

      <!-- 改口合格判定证据栏 -->
      <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
        <span class="text-slate-500 font-medium">合格核验项：</span>
        <div class="flex flex-wrap gap-2 pt-0.5">
          <span
            v-for="(cp, idx) in activeQuestion.checkPoints"
            :key="idx"
            class="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 text-[11px] flex items-center gap-1"
          >
            <i data-lucide="check" class="w-3 h-3 text-emerald-500"></i>
            {{ cp }}
          </span>
        </div>
      </div>
    </div>

    <!-- 3. 底部达标总结栏 -->
    <div class="p-3 border-t border-slate-100 bg-slate-50/70 flex items-center justify-between text-xs">
      <div class="flex items-center gap-2">
        <span class="text-slate-500">改口抽测进度:</span>
        <span class="font-bold text-slate-800">
          {{ probeQuestions.filter(q => q.corrected).length }} / {{ probeQuestions.length }} 题已改口
        </span>
      </div>
      <span class="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded text-[11px] font-bold">
        {{ probeQuestions.every(q => q.corrected) ? '首轮轻量抽测全量达标' : '部分待真机回填' }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  probeQuestions: { type: Array, default: () => [] },
  activeQuestionId: { type: String, default: '' },
  activeQuestion: { type: Object, default: () => ({}) },
});

defineEmits([
  'select-question',
  'copy-question',
  'update-answer',
  'toggle-corrected',
]);
</script>
