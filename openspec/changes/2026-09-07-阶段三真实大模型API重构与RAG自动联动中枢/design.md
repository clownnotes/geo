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

## 2. 统一大模型分级探测架构 (Unified Multi-Provider Chain)

彻底解决此前各模块各写一套环境变量判断（`utils.py` 与 `llm.py`、`evaluator.py` 逻辑割裂）的问题，确立全站统一的 API Key 解析优先级：

```
① 第一优先级：本地 .env 持久化配置（由 Web 管理端直接写入或手动配置，gitignored）
       ↓ 未命中
② 第二优先级：操作系统环境变量（GEO_*_API_KEY、DEEPSEEK_API_KEY、ARK_API_KEY）
       ↓ 未命中
③ 第三优先级：项目级 project.yaml 中的 api_keys 声明（独立客户专用通道）
       ↓ 未命中或请求失败 (Timeout > 30s / 401 欠费)
④ 最终兜底：Python 普林斯顿 9 因子行业自适应规则引擎 (100% 离线保障)
```

---

## 3. 接口与组件设计 (Interface & Component Design)

### 3.1 后端 API 接口

1. **`GET /api/llm/status`**
   - **返回数据**：
     ```json
     {
       "configured": true,
       "provider": "deepseek",
       "model": "deepseek-chat",
       "base_url": "https://api.deepseek.com",
       "source": ".env",
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
     - 向模型接口发送轻量 Ping 探针验证连通性与余额；
     - 验证成功后，写入项目根目录 `.env` 文件并实时更新进程环境；
     - 确保 `.gitignore` 包含 `.env`，杜绝密钥泄露。
3. **`POST /api/projects/{id}/rewrite` (自动级联增强)**
   - **处理逻辑**：
     - 聚合 `raw_materials/` 所有已提纯素材与事实清单；
     - 执行 `run_rewrite(project_id)` 产出 `03_普林斯顿9因子高权威语料库.md`；
     - **核心级联**：立即触发 `tools.geo.rag_diag.diagnose_rag_chunks(project_id)` 重新切片；
     - 返回数据：
       ```json
       {
         "success": true,
         "mode": "llm",
         "provider": "deepseek",
         "rag": {
           "score": 88.5,
           "total_chunks": 10,
           "golden_chunks": 7,
           "entity_coverage_pct": 92.0
         }
       }
       ```

### 3.2 前端组件设计
1. **阶段三头部 LLM 状态徽标与配置入口**：
   - 增加常驻状态灯与配置按钮：
     - `🟢 DeepSeek-V3 思考引擎已就绪`（显示延迟，点击打开配置弹窗）；
     - `🟡 离线规则模式 (点击接入 DeepSeek / 豆包 API 开启真 AI 思考)`。
2. **母盘更新 ➔ RAG 诊断前端联动**：
   - 重构完成后，下方 Markdown 预览秒级更新；
   - 顶部【🧩 RAG 语义分块诊断】按钮即时显示最新诊断徽标（如 `88.5分 极佳`），点开即可直接查阅最新的切片穿透报告。

---

## 4. 安全与兜底规范 (Security & Graceful Degradation)

1. **API Key 安全红线**：
   - 严禁将任何明文 API Key 提交至 Git 仓库；
   - 本地写入 `.env` 时，由 `.gitignore` 进行绝对隔离；
   - `/api/llm/status` 返回时对 Key 进行脱敏（如 `sk-****abcd`）。
2. **平滑降级（0 阻断）**：
   - 当 API 欠费、网络超时（timeout=30s）或用户未配置 Key 时，后端自动切换为 `transform_princeton_corpus_fallback`，保证离线状态下 100% 能产出语料库，绝不报错中断。

