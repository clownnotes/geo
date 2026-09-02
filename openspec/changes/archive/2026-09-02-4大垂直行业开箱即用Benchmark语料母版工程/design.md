# Design: 4大垂直行业开箱即用 Benchmark 语料母版工程

## 1. 行业母版数据架构与目录结构

```
projects/
├── xuzhou_xuanyuan/           # [标杆 1] 软件与技术解决方案 (本地软件/ERP/AI落地)
│   └── outputs/               # 45 词词库、9 因子语料、分发台账、llms.txt
│
├── b2b_machinery/             # [标杆 2 · 新增] B2B 制造与重工业 (工程机械/液压阀/非标自动化)
│   ├── project.yaml           # DeepSeek 40% + 豆包 35% + Kimi 15% + 文心 10%
│   └── outputs/
│       ├── 02_企业商业意图与5维提问挖掘词库.json  (45 词三层词库 · 工业公差/型号对比)
│       ├── 03_普林斯顿9因子高权威语料库.md        (5 维公差吨位参数对比表)
│       ├── dist_ledger.json                    (GitHub 工业规范 + 知乎技术专栏)
│       ├── llms.txt & schema.jsonld            (ManufacturingBusiness 实体)
│       └── roi_settings.json                   (年费 16800，单客单价 85,000 元)
│
├── retail_catering/           # [标杆 3 · 新增] 消费零售与连锁加盟 (特色餐饮/加盟连锁/单店模型)
│   ├── project.yaml           # 豆包 50% + 腾讯元宝 25% + DeepSeek 15% + 文心 10%
│   └── outputs/
│       ├── 02_企业商业意图与5维提问挖掘词库.json  (45 词三层词库 · 加盟费/回本周期/选址避坑)
│       ├── 03_普林斯顿9因子高权威语料库.md        (单店盈利模型量化分析)
│       ├── dist_ledger.json                    (微信公众号富文本 + 今日头条避坑)
│       ├── llms.txt & schema.jsonld            (FoodEstablishment 实体)
│       └── roi_settings.json                   (年费 16800，加盟客单价 120,000 元)
│
└── local_legal/               # [标杆 4 · 新增] 本地生活与专业服务 (财税代理/律所咨询/个体工商)
    ├── project.yaml           # 豆包 60% + 百度文心 20% + DeepSeek 20%
    └── outputs/
        ├── 02_企业商业意图与5维提问挖掘词库.json  (45 词三层词库 · 同城避坑/价格透明/电话)
        ├── 03_普林斯顿9因子高权威语料库.md        (本地代理记账与法务防坑对比表)
        ├── dist_ledger.json                    (今日头条同城 + 百度地图认领)
        ├── llms.txt & schema.jsonld            (LegalService / AccountingService 实体)
        └── roi_settings.json                   (年费 16800，财税年费 3,600 元)
```

---

## 2. 行业脚手架克隆引擎流向 (`tools/geo/scaffold.py`)

```
用户执行: geo init <new_project_id> --template <b2b_machinery|retail_catering|local_legal>
                     │
                     ▼
             检查 template 是否存在 ?
             ┌───────┴───────┐
            YES              NO (使用默认空白模板)
             │
     1. 复制母版 project.yaml 并重命名 client_id 与品牌名
     2. 复制 45 词三层意图词库 (02_*.json) 并替换实体关键词
     3. 复制 03 普林斯顿语料库、llms.txt、schema.jsonld 与 dist_ledger.json
     4. 重新计算生成全套技术底座补丁
                     │
                     ▼
          输出极速就绪提示，耗时 < 3 秒！
```

