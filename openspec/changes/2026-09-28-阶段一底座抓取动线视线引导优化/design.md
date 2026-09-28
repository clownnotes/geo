# Design: 阶段一底座抓取动线视线引导优化

## Architecture (架构设计与对象关系)

### 1. 动线状态机模型 (Delivery Step State Machine)
- **当前现状**：
  动线状态仅维护 `currentStep: number`，每个步骤内部的 `action` 按钮仅执行派发事件，缺乏步骤内的“微状态（Micro State）”，导致动作执行后界面无状态留存。
- **演进设计**：
  为动线卡片注入步骤内动作就绪态 `stepActionStates: Record<string, boolean>`：
  - `crawledMetrics: boolean`：标记“真抓网络底座指标”是否已完成抓取。
  - 当 `crawledMetrics === true` 时，触发两项视图派生：
    1. 动作按钮渲染为已就绪态（文案变更为“已抓取真实指标 (点击重新抓取)”，采用浅绿 `bg-emerald-50 text-emerald-700 border-emerald-200`，严格杜绝彩色 Emoji）。
    2. 主推进按钮进入引导焦点态（添加 `animate-pulse` 柔和呼吸光晕，并在上方显示静态引导标签“指标已抓取就绪，请核对中栏并点击下方继续”，严格杜绝 `animate-bounce` 弹跳等低幼感动效）。

### 2. 状态传递拓扑与防污染边界
```
[useStep1] (生产: crawledMetrics 响应式状态与 saveState 持久化)
    ↓
[Step1App.vue] (胶水层: 解构出 crawledMetrics 并组装字典)
    ↓ :action-completed-map="{ crawlMetrics: crawledMetrics }"
[StudioSop.vue] (呈现层: 共享组件，防污染校验)
```
- **防污染边界原则**：`StudioSop.vue` 被 4 个阶段（Step 0/1/2/3）共享。阶段 0/2/3 未传入 `actionCompletedMap`（取默认 `{}`），组件内部所有动作完成判断与高亮判断短路返回 `false`，确保其它阶段保持零侵入、零污染。

---

## Interface (组件属性与接口设计)

### 1. `StudioSop.vue` 动线组件
- **Props 扩展**：
  ```ts
  actionCompletedMap: {
    type: Object,
    default: () => ({}),
  }
  ```
- **核心辅助函数防污染实现**：
  ```js
  // 动作是否已完成（安全校验空值与字典）
  function isActionDone(type) {
    if (!type || !props.actionCompletedMap) return false;
    return !!props.actionCompletedMap[type];
  }

  // 是否高亮主推进按钮（必须同时满足：动作已完成 且 为当前进行中的步骤）
  function shouldHighlightProceed(step, idx) {
    if (!step?.action?.type) return false;
    if (idx + 1 !== props.currentStep) return false;
    return isActionDone(step.action.type);
  }
  ```
- **模板视图渲染**：
  - **动作按钮**（沿用组件既有已完成 emerald 语义，使用标准 Lucide 图标）：
    ```html
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
    ```
  - **主推进按钮上方静态辅助提示与呼吸高亮**（杜绝彩色 Emoji 与弹跳动效）：
    ```html
    <div
      v-if="shouldHighlightProceed(step, idx)"
      class="text-[11px] text-[#7c5bf5] font-semibold text-center py-0.5"
    >
      指标已抓取就绪，请核对中栏并点击下方继续
    </div>

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
    ```

### 2. `Step1App.vue` 胶水层连接
- 解构 `crawledMetrics`：
  ```js
  const {
    // ...既有解构项...
    crawledMetrics,
  } = useStep1();
  ```
- 绑定到 `<StudioSop>`：
  ```html
  <StudioSop
    :stage-meta="stageMeta"
    :current-step="currentStep"
    :gate="gate"
    :action-completed-map="{ crawlMetrics: crawledMetrics }"
    @action="handleAction"
    @proceed="handleProceed"
    @skip="handleSkip"
    @gotoStep="handleGotoStep"
    @notes-save="handleNotesSave"
  />
  ```

### 3. `stage1Config.js` 动作配置
- 在第 1 步的 action 中补充 `completedLabel`：
  ```js
  action: {
    label: '真抓网络底座指标',
    completedLabel: '已抓取真实指标 (点击重新抓取)',
    icon: 'activity',
    type: 'crawlMetrics',
  }
  ```

### 4. `useStep1.js` 状态流与真实持久化
- 初始化响应式标记：
  ```js
  const crawledMetrics = ref(savedState?.crawledMetrics || false);
  ```
- 真实持久化逻辑（在 `saveState()` 中）：
  ```js
  function saveState() {
    const stateToSave = {
      currentStep: currentStep.value,
      activeFileName: activeFileName.value,
      openTabs: openTabs.value,
      gate: gate.value,
      notes: notes.value,
      files: files.value,
      crawledMetrics: crawledMetrics.value, // 新增持久化字段
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(stateToSave)); // storageKey 为 `geo_step1_state_${clientId}`
    } catch (e) {
      console.warn('Failed to save state to localStorage', e);
    }
  }
  ```
- 在 `handleAction('crawlMetrics')` 中置为 `true` 并更新 Toast 引导（无 Emoji）：
  ```js
  if (actionType === 'crawlMetrics') {
    crawledMetrics.value = true;
    handleSelectTab('01_网络底座指标_待对照.md');
    saveState();
    showStudioToast('已完成抓取：真实底座指标已就绪！请核对中栏数据，确认无误后点击下方【前往出具初稿】');
  }
  ```

---

## Database Schema / Data Structure (数据模型变更)
- **本地存储持久化**：在 `useStep1.js` 的 `saveState()` 中新增 `crawledMetrics: boolean` 字段，写入真实存储键 `` `geo_step1_state_${clientId}` ``。
- **无数据库表改动**：纯前端动线指引增强，不涉及后端数据库与 API 结构变更。
