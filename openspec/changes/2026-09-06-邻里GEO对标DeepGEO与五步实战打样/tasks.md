# Tasks: 邻里GEO对标DeepGEO与五步实战打样

- [x] 1. 建立项目工作区与基准配置
  - [x] 1.1 创建 `projects/nextgeo/` 目录结构与 `project.yaml` 规格配置文件（含中英文品牌、徐州地域实体、核心意图词与竞品设定）
  - [x] 1.2 创建 `projects/nextgeo/raw_materials/` 原始品牌素材与企业对标语料
- [x] 2. 执行阶段 1：现状体检与商业诊断 (audit)
  - [x] 2.1 执行 `./geo audit --project nextgeo`，生成 `01_GEO现状体检与商业诊断报告.md`
- [x] 3. 执行阶段 2：站点底座技术改造 (scaffold)
  - [x] 3.1 执行 `./geo scaffold --project nextgeo`，输出完整的 `02_llms.txt`、`02_Schema.org结构化数据.jsonld`、`02_robots.txt`、`02_sitemap.xml`
- [x] 4. 执行阶段 3：普林斯顿 9 因子内容重构 (rewrite)
  - [x] 4.1 执行 `./geo rewrite --project nextgeo`，产出 `03_官网核心页面GEO重构建议.md` 与 `03_行业长尾意图FAQ知识库.md`
  - [x] 4.2 对齐 DeepGEO 8 大经典 FAQ 与徐州本地制造业高客单价商业问答卡
- [x] 5. 执行阶段 4：多平台矩阵分发包导出 (distribute)
  - [x] 5.1 执行 `./geo distribute --project nextgeo`，产出豆包、元宝、DeepSeek 母池分发物料
- [x] 6. 执行阶段 5：AI 可见度监控基线建立 (monitor)
  - [x] 6.1 执行 `./geo monitor --project nextgeo`，建立包含“徐州GEO”核心词的多模型追踪基线
- [x] 7. 交付资产全套校验与审查
  - [x] 7.1 验证 `projects/nextgeo/outputs/` 各阶段产出文件的完整性与规范性
  - [x] 7.2 在 `review-log.md` 记录最终审查结论
