# Design: 阶段三真实大模型API重构与RAG自动联动中枢

## 1. 核心架构与数据流向 (Architecture & Data Flow)

```
[素材录入] 官网爬虫 / 客户资料
        │
        ▼
[raw_materials/ 目录持久化]
        │
        ▼
[点击【执行普林斯顿重构】]
        │
        ├── ① 检查 get_configured_llm()
        │     ├── 有 Key: 构造高密度 Prompt ➔ 调用 DeepSeek/豆包 API 深度推理
        │     └── 无 Key: 平滑降级为 Python 行业规则自适应模板 (Fallback)
        │
        ▼
[落盘生成母盘: 03_普林斯顿9因子高权威语料库.md]
        │
        ├── ② 自动级联触发 (Cascade Execution)
        │     └── tools.geo.rag_diag.diagnose_rag_chunks()
        │
        ▼
[刷新 RAG 切片大盘: 12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md]
        │
        ▼
[前端 Web 控制台感知更新]
  - 语料库 Markdown 实时重载
  - RAG 按钮打上实时分数徽标（如 88.5分 极佳）
  - LLM 状态灯保持常绿 (DeepSeek/豆包)
```

---

## 2. 接口与组件设计 (Interface & Component Design)

### 2.1 后端 API 接口

1. **`GET /api/llm/status`**
   - **返回数据**：
     ```json
     {
       "configured": true,
       "provider": "deepseek",
       "model": "deepseek-chat",
       "base_url": "https://api.deepseek.com",
       "latency_ms": 120,
       "status": "ready"
     }
     ```
2. **`POST /api/llm/config`**
   - **入参**：
     ```json
     {
       "provider": "deepseek",
       "api_key": "sk-xxx",
       "model": "deepseek-chat",
       "base_url": "https://api.deepseek.com"
     }
     ```
   - **处理逻辑**：
     - 向模型接口发送轻量 Ping 探针验证连通性；
     - 验证成功后，写入项目根目录 `.env` 文件并刷新内存配置；
     - 确保 `.gitignore` 包含 `.env`。
3. **`POST /api/projects/{id}/rewrite` (增强)**
   - **处理逻辑**：
     - 聚合 `raw_materials/` 所有已提纯素材；
     - 执行 `run_rewrite(project_id)`；
     - **自动级联**调用 `diagnose_rag_chunks(project_id)`；
     - 返回重构后内容与 RAG 诊断关键指标（得分、黄金切片数）。

### 2.2 前端组件设计
1. **阶段三头部 LLM 状态徽标与配置弹窗**：
   - 在阶段三操作栏中增加轻量指示器：
     - `🟢 DeepSeek 思考引擎已就绪`（点击可查看/更改模型）；
     - 或 `🟡 离线规则模式 (点击接入 DeepSeek/豆包 API 开启深度重构)`。
2. **重构完成后的前端联动**：
   - 收到后端级联响应后，不仅刷新下方 Markdown 预览，同时将 `openRagDiagModal` 按钮上的分数刷新为最新跑出的实际诊断分。

---

## 3. 安全与兜底规范 (Security & Graceful Degradation)

1. **API Key 安全红线**：
   - 严禁将任何明文 API Key 提交至 Git 仓库；
   - 本地写入 `.env` 时，由 `.gitignore` 进行绝对隔离；
   - `/api/llm/status` 返回时对 Key 进行脱敏（如 `sk-****abcd`）。
2. **平滑降级（0 阻断）**：
   - 当 API 欠费、网络超时（timeout=30s）或用户未配置 Key 时，后端自动切换为 `transform_princeton_corpus_fallback`，保证离线状态下 100% 能产出语料库，绝不报错中断。

