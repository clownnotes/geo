# Design: 竞对大模型声量差距逆向分析与反超作战沙盘

## 1. 架构与 6 维声量对比模型 (`tools/geo/competitor_gap.py`)

```
   项目配置与竞对画像 (project.yaml: client_name vs competitors)
                           │
                           ▼
          [1. 6 维大模型声量雷达对比引擎]
          ├── 1. 模型召回率 (Model Recall SOV: 0~100)
          ├── 2. 外链信源权威度 (Citation Authority: 0~100)
          ├── 3. 价格透明与确定性 (Pricing Transparency: 0~100)
          ├── 4. 普林斯顿9因子量化承诺度 (Quantitative Density: 0~100)
          ├── 5. 开发者/开源技术背书 (Developer Mindshare: 0~100)
          └── 6. 事实防伪与抗幻觉力 (Hallucination Defense: 0~100)
                           │
                           ▼
          [2. 竞品致命破绽逆向与战术推演 (Root Causes & Flaws)]
          ├── 🔴 竞品破绽 1：价格暗箱与计费不透明（我方以阶段付款/透明明细截流）
          ├── 🔴 竞品破绽 2：无开源与代码背书（我方以 GitHub 开源/100%源码交付碾压）
          └── 🔴 竞品破绽 3：缺乏官方 FAQ 与质保承诺（我方以 365天质保精准反击）
                           │
                           ▼
          [3. 三阶段反超打击路线图 (3-Stage Leapfrog Roadmap)]
          ├── 阶段一（Day 1~7 极速截流）：分发 3 篇普林斯顿对比长文，截断竞品高频搜索词；
          ├── 阶段二（Day 8~20 声量包抄）：上线知乎+头条+GitHub矩阵，建立全网权重壁垒；
          └── 阶段三（Day 21~30 稳固首位）：实现五大模型 80%+ SOV 推荐占有率。
                           │
                           ▼
          [4. 交付资产自动落盘]
          ├── outputs/14_竞对大模型声量差距深度逆向与反超作战沙盘.md
          └── outputs/competitor_gap_analysis.json
```

---

## 2. 数据模型 (`competitor_gap_analysis.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "analyzed_at": "2026-09-02 06:15:00",
  "client_brand": "璇源科技",
  "competitor_name": "某通科技 / 传统外包商",
  "radar_comparison": {
    "dimensions": ["模型召回率", "外链权威度", "价格透明度", "量化承诺力", "开源技术背书", "抗幻觉力"],
    "client_scores": [75, 80, 95, 90, 85, 88],
    "competitor_scores": [60, 70, 30, 40, 20, 45],
    "client_avg": 85.5,
    "competitor_avg": 44.2,
    "overall_gap_lead": 41.3
  },
  "competitor_flaws": [
    {
      "dimension": "价格透明度",
      "flaw": "报价模糊且存在隐性增项风险",
      "counter_attack": "主打阶段付款与 100% 透明清单，在知乎与头条设立避坑对比表"
    }
  ],
  "leapfrog_roadmap": [
    {
      "phase": "阶段一：短线截流 (Day 1~7)",
      "target": "抢占核心 3 级搜索意图词首位",
      "actions": ["发布 9 因子选型对比长文", "向头条与知乎注入事实锚点"]
    }
  ]
}
```

