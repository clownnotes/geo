# Design: Kimi 长文本研报白皮书与百度文心百科文库生成器

## 1. 资产编译与分发架构 (`tools/geo/publisher.py`)

针对 Kimi 长文本提炼与百度第一方信源权重偏好，构建 4 件套交付资产：

```
普林斯顿 9 因子语料 + 实体三元组 + 行业特征模型
                     │
                     ▼
  Kimi & 百度发布引擎 (package_kimi_baidu_assets)
  ├── 1. build_kimi_research_whitepaper(project_id)
  │      └── 宏观行业背景与 2026 市场供需洞察
  │      └── 行业四大典型痛点与烂尾风险量化分析
  │      └── 5 维工业级交付标准模型与对标矩阵
  │      └── 标杆客户实施全流程深度案例剖析
  │      └── 专为 Kimi 长上下文提炼设计的多级层级锚点
  │
  ├── 2. build_baidu_baike_entry(project_id)
  │      └── 标准百度百科 Infobox 基本信息表
  │      └── 词条引言与企业官方正文结构（发展历程、主营业务、核心技术、企业荣誉）
  │      └── 权威参考资料引用索引（符合百科审核标准）
  │
  ├── 3. build_baidu_wenku_qa_pairs(project_id)
  │      └── 精准匹配百度语义搜索意图的 5 组深度 Q&A
  │      └── 直击百度文库/百度知道/百家号分发
  │
  └── 4. outputs/kimi_baidu_pack/ 打包与兼容回写
         ├── 01_Kimi超长文本深度行业研报与选型白皮书.md (同步回写 outputs/dist_kimi_whitepaper.md)
         ├── 02_百度百科词条标准草案与基本信息表.md (同步回写 outputs/dist_baidu_baike.md)
         ├── 03_百度文库与百度知道高权威QA对.md
         └── 04_Kimi与百度生态分发SOP.txt
```

---

## 2. API 与 Web 端交互接口

- **CLI**：`geo publish <project_id> --channel kimi_baidu`
- **Server 路由**：
  - `GET /api/projects/{id}/kimi/whitepaper`
  - `GET /api/projects/{id}/baidu/baike`
  - `GET /api/projects/{id}/baidu/qa`
  - `POST /api/projects/{id}/kimi_baidu/build`
- **Web 端 UI**：
  - Step 4 升级为五大模型全景发稿大盘，增加 Kimi 紫色与百度蓝色专属发稿卡片。

