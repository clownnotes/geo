# Design: 运营端仪表盘角色视角改造与待办台账

## 0. 已拍板结论（2026-09-20）

| 项 | 结论 |
| :--- | :--- |
| 实施路线 | **方案 A**（工作台大盘角色裂变）；方案 B 本轮不实施，仅作历史对照保留在 §3 |
| 运营四宫格 | 我的管辖企业 / 待真机实测 / 未完成交付 / **声量异常数** |
| 待办行 | **必须**展示：真机灯色、最近豆包位次、声量、是否异动、开工入口 |
| 帮助信息 | 易混淆按钮与指标旁附白话说明 |

---

## 1. 架构方案对比（历史对照；实施以方案 A 为准）

| 维度 | 方案 A：工作台大盘角色裂变（**已选**） | 方案 B：登录直达企业管理（**本轮不采用**） |
| :--- | :--- | :--- |
| **设计核心** | 仪表盘保留，按角色裂变为两套视图 | 仪表盘仅对开发者开放，运营直达企业列表 |
| **运营进入路径** | 登录 ➔ 运营专用工作台（待办/卡点/预警） ➔ 选企业开工 | 登录 ➔ 企业管理表格 ➔ 选企业开工 |
| **信息呈现** | 真机待补、未完成交付、声量异常 + 带排名/异动的待办行 | 仅企业表格，无全局卡点聚合 |
| **商业数据脱敏** | 运营端绝对不出现价值、ROI、利润倍数 | 同左（无仪表盘入口） |

---

## 2. 方案 A 详细架构设计

### 2.1 视图差异化渲染结构

在 `panel-home-dashboard` 内部，按角色分为两种独立容器：

```html
<section id="panel-home-dashboard" class="home-panel space-y-6">
  <header class="geo-page-head">
    <div>
      <h1 class="geo-page-title" id="dashboard-main-title">仪表盘</h1>
      <p class="geo-page-desc" id="dashboard-desc-dev" data-geo-dev-only>
        一眼看全局健康与商业数字；客户档案请到「企业管理」。
      </p>
      <p class="geo-page-desc hidden" id="dashboard-desc-ops">
        今天先看哪家企业要真机、哪家声量掉了；点进去就能开工。
      </p>
    </div>
  </header>

  <!-- 开发者专属：财务大盘 + 全站真机台账（data-geo-dev-only） -->
  <div id="dashboard-dev-section" data-geo-dev-only class="space-y-6">
    <!-- 原有真机检测总台账 + 4 宫格：托管项目 / 全套交付完成 / 全域商业总价值 / 企业管理 -->
  </div>

  <!-- 运营专属作业看板 -->
  <div id="dashboard-ops-section" class="space-y-6 hidden">
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <!-- 1 我的管辖企业 -->
      <!-- 2 待真机实测 -->
      <!-- 3 未完成交付 -->
      <!-- 4 声量异常数（id: ops-stat-sov-alert） -->
    </div>
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
        <h2 class="text-sm font-bold text-slate-900">今日待办与企业卡点</h2>
        <span class="text-xs text-slate-500">优先处理：真机逾期、声量掉榜</span>
      </div>
      <div id="ops-action-list" class="divide-y divide-slate-100 text-sm">
        <!-- 见 §2.3 行模型 -->
      </div>
    </div>
  </div>
</section>
```

### 2.2 四宫格统计口径（写死，禁止再换成「已结案」）

| 卡片标题 | DOM id | 统计规则 | 白话帮助（旁注 / title） |
| :--- | :--- | :--- | :--- |
| 我的管辖企业 | `ops-stat-my-projects` | `projectsCache.length`（已按 `allowed_projects` 过滤） | 「分给你负责的客户家数」 |
| 待真机实测 | `ops-stat-need-probe` | 真机台账状态为 `never` 或 `overdue` 的企业数 | 「超过 14 天没回填、或从没回填过；需要你拿手机问豆包并粘贴答案」 |
| 未完成交付 | `ops-stat-pending-stage` | 阶段进度小于 5 的企业数 | 「交付流水线还没走到最后一步的客户」 |
| 声量异常数 | `ops-stat-sov-alert` | 管辖企业中，最近一次监测满足 `check_alert_conditions` 任一准则的企业数 | 「豆包里品牌声量掉了或跌出前排；点待办行可看位次并去复测」 |

### 2.3 待办行模型（`ops-action-list`）

每一行对应一家管辖企业，字段如下（界面用白话，代码可用英文 key）：

| 字段 | 人话展示示例 | 数据来源 |
| :--- | :--- | :--- |
| `project_name` | 企业显示名 | 项目配置 |
| `probe_status` | 绿灯 / 黄灯 / 红灯 / 从未真机 | `classify_status`（台账） |
| `probe_hint` | 「还有 3 天到黄灯」或「已超 14 天」 | 距上次有效回填天数 |
| `doubao_rank` | 「豆包第 2 位」/「未上榜」/「暂无数据」 | 最近一次有效解析的 `parse_probe_text().rank`（优先真机回填，其次巡检落库） |
| `sov_pct` | 「声量 52%」 | 最近 SOV |
| `sov_alert` | 徽章「声量异常」或「正常」 | `check_alert_conditions` 结果 |
| `alert_reason` | 短句：如「环比掉 18%」/「跌出第 1」 | 告警原因摘要 |
| `stage_progress` | 「交付进度 3/5」 | 项目阶段 |
| `primary_action` | 按钮「去真机回填」或「进入流水线」 | 真机逾期/从未 → 调用 `openManualCheckForProject(id)`（进探针页并打开粘贴框，**禁止** `enterWizard(id, 5)` 误进阶段五）；有声量异常但真机正常 → 进流水线/监测；否则进流水线 |

排序建议：声量异常且真机逾期 > 仅真机逾期/从未 > 仅声量异常 > 其余（阶段未完优先于已完成）。

### 2.4 脚本渲染逻辑与数据流

- `applyRbacUi()`：
  - `isDeveloper()`：显示 `dashboard-dev-section`，隐藏 `dashboard-ops-section`；
  - 非开发者：隐藏 `dashboard-dev-section`（**绝不**调用 `/api/portfolio/summary` 等财务接口），显示 `dashboard-ops-section`，调用 `renderOpsDashboard()`。
- `renderOpsDashboard()`：
  1. 以 `projectsCache`（已脱敏）为管辖范围；
  2. 拉取/复用真机台账行（与运维告警同源策略，仅过滤管辖 id）；
  3. 对每家企业读取最近 Rank/SOV 与是否命中告警准则；
  4. 填充四宫格与 `ops-action-list`。
- 运营默认落地页：仍进入仪表盘（方案 A），以便先看待办再开工。

### 2.5 就地帮助信息规范

**原则**：按钮名用五年级能懂的话；仍可能误解的，加 `title` 或旁侧问号气泡（无 Emoji）。

| 控件 | 主文案 | 帮助文案（必须具备其一） |
| :--- | :--- | :--- |
| 真机灯色徽章 | 正常 / 将逾期 / 已逾期 / 从未真机 | 「颜色按距上次你粘贴豆包答案的天数自动算，不是手点的」 |
| 「去真机回填」 | 同左 | 「用手机打开豆包提问，把完整回答复制回来粘贴」 |
| 「进入流水线」 | 同左 | 「打开这家客户的交付步骤（摸底、写稿、监测等）」 |
| 「声量异常」徽章 | 同左 | 「系统对比历史发现声量掉了或排名掉了；建议尽快真机复测确认」 |
| 四宫格标题 | 见 §2.2 | 见 §2.2 白话帮助列 |
| 开发者侧「机器全量巡检」相关 | 保留给开发者 | 运营视图中弱化或隐藏；若残留文案须写明「后台自动跑，不用你点」 |

实现方式优先：

1. 原生 `title`（悬停即可）；
2. 卡片标题旁 `<button type="button" aria-label="说明">?</button>` + 短气泡（点击展开一句人话）；
3. 禁止把帮助做成必须跳转外链文档才能懂。

---

## 3. 方案 B（本轮不实施，仅归档对照）

若未来产品改口采用极简路线：侧边栏仪表盘加 `data-geo-dev-only`，运营默认 `switchHomeView('home-enterprises')`。**当前 tasks 与验收不以 B 为准。**

---

## 4. 关键底层机制（系统事实，供看板消费）

### 4.1 真机实测与红黄绿灯

1. 运营真机提问 → `POST /api/projects/{id}/monitor/manual-ingest` → `log_manual_ingest()` 写入 `data/ops_check_logs.jsonl`。
2. `classify_status(days, policy, has_manual)`：
   - 无有效回填 → `never`；
   - `days >= overdue_days`（默认 14）→ `overdue`；
   - `days >= warn_days`（默认 7）→ `warn`；
   - 否则 → `ok`。

### 4.2 豆包排名与声量告警

1. `parse_probe_text()`：切分序号列表 / 首推语境 → Rank；未提及 → 0。
2. SOV 与时序写入项目 `history.db`。
3. `check_alert_conditions()`：SOV 低于阈值、环比突降 ≥15%、或核心词失守 Top1 → 计入「声量异常」。
