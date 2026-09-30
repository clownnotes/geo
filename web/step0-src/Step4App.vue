<template>
  <!-- [2026-09-30] [00~07 全流水线顺延] 阶段四 3 竖列工作区：AI 原生交钥匙官网与大模型三件套专属工作台 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step4-header-card"
      :stage-title="STAGE_4_META.name"
      :mode-tag="STAGE_4_META.tag"
      :is-ready="currentStep >= 3"
      :target-text="STAGE_4_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_4_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业交付工作台 (左资源树 + 中官网高保真打磨区 + 右 SOP 动线) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[760px] min-h-[640px]">
      <!-- 左栏：文件资源树 (260px) -->
      <StudioFileTree
        :categories="STAGE_4_META.categories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        :allow-new-file="false"
        :allow-refresh="true"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @refresh-files="handleCompile"
        @rename-file="handleRenameFile"
      />

      <!-- 中间：交钥匙官网高保真预览与源码双模工作区 -->
      <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
        <!-- 顶部标签栏与工具条 -->
        <div class="bg-slate-50 border-b border-slate-200 flex items-center justify-between px-2 pt-2 gap-2 overflow-x-auto select-none">
          <!-- Tab 标签列表 -->
          <div class="flex items-center gap-1.5 overflow-x-auto flex-1 scrollbar-none">
            <div
              v-for="fn in openTabs"
              :key="fn"
              class="flex items-center gap-2 px-3.5 py-1.5 rounded-t-lg text-[13px] font-medium cursor-pointer transition border border-b-0 shrink-0"
              :class="fn === activeFileName ? 'bg-white text-[#7c5bf5] border-slate-200 font-bold -mb-[1px]' : 'bg-slate-100/80 hover:bg-slate-200/80 text-slate-600 border-transparent'"
              @click="handleSelectTab(fn)"
            >
              <span class="truncate max-w-[160px]">{{ fn }}</span>
              <span
                v-if="files[fn]?.isDirty"
                class="w-2 h-2 rounded-full bg-amber-500 shrink-0"
                title="有未保存修改"
              ></span>
              <span
                class="text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded p-0.5 text-xs"
                title="关闭标签"
                @click.stop="handleCloseTab(fn)"
              >
                ×
              </span>
            </div>
          </div>

          <!-- 右侧工具条：高保真预览/源码模式切换 + 电脑/手机视口切换 + 独立直达 + 复制 + 保存 -->
          <div class="flex items-center gap-2 shrink-0 pb-1">
            <!-- 仅在查看 index.html 时提供双模与多端切换 -->
            <template v-if="activeFileName === 'index.html'">
              <!-- 视图模式：预览 vs 源码 -->
              <div class="flex items-center bg-white border border-slate-200 rounded-md overflow-hidden shadow-2xs">
                <button
                  type="button"
                  class="px-2.5 py-1 text-[12px] font-semibold transition cursor-pointer"
                  :class="dualViewMode === 'preview' ? 'bg-[#7c5bf5] text-white' : 'text-slate-600 hover:bg-slate-50'"
                  @click="dualViewMode = 'preview'"
                >高保真预览</button>
                <button
                  type="button"
                  class="px-2.5 py-1 text-[12px] font-semibold transition cursor-pointer"
                  :class="dualViewMode === 'code' ? 'bg-[#7c5bf5] text-white' : 'text-slate-600 hover:bg-slate-50'"
                  @click="dualViewMode = 'code'"
                >源码编辑</button>
              </div>

              <!-- 视口切换：电脑宽屏 vs 手机竖屏 (仅预览态有效) -->
              <div v-if="dualViewMode === 'preview'" class="flex items-center bg-white border border-slate-200 rounded-md overflow-hidden shadow-2xs">
                <button
                  type="button"
                  class="px-2.5 py-1 text-[12px] font-semibold transition cursor-pointer flex items-center gap-1"
                  :class="viewportMode === 'desktop' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-50'"
                  title="切换电脑宽屏视图"
                  @click="viewportMode = 'desktop'"
                >
                  <i data-lucide="monitor" class="w-3.5 h-3.5"></i>
                  <span>电脑宽屏</span>
                </button>
                <button
                  type="button"
                  class="px-2.5 py-1 text-[12px] font-semibold transition cursor-pointer flex items-center gap-1"
                  :class="viewportMode === 'mobile' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-50'"
                  title="切换手机竖屏视图 (375px)"
                  @click="viewportMode = 'mobile'"
                >
                  <i data-lucide="smartphone" class="w-3.5 h-3.5"></i>
                  <span>手机竖屏</span>
                </button>
              </div>

              <!-- 独立站点直达 -->
              <button
                type="button"
                class="px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[12px] font-medium flex items-center gap-1 transition shadow-2xs cursor-pointer"
                title="在新窗口打开纯净官网"
                @click="handleOpenPureSite"
              >
                <i data-lucide="external-link" class="w-3.5 h-3.5 text-[#7c5bf5]"></i>
                <span>独立直达</span>
              </button>
            </template>

            <!-- 快捷复制 -->
            <button
              type="button"
              class="px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[12px] font-medium flex items-center gap-1 transition shadow-2xs cursor-pointer"
              title="复制当前文件内容"
              @click="handleCopyContent"
            >
              <i data-lucide="copy" class="w-3.5 h-3.5 text-slate-500"></i>
              <span>复制</span>
            </button>

            <!-- 保存文件 -->
            <button
              type="button"
              class="px-3 py-1 rounded-md bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-[12px] font-semibold flex items-center gap-1 transition shadow-2xs cursor-pointer"
              title="保存当前文件修改"
              @click="handleSaveActiveFile"
            >
              <i data-lucide="save" class="w-3.5 h-3.5"></i>
              <span>保存</span>
            </button>
          </div>
        </div>

        <!-- 工作区主体内容 -->
        <div class="flex-1 overflow-hidden relative flex flex-col bg-slate-100">
          <!-- 模式 A：官网高保真可视化预览 (采用 srcdoc 离线实时渲染，绝无 404) -->
          <div
            v-if="activeFileName === 'index.html' && dualViewMode === 'preview'"
            class="flex-1 overflow-y-auto flex items-center justify-center p-3 bg-slate-200/60"
          >
            <!-- 电脑端：100% 容器充满 -->
            <div
              v-if="viewportMode === 'desktop'"
              class="w-full h-full bg-white rounded-lg shadow-sm border border-slate-300 overflow-hidden flex flex-col"
            >
              <!-- 模拟浏览器顶栏 -->
              <div class="px-4 py-2 bg-slate-100 border-b border-slate-200 flex items-center justify-between text-xs text-slate-500">
                <div class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-full bg-red-400"></span>
                  <span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                  <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                  <span class="font-mono ml-2 text-[11px] text-slate-600">https://{{ siteInfo.domain }}/</span>
                </div>
                <span class="text-[11px] text-emerald-600 font-medium">100% 离线预览 · 秒级秒开</span>
              </div>
              <iframe
                :srcdoc="files['index.html']?.content || ''"
                class="w-full flex-1 border-0 bg-white"
                sandbox="allow-scripts allow-same-origin"
                title="交钥匙官网电脑端预览"
              ></iframe>
            </div>

            <!-- 手机端：375px 仿真手机框 -->
            <div
              v-else
              class="w-[375px] h-[640px] bg-slate-900 rounded-[38px] p-2.5 shadow-2xl border-4 border-slate-800 flex flex-col shrink-0 my-auto"
            >
              <!-- 手机听筒与刘海 -->
              <div class="w-28 h-4 bg-slate-800 rounded-full mx-auto mb-2 shrink-0 flex items-center justify-center">
                <div class="w-2.5 h-2.5 rounded-full bg-slate-900 mr-2"></div>
                <div class="w-8 h-1 rounded-full bg-slate-700"></div>
              </div>
              <div class="flex-1 bg-white rounded-[26px] overflow-hidden flex flex-col border border-slate-700">
                <iframe
                  :srcdoc="files['index.html']?.content || ''"
                  class="w-full h-full border-0 bg-white"
                  sandbox="allow-scripts allow-same-origin"
                  title="交钥匙官网手机端预览"
                ></iframe>
              </div>
              <!-- 底部横条 -->
              <div class="w-24 h-1 bg-slate-600 rounded-full mx-auto mt-2 shrink-0"></div>
            </div>
          </div>

          <!-- 模式 B：纯文本/代码编辑态 (行号 + textarea) -->
          <div v-else class="flex-1 flex overflow-hidden relative font-mono text-sm bg-white">
            <div
              class="w-12 bg-slate-50/80 border-r border-slate-200/80 text-slate-400 p-3 select-none text-right font-mono text-[12px] leading-relaxed overflow-hidden shrink-0"
            >
              <div v-for="n in lineCount" :key="n">{{ n }}</div>
            </div>
            <textarea
              :key="activeFileName"
              :value="activeFile?.content || ''"
              class="flex-1 p-3 text-slate-800 bg-white focus:outline-none leading-relaxed resize-none overflow-y-auto font-mono text-[13px] border-none"
              placeholder="当前文件暂无内容..."
              @input="handleUpdateContent($event.target.value)"
            ></textarea>
          </div>
        </div>

        <!-- 底部状态栏 -->
        <div class="px-3.5 py-1.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[12px] text-slate-500 select-none">
          <div class="flex items-center gap-3">
            <span class="font-medium text-slate-700">{{ activeFile ? `${activeFile.dir}/${activeFile.name}` : '未打开文件' }}</span>
            <span>共 {{ lineCount }} 行</span>
            <span>{{ (activeFile?.content || '').length }} 字符</span>
            <span class="px-1.5 py-0.5 rounded bg-slate-200/70 text-slate-600 font-medium">大模型交钥匙静态底座</span>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="activeFile?.isDirty" class="flex items-center gap-1 text-amber-700 font-medium">
              <span class="w-2 h-2 rounded-full bg-amber-500"></span>
              <span>有未保存修改</span>
            </span>
            <span v-else class="flex items-center gap-1 text-emerald-700 font-medium">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>已同步编译最新</span>
            </span>
          </div>
        </div>
      </section>

      <!-- 右栏：3 步 SOP 交付流水线 (320px) -->
      <StudioSop
        :stage-meta="STAGE_4_META"
        :current-step="currentStep"
        @proceed="handleProceed"
        @skip="handleSkip"
        @action="handleAction"
        @goto-step="handleGotoStep"
      />
    </div>

    <!-- 3. 企业底牌信息收集与微调抽屉 (从右侧滑出) -->
    <teleport to="body">
      <div
        v-if="drawerOpen"
        class="fixed inset-0 bg-slate-950/60 backdrop-blur-2xs z-[70] flex justify-end"
        @click.self="drawerOpen = false"
      >
        <div class="w-full max-w-xl h-full bg-white shadow-2xl flex flex-col overflow-hidden border-l border-slate-200">
          <!-- 抽屉头部 -->
          <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div>
              <h3 class="text-base font-bold text-slate-900">企业底牌信息核对与微调</h3>
              <p class="text-xs text-slate-500 mt-0.5">智能预填已带入 80% 核心数据，修改后点击下方重新编译即可瞬间生效</p>
            </div>
            <button
              type="button"
              class="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 flex items-center justify-center transition"
              @click="drawerOpen = false"
            >
              ×
            </button>
          </div>

          <!-- 抽屉滚动表单区域 -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-slate-700">
            <!-- 模块 1: 门面与定位 -->
            <div class="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div class="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                <i data-lucide="building" class="w-4 h-4 text-[#7c5bf5]"></i>
                <span>1. 企业门面与定位</span>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="font-medium text-slate-600 block mb-1">品牌简称</label>
                  <input
                    v-model="siteInfo.brandName"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:border-[#7c5bf5]"
                  />
                </div>
                <div>
                  <label class="font-medium text-slate-600 block mb-1">公司全称</label>
                  <input
                    v-model="siteInfo.companyName"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:border-[#7c5bf5]"
                  />
                </div>
              </div>
              <div>
                <label class="font-medium text-slate-600 block mb-1">一句话定位 (Slogan)</label>
                <input
                  v-model="siteInfo.slogan"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:border-[#7c5bf5]"
                />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="font-medium text-slate-600 block mb-1">官方服务热线</label>
                  <input
                    v-model="siteInfo.contactPhone"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:border-[#7c5bf5]"
                  />
                </div>
                <div>
                  <label class="font-medium text-slate-600 block mb-1">目标域名</label>
                  <input
                    v-model="siteInfo.domain"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:border-[#7c5bf5]"
                  />
                </div>
              </div>
            </div>

            <!-- 模块 2: 核心业务矩阵 (3 项) -->
            <div class="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div class="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                <i data-lucide="briefcase" class="w-4 h-4 text-[#7c5bf5]"></i>
                <span>2. 核心主营业务 (大模型重点抓取)</span>
              </div>
              <div v-for="(srv, sIdx) in siteInfo.services" :key="srv.id" class="p-3 bg-white rounded-lg border border-slate-200 space-y-2">
                <div class="flex items-center justify-between">
                  <span class="font-bold text-slate-800">业务 0{{ sIdx + 1 }}</span>
                  <input
                    v-model="srv.title"
                    class="px-2 py-1 bg-slate-50 border border-slate-200 rounded font-semibold text-xs w-48 text-right focus:bg-white"
                  />
                </div>
                <div>
                  <input
                    v-model="srv.desc"
                    placeholder="业务描述与交付亮点"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs focus:bg-white"
                  />
                </div>
                <div>
                  <input
                    v-model="srv.audience"
                    placeholder="适合客群画像"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-500 focus:bg-white"
                  />
                </div>
              </div>
            </div>

            <!-- 模块 3: 为什么选我们 (核心壁垒) -->
            <div class="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div class="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                <i data-lucide="shield" class="w-4 h-4 text-[#7c5bf5]"></i>
                <span>3. 核心差异化壁垒 (我们 VS 普通同行)</span>
              </div>
              <div v-for="(diff, dIdx) in siteInfo.differentiators" :key="diff.id" class="p-3 bg-white rounded-lg border border-slate-200 space-y-2">
                <div class="font-bold text-slate-800">对比项 0{{ dIdx + 1 }}: {{ diff.title }}</div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold shrink-0">我们的优势</span>
                  <input
                    v-model="diff.highlight"
                    class="flex-1 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs focus:bg-white"
                  />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] bg-red-100 text-red-800 px-1.5 py-0.5 rounded font-bold shrink-0">普通同行</span>
                  <input
                    v-model="diff.vsIndustry"
                    class="flex-1 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-500 focus:bg-white"
                  />
                </div>
              </div>
            </div>

            <!-- 模块 4: 资质与背书 -->
            <div class="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div class="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                <i data-lucide="award" class="w-4 h-4 text-[#7c5bf5]"></i>
                <span>4. 实体资质与背书证明</span>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="font-medium text-slate-600 block mb-1">统一社会信用代码</label>
                  <input
                    v-model="siteInfo.licenseCreditCode"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono"
                  />
                </div>
                <div>
                  <label class="font-medium text-slate-600 block mb-1">经营年限</label>
                  <input
                    v-model.number="siteInfo.yearsInBusiness"
                    type="number"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs"
                  />
                </div>
              </div>
              <div>
                <label class="font-medium text-slate-600 block mb-1">实体门店/办公详细地址</label>
                <input
                  v-model="siteInfo.address"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs"
                />
              </div>
            </div>

            <!-- 模块 5: 常见问答 FAQ (GEO 杀手锏) -->
            <div class="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div class="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                <i data-lucide="help-circle" class="w-4 h-4 text-[#7c5bf5]"></i>
                <span>5. 常见问答与真实解答 (FAQ · 专为大模型首推打造)</span>
              </div>
              <div v-for="(faq, fIdx) in siteInfo.faqs" :key="faq.id" class="p-3 bg-white rounded-lg border border-slate-200 space-y-2">
                <div class="flex items-center justify-between">
                  <span class="font-bold text-slate-800">问答 0{{ fIdx + 1 }}</span>
                  <span class="text-[10px] text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{{ faq.source }}</span>
                </div>
                <div>
                  <input
                    v-model="faq.question"
                    placeholder="客户与大模型提问"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded font-semibold text-xs focus:bg-white"
                  />
                </div>
                <div>
                  <textarea
                    v-model="faq.answer"
                    rows="2"
                    placeholder="权威标准解答"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs focus:bg-white resize-none"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>

          <!-- 抽屉底部操作条 -->
          <div class="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
            <button
              type="button"
              class="px-3 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-medium transition cursor-pointer"
              @click="handleResetSiteInfo"
            >
              重置为智能预填
            </button>
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="px-4 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition cursor-pointer"
                @click="drawerOpen = false"
              >
                取消
              </button>
              <button
                type="button"
                class="px-5 py-2 rounded-lg bg-[#7c5bf5] hover:bg-[#6846e3] text-white text-xs font-bold transition shadow-sm flex items-center gap-1.5 cursor-pointer"
                @click="onSaveDrawerAndCompile"
              >
                <i data-lucide="sparkles" class="w-4 h-4"></i>
                <span>保存并重新编译整站</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 4. 麦肯锡认知与避坑手册抽屉 -->
    <MckinseyDrawer
      :visible="mckinseyVisible"
      :title="STAGE_4_META.mckinsey.title"
      :value-desc="STAGE_4_META.mckinsey.valueDesc"
      :value-business="STAGE_4_META.mckinsey.valueBusiness"
      :what-title="STAGE_4_META.mckinsey.whatTitle"
      :what-desc="STAGE_4_META.mckinsey.whatDesc"
      :why-title="STAGE_4_META.mckinsey.whyTitle"
      :why-desc="STAGE_4_META.mckinsey.whyDesc"
      :how-title="STAGE_4_META.mckinsey.howTitle"
      :how-steps="STAGE_4_META.mckinsey.howSteps"
      @close="mckinseyVisible = false"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, watch } from 'vue';
import StageHeader from './components/StageHeader.vue';
import StudioFileTree from './components/studio/StudioFileTree.vue';
import StudioSop from './components/studio/StudioSop.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import { useStep4 } from './useStep4.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  STAGE_4_META,
  siteInfo,
  files,
  activeCategory,
  activeFileName,
  activeFile,
  openTabs,
  currentStep,
  isHeaderCollapsed,
  mckinseyVisible,
  fullscreenVisible,
  drawerOpen,
  isCompiling,
  notes,
  viewportMode,
  dualViewMode,
  handleSelectTab,
  handleCloseTab,
  handleToggleCategory,
  handleOpenFile,
  handleUpdateContent,
  handleSaveActiveFile,
  handleSaveNotes,
  handleGotoStep,
  handleProceed,
  handleSkip,
  handleAction,
  handleCompile,
  handleOpenPureSite,
  handleCopyNginx,
  handleCopyContent,
  handleExportZip,
  handleResetSiteInfo,
  handleRenameFile,
} = useStep4(props.bridge?.projectData || {});

const lineCount = computed(() => {
  const content = activeFile.value?.content || '';
  return content ? content.split('\n').length : 1;
});

function onSaveDrawerAndCompile() {
  drawerOpen.value = false;
  handleCompile();
}

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

watch([activeFileName, dualViewMode, viewportMode, drawerOpen, currentStep], () => {
  refreshIcons();
});

onMounted(() => {
  refreshIcons();
});
</script>
