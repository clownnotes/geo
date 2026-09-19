# OpenSpec 技术架构设计：老板商业诊断报告高转化视觉样式嵌入

> 对应变更目录：`openspec/changes/2026-09-19-老板商业诊断报告高转化视觉样式嵌入`

---

## 1. 面向对象抽象设计

围绕【阶段一老板诊断报告交付物卡片】（`BossAuditDeliveryCard`）进行面向对象建模：

### 1.1 对象与属性
- **对象**：`BossReportStyleSwitcher`（老板报告展示切换器）
- **核心状态（属性）**：
  - `currentBossReportStyle`：`'visual'`（默认，高转化大屏） | `'md'`（纯文本底稿）
  - `currentProjectId`：当前聚焦的客户项目 ID（如 `nextgeo`）
  - `visualSrc`：当前高转化 HTML 的 API 访问地址（带防缓存时间戳 `?t=...`）

### 1.2 行为与方法
- `switchBossReportStyle(style)`：切换当前选中的视图样式，高亮对应分段胶囊按钮，切换视觉容器与文本容器的显示/隐藏；
- `loadBossReportVisual(forceReload)`：拉取并加载 `01_企业AI可见度商业诊断报告.html` 到内嵌沙箱；
- `openBossReportFullscreen()`：在新标签页独立打开该 HTML 文件，支持全屏大屏演示；
- `handleStep1AuditComplete()`：当跑完第一步真抓或直出诊断时，同时刷新大屏 iframe 与 Markdown 底稿。

---

## 2. 前端 DOM 结构与样式防污染隔离设计

### 2.1 交付物头部栏重构
在 `web/index.html` 的 `id="view-audit-boss"` 交付物卡片标题栏：
```html
<div class="px-6 py-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs font-semibold text-slate-700">
  <!-- 左侧：标题与视觉切换胶囊 -->
  <div class="flex items-center gap-3 min-w-0">
    <span class="truncate font-bold">交付物：01_企业AI可见度商业诊断报告</span>
    <!-- 样式分段器 (方案 B 核心) -->
    <div class="inline-flex p-0.5 bg-slate-200/80 rounded-lg text-[11px] font-semibold">
      <button type="button" id="btn-boss-style-visual" onclick="switchBossReportStyle('visual')" class="px-2.5 py-1 rounded-md bg-white text-[#7c5bf5] shadow-sm transition">
        高转化视觉版 (HTML)
      </button>
      <button type="button" id="btn-boss-style-md" onclick="switchBossReportStyle('md')" class="px-2.5 py-1 rounded-md text-slate-600 hover:text-slate-900 transition">
        文字底稿
      </button>
    </div>
  </div>

  <!-- 右侧：快捷操作组 -->
  <div class="flex items-center gap-3 shrink-0">
    <button type="button" onclick="openBossReportFullscreen()" class="text-slate-600 hover:text-[#7c5bf5] flex items-center gap-1" title="新窗口全屏打开高转化大屏">
      <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i><span>全屏大屏</span>
    </button>
    <button type="button" onclick="openShareModal()" class="text-[#7c5bf5] hover:text-[#6846e3] flex items-center gap-1" title="生成客户可打开的报告链接">
      <i data-lucide="share-2" class="w-3.5 h-3.5"></i><span>客户报告链接</span>
    </button>
    <button type="button" onclick="exportAuditReportHtml('boss')" class="text-slate-600 hover:text-slate-900 flex items-center gap-1" title="下载老板版自包含 HTML">
      <i data-lucide="file-down" class="w-3.5 h-3.5"></i><span>下载老板商业报告 (HTML)</span>
    </button>
    <button type="button" onclick="copyOutput('01_企业AI可见度商业诊断报告.md')" class="text-[#7c5bf5] hover:text-[#6846e3] flex items-center gap-1">
      <i data-lucide="copy" class="w-3.5 h-3.5"></i><span>复制全文</span>
    </button>
  </div>
</div>
```

### 2.2 双容器预览区域
```html
<!-- 容器 1：高转化视觉大屏容器（默认展示） -->
<div id="container-step-1-boss-visual" class="w-full bg-slate-50 min-h-[640px] relative">
  <iframe id="frame-step-1-boss-visual" class="w-full h-[760px] border-0 rounded-b-xl block" loading="lazy"></iframe>
</div>

<!-- 容器 2：原有的 Markdown 纯文本容器（默认隐藏） -->
<div id="preview-step-1-boss" class="p-6 markdown-body max-h-[600px] overflow-y-auto hidden">
  <div class="text-center py-12 text-slate-400 text-sm">请先点「① 真抓网络与底座指标」，再点「② 直出商业诊断与焦虑转化初稿」…</div>
</div>
```

### 2.3 零样式污染与响应式高度
- 使用 `iframe` 完全隔离了转化版 HTML 自带的 `:root` 全局色彩变量与 Tailwind Reset 样式，杜绝任何外部样式污染；
- 提供初始 `760px` 适宜高度，内部自适应滚动。

---

## 3. 接口与数据流联动

1. **报告 URL 生成**：
   - 地址：`/api/projects/{currentProjectId}/output/01_企业AI可见度商业诊断报告.html?t={Date.now()}`
   - **iframe 只带 Cookie，不带 JS 里的 Authorization**。该 output 接口在鉴权门之后，需 `report:view`。实现时必须确认登录/`/api/auth/status` 已下发 `Set-Cookie: geo_token`（现码已有），iframe 用同源地址；禁止把 token 拼进 URL。
   - 文件尚未生成时，视觉容器显示人话空态（先去点直出），不要白屏。
2. **直出操作联动**：
   - 当点击【② 直出商业诊断与焦虑转化初稿】执行成功后，前端同时调用：
     - `loadBossReportVisual(true)`：强制重载 iframe，大屏立刻刷新成最新数据；
     - `loadMarkdownToElem('01_企业AI可见度商业诊断报告.md', 'preview-step-1-boss')`：同步更新 Markdown 底稿。
