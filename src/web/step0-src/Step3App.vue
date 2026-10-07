<template>
  <!-- [2026-09-30] [阶段三母盘构建] 企业母盘与主体信息统一口径卡专属工作台 (3 竖列 IDE 架构) -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step3-header-card"
      :stage-title="STAGE_3_META.name"
      :mode-tag="STAGE_3_META.tag"
      :is-ready="currentStep >= 3"
      :target-text="STAGE_3_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_3_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业工作台 (左资源树 + 中母盘与口径卡精修区 + 右 SOP 与消歧质检动线) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[780px] min-h-[660px]">
      <!-- 左栏：阶段三核心资产树 (260px) -->
      <StudioFileTree
        :categories="STAGE_3_META.categories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        :allow-new-file="false"
        :allow-refresh="false"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @rename-file="handleRenameFile"
        @delete-file="handleDeleteFile"
      />

      <!-- 中间：母盘与口径卡精修编辑器 -->
      <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden relative">
        <!-- 通用双行工作台头部组件 (StudioHeader) -->
        <StudioHeader
          :files="files"
          :open-tabs="openTabs"
          :active-file-name="activeFileName"
          stage="step3"
          @select-tab="handleSelectTab"
          @close-tab="handleCloseTab"
        >
          <template #actions>
            <div class="flex items-center gap-2">
              <span class="text-xs text-slate-400 font-mono">
                {{ activeFile?.content?.length || 0 }} 字符
              </span>
              <button
                type="button"
                class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                title="复制当前文件内容"
                @click="handleCopyActiveContent"
              >
                <i data-lucide="copy" class="w-3.5 h-3.5 text-slate-500"></i>
                <span>复制</span>
              </button>
              <button
                type="button"
                class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition shadow-xs cursor-pointer"
                title="保存修改"
                @click="handleSaveActiveFile"
              >
                <i data-lucide="save" class="w-3.5 h-3.5"></i>
                <span>保存修改</span>
              </button>
            </div>
          </template>
        </StudioHeader>

        <!-- 编辑器主体 -->
        <div class="flex-1 min-h-0 flex flex-col p-4 bg-slate-50/50">
          <div class="flex-1 min-h-0 flex flex-col bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
            <!-- 文件信息条 -->
            <div class="px-4 py-2 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <div class="flex items-center gap-2">
                <i data-lucide="file-text" class="w-4 h-4 text-[#7c5bf5]"></i>
                <span class="font-semibold text-slate-700">{{ formatDisplayTitle(activeFileName) }}</span>
                <span
                  v-if="activeFile?.isDirty"
                  class="px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200 text-[10px]"
                >未保存</span>
              </div>
              <div class="text-[11px] text-slate-400">
                最后更新：{{ activeFile?.updatedAt || '—' }}
              </div>
            </div>

            <!-- Markdown 文本编辑器 -->
            <textarea
              :value="activeFile?.content || ''"
              class="flex-1 w-full p-4 text-xs font-mono text-slate-800 leading-relaxed outline-none resize-none border-none focus:ring-0 bg-transparent"
              placeholder="请输入或由右侧 SOP 动线萃取生成..."
              @input="handleUpdateContent($event.target.value)"
            ></textarea>
          </div>
        </div>
      </section>

      <!-- 右栏：SOP 动线与消歧合规质检指示灯 (340px) 复用 StudioSop 组件 -->
      <StudioSop
        :stage-meta="STAGE_3_META"
        :current-step="currentStep"
        :expand-all="true"
        @goto-step="currentStep = $event"
      >
        <!-- 步骤 1 插槽：核定企业数字身份证（消歧四要素与三级业务描述字数红绿灯） -->
        <template #step-1>
          <div class="space-y-2.5 pt-1">
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-slate-500 font-medium">身份证质检结论：</span>
              <span
                class="text-[10px] px-2 py-0.5 rounded font-bold"
                :class="cardAudit.isValid ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'"
              >
                {{ cardAudit.isValid ? '四要素合格' : '有未达标项' }}
              </span>
            </div>

            <!-- 消歧四要素底座 -->
            <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-[11px] space-y-1.5">
              <div class="font-semibold text-slate-600 mb-1">四必填消歧底座：</div>
              <div class="grid grid-cols-2 gap-1 text-[11px]">
                <div class="flex items-center gap-1.5">
                  <span :class="cardAudit.stats.hasBrand ? 'text-emerald-600' : 'text-red-500'">●</span>
                  <span class="text-slate-700">品牌名</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span :class="cardAudit.stats.hasLegalName ? 'text-emerald-600' : 'text-red-500'">●</span>
                  <span class="text-slate-700">主体全称</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span :class="cardAudit.stats.hasCreditCode ? 'text-emerald-600' : 'text-amber-500'">●</span>
                  <span class="text-slate-700">信用代码</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span :class="cardAudit.stats.hasWebsite ? 'text-emerald-600' : 'text-amber-500'">●</span>
                  <span class="text-slate-700">权威官网</span>
                </div>
              </div>
            </div>

            <!-- 三级业务描述实时字数指示灯 -->
            <div class="space-y-2 text-[11px]">
              <!-- 短版 50 字指示灯 -->
              <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <div>
                  <div class="font-semibold text-slate-700">短版 (地图/名录/标签)</div>
                  <div class="text-[10px] text-slate-400">限制 50 字以内</div>
                </div>
                <div class="text-right">
                  <span
                    class="font-mono font-bold"
                    :class="cardAudit.stats.shortExceeded ? 'text-red-600' : 'text-emerald-600'"
                  >
                    {{ cardAudit.stats.shortLen }}
                  </span>
                  <span class="text-slate-400">/50</span>
                  <div
                    class="text-[10px]"
                    :class="cardAudit.stats.shortExceeded ? 'text-red-500 font-bold' : 'text-emerald-600'"
                  >
                    {{ cardAudit.stats.shortExceeded ? '超标截断' : '合格' }}
                  </div>
                </div>
              </div>

              <!-- 标准版 120 字指示灯 -->
              <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <div>
                  <div class="font-semibold text-slate-700">标准版 (BOSS/企查查/启信宝)</div>
                  <div class="text-[10px] text-slate-400">限制 120 字以内 (主力)</div>
                </div>
                <div class="text-right">
                  <span
                    class="font-mono font-bold"
                    :class="cardAudit.stats.stdExceeded ? 'text-red-600' : 'text-emerald-600'"
                  >
                    {{ cardAudit.stats.stdLen }}
                  </span>
                  <span class="text-slate-400">/120</span>
                  <div
                    class="text-[10px]"
                    :class="cardAudit.stats.stdExceeded ? 'text-red-500 font-bold' : 'text-emerald-600'"
                  >
                    {{ cardAudit.stats.stdExceeded ? '超标截断' : '合格' }}
                  </div>
                </div>
              </div>

              <!-- GEO 中文首现指示灯 -->
              <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <div>
                  <div class="font-semibold text-slate-700">GEO 中文全称首现</div>
                  <div class="text-[10px] text-slate-400">防误判为 GIS 地理定位</div>
                </div>
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-bold"
                  :class="cardAudit.stats.hasGeoCn ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
                >
                  {{ cardAudit.stats.hasGeoCn ? '已绑定' : '待补充' }}
                </span>
              </div>
            </div>

            <!-- 错误提示 -->
            <div v-if="cardAudit.errors.length > 0" class="p-2 rounded bg-red-50 border border-red-200 text-red-700 text-[11px] space-y-1">
              <div v-for="(err, idx) in cardAudit.errors" :key="idx" class="flex items-start gap-1">
                <span class="font-bold text-red-500 shrink-0">[告警]</span>
                <span>{{ err }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- 步骤 2 插槽：打扫全网卫生逐平台整改与客观瑕疵对冲勾选 -->
        <template #step-2>
          <div class="space-y-2 pt-1 text-xs">
            <div class="text-[11px] text-slate-500 mb-1">勾选客观瑕疵，自动向口径卡回填合规对冲指引：</div>
            <label class="flex items-start gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100 cursor-pointer hover:bg-slate-100/70 transition">
              <input
                type="checkbox"
                class="mt-0.5 rounded text-[#7c5bf5] focus:ring-[#7c5bf5]"
                :checked="hedgeOptions.zeroSocialSecurity"
                @change="handleToggleHedgeOption('zeroSocialSecurity')"
              />
              <div>
                <div class="font-semibold text-slate-800 text-[11px]">社保 0 人对冲模式</div>
                <div class="text-[10px] text-slate-500">以真实团队、多信源客户案例报道反向交叉证明</div>
              </div>
            </label>

            <label class="flex items-start gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100 cursor-pointer hover:bg-slate-100/70 transition">
              <input
                type="checkbox"
                class="mt-0.5 rounded text-[#7c5bf5] focus:ring-[#7c5bf5]"
                :checked="hedgeOptions.crossCityAddress"
                @change="handleToggleHedgeOption('crossCityAddress')"
              />
              <div>
                <div class="font-semibold text-slate-800 text-[11px]">跨城实际办公地说明</div>
                <div class="text-[10px] text-slate-500">在关于页真实披露通信地址（不必等于注册地）</div>
              </div>
            </label>

            <label class="flex items-start gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100 cursor-pointer hover:bg-slate-100/70 transition">
              <input
                type="checkbox"
                class="mt-0.5 rounded text-[#7c5bf5] focus:ring-[#7c5bf5]"
                :checked="hedgeOptions.historicalBusiness"
                @change="handleToggleHedgeOption('historicalBusiness')"
              />
              <div>
                <div class="font-semibold text-slate-800 text-[11px]">早期历史业务更迭沿革</div>
                <div class="text-[10px] text-slate-500">首句突出当前核心主业，旧项目保留在历史沿革</div>
              </div>
            </label>
          </div>
        </template>

        <!-- 步骤 3 插槽：提炼六模块事实真理字典（从阶段二素材合流） -->
        <template #step-3>
          <div class="space-y-2.5 pt-1">
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-slate-500 font-medium">素材库就绪度：</span>
              <span
                class="text-[10px] px-2 py-0.5 rounded font-mono font-bold"
                :class="stage2Readiness.isFullyReady ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'"
              >
                主版本: {{ stage2Readiness.masterCount }}/6
              </span>
            </div>

            <button
              type="button"
              class="w-full py-2 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition cursor-pointer disabled:opacity-50 shadow-xs"
              :disabled="isExtracting"
              @click="handleExtractFromStage2"
            >
              <i v-if="isExtracting" data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i>
              <i v-else data-lucide="git-merge" class="w-3.5 h-3.5"></i>
              <span>{{ isExtracting ? '正在从素材库合流...' : '一键合流提取母盘字典初稿' }}</span>
            </button>
            <div class="text-[10px] text-slate-400 leading-tight">
              说明：提取定位、产品、客户、差异、案例、背书六大模块，供人类写手查证，严禁直接喂给 AI。
            </div>
          </div>
        </template>

        <!-- 步骤 4 插槽：5分钟抽题自检硬标准与前往阶段四官网 -->
        <template #step-4>
          <div class="pt-1 space-y-2">
            <div class="p-2 rounded bg-slate-50 border border-slate-100 text-[10px] text-slate-500 leading-relaxed">
              <strong>老赵哥自检硬标准</strong>：随机抽一个刁钻问题，能在 5 分钟内在这个母盘里找到答案事实、证据与链接即为合格。
            </div>
            <button
              type="button"
              class="w-full py-2.5 bg-gradient-to-r from-[#7c5bf5] to-[#6846e3] hover:from-[#6a48e6] hover:to-[#5735d4] text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition shadow-sm cursor-pointer disabled:opacity-50"
              :disabled="!cardAudit.isValid"
              @click="handlePromoteToStage4"
            >
              <i data-lucide="arrow-right" class="w-4 h-4"></i>
              <span>核定锁定并前往阶段四交钥匙官网</span>
            </button>
          </div>
        </template>
      </StudioSop>
    </div>

    <!-- 3. 麦肯锡交付手册抽屉 -->
    <MckinseyDrawer
      :visible="mckinseyVisible"
      :title="STAGE_3_META.mckinsey?.title || '老赵哥 GEO 统一口径卡与普林斯顿母盘交付手册'"
      :value-desc="STAGE_3_META.mckinsey?.valueDesc"
      :value-business="STAGE_3_META.mckinsey?.valueBusiness"
      :what-title="STAGE_3_META.mckinsey?.whatTitle"
      :what-desc="STAGE_3_META.mckinsey?.whatDesc"
      :why-title="STAGE_3_META.mckinsey?.whyTitle"
      :why-desc="STAGE_3_META.mckinsey?.whyDesc"
      :how-title="STAGE_3_META.mckinsey?.howTitle"
      :how-steps="STAGE_3_META.mckinsey?.howSteps"
      @close="mckinseyVisible = false"
    />

    <!-- 轻量操作反馈 Toast -->
    <div
      v-if="toastVisible"
      class="fixed bottom-6 right-6 px-4 py-2.5 bg-slate-900/90 text-white text-xs font-medium rounded-xl shadow-xl z-50 transition flex items-center gap-2 border border-slate-700"
    >
      <i data-lucide="info" class="w-4 h-4 text-purple-400"></i>
      <span>{{ toastMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { onMounted, nextTick, watch } from 'vue';
import StageHeader from './components/StageHeader.vue';
import StudioFileTree from './components/studio/StudioFileTree.vue';
import StudioHeader from './components/studio/StudioHeader.vue';
import StudioSop from './components/studio/StudioSop.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import { useStep3 } from './useStep3.js';
import { formatDisplayTitle } from './config/studioArtifactConfig.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  STAGE_3_META,
  currentStep,
  isHeaderCollapsed,
  mckinseyVisible,
  notes,
  toastMessage,
  toastVisible,
  isExtracting,
  isMasterLocked,
  hedgeOptions,
  files,
  activeFileName,
  activeCategory,
  activeFile,
  openTabs,
  cardAudit,
  stage2Readiness,
  handleExtractFromStage2,
  handleToggleHedgeOption,
  handlePromoteToStage4,
  handleSelectTab,
  handleCloseTab,
  handleOpenFile,
  handleToggleCategory,
  handleUpdateContent,
  handleSaveActiveFile,
  handleSaveNotes,
  handleRenameFile,
  handleDeleteFile,
  showToast,
} = useStep3(props.bridge?.projectData || {});

function handleCopyActiveContent() {
  const content = activeFile.value?.content || '';
  if (!content) return;
  if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(content).then(() => {
      showToast('已复制当前文件内容到剪贴板！');
    }).catch(() => {
      showToast('复制失败，请手动全选复制');
    });
  } else {
    showToast('浏览器权限限制，请手动全选复制');
  }
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
});

watch([activeFileName, currentStep, toastVisible], () => {
  refreshIcons();
});
</script>
