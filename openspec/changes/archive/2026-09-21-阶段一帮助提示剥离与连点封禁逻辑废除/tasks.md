# Tasks: 阶段一帮助提示剥离与连点封禁逻辑废除

## 1. 数据修复与账号解封
- [x] 1.1 将 `data/rbac_members.json` 中被误停用的运营人员账号（`13805206070`）状态恢复为 `active` <!-- id: 1.1 -->

## 2. 后端风控护栏改造 (`tools/geo/opsguard.py`)
- [x] 2.1 删掉 `opsguard.check()` 里 4 处「429 次数够了就 `_auto_disable`」。超限仍返回 429，并打警告日志。**不要**删 `record_sensitive_denial()` 里的停用。 <!-- id: 2.1 -->
- [x] 2.2 `REQ_PER_MINUTE` 改为 300，`OUTPUT_READ_PER_HOUR` 改为 600。跨项目数、不同文件名数、敏感探测次数不改。 <!-- id: 2.2 -->
- [x] 2.3 改 `tests/test_operator_anti_scrape.py` 里 `test_distinct_filename_sweep_rate_limited_first_then_disabled`：反复超限后仍是 429，账号保持 `active`。`test_sensitive_asset_denials_auto_disable` 保持「超过阈值就停用」。 <!-- id: 2.3 -->
- [x] 2.4 不另起一套和旧测试重复的文件；若仍写 `tests/test_opsguard_no_auto_ban.py`，只覆盖「频控不封号」，且不得把敏感探测停用测没。 <!-- id: 2.4 -->

## 3. 前端 UI 重构与独立帮助浮层 (`web/index.html`)
- [x] 3.1 老板版和工程师版一共 4 个问号都从主按钮里拆成旁边的独立按钮。点问号只开说明，不跑体检。 <!-- id: 3.1 -->
- [x] 3.2 **[已修正]** 把 `STEP_HELP_DEFINITIONS` 改成 design 白话表。弹层里禁止：SSR、Schema、JSON-LD、幻觉、零幻觉、端口号、升维。文件名可放括号，不要当主句。当前文案已全部转为五年级白话。 <!-- id: 3.2 -->
- [x] 3.3 **[已修正]** `runStep1Audit` 上锁顺序已前置：查锁 → 查项目 → 上锁 → `try { 查摸底 / 发执行 } finally { 解锁 }`。已经在跑只提示、不放开锁。 <!-- id: 3.3 -->

## 4. 全链路回归测试与验收
- [x] 4.1 既有自动化回归（opsguard / anti-scrape）已通过；修完 3.2/3.3 后无需重跑全仓，本地点一次问号与连点即可。 <!-- id: 4.1 -->
- [x] 4.2 **[已重验通过]** 本地 `:8088`：点问号只开白话说明；直出按钮在「查摸底」等待期间连点不会发出第二次。 <!-- id: 4.2 -->
