<template>
  <li class="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-3 list-none">
    <div class="font-semibold text-slate-900">2. 拿着问题清单去豆包问</div>
    <p class="text-[11px] text-slate-500 leading-relaxed">
      管理台不会登录豆包。你打开豆包，按下面清单逐题问。一题问完就新开一个聊天，再问下一题。问完回到本页，看结果文件有没有出现。
    </p>

    <div class="space-y-2.5">
      <!-- A. 准备环境 -->
      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-1.5">
        <div class="text-[11px] font-bold text-slate-900">A. 先准备好环境</div>
        <ul class="text-[11px] text-slate-600 space-y-0.5 list-disc list-inside">
          <li>打开豆包网页并已登录</li>
          <li>在豆包里<strong>每测一题新开一个聊天</strong>（一题一清空上下文，防止上一题记忆串台）</li>
        </ul>
      </div>

      <!-- B. 问题清单列表与预览 -->
      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
        <div class="flex flex-wrap items-center gap-2">
          <div class="text-[11px] font-bold text-slate-900">B. 要问豆包的问题清单（可预览、可删除）</div>
          <span
            class="px-1.5 py-0.5 rounded text-[10px] font-semibold border"
            :class="
              activeScript
                ? 'bg-sky-50 text-sky-800 border-sky-100'
                : 'bg-amber-50 text-amber-800 border-amber-100'
            "
          >
            {{ scriptKindText }}
          </span>
          <button
            type="button"
            class="ml-auto px-2.5 py-1 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-[10px] font-semibold text-slate-600 flex items-center gap-1"
            title="重新读取电脑里的问题清单文件"
            @click="$emit('refresh-script-list')"
          >
            <i data-lucide="refresh-cw" class="w-3 h-3"></i>刷新列表
          </button>
        </div>
        <!-- [2026-09-17] [阶段零出题落盘] 固定说明：只显示已保存文件，聊天未落盘不出现 -->
        <div class="px-2.5 py-1.5 rounded bg-slate-50 border border-slate-200 text-[10px] text-slate-600 flex items-start gap-1.5">
          <i data-lucide="info" class="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5"></i>
          <span>这里只显示已经保存的问题清单。刚生成的，请点「刷新列表」。</span>
        </div>
        <p class="text-[10px] text-slate-500">
          下面按<strong>时间新→旧</strong>列出所有问题清单。点选一份 = 本轮拿去问豆包的那份；点「预览」看题目；点「删除」只删这一份文件（删前会再问你一次）。
        </p>

        <!-- 问题清单组件 -->
        <ScriptFileList
          :scripts="scripts"
          :selected-file="selectedScriptFile"
          :state="scriptListState"
          :probe-status="probeStatus"
          :kind-label="scriptKindLabel"
          @select="$emit('select-script', $event)"
          @delete="$emit('delete-script', $event)"
        />

        <p class="text-[10px] text-slate-500">选中一份，就是这一轮拿去问豆包的题。</p>

        <!-- 题目预览卡片 -->
        <div class="border border-slate-100 rounded-md px-2.5 py-2 bg-white">
          <div class="text-[10px] font-semibold text-slate-600 mb-1">题目预览</div>
          <div class="text-[11px] text-slate-700 max-h-40 overflow-y-auto space-y-1">
            <template v-if="activeScript && activeScript.items && activeScript.items.length">
              <div
                v-for="(item, idx) in activeScript.items"
                :key="idx"
                class="flex items-start gap-1.5 py-0.5 border-b border-slate-50 last:border-0"
              >
                <span class="text-slate-400 shrink-0 font-mono text-[10px]">{{ idx + 1 }}.</span>
                <span class="break-all">{{ item.query || item.title || item.topic || JSON.stringify(item) }}</span>
              </div>
            </template>
            <div v-else class="text-slate-400">选中一份清单后，这里显示题目。</div>
          </div>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
        <div class="text-[11px] font-bold text-slate-900">去豆包里问这些题</div>
        <p class="text-[11px] text-slate-600 leading-relaxed">
          打开豆包，按上面题目一题一问。不要把题目说明复制到别的软件。问完后，看下面「结果文件」有没有出现。
        </p>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-1">
        <div class="text-[11px] font-bold text-slate-900">等这一轮问完</div>
        <p class="text-[10px] text-slate-500">问完后点「检查有没有写好」。徽章变成「已生成」，再去做第 3 步确认写入。</p>
      </div>

      <!-- F. 第二次粘贴并检查落盘 -->
      <div class="bg-white border-2 border-[#7c5bf5]/40 rounded-lg p-3 space-y-3">
        <div>
          <div class="text-[11px] font-bold text-slate-900">看结果文件写好了没有</div>
          <p class="text-[11px] text-slate-600 mt-1 leading-relaxed">
            问完后点检查。显示「已生成」再去做第 3 步。这里只告诉你有没有文件，不把做法交给别的软件。
          </p>
        </div>
        <div class="text-[10px] space-y-1 bg-slate-50 border border-slate-100 rounded-md px-2.5 py-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-semibold text-slate-700">本轮结果文件：</span>
            <span
              class="px-1.5 py-0.5 rounded text-[10px] font-semibold border"
              :class="(expectedResult && expectedResult.badgeClass) || 'bg-amber-50 text-amber-800 border-amber-100'"
            >
              {{ (expectedResult && expectedResult.badgeText) || '尚未生成' }}
            </span>
          </div>
          <code class="hidden"></code>
          <p class="text-slate-500 pt-0.5">
            {{ (expectedResult && expectedResult.hint) || '点「检查有没有落盘」后，这里会用白话告诉你：文件有了还是还没有。' }}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="px-4 py-2.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold flex items-center gap-1.5 disabled:opacity-50"
            :disabled="checkingDisk"
            @click="$emit('check-result-on-disk')"
          >
            <i data-lucide="radar" class="w-3.5 h-3.5"></i>
            <span>{{ checkingDisk ? '正在检查…' : '检查有没有写好' }}</span>
          </button>
        </div>
        <p class="text-[10px] text-slate-500">
          徽章变「已生成」= 豆包已经问完并写成文件了。接着做第 3 步：选文件 → 预览 → 确认写入。只有确认写入，才算摸底存进项目。
        </p>
      </div>
    </div>
  </li>
</template>

<script setup>
import ScriptFileList from './ScriptFileList.vue';
import { scriptKindLabel } from '../plainCopy.js';

defineProps({
  scripts: { type: Array, default: () => [] },
  selectedScriptFile: { type: String, default: '' },
  scriptListState: { type: String, default: 'idle' },
  probeStatus: { type: String, default: 'unprobed' },
  activeScript: { type: Object, default: null },
  scriptKindText: { type: String, default: '' },
  scriptPathRel: { type: String, default: '' },
  scriptPathAbs: { type: String, default: '' },
  expectedResult: { type: Object, default: null },
  checkingDisk: { type: Boolean, default: false },
});

defineEmits(['refresh-script-list', 'select-script', 'delete-script', 'check-result-on-disk']);
</script>
