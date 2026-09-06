# Design: 首页战略流程五步标准化卡片设计

## 1. 结构与排版设计
- **外层网格**：`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 sm:gap-5`
- **卡片容器**：`p-5 sm:p-6 rounded-2xl bg-white border border-brand-200/80 shadow-xs relative flex flex-col justify-between hover:border-brand-500 hover:shadow-lg transition duration-200`
- **背景悬浮数字**：`text-3xl sm:text-4xl font-black text-brand-200/60 absolute top-4 right-4 select-none font-mono`
- **小节徽标**：`text-xs font-mono font-bold text-brand-700 mb-1`
- **标题**：`text-base sm:text-lg font-bold text-slate-900 mb-2.5 tracking-tight`
- **正文说明**：`text-xs sm:text-[13px] text-slate-600 leading-relaxed mb-4`
- **底部特性列表**：`text-[11px] sm:text-xs text-slate-500 space-y-1.5 pt-3 border-t border-slate-100`

## 2. 五阶段对齐明细
1. **STAGE 01: 现状评测与认知审计**
   - 正文：在主流 LLM（DeepSeek、ChatGPT、Kimi、豆包、元宝）中深度跑测品牌被提及率、回答偏见与关键能力召回率，摸清心智基线。
   - 列表：· 跨模型行业高频 Query 跑测 ｜ · 竞品对抗与首推份额对比
2. **STAGE 02: 站点底座与协议接入**
   - 正文：改造官网技术底座，配置 /llms.txt 标准协议、注入 Schema.org 结构化元数据，并支持 SSR/SSG 爬虫无障碍渲染，让大模型秒懂直接采纳。
   - 列表：· /llms.txt 知识图谱标准配置 ｜ · 爬虫无障碍双模渲染底座
3. **STAGE 03: 普林斯顿 9 因子语料重构**
   - 正文：基于普林斯顿 9 因子规范，重构官网内容体系，提纯权威实体定义、标杆案例与硬核技术参数，为 AI 提供无法辩驳的事实证据链。
   - 列表：· 普林斯顿 9 因子高权威提纯 ｜ · 核心技术参数与标准 FAQ 锚定
4. **STAGE 04: 多平台矩阵借壳分发**
   - 正文：依托主流 AI 极度信赖的高权重第三方信源（知乎专栏、权威百科、行业垂直媒体、技术社区）铺设一致事实佐证，构建全网共识闭环。
   - 列表：· 权威第三方背书交叉验证 ｜ · 高权重公信力专栏借壳占位
5. **STAGE 05: 声量监测与动态复盘周报**
   - 正文：持续追踪主流大模型对品牌的召回率、引用来源质量与情感偏向，每周输出多模型动态周报，实现长效复盘与持续增长。
   - 列表：· 每周 AI 引用与好感度动态监控 ｜ · 竞品攻防与 Prompt 漂移复盘
