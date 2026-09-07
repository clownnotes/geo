# Design: 服务页全量对齐官网五步交付流水线

## 1. 架构与布局模型 (Layout & DOM Structure)

### 1.1 栅格拓扑结构
服务页容器使用 `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`，内部排版采用 **3 + 2 优雅居中对称布局**，保持视觉层次与首页完全同构：

```
[Row 1: 站内核心事实基座]
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8
├── Stage 01: 现状评测与认知审计
├── Stage 02: 站点底座与协议接入
└── Stage 03: 普林斯顿 9 因子语料重构

[Row 2: 全网生态与长效监测]
grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto mt-8
├── Stage 04: 多平台矩阵借壳分发
└── Stage 05: 声量监测与动态复盘周报
```

### 1.2 单个卡片内部组件划分
每个 Stage 卡片基于现代高质感 SaaS 风格设计，包含以下 4 层结构：
1. **顶部角标与水印层**：
   - 阶段代号微徽章：`STAGE 01` ~ `STAGE 05`，`bg-brand-100 text-brand-700 font-black text-xs px-3 py-1 rounded-full`；
   - 右上角绝对定位数字水印：`text-5xl font-black text-brand-200/70 select-none font-mono`。
2. **标题与定位阐述层**：
   - 主标题：`text-2xl sm:text-3xl font-black text-slate-900 tracking-tight mb-3`；
   - 价值阐述：`text-base text-slate-600 leading-relaxed mb-6`。
3. **核心执行动作列表（Action Items）**：
   - 浅紫背景面板：`bg-brand-50/80 p-5 rounded-xl border border-brand-200 text-sm sm:text-base font-bold text-slate-800 space-y-2`；
   - 包含 3 项关键执行清单，点阵圆点采用品牌紫。
4. **服务页专有增量——【核心交付物】专区（Deliverables Badge）**：
   - 卡片底部边界微分割，使用 Tag 标签与实体文件命名方式呈现具体成果物，如：
     - `交付物：《企业 GEO 就绪度诊断报告》& 首推份额差距清单`
     - `交付物：/llms.txt 协议配置包与 Schema.org 结构化元数据`
     - `交付物：普林斯顿 9 因子官网高权威内容库与标准 FAQ 对`
     - `交付物：知乎/百科/垂直媒体第三方共识信源互证矩阵`
     - `交付物：《GEO 多模型心智监测动态周报》与优化清单`

---

## 2. 详细文案规范与对比表

| 阶段代码 | 阶段标准名称 | 核心执行要点 (3项) | 阶段企业级核心交付物 |
| :--- | :--- | :--- | :--- |
| **STAGE 01** | **现状评测与认知审计** | 1. 跨模型行业高频商业 Query 全量跑测<br>2. 竞品心智占有率与首推份额对比<br>3. 企业实体消歧与大模型回答偏见审计 | 《企业 GEO 就绪度诊断报告》&《大模型首推份额差距清单》 |
| **STAGE 02** | **站点底座与协议接入** | 1. `/llms.txt` 标准协议与知识图谱接入<br>2. Schema.org (JSON-LD) 实体元数据注入<br>3. SSR/SSG 爬虫无障碍渲染底座改造 | 官网技术底座改造部署包与机器可读协议接口文件 |
| **STAGE 03** | **普林斯顿 9 因子语料重构** | 1. 普林斯顿 9 因子高权威语料提纯改造<br>2. 核心技术参数与硬核证据链补齐<br>3. 标准结构化高频 FAQ 问答对锚定 | 普林斯顿 9 因子官网权威内容库全量上线文档 |
| **STAGE 04** | **多平台矩阵借壳分发** | 1. 高公信力媒体与问答专栏借壳占位<br>2. 知乎专栏/行业垂直媒体一致事实铺设<br>3. 第三方权威信源全网交叉互证闭环 | 第三方高权重信源共识互证矩阵与发布存档 |
| **STAGE 05** | **声量监测与动态复盘周报** | 1. 每周多模型 AI 引用率与好感度动态监控<br>2. Citation 溯源归因与 Prompt 漂移排查<br>3. 动态知识热补丁与问法库敏捷迭代 | 《GEO 多模型心智监测动态周报》与持续优化清单 |

---

## 3. 视觉与排版约束

1. **绝对禁止 Emoji 彩色表情**：
   - 遵循 `AGENTS.md` 规范第 3 条，全站严禁出现 ⚡️、💡、⚠️、⚙️ 等任何 Emoji，使用标准的微圆点、微徽章或简洁字符替代；
2. **DOM 标签平衡规范**：
   - 确保 `div`、`article`、`section` 等所有容器标签 100% 配对，避免页面栅格崩坏；
3. **响应式适配**：
   - 移动端单列堆叠（`grid-cols-1`），平板双列（`md:grid-cols-2`），PC 端前三后二（`lg:grid-cols-3` + 居中两列）。
