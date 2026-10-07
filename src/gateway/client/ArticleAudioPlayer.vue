<template>
  <div
    class="geo-audio-player-card bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm transition-all hover:border-slate-300"
    data-crawler-ignore="true"
    role="region"
    aria-label="文章智能伴读"
  >
    <!-- 顶部状态栏与音色选择 -->
    <div class="flex items-center justify-between gap-3 pb-3 border-b border-slate-100">
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-[#7c5bf5] border border-purple-100">
          AI 语音伴读
        </span>
        <span v-if="cacheHit" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-normal bg-emerald-50 text-emerald-600 border border-emerald-100">
          本地缓存命中
        </span>
        <span class="text-xs text-slate-400">
          第 {{ currentChunkIndex + 1 }} / {{ totalChunks || 1 }} 段
        </span>
      </div>

      <!-- 音色下拉切换 -->
      <div class="flex items-center gap-2">
        <label for="voice-select" class="text-xs text-slate-500 font-medium hidden sm:inline-block">播报音色</label>
        <select
          id="voice-select"
          v-model="selectedVoice"
          @change="handleVoiceChange"
          class="text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-[#7c5bf5] focus:border-[#7c5bf5]"
        >
          <option v-for="voice in voices" :key="voice.voice_alias" :value="voice.voice_alias">
            {{ voice.name }} ({{ voice.scenario || voice.gender }})
          </option>
        </select>
      </div>
    </div>

    <!-- 中间：当前播报片段文字呈现 -->
    <div class="py-2.5 min-h-[48px] flex items-center">
      <p class="text-xs text-slate-600 leading-relaxed line-clamp-2 select-none">
        <span v-if="currentChunkText" class="text-slate-800 font-normal">
          "{{ currentChunkText }}"
        </span>
        <span v-else class="text-slate-400 italic">
          点击播放按钮即可开始智能朗读当前文章...
        </span>
      </p>
    </div>

    <!-- 底部控制栏 -->
    <div class="flex items-center justify-between gap-4 pt-2">
      <!-- 播放 / 暂停 / 重试主按钮 -->
      <div class="flex items-center gap-3">
        <button
          type="button"
          @click="togglePlay"
          :disabled="totalChunks === 0"
          class="w-9 h-9 rounded-full bg-[#7c5bf5] text-white flex items-center justify-center hover:bg-[#6b4ae6] active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          :title="playerState === 'playing' ? '暂停' : '播放'"
        >
          <!-- 加载中 Spinner -->
          <svg v-if="playerState === 'loading'" class="animate-spin w-4 h-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <!-- 暂停图标 -->
          <svg v-else-if="playerState === 'playing'" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
          </svg>
          <!-- 播放图标 -->
          <svg v-else class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>

        <!-- 停止按钮 -->
        <button
          type="button"
          @click="stop"
          :disabled="playerState === 'idle'"
          class="text-xs text-slate-500 hover:text-slate-800 disabled:opacity-40 transition-colors"
          title="停止并重置"
        >
          停止
        </button>
      </div>

      <!-- 进度条与百分比 -->
      <div class="flex-1 flex items-center gap-3">
        <div class="relative w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            class="absolute left-0 top-0 h-full bg-[#7c5bf5] transition-all duration-300"
            :style="{ width: `${progressPercent}%` }"
          ></div>
        </div>
        <span class="text-xs font-mono text-slate-400 w-9 text-right">{{ progressPercent }}%</span>
      </div>

      <!-- 倍速控制 -->
      <div class="flex items-center gap-1 border-l border-slate-200 pl-3">
        <button
          v-for="s in [1.0, 1.25, 1.5]"
          :key="s"
          type="button"
          @click="setSpeed(s)"
          class="px-2 py-0.5 text-xs rounded transition-colors"
          :class="speed === s ? 'bg-purple-100 text-[#7c5bf5] font-semibold' : 'text-slate-500 hover:text-slate-800'"
        >
          {{ s }}x
        </button>
      </div>
    </div>

    <!-- 错误横幅提示 -->
    <div v-if="errorMessage" class="mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800 flex items-center justify-between">
      <span>{{ errorMessage }}</span>
      <button @click="errorMessage = ''" class="text-amber-600 hover:text-amber-900 ml-2 font-bold">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { NextdoorVoiceClient } from './voiceClient';
import { ArticleAudioPlayer } from './ArticleAudioPlayer';
import { PlayerState, SemanticVoiceItem } from './voiceTypes';

const props = withDefaults(
  defineProps<{
    /** 待朗读的文章全文 Markdown 或纯文本 */
    articleText: string;
    /** 网关 Base URL (默认同源网关或 http://127.0.0.1:8090) */
    gatewayBaseUrl?: string;
    /** 默认音色别名 */
    defaultVoice?: string;
  }>(),
  {
    gatewayBaseUrl: 'http://127.0.0.1:8090',
    defaultVoice: 'standard_female_warm'
  }
);

const emit = defineEmits<{
  (e: 'chunkChange', index: number, total: number, text: string): void;
  (e: 'stateChange', state: PlayerState): void;
}>();

// 核心实例与响应式状态
let player: ArticleAudioPlayer | null = null;
const client = new NextdoorVoiceClient({ baseURL: props.gatewayBaseUrl });

const playerState = ref<PlayerState>('idle');
const currentChunkIndex = ref(0);
const totalChunks = ref(0);
const currentChunkText = ref('');
const progressPercent = ref(0);
const speed = ref(1.0);
const selectedVoice = ref(props.defaultVoice);
const cacheHit = ref(false);
const errorMessage = ref('');

// 音色列表 (预置标准兜底，并在挂载时拉取服务端开放音色)
const voices = ref<SemanticVoiceItem[]>([
  {
    voice_alias: 'standard_female_warm',
    name: '温婉知性 · 佳悦',
    gender: 'female',
    locale: 'zh-CN',
    scenario: '博客伴读'
  },
  {
    voice_alias: 'standard_male_magnetic',
    name: '磁性沉稳 · 晨阳',
    gender: 'male',
    locale: 'zh-CN',
    scenario: '深度解说'
  },
  {
    voice_alias: 'standard_female_news',
    name: '专业播报 · 晓涵',
    gender: 'female',
    locale: 'zh-CN',
    scenario: '资讯新闻'
  }
]);

const initPlayer = () => {
  if (player) {
    player.destroy();
  }

  player = new ArticleAudioPlayer({
    client,
    defaultVoiceAlias: selectedVoice.value,
    defaultSpeed: speed.value,
    enableCache: true,
    onStateChange: (st) => {
      playerState.value = st;
      emit('stateChange', st);
    },
    onProgress: (_cur, _total, pct) => {
      progressPercent.value = pct;
    },
    onChunkStart: (idx, total, text) => {
      currentChunkIndex.value = idx;
      totalChunks.value = total;
      currentChunkText.value = text;
      emit('chunkChange', idx, total, text);
    },
    onError: (err) => {
      errorMessage.value = err.message;
    }
  });

  if (props.articleText) {
    player.loadArticle(props.articleText);
    const info = player.getInfo();
    totalChunks.value = info.totalChunks;
  }
};

const togglePlay = () => {
  errorMessage.value = '';
  player?.togglePlay();
};

const stop = () => {
  player?.stop();
  currentChunkIndex.value = 0;
  progressPercent.value = 0;
  currentChunkText.value = '';
};

const setSpeed = (s: number) => {
  speed.value = s;
  player?.setSpeed(s);
};

const handleVoiceChange = () => {
  player?.setVoice(selectedVoice.value);
};

// 监听文章内容变更，重新切片
watch(
  () => props.articleText,
  (newText) => {
    if (player && newText) {
      player.loadArticle(newText);
      const info = player.getInfo();
      totalChunks.value = info.totalChunks;
    }
  }
);

onMounted(async () => {
  initPlayer();

  // 异步加载开放平台最新的标准音色列表
  try {
    const remoteVoices = await client.getVoices();
    if (remoteVoices && remoteVoices.length > 0) {
      voices.value = remoteVoices;
    }
  } catch {
    // 降级使用内置预设
  }
});

onUnmounted(() => {
  player?.destroy();
});
</script>

<style scoped>
.geo-audio-player-card {
  --geo-primary: #7c5bf5;
}
</style>
