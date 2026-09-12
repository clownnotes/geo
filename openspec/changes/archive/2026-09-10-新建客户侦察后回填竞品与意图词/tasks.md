# 任务清单：新建客户侦察后回填竞品与意图词

> **一期范围**：新建降压 + 拆假占位 + `probe_*` 经 profile + 列表徽章 + CLI。  
> **二期**（本变更不做）：Web JSON 上传与 `/probe/*` HTTP。

## A. 规范与口径

- [x] 确认：新建允许空 `keywords` / `competitors`；成功标准不是 50 词（Antigravity 共识）
- [x] 确认：首轮必测 6～10 题、不问自带竞品名；竞品从答案抽取后人工勾真
- [x] 确认：管理台不内嵌反重力；一期不做 Web 上传回填
- [x] 确认：`probe_*` 纳入 `update_project_profile` 的 `scalar_keys`，不新开状态 API
- [x] 更新 `docs/specs/llm-browser-probe-sop.md`：建档触发、回填、与 `probe_status` 对齐
- [x] 战略清单：`docs/strategy/nextgeo-local-geo-backlog.md` P2 承接说明

## B. 数据与后端（一期）

- [x] 拆除 `tools/geo/server.py` 创建兜底：空则写空列表；默认写入 `probe_status: unprobed`
- [x] `utils.update_project_profile` 的 `scalar_keys` 追加 `probe_status` / `probe_baseline_id` / `probe_baseline_at`
- [x] CLI：`geo probe-script <id>` → 6～10 必测题
- [x] CLI：`geo probe-preview` / `geo probe-apply` → 预览并确认回填 keywords/competitors + 状态
- [x] 单测：空壳创建无假占位；profile 可写 probe_*；回填与状态迁移（`tests/test_probe_backfill.py`）

## C. 管理台 UI（一期）

- [x] 新建弹窗：意图词取消 required；改文案/占位；去掉误导示例；0 Emoji
- [x] 「AI 推演 50」降级为必测草稿（约 10 条）+ 基线后扩写提示
- [x] 企业管理表：侦察状态角标；词库 0 显示待回填
- [x] 资料抽屉：展示/可改 `probe_*` + CLI 回填说明（无上传控件）

## D. 联调与停步

- [x] 本地验证：`unittest tests.test_probe_backfill` 全绿；`probe-script nextgeo`；`probe-preview` 对归档豆包 probe 可读
- [x] 写入 `review-log.md`；**等待产品验收**（不自动归档、不推生产）

## E. 二期（仅登记，本变更不编码）

- [ ] Web：probe JSON 上传预览/确认
- [ ] HTTP：`/api/projects/{id}/probe/script|preview|apply`
