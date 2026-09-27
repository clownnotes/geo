# Design: 阶段一商业诊断升级3竖列工作区

## 一、架构定位与设计理念

阶段一聚焦于**“出具诊断报告，为签约促单提供实锤”**。
整体设计完全继承阶段零的成熟工作台架构，由 **顶部看板 + 3 竖列工作区 + 麦肯锡手册** 组成：

```
+-----------------------------------------------------------------------------------+
| StageHeader (阶段一：AI 可见度商业转化诊断 | 目标：出具诊断报告促成签单 | 备忘录)   |
+--------------------------+------------------------------+-------------------------+
| StudioFileTree (左栏)     | StudioEditor (中栏)          | StudioSop (右栏)        |
| - 指标与素材             | - 多 Tab 标签栏              | 步骤 1: 真抓与客户对照  |
|   01_底座指标_待对照.md  |   [初稿.md] [大屏.html]      |   [真抓底座指标]        |
|   01_豆包问答素材.md     | - 源码编辑 (textarea)        |   [门禁: 已确认 / 挂起] |
| - 过程草稿               |   行号 + 实时打磨微调        | 步骤 2: 出初稿与去水润色|
|   01_商业转化初稿.md     | - 渲染预览 (Markdown / HTML) |   [直出初稿]            |
| - 最终交付报告           |   大屏实时 iframe 渲染       |   [去外部IDE/豆包润色]  |
|   01_老板大屏.html       | - 快捷按钮:                  | 步骤 3: 出具报告与流转  |
|   01_商业文字版.md       |   [一键复制内容] [保存修改]  |   [生成多版本报告]      |
|   01_工程师体检版.md     |   [全屏大屏演示]             |   [完成阶段一前往阶段二]|
+--------------------------+------------------------------+-------------------------+
```

---

## 二、数据对象与状态模型

### 1. 文件资产模型 (Files)
```javascript
export const STAGE_1_FILES = {
  // 1. 指标与素材
  '01_网络底座指标_待对照.md': {
    category: 'materials',
    dir: '指标与素材',
    name: '01_网络底座指标_待对照.md',
    renderMode: 'markdown',
    content: `# 客户网络底座与线上资产真实指标 (机械基础版·待核对)
- 抓取时间: {today}
- 企业官网域名: {domain}
- 服务器所在地域: {city}
- 百度权重 / SEO 底座: PR 1 / 权重 0 (极弱)
- 大模型爬虫放行状态:
  - Bytespider (豆包): ❌ 未配置专属放行 (可能被拦截)
  - DeepSeekSpider: ❌ 未配置
- 大模型可读文件检测:
  - /llms.txt: ❌ 不存在 (大模型抓取无结构化索引)
  - JSON-LD 结构化标签: ❌ 缺失
- 豆包首推率现状: 0% (被竞品截流)

> 交付专家说明：本指标为机械抓取直出，可人工在上方直接微调，用于与客户面对面对照。`
  },
  '01_阶段零豆包实测问答素材.md': {
    category: 'materials',
    dir: '指标与素材',
    name: '01_阶段零豆包实测问答素材.md',
    renderMode: 'markdown',
    content: `# 阶段零豆包实测真实问答记录 (底牌素材)
## 核心问答 1: 徐州做GEO优化哪家公司比较好？
- 豆包实测回答: 推荐了优搜网络、徐州智搜等竞品，未提及客户品牌。
- 竞品吃入口分析: 竞品已布局高权重问答语料，客户直接丢失一手精准询盘。`
  },

  // 2. 过程草稿
  '01_商业诊断与转化初稿.md': {
    category: 'drafts',
    dir: '过程草稿',
    name: '01_商业诊断与转化初稿.md',
    renderMode: 'markdown',
    content: `# 企业 AI 可见度商业诊断与询盘流失初稿 (待润色)
## 一、老板必看的资产确权
客户已拥有徐州本地行业知名度，但大模型搜索入口被竞品截流 100%。

## 二、算清 3 类致命流失账
1. 品牌直搜流失: 老客户朋友问豆包，豆包推荐竞品，信任直接被撬走；
2. 行业词截流: “徐州做GEO优化找哪家”，客户完全隐形；
3. 竞品对比抹黑: 缺乏官方权威真相源，大模型抓取杂乱信息产生幻觉。

## 三、破局路径与 30 天交付目标
立即建立交钥匙原生大模型官网与普林斯顿母盘语料，实现 30 天内豆包首推率从 0% 跃升至 60% 以上。`
  },

  // 3. 最终报告
  '01_老板商业诊断报告_好看大屏.html': {
    category: 'reports',
    dir: '最终交付报告',
    name: '01_老板商业诊断报告_好看大屏.html',
    renderMode: 'html',
    content: `<!DOCTYPE html>
<html><head><meta charset="utf-8"><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-900 text-white p-6 font-sans">
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between border-b border-slate-700 pb-4">
      <div>
        <h1 class="text-2xl font-black text-violet-400">企业 AI 可见度商业诊断决策大屏</h1>
        <p class="text-xs text-slate-400 mt-1">专供老板决策 · 穿透 3 大截流漏洞 · 算清流失账促单</p>
      </div>
      <div class="px-3 py-1 bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-bold">高危预警：商机被抢</div>
    </div>
    <div class="grid grid-cols-3 gap-4 text-center">
      <div class="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
        <div class="text-xs text-slate-400">豆包 (字节生态) 首推率</div>
        <div class="text-2xl font-black text-rose-400 mt-1">0%</div>
      </div>
      <div class="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
        <div class="text-xs text-slate-400">核心竞品截流率</div>
        <div class="text-2xl font-black text-amber-400 mt-1">82.5%</div>
      </div>
      <div class="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
        <div class="text-xs text-slate-400">每月潜在询盘流失估计</div>
        <div class="text-2xl font-black text-emerald-400 mt-1">30~50 条</div>
      </div>
    </div>
  </div>
</body></html>`
  },
  '01_老板商业诊断报告_文字版.md': {
    category: 'reports',
    dir: '最终交付报告',
    name: '01_老板商业诊断报告_文字版.md',
    renderMode: 'markdown',
    content: `# 企业 AI 可见度商业转化诊断报告 (老板交付文字版)
- 客户名称: {brand}
- 诊断专家: GEO 交付团队
- 交付状态: 签约就绪 / 老板定稿`
  },
  '01_工程师底座技术审计.md': {
    category: 'reports',
    dir: '最终交付报告',
    name: '01_工程师底座技术审计.md',
    renderMode: 'markdown',
    content: `# 站点底座技术体检与工程审计报告 (内部施工版)
- 服务器响应时延: 480ms (待优化)
- 爬虫蜘蛛放行情况: Robots.txt 缺少 Bytespider 专门声明
- 结构化语料支持: 暂无 JSON-LD 与 llms.txt`
  }
};

/**
 * 2. 阶段一专属元数据 (STAGE_1_META)
 * 供 StudioSop 与 StageHeader 强类型驱动渲染
 */
export const STAGE_1_META = {
  index: 1,
  key: 'step1',
  name: '阶段一：AI 可见度商业转化诊断',
  tag: '老板决策版',
  target: '真抓网络底座指标，出具商业诊断与询盘流失初稿，为对客签约提供实锤。',
  notesPlaceholder: '记录客户商业诊断备忘（如：关注竞品截流、底座缺失...）',
  categories: [
    { id: 'materials', name: '指标与素材' },
    { id: 'drafts', name: '过程草稿' },
    { id: 'reports', name: '最终交付报告' }
  ],
  sopSteps: [
    {
      id: 'crawl_confirm',
      name: '真抓网络底座与客户对照',
      desc: '抓取客户线上真实底座指标（0 幻觉）。交付专家可直接在中间微调数据，并与客户对照确认。',
      category: 'materials',
      activeFile: '01_网络底座指标_待对照.md',
      action: { label: '真抓网络底座指标', icon: 'activity', type: 'crawlMetrics' },
      gate: {
        type: 'patience_confirm',
        options: [
          { id: 'confirmed', label: '客户已核对确认（推进生成初稿）' },
          { id: 'suspended', label: '客户暂无耐心/意向不足（挂起等待，暂不推进）' }
        ]
      },
      nextLabel: '确认完成，前往出具初稿'
    },
    {
      id: 'draft_polish',
      name: '直出初稿与去水润色',
      desc: '生成基础初稿。交付人员可直接复制中栏内容与豆包问答素材，前往外部 IDE 或豆包进行深度润色（去水、加强焦虑转化说服力），改完贴回保存。',
      category: 'drafts',
      activeFile: '01_商业诊断与转化初稿.md',
      action: { label: '直出商业诊断与转化初稿', icon: 'file-text', type: 'generateDraft' },
      nextLabel: '初稿润色完成，前往生成最终报告',
      skipLabel: '跳过润色，直接出报告'
    },
    {
      id: 'final_reports',
      name: '出具多版本交付报告',
      desc: '根据确认并润色后的素材，生成最终交付报告（老板好看大屏 HTML、商业文字版 MD 与工程师技术审计版）。',
      category: 'reports',
      activeFile: '01_老板商业诊断报告_好看大屏.html',
      action: { label: '一键生成多版本诊断报告', icon: 'sparkles', type: 'generateFinalReports' },
      extraActions: [
        { label: '全屏演示老板大屏', icon: 'maximize-2', type: 'openFullscreen' },
        { label: '复制客户报告链接', icon: 'share-2', type: 'copyClientLink' }
      ],
      nextLabel: '完成阶段一，前往阶段二（交钥匙官网）',
      isFinal: true,
      nextView: 'step-2-scaffold'
    }
  ]
};
```

---

## 三、SOP 动线与门禁交互流转

右栏 SOP 划分为 3 步推进（末步兼具多版本报告生成与交钥匙官网流转）：

### 步骤 1：真抓底座指标与客户对照
- **主操作**：【真抓网络底座指标】（加载/刷新《01_网络底座指标_待对照.md》，中栏自动打开该文件，交付专家可直接编辑）。
- **耐心判定门禁开关**：
  - 单选卡 A：`[✓] 客户已核对确认（意向明确，推进生成初稿）`
  - 单选卡 B：`[!] 客户暂无耐心/意向不足（挂起等待，暂不推进）`
- **推进规则**：只有选中单选卡 A 时，底部的【前往第 2 步：出具初稿】按钮才变为可用高亮状态；若选中 B，按钮置灰并提示“已挂起，等客户有需要再跟进”。

### 步骤 2：生成初稿与去水润色
- **主操作**：【直出商业诊断与焦虑转化初稿】（自动生成初稿并打开）。
- **去水润色卡片**：
  - 提示说明：“初稿已出！可直接在中栏点【一键复制内容】，连同左侧豆包问答底牌带去外部 IDE 或豆包进行去水润色，改好后粘贴回中栏保存。”
  - 快捷提示词复制入口：【复制润色与去水提示词】。
- **推进按钮**：【初稿润色完成，前往生成最终报告】（同时提供次要链接：【跳过润色，直接出报告】）。

### 步骤 3：出具多版本交付报告
- **主操作**：【一键生成多版本诊断报告】（自动就绪老板大屏 HTML、商业文字版 MD 与工程师版）。
- **快捷动作**：
  - 【全屏演示老板大屏】（支持大屏弹窗沉浸展示）
  - 【复制对外客户报告链接】（方便发给老板微信直达）
- **推进按钮**：【验收通过，前往阶段二（交钥匙官网）】。

### 4. 步骤头部跳转与动线前进的文件联动一致性规范
- **痛点与问题**：用户通过点击右侧流水线步骤头部（`gotoStep`）切换步骤时，中栏若只变步骤号而不切换激活文件，会导致操作动线与文件脱节。
- **一致性规范**：无论用户是点击「步骤推进按钮（`proceed`）」还是点击「步骤头部卡片（`gotoStep`）」，SOP 控制层必须统一依据目标步骤的 `activeFile` 自动调用 `handleSelectTab(step.activeFile)`，在中栏精准打开对应文件，实现操作动线与文件视图的 100% 同步联动。

---

## 四、工程契约与前置缺口修复设计

### 1. 阶段零 StudioSop 契约双轨容错修复
为避免新旧组件混血导致阶段零动线按钮消失，`StudioSop.vue` 必须实现双轨兼容：
- **模式 A（新契约）**：当接收到 `props.stageMeta` 时，从 `stageMeta.sopSteps` 动态渲染步骤；
- **模式 B（旧契约容错）**：当 `props.stageMeta` 未传入时，自动回退到阶段零写死的 2 步经典 SOP（0.1 准备题目打磨，0.2 网页提问贴回答），并且同时向下兼容发射旧版事件（`switch-step`、`refresh-questions`、`proceed-to-next`、`finish-stage0`），彻底修复线上阶段零按钮消失的真实故障。

### 2. 单产物双桥接架构（Single Bundle Dual Bridges）
为彻底避免多入口打包 `emptyOutDir: true` 清空或多产物版本不同步问题，采用单产物双桥接架构：
- 统一打包管线输出至 `assets/step0/step0.js`；
- 在 `main.js` 中同时挂载并暴露两个独立全局桥接对象：
  - `window.__GEO_STEP0__`：挂载阶段零应用实例；
  - `window.__GEO_STEP1__`：挂载阶段一应用实例；
- 宿主 `index.html` 仅需加载一份 JS Bundle，按视图切换独立触发各阶段的挂载与卸载，既消除了构建清空风险，又实现了代码高效复用。

### 3. CSS 样式引入规范
在 `index.html` 头部必须显式引入 `assets/step0/geo-step0-island.css`（或阶段一配套样式），确保 Markdown 渲染层 `.geo-md` 样式完整生效。

### 4. 宿主 index.html 隔离挂载设计
- 仅在 `panel-step-1-diag` 内挂载独立实例 `<div id="step1-app-root"></div>`；
- 阶段 2~5 原版 DOM 保持 100% 原始状态，不进行任何隐藏或替换。

### 5. 顶栏概览折叠联动与前端状态持久化设计
- **顶栏概览折叠联动**：`index.html` 的 `applyStepOverviewState` 统一支持阶段零与阶段一概览卡片收纳折叠，按钮文本 `收纳概览` / `展开概览` 与卡片显隐状态（`panel-step-overview`）双向联动，提供沉浸式工作区空间。
- **前端本地持久化（localStorage）**：`useStep1.js` 采用 `step1_workspace_state` 键值持久化阶段一工作区核心状态（包含当前进行的 SOP 步骤号 `activeStepId`、编辑中的文件内容字典 `files`、已打开标签页 `openTabs`、交付备忘录 `note`、客户核对门禁状态 `gateConfirmed` 等），刷新页面后自动从本地存储原位恢复，防止用户打磨成果意外丢失。

### 6. 事件监听生命周期销毁守则（onUnmounted）
所有在 Composable（如 `useStep1.js`）或组件中注册的全局监听（如 `window.addEventListener('geo-toggle-step-overview')`），必须配套注册 `onUnmounted(() => window.removeEventListener(...))`，确保组件重新挂载或卸载时彻底清理，严禁内存泄漏与事件重复触发。

### 7. 数据模型唯一真相源（SSOT）与持久化可观测性
- **单一真相源注入 `dir`**：在 `stage1Config.js` 中，文件对象的 `dir` 属性统一由 `CATEGORY_DIR_MAP[category]` 在构建文件树时一次性计算注入，消除多处硬编码与无用死代码分支。
- **持久化异常日志可观测性**：`saveState()` 在 `catch` 异常时，严禁静默吞掉，必须输出结构化警告日志（如 `console.warn('[useStep1] 本地持久化保存失败，可能超出存储限额:', err)`），杜绝故障黑盒。

### 8. 左栏资源管理器按钮显隐与动作契约
`StudioFileTree.vue` 工具栏的操作按钮必须具备按阶段定制的显隐与事件闭环契约，严禁暴露“能点却无响应”的死按钮：
- **可配置显隐**：通过 `allowNewFile`（默认 true）与 `allowRefresh`（默认 true）prop 精确控制工具栏按钮呈现；
- **阶段一契约**：阶段一聚焦于 6 份确定性交付物，禁用自由新建文件（设置 `:allow-new-file="false"`）；若展示刷新按钮，必须显式监听并接入 `@refresh-files`，由 `handleRefreshFiles` 执行指标资产重载并提供 Toast 反馈，彻底杜绝无响应黑盒。

### 9. 安全合并式刷新契约（Preserved Merge Refresh）
为防止用户在日常点击「刷新目录」时意外丢失已经精心打磨并保存的内容：
- **合并规则**：刷新操作执行**增量与安全合并** —— 重新构建模板时，若发现缺失的文件予以补齐，对于用户从未改动过的初始底座文件同步最新上下文；而对于用户已经修改、保存过的内容（`savedContent !== defaultContent`），**严格予以保留，绝不粗暴覆盖**；
- **本地存储安全**：合并后更新 `localStorage` 存档，同时 Toast 明确提示「资产目录已同步最新底座（已保留您的打磨成果）！」，杜绝无提示静默洗掉成果。

### 10. 编辑器视图与数据层强制同步规范（Editor Sync Guarantee）
为杜绝“DOM 显示旧内容但底层数据已变更”的数据假象脱节：
- **强制重绘 Key**：`StudioEditor.vue` 的 textarea 绑定 `:key="activeFileName"`，确保在切换文件或实例重构时 DOM 与虚拟节点重新绑定；
- **主动变更监听**：增加对当前激活文件 `activeFile.content` 的侦听器，当数据被外部刷新或重载时，若发现 DOM 与数据不同步，主动重新给 textarea DOM 赋值，确保用户所见即所得。
