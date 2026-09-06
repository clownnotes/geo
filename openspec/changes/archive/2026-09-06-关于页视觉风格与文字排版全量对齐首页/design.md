# Design: 关于页视觉风格与文字排版全量对齐首页

## 1. 字体层级与空间比例设计规范 (对齐首页)

### 全局排版尺度对照表

| 界面元素 | 旧版关于页 (字号偏小局促) | 首页基准尺度 | 重构对齐后标准 (更耐看、更通透) |
| :--- | :--- | :--- | :--- |
| **Section 章节大标题 (H2)** | `text-2xl sm:text-3xl font-black mb-5` | `text-3xl sm:text-4xl font-black mb-6` | `text-3xl sm:text-4xl font-black text-slate-900 tracking-tight mb-6` |
| **Section 引导正文 (p)** | `font-size: 17px` 但样式分散 | `text-base sm:text-lg text-slate-700 leading-relaxed` | 统一为 `text-base sm:text-lg text-slate-700 leading-relaxed mb-6` |
| **分水岭引言条** | `p-4 text-xs sm:text-sm` | `p-6 sm:p-7 text-base sm:text-lg` | `p-6 sm:p-7 text-base sm:text-lg rounded-2xl border border-brand-200/90 bg-white/95 shadow-sm` |
| **Bento Grid 模块外壳** | `p-5 sm:p-7 rounded-2xl` | `p-7 sm:p-10 rounded-3xl` | `p-6 sm:p-8 rounded-3xl border border-slate-200/90 shadow-sm bg-white/95` |
| **Bento Grid 顶部标签** | `text-xs sm:text-sm` + `text-[11px]` | `text-sm font-black` + `text-xs font-bold` | `text-sm sm:text-base font-black text-slate-900` + `text-xs font-bold text-brand-700` |
| **Bento 左侧大卡片** | 标题 27px，正文 13~14px | 首页 Hero 卡片：标题 32px，正文 16px | 标题 `text-2xl sm:text-[30px]`，正文 `text-sm sm:text-base`，真相卡 `text-sm sm:text-base`，内边距 `p-7 sm:p-8` |
| **Bento 右侧 6 宫格卡片** | **标题仅 12px，正文仅 11.5px，追问仅 10.5px** | 首页 Feature 卡片：标题 18~20px，正文 14~15px | **全量升阶**：<br>• 容器 `p-5 sm:p-6 rounded-2xl`；<br>• 标题 `text-base sm:text-lg font-bold text-slate-900`；<br>• Tag `text-xs font-bold px-2.5 py-0.5`；<br>• 正文 `text-sm sm:text-[14.5px] text-slate-600 leading-relaxed`；<br>• 追问 `text-xs sm:text-sm text-slate-600` |
| **核心团队 (Core Team)** | 职务 12px，介绍 14px，padding 28px | 首页卡片：职务 14px，介绍 15~16px | 职务 `text-sm font-bold text-brand-700`，介绍 `text-sm sm:text-base text-slate-600 leading-relaxed`，容器留白扩大 |
| **6 步闭环 (Methodology)** | 步骤标题 18px，正文 14px，padding 20px | 首页价值卡：标题 20px，正文 15~16px，padding 24px | 步骤标题 `text-lg sm:text-xl font-black`，正文 `text-sm sm:text-base text-slate-600 leading-relaxed`，容器 `p-6 sm:p-7 rounded-2xl` |
| **全页对比数据表格** | `table class="content-table text-xs"` (12px) | 单元格 15px，清晰饱满 | 表头 `text-sm sm:text-base font-bold`，单元格 `text-sm sm:text-base text-slate-600 leading-relaxed`，内边距 `py-4 px-5` |

---

## 2. 设计美学准则（大而好看的排版法则）

1. **同频扩大留白**：字体放大时，如果 padding 不变就会显得逼仄臃肿。因此所有卡片内边距从 `p-4` 提升至 `p-5` 或 `p-6`，圆角从 `rounded-xl` 提升至 `rounded-2xl`；
2. **强化粗细与明度对比**：
   - 标题统一使用 `font-black` 或 `font-bold`，颜色使用 `#0f172a (slate-900)`；
   - 正文使用 `font-normal`，颜色使用 `#475569 (slate-600)` 或 `#334155 (slate-700)`，杜绝昏暗死灰；
   - 重点关键词使用 `text-brand-700 font-bold` 或 `text-amber-300`，点缀微发光质感；
3. **零 Emoji 彩色表情红线**：严禁在任何文本或 HTML 中使用彩色 Emoji 符号。
