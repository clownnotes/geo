# Proposal: 大模型 Prompt 探针动态演进与追问词裂变引擎

## Why (为什么做 / 业务痛点)

1. **业务痛点：意图词库长期固化引发“词库钝化”与覆盖盲区**
   - 真实用户的搜索与提问习惯随时间、行业热点和新模型（如 DeepSeek V3、豆包 1.5）的发布而快速演进；
   - 企业客户在运营 2~3 个月后，原本固定的 40~50 组词库逐渐饱和，无法捕捉大模型生成的全新长尾衍生提问（如“某某软件最新替代品”、“2026 避坑选型指南”）；
2. **商业续费痛点：代运营缺乏强有力的下一季度续费交付抓手**
   - 客户成功团队在每季度为客户复盘续费时，最核心的增值筹码是 **“为客户挖掘并开拓下一季度新增的 15~30 组高商业转化意图词”**；
3. **技术痛点：缺乏基于大模型真实回答的逆向追问词裂变机制**
   - 大模型在生成答案时，常在文末或逻辑中引导关联问题（Related Follow-up Prompts），当前系统未将其提取并转化为新的攻防探测点。

---

## What Changes (改动范围)

1. **研发大模型 Prompt 演进与裂变引擎 (`tools/geo/evolution.py`)**：
   - 实现大模型关联追问逆向提取器 `extract_fission_prompts(project_id, max_candidates=20)`：从历史探测日志与大模型语义中逆向裂变出场景化长尾词；
   - 实现词库健康度与生命周期评估器 `analyze_prompt_portfolio(project_id)`：对现有词库进行四维划分（🏆 垄断垄断词、🌱 高潜裂变词、⚠️ 竞品拦截词、❄️ 冷门衰退词）；
   - 实现一键词库合并与流水线下发器 `apply_evolved_prompts(project_id, new_prompts, auto_run=False)`。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo evolve <project_id> [--count 15] [--auto-apply]` 子命令。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/evolution/analyze`：获取当前词库生命周期健康度与裂变候选词；
   - `POST /api/projects/{id}/evolution/generate`：触发大模型逆向推演生成 15 组新意图词；
   - `POST /api/projects/{id}/evolution/apply`：一键合并勾选的新词到客户配置 `project.yaml` 并可触发增量流水线。
4. **Web 管理工作台前端升级 (`web/index.html`)**：
   - 向导页 Step 1 与 Step 5 增加 **「🌱 Prompt 动态演进与追问词裂变」** 抽屉/卡片；
   - 支持词库健康度矩阵可视化、勾选新词一键扩容入库并生成季度续费提案报告。
5. **SOP 知识库更新 (`docs/sop/05-monitor-sop.md` & `delivery-sop.md`)**：
   - 规范化“季度词库动态演进与续费提案”的标准交付动作。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/evolution/analyze`
- `POST /api/projects/{id}/evolution/generate`
- `POST /api/projects/{id}/evolution/apply`
- CLI: `python3 -m tools.geo evolve <project_id> [--count 15] [--apply]`

---

## Impact (影响分析)

- **完全向下兼容**：新词合并后自动兼容现有 5 步流水线，不破坏已有历史数据；
- **商业闭环加速**：为客户提供具备自我生长能力的意图词库，为季度续费谈判提供直接支撑。
