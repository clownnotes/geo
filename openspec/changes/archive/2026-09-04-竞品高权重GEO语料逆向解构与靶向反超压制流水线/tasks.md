# Tasks: 竞品高权重GEO语料逆向解构与靶向反超压制流水线 (第 32 维)

## Phase 1: 核心逆向解构与破绽侦测引擎 (`tools/geo/rival_crack.py`)
- [x] 1.1 创建 `tools/geo/rival_crack.py` 基础框架，设计安全加载机制（URL 抓取接入 `crawler.py` 的 SSRF 防护与 Clean Markdown 提纯，本地文件与文案输入支持）。
- [x] 1.2 实现确定性沙箱回放类 `RivalSandboxGenerator`，在离线环境或指定竞对名称时提供确定性竞品语料与特征（哈希固定种子），确保单测零网络依赖且毫秒级通过。
- [x] 1.3 实现普林斯顿 9 因子逆向解构器 `RivalContentDeconstructor`，量化提取竞品 8 项因子得分，抽取数据声明、引用信源、论断主张与结构化表格/FAQ。
- [x] 1.4 实现致命破绽侦测引擎 `RivalFlawDetector`，精准识别数据空心化、信源凭空化、商业暗坑与问答盲区 4 大破绽。

## Phase 2: 靶向反超压制三件套生成与报告导出 (`tools/geo/rival_crack.py`)
- [x] 2.1 实现 `TargetedSuppressionGenerator`，绑定 `project.yaml` 真实参数，自动生成【第一件套：高维数据降维压制参数对照表 (Markdown Table)】。
- [x] 2.2 生成【第二件套：长尾破绽拦截型 9 因子深度反超语料 (Markdown)】，结论先行、双重信源、合规免责。
- [x] 2.3 生成【第三件套：大模型诱导型破绽反问 FAQ 矩阵】，覆盖买家高频暗坑痛点。
- [x] 2.4 实现公文级报告《32_竞品高权重GEO语料逆向解构与靶向反超压制报告.md》与 JSON 结构化结果持久化输出。

## Phase 3: CLI、后端 API 与高管门户战果反哺
- [x] 3.1 在 `tools/geo/cli.py` 注册 `geo rival-crack <project_id> [--url/--file/--competitor] [--report]` 命令并与现有 CLI 格式统一。
- [x] 3.2 在 `tools/geo/server.py` 挂载 `POST /api/projects/{id}/rival-crack/run`（Bearer Token 保护）与 `GET /api/projects/{id}/rival-crack/status`。
- [x] 3.3 在 `tools/geo/share.py` 的 `compile_portal_data()` 中接入 `rival_crack_summary`，实现 `never_run` 优雅降级。
- [x] 3.4 在 `web/share.html` 中增设【竞品语料靶向反超压制态势】只读大屏卡片。

## Phase 4: 全栈单元测试、跨端审查与交付闭环
- [x] 4.1 编写完整单元测试 `tests/test_rival_crack.py`，覆盖 SSRF 防御、9 因子解构打分、破绽探测、三件套生成、CLI 与 API 鉴权、门户反哺契约。
- [x] 4.2 运行项目全量单元测试（原 154 项 + 新增 15 项共 169 项单测），确保 100% 秒绿（基线 < 3.0s）。
- [x] 4.3 跨 IDE 审查协同与 `review-log.md` 审核记录更新。
