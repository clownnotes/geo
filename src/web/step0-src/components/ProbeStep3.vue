<template>
  <li class="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-3 list-none">
    <div class="font-semibold text-slate-900">3. 把豆包结果存进项目</div>

    <div class="text-[11px] text-slate-600 leading-relaxed bg-indigo-50/60 border border-indigo-100 rounded-lg px-3 py-2.5 space-y-1.5">
      <p class="font-semibold text-slate-800">这一步在干什么？（一句话）</p>
      <p>{{ isDeveloper
        ? '反重力已经把答案写成了一个 JSON 文件。现在你要告诉管理台：「就用这个文件」，先看一眼会改什么，觉得没问题再真正写进去。'
        : '豆包问完后，结果会写成一个文件。你在这里选中它，先看一眼会改什么，觉得没问题再确认写入。'
      }}</p>
      <p class="text-slate-500">比喻：作业本在桌上了（第 2 步落盘）。第 3 步是：选哪本作业本 → 先翻开看一眼 → 再交到老师那里存档。</p>
      <p class="text-amber-800">下面 A、B、C 三个按钮都在本卡片里往下滚就能看到，不是藏在别处。</p>
    </div>

    <div class="space-y-3">
      <!-- A. 选作业本 -->
      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="text-[11px] font-bold text-slate-900">A. 选一份结果文件（准备交哪本作业）</div>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-[10px] font-semibold text-slate-600 flex items-center gap-1"
            title="重新读取电脑里的结果文件"
            @click="$emit('refresh-results')"
          >
            <i data-lucide="refresh-cw" class="w-3 h-3"></i>刷新列表
          </button>
        </div>
        <p class="text-[10px] text-slate-500">
          选中的那份文件，后面 B「预览」和 C「确认写入」就对它生效。点某一行 = 选中；点删除 = 删那一份文件。
        </p>

        <!-- 结果文件列表 -->
        <div class="border border-slate-200 rounded-lg overflow-hidden text-xs">
          <div v-if="resultListState === 'loading'" class="text-slate-400 p-3">加载中…</div>
          <div v-else-if="resultListState === 'error'" class="text-amber-700 p-3">无法读取已存在结果列表。</div>
          <div v-else-if="!results.length" class="text-amber-700 p-3">
            目前还没有任何结果文件。请先做完第 2 步去豆包问完，再点「刷新列表」。
          </div>
          <template v-else>
            <div
              v-for="f in results"
              :key="f.name"
              class="flex flex-wrap items-center justify-between gap-2 px-3 py-2 border-b border-slate-100 last:border-0 hover:bg-slate-50/80 cursor-pointer"
              :class="selectedResultFile === f.name ? 'bg-indigo-50/70 border-l-4 border-l-[#7c5bf5]' : ''"
              @click="$emit('select-result', f.name)"
            >
              <div class="flex items-center gap-2 min-w-0">
                <input
                  type="radio"
                  name="selected-result"
                  :value="f.name"
                  :checked="selectedResultFile === f.name"
                  class="text-[#7c5bf5] shrink-0"
                  @change="$emit('select-result', f.name)"
                />
                <span class="font-mono text-[11px] font-semibold text-slate-800 truncate">{{ f.name }}</span>
                <span v-if="f.item_count != null" class="text-[10px] text-slate-400 shrink-0">({{ f.item_count }} 题)</span>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <span class="text-[10px] text-slate-400">{{ f.mtime_text || f.time || '' }}</span>
                <button
                  type="button"
                  class="text-rose-500 hover:text-rose-700 p-1 text-[10px]"
                  title="删除该文件"
                  @click.stop="$emit('delete-result', f.name)"
                >
                  删除
                </button>
              </div>
            </div>
          </template>
        </div>

        <p class="text-[10px] text-slate-400 font-mono break-all">
          {{ uploadExpected }}
        </p>

        <!-- 选项勾选 -->
        <label class="flex items-center gap-2 text-[11px] text-slate-700 cursor-pointer">
          <input
            v-model="localMerge"
            type="checkbox"
            class="text-[#7c5bf5] rounded"
            @change="$emit('update:merge', localMerge)"
          />
          <span>合并写入（保留历史已有维度与题目，推荐）</span>
        </label>
        <label class="flex items-center gap-2 text-[11px] text-slate-700 cursor-pointer">
          <input
            v-model="localWriteTopics"
            type="checkbox"
            class="text-[#7c5bf5] rounded"
            @change="$emit('update:write-topics', localWriteTopics)"
          />
          <span>同时提炼竞品与潜在搜索主题</span>
        </label>
      </div>

      <!-- B. 预览区 -->
      <div class="bg-white border-2 border-[#7c5bf5]/35 rounded-lg p-3 space-y-2">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0">
            <div class="text-[11px] font-bold text-slate-900">B. 看这份结果里「豆包怎么说」+「准备写入项目什么」</div>
            <p class="text-[10px] text-slate-500 mt-1">
              这里<strong>不是</strong>豆包网页聊天全文。落盘文件里存的是每题的结论摘要。
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="isDeveloper"
              type="button"
              class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!previewCopyText"
              @click="$emit('copy-preview-for-ide')"
            >
              一键复制给 IDE
            </button>
            <button
              type="button"
              class="w-full sm:w-auto px-4 py-2.5 rounded-lg border-2 border-[#7c5bf5] bg-white hover:bg-violet-50 text-[#7c5bf5] text-[11px] font-semibold flex items-center justify-center gap-1.5"
              @click="$emit('preview-from-disk')"
            >
              <i data-lucide="eye" class="w-3.5 h-3.5"></i>
              <span>刷新预览</span>
            </button>
          </div>
        </div>

        <div
          v-if="previewData"
          class="text-[11px] text-slate-700 bg-slate-50 border border-slate-100 rounded-md p-2.5 space-y-1.5 max-h-80 overflow-y-auto"
        >
          <div v-if="previewData.summary" class="font-semibold text-slate-800 border-b border-slate-200 pb-1">
            {{ previewData.summary.primary_finding || previewData.summary.brand_status || previewData.summary }}
          </div>
          <div v-if="(previewData.answer_briefs || previewData.items) && (previewData.answer_briefs || previewData.items).length" class="space-y-2 pt-1">
            <div
              v-for="(it, i) in (previewData.answer_briefs || previewData.items)"
              :key="i"
              class="border-b border-slate-200/60 pb-1.5 last:border-0"
            >
              <div class="font-medium text-slate-900">
                {{ i + 1 }}. {{ it.query }}
                <span
                  class="ml-1 px-1 py-0.5 rounded text-[9px] font-semibold"
                  :class="(it.mentioned_self ?? it.brand_mentioned) ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'"
                >
                  {{ (it.mentioned_self ?? it.brand_mentioned) ? '提到我们' : '未提我们' }}
                </span>
                <span v-if="it.standpoint" class="ml-1 px-1 py-0.5 rounded text-[9px] font-semibold bg-slate-100 text-slate-700">
                  {{ it.standpoint }}
                </span>
              </div>
              <div v-if="it.doubao_verdict || it.answer_snippet" class="text-slate-500 text-[10px] mt-0.5">
                {{ it.doubao_verdict || it.answer_snippet }}
              </div>
              <div v-if="it.competitors && it.competitors.length" class="text-amber-800 text-[10px] mt-0.5">
                竞品/友商：{{ it.competitors.join('、') }}
              </div>
            </div>
          </div>
        </div>
        <p v-else class="text-[10px] text-slate-400">没有内容时：先在 A 选中文件，再点「刷新预览」。</p>
      </div>

      <!-- C. 确认写入 -->
      <div class="bg-white border-2 border-[#7c5bf5]/35 rounded-lg p-3 space-y-2">
        <div class="text-[11px] font-bold text-slate-900">C. 点「确认写入」——真正存进项目</div>
        <p class="text-[10px] text-slate-500">
          选中文件并出现预览后，这个按钮才会亮。点它 = 真正写入项目；右上角应出现<strong>「确认已写入」</strong>。
        </p>
        <button
          type="button"
          class="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          :disabled="!diskPreviewReady"
          @click="$emit('apply-from-disk')"
        >
          <i data-lucide="check" class="w-3.5 h-3.5"></i>
          <span>确认写入项目</span>
        </button>
        <p v-if="!diskPreviewReady" class="text-[10px] text-slate-400">按钮是灰的 = 还没预览成功，先去做 B。</p>
      </div>

      <!-- D. 写完了再往下走 -->
      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="text-[11px] font-bold text-slate-900">D. 写完了再往下走</div>
          <span
            class="px-2 py-0.5 rounded-md text-[10px] font-semibold border"
            :class="writeStatusBadge.className"
          >
            {{ writeStatusBadge.text }}
          </span>
        </div>
        <p class="text-[10px] text-slate-500 leading-relaxed">
          <strong class="text-rose-700">红色「还没把豆包答案存进项目」</strong> = 新建客户，或还没点过上面的「确认写入」——这时只能写「第一次要问的题」。<br />
          <strong class="text-emerald-700">绿色「豆包答案已存进项目」</strong> = 第 3 步已经把某份豆包结果存进去了。这才是摸底存档。之后出题会变成「再测一遍」。
        </p>
        <p v-if="baselineMetaText" class="text-[10px] font-mono text-slate-400 break-all">
          {{ baselineMetaText }}
        </p>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="px-4 py-2.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[11px] font-semibold flex items-center gap-1.5"
            @click="$emit('refresh-results')"
          >
            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
            <span>重新检查进度</span>
          </button>
        </div>
      </div>

      <details class="bg-white border border-dashed border-slate-200 rounded-lg p-3">
        <summary class="text-[11px] font-semibold text-slate-600 cursor-pointer select-none">
          {{ isDeveloper ? '备用：本机上传文件 / CLI（一般不用）' : '备用：从本机选一个结果文件上传' }}
        </summary>
        <div class="mt-2 space-y-2">
          <input
            ref="fileInputRef"
            type="file"
            accept=".json,application/json"
            class="block w-full text-[11px] text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-[11px] file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[11px] font-semibold text-slate-700"
              @click="$emit('preview-upload', fileInputRef)"
            >
              上传预览
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[11px] font-semibold text-slate-700"
              @click="$emit('apply-upload', fileInputRef)"
            >
              上传后确认回填
            </button>
          </div>

          <!-- 开发者专属：CLI 命令行 -->
          <template v-if="isDeveloper">
            <div class="flex flex-wrap items-stretch gap-2">
              <div class="flex-1 min-w-[12rem] flex items-center font-mono text-[11px] bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
                <code class="flex-1 break-all select-all">{{ cmdPreview }}</code>
              </div>
              <button
                type="button"
                class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold"
                @click="$emit('copy-cmd', cmdPreview)"
              >
                复制
              </button>
            </div>

            <div class="flex flex-wrap items-stretch gap-2">
              <div class="flex-1 min-w-[12rem] flex items-center font-mono text-[11px] bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
                <code class="flex-1 break-all select-all">{{ cmdApply }}</code>
              </div>
              <button
                type="button"
                class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold"
                @click="$emit('copy-cmd', cmdApply)"
              >
                复制
              </button>
            </div>
          </template>
        </div>
      </details>
    </div>
  </li>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  isDeveloper: { type: Boolean, default: true },
  results: { type: Array, default: () => [] },
  selectedResultFile: { type: String, default: '' },
  resultListState: { type: String, default: 'idle' },
  uploadExpected: { type: String, default: '' },
  merge: { type: Boolean, default: true },
  writeTopics: { type: Boolean, default: true },
  previewData: { type: Object, default: null },
  previewCopyText: { type: String, default: '' },
  diskPreviewReady: { type: Boolean, default: false },
  writeStatusBadge: { type: Object, required: true },
  baselineMetaText: { type: String, default: '' },
  cmdPreview: { type: String, default: '' },
  cmdApply: { type: String, default: '' },
});

const emit = defineEmits([
  'refresh-results',
  'select-result',
  'delete-result',
  'update:merge',
  'update:write-topics',
  'copy-preview-for-ide',
  'preview-from-disk',
  'apply-from-disk',
  'preview-upload',
  'apply-upload',
  'copy-cmd',
]);

const localMerge = ref(props.merge);
const localWriteTopics = ref(props.writeTopics);
const fileInputRef = ref(null);
</script>
