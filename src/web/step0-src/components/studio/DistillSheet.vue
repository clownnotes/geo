<template>
  <!-- [2026-09-30] [盖板工作台] 阶段二素材采集与智能蒸馏沉浸式全屏盖板组件 (师弟定规) -->
  <div class="flex-1 min-h-0 bg-white flex flex-col overflow-hidden relative select-none">
    <!-- ===== 1. 盖板顶栏 ===== -->
    <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3 shrink-0">
      <div class="flex items-center gap-2.5">
        <span class="p-1.5 rounded-lg bg-[#7c5bf5]/10 text-[#7c5bf5]">
          <i :data-lucide="currentMode === 'web' ? 'globe' : 'file-text'" class="w-4 h-4"></i>
        </span>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="font-bold text-slate-800 text-sm">素材采集与智能蒸馏大工作台</h3>
            <span class="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#7c5bf5]/15 text-[#7c5bf5] border border-[#7c5bf5]/30 font-bold">
              {{ currentMode === 'web' ? '网页蒸馏模式' : '文案蒸馏模式' }}
            </span>
          </div>
          <p class="text-[11px] text-slate-500">
            提取、删减与人工润色后，一键蒸馏切块；逐条核验后点击【确认加入该分类】，确认一条入库一条。
          </p>
        </div>
      </div>

      <!-- 右侧：模式快速切换与退出盖板按钮 -->
      <div class="flex items-center gap-2 shrink-0">
        <div class="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100 text-xs">
          <button
            type="button"
            class="px-2.5 py-1 rounded font-medium transition cursor-pointer flex items-center gap-1"
            :class="currentMode === 'web' ? 'bg-white text-[#7c5bf5] shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'"
            @click="currentMode = 'web'"
          >
            <i data-lucide="globe" class="w-3.5 h-3.5"></i>
            <span>网页蒸馏</span>
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded font-medium transition cursor-pointer flex items-center gap-1"
            :class="currentMode === 'text' ? 'bg-white text-[#7c5bf5] shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'"
            @click="currentMode = 'text'"
          >
            <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
            <span>文案蒸馏</span>
          </button>
        </div>

        <button
          type="button"
          class="px-3.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          title="退出盖板返回原素材库文件视图"
          @click="handleClose"
        >
          <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
          <span>退出盖板</span>
        </button>
      </div>
    </div>

    <!-- ===== 2. 盖板主体左右双栏流转区 ===== -->
    <div class="flex-1 min-h-0 flex flex-col md:flex-row overflow-hidden divide-y md:divide-y-0 md:divide-x divide-slate-200">
      <!-- 左栏：抓取/粘贴与人工初审润色大写字板 (50%) -->
      <div class="flex-1 min-w-0 p-4 flex flex-col bg-slate-50/50 space-y-3 overflow-y-auto">
        <!-- 网页蒸馏模式专有：网址输入框 -->
        <div v-if="currentMode === 'web'" class="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs space-y-2">
          <label class="block text-xs font-bold text-slate-700">
            客户官网 / 微信公众号 / 展示页网址
          </label>
          <div class="flex items-center gap-2">
            <input
              v-model="inputUrl"
              type="text"
              placeholder="输入客户官网或宣传展示链接 (如 https://www.example.com)..."
              class="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:border-[#7c5bf5] outline-none"
              @keyup.enter="handleScrape"
            />
            <button
              type="button"
              :disabled="isScraping || !inputUrl.trim()"
              class="px-3.5 py-1.5 bg-[#7c5bf5] hover:bg-[#6846e3] disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shrink-0"
              @click="handleScrape"
            >
              <i data-lucide="download-cloud" class="w-3.5 h-3.5" :class="isScraping ? 'animate-spin' : ''"></i>
              <span>{{ isScraping ? '正在抓取…' : '抓取官网骨架' }}</span>
            </button>
          </div>
        </div>

        <!-- 大写字板与人工初审修改区 -->
        <div class="flex-1 min-h-[260px] bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs flex flex-col space-y-2">
          <div class="flex items-center justify-between pb-1 text-xs">
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-slate-800">
                {{ currentMode === 'web' ? '抓取正文清洗与润色' : '原始文案粘贴与修饰' }}
              </span>
              <span class="text-[11px] text-slate-400">（在此删改错字、剔除废话）</span>
            </div>
            <!-- 字数与 8500 汉字安全线 -->
            <span
              class="font-mono px-2 py-0.5 rounded text-[11px] font-medium"
              :class="isOverLimit ? 'bg-amber-100 text-amber-700 font-bold border border-amber-300' : 'bg-slate-100 text-slate-600'"
            >
              {{ draftText.length }} / 8500 汉字
            </span>
          </div>

          <textarea
            v-model="draftText"
            placeholder="在此直接粘贴文字或修改上方抓取的正文内容。字数控制在 8500 字以内，完成后点击下方【一键蒸馏与智能分类 →】..."
            class="flex-1 w-full p-3 font-mono text-xs text-slate-800 rounded-lg border border-slate-200 focus:border-[#7c5bf5] focus:ring-1 focus:ring-[#7c5bf5] outline-none resize-none leading-relaxed overflow-y-auto"
          ></textarea>

          <!-- 底部动作条 -->
          <div class="flex items-center justify-between pt-1">
            <button
              v-if="draftText"
              type="button"
              class="text-slate-400 hover:text-red-600 cursor-pointer text-xs"
              @click="draftText = ''"
            >
              清空文字稿
            </button>
            <span v-else></span>

            <button
              type="button"
              :disabled="isDistilling || !draftText.trim() || isOverLimit"
              class="px-4 py-2 bg-[#7c5bf5] hover:bg-[#6846e3] disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
              @click="handleStartDistill"
            >
              <i data-lucide="sparkles" class="w-3.5 h-3.5" :class="isDistilling ? 'animate-spin' : ''"></i>
              <span>{{ isDistilling ? '正在智能蒸馏拆分…' : '一键蒸馏与智能分类 →' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 右栏：蒸馏切块结果与逐条确认流水席 (50%) -->
      <div class="flex-1 min-w-0 p-4 flex flex-col bg-white overflow-y-auto space-y-3">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100 shrink-0">
          <div class="flex items-center gap-2">
            <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
              <i data-lucide="layers" class="w-4 h-4"></i>
            </span>
            <span class="font-bold text-slate-800 text-xs">
              AI 智能蒸馏切片列表 (共 {{ chunks.length }} 个片段)
            </span>
          </div>
          <span class="text-[11px] text-slate-400">确认一条加入一条，即点即入库</span>
        </div>

        <!-- 空态引导 -->
        <div
          v-if="chunks.length === 0"
          class="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-2 border-2 border-dashed border-slate-200 rounded-xl"
        >
          <i data-lucide="sparkles" class="w-8 h-8 text-slate-300"></i>
          <p class="text-xs font-medium text-slate-500">尚无蒸馏切片</p>
          <p class="text-[11px] text-slate-400 max-w-xs">
            请在左侧输入网址抓取或粘贴文案后，点击【一键蒸馏与智能分类 →】，系统将自动为您提取 6 大分类素材。
          </p>
        </div>

        <!-- 切片卡片流水席 -->
        <div v-else class="space-y-3">
          <div
            v-for="(chunk, idx) in chunks"
            :key="chunk.chunkId"
            class="p-3.5 rounded-xl border transition shadow-2xs space-y-2.5"
            :class="chunk.isAdopted ? 'border-emerald-200 bg-emerald-50/40' : 'border-slate-200 bg-white'"
          >
            <!-- 卡片头部：分类与动作 -->
            <div class="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
              <div class="flex items-center gap-2">
                <span class="font-bold text-slate-700">片段 #{{ idx + 1 }}</span>
                <!-- 目标分类下拉纠偏 -->
                <select
                  v-model="chunk.targetCategory"
                  :disabled="chunk.isAdopted"
                  class="text-xs px-2 py-0.5 rounded bg-slate-100 border border-slate-200 font-bold text-[#7c5bf5] outline-none disabled:opacity-60"
                >
                  <option value="S1">S1 · 主体与法定边界</option>
                  <option value="S2">S2 · 产品与价格标准</option>
                  <option value="S3">S3 · 客户画像与痛点场景</option>
                  <option value="S4">S4 · 同行策略与参数对比</option>
                  <option value="S5">S5 · 真实故事化案例库</option>
                  <option value="S6">S6 · 权威凭据与背书</option>
                </select>
                <span class="text-[11px] text-slate-400">({{ chunk.content.length }} 汉字)</span>
              </div>

              <!-- 右侧按钮：丢弃 / 确认入库 -->
              <div class="flex items-center gap-1.5">
                <button
                  v-if="!chunk.isAdopted"
                  type="button"
                  class="p-1 text-slate-400 hover:text-red-600 rounded transition cursor-pointer"
                  title="丢弃此片段"
                  @click="handleDiscardChunk(idx)"
                >
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>

                <!-- 已入库徽章 -->
                <span
                  v-if="chunk.isAdopted"
                  class="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full flex items-center gap-1"
                >
                  <i data-lucide="check" class="w-3 h-3"></i>
                  <span>已入库 ({{ chunk.adoptedFileName || '增补分片' }})</span>
                </span>

                <!-- 确认加入按钮 -->
                <button
                  v-else
                  type="button"
                  class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition shadow-2xs cursor-pointer"
                  @click="handleAdoptSingleChunk(chunk)"
                >
                  <i data-lucide="check" class="w-3.5 h-3.5"></i>
                  <span>确认加入该分类</span>
                </button>
              </div>
            </div>

            <!-- 切片文本编辑框 (纯新增内容，行内打字润色) -->
            <textarea
              v-model="chunk.content"
              :disabled="chunk.isAdopted"
              rows="3"
              class="w-full p-2.5 font-mono text-xs text-slate-800 bg-slate-50/70 rounded-lg border border-slate-200 focus:border-[#7c5bf5] focus:bg-white outline-none resize-none leading-relaxed disabled:opacity-75"
              placeholder="在此微调或增减该片段内容..."
            ></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import { semanticChunkRawMaterial, CATEGORY_DIR_MAP } from '../../stage2Config.js';
import { computeStage2ChunkVersion, normalizeOfficialUrl } from '../../config/studioArtifactConfig.js';

const props = defineProps({
  mode: { type: String, default: 'web' },
  initialUrl: { type: String, default: '' },
  initialText: { type: String, default: '' },
  files: { type: Object, required: true },
  clientId: { type: String, default: 'geo' },
  brand: { type: String, default: '邻里GEO' },
  city: { type: String, default: '徐州' },
  category: { type: String, default: 'GEO 优化' },
  competitor: { type: String, default: '优搜网络' },
});

const emit = defineEmits(['close', 'adopt-chunk', 'toast', 'update:draftText']);

const currentMode = ref(props.mode);
const inputUrl = ref(normalizeOfficialUrl(props.initialUrl || ''));
const draftText = ref(props.initialText || '');
const isScraping = ref(false);
const isDistilling = ref(false);
const chunks = ref([]);

const isOverLimit = computed(() => draftText.value.length > 8500);

// [2026-09-30] 双向草稿同步守卫：父子组件双向同步，避免草稿丢失 (解决 🟡3)
watch(
  () => props.initialText,
  (val) => {
    if (!draftText.value && val) {
      draftText.value = val;
    }
  }
);

watch(
  () => props.initialUrl,
  (val) => {
    if (val) {
      inputUrl.value = normalizeOfficialUrl(val);
    }
  }
);

watch(draftText, (newVal) => {
  emit('update:draftText', newVal);
});

function handleClose() {
  emit('update:draftText', draftText.value);
  emit('close');
}

// 抓取官网核心骨架 (对接真实服务器证据库 API，坚决禁止塞入假数据)
async function handleScrape() {
  const cleanUrl = normalizeOfficialUrl(inputUrl.value);
  if (!cleanUrl) {
    emit('toast', { message: '请输入合法的企业官网或展示页网址！', type: 'warning' });
    return;
  }
  inputUrl.value = cleanUrl;
  isScraping.value = true;
  emit('toast', { message: '正在连接服务器抓取官网纯净骨架…', type: 'info' });
  try {
    const token = typeof window !== 'undefined' ? window.currentAuthToken || '' : '';
    const pid = props.clientId || (typeof window !== 'undefined' ? window.currentProjectId || 'nextgeo' : 'nextgeo');
    const probeApi = `/api/projects/${encodeURIComponent(pid)}/ingest/url`;
    const resp = await fetch(probeApi, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ url: cleanUrl }),
    });
    const data = await resp.json();
    if (data && data.success && data.content) {
      draftText.value = data.content.slice(0, 8500);
      emit('update:draftText', draftText.value);
      emit('toast', { message: `官网骨架提取成功（已抓取 ${data.crawled_words || draftText.value.length} 字），已填入写字板！`, type: 'success' });
      refreshIcons();
      return;
    } else {
      const errMsg = data?.message || '服务器抓取未返回有效正文';
      console.warn('[DistillSheet] 抓取未成功:', errMsg);
      emit('toast', { message: `官网抓取未成功 (${errMsg})，请检查网址或在此直接粘贴文字稿`, type: 'warning' });
    }
  } catch (e) {
    console.error('[DistillSheet] 抓取接口异常:', e);
    emit('toast', { message: '网络请求异常，无法连接抓取服务，您可在此直接粘贴文字稿', type: 'error' });
  } finally {
    isScraping.value = false;
    refreshIcons();
  }
}

// 一键智能蒸馏切块
function handleStartDistill() {
  if (!draftText.value.trim() || isOverLimit.value) return;
  isDistilling.value = true;
  try {
    const ctx = {
      company: props.brand,
      brand: props.brand,
      city: props.city,
      category: props.category,
      competitor: props.competitor,
    };
    const rawChunks = semanticChunkRawMaterial(draftText.value, ctx);
    chunks.value = rawChunks.map((c) => ({
      chunkId: c.chunkId || `chunk_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      targetCategory: c.targetCategory || 'S1',
      content: c.content || '',
      isAdopted: false,
      adoptedFileName: '',
    }));
    emit('toast', { message: `智能蒸馏完成！成功提取出 ${chunks.value.length} 个分类素材片段`, type: 'success' });
  } catch (err) {
    console.error('[DistillSheet] 蒸馏异常:', err);
    emit('toast', { message: '蒸馏切块失败，请检查输入文字', type: 'error' });
  } finally {
    isDistilling.value = false;
    refreshIcons();
  }
}

// 丢弃单个切片
function handleDiscardChunk(idx) {
  chunks.value.splice(idx, 1);
  emit('toast', { message: '已丢弃该素材片段', type: 'info' });
}

// 确认加入该分类 (即点即入库 · 1.x 纯新增)
function handleAdoptSingleChunk(chunk) {
  // [2026-09-30] [阶段二盖板蒸馏] 切片空内容守卫，防止写入空增量文件
  if (!chunk.content || !chunk.content.trim()) {
    emit('toast', { message: '切片内容不能为空，请输入或补充文字后再确认！', type: 'warning' });
    return;
  }

  const cat = chunk.targetCategory || 'S1';
  const slotKey = `slot_stage2_${cat.toLowerCase()}`;
  
  // [2026-09-30] 防并发版本碰撞守卫 (解决 🔴4)：
  // 将本组件当前已经采纳但父级尚未完成回灌的切片纳入计算，确保多次连续点击单调递增
  const mergedFiles = { ...props.files };
  for (const c of chunks.value) {
    if (c.isAdopted && c.adoptedFileName) {
      mergedFiles[c.adoptedFileName] = {
        name: c.adoptedFileName,
        slotKey: `slot_stage2_${(c.targetCategory || 'S1').toLowerCase()}`,
      };
    }
  }

  const versionInfo = computeStage2ChunkVersion(mergedFiles, slotKey);
  if (!versionInfo) {
    emit('toast', { message: `未找到槽位 [${slotKey}]`, type: 'error' });
    return;
  }

  const newFile = {
    name: versionInfo.nextFileName,
    slotKey: versionInfo.slotKey,
    category: versionInfo.category,
    dir: CATEGORY_DIR_MAP[versionInfo.category] || `分类 ${cat.slice(1)}`,
    content: chunk.content.trim(),
    savedContent: chunk.content.trim(),
    isDirty: false,
    isActive: false,
    isRetired: false,
    isCanonicalMirror: false,
    versionTag: versionInfo.nextVersionTag,
    isBranchDraft: true,
    isDeleted: false,
    isProtectedArchive: false,
    generatedAt: new Date().toISOString(),
  };

  chunk.isAdopted = true;
  chunk.adoptedFileName = versionInfo.nextFileName;

  emit('adopt-chunk', {
    chunk,
    targetSlotKey: slotKey,
    newFile,
  });

  emit('toast', {
    message: `已成功将素材加入 ${cat} (生成增补分片【${versionInfo.nextFileName}】)`,
    type: 'success',
  });
  refreshIcons();
}

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

onMounted(() => {
  refreshIcons();
  // 若传入了初始网址且正文为空，自动触发一次抓取
  if (props.mode === 'web' && props.initialUrl && !props.initialText) {
    handleScrape();
  }
});

watch([currentMode, chunks], () => {
  refreshIcons();
}, { deep: true });
</script>
