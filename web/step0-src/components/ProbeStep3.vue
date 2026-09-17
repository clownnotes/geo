<template>
  <li class="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-3 list-none">
    <div class="font-semibold text-slate-900">3. 把豆包问到的结果，存进这个客户项目</div>

    <div class="text-[11px] text-slate-600 leading-relaxed bg-indigo-50/60 border border-indigo-100 rounded-lg px-3 py-2.5 space-y-1.5">
      <p class="font-semibold text-slate-800">这一步在干什么？（一句话）</p>
      <p>反重力已经把答案写成了一个 JSON 文件。现在你要告诉管理台：「就用这个文件」，先<strong>看一眼会改什么</strong>，觉得没问题再<strong>真正写进去</strong>。</p>
      <p class="text-slate-500">比喻：作业本在桌上了（第 2 步落盘）。第 3 步是：选哪本作业本 → 先翻开看一眼 → 再交到老师那里存档。</p>
      <p class="text-amber-800">下面 A、B、C 三个按钮都在本卡片里往下滚就能看到，不是藏在别处。</p>
    </div>

    <div class="space-y-2.5">
      <!-- A. 选结果文件 -->
      <div class="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="text-[11px] font-bold text-slate-900">A. 选哪一份结果（选中后立刻能看见里面问了啥）</div>
          <button
            type="button"
            class="px-2.5 py-1 rounded border border-slate-200 bg-white hover:bg-slate-50 text-[10px] font-semibold text-slate-600"
            @click="$emit('refresh-results')"
          >
            刷新列表
          </button>
        </div>
        <p class="text-[10px] text-slate-500">
          不是盲选。点某一行后，下面会展开：问了哪些题、提没提我们、冒出哪些竞品。只有一份时也要勾一下，等于告诉系统「就用这一份」；有多份时，看日期和摘要挑对的（一般选最新，或带 retest 的复测）。
        </p>
        <p class="text-[10px] text-slate-500 break-all">{{ uploadExpected }}</p>

        <!-- 结果列表 -->
        <div class="text-[11px] text-slate-600 space-y-1.5 bg-slate-50 border border-slate-100 rounded-md px-2.5 py-2 min-h-[2.5rem]">
          <div v-if="resultListState === 'loading'" class="text-slate-400">加载中…</div>
          <div v-else-if="resultListState === 'error'" class="text-amber-700">无法读取已存在结果列表。</div>
          <div v-else-if="!results.length" class="text-amber-700">
            目前还没有任何结果文件。请先做完第 2 步让反重力落盘，再点「刷新列表」。
          </div>
          <template v-else>
            <div
              v-for="r in results"
              :key="r.file"
              class="flex items-start gap-2 border rounded-md px-2 py-1.5 cursor-pointer"
              :class="
                r.file === selectedResultFile
                  ? 'border-indigo-200 bg-indigo-50/60'
                  : 'border-slate-100 bg-white'
              "
              @click="$emit('select-result', r.file)"
            >
              <input
                type="radio"
                name="step0-result-pick"
                class="mt-1"
                :checked="r.file === selectedResultFile"
                @change="$emit('select-result', r.file)"
              />
              <div class="min-w-0 flex-1">
                <div class="font-semibold text-slate-800 break-all">
                  {{ r.file }}
                  <span
                    v-if="r.file === selectedResultFile"
                    class="ml-1 px-1 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-100 text-[9px] font-semibold"
                  >
                    选用中
                  </span>
                </div>
                <div class="text-[10px] text-slate-400">
                  {{ r.mtime || '' }}{{ r.item_count != null ? ` · ${r.item_count} 题` : '' }}{{ r.model ? ` · ${r.model}` : '' }}
                </div>
              </div>
            </div>
          </template>
        </div>

        <label class="flex items-center gap-2 text-[11px] text-slate-600 select-none pt-1">
          <input
            v-model="localMerge"
            type="checkbox"
            class="rounded border-slate-300 text-[#7c5bf5] focus:ring-[#7c5bf5]"
            @change="$emit('update:merge', localMerge)"
          />
          <span>写入时合并旧内容（项目里已有精修选题/竞品时请勾上，避免被盖掉）</span>
        </label>
        <label class="flex items-start gap-2 text-[11px] text-slate-600 select-none pt-1">
          <input
            v-model="localWriteTopics"
            type="checkbox"
            class="mt-0.5 rounded border-slate-300 text-[#7c5bf5] focus:ring-[#7c5bf5]"
            @change="$emit('update:write-topics', localWriteTopics)"
          />
          <span><strong>同时把本题长问写入选题清单</strong>（推荐）。短词会被自动拒收；写入后可去「日常运维 · 选题长问清单」跟客户确认。</span>
        </label>
      </div>

      <!-- B. 预览区 -->
      <div class="bg-white border-2 border-[#7c5bf5]/35 rounded-lg p-3 space-y-2">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0">
            <div class="text-[11px] font-bold text-slate-900">B. 看这份结果里「豆包怎么说」+「准备写入项目什么」</div>
            <p class="text-[10px] text-slate-500 mt-1">
              这里<strong>不是</strong>豆包网页聊天全文（全文在豆包会话里）。落盘文件里存的是每题的结论摘要。下面分两块：① 每题答案摘要；② 若点确认，会写进项目的竞品/问句。题少 = 这份结果文件里本来就只有这么多题（邻里 GEO 第一次摸底只有 3 题），不是被界面截断了。
            </p>
          </div>
          <button
            type="button"
            class="shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[#7c5bf5] text-[11px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!previewCopyText"
            @click="$emit('copy-preview-for-ide')"
          >
            一键复制给 IDE
          </button>
        </div>

        <button
          type="button"
          class="w-full sm:w-auto px-4 py-2.5 rounded-lg border-2 border-[#7c5bf5] bg-white hover:bg-violet-50 text-[#7c5bf5] text-[11px] font-semibold flex items-center justify-center gap-1.5"
          @click="$emit('preview-from-disk')"
        >
          <i data-lucide="eye" class="w-3.5 h-3.5"></i>
          <span>刷新预览</span>
        </button>

        <div
          v-if="previewData"
          class="text-[11px] text-slate-700 bg-slate-50 border border-slate-100 rounded-md p-2.5 space-y-1.5 max-h-80 overflow-y-auto"
        >
          <div v-if="previewData.summary" class="font-semibold text-slate-800 border-b border-slate-200 pb-1">
            {{ previewData.summary }}
          </div>
          <div v-if="previewData.items && previewData.items.length" class="space-y-2 pt-1">
            <div
              v-for="(it, i) in previewData.items"
              :key="i"
              class="border-b border-slate-200/60 pb-1.5 last:border-0"
            >
              <div class="font-medium text-slate-900">
                {{ i + 1 }}. {{ it.query }}
                <span
                  class="ml-1 px-1 py-0.5 rounded text-[9px] font-semibold"
                  :class="it.brand_mentioned ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'"
                >
                  {{ it.brand_mentioned ? '提到我们' : '未提我们' }}
                </span>
              </div>
              <div v-if="it.answer_snippet" class="text-slate-500 text-[10px] mt-0.5">
                {{ it.answer_snippet }}
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
          选中文件并出现预览后，这个按钮才会亮。点它 = 真正写入项目；右上角应出现<strong>「确认已写入」</strong>。只有你亲手点 B「刷新预览」时才会提示「已预览」，两者不要搞混。
        </p>
        <button
          type="button"
          class="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
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
          <strong class="text-emerald-700">绿色「豆包答案已存进项目」</strong> = 第 3 步已经把某份豆包结果存进去了——这才是摸底存档，不是 Cursor 写的题目。之后出题会变成「再测一遍」。<br />
          点「重新检查进度」只是再读一遍电脑和项目状态；不会凭空变出豆包答案。
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

      <!-- 备用：上传与CLI -->
      <details class="bg-white border border-dashed border-slate-200 rounded-lg p-3">
        <summary class="text-[11px] font-semibold text-slate-600 cursor-pointer select-none">
          备用：本机上传文件 / CLI（一般不用）
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
        </div>
      </details>
    </div>
  </li>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
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
