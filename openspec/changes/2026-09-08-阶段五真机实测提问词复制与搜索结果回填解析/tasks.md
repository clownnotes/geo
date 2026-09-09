# Tasks: 阶段五真机实测提问词复制与搜索结果回填解析

- [ ] 1. 后端语义解析与持久化引擎 (`tools/geo/monitor.py`)
  - [ ] 1.1 抽象公共回答解析函数 `parse_probe_text(content, client_name, brand_name, competitors)`，支持位次提取、竞品拦截分析与 Citation 外链域名归一化。
  - [ ] 1.2 实现真机数据持久化与周报动态合并函数 `ingest_manual_probe_result(project_id, keyword, model, content, notes)`，支持将实测结果更新入《`05_企业AI可见度与声量追踪周报.md`》并持久化写入 `outputs/05_manual_probes.json`。
  - [ ] 1.3 实现 `get_project_monitor_prompts(project_id)`，针对项目词库自动组装 DeepSeek、豆包、元宝、Kimi 的拟真决策者提问词与平台直达元数据。

- [ ] 2. 后端 REST API 路由打通 (`tools/geo/server.py`)
  - [ ] 2.1 新增 `GET /api/projects/{id}/monitor/prompts` 接口，支持鉴权并返回结构化提问词列表。
  - [ ] 2.2 新增 `POST /api/projects/{id}/monitor/manual-ingest` 接口，接收网页复制回答并返回最新解析详情及联动指标（SOV、首推率、权威得分）。

- [ ] 3. 前端交互组件与大盘联动 (`web/index.html`)
  - [ ] 3.1 在阶段五「首轮监测与验收」顶部控制栏新增「真机实测回填」按钮（遵循严谨商业视觉与 0 Emoji 规范）。
  - [ ] 3.2 构建「真机无痕实测与回填助手」双栏模态弹窗：
    - 左栏：关键词选择器、目标平台 Tab、拟真 Prompt 预览与一键复制、无痕模式直达提示；
    - 右栏：大模型网页端回答粘贴区、字数统计、提交解析按钮。
  - [ ] 3.3 对接 `/manual-ingest` 成功回调，即时触发 `loadMonitorDashboardMetrics()` 刷新主大盘指标与商业 ROI 看板。

- [ ] 4. 自动化测试与交付验证
  - [ ] 4.1 编写单元测试脚本 `tests/test_manual_probe_ingest.py`，验证包含 DeepSeek/豆包真实引用链接的文本解析与周报合并逻辑。
  - [ ] 4.2 验证在零 API Key 状态下，通过真机回填完全跑通阶段五闭环与验收单导出。
