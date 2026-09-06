# Proposal: 关于页视觉风格与文字排版全量对齐首页

## Why (为什么做)
1. **用户核心反馈**：
   - 用户在浏览 `http://localhost:8088/sites/nextgeo/about/` 时明确提出：关于页的“文字都很小”，希望与首页 `http://localhost:8088/sites/nextgeo/` 的文字样式与字号层级对齐，放大字号；
   - **核心质量前提**：“大一些的前提，我希望是文字排版更好看。当然，整体文字风格如果都能对齐，让整个网站看着好看是最好的。”
2. **现状诊断（关于页与首页的视觉断层）**：
   - 首页采用了现代化、大字号、舒展留白的 B2B 视觉体系（正文 16~18px、卡片标题 20~24px、内边距 p-6~p-8、呼吸感极强）；
   - 关于页内部却充斥着早期的微缩字体（10px、11.5px、12px 表格、13px 描述），卡片间距紧绷，在宽屏上显得局促、小气、疲劳，与首页大气从容的科技感产生了明显的审美断层。

## What Changes (改动了什么)
1. **建立整站统一的 Typography 排版阶梯**：
   - 章节大标题 (H2)：从 24~28px 升级至 `text-3xl sm:text-4xl font-black text-slate-900 tracking-tight`，与首页完全一致；
   - 叙事段落 (p)：升级至 `text-base sm:text-lg leading-relaxed text-slate-700`；
2. **重构 Bento Grid 客群画像 6 宫格卡片视觉**：
   - 行业卡片标题从 12px 升级至 `text-base sm:text-lg font-bold text-slate-900`；
   - 描述正文从 11.5px 升级至 `text-sm sm:text-base (15px) text-slate-600 leading-relaxed`；
   - 典型追问从 10.5px 升级至 `text-xs sm:text-sm text-slate-700`，内边距同步从 p-4 加大到 `p-5 sm:p-6`，圆角升级为 `rounded-2xl`，与左侧大卡片完美均衡；
3. **左侧深色核心卡片同步按比例升阶**：
   - 标题从 26px 升阶为 `text-2xl sm:text-3xl font-black`；
   - 正文提升为 `text-sm sm:text-base (15px) text-slate-100`；
   - 【防丢单真相】容器同步加大至 `p-5 sm:p-6`，警示文案提升为 `text-sm sm:text-base`；
   - 底部数据模块升级至 `text-3xl font-black`，说明文案提升为 `text-sm text-slate-200`；
4. **核心引言条、团队卡片、6步闭环与表格全量升阶**：
   - 分水岭引言条：升级至 `p-6 text-base sm:text-lg rounded-2xl`；
   - 核心团队卡片：职务升级至 `text-sm font-bold`，介绍正文升级至 `text-base (16px)`，卡片加大留白；
   - 6 步闭环：卡片升级至 `p-6 sm:p-7 rounded-2xl`，步骤正文提升至 `text-base`；
   - 对比表格：表头与单元格从 12px 升级至 `text-sm sm:text-base (14~16px)`，行高加大至 1.75，彻底消除眯眼看表格的局促感；
5. **资产双端同步与零 Emoji 规范**：
   - 双向同步 `outputs/about/` 与 `outputs/site/about/`；
   - 严格杜绝任何 Emoji，以严谨排版层次与微光对比呈现高级感。

## Capabilities (对外能力)
- 使整个关于页与首页形成高度统一的视觉审美与排版节奏，字字清晰饱满、层次从容分明，提升品牌的企业级信任度。

## Impact (影响范围)
- `projects/nextgeo/outputs/about/index.html`
- `projects/nextgeo/outputs/site/about/index.html`
- 仅涉及前端排版与视觉样式，无破坏性改动。
