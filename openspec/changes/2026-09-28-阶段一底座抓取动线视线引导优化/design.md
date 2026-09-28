# Design: 2026-09-28-阶段一底座抓取动线视线引导优化

## Architecture (架构设计与对象关系)

### 1. 动线状态机模型 (Delivery Step State Machine)
- **当前现状**：
  动线状态仅维护 `currentStep: number`，每个步骤内部的 `action` 按钮仅执行派发事件，缺乏步骤内的“微状态（Micro State）”，导致动作执行后界面无状态留存。
- **演进设计**：
  为动线卡片注入步骤内动作就绪态 `stepActionStates: Record<string, boolean>`：
  - `crawledMetrics: boolean`：标记“真抓网络底座指标”是否已完成抓取。
  - 当 `crawledMetrics === true` 时，触发两项视图派生：
    1. 动作按钮渲染为已就绪态（文案变更为“已抓取真实指标（可重新抓取）”，采用翠绿轻量高亮）。
    2. 主推进按钮进入引导焦点态（添加 `animate-pulse` 或柔和呼吸光晕，并在上方显示引导标签“👉 指标已就绪，请核验后点击进入出初稿”）。

## Interface (组件属性与事件设计)

### 1. `StudioSop.vue` 动线组件
- **新增属性 Props**：
  ```ts
  // 步骤内微动作完成态字典，如 { crawlMetrics: true }
  actionCompletedMap: {
    type: Object,
    default: () => ({})
  }
  ```
- **视图渲染逻辑**：
  - 动作按钮：
    ```html
    <button
      :class="isActionDone(step.action.type) ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-[#7c5bf5]/10 text-[#7c5bf5] border-[#7c5bf5]/30'"
    >
      <i :data-lucide="isActionDone(step.action.type) ? 'check-circle' : step.action.icon"></i>
      <span>{{ isActionDone(step.action.type) ? (step.action.completedLabel || '重新' + step.action.label) : step.action.label }}</span>
    </button>
    ```
  - 主推进按钮上方引导文案与高亮动效：
    ```html
    <div v-if="shouldHighlightProceed(step)" class="text-[11px] text-[#7c5bf5] font-semibold text-center animate-bounce">
      👇 数据已抓取就绪，请核对中栏并点击下方继续
    </div>
    ```

### 2. `stage1Config.js` 配置规范
- 在 Step 1 的 action 中补充配置：
  ```js
  action: {
    label: '真抓网络底座指标',
    completedLabel: '已抓取真实指标 (点击重新抓取)',
    icon: 'activity',
    type: 'crawlMetrics',
  }
  ```

### 3. `useStep1.js` 状态流
- `crawledMetrics = ref(savedState?.crawledMetrics || false)`
- 在 `handleAction('crawlMetrics')` 中：
  - `crawledMetrics.value = true;`
  - `saveState();`
  - 派发升级版 Toast：“底座指标已抓取完毕！请核对中栏数据，核验后点击下方【前往出具初稿】”。

## Database Schema / Data Structure (数据模型变更)
- **本地存储**：在 `localStorage.getItem('nextgeo_step1_state_v1')` 的 JSON 中增加持久化字段 `crawledMetrics: boolean`。
- **无数据库改动**：纯前端交互动线优化，不涉及 MySQL 库表与后端 API 改造。
