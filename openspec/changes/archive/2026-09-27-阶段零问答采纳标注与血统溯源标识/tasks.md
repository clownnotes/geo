# Tasks: 阶段零问答采纳标注与血统溯源标识

## 1. 数据模型与状态管理扩展
- [x] 1.1 在 `Step0App.vue` 中扩展 `files` 数据结构，支持 `isActive`、`versionTag`、`pairFile` 属性初始化与历史数据向下兼容。
- [x] 1.2 编写 `handleAdoptFile(fileName)` 采纳切换函数，实现单底牌互斥、版本号自动递增（`QA-V1` -> `QA-V2`）与文件首行元数据更新。
- [x] 1.3 改造 `handleFinishStage0`，持久化 `activeQaVersion`、`activeQuestionFile`、`activeAnswerFile` 至纯前端 `localStorage`（严禁修改后端文件）。
- [x] 1.4 在 `Step0App.vue` 中增加阶段零文件字典本地持久化（`geo_step0_files_${clientId}`），使新生成的题目版本刷新后不丢失。
- [x] 1.5 强化 `initDefaultFiles` 加载双向一致性校验：若 `activeQuestionFile` 不在 `files` 中，执行回退并同步回写修正 `localStorage`，版本号重置为 `QA-V1`。

## 2. UI 界面视觉与交互联动 (严禁 Emoji，统一采用 Lucide 图标)
- [x] 2.1 改造 `StudioFileTree.vue`，在文件条目右侧增加【已采纳 [QA-V1]】徽章（配合 Lucide check 图标）。
- [x] 2.2 改造 `StudioEditor.vue`，在顶栏展示当前文件生效状态与【设为客户采纳】操作按钮（配合 Lucide star 图标），并向父组件派发 `adoptFile` 事件。
- [x] 2.3 改造 `Step0App.vue` 中的生成新题目逻辑（`handleRefreshQuestions`），新生成的题目默认为草稿态，支持专家手动打磨后点击采纳。

## 3. 下游链路溯源闭环与阶段一消费
- [x] 3.1 改造 `stage1Config.js` 中的 `resolveContext` 与 `buildStage1Files`，支持解析本地存储的生效底牌与版本号。
- [x] 3.2 在阶段一素材（`01_阶段零豆包实测问答素材.md`）及初稿头部显式印制溯源血统盖章。

## 4. 跨端验证与全流程回归
- [x] 4.1 使用 `./scripts/verify-2019pro-safari.sh` 在 2019 PRO 既有标签页中验证阶段零出题与采纳徽章切换。
- [x] 4.2 验证在阶段零生成新版题目并设为采纳后，版本号正确递增为 `QA-V2`，且回答文件成功继承。
- [x] 4.3 验证通关阶段零进入阶段一后，阶段一问答素材头部精准印制阶段零对应的生效版本号与溯源戳。
