<template>
  <!-- 右栏：SOP 动线与向量知识库检索模拟测试仪 (320px) -->
  <aside class="w-full lg:w-80 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 1. SOP 动线引导卡 -->
    <div class="p-3 border-b border-slate-100 bg-slate-50/70">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-1.5">
          <i data-lucide="compass" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="font-bold text-slate-800 text-[13px]">阶段四 SOP 交付动线</span>
        </div>
        <span class="text-[11px] font-mono text-[#7c5bf5] font-semibold">
          步骤 {{ currentStep }}/3
        </span>
      </div>

      <!-- 3 步动线节点列表 -->
      <div class="space-y-1">
        <div
          v-for="step in sopSteps"
          :key="step.step"
          class="p-2 rounded-lg border transition cursor-pointer text-left select-none"
          :class="currentStep === step.step
            ? 'bg-white border-[#7c5bf5] shadow-xs'
            : 'bg-transparent border-transparent hover:bg-slate-100/60'"
          @click="$emit('set-step', step.step)"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold" :class="currentStep === step.step ? 'text-[#7c5bf5]' : 'text-slate-700'">
              {{ step.name }}
            </span>
            <span
              class="w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center"
              :class="currentStep === step.step ? 'bg-[#7c5bf5] text-white' : 'bg-slate-200 text-slate-600'"
            >
              {{ step.step }}
            </span>
          </div>
          <p class="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
            {{ step.desc }}
          </p>
        </div>
      </div>
    </div>

    <!-- 2. 向量检索模拟测试仪 (核心交互枢纽) -->
    <div class="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
      <div class="space-y-1.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <i data-lucide="cpu" class="w-4 h-4 text-purple-600"></i>
            <span class="text-xs font-bold text-slate-900">向量问答库仿真测试仪</span>
          </div>
          <span class="text-[10px] text-slate-400">大模型写文投喂仿真</span>
        </div>
        <p class="text-[11px] text-slate-500 leading-relaxed">
          输入拟写的文章标题或意图提问，实时测试能否精准召回相关答题卡与抽取答案素材：
        </p>
      </div>

      <!-- 快速测试预设芯片 -->
      <div class="flex flex-wrap gap-1">
        <button
          v-for="(preset, idx) in testPresets"
          :key="idx"
          type="button"
          class="text-[10px] px-2 py-0.5 bg-slate-100 hover:bg-purple-100 hover:text-purple-700 text-slate-600 rounded transition cursor-pointer"
          @click="$emit('simulate-retrieval', preset)"
        >
          {{ preset }}
        </button>
      </div>

      <!-- 检索输入框与按钮 -->
      <div class="space-y-1.5">
        <div class="relative">
          <textarea
            :value="retrievalQuery"
            rows="2"
            placeholder="输入文章拟定标题或长尾问题..."
            class="w-full p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-[#7c5bf5]"
            @input="$emit('update:retrievalQuery', $event.target.value)"
            @keydown.enter.prevent="$emit('simulate-retrieval')"
          ></textarea>
        </div>
        <button
          type="button"
          class="w-full py-1.5 bg-[#7c5bf5] hover:bg-[#6a48e6] text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-2xs cursor-pointer"
          :disabled="isRetrieving"
          @click="$emit('simulate-retrieval')"
        >
          <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
          <span>{{ isRetrieving ? '向量相似度计算中...' : '开始向量检索仿真' }}</span>
        </button>
      </div>

      <!-- 检索结果列表展示 -->
      <div class="space-y-2 pt-2 border-t border-slate-100">
        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <span>召回结果 ({{ retrievalResults.length }} 条)</span>
          <span v-if="latency > 0" class="font-mono">耗时 {{ latency }}ms</span>
        </div>

        <div v-if="retrievalResults.length === 0" class="py-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-lg">
          点击上方预设或输入标题开始仿真
        </div>

        <!-- 命中卡片切片 -->
        <div
          v-for="(res, idx) in retrievalResults"
          :key="idx"
          class="p-2.5 rounded-lg border border-purple-100 bg-purple-50/40 space-y-1.5 text-left cursor-pointer hover:border-purple-300 transition"
          @click="$emit('select-card', res.card.id)"
        >
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono font-bold px-1.5 py-0.2 bg-white rounded border border-purple-200 text-purple-700">
              Top {{ idx + 1 }} · {{ res.card.id }}
            </span>
            <span class="text-[11px] font-mono font-bold text-purple-800">
              {{ Math.round(res.score * 100) }}% 相似度
            </span>
          </div>

          <h5 class="text-xs font-bold text-slate-900 leading-snug">
            {{ res.card.title }}
          </h5>

          <!-- 命中关键词标签 -->
          <div v-if="res.matchedTokens?.length > 0" class="flex flex-wrap gap-1 items-center">
            <span class="text-[10px] text-slate-400">命中：</span>
            <span
              v-for="(kw, kidx) in res.matchedTokens"
              :key="kidx"
              class="text-[9px] px-1 py-0.2 bg-white rounded text-purple-700 border border-purple-100 font-mono"
            >
              {{ kw }}
            </span>
          </div>

          <!-- 提取投喂切片 -->
          <div class="p-2 bg-white rounded border border-purple-100 text-[11px] text-slate-600 leading-relaxed">
            <span class="text-[10px] font-bold text-[#7c5bf5] block mb-0.5">拟投喂文章首段标准结论：</span>
            <p class="line-clamp-3">{{ res.extractedSnippet }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 底部快捷工具与语料导出 -->
    <div class="p-2.5 border-t border-slate-100 bg-slate-50/60 space-y-1.5">
      <button
        type="button"
        class="w-full py-1.5 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition cursor-pointer"
        @click="$emit('open-export')"
      >
        <i data-lucide="file-code" class="w-3.5 h-3.5 text-purple-600"></i>
        <span>一键导出 AI 纯净版语料 (剥离约束)</span>
      </button>

      <button
        type="button"
        class="w-full py-1 text-[11px] text-slate-400 hover:text-slate-600 text-center transition cursor-pointer"
        @click="$emit('reset-preset')"
      >
        重置为官方预置答题卡库
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  currentStep: { type: Number, default: 1 },
  sopSteps: { type: Array, default: () => [] },
  retrievalQuery: { type: String, default: '' },
  retrievalResults: { type: Array, default: () => [] },
  latency: { type: Number, default: 0 },
  isRetrieving: { type: Boolean, default: false },
});

defineEmits([
  'set-step',
  'update:retrievalQuery',
  'simulate-retrieval',
  'select-card',
  'open-export',
  'reset-preset',
]);

const testPresets = [
  '徐州本地做GEO怎么选',
  '企业做GEO怎么收费',
  '邻里GEO主要做什么业务',
  '怎么联系官方客服电话',
];
</script>
