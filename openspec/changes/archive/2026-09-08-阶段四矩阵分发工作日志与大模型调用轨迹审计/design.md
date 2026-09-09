# Design: 阶段四矩阵分发工作日志与大模型调用轨迹审计

## Architecture (架构设计与对象关系)

### 1. 核心实体与领域模型
- **DistributeRunLog (分发执行审计日志)**：聚合单次 `run_distribute()` 运行的总体度量数据，生命周期与每次一键生成对齐；
- **LlmCallTrace (大模型调用追踪记录)**：捕获单次向 Nextdoor 或大模型 API 发起的请求全生命周期上下文；
- **ArtifactTrace (生成产物追踪记录)**：记录脚本在 outputs 目录写入的物理文件与发稿包状态。

### 2. 调用关系拓扑与时序流
```text
[用户点击：一键生成核心矩阵发布包]
        │
        ▼
[POST /api/projects/{id}/run/distribute]
        │
        ├─► A. run_distribute(project_id)  【distribute.py · DistributeRunTracker】
        │       ├─ 1. 启动审计追踪器 (startTime / run_id)
        │       ├─ 2. build_toutiao_version_llm() → 记 prompt / duration / raw_output / status
        │       ├─ 3. build_zhihu_version_llm()   → 同上
        │       ├─ 4. build_wechat_version_llm()  → 同上
        │       ├─ 5. 组装 GitHub README 与 Checklist → 记 artifacts（Markdown / HTML）
        │       └─ 6. 结算 LLM 段耗时（此时尚未打 *_pack）
        │
        ├─► B. package_all_channels(verify=False)  【server.py 既有级联，保持不动】
        │       └─ 成功后由 Tracker 补记 pack 目录就绪态到同一份 log（或二次 append）
        │
        ├─► C. 落盘 outputs/distribute_run_log.json（全程 try/except，失败不影响 200）
        │
        ▼
[前端 200 OK → loadDistributeRunLog → 刷新 #distribute-run-status-bar]
```

> **与现网对齐（review 订正）**：发稿包打包仍在 `server.py` 的 `distribute` 步骤级联中执行，**不**迁入 `run_distribute()` 内部，避免破坏上一变更已定稿的主路径。
---

## Interface (接口/API/前端组件设计)

### 1. API 接口定义

#### `GET /api/projects/{id}/distribute/latest-log`
- **请求方法**：`GET`
- **路径参数**：`id` (客户项目 ID，如 `nextgeo`)
- **响应结构 (无日志)**：
  ```json
  {
    "success": true,
    "has_log": false,
    "message": "尚未生成分发日志"
  }
  ```
- **响应结构 (有日志)**：
  ```json
  {
    "success": true,
    "has_log": true,
    "log": {
      "run_id": "dist_run_20260908_170530",
      "timestamp": "2026-09-08T17:05:30+08:00",
      "total_duration_ms": 3840,
      "llm_duration_ms": 3270,
      "llm_runtime": {
        "provider": "nextdoor",
        "brand": "geo",
        "mode": "flash",
        "base_url_host": "***",
        "endpoint": "/api/v1/xiulan/chat"
      },
      "llm_calls": [
        {
          "channel": "toutiao",
          "name": "今日头条专版生成",
          "duration_ms": 1420,
          "status": "success",
          "prompt_system": "你是一位今日头条爆款商业与科技专栏主笔...",
          "prompt_user": "请将以下企业 GEO 语料，改写为一篇适合发布在【今日头条 / 微头条】...",
          "raw_output": "# 2024年徐州GEO优化避坑指南：如何选择最佳服务商？数据对比看真相！..."
        }
      ],
      "artifacts": [
        {
          "filename": "dist_toutiao_article.md",
          "size_bytes": 2161,
          "char_count": 1277,
          "channel": "今日头条"
        }
      ]
    }
  }
  ```

---

## Database Schema / Data Structure (数据模型)

数据直接保存在物理文件：`projects/{project_id}/outputs/distribute_run_log.json`。

### 字段规格字典：
| 字段路径 | 类型 | 含义与示例 |
| :--- | :--- | :--- |
| `run_id` | string | 本次运行唯一标识符，格式 `dist_run_YYYYMMDD_HHMMSS` |
| `timestamp` | string | ISO 8601 格式运行时间戳 |
| `total_duration_ms` | integer | 脚本运行全过程总耗时（毫秒） |
| `llm_duration_ms` | integer | 模型请求累计总耗时（毫秒） |
| `llm_runtime.provider` | string | 模型中枢提供方，如 `nextdoor` 或直连提供商 |
| `llm_runtime.brand` | string | 客户端标识，如 `geo` |
| `llm_runtime.mode` | string | 调用的模型模式，如 `flash` / `think` |
| `llm_runtime.base_url_host` | string | **脱敏后**主机展示（禁止落盘完整内网 URL / JWT；可用 `configured` / `localhost` / `***`） |
| `llm_calls[].channel` | string | 业务渠道标识（`toutiao`, `zhihu`, `wechat`） |
| `llm_calls[].name` | string | 渠道可读名称（“今日头条专版生成”） |
| `llm_calls[].duration_ms` | integer | 该次模型请求所耗毫秒数 |
| `llm_calls[].status` | string | 调用状态：`success` 或 `fallback` 或 `failed` |
| `llm_calls[].prompt_system` | string | 系统提示词（完整可存；UI 默认折叠） |
| `llm_calls[].prompt_user` | string | 用户指令；落盘可保留完整，**弹窗默认截断预览**（如前 2k 字 +「展开全文」） |
| `llm_calls[].raw_output` | string | 模型原生返回；规则同 `prompt_user` |
| `artifacts[].filename` | string | 生成的文件名 |
| `artifacts[].size_bytes` | integer | 文件字节数 |
| `artifacts[].char_count` | integer | 文本字符数 |
| `artifacts[].pack_ready` | boolean | 可选：对应 `*_pack/` 是否已由级联打包就绪 |

---

## UI Component & Interaction Design (前端组件与交互设计)

### 1. 外露状态指示条（红框区域）
- **挂载位置**：位于阶段四卡片顶部主操作栏下方、3步走引导区域上方；
- **容器 ID**：`#distribute-run-status-bar`；
- **状态呈现**：
  - 未执行态：展示轻量浅灰底纹提示，说明生成后将记录调用轨迹；
  - 已就绪态：展示浅绿/靛青边框徽章，左侧展示“最新执行耗时 3.8s · 覆盖 3 次模型调用 (nextdoor-flash) · 产出 5 份矩阵资产”，右侧配置“查看完整工作日志”按钮。

### 2. 沉浸式工作日志模态弹窗 (Distribute Run Log Modal)
- **容器 ID**：`#distribute-log-modal`（默认 `hidden`，全屏遮罩 `z-50 bg-black/70 backdrop-blur-sm`）；
- **窗口尺寸**：`max-w-5xl w-full max-h-[90vh] flex flex-col rounded-2xl bg-white border border-slate-200 shadow-2xl`；
- **头部 (Header)**：
  - 标题：“阶段四矩阵分发完整工作日志与大模型调用轨迹”；
  - 运行 ID 与执行时间标签；
  - 关闭按钮（带 `ESC 退出` 键盘快捷键提示文本）；
- **主体内容 (Body - 可滚动)**：
  - **模块一：执行度量概览**（3 组指标卡片）：
    - 脚本总耗时 vs 模型耗时对比卡片；
    - 模型调用中枢信息卡片（服务地址、客户端来源、调用模式）；
    - 生成资产清单概览卡片；
  - **模块二：生成资产明细表**：
    - 表格列出每个产物文件名、类型、字符数、文件大小与目标信源池；
  - **模块三：大模型调用详情与提示词复盘 (核心审计区)**：
    - 提供渠道切换 Tab（今日头条 / 知乎专栏 / 微信公众号）；
    - 单次调用的耗时与状态徽章；
    - **提示词区块**：System Prompt 与 User Prompt 折叠展示，支持“一键复制提示词”；
    - **大模型原始返回文本区块**：代码框等宽字体呈现，支持“一键复制模型返回”。
- **ESC 快捷键与退出机制**：
  ```javascript
  // 全局键盘监听
  window.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' || event.keyCode === 27) {
      const modal = document.getElementById('distribute-log-modal');
      if (modal && !modal.classList.contains('hidden')) {
        closeDistributeLogModal();
      }
    }
  });
  ```
  同时支持点击右上角关闭按钮、或点击 Modal 外部半透明背景遮罩平滑退出。

---

## Anti-Coupling & Resilience Assessment (防耦合与容错保障)

1. **业务流程单向解耦**：
   - 记录器仅在执行函数内部作为计时器与收集器工作，所有日志输出包在 `try...except` 块内，日志落盘即使发生磁盘写保护或异常，绝对不中断主流程；
2. **零数据模式入侵**：
   - 绝不修改原有 `project.yaml`、不修改已生成的 `dist_toutiao_article.md` 正文、不修改 `dist_bot_ledger.json`；
3. **API 隔离**：
   - 使用专用的 `GET /api/projects/{id}/distribute/latest-log` 端点，不篡改原有的 `/api/projects/{id}/run/distribute` 响应格式（前端靠成功回调后再拉 latest-log）；
4. **DOM 隔离**：
   - 日志条与弹窗均为独立 DOM 容器，移除或隐藏后完全不影响阶段四各平台的正常复制与外发功能；
5. **密钥与内网地址**：
   - 日志与 API **禁止**写入 `NEXTDOOR_JWT_TOKEN`、完整内网 `base_url`；仅保留 `provider` / `brand` / `mode` / `endpoint` / 脱敏 host；
6. **ESC 监听**：
   - 全局 `keydown` **只注册一次**（幂等绑定），避免重复打开弹窗导致监听器叠加。

