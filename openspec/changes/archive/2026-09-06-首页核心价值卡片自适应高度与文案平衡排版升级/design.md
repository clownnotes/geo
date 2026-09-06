# Design: 首页核心价值卡片自适应高度与文案平衡排版

## 1. 排版与高度自适应方案
- **卡片容器**：`h-full p-8 rounded-2xl bg-brand-50/30 border border-brand-200/80 hover:border-brand-500 hover:shadow-lg transition duration-200 flex flex-col justify-between`
- **文字主体区**：`space-y-3`，正文使用 `text-sm sm:text-base text-slate-600 leading-relaxed`
- **底部分割线与链接**：`mt-auto pt-5 mt-6 sm:mt-8 border-t border-brand-200/70 text-xs font-bold text-brand-700 flex items-center justify-between`

## 2. 三张卡片文案对称设计（字数 ~97-105 字）
- **Card 1 (Brand Visibility - 让品牌进入 AI 候选集合, 97字)**：
  当采购方向大模型咨询意向产品时，往往会深入对比很多细节。企业要想让 AI 给出对自己有利的回答，首先必须被识别为清晰完整的品牌整体，并让 AI 充分理解自身的真实实力，才能在竞品对比中稳定进入核心候选集。
- **Card 2 (Brand Cognition - 减少错误描述和能力偏移, 99字)**：
  大模型在生成推荐答案时会抓取全网碎片信息，若缺乏统一证据，极易产生错误幻觉或采信竞品唱衰。企业必须通过 GEO 明确业务边界、技术参数与资质实证，让 AI 准确理解真实能力，彻底杜绝错误描述与偏离。
- **Card 3 (Growth Channel - 把官网建设成权威答案源, 105字)**：
  官网不再只是给客户翻看的宣传手册，而是大模型抓取实体事实、标杆案例与技术参数的黄金信源。通过普林斯顿因子规范站点结构，能让 AI 在输出结论时直接采信官网事实，并为品牌打上权威的 Citation 来源引用角标。
