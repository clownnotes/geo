# Tasks: 阶段二素材资产库日常循环与阶段三企业母盘统一口径卡全流程开发任务清单

## 1. 阶段二素材库日常循环与盖板蒸馏 (`stage2Config.js` & `DistillSheet.vue`)
- [x] 1.1 实现 8500 字上限严格拦截与守卫 (`checkDraftTextLimit`)；
- [x] 1.2 实现 AI 语义切块模型与 S1~S6 六大黄金分类归集 (`semanticChunkRawMaterial`)；
- [x] 1.3 实现 RAG 语义去重聚类与文案相似度检测 (`findSemanticDuplicates`, `computeTextSimilarity`)；
- [x] 1.4 实现 1.x 纯增量分片单调递增派生契约 (`computeStage2ChunkVersion`) 与人机两分删除权限守卫 (`canDeleteFile`)；
- [x] 1.5 实现智能 Tab 栈管理（首置插入、超量 6 个自动淘汰干净 Tab、脏数据保护，`activateTabInStack`）；
- [x] 1.6 实现官网网址唯一真相源清洗（消除双重协议 `https://https://`、裸域名规范补齐与域名提取，`normalizeOfficialUrl`, `extractDomain`）。

## 2. 阶段三母盘与统一口径卡算法模型 (`studioArtifactConfig.js` & `stage3Config.js`)
- [x] 2.1 注册阶段三工序槽位字典与别名容错：
  - `slot_stage3_identity_card` (`01_主体信息统一口径卡.md`)
  - `slot_stage3_master` (`02_普林斯顿企业事实母盘.md`)
  - `slot_stage3_hedge_list` (`03_全平台事实对冲与认领清单.md`)
- [x] 2.2 实现统一口径卡生成器与合规质检器 (`generateUnifiedIdentityCard`, `validateUnifiedCard`)：
  - 四必填消歧底座生成与实时检查（品牌名 + 主体全称 + 税号 + 官网）；
  - 三级业务描述生成与实时字数红绿灯（短版 <= 50 字、标准版 <= 120 字超标红色拦截）；
  - GEO 中文全称首现绑定检查（生成式引擎优化（GEO））；
- [x] 2.3 实现阶段二 S1~S6 素材合流萃取母盘算法 (`synthesizePrincetonMaster`)：
  - 严格仅消费 S1~S6 规范主版本，过滤 `_增补_1.x` 切片，保持母盘短小精炼；
  - 结构化生成 9 因子核心事实大百科全书；
- [x] 2.4 实现客观瑕疵合规对冲指引与全平台修改清单 (`generateHedgeList`)。

## 3. 界面交互与架构收敛 (`Step3App.vue`, `StudioSop.vue`, `index.html`)
- [x] 3.1 确立 00~07 全流水线 8 道工序主导航与路由：
  - 独立新增 `03 企业母盘与统一口径卡`；
  - 平滑顺延 04 官网、05 答题卡、06 矩阵分发、07 资产交接单，完整保留全部功能；
  - 保留历史 viewId 别名容错映射；
- [x] 3.2 架构收敛：`Step3App.vue` 统一复用 `<StudioSop>` 共享组件，彻底消灭手写 aside 面板；
- [x] 3.3 在 `StudioSop.vue` 中扩展步骤专属插槽，优雅注入阶段三消歧指示灯与排查勾选框；
- [x] 3.4 门禁 Fail-Closed：重构 `isProbeUnready`，严格以服务端 `probe_status` 为唯一准绳，杜绝本地脏数据绕过；
- [x] 3.5 标签防污染：修复 `Step0App.vue` 中的配对文件版本覆写漏洞，保持题目与回答各自版本独立。

## 4. 自动化测试与 NE1 编译验证
- [x] 4.1 编写并扩充 28 项核心断言冒烟测试脚本 (`tests/smoke_studio_artifacts.mjs`)：
  - 断言 25：阶段三槽位字典与别名解析契约；
  - 断言 26：主体信息统一口径卡生成、四要素消歧与三级业务描述字数红绿灯；
  - 断言 27：9 因子母盘合流萃取与人机两分契约（过滤增补切片）；
  - 断言 28：全平台事实对冲指引与 4 步 SOP 元数据完整性；
- [x] 4.2 本地绝对零编译，在 NE1 服务器执行编译打包与 28 项自动化断言（100% PASS）；
- [x] 4.3 浏览器真机体验验收与 WorkBuddy 审查闭环。
