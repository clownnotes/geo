<template>
  <!-- 中栏：文章字典式撰写与在线定稿工作台 (flex-1) -->
  <main class="flex-1 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden min-w-0">
    <div v-if="topic" class="flex-1 flex flex-col min-h-0">
      <!-- 1. 顶部操作栏 -->
      <div class="p-3.5 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between gap-3 flex-wrap">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-mono px-1.5 py-0.5 rounded font-bold bg-slate-200/70 text-slate-800">
              {{ topic.id }}
            </span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded font-semibold border"
              :class="topic.group === 'first_sample' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-700 border-slate-200'"
            >
              {{ topic.group === 'first_sample' ? '交付核心 · 首次打样' : '日常运营池' }}
            </span>
            <span
              v-if="topic.status === 'invalid_404'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-rose-50 text-rose-700 border border-rose-200"
            >
              404 失效需改写
            </span>
            <span
              v-else-if="article?.isFinalized"
              class="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-blue-50 text-blue-700 border border-blue-200"
            >
              已定稿落盘
            </span>
            <span
              v-else
              class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-amber-50 text-amber-800 border border-amber-200"
            >
              仅草稿 · 待定稿
            </span>
          </div>
          <h3 class="text-sm font-bold text-slate-900 mt-1 truncate" :title="topic.title">
            {{ topic.title }}
          </h3>
        </div>

        <!-- 动作按钮组 -->
        <div class="flex items-center gap-2 shrink-0">
          <button
            type="button"
            class="py-1.5 px-3 bg-violet-600 hover:bg-violet-700 text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer"
            title="基于关联答题卡事实，严格遵循老赵哥 S7 规范一键拼装生成字典式长文"
            @click="$emit('generate-draft', topic.id)"
          >
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            <span>智能生成初稿</span>
          </button>

          <button
            type="button"
            class="py-1.5 px-3.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer"
            title="核对品牌名、电话与论据无误后保存定稿"
            @click="$emit('save-final', topic.id)"
          >
            <i data-lucide="save" class="w-3.5 h-3.5"></i>
            <span>保存定稿</span>
          </button>
        </div>
      </div>

      <!-- 404 失效报警预警横幅 -->
      <div
        v-if="topic.status === 'invalid_404'"
        class="bg-rose-50 border-b border-rose-200 px-4 py-2.5 flex items-center justify-between text-xs text-rose-800"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="alert-octagon" class="w-4 h-4 text-rose-600 shrink-0"></i>
          <span><strong>信源异常警报</strong>：该选题先前发布的外链返回 404（已下架）。请微调首段或论据事实，重新点击【保存定稿】并发往新信源！</span>
        </div>
      </div>

      <!-- 2. 编辑区主体 -->
      <div class="flex-1 min-h-0 p-3.5 flex flex-col space-y-2.5 overflow-hidden">
        <div class="flex items-center justify-between text-xs text-slate-500">
          <span class="font-medium">老赵哥 S7 字典式正文（首段直接结论 · 模块独立无过渡词 · 纯净 Markdown）</span>
          <span class="font-mono text-[11px]">{{ article?.charCount || 0 }} 字</span>
        </div>

        <textarea
          :value="article?.fullMarkdown || ''"
          class="flex-1 w-full p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 leading-relaxed resize-none focus:bg-white focus:border-[#7c5bf5] focus:outline-none overflow-y-auto"
          placeholder="点击上方【智能生成初稿】一键填充，或直接在此编写长文..."
          @input="$emit('update-markdown', $event.target.value)"
        ></textarea>
      </div>

      <!-- 3. 底部 S7 质检合规条 -->
      <div class="p-3 border-t border-slate-100 bg-slate-50/80 flex items-center justify-between gap-3 text-xs flex-wrap">
        <div class="flex items-center gap-3 flex-wrap">
          <div class="flex items-center gap-1.5">
            <span class="text-[11px] font-semibold text-slate-600">S7 质检评分：</span>
            <span
              class="font-mono font-bold px-1.5 py-0.5 rounded text-[11px]"
              :class="auditResult?.isHealthy ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
            >
              {{ auditResult?.score || 0 }} 分
            </span>
          </div>

          <!-- 质检项标签 -->
          <div class="flex items-center gap-1.5 text-[10px]">
            <span class="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
              首段直接结论
            </span>
            <span class="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
              无过渡词 (首先/其次)
            </span>
            <span class="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
              广告法无极限词
            </span>
            <span class="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
              统一信用代码核验
            </span>
          </div>
        </div>

        <div v-if="auditResult?.issues?.length" class="text-[11px] text-amber-700 flex items-center gap-1">
          <i data-lucide="info" class="w-3.5 h-3.5 text-amber-600"></i>
          <span>{{ auditResult.issues[0].text }}</span>
        </div>
        <div v-else class="text-[11px] text-emerald-700 flex items-center gap-1">
          <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>完美符合 S7 字典式长文与信源发布规范</span>
        </div>
      </div>
    </div>

    <!-- 空白占位态 -->
    <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-400 p-8 space-y-2">
      <i data-lucide="file-edit" class="w-10 h-10 text-slate-300"></i>
      <span class="text-xs font-medium">请从左侧选择一个选题进行撰写与定稿</span>
    </div>
  </main>
</template>

<script setup>
defineProps({
  topic: { type: Object, default: null },
  article: { type: Object, default: null },
  auditResult: { type: Object, default: null },
});

defineEmits([
  'generate-draft',
  'save-final',
  'update-markdown',
]);
</script>
