<template>
  <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
    <!-- 头部与 SOP 顺序说明 -->
    <Step0Header
      :project-data="projectData"
      :qlist-badge="qlistBadge"
      :write-status-badge="writeStatusBadge"
      :mode-banner="modeBanner"
      @refresh="refresh"
    />

    <!-- 步骤 1, 2, 3 主列表 -->
    <ol class="space-y-3 text-xs text-slate-700 list-none p-0 m-0">
      <!-- 第 1 步：准备要问的题（开发者带 Cursor 与 CLI，写文纯网页） -->
      <ProbeStep1
        :is-developer="isDeveloper"
        :project-id="projectId"
        :is-retest="isRetest"
        :step1-blurb-text="step1BlurbText"
        :copy-prompt-label="copyPromptLabel"
        :script-hint-text="scriptHintText"
        :generating-script="generatingScript"
        :cd-cmd-text="cdCmdText"
        :script-cmd-text="scriptCmdText"
        @copy-quality-prompt="copyQualityPrompt"
        @generate-script="generateScript"
        @copy-cmd="copyCmd"
        @copy-cursor-prompt="copyCursorPrompt"
      />

      <!-- 第 2 步：去豆包问（开发者带反重力与收工说明书，写文纯白话与落盘检查） -->
      <ProbeStep2
        :is-developer="isDeveloper"
        :scripts="scripts"
        :selected-script-file="selectedScriptFile"
        :script-list-state="scriptListState"
        :probe-status="probeStatus"
        :active-script="activeScript"
        :script-kind-text="scriptKindText"
        :script-path-rel="scriptPathRel"
        :script-path-abs="scriptPathAbs"
        :expected-result="expectedResult"
        :checking-disk="checkingDisk"
        @refresh-script-list="refresh({ asScriptCheck: true })"
        @select-script="selectScriptFile"
        @delete-script="deleteScriptFile"
        @copy-antigravity-prompt="copyAntigravityPrompt"
        @copy-antigravity-save-prompt="copyAntigravitySavePrompt"
        @copy-cmd="copyCmd"
        @check-result-on-disk="checkResultOnDisk"
      />

      <!-- 第 3 步：把豆包结果存进项目（开发者带 IDE 摘要复制与 CLI，写文纯预览写入） -->
      <ProbeStep3
        :is-developer="isDeveloper"
        :results="results"
        :selected-result-file="selectedResultFile"
        :result-list-state="resultListState"
        :upload-expected="uploadExpected"
        :merge="merge"
        :write-topics="writeTopics"
        :preview-data="previewData"
        :preview-copy-text="previewCopyText"
        :disk-preview-ready="diskPreviewReady"
        :write-status-badge="writeStatusBadge"
        :baseline-meta-text="baselineMetaText"
        :cmd-preview="cmdPreview"
        :cmd-apply="cmdApply"
        @refresh-results="refresh"
        @select-result="selectResultFile"
        @delete-result="deleteResultFile"
        @update:merge="merge = $event"
        @update:write-topics="writeTopics = $event"
        @copy-preview-for-ide="copyPreviewForIde"
        @preview-from-disk="previewFromDisk"
        @apply-from-disk="applyFromDisk"
        @preview-upload="previewUpload"
        @apply-upload="applyUpload"
        @copy-cmd="copyCmd"
      />
    </ol>

    <!-- 底部操作栏 -->
    <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
      <p class="text-[11px] text-slate-400">
        阶段零做完 = 第 2 步有豆包结果文件 + 第 3 步点过「确认写入项目」+ 这里变成绿色「豆包答案已存进项目」。
      </p>
      <button
        type="button"
        class="py-2.5 px-4 bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-semibold rounded-lg shadow flex items-center gap-1.5"
        @click="goStep1"
      >
        <span>进入阶段一体检</span>
        <i data-lucide="chevron-right" class="w-4 h-4"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useStep0 } from './useStep0.js';
import Step0Header from './components/Step0Header.vue';
import ProbeStep1 from './components/ProbeStep1.vue';
import ProbeStep2 from './components/ProbeStep2.vue';
import ProbeStep3 from './components/ProbeStep3.vue';

const props = defineProps({
  bridge: { type: Object, required: true },
});

const s0 = useStep0(props.bridge);

const {
  isDeveloper,
  projectData,
  qlistBadge,
  writeStatusBadge,
  modeBanner,
  projectId,
  isRetest,
  step1BlurbText,
  copyPromptLabel,
  scriptHintText,
  generatingScript,
  cdCmdText,
  scriptCmdText,
  scripts,
  selectedScriptFile,
  scriptListState,
  probeStatus,
  activeScript,
  scriptKindText,
  scriptPathRel,
  scriptPathAbs,
  expectedResult,
  checkingDisk,
  results,
  selectedResultFile,
  resultListState,
  uploadExpected,
  merge,
  writeTopics,
  previewData,
  previewCopyText,
  diskPreviewReady,
  baselineMetaText,
  cmdPreview,
  cmdApply,
  renderPanel,
  refresh,
  selectScriptFile,
  deleteScriptFile,
  copyQualityPrompt,
  generateScript,
  checkResultOnDisk,
  selectResultFile,
  deleteResultFile,
  copyPreviewForIde,
  previewFromDisk,
  applyFromDisk,
  previewUpload,
  applyUpload,
  copyCmd,
  copyCursorPrompt,
  copyAntigravityPrompt,
  copyAntigravitySavePrompt,
  goStep1,
} = s0;

onMounted(() => {
  renderPanel();
});

defineExpose({
  refresh,
  renderPanel,
});
</script>
