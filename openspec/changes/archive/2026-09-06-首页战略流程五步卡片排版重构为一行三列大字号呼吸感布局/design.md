# Design: 首页战略流程 3+2 大卡片排版架构

## 1. 网格与容器架构
- **第一行（站内事实筑基三部曲）**：
  `<div class="grid grid-cols-1 md:grid-cols-3 gap-6">`
  包含 STAGE 01、STAGE 02、STAGE 03，每卡宽约 375px。
- **第二行（全网生态与长效监测）**：
  `<div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-[780px] mx-auto mt-6">`
  包含 STAGE 04、STAGE 05，宽度同样为 378px 并居中对齐，与第一行完全等宽对称！

## 2. 卡片内部排版升阶
- **容器**：`p-7 sm:p-8 rounded-2xl bg-white border border-brand-200/80 shadow-xs relative flex flex-col justify-between hover:border-brand-500 hover:shadow-lg transition duration-200`
- **悬浮大水印**：`text-5xl font-black text-brand-200/50 absolute top-5 right-5 select-none font-mono`
- **阶段标签**：`text-xs font-mono font-bold text-brand-700 tracking-wider mb-1`
- **大标题**：`text-xl sm:text-2xl font-bold text-slate-900 mb-3 tracking-tight`
- **正文**：`text-sm sm:text-base text-slate-600 leading-relaxed mb-5`
- **底部特性列表**：`text-xs sm:text-sm text-slate-600 space-y-2 pt-4 border-t border-slate-100`
