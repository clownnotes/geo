<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-base font-bold text-slate-900">阶段零：先去豆包摸底</h2>
        <p class="text-xs text-slate-500 mt-1 max-w-xl">
          先问豆包几句<strong>真人会问的话</strong>：它认不认识你们、推谁、有没有说错。这是摸底，不是一次塞满词库。
        </p>
        <p class="text-[11px] text-slate-400 mt-1">
          右上角会分开显示两件事：<strong>问题清单</strong>（要问豆包什么）和<strong>豆包答案是否已存进项目</strong>（问完并点过确认）。不要当成一回事。
        </p>
      </div>
      <div class="flex flex-col items-end gap-2 shrink-0">
        <div class="flex flex-wrap gap-2 justify-end">
          <span
            class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border"
            :class="qlistBadge.className"
          >
            {{ qlistBadge.text }}
          </span>
          <span
            class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border"
            :class="writeStatusBadge.className"
          >
            {{ writeStatusBadge.text }}
          </span>
          <span
            v-if="String(projectData.probe_status || '') === 'awaiting_retest'"
            class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border bg-amber-50 text-amber-900 border-amber-200"
          >
            该再测一遍
          </span>
          <span
            v-if="isSitePending"
            class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border bg-indigo-50 text-indigo-800 border-indigo-200"
          >
            由我方全托管 / 待客户域名
          </span>
          <span
            v-if="projectData.probe_baseline_id"
            class="text-[10px] font-mono text-slate-500"
            title="存档编号"
          >
            {{ projectData.probe_baseline_id }}
          </span>
        </div>
        <button
          type="button"
          class="py-1.5 px-3 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 flex items-center gap-1"
          @click="$emit('refresh')"
        >
          <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>重新检查进度
        </button>
      </div>
    </div>

    <!-- [2026-09-22] [管理端功能解答麦肯锡模型与阶段零重构] 重构顶部静态引导为麦肯锡 V-W-W-H 四层卡片与四色侧彩条，保留 modeBanner 与右上角双徽章 -->
    <!-- 麦肯锡 V-W-W-H 认知引导系统 -->
    <div class="space-y-2.5">
      <!-- 1. Value 价值结论（系统主色紫 #7c5bf5，结论先行大卡片） -->
      <div class="bg-indigo-50/70 border border-indigo-100 border-l-4 border-l-[#7c5bf5] rounded-lg p-3 text-indigo-950">
        <div class="flex items-center gap-1.5 text-xs font-bold text-[#7c5bf5]">
          <span class="w-4 h-4 rounded-full bg-indigo-100 text-[#7c5bf5] text-[10px] font-bold inline-flex items-center justify-center">1</span>
          <span class="px-1.5 py-0.5 rounded bg-indigo-100/90 text-[10px] tracking-wide font-bold">核心交付成果</span>
          做完后能拿到什么？
        </div>
        <div class="text-xs leading-relaxed mt-1.5 text-indigo-950">
          <p>
            做完后，项目里会有：<strong>① 一份问题清单</strong>；<strong>② 一份已确认写入的豆包答案存档</strong>。
          </p>
          <p class="text-[11px] text-indigo-900/80 mt-1">
            <strong>业务价值</strong>：后面写什么文章、补什么官网，都拿这份真实摸底当对照，不再凭感觉瞎写。
          </p>
        </div>
      </div>

      <!-- 2. What 与 3. Why 双列并排（提升垂直利用率，不压迫下方操作区） -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        <!-- What 这是什么（冷调蓝灰色，客观边界） -->
        <div class="bg-slate-50 border border-slate-200 border-l-4 border-l-sky-500 rounded-lg p-2.5 text-slate-800">
          <div class="flex items-center gap-1.5 text-xs font-bold text-slate-800">
            <span class="w-4 h-4 rounded-full bg-sky-100 text-sky-700 text-[10px] font-bold inline-flex items-center justify-center">2</span>
            【这是什么】快速口语摸底，不是建词库
          </div>
          <p class="text-[11px] leading-relaxed mt-1 text-slate-600">
            就像看病前先量个血压：挑 8~10 句客户行业里真人常问的话去问豆包。只管摸清它认不认识你们、推谁、有没有说错。不改官网、不建正式词库。
          </p>
        </div>

        <!-- Why 为什么做（暖调琥珀黄，痛点避坑） -->
        <div class="bg-amber-50/60 border border-amber-200 border-l-4 border-l-amber-500 rounded-lg p-2.5 text-amber-950">
          <div class="flex items-center gap-1.5 text-xs font-bold text-amber-900">
            <span class="w-4 h-4 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold inline-flex items-center justify-center">3</span>
            【为什么做】防止闭门造车与盲人摸象
          </div>
          <p class="text-[11px] leading-relaxed mt-1 text-amber-900/80">
            很多客户以为大模型什么都懂，其实常把客户当竞品或根本搜不到。不摸底就发文章 = 盲人摸象。先找出答错、漏答的地方，后面优化才有的放矢。
          </p>
        </div>
      </div>

      <!-- 4. How 怎么去做（通路翡翠绿，动线闭环） -->
      <div class="bg-emerald-50/50 border border-emerald-200 border-l-4 border-l-emerald-500 rounded-lg p-3 text-emerald-950">
        <div class="flex flex-wrap items-center justify-between gap-1">
          <div class="flex items-center gap-1.5 text-xs font-bold text-emerald-900">
            <span class="w-4 h-4 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold inline-flex items-center justify-center">4</span>
            【怎么去做】极简三步闭环（约 3 分钟）
          </div>
          <span class="text-[10px] text-emerald-700/80 font-medium">本页出题 → 你去豆包真问 → 你点确认写入</span>
        </div>
        <ol class="list-decimal list-inside space-y-1 text-[11px] text-emerald-900 mt-1.5 leading-relaxed">
          <li><strong>1. 出题</strong>：点下方第 1 步按钮，生成并保存问题清单（8~10 题）；</li>
          <li><strong>2. 真问</strong>：拿着问题清单去豆包网页问一遍，把回答存成结果文件；</li>
          <li><strong>3. 写入</strong>：在第 3 步点「确认写入」——右上角才亮绿色「豆包答案已存进项目」。摸底才算真正完成。</li>
        </ol>
        <p class="text-[10px] text-emerald-800/70 pt-1.5 border-t border-emerald-200/50 mt-1.5">
          分工说明：管理台自己不会登录豆包，需要你把清单拿去问，并在第 3 步确认存入。
        </p>
      </div>
    </div>

    <!-- 动态轮次状态横幅（首轮 vs 再测） -->
    <div
      v-if="modeBanner"
      :class="modeBanner.className"
      v-html="modeBanner.html"
    ></div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  projectData: { type: Object, default: () => ({}) },
  qlistBadge: { type: Object, required: true },
  writeStatusBadge: { type: Object, required: true },
  modeBanner: { type: Object, default: null },
});

defineEmits(['refresh']);

const isSitePending = computed(() => {
  const p = props.projectData || {};
  return p.site_pending === true || p.site_pending === 'true' || p.site_pending === 1;
});
</script>
