<template>
  <!-- [2026-09-27] [双轨兼容] SOP 交付动线面板：
       1. 支持新版由 props.stageMeta 动态配置驱动；
       2. 若未传入 stageMeta，自动退回阶段零默认 2 步，并双向兼容发射新旧事件，确保阶段零完好工作 -->
  <aside class="w-full lg:w-[340px] shrink-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
    <!-- 顶栏：当前阶段动线标题与进度 -->
    <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <i data-lucide="list-ordered" class="w-4 h-4 text-[#7c5bf5]"></i>
        <span class="text-[13px] font-bold text-slate-800 uppercase tracking-wider">交付动线</span>
      </div>
      <span class="text-[12px] text-slate-500 font-medium">{{ expandAll ? `共 ${steps.length} 项操作` : `第 ${currentStep} / ${steps.length} 步` }}</span>
    </div>

    <!-- 动线卡片区 -->
    <div class="flex-1 overflow-y-auto p-3.5 text-sm space-y-2.5">
      <div
        v-for="(step, idx) in steps"
        :key="step.id || idx"
        class="rounded-xl border-2 transition-all duration-200"
        :class="stepClass(idx)"
      >
        <!-- 步骤头部：序号 + 名称 + 状态标签 -->
        <div
          class="flex items-center justify-between gap-2 p-3 select-none"
          :class="expandAll ? 'cursor-default' : 'cursor-pointer'"
          @click="onGotoStep(idx + 1)"
        >
          <div class="flex items-center gap-2 min-w-0">
            <span
              class="w-5.5 h-5.5 rounded-full font-bold flex items-center justify-center text-[12px] shrink-0"
              :class="expandAll ? 'bg-[#7c5bf5]/10 text-[#7c5bf5]' : (idx + 1 < currentStep ? 'bg-emerald-500 text-white' : (idx + 1 === currentStep ? 'bg-[#7c5bf5] text-white' : 'bg-slate-200 text-slate-500'))"
            >
              <span v-if="!expandAll && idx + 1 < currentStep">✓</span>
              <span v-else>{{ idx + 1 }}</span>
            </span>
            <span
              class="font-bold text-[14px] truncate"
              :class="expandAll || idx + 1 === currentStep ? 'text-slate-900' : 'text-slate-500'"
            >{{ step.name }}</span>
          </div>
          <span
            v-if="!expandAll"
            class="text-[11px] px-2 py-0.5 rounded font-bold shrink-0"
            :class="idx + 1 < currentStep
              ? 'text-emerald-700 bg-emerald-50 border border-emerald-200'
              : (idx + 1 === currentStep ? 'text-[#7c5bf5] bg-white border border-[#7c5bf5]/30' : 'text-slate-400 bg-slate-100')"
          >
            {{ idx + 1 < currentStep ? '已完成' : (idx + 1 === currentStep ? '进行中' : '待执行') }}
          </span>
        </div>

        <!-- 当前步骤展开：说明 + 动作/门禁/按钮 -->
        <div v-if="expandAll || idx + 1 === currentStep" class="px-3 pb-3 space-y-3">
          <p class="text-[13px] text-slate-700 leading-relaxed">{{ step.desc }}</p>

          <!-- 步骤门禁单选判定 (如阶段一耐心确认门禁) -->
          <div v-if="step.gate && step.gate.type === 'patience_confirm'" class="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <div class="text-[12px] font-bold text-slate-800">客户意向与核对门禁：</div>
            <label
              v-for="opt in step.gate.options"
              :key="opt.id"
              class="flex items-start gap-2 text-[12px] cursor-pointer p-1.5 rounded hover:bg-white transition"
              :class="selectedGate === opt.id ? 'bg-white font-semibold text-[#7c5bf5]' : 'text-slate-600'"
            >
              <input
                type="radio"
                name="patience_gate"
                :value="opt.id"
                v-model="selectedGate"
                class="mt-0.5 text-[#7c5bf5] focus:ring-[#7c5bf5]"
              />
              <span>{{ opt.label }}</span>
            </label>
          </div>

          <div class="flex flex-col gap-2.5">
            <!-- 动作按钮 (如真抓指标 / 直出初稿) -->
            <button
              v-if="step.action"
              type="button"
              class="px-3 py-2 rounded-lg border text-[13px] font-bold flex items-center justify-center gap-1.5 transition shadow-2xs cursor-pointer"
              :class="isActionDone(step.action.type)
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100/60'
                : 'bg-[#7c5bf5]/10 border-[#7c5bf5]/30 hover:bg-[#7c5bf5]/20 text-[#7c5bf5]'"
              @click.stop="onActionClick(step.action.type)"
            >
              <i :data-lucide="isActionDone(step.action.type) ? 'check-circle' : (step.action.icon || 'activity')" class="w-4 h-4"></i>
              <span>{{ isActionDone(step.action.type) ? (step.action.completedLabel || '已抓取真实指标 (点击重新抓取)') : step.action.label }}</span>
            </button>

            <!-- 附加动作（如重新出题） -->
            <button
              v-if="step.extraAction"
              type="button"
              class="px-3 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-[#7c5bf5] text-[13px] font-semibold flex items-center justify-center gap-1.5 transition shadow-2xs cursor-pointer"
              @click.stop="onExtraAction(step.extraAction.type)"
            >
              <i :data-lucide="step.extraAction.icon || 'sparkles'" class="w-4 h-4"></i>
              <span>{{ step.extraAction.label }}</span>
            </button>

            <!-- 外链动作（如打开豆包网页版） -->
            <a
              v-if="step.linkAction"
              :href="step.linkAction.href"
              target="_blank"
              rel="noopener noreferrer"
              class="px-3 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-semibold flex items-center justify-center gap-1.5 transition shadow-2xs"
            >
              <i :data-lucide="step.linkAction.icon || 'external-link'" class="w-4 h-4 text-[#7c5bf5]"></i>
              <span>{{ step.linkAction.label }}</span>
            </a>

            <!-- 多重快捷动作 (如全屏演示大屏 / 复制客户报告链接) -->
            <div v-if="step.extraActions && step.extraActions.length" class="grid grid-cols-2 gap-2">
              <button
                v-for="ea in step.extraActions"
                :key="ea.type"
                type="button"
                class="px-2 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[12px] font-semibold flex items-center justify-center gap-1 transition shadow-2xs cursor-pointer"
                @click.stop="onActionClick(ea.type)"
              >
                <i :data-lucide="ea.icon || 'link'" class="w-3.5 h-3.5 text-[#7c5bf5]"></i>
                <span class="truncate">{{ ea.label }}</span>
              </button>
            </div>

            <!-- [2026-09-28] 主推进按钮上方静态辅助提示 (杜绝彩色 Emoji) -->
            <div
              v-if="shouldHighlightProceed(step, idx)"
              class="text-[11px] text-[#7c5bf5] font-semibold text-center py-0.5"
            >
              指标已抓取就绪，请核对中栏并点击下方继续
            </div>

            <!-- 主推进按钮：下一步 / 完成阶段 (仅在未显式声明 hideProceed 时渲染) -->
            <button
              v-if="!step.hideProceed"
              type="button"
              class="w-full py-2.5 rounded-lg text-white text-[14px] font-bold transition flex items-center justify-center gap-1.5 shadow cursor-pointer"
              :class="[
                isProceedDisabled(step) ? 'bg-slate-300 cursor-not-allowed text-slate-500 shadow-none' : 'bg-[#7c5bf5] hover:bg-[#6846e3]',
                shouldHighlightProceed(step, idx) ? 'animate-pulse ring-2 ring-[#7c5bf5]/40 shadow-md' : ''
              ]"
              :disabled="isProceedDisabled(step)"
              @click.stop="onProceedClick(step, idx)"
            >
              <span>{{ step.nextLabel || '前往下一步' }}</span>
              <i data-lucide="arrow-right" class="w-4 h-4"></i>
            </button>

            <!-- 次要跳过动作 (如跳过润色直接出报告) -->
            <button
              v-if="!step.hideProceed && step.skipLabel"
              type="button"
              class="w-full py-1 text-slate-500 hover:text-slate-800 text-[12px] transition text-center underline cursor-pointer"
              @click.stop="onSkipClick(step, idx)"
            >
              {{ step.skipLabel }}
            </button>

            <!-- 回退上一步 -->
            <button
              v-if="!expandAll && idx > 0"
              type="button"
              class="w-full py-1 text-slate-400 hover:text-slate-600 text-[12px] transition text-center cursor-pointer"
              @click.stop="onGotoStep(idx)"
            >
              ← 返回上一步
            </button>

            <!-- 阶段零三级微动线完成提示 -->
            <div v-if="step.hideProceed && idx === steps.length - 1" class="pt-2 border-t border-slate-100 text-[11px] text-slate-400 text-center">
              提示：本小节工作完成后，可直接在左侧菜单切换至下一项
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';

const props = defineProps({
  /** 当前阶段配置（来自 stageConfigs 或外部传入） */
  stageMeta: { type: Object, default: () => null },
  /** 当前步骤序号，1 起 */
  currentStep: { type: Number, default: 1 },
  /** [2026-09-28] 是否平铺展开所有三级微操作卡片（阶段零专用） */
  expandAll: { type: Boolean, default: false },
  /** 兼容阶段零 ready 状态 */
  isReady: { type: Boolean, default: false },
  /** 门禁单选值 (confirmed / suspended) */
  gate: { type: String, default: 'confirmed' },
  /** [2026-09-28] [阶段一底座抓取动线视线引导优化] 动作完成态映射字典，如 { crawlMetrics: true } */
  actionCompletedMap: { type: Object, default: () => ({}) },
});

const emit = defineEmits([
  'proceed', 'gotoStep', 'extraAction', 'action', 'skip',
  'update:gate',
  // [2026-09-28] [出题草稿采纳流] 阶段零核心事件与动作事件，彻底清理废弃悬空的 proceed-to-next
  'switch-step', 'refresh-questions', 'finish-stage0',
  'save-file', 'adopt-current-file'
]);

// 阶段零默认 SOP（当 stageMeta 为空时回退兜底）
const DEFAULT_STAGE0_STEPS = [
  {
    id: 'prepare',
    name: '0.1 准备题目打磨',
    desc: 'AI 根据客户定位已预生成 5 道核心题。交付专家可在中间编辑器直接修改润色，从 60 分打磨到 80 分。',
    extraAction: { label: '重新出题（生成新版）', icon: 'sparkles', type: 'refreshQuestions' },
    nextLabel: '保存并前往：0.2 网页提问拿答案',
  },
  {
    id: 'ask',
    name: '0.2 网页提问贴回答',
    desc: '点击中间【一键复制内容】，打开豆包网页逐题提问，将豆包的真实回答结果贴回中间文件。',
    linkAction: { label: '打开豆包网页版提问', icon: 'external-link', href: 'https://www.doubao.com' },
    nextLabel: '保存答案，完成阶段零（前往 01 现状诊断）',
    isFinal: true,
  },
];

const selectedGate = ref(props.gate || 'confirmed');
watch(() => props.gate, (v) => {
  if (v) selectedGate.value = v;
});
watch(selectedGate, (v) => {
  emit('update:gate', v);
});

const steps = computed(() => {
  if (props.stageMeta) {
    if (Array.isArray(props.stageMeta.sopSteps) && props.stageMeta.sopSteps.length > 0) {
      return props.stageMeta.sopSteps;
    }
    if (Array.isArray(props.stageMeta.steps) && props.stageMeta.steps.length > 0) {
      return props.stageMeta.steps;
    }
  }
  return DEFAULT_STAGE0_STEPS;
});

function stepClass(idx) {
  if (props.expandAll) return 'border-slate-200 bg-white shadow-2xs';
  if (idx + 1 === props.currentStep) return 'border-[#7c5bf5] bg-indigo-50/20';
  if (idx + 1 < props.currentStep) return 'border-emerald-200 bg-emerald-50/30';
  return 'border-slate-200 bg-slate-50/60';
}

// [2026-09-28] [阶段一底座抓取动线视线引导优化] 检查动作是否已完成，做空值与空字典安全短路
function isActionDone(type) {
  if (!type || !props.actionCompletedMap) return false;
  return !!props.actionCompletedMap[type];
}

// [2026-09-28] [阶段一底座抓取动线视线引导优化] 是否高亮推进按钮（防污染：严格限定当前步骤且动作已完成）
function shouldHighlightProceed(step, idx) {
  if (!step?.action?.type) return false;
  if (idx + 1 !== props.currentStep) return false;
  return isActionDone(step.action.type);
}

function isProceedDisabled(step) {
  if (step.gate && step.gate.type === 'patience_confirm') {
    return selectedGate.value === 'suspended';
  }
  return false;
}

function onGotoStep(num) {
  // [2026-09-28] [线上P0热修] 平铺微动线模式下所有卡片已展开，禁止点击卡片头部意外派发 switch-step
  // 杜绝：1) 点击卡片 2 触发 switch-step(2) 跨页跳往 0.2；
  //       2) 点击卡片 3 触发 switch-step(3) 导致 subMetaMap[3] 抛出 TypeError
  if (props.expandAll) return;
  emit('gotoStep', num);
  emit('switch-step', num);
}

function onExtraAction(type) {
  emit('extraAction', type);
  emit('refresh-questions');
}

function onActionClick(type) {
  emit('action', type);
  // [2026-09-28] [出题草稿采纳流] 显式派发封版、保存文件与采纳底牌事件
  if (type === 'finishStage0') emit('finish-stage0');
  if (type === 'saveCurrentFile') emit('save-file');
  if (type === 'adoptCurrentFile') emit('adopt-current-file');
}

function onProceedClick(step, idx) {
  emit('proceed', step);
  // [2026-09-28] 清理废弃悬空的 proceed-to-next 发射，仅保留两步以内的封版逻辑
  if (idx === 1 && steps.value.length <= 2) {
    emit('finish-stage0');
  }
}

function onSkipClick(step, idx) {
  emit('skip', step);
  emit('proceed', step);
}

watch([() => props.currentStep, () => props.stageMeta, () => props.expandAll, () => props.actionCompletedMap], () => {
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons();
  });
}, { deep: true });
</script>
