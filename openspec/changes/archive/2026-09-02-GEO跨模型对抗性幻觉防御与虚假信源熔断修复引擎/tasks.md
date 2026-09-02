## 1. 幻觉防御与事实纠偏核心引擎 (`tools/geo/guard.py`)

- [x] 1.1 编写 4 维幻觉风险检测算法（`detect_factual_hallucinations`，比对项目真实事实库与大模型回答，识别主体混淆、虚假参数、恶意截流与边界失真）。
- [x] 1.2 编写事实锚点补丁与反击语料生成器（`generate_adversarial_countermeasures`，输出《07_大模型事实幻觉纠偏与信源反击策略.md》与 `factual_anchors.json`）。
- [x] 1.3 编写修复前后双轨沙箱推演模拟器（`simulate_guard_repair_effect`，模拟修复前 35 分幻觉 vs 修复后 99 分强事实置信度）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `detect_factual_hallucinations`、`generate_adversarial_countermeasures` 与 `simulate_guard_repair_effect`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo guard <project_id> [--detect|--repair|--simulate]` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/guard/risks` 接口（返回幻觉风险与防御状态）。
- [x] 3.2 实现 `POST /api/projects/{id}/guard/repair` 接口（触发一键纠偏补丁生成）。
- [x] 3.3 实现 `GET /api/projects/{id}/guard/simulation` 接口（返回修复前后沙箱推演对比）。
- [x] 3.4 在专属交付门户 `tools/geo/share.py` 注入品牌公关与幻觉防守摘要。

## 4. Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 4（防守与分发）/ 顶部增加「🛡️ 幻觉防御与信源反击」操作视窗与沙箱推演弹窗。
- [x] 4.2 在专属交付门户 `web/share.html` 嵌入品牌公关与大模型幻觉防守展示卡片。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/delivery-sop.md` 与 `04-defense-sop.md`，规范化大模型负面与幻觉修复 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：幻觉检测、反击语料生成、沙箱推演与门户交互。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
