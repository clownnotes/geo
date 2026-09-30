<template>
  <!-- [2026-09-29] [阶段二 3 竖列工作区] 客户素材资产管理库专属工作台 -->
  <div class="space-y-4">
    <!-- 1. 顶部阶段概览看板 -->
    <StageHeader
      id="step2-header-card"
      :stage-title="STAGE_2_META.name"
      :mode-tag="STAGE_2_META.tag"
      :is-ready="currentStep >= 5 && assetsHealth >= 80"
      :target-text="STAGE_2_META.target"
      :notes="notes"
      :notes-placeholder="STAGE_2_META.notesPlaceholder"
      :collapsed="isHeaderCollapsed"
      @update:notes="notes = $event"
      @save-notes="handleSaveNotes"
      @open-mckinsey="mckinseyVisible = true"
    />

    <!-- 2. 主区域：IDE 3 竖列专业交付工作台 (左素材资源树 + 中资产管理打磨区 + 右 SOP 动线) -->
    <div class="flex gap-4 items-stretch flex-col lg:flex-row h-[780px] min-h-[660px]">
      <!-- 左栏：素材资产文件树 (260px) -->
      <StudioFileTree
        :categories="STAGE_2_META.categories"
        :files="files"
        :active-category="activeCategory"
        :active-file-name="activeFileName"
        :allow-new-file="false"
        :allow-refresh="true"
        :stage="'step2'"
        :show-status-badge="false"
        @toggle-category="handleToggleCategory"
        @open-file="handleOpenFile"
        @refresh-files="handleInitSources"
        @rename-file="handleRenameFile"
      />

      <!-- 中间：素材资产结构化卡片与源码打磨工作区 -->
      <section class="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden relative">
        <!-- [2026-09-30] [师弟定规 · 盖板工作台] 沉浸式盖板蒸馏工作台 (覆盖中区，左侧树保持常驻) -->
        <DistillSheet
          v-if="isDistillSheetOpen"
          :mode="distillMode"
          :initial-url="crawlingUrl"
          :initial-text="rawMaterialDraft"
          :files="files"
          :client-id="ctx.clientId || 'nextgeo'"
          :brand="ctx.brand || '邻里GEO'"
          :city="ctx.city || '徐州'"
          :category="ctx.category || 'GEO 优化'"
          :competitor="ctx.competitor || '区域竞品同行'"
          @close="closeDistillSheet"
          @update:draft-text="handleUpdateRawDraft"
          @adopt-chunk="handleAdoptDistillChunk"
          @toast="showDistillToast"
        />

        <template v-else>
          <!-- [2026-09-29] 引入通用双行工作台头部组件 (StudioHeader)，彻底消灭第一排挤扁变形 -->
          <StudioHeader
            :files="files"
            :open-tabs="openTabs"
            :active-file-name="activeFileName"
            stage="step2"
            @select-tab="handleSelectTab"
            @close-tab="handleCloseTab"
          >
            <template #actions>
              <!-- 快捷呼出盖板按钮 -->
              <button
                type="button"
                class="px-2.5 py-1 bg-[#7c5bf5]/10 hover:bg-[#7c5bf5]/20 text-[#7c5bf5] border border-[#7c5bf5]/30 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                title="呼出网页蒸馏大盖板"
                @click="openDistillSheet('web')"
              >
                <i data-lucide="globe" class="w-3.5 h-3.5"></i>
                <span>网页蒸馏</span>
              </button>
              <button
                type="button"
                class="px-2.5 py-1 bg-[#7c5bf5]/10 hover:bg-[#7c5bf5]/20 text-[#7c5bf5] border border-[#7c5bf5]/30 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                title="呼出文案蒸馏大盖板"
                @click="openDistillSheet('text')"
              >
                <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
                <span>文案蒸馏</span>
              </button>

              <!-- 视图模式切换 -->
              <div class="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100 text-xs">
              <button
                type="button"
                class="px-2.5 py-0.5 rounded font-medium transition cursor-pointer flex items-center gap-1"
                :class="viewMode !== 'source' ? 'bg-white text-[#7c5bf5] shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
                @click="viewMode = 'draft'"
              >
                <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                <span>素材采集与蒸馏工作台</span>
              </button>
              <button
                type="button"
                class="px-2.5 py-0.5 rounded font-medium transition cursor-pointer flex items-center gap-1"
                :class="viewMode === 'source' ? 'bg-white text-[#7c5bf5] shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'"
                @click="viewMode = 'source'"
              >
                <i data-lucide="file-code" class="w-3.5 h-3.5"></i>
                <span>Markdown源码</span>
              </button>
            </div>

            <button
              type="button"
              class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              title="一键复制当前文件内容"
              @click="handleCopyContent"
            >
              <i data-lucide="copy" class="w-3.5 h-3.5 text-slate-500"></i>
              <span>复制内容</span>
            </button>
            <button
              type="button"
              class="px-2.5 py-1 bg-[#7c5bf5] hover:bg-[#6a48e6] text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition shadow-xs cursor-pointer"
              title="保存当前文件"
              @click="handleSaveActiveFile"
            >
              <i data-lucide="save" class="w-3.5 h-3.5"></i>
              <span>保存修改</span>
            </button>
          </template>
        </StudioHeader>

        <!-- 中栏主体内容区 (上下同屏平铺 · 网页蒸馏与文案蒸馏常驻主视觉) -->
        <div v-if="viewMode !== 'source'" class="flex-1 min-h-0 flex flex-col relative bg-slate-50/50 overflow-y-auto p-3 space-y-4">
          <!-- 核心工作区 1：网页骨架蒸馏与文案打磨大文字稿 (常驻主视觉 · 绝不隐藏) -->
          <div class="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <!-- 场景一：网页骨架蒸馏（一键抓取官网） -->
            <div class="space-y-1.5 pb-2.5 border-b border-slate-100">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="globe" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-xs">【网页蒸馏】输入网址一键提取官网/展示页纯净骨架</span>
                </div>
                <span class="text-[11px] text-slate-400">自动过滤样式，提纯至大文字稿</span>
              </div>
              <div class="flex items-center gap-2">
                <input
                  v-model="crawlingUrl"
                  type="text"
                  placeholder="输入客户官网、美团商户页、微信公众号或展示页网址..."
                  class="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:border-[#7c5bf5] outline-none"
                />
                <button
                  type="button"
                  class="px-3.5 py-1.5 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shrink-0"
                  @click="openDistillSheet('web')"
                >
                  <i data-lucide="download-cloud" class="w-3.5 h-3.5"></i>
                  <span>进入网页蒸馏大盖板 →</span>
                </button>
              </div>
            </div>

            <!-- 场景二：文案蒸馏与打磨工作台（大文字稿 · 8500字安全线） -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="file-text" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-xs">【文案蒸馏】直接打字修饰 / 粘贴客户微信口述、合同折页材料</span>
                </div>
                <!-- 字数与限额提醒 (8500字硬限) -->
                <div class="flex items-center gap-2 text-xs">
                  <span
                    class="font-mono px-2 py-0.5 rounded font-medium transition"
                    :class="isDraftOverLimit ? 'bg-amber-100 text-amber-700 font-bold border border-amber-300' : 'bg-slate-100 text-slate-600'"
                  >
                    当前字数：{{ draftCharCount }} / 8500 汉字 (8K Token 本地大模型安全线)
                  </span>
                  <span v-if="isDraftOverLimit" class="text-amber-700 text-[11px] font-bold">
                    [超限提醒] 已超过 8500 字，请删减无用段落，否则大模型将拒绝蒸馏处理！
                  </span>
                </div>
              </div>

              <!-- 大文本编辑器主体 -->
              <textarea
                :value="rawMaterialDraft"
                placeholder="在此直接粘贴客户微信聊天记录、企业宣传折页、合同片段或历史老文档；也可点击上方网址一键蒸馏抓取。您可在此自由打字修改、补充细节或删减废话。字数请控制在 8500 汉字以内，完成后点击右下角【AI 智能语义切块与蒸馏 →】..."
                class="w-full p-3 font-mono text-xs rounded-lg border border-slate-200 focus:border-[#7c5bf5] focus:ring-1 focus:ring-[#7c5bf5] outline-none resize-none leading-relaxed min-h-[160px]"
                rows="6"
                @input="handleUpdateRawDraft($event.target.value)"
              ></textarea>

              <!-- 底部操作条 -->
              <div class="flex items-center justify-between pt-1 text-xs">
                <div class="flex items-center gap-2">
                  <button
                    v-if="rawMaterialDraft"
                    type="button"
                    class="text-slate-400 hover:text-red-600 cursor-pointer text-xs"
                    @click="handleUpdateRawDraft('')"
                  >
                    清空文字稿
                  </button>
                  <span class="text-[11px] text-slate-400">（修改即自动实时存盘）</span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="px-4 py-2 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
                    @click="openDistillSheet('text')"
                  >
                    <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                    <span>进入文案蒸馏大盖板 →</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 核心工作区 2：6 大黄金分类卡片 (分拣结果或卡片档案查看) -->
          <div class="space-y-4">
            <!-- S1: 企业主体与法定边界卡片 -->
            <div
              v-if="activeCategory === 'source_identity' || (activeFileName || '').startsWith('S1_')"
              class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="building" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-sm">分类 1 · 主体与法定边界结构化卡片 (S1)</span>
                </div>
                <button
                  type="button"
                  class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                  @click="syncFormToMarkdown('source_identity')"
                >
                  <i data-lucide="check" class="w-3.5 h-3.5"></i>
                  <span>同步并保存 S1</span>
                </button>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <label class="block font-medium text-slate-700 mb-1">企业规范全称</label>
                  <input
                    v-model="s1Form.companyName"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">品牌对外简称</label>
                  <input
                    v-model="s1Form.brandName"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">统一社会信用代码</label>
                  <input
                    v-model="s1Form.licenseCreditCode"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg font-mono focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">全国客服专线</label>
                  <input
                    v-model="s1Form.phone"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div class="md:col-span-2">
                  <label class="block font-medium text-slate-700 mb-1">法定注册与实体经营地址</label>
                  <input
                    v-model="s1Form.address"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div class="md:col-span-2">
                  <label class="block font-medium text-slate-700 mb-1">坚决不做的负面清单（避免大模型越权瞎承诺）</label>
                  <textarea
                    v-model="s1Form.negativeList"
                    rows="2"
                    class="w-full p-2 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none resize-none"
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- S2: 核心产品与价格承诺卡片 -->
            <div
              v-else-if="activeCategory === 'source_products' || (activeFileName || '').startsWith('S2_')"
              class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="tag" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-sm">分类 2 · 产品与价格标准结构化卡片 (S2)</span>
                </div>
                <button
                  type="button"
                  class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                  @click="syncFormToMarkdown('source_products')"
                >
                  <i data-lucide="check" class="w-3.5 h-3.5"></i>
                  <span>同步并保存 S2</span>
                </button>
              </div>

              <div class="space-y-3 text-xs">
                <div>
                  <label class="block font-medium text-slate-700 mb-1">核心业务主营定调</label>
                  <input
                    v-model="s2Form.category"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">明码标价公开标准（起步价与区间）</label>
                  <input
                    v-model="s2Form.pricing"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">标准交付流程链路</label>
                  <input
                    v-model="s2Form.process"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">交付源码与数据归属约定</label>
                  <input
                    v-model="s2Form.ownership"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">明确不承诺的结果（打消客户不合理预期）</label>
                  <input
                    v-model="s2Form.unpromised"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
              </div>
            </div>

            <!-- S3: 客户画像与痛点场景卡片 -->
            <div
              v-else-if="activeCategory === 'source_scenarios' || (activeFileName || '').startsWith('S3_')"
              class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="users" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-sm">分类 3 · 客户画像与痛点场景卡片 (S3)</span>
                </div>
                <button
                  type="button"
                  class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                  @click="syncFormToMarkdown('source_scenarios')"
                >
                  <i data-lucide="check" class="w-3.5 h-3.5"></i>
                  <span>同步并保存 S3</span>
                </button>
              </div>

              <div class="space-y-3 text-xs">
                <div>
                  <label class="block font-medium text-slate-700 mb-1">主要服务目标客户人群</label>
                  <input
                    v-model="s3Form.targetAudience"
                    type="text"
                    class="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none"
                  />
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">客户决策与触发时机</label>
                  <textarea
                    v-model="s3Form.triggerTiming"
                    rows="2"
                    class="w-full p-2 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none resize-none"
                  ></textarea>
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">客户当前核心痛点与替代方案缺陷</label>
                  <textarea
                    v-model="s3Form.painPoints"
                    rows="2"
                    class="w-full p-2 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none resize-none"
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- S4: 同行对标与参数对比卡片（支持增删竞品） -->
            <div
              v-else-if="activeCategory === 'source_competitors' || (activeFileName || '').startsWith('S4_')"
              class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="swords" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-sm">分类 4 · 同行策略与参数对比卡片 (S4)</span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                    @click="handleAddCompetitor"
                  >
                    <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                    <span>添加对标竞品</span>
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                    @click="syncFormToMarkdown('source_competitors')"
                  >
                    <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    <span>同步并保存 S4</span>
                  </button>
                </div>
              </div>

              <!-- 竞品卡片列表 -->
              <div class="space-y-3">
                <div
                  v-for="(comp, idx) in s4Competitors"
                  :key="idx"
                  class="p-3 bg-slate-50/70 rounded-lg border border-slate-200 space-y-2 text-xs"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-700">对标竞品 #{{ idx + 1 }}</span>
                    <button
                      v-if="s4Competitors.length > 1"
                      type="button"
                      class="text-red-500 hover:text-red-700 text-[11px]"
                      @click="s4Competitors.splice(idx, 1)"
                    >
                      删除该竞品
                    </button>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div>
                      <label class="block text-slate-500 text-[11px] mb-0.5">竞品名称</label>
                      <input
                        v-model="comp.name"
                        type="text"
                        class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded text-xs outline-none"
                      />
                    </div>
                    <div>
                      <label class="block text-slate-500 text-[11px] mb-0.5">竞品交付形式</label>
                      <input
                        v-model="comp.form"
                        type="text"
                        class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded text-xs outline-none"
                      />
                    </div>
                    <div>
                      <label class="block text-slate-500 text-[11px] mb-0.5">竞品可见度现状 (大模型)</label>
                      <input
                        v-model="comp.sov"
                        type="text"
                        class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded text-xs outline-none"
                      />
                    </div>
                    <div>
                      <label class="block text-slate-500 text-[11px] mb-0.5">收费套路对比</label>
                      <input
                        v-model="comp.pricing"
                        type="text"
                        class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded text-xs outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- S5: 真实故事化案例库（支持增删案例） -->
            <div
              v-else-if="activeCategory === 'source_cases' || (activeFileName || '').startsWith('S5_')"
              class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="book-open" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-sm">分类 5 · 真实故事化案例库 (S5)</span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                    @click="handleAddCase"
                  >
                    <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                    <span>添加故事案例</span>
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                    @click="syncFormToMarkdown('source_cases')"
                  >
                    <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    <span>同步并保存 S5</span>
                  </button>
                </div>
              </div>

              <!-- 案例卡片列表 -->
              <div class="space-y-3">
                <div
                  v-for="(cs, idx) in s5Cases"
                  :key="idx"
                  class="p-3 bg-slate-50/70 rounded-lg border border-slate-200 space-y-2 text-xs"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-700">故事案例 #{{ idx + 1 }}</span>
                    <button
                      v-if="s5Cases.length > 1"
                      type="button"
                      class="text-red-500 hover:text-red-700 text-[11px]"
                      @click="s5Cases.splice(idx, 1)"
                    >
                      删除该案例
                    </button>
                  </div>
                  <div>
                    <label class="block text-slate-500 text-[11px] mb-0.5">案例标题 / 逆袭成效</label>
                    <input
                      v-model="cs.title"
                      type="text"
                      class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded text-xs outline-none"
                    />
                  </div>
                  <div>
                    <label class="block text-slate-500 text-[11px] mb-0.5">客户经营背景与初态困境</label>
                    <textarea
                      v-model="cs.background"
                      rows="2"
                      class="w-full p-2 bg-white border border-slate-200 rounded text-xs outline-none resize-none"
                    ></textarea>
                  </div>
                  <div>
                    <label class="block text-slate-500 text-[11px] mb-0.5">实施行动措施 (普林斯顿语料与/llms.txt)</label>
                    <textarea
                      v-model="cs.action"
                      rows="2"
                      class="w-full p-2 bg-white border border-slate-200 rounded text-xs outline-none resize-none"
                    ></textarea>
                  </div>
                  <div>
                    <label class="block text-slate-500 text-[11px] mb-0.5">真实量化成果 (首推率/线索增幅)</label>
                    <input
                      v-model="cs.result"
                      type="text"
                      class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded text-xs outline-none"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- S6: 权威背书与资质凭据卡片 -->
            <div
              v-else-if="activeCategory === 'source_credentials' || (activeFileName || '').startsWith('S6_')"
              class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="p-1 rounded bg-[#7c5bf5]/10 text-[#7c5bf5]">
                    <i data-lucide="shield-check" class="w-4 h-4"></i>
                  </span>
                  <span class="font-bold text-slate-800 text-sm">分类 6 · 权威凭据与背书档案卡片 (S6)</span>
                </div>
                <button
                  type="button"
                  class="px-3 py-1 bg-[#7c5bf5] hover:bg-[#6846e3] text-white rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer"
                  @click="syncFormToMarkdown('source_credentials')"
                >
                  <i data-lucide="check" class="w-3.5 h-3.5"></i>
                  <span>同步并保存 S6</span>
                </button>
              </div>

              <div class="space-y-3 text-xs">
                <div>
                  <label class="block font-medium text-slate-700 mb-1">国家标准与资质认证清单</label>
                  <textarea
                    v-model="s6Form.standards"
                    rows="3"
                    class="w-full p-2 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none font-mono resize-none leading-relaxed"
                  ></textarea>
                </div>
                <div>
                  <label class="block font-medium text-slate-700 mb-1">真实服务合同条款佐证 (已脱敏凭据)</label>
                  <textarea
                    v-model="s6Form.contracts"
                    rows="3"
                    class="w-full p-2 border border-slate-200 rounded-lg focus:border-[#7c5bf5] outline-none font-mono resize-none leading-relaxed"
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- 默认未匹配提示 -->
            <div v-else class="p-4 text-center text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
              请在左侧文件树选择 S1~S6 分类素材文件查看或修改细节卡片
            </div>
          </div>
        </div>

        <!-- 2. Markdown 源码打磨编辑器主体 (仅在切换为 source 模式时展示) -->
        <div v-else class="flex-1 min-h-0 flex flex-col p-3">
          <div class="flex-1 bg-white rounded-lg border border-slate-200 shadow-2xs flex flex-col overflow-hidden">
            <div class="bg-slate-50/80 px-3 py-1.5 border-b border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span class="font-mono text-slate-700 truncate max-w-[300px]">
                {{ activeFileName || '未打开文件' }}
              </span>
              <span class="text-[11px] text-slate-400">
                {{ activeFile?.content ? activeFile.content.split('\n').length : 0 }} 行 · Markdown 高保真纯文本
              </span>
            </div>
            <textarea
              :value="activeFile?.content || ''"
              class="flex-1 p-4 font-mono text-xs text-slate-800 bg-white resize-none outline-none leading-relaxed overflow-y-auto"
              placeholder="在此查看或编辑内容..."
              @input="handleUpdateContent($event.target.value)"
            ></textarea>
          </div>
        </div>
      </template>
    </section>

      <!-- 右栏：SOP 交付动线流水线 (320px) -->
      <StudioSop
        :stage-meta="STAGE_2_META"
        :current-step="currentStep"
        :expand-all="true"
        @goto-step="handleGotoStep"
        @proceed="handleProceed"
        @skip="handleSkip"
        @action="handleAction"
      />
    </div>

    <!-- 3. 抽屉与模态层 (麦肯锡认知手册) -->
    <MckinseyDrawer
      v-if="STAGE_2_META.mckinsey"
      :visible="mckinseyVisible"
      :mckinsey-data="STAGE_2_META.mckinsey"
      @close="mckinseyVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue';
import StageHeader from './components/StageHeader.vue';
import StudioFileTree from './components/studio/StudioFileTree.vue';
import StudioHeader from './components/studio/StudioHeader.vue';
import StudioSop from './components/studio/StudioSop.vue';
import DistillSheet from './components/studio/DistillSheet.vue';
import MckinseyDrawer from './components/MckinseyDrawer.vue';
import { useStep2 } from './useStep2.js';

const props = defineProps({
  bridge: { type: Object, default: () => ({}) },
});

const {
  ctx,
  STAGE_2_META,
  CATEGORY_DIR_MAP,
  files,
  viewMode,
  activeCategory,
  activeFileName,
  activeFile,
  openTabs,
  currentStep,
  isHeaderCollapsed,
  mckinseyVisible,
  notes,
  assetsHealth,
  crawlingUrl,
  isScraping,
  sortingText,
  isSorting,
  showSorterCard,
  s1Form,
  s2Form,
  s3Form,
  s4Competitors,
  s5Cases,
  s6Form,
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
  handleCopyContent,
  handleScrapeWebsite,
  handleDistributeSources,
  syncFormToMarkdown,
  handleAddCompetitor,
  handleAddCase,
  handleInitSources,
  // [2026-09-30] [师弟定规 · 盖板工作台] 引入盖板状态与操作
  isDistillSheetOpen,
  distillMode,
  openDistillSheet,
  closeDistillSheet,
  handleAdoptDistillChunk,
  // 核心大文字稿与编辑状态
  rawMaterialDraft,
  draftCharCount,
  isDraftOverLimit,
  handleUpdateRawDraft,
  handleRenameFile,
} = useStep2(props.bridge?.projectData || {});

function showDistillToast(evt) {
  const msg = evt?.message || evt;
  const type = evt?.type || 'info';
  if (typeof window !== 'undefined' && window.showToast) {
    window.showToast(msg, type);
  }
}

function refreshIcons() {
  nextTick(() => {
    if (typeof window !== 'undefined' && window.lucide) {
      window.lucide.createIcons();
    }
  });
}

watch([activeFileName, viewMode, currentStep, showSorterCard, isScraping, isSorting, isDistillSheetOpen], () => {
  refreshIcons();
});

onMounted(() => {
  refreshIcons();
});
</script>
