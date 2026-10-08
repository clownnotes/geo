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
  - [x] 改造 `studioArtifactConfig.js` 中 `isMasterFile`：**判定口径唯一真相源为 `design.md` §1.4 第 9 条的函数原文（三分支：软删过滤 → 参考件优先排除 → `isMaster` / `isActive` 且排除 `slot_manual`、`slot_misc`，含 `CANONICAL_SLOT_DICT` 规范名兜底）**，本任务不再重述条件（第 2 次审 🔴-3：原先此处写成“两分支、无规范名兜底、无 manual 槽排除”，与 design 形成两套 `isMasterFile`，属 R-1“判定标准不一致”的文档版复发）；**禁止**再用 `isProtectedArchive` / `isRetired` 一票否决当前生效主文件；

  - [x] 同步订正 `getMasterFileForSlot`：选取 active 主文件时不得因历史 `isProtectedArchive` 标记跳过当前生效件；
  - [x] 优化 `migrateAndNormalizeFiles`：废除对 `_第1版` 强制赋 `isProtectedArchive` 的存量迁移规则，严禁历史归档污染当前生效的主文件；
- [x] 7.2 【文件树与改名拦截口径 100% 对齐】：
  - [x] 统一 `StudioFileTree.vue` 的晨光淡黄打勾展示、右键改名唤起条件与各阶段 `handleRenameFile` 改名拦截条件，全部收敛调用同一 `isMasterFile()`，确保凡显示为主文件者均可平滑改名；
- [x] 7.3 【自动化断言与实测回归】：
  - [x] 在 `tests/smoke_studio_artifacts.mjs` 中补充：① `isMaster=true` 且误带 `isProtectedArchive` 时 `isMasterFile===true`；② `_第1版` 命名的生效主文件可改名；③ 参考件仍禁止改名。NE1 冒烟须继续全绿。
  - [ ] ④（第 2 次审 🔴-3 补）针对 `CANONICAL_SLOT_DICT` **规范名兜底分支**补一条断言（或显式声明该分支废弃并删除），使 design 与实现三方对齐；属回归验证，不重写函数。








## 8. 纯源码对外协作仓库与白名单双向同步工具建设 (2026-10-07 师弟立规 · 【已被 §9 于 2026-10-08 就地覆盖取代】)
> 注：本节产物 `scripts/sync_export_to_core_repo.sh` / `sync_pull_from_core_repo.sh` 均按 2026-10-07 的根目录平铺口径（`web/ tools/ gateway/`、tests 绝对排除、目标仓 `GEO-Core`）编写，随 §10 源码下沉 `src/` 与本轮卡片裁决已全面失效，改造任务见 9.2 与 9.6。
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

## 9. 同事协作仓 GEOChen 出包与单向回流 (2026-10-08 师弟卡片裁决 · 就地覆盖旧 9.1-9.3)

> 旧任务 9.2 口径（提取 `web/ tools/ gateway/`）已随 §10 源码下沉 `src/` 失效；本节按 design.md §7 修订版重开。

- [ ] 9.0 【交付前硬阻塞修复 · B-1 生产启动链路】：先在 NE1 核实 mini 现役进程实际启动方式，再把 `deploy/start.sh:19` 与 `scripts/run_geo_prod.sh:16` 统一改为 `PYTHONPATH=src` 入口（或复用根 `./geo`）；严禁擅自重启线上服务，改动仅落盘待师弟验收；
- [ ] 9.0b 【B-2 分享模板漏改】：`src/tools/geo/share.py:35` 的 `WEB_DIR` 对齐为 `PROJECT_ROOT/src/web`（与 `server.py:61` 同口径），补 `share.html` 模板读取断言；
- [ ] 9.0c 【B-3 测试导入根修复（考官 G4 定为单点）】：新增 `tests/conftest.py` 作为唯一 bootstrap，把 `工程根/src` 插入 `sys.path`，**禁止**在 61 个测试文件里逐个改 `sys.path`（散改会造成回流比对噪音）；
- [ ] 9.0d 【B-4 站点校验旧路径】：`scripts/check_site_standard.py:336` 改指 `src/tools/geo/scaffold.py`；
- [x] 9.0e 【~~B-5 真实客户身份清洗~~ → 2026-10-08 第四轮撤案 · 已作废结案】：师弟明确对方为核心合伙人，客户身份与业务数据（`templates_pack.py` 的 `xuzhou_xuanyuan` 行业母版、四处默认 `pid`、`nextgeo` 字样）**原样保留、不洗**；本任务作废，仅保留 §0.2 第 19 条的撤案记录；
- [ ] 9.0g 【B-7 服务器安全痕迹脱敏（第五轮尺度定稿：注释 + UI 文案中性化）】：只在出包副本上动手，按 §7.7 矩阵执行 —— 中性化 `src/gateway/main.go:2`、`src/tools/geo/server.py:552、643、4226-4235、4277`、`src/tools/geo/llm.py:32、391-392`、`src/web/index.html:1105、4828、16050、16058` 中出现的 `mini / NE1 / SSH 隧道 / 家用物理机 / 中国联通动态公网 / 家宽 DDNS / tccli CDN` 等表述（改为“上游服务走本机回环”一类中性说法）；**端口 `8088/3001/3002/8090` 与 `127.0.0.1` 回环逻辑一律保留原样（功能必需）**；`baicl.cc` 系列域名按第五轮裁决**全部保留**；`config.yaml` 整文件不进包；主仓文件一字不改（见 9.10）。
- [ ] 9.0f 【B-6 内网坐标与密钥物理隔离】：`src/gateway/config.yaml:4-6`（NE1 内网 `100.83.64.112:3002` + 真实 `ndsk_` voice_key）绝对不进包，仅交付 `config.yaml.example`；出包脚本与 9.7 门禁必须对其做关键词扫描（`100.83.64.112`、`ndsk_`、`jwt_token`、`voice_key`）要求 0 命中（注：`xuzhou`、`nextgeo` 因第四轮撤案不再列入扫描项）；
- [ ] 9.1 【主仓回归全绿】：B-1~B-4 修复完成后在 NE1 跑全量冒烟（32 项 + `tests/` Python 套件 + `src/gateway` go 测试），必须 100% PASS 才允许出包（师弟 2026-10-08 裁决“先修断链再出包”）；B-5/B-6 属出包副本处理，不改主仓；
- [ ] 9.1b 【交付包干净房自测（第 2 次审 🔴-2，出厂前最后一道保险）】：出包一律**先写 NE1 临时 staging 目录**（如 `/Users/ne/tmp/geochen-export`，不直接写本地 `GEOChen`），在 staging 内按 §7.6 顺序完整执行 `npm install && npm run build:step0` ➔ `./geo web --port 8088` ➔ `PYTHONPATH=src python3 -m pytest tests -q` ➔ `cd src/gateway && go test ./...`，全绿后才以 git 提交方式原子落位并 push `GEOChen`；专项验证六项预判坑：无 key 降级、`requirements.txt` 是否含 `pytest` 等测试依赖、包内无 `/Users/a1` 与 `/Users/ne` 绝对路径、`geo_partners.yaml` 骨架可被 `partners.py:61` 解析、根 `package.json` 与 `geo` 与裁剪后结构自洽、**首开管理台默认项目不炸（见 9.15）**；staging 实测记录（含全部降级行为）作为出厂合格证明附件存主仓侧。本任务在 NE1 执行，符合 AGENTS.md §4.5 本地零编译；
- [ ] 9.2 【出包脚本按白名单提取】：**重写** 2026-10-07 的旧脚本 `scripts/sync_export_to_core_repo.sh`（仍按根目录平铺 `web/ tools/ gateway/` 提取、目标写死 `GEO-Core`、README 里教同事跑 `python3 tools/geo/server.py`、`.gitignore` 连 `.env.example` 一起排除，已全面失效），按 design.md §7.1 将 `src/`（排除 `__pycache__`、`node_modules`、`src/gateway/config.yaml` 实值与 `gateway` 二进制）+ `tests/` + 最小底盘（`geo`、`requirements.txt`、`package.json`、`config/geo_partners.yaml` 骨架、`.env.example`、空 `data/storage/reports` 骨架、1 个虚构 `projects/demo-client/`）单向提取到 `/Users/a1/代码/GEOChen`；**`scripts/`（21 个）与 `deploy/` 以 0 文件进包**（师弟 2026-10-08 明确“一个脚本都不给”，含 `opsx.py`、`qoder_reviewer.py`、`workbuddy_reviewer.py`、`sync_*_ziliao.sh`、`run_geo_prod.sh`、`smoke_step0.sh` 全部留主仓）；`projects/demo-client/` 必须用假品牌假域名，严禁残留任何真实客户名、官网域名或报告；**同时物理删除已废除的 `scripts/sync_pull_from_core_repo.sh`（🟢-2，task 8.2 虽已勾但脚本仍在库，留着会被后人误用成双向同步），并在 §8 标注其已退役**；出包脚本自带的词表文件 `scripts/export-clean-terms.json` 只存主仓、不进包；
- [ ] 9.3 【工作规范清洗（第 2 次写按考官 R4/Y1 补强）】：出包脚本按固定词表自动替换 **120 处 / 43 个文件**的 AI 工作规范痕迹（`openspec` 19、`AGENTS` 38、`RULES.md` 2、`antigravity` 19、`师弟` 41、`立规` 33、`师兄` 1），并按 §7.4 第 1 条**补语义变体词表**（`规范`、`设计文档`、`变更目录`、`决策记录`、`spec 目录`、`内部规范`，含大小写全半角），随后人工抽查 10 个高频文件；
  - 3a **严禁置空或删除**参与运行判断的字符串，只做语义等价的中性替换（考官 Y1 收紧）；
  - 3b **tests 安全探测样本例外（考官 R4 + 第 2 次审 🟡-6）**：`test_console_gate_leak_prevention.py:70`、`test_site_crawler_and_gate.py:94` 的 `/AGENTS.md`、`/tools/geo/server.py` 探测样本，一律改为**测试自建 fixture**（pytest `tmp_path` 内造假敏感文件，断言“服务绝不暴露工作区任意文件”），需要“磁盘真实存在且必须拒绝提供”的高强度靶时统一选 **`/.git/config`** 并在注释写明理由；**禁止**使用 `/data/sessions.json`、`config/geo_partners.yaml` 这类包内会真实存在或运行期自动生成的路径（断言会因时机红绿翻转）；顺手校正随 `src/` 迁移过期的探测路径；**404 断言语义必须保留**，禁止为凑“0 命中”删掉整段安全测试；
  - 3c 门禁断言：`grep -rniE "<第 1 条全词表>" GEOChen` 命中 0；**清洗词表黑名单（脚本严禁触碰）**：客户身份 `xuzhou_xuanyuan`、`nextgeo` 与产品交付话术 `老赵哥`、`麦肯锡`、`V-W-W-H`；主仓文件一字不动（见 9.10）；
- [ ] 9.4 【交付清单与清洗映射表落盘（第 2 次审 🔴-1/🟢-4 订正存放地与 Schema）】：`delivery-manifest.json` 覆盖 **§7.3 全部进包文件**（含根 `package.json`、`geo`、`requirements.txt`、`config/geo_partners.yaml`、`.env.example`、`.gitignore`、`README.md`、`PROJECT_GUIDE.md`、`projects/demo-client/` 骨架），留在包内的字段**只允许中性项（路径 + sha256 + 行数）**，不得含任何被清洗的原字符串；`cleaning-map.json`（文件 → 原字符串 → 替换字符串 → 行号提示）**只存主仓 `openspec/changes/<本变更>/artifacts/`，严禁进包与进 GEOChen 任何提交**（否则同事一条 `git log -p` 就能还原全部被洗内容，且推送不可撤回）；两份清单共用一份 JSON Schema（`version`、生成工具版本、导出 commit SHA、`repo` 字段，`cleaning-map.json` 的 `repo` 固定 `GEO`）；包内基线锚点改用导出 commit SHA + git tag；
- [ ] 9.5 【同事仓 README 与首次提交推送】：写同事上手文档（目录结构、起服务命令、跑测试命令、PR 约定、严禁改 `.env` 与 `config.yaml`），在 `GEOChen` 提交并 `git push origin main`（`baiTouYing/geoChen`）；
  - 5a README 必须逐字写清 §7.6 的四条自测口径（`npm run build:step0` / `PYTHONPATH=src python3 -m pytest tests -q` / `cd src/gateway && go test ./...` / `./geo web --port 8088`），并说明依赖常驻 8088 的 2 个测试要先起服务；
  - 5b README 必须声明：上游 key 由同事自备，未配置时 AI 生成类按钮按 `llm.py:592` 返回结构化提示属预期行为，不得当 Bug 提报；
  - 5c README 的 PR 门禁条款：PR 描述必须附上述 3 条测试命令的实际输出，未附者一律退回（师弟 2026-10-08 裁决“同事自测绿才能提 PR”）。
- [ ] 9.6 【AI 单向回灌主仓 SOP（串行两方 · 第 2 次写按考官 R3/R5 修订）】：写权与节拍按师弟原话定死 —— “出包之后，我这边不开发。他开发完，我这边合并了他的版本以后，我才会来我这边进行修改”，故**同事开发期内主仓 `src/tests` 冻结功能演进**，两仓不并行；
  - 6a 比对范围＝**全部进包文件**（与 9.4 的 manifest 同集合，不再限 `src/` + `tests/`）；AI 以出包基线比对 `GEOChen` 与主仓，产出三态差异表（新增/删除/变更）；因主仓本圈冻结，**一旦查出主仓侧也有改动即视为违反冻结，立即停步报师弟**，不得自行合并；
  - 6b 归位规则：`src/`、`tests/` 内新增文件按同相对路径直接落位；包根与其他目录（`package.json`、`requirements.txt`、`geo`、`config/geo_partners.yaml`）的变更单列“人工裁决清单”，依赖类改动必须过 NE1 回归后才入库；
  - 6c 师弟点头后单向拷回主仓，并按 `cleaning-map.json` **定向还原**主仓侧的内部规范引用与服务器坐标（清洗件只存在于交付包），再在 NE1 跑绿（含 32 项冒烟）。严禁无脑覆盖主仓；
- [ ] 9.14 【冻结期紧急修复通道（考官 Y2 新增）】：同事开发期内主仓原则上不开发，但线上 bugfix 例外，动线为「最小 patch ➔ 主仓跑绿 ➔ 以新 manifest 立即再出包覆盖 `GEOChen` ➔ 明确告知同事新基线」，禁止攒批；同事交付周期上限与超期预案（缩小范围 / 提前解冻 / 换人）留给师弟拍板，AI 不代决；
- [ ] 9.7 【红线守护自检（第四轮改版）】：严禁给主仓添加 `baiTouYing` remote、严禁 subtree 双向拉同事历史、**严禁师弟与 AI 在 `GEOChen` 手写业务代码**（同事为该仓唯一写手）、主仓 `src/` 之外不得出现第二份可编辑源码；出包与回流各跑一次扫描门禁，命中数写入 `delivery-manifest.json` 作为出厂合格证明：
  - 服务器安全类必须 0 命中：`100.83.64.112`、`tailscale`、`ndsk_`、`jwt_token`、`voice_key`、`NE1`、`Mac mini`（机器指代）、`SSH 隧道`、`家用物理机`、`中国联通动态公网`、`DDNS`、`tccli`（域名类经第五轮裁决**移出清洗范围，全部保留**）；
  - 扫描口径消歧（考官 Y5，见 §7.7.2）：区分“键名”与“值”——`*.example`、`.env.example`、`config/geo_partners.yaml` 骨架允许出现 `jwt_token`、`voice_key`、`base_url` 这类**键名且值为空/占位**，其余任何位置、以及任何真值形态（`ndsk_` 后跟 ≥16 位、内网 IP、真实业务域名出现在示例文件里）一律判不合格；扫描统一 `-i` 不区分大小写，正则口径写进脚本注释；
  - 工作规范类必须 0 命中：`openspec`、`AGENTS`、`RULES.md`、`antigravity`、`师弟`、`师兄`、`立规`、`docs/specs`、`docs/strategy`（含 §7.4 第 1 条的语义变体词表）；
  - 核心合伙人可见类**不纳入清洗**（第四轮撤案）：`xuzhou_xuanyuan`、`nextgeo`、客户行业母版与词库、`老赵哥`、`麦肯锡`、`V-W-W-H`；
  - 7d **词表同源（第 2 次审 🟡-1）**：替换与扫描必须共用主仓侧单一词表文件 `scripts/export-clean-terms.json`（不进包），断言「替换集合 ⊇ 扫描集合」，消除 §7.7 ② 与本条 9.7 此有彼无（`mini:3001`、`联通宽带`、`家宽`、`tailscale` 曾只在一边）；并补扫 `ssh ` 主机形态、`mini[:：]`、`/Users/a1`、`/Users/ne` 四类；9.0f 的“0 命中”字面改为引用 §7.7.2 键位豁免规则，避免误删 `config.yaml.example` 的键名；

- [ ] 9.8 【交付包项目导览 `PROJECT_GUIDE.md`】：按师弟“这个项目怎么做的，需要让他能知道”，出包时生成一份只讲代码与契约的导览：目录结构、00~07 八阶段流水线在代码里的落点、`server.py` 215 条路由的清单与用途（自动生成）、前端两轨（`index.html` 大屏 + `step0-src` Vue 岛）的装配关系、起服务与跑测试命令；**严禁**写入内部规范名称、AI 协作流程与服务器坐标（与 9.7 扫描门禁共用同一套断言）；
- [ ] 9.9 【串行版本节拍与再出包】：按师弟“每次合并后，我会提交新版本给他，他等我合并后的版本再抓取到本地参考”，节拍定为一圈：同事提 PR ➔ 师弟 review+merge 进 `GEOChen` ➔ AI 两方比对回灌主仓 ➔ 主仓跑绿 ➔（师弟需要时）主仓再开发 ➔ 出下一版包覆盖 `GEOChen` 作为新基线；同事开发期内主仓 `src/tests` 冻结功能演进，两仓绝不并行修改。

- [ ] 9.10 【主仓零污染铁律物理断言（师弟第五轮原话升为最高约束）】：“你要注意，改的代码是放到新出的仓库，别把我们自己仓库清得谁都看不懂了” —— 出包脚本对主仓必须**只读**，清洗与脱敏的写入只允许落在 `GEOChen`；出包前后各断言一次 `git status --porcelain -- src/ tests/`，输出非 0 行立即中止出包并报警，绝不允许把主仓改成“谁都看不懂”的样子；
  - 10a **脚本防呆四条（考官 Y3，必须写进脚本而不是只靠事后断言）**：① 目标路径硬校验，必须精确等于 `/Users/a1/代码/GEOChen`，否则立即中止；② 全程**禁用 `rsync --delete`**（源/目标颠倒即清空主仓，属灾难级）；③ 首次运行强制 `--dry-run` 输出待写清单给师弟过目；④ 收尾复查主仓 `git status --porcelain -- src/ tests/` 为 0 行；
  - 10b **本地 `GEOChen` 定位声明（考官 Y7）**：该目录只是同事仓镜像与只读比对输入，不是我方第二套源码，不违反反双份源码立规；比对一律以只读方式进行，并建议 IDE / 全局搜索索引排除该目录，防 AI 视野里出现两套同名文件；
- [ ] 9.11 【免登注释口径 · 第六轮已定案】：`server.py:330-344、936、3190` 的代码逻辑在主仓与交付包**均一字不动**，仅交付包副本内把“免登/免密通道/绕过”措辞改为中性描述（如“本机回环直连识别”）；此项已由师弟第六轮亲口点选“认可：只中性化交付包注释”，不再是推导项；
- [ ] 9.12 【qspec quotes 脚本缺陷修复（授权已到，本轮禁止执行）】：师弟第六轮授权把 `~/.qoder/skills/qspec/scripts/qspec.py` 的 `quotes` 子命令改为“只追加用户实录、绝不删除已有内容”（该脚本已两次整体重写 `proposal.md` 并吞掉人工补录）。**因 `/qgrill` 探讨流绝对禁止修改任何 `.py`，本任务只登记授权，必须等师弟退出探讨流另行下令后方可执行**；改动范围严格限定该技能脚本，严禁触碰 GEO 项目任何文件；
- [x] 9.13 【送审方式 · 已裁决结案（原话出处已补齐，闭环考官 🟡-3）】：师弟第六轮卡片第三题逐字答复“**用你自己的 DeepSeek 4.1 审核**”（出处：`/qgrill` 第六轮 `AskUserQuestion` 返回结果，现已回填 `proposal.md` 第二部分第六轮实录），并于 2026-10-08 亲自触发 `/qteam` 执行；故本套 §7 方案的审查路径定为：**qteam 主刀↔考官循环，考官为 Qoder 独立会话 · DeepSeek-Flash，审 `design` 档**；此前 Qoder 误记“未点选”已订正，`design.md` §0.2 第 26 条同步改为已决。

- [ ] 9.15 【默认项目兜底（第 2 次审 🟡-5，师弟 2026-10-08 已授权“项目不存在就退回列表”）】：主仓补一层防御 —— 当默认 `pid` / 兜底 `clientId` 指向的项目在 `projects/` 下不存在时，后端与前端一律**退回项目列表或引导新建**，不再直接踩空报错；涉及 `Step2App.vue:46`、`roi.py:225`、`playground.py:250`、`benchmark.py:315`、`dist_bot.py:853`、`server.py:611-612、3388-3389`；**只加兜底、不改任何默认值语义与客户身份**（第四轮撤案保护对象）；配套补一条回归断言，并在 9.6b 人工裁决清单增设「默认 pid / 客户身份相关改动」一类强制师弟点头；
- [ ] 9.16 【生产红线 B-8 / B-9（2026-10-08 NE1 只读实测发现，需师弟另行授权后才动线上）】：① 生产仓 `/Users/ne/apps/GEO` 的 HEAD 停在 `f1db08a`（无 `src/`，仍旧结构），且工作区有未提交改动（`tools/geo/server.py`、`tools/geo/ingest.py`、`scripts/smoke_step0.sh`、`scripts/workbuddy_reviewer.py`、`tests/test_member_dashboard_and_perspective.py`、`AGENTS.md` 及客户 `outputs/.compliance_backup/*`）—— 先逐条查清来源与是否回收，**严禁 `reset --hard` / `checkout --` 丢弃**；② 线上 8088 实由 launchd（`com.geo.web-8088.plist`，`KeepAlive=true`）调 `/Users/ne/bin/run_geo.sh` 启动，**不是**仓内 `deploy/start.sh` 或 `scripts/run_geo_prod.sh`，故 B-1 的真实修点在仓外脚本；未给该脚本加 `PYTHONPATH=src` 之前，**严禁把生产仓同步到 `src/` 结构**，否则重启即失败且被 KeepAlive 反复拉起刷日志；③ plist 的 `WorkingDirectory` 为小写 `/Users/ne/apps/geo`，顺手订正为真实大小写路径。本轮仅只读核实与登记，任何线上变更须师弟明示授权。

## 10. GEO 主工程根目录瘦身与源码集中收纳 (2026-10-07 师弟立规)
- [x] 10.0 【本地安全快照门禁】：在文件平移前完成本地 Git 提交留痕（信息：`chore: 建立本地安全快照基线（准备平移源码至 src/）`），建立全绿基线物理回滚点；
- [x] 10.1 【创建统一源码目录】：在根目录创建 `src/`，将散落的业务源码（`web/`、`tools/`、`gateway/`）集中下沉至 `src/` 下；
- [x] 10.2 【对齐后端服务寻址】：更新 `src/tools/geo/utils.py` 与 `server.py` 的项目根路径与静态资源托管路径；
- [x] 10.3 【对齐前端与入口命令】：更新 `package.json` 中的脚本前缀路径与根目录 `./geo` 启动命令；
- [x] 10.4 【自动化冒烟回归守护】：更新 `tests/smoke_studio_artifacts.mjs` 测试引用路径，实跑确保 32 项断言 100% PASS；
- [x] 10.5 【Qoder 外部审查与阻断修复闭环】：响应 Qoder 审查，完成 `src/gateway/main.go`（默认绑定 127.0.0.1、基于 ProjectRoot 寻址、长连接写超时放行、路径穿越与 SSRF 防御）、`ChatWidget.tsx`（拔除原生 alert 弹窗、移除彩色 Emoji）的针对性修复，32 项自动化冒烟保持 100% 全绿。





