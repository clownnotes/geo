# Design: 全阶段升级3竖列工作区

## 一、架构定位与设计哲学

本设计致力于解决阶段 1 至阶段 5 界面排版混乱、与阶段 0 交互断层的问题。
核心哲学：
1. **单一真实信源（SSOT）**：将 `StageHeader`、`StudioFileTree`、`StudioEditor`、`MckinseyDrawer` 彻底抽象为通用组件，阶段间的差异完全下沉至配置驱动层（`stageConfigs`）。
2. **纯粹化编辑打磨**：中栏编辑器始终作为核心视界，保持高保真、沉浸式编辑与预览体验；辅助管理（如证据抓取、事实仲裁、对照卡）按用户裁决紧凑收纳在右侧 SOP 面板中。
3. **闭环 SOP 动线**：右栏统一使用清晰的四步/三步卡片动线，带有操作主按钮、状态标识、辅助说明及通关指引。

---

## 二、核心对象模型与配置字典 (StageConfigs)

在前端状态层定义统一的 `stageConfigs` 字典：

```javascript
export const STAGE_CONFIGS = {
  0: {
    key: 'step0',
    name: '阶段零：去豆包提问，查客户真实情况',
    tag: '摸底阶段',
    target: '出 5 道核心题去豆包真机实测，摸清 AI 对客户的真实认知。',
    categories: [
      { id: 'questions', name: '豆包出的题目' },
      { id: 'answers', name: '豆包实测回答' }
    ],
    sopSteps: ['0.1 准备题目打磨', '0.2 网页提问贴回答'],
    mckinsey: { /* 阶段零避坑手册 */ }
  },
  1: {
    key: 'step1',
    name: '阶段一：AI 可见度商业转化诊断',
    tag: '老板签单决策',
    target: '真抓网络底座指标，直出商业诊断报告与视觉大屏，量化询盘流失痛点促成签单。',
    categories: [
      { id: 'reports', name: '商业诊断报告 (MD)' },
      { id: 'dashboards', name: '老板高转化大屏 (HTML)' },
      { id: 'tech', name: '底座技术体检清单 (MD)' }
    ],
    editorTabs: ['report.md', 'dashboard.html', 'tech_audit.md'],
    sopSteps: [
      { id: 'crawl', name: '① 真抓网络与底座指标' },
      { id: 'direct', name: '② 直出商业诊断与转化初稿' },
      { id: 'polish', name: '③ 调小毛驴/复制给 IDE 润色' },
      { id: 'screen', name: '④ 生成高转化大屏与定稿验收' }
    ],
    mckinsey: {
      value: '为老板算清 3 类询盘流失账，明示竞品截流现状。',
      why: '老板不关心底层爬虫代码，只关心商机被谁抢走、不做损失多大。',
      how: '一键真抓底座 -> 程序直出初稿 -> 润色说服力 -> 输出签单大屏。'
    }
  },
  2: {
    key: 'step2',
    name: '阶段二：AI 原生交钥匙官网交付',
    tag: '交钥匙交付',
    target: '交付专为大模型智能搜索打造的 100% 静态极速官网与大模型底座代码，零技术债。',
    categories: [
      { id: 'foundation', name: '大模型底座配置文件' },
      { id: 'deploy', name: 'VPS 部署与反代配置' }
    ],
    editorTabs: ['llms.txt', 'schema.jsonld', 'robots.txt', 'nginx.conf'],
    previewAction: 'openSiteModal', // 弹窗或新开窗口查看完整高保真交钥匙整站
    sopSteps: [
      { id: 'compile', name: '① 一键编译交钥匙整站' },
      { id: 'verify', name: '② 验证大模型抓取友好度' },
      { id: 'vps', name: '③ 查看/复制 VPS 反代与导出源码' }
    ],
    mckinsey: {
      value: '彻底免碰客户老旧代码，二级域名挂载，快速交付秒开站点。',
      why: '改老代码成本高风险大；大模型专属站点干净透明，SEO/GEO 权重更高。',
      how: '编译整站 -> 检查 llms.txt / JSON-LD -> 复制 Nginx 规则上线。'
    }
  },
  3: {
    key: 'step3',
    name: '阶段三：普林斯顿 9 因子高权威内容重构',
    tag: '母盘语料',
    target: '沉淀无可辩驳的证据与真相源，重构注入三元组与高采纳率对比表的权威母盘。',
    categories: [
      { id: 'master', name: '普林斯顿高权威母盘' },
      { id: 'materials', name: '证据素材与真相清单' }
    ],
    editorTabs: ['master_corpus.md'], // 中栏纯粹专注文档
    sopSteps: [
      { id: 'evidence', name: '① 收集证据素材 (单页抓取/手册粘贴)' },
      { id: 'facts', name: '② 预检冲突并确认安全真相' },
      { id: 'reconstruct', name: '③ 普林斯顿增量/全量重构' },
      { id: 'diff_pin', name: '④ 审查前后对照卡并钉住母盘' }
    ],
    mckinsey: {
      value: '大模型不认泛泛空话，只认有信源、有三元组、有参数表的硬核事实。',
      why: '证据不实会导致 AI 幻觉，甚至替竞品宣传。先存证据再认真相。',
      how: '收证据 -> 清洗真相源 -> 普林斯顿母盘重构 -> 钉住母盘。'
    }
  },
  4: {
    key: 'step4',
    name: '阶段四：矩阵分发与定稿发布',
    tag: '定稿发布',
    target: '严格遵循「草稿 ≠ 定稿 ≠ 可发」铁律，在线精修并按渠道分发放行。',
    categories: [
      { id: 'channels', name: '分发渠道定稿文章' }
    ],
    editorTabs: ['toutiao.md', 'zhihu.md', 'wechat.md', 'qa_matrix.md'],
    sopSteps: [
      { id: 'draft', name: '① 批量/单篇生成渠道草稿' },
      { id: 'edit', name: '② 对照题目与事实在线精修改定稿' },
      { id: 'release', name: '③ 勾选放行并复制富文本发布' }
    ],
    mckinsey: {
      value: '精准占领各平台搜索入口，确保输出内容保真度 100%。',
      why: 'AI 草稿不可直接外发，必须经过交付人员事实核验和语气微调。',
      how: '看题目 -> 网页改定稿 -> 勾选放行确认 -> 复制去平台发帖。'
    }
  },
  5: {
    key: 'step5',
    name: '阶段五：首轮监测与结案验收',
    tag: '结案交付',
    target: '运行多模型首轮声量实测，生成美化交付周报，签发客户结案验收单。',
    categories: [
      { id: 'deliverables', name: '结案交付文档与周报' },
      { id: 'data', name: '声量监测与题目实测数据' }
    ],
    editorTabs: ['metrics_dashboard.html', 'weekly_report.html', 'acceptance_sheet.html'],
    sopSteps: [
      { id: 'monitor', name: '① 运行实时声量监测 / 真机回填' },
      { id: 'analyze', name: '② 指标达成度归因分析' },
      { id: 'export', name: '③ 导出美化周报与签发结案单' }
    ],
    mckinsey: {
      value: '用清晰可见的量化数据与美化报告，让客户直观看到成效并痛快结案。',
      why: '交付有头有尾，用 DeepSeek、豆包首推率和信源评分证明交付价值。',
      how: '跑监测 -> 看 4 维指标 -> 导出周报 -> 开具客户验收单。'
    }
  }
};
```

---

## 三、布局与组件交互规范

统一的主容器网格排布：
```html
<div class="flex gap-4 items-stretch flex-col lg:flex-row h-[720px] min-h-[600px]">
  <!-- 1. 左栏：文件与资产树 (宽度固定 240px~260px) -->
  <StudioFileTree
    :categories="currentStage.categories"
    :files="files"
    :active-category="activeCategory"
    :active-file-name="activeFileName"
    @toggle-category="handleToggleCategory"
    @open-file="handleOpenFile"
    @new-file="handlePromptNewFile"
    @refresh-files="handleRefreshFiles"
  />

  <!-- 2. 中栏：多 Tab 编辑打磨区 (弹性伸缩 flex-1) -->
  <StudioEditor
    :open-tabs="openTabs"
    :active-file-name="activeFileName"
    :files="files"
    :render-mode="currentTabRenderMode"
    @select-tab="handleSelectTab"
    @close-tab="handleCloseTab"
    @update-content="handleUpdateContent"
    @copy-content="handleCopyContent"
    @save-file="handleSaveActiveFile"
  />

  <!-- 3. 右栏：SOP 交付动线流水线 (宽度固定 340px~360px) -->
  <StudioSop
    :current-stage="currentStageIndex"
    :current-step="currentSubStep"
    :stage-meta="currentStage"
    :project-data="projectData"
    @action="handleSopAction"
    @proceed-to-next="handleProceedNext"
  />
</div>
```

### 中栏与右栏职责解耦原则（已对齐裁决）
- **阶段一**：中栏支持双 Tab（Markdown 诊断文本 + 老板视觉大屏 HTML 实时预览），全屏切换顺滑；右栏为四步流水线。
- **阶段二**：中栏专注编辑 `llms.txt`、`schema.jsonld`、`robots.txt`、`nginx.conf`；交钥匙全景预览支持点击弹窗或独立新标签页全屏预览。
- **阶段三**：中栏为纯粹母盘正文 Markdown 编辑区；右栏收纳折叠式证据库抓取输入与真相源清洗仲裁卡片。
- **阶段四**：中栏为稿件在线改稿定稿区；右栏提供主问句/事实依据对照卡与放行复制按钮。
- **阶段五**：中栏支持 4 维指标可视化大屏、周报 HTML 与结案验收单 HTML 实时预览；右栏提供监测触发与导出按钮。

---

## 四、时序与数据流设计

1. **阶段切换**：
   - 用户在侧边栏或顶部导航点击进入指定阶段（0～5）；
   - 父级触发 `switchStep(n)`，统一向 Studio 岛发送 `setStage(n)` 事件；
   - Studio 岛根据 `STAGE_CONFIGS[n]` 动态加载对应阶段的资产文件列表、初始化默认 Tab，并渲染专属 SOP 流水线；
   - 顶部 `StageHeader` 响应式展示当前阶段的标题、定位、核心目标及交付备忘录。
2. **数据持久化与 Mock 桥接**：
   - 所有打磨修改的文件（如诊断报告、母盘 Markdown、周报 HTML）保存时，通过 `server.py` 本地 CRUD 接口写入本地 `data/projects.json`；
   - 即使刷新页面或归档重开对话，所有文件修改与打勾状态均完整持久化。
