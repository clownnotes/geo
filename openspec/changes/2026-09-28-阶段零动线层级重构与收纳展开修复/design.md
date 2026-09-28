# Design: 阶段零动线层级重构与收纳展开交互修复

## 1. 架构对象模型与层级三问

针对用户界面的组织结构，确立清晰的三层面向对象关系：

| 层级 | 对象名称 (Entity) | 所属界面区域 | 核心职责与行为 |
|---|---|---|---|
| **第一级 (L1)** | 阶段大步骤 (Stage) | 左侧主导航菜单顶层 (如 `00 去豆包提问拿现状`) | 承载业务全局里程碑，展开/折叠二级子菜单 |
| **第二级 (L2)** | 交付子步骤/页面 (SubStep) | 左侧次级导航菜单 (如 `0.1 准备题目`、`0.2 网页提问拿答案`) | 确定当前工作台的上下文、资源管理器文件类别及编辑主题 |
| **第三级 (L3)** | 交付动线微操作 (MicroAction) | 右侧动线面板 (`StudioSop.vue`) | 指引交付专家在**当前二级页面**内部完成具体的作业动作，不跨页跳转 |

---

## 2. 动线数据模型设计与契约保持

### 2.1 契约保持原则 (SSOT)
`StudioSop.vue` 是一个被 `Step0App.vue`、`Step1App.vue`、`Step2App.vue`、`Step3App.vue` 4 个阶段共同复用的通用组件。
**严禁从模板中物理删除主推进按钮**，否则阶段 1/2/3 将失去唯一的前进与通关入口。

### 2.2 `StudioSop.vue` 条件渲染设计
在 `StudioSop.vue` 中保持现有 `props.stageMeta` 统一通道，仅对推进按钮增加条件判断：
```html
<!-- 主推进按钮：仅在未声明 hideProceed 且存在 nextLabel 时渲染 -->
<button
  v-if="!step.hideProceed && step.nextLabel"
  type="button"
  class="w-full py-2.5 rounded-lg text-white text-[14px] font-bold transition flex items-center justify-center gap-1.5 shadow cursor-pointer"
  :class="isProceedDisabled(step) ? 'bg-slate-300 cursor-not-allowed text-slate-500 shadow-none' : 'bg-[#7c5bf5] hover:bg-[#6846e3]'"
  :disabled="isProceedDisabled(step)"
  @click.stop="onProceedClick(step, idx)"
>
  <span>{{ step.nextLabel }}</span>
  <i data-lucide="arrow-right" class="w-4 h-4"></i>
</button>
```
当 `step.hideProceed === true` 时，该大按钮自动隐藏，并在面板底部展示轻量指引：
```html
<div v-if="step.hideProceed" class="p-2.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-400 text-center">
  提示：本小节工作完成后，可直接在左侧菜单切换至下一项
</div>
```

### 2.3 `Step0App.vue` 动线数据下发规范
`Step0App.vue` 依据当前响应式变量 `currentSubStep.value`（1 或 2），计算对应的 `currentStageMeta` 并下发给 `<StudioSop :stage-meta="currentStageMeta" ... />`：

#### 2.3.1 `0.1 准备题目` 专属三级动线定义
```javascript
const STAGE0_SUB1_META = {
  sopTitle: '0.1 准备题目动线',
  sopSteps: [
    {
      id: 'view_or_refresh',
      name: '1. AI 出题与查看',
      desc: '系统已根据客户定位预生成核心题。若需换一批，可点击下方重新出题。',
      extraAction: { label: '重新出题（生成新版）', icon: 'sparkles', type: 'refreshQuestions' },
      hideProceed: true
    },
    {
      id: 'edit_in_editor',
      name: '2. 中间区润色打磨',
      desc: '交付专家可在中间编辑器直接润色修改，从 60 分打磨至 80 分。',
      hideProceed: true
    },
    {
      id: 'save_and_adopt',
      name: '3. 保存文件并采纳',
      desc: '题目打磨满意后，在中间工具栏点击【保存文件】，并可点击【设为客户采纳】生效为基线文件。',
      hideProceed: true
    }
  ]
};
```

#### 2.3.2 `0.2 网页提问拿答案` 专属三级动线定义
```javascript
const STAGE0_SUB2_META = {
  sopTitle: '0.2 网页提问动线',
  sopSteps: [
    {
      id: 'copy_questions',
      name: '1. 一键复制提问内容',
      desc: '点击中间编辑区的【一键复制内容】，获得打磨完毕的提问清单。',
      hideProceed: true
    },
    {
      id: 'ask_doubao_web',
      name: '2. 豆包网页版逐题提问',
      desc: '前往豆包网页版逐题提问，观察并记录 AI 推荐的服务商和排位。',
      linkAction: { label: '打开豆包网页版提问', icon: 'external-link', href: 'https://www.doubao.com' },
      hideProceed: true
    },
    {
      id: 'paste_and_save_answers',
      name: '3. 贴回实测回答并封版',
      desc: '将豆包的实测回答完整贴回中间的 02 回答记录文件，点击下方完成阶段零封版。',
      action: { label: '保存并封版完成阶段零', icon: 'check-circle-2', type: 'finishStage0' },
      hideProceed: true
    }
  ]
};
```
在 `StudioSop.vue` 的 `onActionClick` 中处理 `type === 'finishStage0'` 时，触发 `emit('finish-stage0')`，确保 `handleFinishStage0`（原封版与持久化链路）完好无损地正常执行。

---

## 3. 顶栏“收纳概览”展开 Bug 修复设计

### 3.1 根因分析
在 `web/index.html` 的 `applyStepOverviewState` 函数（真实锚点约在第 7041 行）：
直接访问了未在当前函数作用域内声明的变量 `btn`、`icon`、`text`，触发 `ReferenceError: btn is not defined`，导致执行流程中断：
1. 按钮文字未切换为“展开概览”，图标未切换；
2. `localStorage` 未能保存最新状态 `'1'`；
3. `geo-toggle-step-overview` 事件未派发；
4. 调用该函数的 `renderStep0ProbePanel` 与 `renderStep1DiagPanel` 渲染函数中断，吞掉了后续的 `lucide.createIcons()`，导致图标渲染缺失。

### 3.2 修复代码实现
在 `applyStepOverviewState` 函数内部增加标准 DOM 获取：
```javascript
function applyStepOverviewState(collapsed) {
  const cards = document.querySelectorAll('#step0-header-card, #step1-header-card, #step2-header-card, #step3-header-card, #step4-header-card, #step5-header-card, #step6-header-card');
  cards.forEach(card => {
    if (card) {
      if (collapsed) card.classList.add('hidden');
      else card.classList.remove('hidden');
    }
  });

  const btn = document.getElementById('btn-toggle-step-overview');
  const icon = document.getElementById('icon-toggle-step-overview');
  const text = document.getElementById('text-toggle-step-overview');

  if (btn) {
    if (collapsed) {
      btn.classList.add('bg-indigo-50', 'text-[#7c5bf5]', 'border-indigo-200');
      btn.classList.remove('bg-white', 'text-slate-600', 'border-slate-200');
      btn.title = '展开顶部阶段概览与备注';
    } else {
      btn.classList.remove('bg-indigo-50', 'text-[#7c5bf5]', 'border-indigo-200');
      btn.classList.add('bg-white', 'text-slate-600', 'border-slate-200');
      btn.title = '收纳顶部阶段概览与备注';
    }
  }
  if (icon) {
    icon.setAttribute('data-lucide', collapsed ? 'panel-top-open' : 'panel-top-close');
  }
  if (text) {
    text.textContent = collapsed ? '展开概览' : '收纳概览';
  }
  if (window.lucide) {
    lucide.createIcons();
  }
}
```

### 3.3 三步制残迹清理
在 `web/index.html` 约 7084 行，将原 3 步残留字典收敛为真实的 2 个二级子步骤：
```javascript
const STEP0_SUB_LABELS = {
  1: '0.1 准备题目',
  2: '0.2 网页提问'
};
```

---

## 4. 构建、验证与部署闭环

- **构建命令**：在 `web/step0-src/` 目录下执行 `npm run build`（或根目录 `npm run build:step0`），重新编译生成 `web/assets/step0/step0.js` 与 `geo-step0-island.css`，并由脚本自动为 `web/index.html` 注入最新静态资源时间戳。
- **冒烟测试**：执行 `bash scripts/smoke_step0.sh`，确保 4/4 步检查全部通过。
- **真实验证端口**：GEO 交付管理端真实服务在端口 **8088**（`http://127.0.0.1:8088/` 或 `http://100.83.64.112:8088/`），绝不连接 3002。
