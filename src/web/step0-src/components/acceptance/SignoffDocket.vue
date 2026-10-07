<template>
  <!-- [2026-09-27] [首次交付验收与日常运营复测解耦] 阶段六右栏：首期工程移交与结项验收单凭据 -->
  <div class="w-full lg:w-[350px] shrink-0 bg-white rounded-xl border border-slate-200 flex flex-col h-full shadow-xs overflow-hidden">
    <!-- 1. 顶部公文抬头 -->
    <div class="p-3.5 border-b border-slate-100 bg-slate-50/70">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <i data-lucide="file-check-2" class="w-4 h-4 text-[#7c5bf5]"></i>
          <span class="text-xs font-bold text-slate-800">首期工程移交与结项验收单</span>
        </div>
        <span
          :class="[
            'text-[10px] font-bold px-2 py-0.5 rounded-full border',
            signoffForm.isSigned
              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
              : 'bg-amber-50 text-amber-700 border-amber-300'
          ]"
        >
          {{ signoffForm.isSigned ? '双方已签字结项' : '待确认签字' }}
        </span>
      </div>
      <p class="text-[11px] text-slate-500 mt-1">
        交付结项凭据，可直接用于首期尾款结算与知识资产移交。
      </p>
    </div>

    <!-- 2. 中间公文卡片与签署表单滚动区 -->
    <div class="flex-1 overflow-y-auto p-3.5 space-y-3">
      <!-- 凭据核心摘要卡 (公文信纸感) -->
      <div class="p-3 bg-slate-50/90 rounded-xl border border-slate-200 space-y-2 text-xs">
        <div class="flex justify-between items-center pb-2 border-b border-slate-200">
          <span class="text-slate-500">项目品牌:</span>
          <span class="font-bold text-slate-900">{{ projectContext.brand }}</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-500">企业主体:</span>
          <span class="font-medium text-slate-700 truncate max-w-[180px]">{{ projectContext.company }}</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-500">移交资产:</span>
          <span class="font-bold text-emerald-600">母盘 + 40答题卡 + 官网源码 + 外链台账</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-500">首轮改口:</span>
          <span class="font-bold text-emerald-600">3/3 核心问句改口达标</span>
        </div>
        <div class="flex justify-between items-center pt-1 border-t border-slate-200 text-[11px]">
          <span class="text-slate-400">交接基准:</span>
          <span class="text-slate-600 font-mono">S11 换人能接手</span>
        </div>
      </div>

      <!-- 双方签署人与验收意见 -->
      <div class="space-y-2 text-xs">
        <div>
          <label class="block text-slate-600 font-medium mb-1">交付方代表 (邻里GEO):</label>
          <input
            v-model="signoffForm.vendorSigner"
            type="text"
            class="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-[#7c5bf5]"
          />
        </div>

        <div>
          <label class="block text-slate-600 font-medium mb-1">接收方代表 (客户企业):</label>
          <input
            v-model="signoffForm.clientSigner"
            type="text"
            class="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-[#7c5bf5]"
          />
        </div>

        <div>
          <label class="block text-slate-600 font-medium mb-1">签署日期:</label>
          <input
            v-model="signoffForm.signDate"
            type="text"
            class="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-[#7c5bf5]"
          />
        </div>

        <div>
          <label class="block text-slate-600 font-medium mb-1">结项意见与备忘:</label>
          <textarea
            v-model="signoffForm.comments"
            rows="2"
            class="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-[#7c5bf5] resize-none"
          ></textarea>
        </div>
      </div>

      <!-- 绿色印章状态显示 -->
      <div
        v-if="signoffForm.isSigned"
        class="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200 text-center space-y-0.5"
      >
        <span class="text-xs font-black text-emerald-800 tracking-wider">【 首期工程验收合格 · 正式结案 】</span>
        <p class="text-[10px] text-emerald-600">已存档入项目历史，后续转入日常运维周报体系。</p>
      </div>
    </div>

    <!-- 3. 底部主操作动作栏 -->
    <div class="p-3 border-t border-slate-100 bg-slate-50/70 space-y-2">
      <div class="flex gap-2">
        <button
          type="button"
          @click="$emit('save-signoff')"
          class="flex-1 py-2 bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center justify-center gap-1.5"
        >
          <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
          <span>保存签署确认</span>
        </button>

        <button
          type="button"
          @click="$emit('print-signoff')"
          class="py-2 px-3 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1 shrink-0"
          title="打印或导出PDF"
        >
          <i data-lucide="printer" class="w-3.5 h-3.5"></i>
          <span>打印凭据</span>
        </button>
      </div>

      <button
        type="button"
        @click="$emit('export-markdown')"
        class="w-full py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-[11px] font-semibold rounded-lg transition flex items-center justify-center gap-1"
      >
        <i data-lucide="download" class="w-3.5 h-3.5 text-slate-500"></i>
        <span>导出交付资产清册.md</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  projectContext: { type: Object, default: () => ({}) },
  signoffForm: { type: Object, default: () => ({}) },
});

defineEmits([
  'save-signoff',
  'reset-signoff',
  'print-signoff',
  'export-markdown',
]);
</script>
