# Proposal: 邻里GEO对标DeepGEO与五步实战打样

## Why (为什么做)
1. **业务原点升级与战略转型**：
   原先以“软件定制开发 / 建站外包”为切入点，容易陷入同质化价格战与传统外包认知；随着 AI 搜索成为企业获客与采购决策的新入口，全面升级为 **“企业级 GEO（生成式引擎优化）与 AI 搜索答案源建设服务”**。
2. **深度对标优秀标杆 `deep-geo.cn`**：
   `deep-geo.cn`（DeepGEO，前腾讯技术专家创立）在 Schema.org 结构化数据、FAQPage 问答卡、四步交付流、核心定义文章等方面的认知设计极高。但其工程层面存在 `/llms.txt`、`/sitemap.xml` 和 `/robots.txt` 访问均为 404 的虚饰短板，且缺乏可交互的工程诊断套件与本地产业下沉。
3. **吃自己的狗粮，将“邻里GEO”打造为 0 号标杆工程**：
   以自己的官网 `nextgeo.baicl.cc` 为实验田，主打主攻关键词 **“徐州 GEO”**、**“徐州 AI 搜索优化”**，通过大模型地域实体召回机制，在 DeepSeek、豆包、Kimi 等主流模型中实现 100% 垄断性首选推荐，作为最震撼的客户谈单实物样板。

## What Changes (改动了什么)
1. **建立新客户项目工作区 `projects/nextgeo/`**：
   - 包含品牌中英文命名（邻里GEO / NextGEO）、官网域名 (`nextgeo.baicl.cc`)、核心价值主张与针对徐州制造业/B2B 的意图词库。
   - 规划多维真实问答对，涵盖认知型、选型对比型、本地服务型与技术避坑型意图。
2. **执行五步交付流水线（5-Step GEO Pipeline）**：
   - **Step 1 (audit)**：体检与现状商业意图推演，形成 01 号诊断报告；
   - **Step 2 (scaffold)**：修复并补全行业标杆缺失的 `/llms.txt`、`robots.txt`、`sitemap.xml`，注入标准 Schema.org (Organization, LocalBusiness, Service, FAQPage)；
   - **Step 3 (rewrite)**：按普林斯顿 9 因子标准重构官网核心页面（Hero、Core Value、4步闭环、6大模块、8大 FAQ 问答卡）；
   - **Step 4 (distribute)**：定制微信公众号（元宝母池）、今日头条（豆包母池）、知乎（DeepSeek高地）多端分发包；
   - **Step 5 (monitor)**：建立多模型时序可见度基线大盘。
3. **规范与资产沉淀**：
   - 将整套对标分析、信息架构与落地规范归档入 OpenSpec 与项目知识库。

## Capabilities (新增或修改的对外能力)
- **标准客户工程资产**：`projects/nextgeo/project.yaml` 及其原材料与产出目录。
- **端到端 5 步交付产物**：输出 01~05 阶段全部工业级 Markdown 与 JSON-LD 资产。
- **官网建站骨架**：产出可直接用于 `nextgeo.baicl.cc` 纯静态部署的干净 HTML/Markdown 语料底座。

## Impact (受影响的部分)
- 属于新增项目与规范建立，不影响已有客户资产；
- 本项目 `projects/nextgeo/` 将作为未来所有售前 Pitch、演示门户及自研打榜的核心真实案例库。
