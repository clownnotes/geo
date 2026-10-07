# Tasks: 全流水线主文件预置、参考比对件与标准 5 点质检落地任务

## 1. 概念与规则探讨（Grill-me 探讨阶段）
- [x] 1.1 与师弟对齐文件初始生成时机：正式确立【建档即预置第一版主文件，后续生成逐步丰富更新】；
- [x] 1.2 与师弟对齐全流水线版本管理模式：废除 1.1/1.2，确立【主文件（打勾/不可删/可改）+ 参考生成件（1/2/3后缀/供人工对比采纳）】铁律；
- [x] 1.3 与师弟对齐更新交互动线：确立【左右双栏比对 + 人工挑词手动复制粘贴更新】，严禁机器一键覆盖冲毁主文件；
- [x] 1.4 与师弟对齐标准【5 点质检模型】：①主文件存在、②脱离空模板、③字数达标、④四要素齐备、⑤人工确认就绪；
- [x] 1.5 与师弟对齐主文件视觉：彻底消除 V1/QA-V1 及笨重文字，统一在文件名右侧展示高辨识度【晨光淡黄对勾 `✓`】；
- [x] 1.6 与师弟对齐主文件人工改名架构：允许人工自由重命名，底层以唯一雪花 ID (Snowflake ID) 与 slotKey 稳定锚定；
- [x] 1.7 与师弟对齐界面空间极致优化：彻底取消文件左侧无用文件图标，释放宝贵的横向宽度，让文件名一目了然看全看清；
- [x] 1.8 与师弟对齐隐藏扩展名：界面全域不展示 `.txt`、`.md`，统一展示干净的主名称；
- [x] 1.9 与师弟对齐电脑桌面级右键改名：右键唤起【修改名称】，行内编辑回车存盘，操作零弹窗零打扰；
- [x] 1.10 与师弟对齐改名权限与重名拦截：仅主文件支持改名，参考件由系统自管编号；重名时前端强提示“名称已存在”并恢复原名。

## 2. 规范方案归档与实施准备
- [x] 2.1 同步更新 proposal.md / design.md / tasks.md / review-log.md；
- [x] 2.2 师弟发起 `/opsx-review-workbuddy`，进入【三写两审两修】代码先行与规范反哺流程。

## 3. 全局架构与工序全量改造登记 (Diff 全貌追溯)
- [x] 3.1 【前端工序与组件全量升级】：
  - [x] 抽取统一双行工作台头部组件 `StudioHeader.vue` (状态徽章/只读提示/字数时间/Tab栏)；
  - [x] 抽取素材语义切块与蒸馏抽屉 `DistillSheet.vue` (8500 字上限管控与智能分类)；
  - [x] `web/index.html` 完成阶段 00~07 全流水线重编号（含 03 母盘、04 官网、05 答题卡等）与 `LEGACY_VIEW_REDIRECT_MAP` 双向重定向平滑兼容；
  - [x] `Step0App.vue` ~ `Step7App.vue` 及对应 `stageConfig`、`useStep` 完成主文件挂载与动线对齐；
- [x] 3.2 【后端建档配置完整性保护与防丢】：
  - [x] `tools/geo/utils.py` `update_project_profile`：标量清单扩充（`probe_status`、`brand_name`、`company_name` 等）；
  - [x] `tools/geo/utils.py` `update_project_profile`：新增 `models`、`member_user_ids` 列表字段持久化，杜绝项目更新静默丢数据；
  - [x] `tools/geo/server.py`：统一复用 `update_project_profile` 单一真相源；
- [x] 3.3 【主文件预置、参考比对件与防冲毁实现】：
  - [x] `studioArtifactConfig.js`：导出 `isMasterFile`、`computeReferenceVersion`、`getMasterFileForSlot`、`evaluate5PointCheck`，且锁定 `canDeleteFile` 物理禁止删除主文件；
  - [x] `Step0App.vue`：建档即预置主文件，重新出题派生 `_参考N.txt`，配对文件严格互指预置主文件，彻底删除派生 `_第1版.txt` 抢占 active 的双轨冗余逻辑；
  - [x] `StudioEditor.vue`：透出参考比对件徽章，`canAdoptCurrentFile` 拦截参考件整篇采纳覆盖，确保主文件神圣不被冲毁。

## 4. 自动化测试与审查流转（三写两审两修）
- [x] 4.1 【第 1 次写代码与第 1 次审查】：
  - [x] 落实全流水线主文件预置、参考候选件派生、晨光淡黄打勾、雪花 ID、全域隐藏扩展名与桌面级右键改名；
  - [x] 新增断言 29、30、31、32，NE1 服务器冒烟 32/32 项自动化断言全部 PASS；
- [x] 4.2 【第 1 次修复代码 + 规范反哺】：
  - [x] 规范反哺：proposal/design/tasks 消除歧义，对齐 32 项自动化断言真相源；
  - [x] 修复 `workbuddy_reviewer.py` git status 中文路径 `-c core.quotepath=false` 避免转义失效；
  - [x] 修复 `smoke_step0.sh` 与 `smoke_studio_artifacts.mjs` 统一为 32 项断言；
- [x] 4.3 【第 2 次修复代码 + 终局写代码】：
  - [x] 修复 R1：`stripExtension` 订正为白名单真实扩展名匹配，严密保护 1.1 / V2.0 等小数点业务版本号；
  - [x] 修复 R2：`design.md` 补全 00~07 全流水线架构映射矩阵与向后兼容契约；
  - [x] 修复 R3：`isProbeUnready` 补全空状态 `unprobed` 显式兜底；
  - [x] 经 NE1 服务器（100.83.64.112:8088）冒烟 32/32 项断言全部 100% PASS！
- [ ] 4.4 【终局交付师弟真机验收】：3 轮硬熔断强制停止，交付师弟真机体验裁决！

## 5. 只读限制解绑与全域编辑自由（轮次五探讨落地）
- [x] 5.1 【只读判定纯函数与组件重构】：
  - [x] 改造 `studioArtifactConfig.js` 中 `isReadOnlyFile`：仅保留 `file.isDeleted || file.is_deleted`（废纸篓）作为唯一只读条件，全域解除历史母版、规范镜像、淘汰草稿的只读限制；
  - [x] 同步优化 `StudioEditor.vue` 与 `StudioHeader.vue`，清理非废纸篓下的禁止光标与生硬只读标签；
  - [x] 更新 `tests/smoke_studio_artifacts.mjs` 中涉及 `isReadOnlyFile` 的相关断言，确保 NE1 冒烟继续 100% PASS。
- [x] 5.2 【全工序零锁自由穿梭与文件事实探活】：
  - [x] 彻底拔除 `web/index.html` 中的 `confirm` 弹窗拦截（违背 RULES.md 4.4）与 `targetView = 'step-0-probe'` 强行回退逻辑；
  - [x] 改造 `isProbeUnready`：不再机械绑定 `probe_status` 字符串，改为基于主文件事实（`02_豆包实测回答记录` 存在、非空、字数达标）进行自适应动态就绪判定；
  - [x] 确保 00~07 各阶段工序在左侧菜单自由点击平滑穿梭，零弹窗、零打扰。

## 6. 阶段三母盘与统一口径卡 SOP 正统重构（轮次十三探讨落地）
- [x] 6.1 【精简文件树对象 (SSOT)】：废除孤立的 `03_全平台事实对冲与认领清单.md`，将其完整合流回收进 `01_主体信息统一口径卡.md`，保持阶段三仅有两大核心资产；
- [x] 6.2 【确立阶段三两大核心主文件】：
  - `01_主体信息统一口径卡.md`：企业全网标准数字身份证（消歧四要素 + 短版≤50字/标准版≤120字三级业务描述 + 逐平台打扫卫生操作指引 + 客观瑕疵对冲说明）；
  - `02_普林斯顿企业事实母盘.md`：企业事实真理总库（六模块事实大字典，供人类查证，严禁直接喂给 AI）；
- [x] 6.3 【SOP 步骤全面采用老赵哥大白话】：
  - 重写 `stage3Config.js` 中的 `STAGE_3_META.sopSteps` 文案：
    - 步骤 1：【核定企业数字身份证】（消歧四要素齐备 + 50/120字红绿灯质检）；
    - 步骤 2：【打扫全网卫生逐平台整改】（天眼查/启信宝/爱企查/BOSS直聘/地图认领修改备忘）；
    - 步骤 3：【提炼六模块事实真理字典】（从 S1~S6 生效主文件提纯产品/客户/差异/案例/背书六大抽屉）；
    - 步骤 4：【5分钟抽题自检硬标准】（老赵哥硬门槛：随机抽题 5 分钟内能否在母盘找到答案依据）；
- [x] 6.4 【字数红绿灯质检规则与模板校准】：严格按照老赵哥标准版 ≤120 字、短版 ≤50 字实施红绿灯核验，防止超出平台字数限制被截断；
- [x] 6.5 【NE1 自动化冒烟守护】：更新 `tests/smoke_studio_artifacts.mjs`，覆盖阶段三双主文件与 SOP 配置，确保实机断言 100% PASS。

## 7. 主文件 SSOT 唯一定位与改名拦截纠偏（轮次十五探讨落地 · 方案 A）
- [x] 7.1 【主文件判定纯函数彻底收敛】：
  - [x] 改造 `studioArtifactConfig.js` 中 `isMasterFile`：全仓严格按 `file.isMaster === true` 或 `file.isActive === true && !file.isDeleted && !file.is_deleted && !file.isReference && !file.versionTag?.startsWith('参考') && !file.name?.includes('_参考')` 判定，**禁止**再用 `isProtectedArchive` / `isRetired` 一票否决当前生效主文件；

  - [x] 同步订正 `getMasterFileForSlot`：选取 active 主文件时不得因历史 `isProtectedArchive` 标记跳过当前生效件；
  - [x] 优化 `migrateAndNormalizeFiles`：废除对 `_第1版` 强制赋 `isProtectedArchive` 的存量迁移规则，严禁历史归档污染当前生效的主文件；
- [x] 7.2 【文件树与改名拦截口径 100% 对齐】：
  - [x] 统一 `StudioFileTree.vue` 的晨光淡黄打勾展示、右键改名唤起条件与各阶段 `handleRenameFile` 改名拦截条件，全部收敛调用同一 `isMasterFile()`，确保凡显示为主文件者均可平滑改名；
- [x] 7.3 【自动化断言与实测回归】：
  - [x] 在 `tests/smoke_studio_artifacts.mjs` 中补充：① `isMaster=true` 且误带 `isProtectedArchive` 时 `isMasterFile===true`；② `_第1版` 命名的生效主文件可改名；③ 参考件仍禁止改名。NE1 冒烟须继续全绿。








## 8. 纯源码对外协作仓库与白名单双向同步工具建设 (2026-10-07 师弟立规)
- [x] 8.1 【白名单导出与同步脚本建设】：
  - 编写 `scripts/sync_export_to_core_repo.sh`，以严格白名单方式提取 `web/`、`tools/`、`gateway/` 与最小运行依赖（`package.json`、`requirements.txt`）；
  - 物理排除 `docs/`、`openspec/`、`tests/`、`scripts/`、`deploy/`、`projects/` 与 `.env`；
- [x] 8.2 【协作代码拉取与合流脚本建设】：
  - 编写 `scripts/sync_pull_from_core_repo.sh`，在师弟合并 PR 后，一键将协作仓代码精准同步回主工程源码目录；
  - 协作者新增的文档/文件夹保持清晰可见，合入时清晰可读、能看懂、逻辑对齐；
- [x] 8.3 【零预设纯净交付】：
  - 坚决不预置任何多余模板或框架，仅提供纯前后端源码与运行依赖，给朋友完全自由的折腾空间；
- [x] 8.4 【白名单与安全性离线验证】：
  - 离线测试导出目录，确保战略文档与机密数据 100% 零泄露，测试脚本与生产脚本 100% 隔离。

## 9. 纯源码极简提取与新仓库交付 (2026-10-07 师弟立规)
- [ ] 9.1 【原主仓纹丝不动】：保持 `/Users/a1/代码/GEO` 结构、文档、配置 100% 现状原样不动；
- [ ] 9.2 【纯源码提取到新目录】：将纯业务源码（`web/`、`tools/`、`gateway/`、`package.json`、`requirements.txt`）单向提取到指定新仓库目录（如 `/Users/a1/代码/GEOChen`）；
- [ ] 9.3 【新仓库 Git 初始化】：在新目录执行 `git init -b main` 并生成首次提交，等待师弟关联远程仓库推给朋友。

## 10. GEO 主工程根目录瘦身与源码集中收纳 (2026-10-07 师弟立规)
- [x] 10.0 【本地安全快照门禁】：在文件平移前完成本地 Git 提交留痕（信息：`chore: 建立本地安全快照基线（准备平移源码至 src/）`），建立全绿基线物理回滚点；
- [x] 10.1 【创建统一源码目录】：在根目录创建 `src/`，将散落的业务源码（`web/`、`tools/`、`gateway/`）集中下沉至 `src/` 下；
- [x] 10.2 【对齐后端服务寻址】：更新 `src/tools/geo/utils.py` 与 `server.py` 的项目根路径与静态资源托管路径；
- [x] 10.3 【对齐前端与入口命令】：更新 `package.json` 中的脚本前缀路径与根目录 `./geo` 启动命令；
- [x] 10.4 【自动化冒烟回归守护】：更新 `tests/smoke_studio_artifacts.mjs` 测试引用路径，实跑确保 32 项断言 100% PASS；
- [x] 10.5 【Qoder 外部审查与阻断修复闭环】：响应 Qoder 审查，完成 `src/gateway/main.go`（默认绑定 127.0.0.1、基于 ProjectRoot 寻址、长连接写超时放行、路径穿越与 SSRF 防御）、`ChatWidget.tsx`（拔除原生 alert 弹窗、移除彩色 Emoji）的针对性修复，32 项自动化冒烟保持 100% 全绿。





