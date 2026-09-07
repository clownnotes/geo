# Design: 服务页准入合作机制双速见效与准入边界重构

## 1. 架构逻辑与业务模型 (Architecture & Business Logic)

### 1.1 双速见效与双向准入四维模型
针对采购决策人的评估模型，将准入板块划分为两大维度的平衡：
1. **时间维度（速度 vs 壁垒）**：
   - 前期给出首期 14 天快速见效的里程碑（让采购方有底气立项与向公司交差）；
   - 后期构筑 180 天品类首推的长效护城河（让采购方确信这项投资具备长期复利）。
2. **准入维度（正向画像 vs 负面清单）**：
   - 正向指出大模型的技术底层逻辑：大模型不为空气代言，只采信具备真实业务实力与案例的实体；
   - 负向树立专业技术团队的底线：坚决不碰黑盒投机与垃圾铺量，确保项目百分百交付质量。

---

## 2. 卡片对比与文案规范

| 卡片代号 | 原版（冗余/说教） | 新版（双速见效 + 专业准入） | 视觉特征 |
| :--- | :--- | :--- | :--- |
| **Card 1** | **标准包含**<br>与上一屏交付物完全重复 | **【14天首期快速起效】**<br>• /llms.txt 与 Schema 协议光速接入<br>• 高权重第三方信源核心实体借壳<br>• 14天跑出首批主流 AI 引用推荐<br>• 首期成果可验证、可验收、可汇报 | 白色卡片，品牌紫微徽章，hover 微动效 |
| **Card 2** | **交付样张**<br>与上一屏清单完全重复 | **【180天长效壁垒】**<br>• 普林斯顿 9 因子事实证据链全量上线<br>• 全网第三方高公信力多源交叉互证<br>• 阻断竞品借壳抄袭与低价反超<br>• 稳固行业品类第一首推标准心智 | 白色卡片，品牌紫微徽章，hover 微动效 |
| **Card 3** | **适合客户**<br>表述偏空洞，略显傲慢 | **【大模型只为真实实力代言】**<br>✓ B2B制造、硬科技、专业服务实体<br>✓ 拥有真实产品力与标杆客户案例<br>✓ 愿意开放业务核心事实与硬核参数<br>✓ 追求高意向商业买家线索转化 | 浅紫背景高亮卡片（`bg-brand-50 border-brand-400`），绿色微徽章，粗体文字 |
| **Card 4** | **不适合客户**<br>顾问说教感强 | **【专业交付底线与边界】**<br>✕ 企图短平快投机刷黑盒黑帽排名<br>✕ 缺乏真实交付能力的虚假空头产品<br>✕ 拒绝提供事实证据链与核心参数<br>✕ 希望靠批量垃圾内容充水铺量 | 浅灰背景（`bg-slate-50 border-slate-200`），红色微徽章，深灰文字 |

---

## 3. DOM 结构与样式实现

```html
<!-- 5. 准入合作与见效机制 (Trust Signals & Fit) -->
<section id="fit" class="py-20 bg-brand-50/60">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mb-14">
      <div class="text-sm font-extrabold text-brand-700 uppercase tracking-widest mb-3">Trust Signals</div>
      <h2 class="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight mb-5">准入合作与见效机制</h2>
      <p class="text-lg sm:text-xl text-slate-600 leading-relaxed">
        GEO 既有敏捷见效的爆发力，更有长期沉淀的复利壁垒。我们通过明确的双阶段见效周期与双向准入机制，确保每一个交付项目都能快速见效、长期稳赢。
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Card 1: Quick Win 14天首期快速起效 -->
      <!-- Card 2: Long-Term Moat 180天长效壁垒 -->
      <!-- Card 3: Good Fit 大模型只为真实实力代言 -->
      <!-- Card 4: Not Fit 专业交付底线与边界 -->
    </div>
  </div>
</section>
```
