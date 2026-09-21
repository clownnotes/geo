# Design: 写文同事界面移除协作与任务入口

## 1. 架构与角色定位

根据面向对象设计原则，系统角色分为两类：
- **写文同事 (`operator`)**：聚焦于企业客户的内容生产与交付，界面只保留生产所必需的视图（仪表盘、企业列表）。
- **系统开发者 (`developer`)**：负责系统运维、大模型调度、流水线底层排队监控与打包。

「协作与任务」模块本质为后台任务监控与打包工具，归属为**开发者专属视图**。

---

## 2. 界面与权限控制设计

### 2.1 侧边栏导航控制 (DOM 标记)
只给导航按钮加标记，不要给面板加：

```html
<button type="button" id="nav-home-collab" data-geo-dev-only onclick="switchHomeView('home-collab')" class="sidebar-nav-item">...</button>
```

`applyRbacUi()` 对写文同事给这个按钮加上 `hidden`（现有机制是 class，不是另写 `display:none`）。

**禁止**给 `#panel-home-collab`（它带 `home-panel`）加 `data-geo-dev-only`。开发者登录时，`applyRbacUi` 会把所有带这个标记的元素的 `hidden` 去掉。面板若也带上，人在仪表盘时协作页会一起露出来。藏入口只藏按钮；面板仍由 `switchHomeView` 决定显不显示。

### 2.2 路由与视图切换防护（两份名单都要改）
`devOnlyViews` 在 `web/index.html` 里写了两遍，漏一处就会从地址栏钻进来：

1. `showDashboard()` 里恢复上次页面的那份（约 6235 行）
2. `switchHomeView()` 里的那份（约 6356 行）

两处都加上 `'home-collab'`：

```javascript
const devOnlyViews = ['home-insights', 'home-ops', 'home-partners', 'home-settings', 'home-members', 'home-collab'];
if (devOnlyViews.includes(viewId) && !isDeveloper()) {
  viewId = 'home-dashboard';
}
```

写文同事从地址栏、刷新或控制台进来，都回到仪表盘。开发者不受影响。进入协作页才会调的 `fillCollabProjectSelect` / `collabRefreshTasks` 因此不会被写文同事触发，不必改后端。

---

## 3. 验收与回归方案
- 静态代码审查：确保 `#nav-home-collab` 存在 `data-geo-dev-only`，确保 `devOnlyViews` 包含 `'home-collab'`。
- 自动化测试：运行前端断言测试脚本，验证写文同事视角下侧边栏无此入口，强制访问被拦截回仪表盘。
