<template>
  <!-- 右栏：矩阵分发与 404 存活监测 (384px) -->
  <aside class="w-full lg:w-96 shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 1. 顶部存活指标与批量体检按钮 -->
    <div class="p-3 border-b border-slate-100 bg-slate-50/70 space-y-2.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <i data-lucide="radio" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="font-bold text-slate-800 text-[13px]">矩阵分发与存活监测</span>
        </div>
        <button
          type="button"
          class="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold rounded-lg shadow-xs transition flex items-center gap-1 cursor-pointer"
          :disabled="isCheckingUrls"
          title="一键测试所有已回填外链是否返回 200 正常存活"
          @click="$emit('check-all-urls')"
        >
          <i data-lucide="activity" class="w-3.5 h-3.5" :class="{ 'animate-spin': isCheckingUrls }"></i>
          <span>{{ isCheckingUrls ? '检测中…' : '全网存活体检' }}</span>
        </button>
      </div>

      <!-- 存活指标仪表盘 -->
      <div class="grid grid-cols-3 gap-1.5 text-center text-[10px]">
        <div class="bg-indigo-50/80 border border-indigo-100/80 rounded py-1 px-1">
          <span class="text-indigo-600 block">已回填外链</span>
          <span class="font-bold text-indigo-900">{{ overallStats.filledCount }} / {{ overallStats.totalChannels }}</span>
        </div>
        <div class="bg-emerald-50/80 border border-emerald-100/80 rounded py-1 px-1">
          <span class="text-emerald-600 block">正常存活</span>
          <span class="font-bold text-emerald-800">{{ overallStats.aliveCount }} 条 (200)</span>
        </div>
        <div
          class="border rounded py-1 px-1 transition"
          :class="overallStats.deadCount > 0 ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-slate-50 border-slate-200 text-slate-500'"
        >
          <span class="block">404 失效</span>
          <span class="font-bold">{{ overallStats.deadCount }} 条</span>
        </div>
      </div>
    </div>

    <!-- 2. 分发渠道卡片列表 -->
    <div class="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
      <!-- 必做与加分核心渠道（头条、知乎） -->
      <div
        v-for="ch in coreChannels"
        :key="ch.key"
        class="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-3 space-y-2.5 transition"
        :class="{ 'border-rose-300 ring-1 ring-rose-200 bg-rose-50/20': channelDataMap[ch.key]?.urlStatus === 'dead_404' }"
      >
        <!-- 渠道头部信息 -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-bold text-slate-800">{{ ch.name }}</span>
            <span class="text-[9px] px-1.5 py-0.2 rounded font-semibold border" :class="ch.badgeClass">
              {{ ch.priority === 'must' ? '抓取必做' : '技术加分' }}
            </span>
          </div>
          <span class="text-[10px] text-slate-400 font-mono">{{ ch.targetBot }}</span>
        </div>

        <p class="text-[11px] text-slate-500 leading-normal">
          {{ ch.desc }}
        </p>

        <!-- 一键复制与直达平台 -->
        <div class="grid grid-cols-2 gap-2">
          <button
            type="button"
            class="py-1.5 px-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center justify-center gap-1 cursor-pointer"
            @click="$emit('copy-richtext', ch.key)"
          >
            <i data-lucide="clipboard-copy" class="w-3.5 h-3.5"></i>
            <span>{{ ch.actionText }}</span>
          </button>

          <a
            :href="ch.creatorUrl"
            target="_blank"
            class="py-1.5 px-2 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 transition flex items-center justify-center gap-1"
          >
            <span>{{ ch.linkBtnText }}</span>
            <i data-lucide="external-link" class="w-3 h-3 text-slate-400"></i>
          </a>
        </div>

        <!-- 外链回填与存活探测输入框 -->
        <div class="pt-2 border-t border-slate-100 space-y-1.5">
          <div class="flex items-center justify-between text-[11px]">
            <span class="font-semibold text-slate-700">线上真实外链 (URL 回填)</span>
            <button
              v-if="channelDataMap[ch.key]?.postUrl"
              type="button"
              class="text-indigo-600 hover:underline flex items-center gap-0.5 cursor-pointer text-[10px]"
              @click="$emit('check-url-alive', ch.key)"
            >
              <i data-lucide="refresh-cw" class="w-2.5 h-2.5"></i>
              <span>测存活</span>
            </button>
          </div>

          <div class="flex items-center gap-1.5">
            <input
              :value="channelDataMap[ch.key]?.postUrl || ''"
              type="url"
              placeholder="粘贴发布后的公开文章网址..."
              class="flex-1 min-w-0 px-2.5 py-1 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:bg-white focus:border-[#7c5bf5] focus:outline-none"
              @change="$emit('save-channel-url', ch.key, $event.target.value)"
            />
          </div>

          <!-- 存活检测状态提示 -->
          <div class="flex items-center justify-between text-[10px] pt-0.5">
            <div class="flex items-center gap-1">
              <span
                v-if="channelDataMap[ch.key]?.urlStatus === 'active_200'"
                class="text-emerald-700 font-semibold flex items-center gap-1"
              >
                <i data-lucide="check-circle" class="w-3 h-3 text-emerald-600"></i>
                正常存活 (HTTP 200)
              </span>
              <span
                v-else-if="channelDataMap[ch.key]?.urlStatus === 'dead_404'"
                class="text-rose-700 font-bold flex items-center gap-1"
              >
                <i data-lucide="alert-octagon" class="w-3 h-3 text-rose-600"></i>
                已下架失效 (HTTP 404)
              </span>
              <span
                v-else-if="channelDataMap[ch.key]?.urlStatus === 'checking'"
                class="text-indigo-600 flex items-center gap-1"
              >
                <i data-lucide="loader" class="w-3 h-3 animate-spin"></i>
                探测中…
              </span>
              <span v-else class="text-slate-400">
                尚未检测
              </span>
            </div>

            <!-- 404 联动重发入口 -->
            <button
              v-if="channelDataMap[ch.key]?.urlStatus === 'dead_404' && activeTopic"
              type="button"
              class="text-rose-700 hover:text-rose-900 font-bold underline cursor-pointer"
              @click="$emit('regenerate-topic', activeTopic.id)"
            >
              一键改动重发
            </button>
          </div>
        </div>
      </div>

      <!-- 拓展生态折叠抽屉（微信/百家号） -->
      <details class="rounded-xl border border-slate-200 bg-white group">
        <summary class="cursor-pointer px-3.5 py-2.5 text-xs font-semibold text-slate-700 flex items-center justify-between select-none">
          <div class="flex items-center gap-1.5">
            <i data-lucide="layout-grid" class="w-3.5 h-3.5 text-slate-500"></i>
            <span>拓展生态渠道（微信公众号 / 百家号）</span>
          </div>
          <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 group-open:rotate-180 transition-transform"></i>
        </summary>

        <div class="p-3 border-t border-slate-100 space-y-3">
          <div
            v-for="ch in optionalChannels"
            :key="ch.key"
            class="p-2.5 rounded-lg border border-slate-200/80 bg-slate-50/60 space-y-2 text-xs"
          >
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-800">{{ ch.name }}</span>
              <span class="text-[10px] text-slate-400 font-mono">{{ ch.targetBot }}</span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <button
                type="button"
                class="py-1 px-2 bg-slate-800 hover:bg-slate-700 text-white text-[11px] font-medium rounded-lg transition"
                @click="$emit('copy-richtext', ch.key)"
              >
                {{ ch.actionText }}
              </button>
              <a
                :href="ch.creatorUrl"
                target="_blank"
                class="py-1 px-2 bg-white text-slate-700 text-[11px] font-medium rounded-lg border border-slate-200 text-center"
              >
                直达后台
              </a>
            </div>
          </div>
        </div>
      </details>
    </div>

    <!-- 3. 底部发稿 SOP 派单卡一键复制 -->
    <div class="p-3 border-t border-slate-100 bg-slate-50/80 flex items-center justify-between text-xs">
      <div class="flex items-center gap-1.5 text-slate-500 text-[11px]">
        <i data-lucide="clipboard-list" class="w-3.5 h-3.5 text-slate-400"></i>
        <span>交付台账与派单卡</span>
      </div>
      <button
        type="button"
        class="text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer text-[11px] flex items-center gap-1"
        @click="$emit('copy-richtext', 'toutiao')"
      >
        <i data-lucide="copy" class="w-3 h-3"></i>
        <span>复制派单文案</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  channels: { type: Array, default: () => [] },
  channelDataMap: { type: Object, default: () => ({}) },
  overallStats: {
    type: Object,
    default: () => ({
      totalChannels: 0,
      filledCount: 0,
      aliveCount: 0,
      deadCount: 0,
      aliveRate: 0,
    }),
  },
  isCheckingUrls: { type: Boolean, default: false },
  activeTopic: { type: Object, default: null },
});

defineEmits([
  'copy-richtext',
  'save-channel-url',
  'check-url-alive',
  'check-all-urls',
  'regenerate-topic',
]);

const coreChannels = computed(() => {
  return props.channels.filter(c => c.priority === 'must' || c.priority === 'plus');
});

const optionalChannels = computed(() => {
  return props.channels.filter(c => c.priority === 'optional');
});
</script>
