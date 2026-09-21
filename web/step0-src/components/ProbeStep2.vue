<template>
  <li class="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-3 list-none">
    <div class="font-semibold text-slate-900">
      {{ isDeveloper ? '2. 反重力去豆包问完题并落盘' : '2. 拿着问题清单去豆包问' }}
    </div>
    <p class="text-[11px] text-slate-500 leading-relaxed">
      {{ isDeveloper
        ? '管理台不会登录豆包。开发者将题目交由反重力智能助手或人工在 Safari 中逐题实战，并收工落盘为 UTF-8 JSON。'
        : '管理台不会登录豆包。你打开豆包，按下面清单逐题问。一题问完就新开一个聊天，再问下一题。问完回到本页，看结果文件有没有出现。'
      }}
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
        <div class="px-2.5 py-1.5 rounded bg-slate-50 border border-slate-200 text-[10px] text-slate-600 flex items-start gap-1.5">
          <i data-lucide="info" class="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5"></i>
          <span>{{ isDeveloper
            ? '这里只显示电脑里已经保存的问题清单。Cursor 聊天里列过题、但还没说「可以落盘」的，不会出现在这里。保存后请点本区「刷新列表」。'
            : '这里只显示已经保存的问题清单。刚生成的，请点「刷新列表」。'
          }}</span>
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

        <p class="text-[10px] text-slate-500">
          {{ isDeveloper ? `当前选用：${scriptPathRel}` : '选中一份，就是这一轮拿去问豆包的题。' }}
        </p>

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

      <!-- 开发者专属：C + D. 交付反重力 -->
      <template v-if="isDeveloper">
        <div class="bg-white border-2 border-amber-300 rounded-lg p-3 space-y-3">
          <div>
            <div class="text-[11px] font-bold text-amber-950">C + D. 开工前要交给反重力两样东西（缺一不可）</div>
            <p class="text-[11px] text-amber-900/80 mt-1 leading-relaxed">
              只点紫色按钮、只贴说明就让它开跑 = <strong>不够</strong>。还必须把「问题清单」文件用 @ 附上，它才知道问哪几句。顺序：先贴 C，马上做 D，两样齐了再让它去问。
            </p>
          </div>

          <div class="space-y-2 border-t border-amber-200/80 pt-3">
            <div class="text-[11px] font-semibold text-slate-800">① 先复制「怎么问」的说明，贴到反重力</div>
            <p class="text-[10px] text-slate-500">这里写的是规矩：用已登录的豆包、按顺序问、怎么记答案。贴完先别让它开跑，马上做 ②。</p>
            <button
              type="button"
              class="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 shadow-sm"
              @click="$emit('copy-antigravity-prompt')"
            >
              <i data-lucide="bot" class="w-3.5 h-3.5"></i><span>复制①怎么问（贴反重力）</span>
            </button>
          </div>

          <div class="space-y-2 border-t border-amber-200/80 pt-3">
            <div class="text-[11px] font-semibold text-slate-800">② 再把「问题清单」文件交给反重力（必须）</div>
            <p class="text-[10px] text-slate-500">在反重力输入框用 @ 或附件，选中下面这个文件。两样都进对话后，再让它去问豆包。</p>
            <div class="flex flex-wrap items-stretch gap-2">
              <div class="flex-1 min-w-[12rem] flex items-center font-mono text-[11px] bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
                <code class="flex-1 break-all select-all">{{ scriptPathAbs }}</code>
              </div>
              <button
                type="button"
                class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold"
                @click="$emit('copy-cmd', scriptPathAbs)"
              >
                复制问题清单路径（方便 @）
              </button>
            </div>
          </div>
        </div>

        <!-- E. 等反重力把题问完 -->
        <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-1">
          <div class="text-[11px] font-bold text-slate-900">E. 等反重力把题问完</div>
          <p class="text-[10px] text-slate-500">它会在豆包里逐题提问并在对话里汇总。这阶段<strong>还不会</strong>写结果文件。等它说问完了，再去做下面的 F。</p>
        </div>

        <!-- F. 第二次粘贴并检查落盘 -->
        <div class="bg-white border-2 border-[#7c5bf5]/40 rounded-lg p-3 space-y-3">
          <div>
            <div class="text-[11px] font-bold text-slate-900">F. 第二次粘贴：让反重力把结果写成文件</div>
            <p class="text-[11px] text-slate-600 mt-1 leading-relaxed">
              第一次粘贴<strong>不会</strong>自动落盘。你要再复制一次「收工说明书」贴进<strong>同一个</strong>反重力对话，它才会按路径新建/写入 JSON。写完后，你点「检查有没有落盘」。
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
            <code class="block break-all text-slate-600 select-all">
              {{ (expectedResult && (expectedResult.rel || expectedResult.file || expectedResult.resultPathText)) || '…' }}
            </code>
            <p class="text-slate-500 pt-0.5">
              {{ (expectedResult && expectedResult.hint) || '点「检查有没有落盘」后，这里会用白话告诉你：文件有了还是还没有。' }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="px-4 py-2.5 rounded-lg border-2 border-[#7c5bf5] bg-white hover:bg-violet-50 text-[#7c5bf5] text-[11px] font-semibold flex items-center gap-1.5"
              @click="$emit('copy-antigravity-save-prompt')"
            >
              <i data-lucide="save" class="w-3.5 h-3.5"></i>
              <span>复制②收工说明书（再贴反重力）</span>
            </button>
            <button
              type="button"
              class="px-4 py-2.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold flex items-center gap-1.5 disabled:opacity-50"
              :disabled="checkingDisk"
              @click="$emit('check-result-on-disk')"
            >
              <i data-lucide="radar" class="w-3.5 h-3.5"></i>
              <span>{{ checkingDisk ? '正在检查…' : '检查有没有落盘' }}</span>
            </button>
          </div>
          <p class="text-[10px] text-slate-500">
            徽章变「已生成」= 豆包已经问完并写成文件了。接着做第 3 步：选文件 → 预览 → 确认写入。只有确认写入，才算摸底存进项目。
          </p>
        </div>
      </template>

      <!-- 写文同事专属：极简手工问与检查 -->
      <template v-else>
        <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
          <div class="text-[11px] font-bold text-slate-900">去豆包里问这些题</div>
          <p class="text-[11px] text-slate-600 leading-relaxed">
            打开豆包，按上面题目一题一问。问完后，看下面「结果文件」有没有出现。
          </p>
        </div>

        <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-1">
          <div class="text-[11px] font-bold text-slate-900">等这一轮问完</div>
          <p class="text-[10px] text-slate-500">问完后点「检查有没有写好」。徽章变成「已生成」，再去做第 3 步确认写入。</p>
        </div>

        <!-- 检查落盘 -->
        <div class="bg-white border-2 border-[#7c5bf5]/40 rounded-lg p-3 space-y-3">
          <div>
            <div class="text-[11px] font-bold text-slate-900">看结果文件写好了没有</div>
            <p class="text-[11px] text-slate-600 mt-1 leading-relaxed">
              问完后点检查。显示「已生成」再去做第 3 步。
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
            <p class="text-slate-500 pt-0.5">
              {{ (expectedResult && expectedResult.hint) || '点「检查有没有写好」后，这里会告诉你：文件有了还是还没有。' }}
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
        </div>
      </template>
    </div>
  </li>
</template>

<script setup>
import ScriptFileList from './ScriptFileList.vue';
import { scriptKindLabel } from '../plainCopy.js';

defineProps({
  isDeveloper: { type: Boolean, default: true },
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

defineEmits([
  'refresh-script-list',
  'select-script',
  'delete-script',
  'copy-antigravity-prompt',
  'copy-antigravity-save-prompt',
  'copy-cmd',
  'check-result-on-disk',
]);
</script>
