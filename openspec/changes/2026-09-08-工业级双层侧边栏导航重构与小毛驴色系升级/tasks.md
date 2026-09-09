## 1. 准备工作与规范对齐

- [ ] 1.1 核对 AGENTS.md 规范（0 Emoji 违规、DOM 标签完全闭合、阶段隔离与单步停步铁律）。
- [ ] 1.2 按 design 固化「一级分组 + 二级菜单」映射表（含监测运维 7 项、进阶攻防 4 主题），确认原 boost/ops 入口全部有二级归属、无删除。

## 2. 侧边栏与主工作区骨架开发

- [ ] 2.1 在 `web/index.html` 注入小毛驴 AI 专属色彩系统变量（`#7c5bf5` 紫色系），将外层容器重构为现代全屏水平分栏布局（`flex h-screen overflow-hidden`）。
- [ ] 2.2 构建左侧 `#app-sidebar`（240px）：品牌 Logo、项目下拉切换、**一级分组标题（可折叠）+ 二级菜单项（可点击高亮）**、底部账号与退出；窄屏改为抽屉。
- [ ] 2.3 构建顶部轻量级工作台 Top Bar（52px），包含：动态面包屑（客户名 / 一级分类 / 二级功能）、全局一键流水线、离线导出 ZIP 与刷新操作。

## 3. 页面面板承接与路由调度重构

- [ ] 3.1 重构 `#app-workspace`：去掉顶部场景 Tab + 步进条；Step 1~5 与监测/攻防各二级项挂为独立 `workspace-panel`；boost/ops 按主题迁入对应 Panel，保留原 Modal 按钮。
- [ ] 3.2 实现 `switchView(viewId)` + 改造 `parseCurrentRoute` / `updateRouteState`：Hash 为 `#project={id}&view={viewId}`（禁止前导 `/`），兼容旧 `step`/`tab`，同步侧栏高亮、分组展开与面包屑。
- [ ] 3.3 全面升级界面色彩：核心 CTA 迁至 `#7c5bf5` / Hover `#6846e3`，全面确保 0 彩色 Emoji。

## 4. 验证与回归测试

- [ ] 4.1 运行全套自动化测试，确保原有分发、发稿包、自愈与探测功能无回归缺陷。
- [ ] 4.2 执行前端 DOM 标签配对检查（`open_divs == close_divs` 差值为 0），并静态扫描 `web/index.html` 无彩色 Emoji。
- [ ] 4.3 本地 8088 真机验证：二级菜单分类点击、客户切换、旧 Hash 回放、头条知乎分发、监测/攻防各面板弹窗与审计正常。
