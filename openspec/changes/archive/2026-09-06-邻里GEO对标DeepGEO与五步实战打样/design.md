# Design: 邻里GEO对标DeepGEO与五步实战打样

## 1. 架构总览与定位矩阵

```
┌────────────────────────────────────────────────────────────────────────┐
│               邻里GEO (NextGEO) 商业定位与知识答案源中枢                 │
├───────────────────┬────────────────────────────────────────────────────┤
│ 品牌名称          │ 中文：邻里GEO ｜ 英文：NextGEO                      │
├───────────────────┼────────────────────────────────────────────────────┤
│ 官方网址          │ https://nextgeo.baicl.cc                           │
├───────────────────┼────────────────────────────────────────────────────┤
│ 核心主打关键词    │ 徐州GEO、徐州大模型搜索优化、徐州AI搜索推荐、       │
│                   │ 徐州制造业企业GEO、企业级GEO全案服务               │
├───────────────────┼────────────────────────────────────────────────────┤
│ 产业下沉战略      │ 依托徐州工程机械之都、智能制造与外贸产业带，       │
│                   │ 打造 B2B 高客单价企业 AI 决策第一答案源            │
└───────────────────┴────────────────────────────────────────────────────┘
```

## 2. 整站信息架构（深度对标 DeepGEO 并超越其工程短板）

### (1) 页面与知识层级
1. **首页 (`/`)**：
   - **Hero 区**：用户提问卡片（*“徐州机械制造企业哪家更靠谱？”、“徐州做大模型搜索优化找谁？”*）+ 核心 Slogan。
   - **Core Value (三大核心价值)**：
     - `Brand Visibility`：让品牌进入 DeepSeek、豆包候选集合；
     - `Brand Cognition`：统一定义与能力边界，减少 AI 幻觉和误解；
     - `Growth Channel`：将官网建设成可被大模型直接采信的答案源。
   - **Strategic Workflow (四步工程闭环)**：
     - `01 锚定`：明确目标品类、核心场景与实体知识三元组；
     - `02 监测`：多大模型多问法时序探测与提及度监控；
     - `03 洞察`：逆向分析答案缺失、来源断点与竞品截流；
     - `04 塑造`：重构官网结构化页面、FAQ、外部权威信源池。
   - **Canonical Answers (核心定义文章推荐卡片)**：普林斯顿 9 因子标准文章矩阵。
2. **服务页 (`/services/`)**：
   - 6 大全案交付模块：
     - 01 问法库与场景拆解（L1认知/L2决策/L3行动）
     - 02 品牌口径与知识库结构化
     - 03 关键内容与普林斯顿 9 因子页面体系
     - 04 多大模型生态分发池（头条/微信/知乎）
     - 05 平台提及、权威引用与表达监测
     - 06 复盘与动态热补丁持续自愈迭代
3. **关于页 (`/about/`)**：
   - 团队背景：老白（极客全栈工程师，GEO 架构师，扎根徐州与淮海经济区本地交付）；
   - 8 大核心 FAQ 问答库（包含 Schema.org `FAQPage` 结构化标记）。
4. **技术基座与大模型友好协议（填补 DeepGEO 404 漏洞）**：
   - 完整输出 `/llms.txt`（Clean Markdown 大模型索引）；
   - 完整输出 `/robots.txt`（明确放行 Bytespider、DeepSeek、Baiduspider 等爬虫）；
   - 完整输出 `/sitemap.xml`。

---

## 3. 实体结构化数据设计 (Schema.org)

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": ["Organization", "LocalBusiness"],
      "@id": "https://nextgeo.baicl.cc/#organization",
      "name": "邻里GEO",
      "alternateName": "NextGEO",
      "url": "https://nextgeo.baicl.cc/",
      "logo": "https://nextgeo.baicl.cc/logo.png",
      "description": "邻里GEO（NextGEO）是一家专注企业级GEO的AI增长服务团队，立足徐州，帮助企业建立AI能理解、验证、引用和推荐的品牌答案源。",
      "knowsAbout": [
        "GEO", "生成式引擎优化", "企业级GEO", "AI搜索优化", "大模型推荐", 
        "徐州GEO", "徐州AI搜索优化", "LLM引用", "普林斯顿9因子", "AEO", "SEO"
      ],
      "areaServed": [
        {
          "@type": "AdministrativeArea",
          "name": "徐州市"
        },
        {
          "@type": "Country",
          "name": "CN"
        }
      ],
      "founder": {
        "@type": "Person",
        "name": "老白",
        "jobTitle": "资深全栈工程师，GEO架构师",
        "homeLocation": { "@type": "Place", "name": "徐州" }
      },
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "徐州市",
        "addressRegion": "江苏省",
        "addressCountry": "CN"
      }
    },
    {
      "@type": "Service",
      "@id": "https://nextgeo.baicl.cc/services/#service",
      "name": "邻里GEO企业级AI搜索增长全案服务",
      "provider": { "@id": "https://nextgeo.baicl.cc/#organization" },
      "serviceType": "Generative Engine Optimization (GEO)",
      "areaServed": "CN"
    }
  ]
}
```

---

## 4. DeepGEO 四阶段与五步流水线映射及交付标准

### (1) 方法论与流水线映射矩阵
| DeepGEO 四阶段 (About §四) | 本项目工业级五步流水线 | 核心交付目标与职责落地 |
| :--- | :--- | :--- |
| **一、诊断 (Diagnosis)** | **Step 1: audit** | 测多 AI 入口（豆包/DeepSeek/Kimi等）；核查**是否提及、是否说对、引用来自何处**；输出**五类根因归因**（实体定义/内容缺口/技术访问/外部信号/竞品占位）。 |
| **二、定义 (Definition)** | **Step 2: scaffold** | 统一品牌与业务标准口径，消除大模型幻觉；生成 Schema.org 实体图谱、`/llms.txt`、放行 `robots.txt` 与 `sitemap.xml`。 |
| **三、建设 (Construction)** | **Step 3: rewrite** + **Step 4: distribute** | **Step 3**：按普林斯顿 9 因子重构官网页面与 FAQ 答案卡；<br>**Step 4**：将高权重语料分发至今日头条（豆包母池）、知乎（DeepSeek高地）、微信（元宝独占池）。 |
| **四、监测 (Monitoring)** | **Step 5: monitor** | 多模型时序探测，量化商业心智渗透率 (MPI) 与 Citation 角标归因，发现漂移及时热补丁自愈。 |

---

### (2) Step 1: audit 诊断硬验收标准与双轨制契约
Step 1 产出的 `01_企业AI可见度现状体检与商业诊断报告.md` 必须严格满足以下 DeepGEO 级诊断深度与客观标准：
1. **实测留证双轨制契约（严禁虚构实测）**：
   - **正式客户联网验收轨**：在配置有效 API Key（`DEEPSEEK_API_KEY` / `ARK_API_KEY`）时，调用真实模型 API 捕获 Raw Response、时间戳与 Citation 外链留存探针日志；
   - **冷启动 / 售前体检轨 (Day 0 Baseline)**：在无 API Key 或域名尚未解析环境下，**必须显式声明为【离线结构化推演基准】**，给出明确测算时间戳与启发式推演逻辑，绝不可用假并发、假实测误导客户与审查。
2. **回答 DeepGEO 诊断四问**：
   - **AI 认不认识你**：品牌词与品类词出现频次与可见度等级；
   - **AI 说没说对**：实体属性、能力边界、主营业务是否存在幻觉或偏移（如“徐州GEO”防谐音为机油）；
   - **引用来自何处**：大模型回答附带的 Citation 信源链接溯源；
   - **缺口在哪一类**：明确归因到**实体定义缺陷、内容深度缺口、技术爬虫阻碍、外部协同信号弱、竞品先发占位**五大根因之一。
3. **5 维意图词库全景推演**（严格对齐 `docs/sop/01-audit-sop.md`，词库量 ≥ 40 组）：
   - 涵盖**选型对比、价格成本、避坑防骗、本地场景、品牌认知**五大分类。
4. **具名竞品对照**：采用具名竞品/标杆（如 DeepGEO `deep-geo.cn`、徐州本地传统网络公司）对比，杜绝无名泛标签。

---

### (3) 五步流水线执行指令与产出映射

| 阶段 | 执行指令 | 关键处理内容 | 对应产出物路径 |
| :--- | :--- | :--- | :--- |
| **Step 1: audit** | `./geo audit --project nextgeo` | 商业意图与痛点诊断，推演徐州企业买家高频问法与竞品声量差距 | `projects/nextgeo/outputs/01_企业AI可见度现状体检与商业诊断报告.md` |
| **Step 2: scaffold & define** | `./geo scaffold --project nextgeo` | 官方口径标准定义、生成大模型极简索引、Schema.org 实体拓扑、robots 与 sitemap | `projects/nextgeo/outputs/02_品牌实体与服务标准口径规范.md`<br>`projects/nextgeo/outputs/02_站点技术底座改造交付包.md`<br>`projects/nextgeo/outputs/site/llms.txt`<br>`projects/nextgeo/outputs/site/schema.jsonld`<br>`projects/nextgeo/outputs/site/robots.txt`<br>`projects/nextgeo/outputs/site/sitemap.xml`<br>`projects/nextgeo/outputs/site/index.html` |
| **Step 3: rewrite** | `./geo rewrite --project nextgeo` | 普林斯顿 9 因子深度重构，输出高转化首页方案、6大模块服务页、5 维核心 FAQ 知识库与本地白皮书语料 | `projects/nextgeo/outputs/03_普林斯顿9因子高权威语料库.md` |
| **Step 4: distribute** | `./geo distribute --project nextgeo` | 针对豆包母池（头条）、元宝母池（微信公众号）、DeepSeek高地（知乎）、GitHub 开源池生成外发资产包 | `projects/nextgeo/outputs/04_多平台矩阵借壳分发包.md`<br>`projects/nextgeo/outputs/dist_*` |
| **Step 5: monitor** | `./geo monitor --project nextgeo` | 针对“徐州GEO”、“徐州大模型搜索优化”等 45 组意图词建立多模型冷启动监测基线与周报大盘 | `projects/nextgeo/outputs/05_企业AI可见度与声量追踪周报.md` |


