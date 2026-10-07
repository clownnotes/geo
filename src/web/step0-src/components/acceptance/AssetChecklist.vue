<template>
  <!-- [2026-09-27] [首次交付验收与日常运营复测解耦] 阶段六左栏：S11 七项工程交付资产盘点清单 -->
  <div class="w-full lg:w-[320px] shrink-0 bg-white rounded-xl border border-slate-200 flex flex-col h-full shadow-xs overflow-hidden">
    <!-- 1. 顶部标题与达标统计 -->
    <div class="p-3.5 border-b border-slate-100 bg-slate-50/70">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <i data-lucide="clipboard-check" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="text-xs font-bold text-slate-800">S11 七项工程资产盘点</span>
        </div>
        <span class="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
          7/7 达标通过
        </span>
      </div>
      <p class="text-[11px] text-slate-500 mt-1">
        判定标准：换一个人能不能接手。逐项核对交付底座。
      </p>
    </div>

    <!-- 2. 七项指标列表滚动区 -->
    <div class="flex-1 overflow-y-auto p-2.5 space-y-2">
      <div
        v-for="item in checklist"
        :key="item.id"
        class="p-2.5 rounded-lg border border-slate-200 hover:border-violet-200 hover:bg-slate-50/50 transition relative group"
      >
        <div class="flex items-start justify-between gap-1.5">
          <div class="flex items-center gap-1.5">
            <span class="w-4 h-4 rounded-full bg-violet-100 text-violet-700 text-[10px] font-black flex items-center justify-center shrink-0">
              {{ item.no }}
            </span>
            <span class="text-xs font-bold text-slate-800">{{ item.name }}</span>
          </div>
          <span class="text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-medium border border-emerald-100 shrink-0 flex items-center gap-0.5">
            <i data-lucide="check" class="w-3 h-3"></i>
            {{ item.statusLabel }}
          </span>
        </div>

        <p class="text-[11px] text-slate-500 mt-1.5 leading-relaxed">
          {{ item.standard }}
        </p>

        <div class="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
          <span class="text-slate-400">{{ item.stageName }}</span>
          <span class="font-semibold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
            数量: {{ item.currentCount }}
          </span>
        </div>
      </div>
    </div>

    <!-- 3. 底部外链存活率小结 -->
    <div class="p-3 border-t border-slate-100 bg-slate-50/70 space-y-1.5">
      <div class="flex items-center justify-between text-[11px]">
        <span class="text-slate-500">知乎/头条外链存活</span>
        <span class="font-bold text-emerald-600">100% (无 404 失效)</span>
      </div>
      <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
        <div class="bg-emerald-500 h-full rounded-full w-full"></div>
      </div>
      <p class="text-[10px] text-slate-400 leading-tight">
        注：信源台账已具备真实公开 URL，大模型观察池已注入完成。
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  checklist: { type: Array, default: () => [] },
});
</script>
