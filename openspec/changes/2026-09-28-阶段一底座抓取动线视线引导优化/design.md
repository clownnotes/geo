# Design: 阶段一官网底座真机探测与中栏数据实时落盘闭环

## Architecture (时序架构与数据拓扑)

```
[交付专家点击动线按钮]
       │
       ▼
[StudioSop.vue] (按钮触发 loading 态，展示转圈图标与“正在探测官网底座…”)
       │ emit('action', 'crawlMetrics')
       ▼
[useStep1.js] (handleAction 异步发起请求)
       │ fetch('/api/projects/' + pid + '/run/audit', { mode: 'crawl' })
       ▼
[server.py / tools/geo/server.py] (路由调度 /run/audit)
       │
       ▼
[tools/geo/audit.py] (run_audit_crawl 真机探测引擎)
       ├── inspect_website() -> 真实 HTTP 请求探测官网、/robots.txt、/llms.txt、Schema、SSR、DNS
       ├── load_probe_snapshot() -> 挂载阶段零豆包实测底牌（首推率与竞品数据）
       ├── save_audit_metrics() -> 真实落盘 projects/{id}/outputs/audit_metrics.json
       └── save_project_output() -> 真实落盘技术体检与商业诊断 Markdown 报告
       │
       ▼ 返回 JSON：{ success: true, metrics: { ... }, tech_score: 85 }
[useStep1.js] (接收 metrics，生成客观排版 Markdown，写入 files['01_网络底座指标_待对照.md'].content)
       │
       ▼
[StudioEditor.vue] (中栏编辑器即刻响应式渲染最新探测真数据！)
       │
       ▼
[StudioSop.vue] (按钮转为浅绿已完成态，下方推进大按钮呼吸高亮引导进入下一步)
```

---

## Interface (组件属性与接口规范)

### 1. 后端路由强化 (`GEO/tools/geo/server.py`)
- **路由路径**：`POST /api/projects/{id}/run/audit`
- **请求载荷**：
  ```json
  { "mode": "crawl" }
  ```
- **响应载荷结构强化**（在现存响应基础上确保输出 `metrics` 详情字段）：
  ```json
  {
    "success": true,
    "step": "audit",
    "mode": "crawl",
    "message": "阶段 1 已执行完毕！",
    "tech_score": 85,
    "metrics": {
      "url": "https://nextgeo.baicl.cc",
      "is_online": true,
      "status_code": 200,
      "html_size_kb": 35.5,
      "has_ssr": true,
      "has_llms_txt": true,
      "has_json_ld": true,
      "clean_text_length": 2484,
      "text_density_ratio": 6.8,
      "robots_status": "已主动配置本土 AI 爬虫规则",
      "warnings": [],
      "tech_score": 85
    }
  }
  ```

### 2. 前端动线卡片组件 (`GEO/web/step0-src/components/studio/StudioSop.vue`)
- **新增属性 Props**：
  ```js
  /** 动作执行中 loading 字典，如 { crawlMetrics: true } */
  actionLoadingMap: {
    type: Object,
    default: () => ({}),
  }
  ```
- **模板中动作按钮渲染逻辑**：
  ```html
  <button
    v-if="step.action"
    type="button"
    :disabled="isActionLoading(step.action.type)"
    class="px-3 py-2 rounded-lg border text-[13px] font-bold flex items-center justify-center gap-1.5 transition shadow-2xs"
    :class="[
      isActionLoading(step.action.type) ? 'bg-slate-100 border-slate-300 text-slate-400 cursor-wait' :
      (isActionDone(step.action.type) ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100/60' : 'bg-[#7c5bf5]/10 border-[#7c5bf5]/30 hover:bg-[#7c5bf5]/20 text-[#7c5bf5] cursor-pointer')
    ]"
    @click.stop="onActionClick(step.action.type)"
  >
    <i :data-lucide="isActionLoading(step.action.type) ? 'loader-2' : (isActionDone(step.action.type) ? 'check-circle' : (step.action.icon || 'activity'))"
       :class="isActionLoading(step.action.type) ? 'w-4 h-4 animate-spin' : 'w-4 h-4'"></i>
    <span>{{ isActionLoading(step.action.type) ? '正在探测官网底座…' : (isActionDone(step.action.type) ? (step.action.completedLabel || '已抓取真实指标 (点击重新抓取)') : step.action.label) }}</span>
  </button>
  ```

### 3. 阶段一状态管理 (`GEO/web/step0-src/useStep1.js`)
- **状态声明**：
  ```js
  const isCrawling = ref(false);
  ```
- **真实异步动作执行与内容回填**：
  ```js
  async function handleAction(actionType) {
    if (actionType === 'crawlMetrics') {
      if (isCrawling.value) return;
      isCrawling.value = true;
      try {
        const token = typeof window !== 'undefined' ? window.currentAuthToken || '' : '';
        const pid = typeof window !== 'undefined' ? window.currentProjectId || ctx.clientId : ctx.clientId;
        
        const res = await fetch(`/api/projects/${encodeURIComponent(pid)}/run/audit`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ mode: 'crawl' })
        });
        const data = await res.json();
        if (data.success) {
          crawledMetrics.value = true;
          // 根据后端真实 metrics 数据动态生成最新 Markdown 内容
          const freshMarkdown = buildCrawledMetricsMarkdown(ctx, data.metrics || {});
          if (files.value['01_网络底座指标_待对照.md']) {
            files.value['01_网络底座指标_待对照.md'].content = freshMarkdown;
            files.value['01_网络底座指标_待对照.md'].isDirty = false;
          }
          handleSelectTab('01_网络底座指标_待对照.md');
          saveState();
          showStudioToast('真实底座指标抓取完毕！已同步至中栏与磁盘文件，请核对并进入下一步出初稿');
        } else {
          showStudioToast(`探测失败: ${data.message || '网络连接超时'}`, 'error');
        }
      } catch (err) {
        showStudioToast(`请求失败: ${err.message}`, 'error');
      } finally {
        isCrawling.value = false;
      }
    }
  }
  ```

---

## Data Structure & Storage (数据存储规范)

1. **后端磁盘持久化文件**：
   - 指标真源：`projects/{id}/outputs/audit_metrics.json`
   - 技术体检报告：`projects/{id}/outputs/01_企业底座技术体检审计报告.md`
2. **前端工作区持久化**：
   - 随 `useStep1` 的 `saveState()` 统一持久化至本地存储键 `` `geo_step1_state_${clientId}` ``，保证刷新页面后真实抓取指标依然在位。
