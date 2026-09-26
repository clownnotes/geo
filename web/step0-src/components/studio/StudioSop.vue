<template>
  <!-- [2026-09-23] [阶段零子页面纯粹化] 右侧 SOP 面板：阶段零极简两步闭环，0.2 贴回答后直接收口通关 -->
  <aside class="w-full lg:w-80 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 顶栏：显示当前小步交付动作 (字号对齐反重力 IDE 顶栏) -->
    <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <i data-lucide="list-ordered" class="w-4 h-4 text-[#7c5bf5]"></i>
        <span class="text-[13px] font-bold text-slate-800 uppercase tracking-wider">{{ stepBarTitle }}</span>
      </div>
      <span class="text-[12px] text-slate-500 font-medium">第 {{ currentStep }} / 2 步</span>
    </div>

    <!-- 动线卡片区：100% 只保留当前小步的内容 -->
    <div class="flex-1 overflow-y-auto p-3.5 text-sm">
      <!-- 0.1 专属：出题与打磨 -->
      <div
        v-if="currentStep === 1"
        class="p-4 rounded-xl border-2 border-[#7c5bf5] bg-indigo-50/20 space-y-3.5"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-5.5 h-5.5 rounded-full font-bold flex items-center justify-center text-[12px] bg-[#7c5bf5] text-white shrink-0">
              1
            </span>
            <span class="font-bold text-slate-900 text-[15px]">生成并打磨提问清单</span>
          </div>
          <span class="text-[11px] px-2 py-0.5 rounded font-bold text-[#7c5bf5] bg-white border border-[#7c5bf5]/30">
            进行中
          </span>
        </div>
        <p class="text-[13px] text-slate-700 leading-relaxed">
          AI 根据客户定位已预生成 5 道核心题。交付专家可在中间编辑器直接修改润色，从 60 分打磨到 80 分。
        </p>
        <div class="pt-2 flex flex-col gap-2.5">
          <button
            type="button"
            class="px-3 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-[#7c5bf5] text-[13px] font-semibold flex items-center justify-center gap-1.5 transition shadow-2xs cursor-pointer"
            @click="$emit('refreshQuestions')"
          >
            <i data-lucide="sparkles" class="w-4 h-4"></i>
            <span>重新出题（生成新版）</span>
          </button>
          <button
            type="button"
            class="w-full py-2.5 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[14px] font-bold transition flex items-center justify-center gap-1.5 shadow cursor-pointer"
            @click="$emit('proceedToNext', 2)"
          >
            <span>保存并前往：0.2 网页提问拿答案</span>
            <i data-lucide="arrow-right" class="w-4 h-4"></i>
          </button>
        </div>
      </div>

      <!-- 0.2 专属：去豆包网页提问拿答案 (直接完成阶段零) -->
      <div
        v-else-if="currentStep === 2"
        class="p-4 rounded-xl border-2 border-[#7c5bf5] bg-indigo-50/20 space-y-3.5"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-5.5 h-5.5 rounded-full font-bold flex items-center justify-center text-[12px] bg-[#7c5bf5] text-white shrink-0">
              2
            </span>
            <span class="font-bold text-slate-900 text-[15px]">去豆包网页提问拿答案</span>
          </div>
          <span class="text-[11px] px-2 py-0.5 rounded font-bold text-[#7c5bf5] bg-white border border-[#7c5bf5]/30">
            进行中
          </span>
        </div>
        <p class="text-[13px] text-slate-700 leading-relaxed">
          点击中间【一键复制内容】，打开豆包网页逐题提问，将豆包的真实回答结果贴回中间文件。
        </p>
        <div class="pt-2 flex flex-col gap-2.5">
          <a
            href="https://www.doubao.com"
            target="_blank"
            rel="noopener noreferrer"
            class="px-3 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-semibold flex items-center justify-center gap-1.5 transition shadow-2xs"
          >
            <i data-lucide="external-link" class="w-4 h-4 text-[#7c5bf5]"></i>
            <span>打开豆包网页版提问</span>
          </a>
          <button
            type="button"
            class="w-full py-2.5 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[14px] font-bold transition flex items-center justify-center gap-1.5 shadow cursor-pointer"
            @click="$emit('finishStage0')"
          >
            <span>保存答案，完成阶段零（前往 01 现状诊断）</span>
            <i data-lucide="arrow-right" class="w-4 h-4"></i>
          </button>
          <button
            type="button"
            class="w-full py-1 text-slate-400 hover:text-slate-600 text-[12px] transition text-center cursor-pointer"
            @click="$emit('switchStep', 1)"
          >
            ← 返回 0.1 修改题目
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, nextTick, watch } from 'vue';

const props = defineProps({
  currentStep: { type: Number, default: 1 },
  isReady: { type: Boolean, default: false },
});

defineEmits(['switchStep', 'refreshQuestions', 'proceedToNext', 'finishStage0']);

const stepTitles = {
  1: '0.1 题目打磨动作',
  2: '0.2 网页提问拿答案',
};

const stepBarTitle = computed(() => stepTitles[props.currentStep] || 'SOP 交付动作');

watch(() => props.currentStep, () => {
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
});
</script>
