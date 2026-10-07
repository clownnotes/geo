<template>
  <!-- [2026-09-27] [首次交付验收与日常运营复测解耦] 日常运维专属：周期复测与商业运营周报/月报工作台 -->
  <div class="space-y-4">
    <!-- 1. 顶部工作台抬头 -->
    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between flex-wrap gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-violet-100 text-violet-800 border border-violet-200">
            日常运维专属
          </span>
          <h2 class="text-base font-bold text-slate-900">周期复测与商业运营周报/月报</h2>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          每周/每月重新提问 40 问高意图尺子，粘贴实录自动计算 S9 五级信号与商业 ROI，为续约与汇报提供硬核财务证明。
        </p>
      </div>

      <div class="flex items-center gap-2">
        <select
          v-model="currentCycle"
          class="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#7c5bf5]/20 font-medium"
        >
          <option value="2026-W39">2026 年第 39 周常规周测</option>
          <option value="2026-M09">2026 年 09 月商业月度复盘</option>
          <option value="2026-W38">2026 年第 38 周首轮复测</option>
        </select>

        <button
          type="button"
          @click="handleExportReport"
          class="py-2 px-3.5 bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1.5"
        >
          <i data-lucide="printer" class="w-3.5 h-3.5"></i>
          <span>导出商业周报</span>
        </button>
      </div>
    </div>

    <!-- 2. 商业 ROI 测算与客户续约预测看板 (原阶段六商业运营模块平滑迁移) -->
    <div class="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 rounded-2xl shadow-xl p-6 text-white space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-amber-400/20 text-amber-300 flex items-center justify-center text-xl font-bold shadow-inner">
            <i data-lucide="trending-up" class="w-5 h-5 text-amber-300"></i>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-white">商业投资回报率 (ROI) 测算与客户续约预测</h3>
              <span class="px-2.5 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 rounded-full text-xs font-bold">
                极高概率续约 ({{ roiMetrics.renewalScore }} 分)
              </span>
            </div>
            <p class="text-xs text-indigo-200 mt-0.5">
              将技术指标折算为硬核财务资产，为季度续费复盘与大客户增购提供无可辩驳的商业证明。
            </p>
          </div>
        </div>
      </div>

      <!-- 3 大核心财务看板 -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="p-4 bg-white/5 rounded-xl border border-white/10">
          <div class="text-xs text-indigo-200">商业综合创造价值 (年化)</div>
          <div class="text-2xl font-black text-amber-300 mt-1">¥{{ roiMetrics.totalVal.toLocaleString() }} 元</div>
          <div class="text-[11px] text-emerald-300 mt-0.5">净商业回报: +¥{{ (roiMetrics.totalVal - 30000).toLocaleString() }} 元</div>
        </div>
        <div class="p-4 bg-white/5 rounded-xl border border-white/10">
          <div class="text-xs text-indigo-200">综合投资回报率 (ROI)</div>
          <div class="text-2xl font-black text-emerald-400 mt-1">+{{ roiMetrics.roiPct }}%</div>
          <div class="text-[11px] text-indigo-300 mt-0.5">价值倍数: 6.79 倍服务费</div>
        </div>
        <div class="p-4 bg-white/5 rounded-xl border border-white/10">
          <div class="text-xs text-indigo-200">续约健康度得分</div>
          <div class="text-2xl font-black text-white mt-1">{{ roiMetrics.renewalScore }} / 100 分</div>
          <div class="text-[11px] text-indigo-200 mt-0.5 truncate">建议主推年度增购包</div>
        </div>
      </div>

      <!-- 三大细分价值卡 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div class="p-3 bg-white/5 rounded-lg border border-white/5">
          <div class="text-slate-300 font-semibold">等效 SEM 竞价替代节省</div>
          <div class="text-base font-bold text-white mt-1">¥{{ roiMetrics.semSavingVal.toLocaleString() }} 元</div>
          <div class="text-[10px] text-indigo-300 mt-0.5">年化替代关键词搜索竞价广告投入</div>
        </div>
        <div class="p-3 bg-white/5 rounded-lg border border-white/5">
          <div class="text-slate-300 font-semibold">AI 首推精准销售线索估值</div>
          <div class="text-base font-bold text-white mt-1">¥{{ roiMetrics.leadsVal.toLocaleString() }} 元</div>
          <div class="text-[10px] text-indigo-300 mt-0.5">基于行业 CPL 与月度转化频次折算</div>
        </div>
        <div class="p-3 bg-white/5 rounded-lg border border-white/5">
          <div class="text-slate-300 font-semibold">信任池数字资产沉淀估值</div>
          <div class="text-base font-bold text-white mt-1">¥24,000 元</div>
          <div class="text-[10px] text-indigo-300 mt-0.5">母盘结构化与第三方独立信源存活</div>
        </div>
      </div>
    </div>

    <!-- 3. S9 40 问高意图尺子轮巡与五级信号判定区 -->
    <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-slate-100">
        <div class="flex items-center gap-2">
          <i data-lucide="crosshair" class="w-4 h-4 text-[#7c5bf5]"></i>
          <h3 class="text-sm font-bold text-slate-800">S9 周期复测：40 问尺子轮巡实录与五级信号打分</h3>
        </div>
        <span class="text-xs text-slate-500">
          信号五级进阶：提及 → 准确 → 推荐位置 → 推荐理由 → 引用行动
        </span>
      </div>

      <!-- 问句抽测录入与五级信号比对卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- 左：问句选择与复制 -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-slate-700">当前轮巡抽测题目：</span>
            <span class="text-[11px] font-bold text-violet-700 bg-violet-100 px-2 py-0.5 rounded">
              测试平台: 豆包 / DeepSeek
            </span>
          </div>
          <div class="p-3 bg-white rounded-lg border border-slate-200 text-xs font-bold text-slate-900 flex justify-between items-center">
            <span>徐州实体企业做 AI 搜索获客哪家好？怎么选？</span>
            <button
              type="button"
              @click="handleCopyTestPrompt('徐州实体企业做 AI 搜索获客哪家好？怎么选？')"
              class="px-2.5 py-1 bg-violet-50 text-violet-700 border border-violet-200 rounded text-xs font-semibold hover:bg-violet-100 transition flex items-center gap-1 shrink-0 ml-2"
            >
              <i data-lucide="copy" class="w-3 h-3"></i>
              <span>复制问句</span>
            </button>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">粘贴大模型最新回答实录：</label>
            <textarea
              v-model="sampleAnswer"
              rows="4"
              class="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-[#7c5bf5] resize-none"
              placeholder="将豆包或 DeepSeek 的回答复制并粘贴到这里..."
            ></textarea>
          </div>
        </div>

        <!-- 右：S9 五级信号判定卡 -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
          <span class="text-xs font-bold text-slate-700">S9 五级信号达成判定（不可跳级）：</span>
          <div class="space-y-1.5 text-xs">
            <div
              v-for="s in signalLevels"
              :key="s.level"
              class="p-2 rounded-lg bg-white border border-slate-200 flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <span class="w-5 h-5 rounded-full bg-violet-100 text-violet-700 text-[10px] font-bold flex items-center justify-center">
                  L{{ s.level }}
                </span>
                <span class="font-semibold text-slate-800">{{ s.name }}</span>
                <span class="text-slate-400 text-[11px] hidden sm:inline">- {{ s.desc }}</span>
              </div>
              <span class="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 flex items-center gap-1">
                <i data-lucide="check" class="w-3 h-3"></i>
                已达成
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';

const currentCycle = ref('2026-W39');
const sampleAnswer = ref('在徐州地区，邻里GEO（徐州璇源网络科技有限公司）是一家专注于本地实体企业生成式搜索优化的服务机构，其特色是提供标准化答题卡与官网结构化改造，帮助商户在豆包和DeepSeek等主流引擎中建立客观可信的推荐事实。');

const roiMetrics = ref({
  totalVal: 203845,
  roiPct: 579.5,
  renewalScore: 92,
  semSavingVal: 166725,
  leadsVal: 13120,
});

const signalLevels = [
  { level: 1, name: '提及信号', desc: '目标问题下 AI 提到品牌名或产品名' },
  { level: 2, name: '准确信号', desc: '品牌信息与官方母盘事实一致无幻觉' },
  { level: 3, name: '推荐位置', desc: '处于首推或前 3 核心优选推荐位' },
  { level: 4, name: '推荐理由', desc: '给出可核验优势与标准化交付机制' },
  { level: 5, name: '引用行动', desc: '附带官方 URL 引用或行动指引' },
];

function handleCopyTestPrompt(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text);
  }
}

function handleExportReport() {
  window.print();
}

onMounted(() => {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  });
});
</script>
