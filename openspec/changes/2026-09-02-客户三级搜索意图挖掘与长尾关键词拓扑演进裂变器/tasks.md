## 1. 编写 3 级搜索意图挖掘与长尾裂变核心引擎 (`tools/geo/intent.py`)

- [x] 1.1 实现 `build_3tier_intent_matrix(project_id: str)`，自适应裂变 L1(认知大词)、L2(选型避坑)、L3(场景长尾) 三级提示词矩阵。
- [x] 1.2 实现 `render_intent_topology_markdown(project_id: str, matrix: dict)`，输出 `outputs/11_三级搜索意图挖掘与长尾关键词裂变拓扑.md` 与 `outputs/keywords_intent_matrix.json`。
- [x] 1.3 实现 `sync_intent_keywords_to_eval(project_id: str, tier: str = "all")`，将裂变关键词同步至评测词库。

## 2. CLI、服务端与 Web 端大一统集成 (`tools/geo/cli.py`, `server.py`, `web/index.html`)

- [x] 2.1 更新 `tools/geo/cli.py`，完善 `intent` 子命令（支持 `--generate`、`--sync-eval`、`--tier`）。
- [x] 2.2 更新 `tools/geo/server.py`，挂载 `/api/projects/{id}/intent/matrix`、`POST /generate` 与 `POST /sync-eval`。
- [x] 2.3 更新 `web/index.html`，在 Step 2 与 Step 5 呈现 3 级意图漏斗大盘并支持一键裂变与同步。

## 3. 全链路验证与跨 IDE 审查

- [x] 3.1 编写 `tests/test_intent_mining.py` 单元测试，覆盖 3 级意图生成、去重与资产落盘。
- [x] 3.2 针对 4 大母版项目生成 3 级意图拓扑，本地验证通过并 Git 推送。


