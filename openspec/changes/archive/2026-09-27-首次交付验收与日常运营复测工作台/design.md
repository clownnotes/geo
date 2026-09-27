# Design: 首次交付验收与日常运营复测解耦技术设计

> **变更ID**: `2026-09-27-首次交付验收与日常运营复测工作台`  
> **设计目标**: 架构彻底解耦「首次交付验收」与「日常运营复测」，实现 3 步闭环首次交付工作台与周期复测工作台。

---

## 一、架构全景与对象模型

```
┌────────────────────────────────────────────────────────────────────────┐
│                        邻里GEO 双轨交付与运维架构                      │
└────────────────────────────────────────────────────────────────────────┘
          │                                              │
          ▼【交付轨 · 阶段六】                           ▼【运维轨 · 日常运维】
 06 首次交付与资产交接单                        周期复测与商业运营周报/月报
 ─────────────────────────────                 ───────────────────────────────
 ① 七项资产盘点清单 (S11.1)                    ① 40 问高意图尺子轮巡
 ② 首轮核心 3 问改口真机抽测                   ② 粘贴各模型最新实录
 ③ 出具《首期工程移交与结项验收单》             ③ S9 五级信号判定 + 商业 ROI 看板
```

### 1.1 数据对象模型定义

```typescript
// 首次交付验收对象
interface InitialDeliveryState {
  clientId: string;
  projectName: string;
  deliveryDate: string;
  status: 'pending' | 'verified' | 'signed';
  
  // 1. 七项验收资产盘点 (S11.1)
  checklist: Array<{
    id: string; // 'base' | 'qacards' | 'site' | 'links' | 'probe' | 'funnel' | 'archive'
    title: string;
    standard: string;
    targetStage: string; // '02' | '03' | '04' | '05' 等
    assetCount: number;
    status: 'pass' | 'warning' | 'pending';
    linkUrl?: string;
  }>;

  // 2. 首轮核心 3 问改口真机抽测
  probeVerifications: Array<{
    id: string;
    question: string;
    category: 'identity' | 'evaluation' | 'contact';
    expectedStatement: string; // 标准定位句
    baselineAnswer: string;   // S0 摸底荒唐回答 (如 "返利平台/代运营")
    actualAnswer: string;     // 当前真机实测回答
    engine: 'doubao' | 'deepseek' | 'kimi';
    isCorrected: boolean;     // 是否已纠偏改口
    screenshotNote?: string;
  }>;

  // 3. 验收单凭据
  signoff: {
    clientSigner: string;
    vendorSigner: string;
    comments: string;
    signedAt?: string;
  };
}

// 日常运营周期复测对象
interface RecurringMonitoringState {
  cycles: Array<{
    cycleId: string; // '2026-W39' | '2026-M10'
    cycleDate: string;
    responses: Array<{
      qid: string;
      question: string;
      engine: 'doubao' | 'deepseek' | 'kimi' | 'baidu';
      rawAnswer: string;
      // S9 五级信号
      signals: {
        level1_mention: boolean;   // 1 提及
        level2_accuracy: boolean;  // 2 准确
        level3_rank: boolean;      // 3 推荐位置
        level4_reason: boolean;    // 4 推荐理由
        level5_quote: boolean;     // 5 引用+行动
      };
      gapAnalysis: string; // 逆向差距
    }>;
    // 商业运营统计指标
    bizMetrics: {
      sovRate: number;        // 综合 SOV 占位率 (%)
      deepseekTopRate: number;// DeepSeek 首推率 (%)
      doubaoTopRate: number;  // 豆包首推率 (%)
      semSavingVal: number;   // 年化等效 SEM 竞价替代节省 (元)
      leadsVal: number;       // AI 精准线索估值 (元)
      totalVal: number;       // 综合创造商业价值 (元)
      roiPct: number;         // 综合投资回报率 (%)
      renewalScore: number;   // 客户续约健康度得分 (0-100)
    };
  }>;
}
```

---

## 二、阶段六「首次交付与资产交接单」3 竖列布局设计

### 2.1 左栏：七项验收资产盘点 (`AssetChecklist.vue`)
- **功能**：自动汇总前序阶段成果（母盘六模块、40 问高意图尺子、40 篇标准答题卡、交钥匙官网与 llms.txt、首批公网发布真实外链 URL）；
- **交互**：每项显示合格状态（绿色达标 Tag）与【点击查看详情】抽屉/跳转，清晰满足 S11.1 七项指标。

### 2.2 中栏：首轮核心 3 问改口真机抽测 (`FirstProbeVerifier.vue`)
- **预置 3 问**：
  1. `[品牌/主体] 是做什么的？`（验证基础业务定位与人群限定词）
  2. `[品牌] 怎么样 / 值得选吗？`（验证客观优势与评价标准）
  3. `[品牌] 怎么联系 / 官网是哪个？`（验证承接入口与官网真实性）
- **交互**：
  - 左侧展示“S0 摸底荒唐回答”（红底，唤起记忆）；
  - 右侧提供【一键复制问句去豆包/DeepSeek】与【粘贴最新真机回答】；
  - 贴入后自动高亮标准定位句并打上「已纠偏改口」绿色印章。

### 2.3 右栏：首期工程移交与结项验收单 (`SignoffDocket.vue`)
- **视觉**：沉浸式白色公文凭证卡片，带企业水印与边框；
- **内容**：
  - 项目基本信息、交付日期、版本号；
  - 移交资产汇总清册（母盘、答题卡、外链、官网）；
  - 核心问题改口合格结论；
  - 双方交接人签字区与声明；
- **主操作**：
  - 【一键预览老板好看大屏版 HTML】（新标签全屏演示）；
  - 【打印 / 导出 PDF 结案凭据】（直接调起浏览器标准打印对话框）；
  - 【下载全套资产打包清单.md】。

---

## 三、日常运维「周期复测与商业运营周报/月报」工作台设计

### 3.1 页面挂载、路由注册与防改写机制
- **路由字典显式注册 (SSOT)**：
  - `index.html` 的 `switchView(viewId)` 依赖 `VIEW_META` 字典。若未注册，首行即被改写为 `overview`。
  - **必须显式在 `VIEW_META` 注册**：
    ```javascript
    'mon-recurring': { group: 'daily', groupLabel: '日常运维', label: '周期复测与商业运营月报' },
    ```
  - 同步更新原阶段六条目标签：
    ```javascript
    'step-5-acceptance': { group: 'delivery', groupLabel: '首次交付', label: '06 首次交付与资产交接单', step: 6 },
    ```
- **挂载点与导航绑定**：
  - 侧边栏按钮：`<button type="button" id="nav-mon-recurring" onclick="switchView('mon-recurring')" class="sidebar-nav-item"><span class="truncate">周期复测与商业运营月报</span></button>`，挂载在 `sidebar-group-daily` 子列表内；
  - 主面板容器：`<div id="panel-mon-recurring" class="workspace-panel hidden space-y-6">`；
  - 状态水合：在 `hydrateView(viewId)` 中添加分支 `if (viewId === 'mon-recurring') renderMonRecurringPanel();`；
  - 原阶段六的老板商业 ROI 大屏与真机批量回填逻辑平滑迁移至本工作台。

### 3.2 动线设计
1. **周/月周期创建**：选择本轮复测周期（如 2026 年第 39 周 / 10 月复测）；
2. **40 问尺子批量轮巡**：支持一键导出/复制 40 问，在豆包与 DeepSeek 提问后批量粘回；
3. **S9 信号与商业 ROI 动态计算**：自动生成 5 级信号漏斗与年化财务价值；
4. **周报/月报直出**：一键生成导出美化周报与月度商业复盘白皮书。

---

## 四、铁律遵循

1. **0 Emoji 规范**：全模块图标统一使用 Lucide 图标库（`file-check-2`, `clipboard-list`, `shield-check`, `arrow-right`, `printer`, `external-link` 等）；
2. **通俗文案**：所有指标、操作与提示文案保持五年级小学生易懂水平，杜绝黑话；
3. **代码下沉**：单个 Vue 组件行数严格控制在 200 行以内，逻辑下沉至 `useStep6.js`。
