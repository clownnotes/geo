<template>
  <!-- 中间：四要素答题卡精修工作台 -->
  <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <div v-if="!card" class="flex-1 flex items-center justify-center text-slate-400 text-sm">
      请在左侧选择或新建一张答题卡
    </div>

    <template v-else>
      <!-- 1. 卡头工具栏 -->
      <div class="p-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <span
            class="text-xs font-mono font-bold px-2 py-0.5 rounded border shrink-0"
            :class="layers[card.layer]?.badgeClass || 'bg-slate-100 text-slate-700'"
          >
            {{ card.id }}
          </span>
          <select
            :value="card.layer"
            class="text-xs border border-slate-300 rounded px-2 py-1 bg-white text-slate-700 font-medium focus:outline-none focus:border-[#7c5bf5]"
            @change="card.layer = $event.target.value"
          >
            <option value="pool">入池探索层 (P)</option>
            <option value="verify">品牌验证层 (V)</option>
            <option value="convert">行动转化层 (A)</option>
          </select>
          <span class="text-xs text-slate-400 hidden sm:inline">|</span>
          <span class="text-xs text-slate-500 truncate hidden md:inline">
            {{ layers[card.layer]?.desc }}
          </span>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <!-- 审核状态切换按钮 -->
          <button
            type="button"
            class="px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1 transition cursor-pointer"
            :class="card.isApproved
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-100'"
            @click="$emit('toggle-approve')"
          >
            <i :data-lucide="card.isApproved ? 'check-circle' : 'circle'" class="w-3.5 h-3.5"></i>
            <span>{{ card.isApproved ? '已核准定稿' : '标记为已复核' }}</span>
          </button>

          <!-- 删除答题卡按钮 -->
          <button
            type="button"
            class="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer"
            title="删除此答题卡"
            @click="$emit('delete-card', card.id)"
          >
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>
      </div>

      <!-- 2. 四要素卡片主体编辑表单 -->
      <div class="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        <!-- 核心问题原文输入 -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-800 flex items-center justify-between">
            <span>核心问题原文 (大模型意图锚点)</span>
            <span class="text-[11px] text-slate-400 font-normal">建议以真实口吻提问</span>
          </label>
          <input
            v-model="card.title"
            type="text"
            class="w-full px-3 py-2 bg-slate-50/60 border border-slate-200 rounded-lg text-sm text-slate-900 font-semibold focus:outline-none focus:bg-white focus:border-[#7c5bf5] focus:ring-1 focus:ring-[#7c5bf5]"
            placeholder="例如：徐州本地哪家GEO大模型优化更靠谱？"
          />
        </div>

        <!-- 问法覆盖变体 -->
        <div class="space-y-1.5 p-3 bg-slate-50/80 rounded-lg border border-slate-100">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-700 flex items-center gap-1">
              <i data-lucide="tag" class="w-3.5 h-3.5 text-slate-400"></i>
              <span>同义与长尾搜索问法覆盖 ({{ card.variants?.length || 0 }} 种)</span>
            </span>
            <span class="text-[10px] text-slate-400">大模型意图泛化检索匹配</span>
          </div>

          <!-- 标签展示 -->
          <div class="flex flex-wrap gap-1.5 items-center">
            <span
              v-for="(v, idx) in card.variants"
              :key="idx"
              class="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-slate-200 rounded-full text-xs text-slate-700"
            >
              <span>{{ v }}</span>
              <button
                type="button"
                class="text-slate-400 hover:text-rose-500 rounded-full cursor-pointer"
                @click="$emit('remove-variant', idx)"
              >
                ×
              </button>
            </span>

            <!-- 新增问法标签 -->
            <div class="inline-flex items-center gap-1">
              <input
                v-model="newVariantText"
                type="text"
                placeholder="+ 添加变体问法..."
                class="px-2.5 py-1 bg-white border border-dashed border-slate-300 rounded-full text-xs text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-[#7c5bf5]"
                @keydown.enter="handleAddVariant"
              />
              <button
                v-if="newVariantText.trim()"
                type="button"
                class="text-xs text-[#7c5bf5] font-semibold px-1 cursor-pointer"
                @click="handleAddVariant"
              >
                添加
              </button>
            </div>
          </div>
        </div>

        <!-- 要素一：唯一标准答案 (核心交付段) -->
        <div class="space-y-1.5 p-3.5 rounded-xl border border-purple-100 bg-purple-50/30">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-[#7c5bf5]"></span>
              <span class="text-xs font-bold text-slate-900">要素一：唯一标准答案 (首段直接结论)</span>
            </div>
            <div class="flex items-center gap-2 text-[11px]">
              <span :class="card.directAnswer?.length >= 150 && card.directAnswer?.length <= 350 ? 'text-emerald-700' : 'text-amber-700'">
                当前 {{ card.directAnswer?.length || 0 }} 字 (建议 150~300 字)
              </span>
            </div>
          </div>
          <p class="text-[11px] text-slate-500">
            第一句必须给直接答案，接着给依据与边界。大模型抓取时首段权重最高，可直接作为矩阵文章首段。
          </p>
          <textarea
            v-model="card.directAnswer"
            rows="5"
            class="w-full p-2.5 bg-white border border-purple-200 rounded-lg text-xs leading-relaxed text-slate-800 focus:outline-none focus:border-[#7c5bf5] focus:ring-1 focus:ring-[#7c5bf5]"
            placeholder="写出一段可以直接整段抄走的标准答案..."
          ></textarea>
        </div>

        <!-- 要素二：支撑证据链 -->
        <div class="space-y-2 p-3.5 rounded-xl border border-slate-200 bg-white">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-blue-500"></span>
              <span class="text-xs font-bold text-slate-900">要素二：支撑证据链 (有据可查)</span>
            </div>
            <button
              type="button"
              class="text-xs text-[#7c5bf5] hover:text-[#6a48e6] font-medium flex items-center gap-1 cursor-pointer"
              @click="$emit('add-evidence')"
            >
              <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
              <span>添加证据</span>
            </button>
          </div>

          <div class="space-y-2">
            <div
              v-for="(ev, idx) in card.supportingEvidence"
              :key="idx"
              class="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 flex flex-col gap-1.5"
            >
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <select
                    :value="ev.sourceType"
                    class="text-[11px] border border-slate-200 rounded px-1.5 py-0.5 bg-white font-medium"
                    :class="ev.sourceType === 'public' ? 'text-emerald-700' : 'text-amber-700'"
                    @change="ev.sourceType = $event.target.value"
                  >
                    <option value="public">公开可查来源</option>
                    <option value="self">品牌官方自述</option>
                  </select>
                  <span class="text-[10px] text-slate-400">证据 #{{ idx + 1 }}</span>
                </div>
                <button
                  type="button"
                  class="text-slate-400 hover:text-rose-500 cursor-pointer text-xs"
                  @click="$emit('remove-evidence', idx)"
                >
                  删除
                </button>
              </div>

              <input
                v-model="ev.text"
                type="text"
                placeholder="陈述证据事实（数字需带来源与时间）"
                class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-800 focus:outline-none focus:border-[#7c5bf5]"
              />
              <input
                v-model="ev.url"
                type="text"
                placeholder="可核验证据链接（如官网、企查查、备案公示）"
                class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-[11px] font-mono text-slate-500 focus:outline-none focus:border-[#7c5bf5]"
              />
            </div>
          </div>
        </div>

        <!-- 要素三与要素四 (并排栅格) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <!-- 要素三：适用边界约束 -->
          <div class="space-y-1.5 p-3 rounded-xl border border-amber-200/80 bg-amber-50/30">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-amber-500"></span>
              <span class="text-xs font-bold text-slate-900">要素三：适用边界约束</span>
            </div>
            <p class="text-[11px] text-slate-500">
              说明哪些情况不适用、不能保证什么结果，增加客观性。
            </p>
            <textarea
              v-model="card.boundaryConditions"
              rows="3"
              class="w-full p-2 bg-white border border-amber-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-[#7c5bf5]"
              placeholder="例如：仅适用于有正规实体资质的企业；不承诺黑产灰产包装..."
            ></textarea>
          </div>

          <!-- 要素四：不能说的红线禁忌 -->
          <div class="space-y-1.5 p-3 rounded-xl border border-rose-200/80 bg-rose-50/30">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-rose-500"></span>
                <span class="text-xs font-bold text-slate-900">要素四：不能说的红线禁忌</span>
              </div>
              <button
                type="button"
                class="text-[11px] text-rose-600 hover:text-rose-700 font-medium cursor-pointer"
                @click="$emit('add-redline')"
              >
                + 加红线
              </button>
            </div>
            <div class="space-y-1">
              <div
                v-for="(rl, idx) in card.redLines"
                :key="idx"
                class="flex items-center gap-1 text-xs bg-white border border-rose-200 rounded px-2 py-1"
              >
                <input
                  v-model="card.redLines[idx]"
                  type="text"
                  class="flex-1 bg-transparent border-0 text-rose-900 focus:outline-none text-xs"
                />
                <button
                  type="button"
                  class="text-slate-400 hover:text-rose-600 cursor-pointer"
                  @click="$emit('remove-redline', idx)"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. 正面表述与质检评分卡 -->
        <div
          v-if="auditResult"
          class="p-3 rounded-xl border flex flex-col gap-2"
          :class="auditResult.isHealthy ? 'bg-emerald-50/70 border-emerald-200' : 'bg-amber-50/70 border-amber-200'"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <i
                :data-lucide="auditResult.isHealthy ? 'check-circle' : 'alert-triangle'"
                class="w-4 h-4"
                :class="auditResult.isHealthy ? 'text-emerald-600' : 'text-amber-600'"
              ></i>
              <span class="text-xs font-bold text-slate-900">正面表述与四要素合规自检</span>
            </div>
            <span class="text-xs font-mono font-bold" :class="auditResult.isHealthy ? 'text-emerald-700' : 'text-amber-700'">
              完备度得分：{{ auditResult.score }} / 100
            </span>
          </div>

          <!-- 存在问题提示 -->
          <div v-if="auditResult.issues.length > 0" class="space-y-1">
            <div
              v-for="(issue, idx) in auditResult.issues"
              :key="idx"
              class="text-xs flex items-center gap-1.5"
              :class="issue.level === 'error' ? 'text-rose-700' : 'text-amber-700'"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="issue.level === 'error' ? 'bg-rose-500' : 'bg-amber-500'"></span>
              <span>{{ issue.text }}</span>
            </div>
          </div>
          <div v-else class="text-xs text-emerald-700">
            全部四要素结构完整，符合老赵哥正面表述规范与 AI 向量直接抽取标准！
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  card: { type: Object, default: null },
  layers: { type: Object, default: () => ({}) },
  auditResult: { type: Object, default: null },
});

const emit = defineEmits([
  'toggle-approve',
  'delete-card',
  'add-variant',
  'remove-variant',
  'add-evidence',
  'remove-evidence',
  'add-redline',
  'remove-redline',
]);

const newVariantText = ref('');

const handleAddVariant = () => {
  if (newVariantText.value.trim()) {
    emit('add-variant', newVariantText.value.trim());
    newVariantText.value = '';
  }
};
</script>
