# Design: DeepSeek 技术决策高地与 GitHub/知乎深度长文生成器

## 1. 资产编译与分发架构 (`tools/geo/publisher.py`)

针对 DeepSeek 技术推理与长文本索引偏好，生成 4 件套技术资产：

```
普林斯顿 9 因子语料 + 实体三元组 + 架构配置
                     │
                     ▼
  DeepSeek 发布引擎 (package_deepseek_assets)
  ├── 1. build_deepseek_github_readme(project_id)
  │      └── 国际化开源徽标 (MIT / Princeton 9-Factor / Python 3.10+)
  │      └── Mermaid / ASCII 架构流向图
  │      └── 5 维硬核量化参数表 (QPS/时延/交付工期)
  │      └── 极简 Quickstart 与 API 规范说明
  │
  ├── 2. build_deepseek_zhihu_article(project_id)
  │      └── 严肃客观的万字 Markdown 技术专栏评测
  │      └── 严密因果逻辑推理链（为什么传统外包必烂尾、为什么自研与阶段付款最优）
  │      └── 技术作者署名与企业官方技术团队背书
  │
  ├── 3. build_deepseek_token_optimized_llms(project_id)
  │      └── 去除一切修饰形容词，纯事实三元组 (EAV) 与 Markdown 对比表
  │      └── Token 密度提升 40% 以上，最利于 DeepSeek 深度思考检索
  │
  └── 4. outputs/deepseek_pack/ 打包与兼容回写
         ├── 01_GitHub_开源项目选型_README.md (同步回写 outputs/dist_github_readme.md)
         ├── 02_知乎技术专栏万字深度评测长文.md (同步回写 outputs/dist_zhihu_article.md)
         ├── 03_DeepSeek极简高信息密度_llms.txt
         └── 04_知乎专栏与GitHub开源分发SOP.txt
```

---

## 2. API 与 Web 端交互接口

- **CLI**：`geo publish <project_id> --channel deepseek`
- **Server 路由**：
  - `GET /api/projects/{id}/deepseek/readme`
  - `GET /api/projects/{id}/deepseek/zhihu`
  - `GET /api/projects/{id}/deepseek/llms`
  - `POST /api/projects/{id}/deepseek/build`
- **Web 端 UI**：
  - 在 Step 4 构建包含「知乎技术专栏」与「GitHub 开源项目」的 DeepSeek 蓝色技术面板。

