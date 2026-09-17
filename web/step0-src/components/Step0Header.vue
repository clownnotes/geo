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

    <div
      v-if="modeBanner"
      :class="modeBanner.className"
      v-html="modeBanner.html"
    ></div>

    <div class="text-[11px] text-slate-600 bg-indigo-50/70 border border-indigo-100 rounded-lg px-3 py-2.5 space-y-1.5">
      <p class="font-semibold text-slate-800">按这个顺序做（新建客户也一样）</p>
      <ol class="list-decimal list-inside space-y-0.5 text-slate-600">
        <li><strong>创建时</strong>：只填品牌、一句话业务，以及客户说过的「会搜什么 / 要对标谁」。这时还<strong>没有</strong>豆包答案。</li>
        <li><strong>第 1 步</strong>：让 Cursor 写出「要问豆包的几句话」，保存成问题清单文件。</li>
        <li><strong>第 2 步</strong>：反重力按清单去豆包真问，把回答存成结果文件。</li>
        <li><strong>第 3 步</strong>：你点「确认写入」——豆包答案才真正存进这个客户项目。之后再出题，才是「再测一遍」。</li>
      </ol>
      <p class="text-slate-500 pt-0.5">谁干什么：Cursor 出题 → 反重力问豆包 → 你点确认存进项目。管理台自己不会登录豆包。</p>
    </div>
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
