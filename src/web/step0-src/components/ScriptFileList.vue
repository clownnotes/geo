<template>
  <div class="space-y-1.5">
    <div v-if="state === 'loading'" class="text-slate-400">{{ loadingText }}</div>
    <div v-else-if="state === 'error'" class="text-amber-700">{{ errorText }}</div>
    <div v-else-if="!scripts.length" class="text-amber-700">{{ emptyText }}</div>
    <template v-else>
      <div class="text-[10px] text-slate-500 mb-1">
        共 {{ scripts.length }} 份，按保存时间新→旧。点选 = 本轮拿去问豆包；可预览、可删除。
      </div>
      <div
        v-for="r in scripts"
        :key="r.file"
        class="flex items-start gap-2 border rounded-md px-2 py-2"
        :class="
          r.file === selectedFile
            ? 'border-indigo-200 bg-indigo-50/60'
            : 'border-slate-100 bg-white'
        "
      >
        <input
          type="radio"
          name="step0-script-pick"
          class="mt-1"
          :checked="r.file === selectedFile"
          @change="$emit('select', r.file)"
        />
        <div class="min-w-0 flex-1 cursor-pointer" @click="$emit('select', r.file)">
          <div class="font-semibold text-slate-800 break-all">
            {{ r.file }}
            <span
              class="ml-1 px-1 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 text-[9px] font-semibold"
            >
              {{ kindLabel(r.file) }}
            </span>
            <span
              v-if="r.file === selectedFile"
              class="ml-1 px-1 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-100 text-[9px] font-semibold"
            >
              本轮选用
            </span>
          </div>
          <div class="text-[10px] text-slate-400">
            {{ r.mtime || '' }}{{ r.item_count != null ? ` · ${r.item_count} 题` : '' }}{{ r.title ? ` · ${r.title}` : '' }}
          </div>
          <div
            v-if="peekLine(r)"
            class="text-[10px] text-slate-500 mt-0.5 truncate"
          >
            开头：{{ peekLine(r) }}
          </div>
        </div>
        <div class="flex flex-col gap-1 shrink-0">
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-200 bg-white hover:bg-slate-50 text-[10px] font-semibold text-slate-700"
            @click.stop="$emit('select', r.file)"
          >
            预览
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded border border-rose-200 bg-white hover:bg-rose-50 text-[10px] font-semibold text-rose-700"
            @click.stop="$emit('delete', r.file)"
          >
            删除
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  scripts: { type: Array, default: () => [] },
  selectedFile: { type: String, default: '' },
  state: { type: String, default: 'idle' },
  probeStatus: { type: String, default: 'unprobed' },
  loadingText: { type: String, default: '正在读取问题清单…' },
  emptyText: {
    type: String,
    default:
      '还没有要问豆包的问题清单文件。请先在本页生成问题清单，再点「刷新列表」。',
  },
  errorText: { type: String, default: '读取问题清单失败' },
  kindLabel: { type: Function, required: true },
});

defineEmits(['select', 'delete']);

function peekLine(r) {
  const qs = r.peek && Array.isArray(r.peek.queries) ? r.peek.queries : [];
  if (!qs.length) return '';
  const head = qs.slice(0, 2).join('；');
  return head + (qs.length > 2 ? '…' : '');
}
</script>
