<template>
  <!-- [2026-09-23] [麦肯锡避坑手册抽屉组件化] 通用麦肯锡 V-W-W-H 避坑手册抽屉，支持各阶段配置化传入 -->
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 transition-opacity duration-300"
      @click="$emit('close')"
    ></div>

    <aside
      class="fixed top-0 right-0 w-full sm:w-[500px] h-full bg-white z-50 shadow-2xl border-l border-slate-200 transform transition-transform duration-300 flex flex-col"
      :class="visible ? 'translate-x-0' : 'translate-x-full'"
    >
      <div class="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-[#7c5bf5]"></span>
          <h3 class="text-sm font-bold text-slate-900">{{ title }}</h3>
        </div>
        <button
          type="button"
          class="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition cursor-pointer"
          @click="$emit('close')"
        >
          <i data-lucide="x" class="w-4 h-4"></i>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-5 space-y-3.5 text-slate-800">
        <p class="text-xs text-slate-500">
          说明：本手册收录本阶段的核心认知、业务边界、避坑代价与动线分工，供随时查阅，不打扰主作业区。
        </p>

        <!-- 1. Value 价值成果卡片 -->
        <div class="bg-indigo-50/70 border border-indigo-100 border-l-4 border-l-[#7c5bf5] rounded-lg p-3.5 text-indigo-950">
          <div class="flex items-center gap-1.5 text-[13px] font-bold text-[#7c5bf5]">
            <span class="w-4.5 h-4.5 rounded-full bg-indigo-100 text-[#7c5bf5] text-[11px] font-bold inline-flex items-center justify-center">1</span>
            <span class="px-1.5 py-0.5 rounded bg-indigo-100/90 text-[11px] tracking-wide font-bold">核心交付成果</span>
            做完后能拿到什么？
          </div>
          <div class="text-[13px] leading-relaxed mt-2 text-indigo-950">
            <p v-html="valueDesc"></p>
            <p v-if="valueBusiness" class="text-[12px] text-indigo-900/80 mt-1.5">
              <strong>业务价值</strong>：{{ valueBusiness }}
            </p>
          </div>
        </div>

        <!-- 2. What 本质卡片 -->
        <div class="bg-slate-50 border border-slate-200 border-l-4 border-l-sky-500 rounded-lg p-3 text-slate-800">
          <div class="flex items-center gap-1.5 text-[13px] font-bold text-slate-800">
            <span class="w-4.5 h-4.5 rounded-full bg-sky-100 text-sky-700 text-[11px] font-bold inline-flex items-center justify-center">2</span>
            【这是什么】{{ whatTitle }}
          </div>
          <p class="text-[13px] leading-relaxed mt-1.5 text-slate-600">
            {{ whatDesc }}
          </p>
        </div>

        <!-- 3. Why 原因卡片 -->
        <div class="bg-amber-50/60 border border-amber-200 border-l-4 border-l-amber-500 rounded-lg p-3 text-amber-950">
          <div class="flex items-center gap-1.5 text-[13px] font-bold text-amber-900">
            <span class="w-4.5 h-4.5 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold inline-flex items-center justify-center">3</span>
            【为什么做】{{ whyTitle }}
          </div>
          <p class="text-[13px] leading-relaxed mt-1.5 text-amber-900/80">
            {{ whyDesc }}
          </p>
        </div>

        <!-- 4. How 动线卡片 -->
        <div class="bg-emerald-50/50 border border-emerald-200 border-l-4 border-l-emerald-500 rounded-lg p-3.5 text-emerald-950">
          <div class="flex items-center gap-1.5 text-[13px] font-bold text-emerald-900">
            <span class="w-4.5 h-4.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold inline-flex items-center justify-center">4</span>
            【怎么去做】{{ howTitle }}
          </div>
          <ol class="list-decimal list-inside space-y-1.5 text-[13px] text-emerald-900 mt-2 leading-relaxed">
            <li v-for="(step, idx) in howSteps" :key="idx" v-html="step"></li>
          </ol>
        </div>
      </div>

      <!-- 抽屉底部关闭按钮 -->
      <div class="p-3.5 border-t border-slate-200 bg-slate-50 flex justify-end">
        <button
          type="button"
          class="px-4 py-2 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          @click="$emit('close')"
        >
          我知道了，去干活
        </button>
      </div>
    </aside>
  </teleport>
</template>

<script setup>
import { watch, nextTick } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '麦肯锡认知与避坑手册' },
  valueDesc: { type: String, default: '' },
  valueBusiness: { type: String, default: '' },
  whatTitle: { type: String, default: '' },
  whatDesc: { type: String, default: '' },
  whyTitle: { type: String, default: '' },
  whyDesc: { type: String, default: '' },
  howTitle: { type: String, default: '极简三步闭环' },
  howSteps: { type: Array, default: () => [] },
});

defineEmits(['close']);

watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => {
      if (window.lucide) window.lucide.createIcons();
    });
  }
});
</script>
