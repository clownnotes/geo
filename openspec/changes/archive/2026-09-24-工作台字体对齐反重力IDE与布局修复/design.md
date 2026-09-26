# Design: 工作台字体对齐反重力IDE与布局修复

## 〇、源码现状核对（2026-09-24；Antigravity fix 后 Cursor 复审更新）

| 项 | 主工程现状 | 状态 |
| :--- | :--- | :--- |
| 字体栈 / 抗锯齿 / 等宽 | `geo-admin.css` + `index.html` 已注入 | 已达标 |
| 侧栏 0.1 / 0.2 | `index.html` 已为 `text-[13px]` | 已达标 |
| StudioEditor / FileTree / Sop 字号 | 对齐下表目标矩阵 | 已达标 |
| `StudioSop` 宽度 | `w-full lg:w-80 shrink-0`（已去 `lg:w-84`） | **已修复** |
| `StudioEditor` 弹性 | `flex-1 min-w-0` | **已修复** |
| `MckinseyDrawer.vue` | 非本轮主体 | 非目标 |
| 产物 | `web/assets/step0/step0.js` 已重编 | 已落盘 |

下表「原代码字号」保留为问题背景；实现以本节为准。

## 一、视觉设计与字号映射对齐矩阵

| 界面区域 | 原代码字号 | 反重力 IDE 基准 | 目标设计字号与类名 | 视觉目标与理由 |
| :--- | :--- | :--- | :--- | :--- |
| **中间编辑器文本区** | 12px (`text-[12px]`) | 14px 饱满等宽 | **14px** (`text-[14px] leading-relaxed`) | 核心作业区，字号舒展，长期盯屏不酸痛 |
| **中间编辑器行号栏** | 11px (`text-[11px]`) | 12px 精致等宽 | **12px** (`text-[12px] leading-relaxed w-12`) | 与 14px 正文严格行高对齐，辅助定位 |
| **中间编辑器 Tab 标签** | 12px (`text-xs`) | 13px 中等加粗 | **13px** (`text-[13px] px-3.5 py-1.5`) | 标签清晰可读，关闭按钮 12px |
| **中间编辑器顶部按钮** | 12px (`text-xs`) | 13px 图标文字 | **13px** (`text-[13px] px-3 py-1.5`) | 复制与保存按钮更具操作手感 |
| **左侧资源树文件名** | 11px (`text-[11px]`) | 13px 清晰可读 | **13px** (`text-[13px] py-2 px-2.5`) | 扩大点击热区，杜绝蚂蚁字 |
| **左侧资源树分类名** | 12px (`text-xs`) | 13px 加粗 | **13px** (`text-[13px] font-semibold`) | 分类与目录层级鲜明 |
| **右侧 SOP 步骤说明** | 11px (`text-[11px]`) | 13px 宽松正文 | **13px** (`text-[13px] text-slate-700 leading-relaxed`) | 交付业务指引清晰一目了然 |
| **右侧 SOP 卡片主标题** | 14px (`text-sm`) | 15px 加粗 | **15px** (`text-[15px] font-bold text-slate-900`) | 步骤核心动作抓人眼球 |
| **右侧 SOP 主操作按钮** | 12px (`text-xs`) | 14px 饱满主按钮 | **14px** (`text-[14px] font-bold py-2.5`) | “保存并前往”突出主路径动线 |
| **全局导航三级小步** | 11px (`text-[11px]`) | 13px 导航项 | **13px** (`text-[13px] py-2 px-2.5`) | 侧边栏高亮清晰直观 |

---

## 二、字体栈（Font Stack）规范

```css
/* 全局界面无衬线字体 */
html, body, button, input, select, textarea {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* 专业代码与文本编辑等宽字体 */
.font-mono, textarea.font-mono, code, pre {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
}
```

---

## 三、三栏 Flex 栅格布局防挤压模型

### 1. 结构与尺寸分配
外层容器：
`<div class="flex gap-4 items-stretch flex-col lg:flex-row h-[700px] min-h-[580px]">`

- **左栏（资源管理器）**：
  - 样式：`w-full lg:w-60 shrink-0`（固定 240px，不可收缩）
- **中栏（编辑器主区）**：
  - 样式：`flex-1 min-w-0`（**关键加固：`min-w-0` 允许弹性自适应，阻止 Flex 子项内容溢出**）
- **右栏（SOP 动作面板）**：
  - 样式：`w-full lg:w-80 shrink-0`（**严禁使用非标准类名 `lg:w-84`，锁定固定 320px 宽度**）

### 2. 防挤压机理
当三栏并列时，左栏 240px + 右栏 320px + 间距 32px 共固定占用 592px。
其余屏幕宽度（如 1440px 屏幕剩余约 800px+）由中间编辑区 `flex-1 min-w-0` 完整占领。
任何情况下，右栏绝不会霸占整屏，中间编辑器绝不会被压缩至 0 像素。
