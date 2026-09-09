# Design: 阶段四矩阵分发核心主线重构与信息架构精简优化

## Architecture (架构设计与组件划分)

### 1. 页面信息架构与组件划分 (IA Partitioning)

`step-panel-4` 容器将划分为四个逻辑层次：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 阶段四顶部总览与全局打包条                                                 │
│    • 核心说明：抢占 75%+ 本土 AI 信任池（豆包 + DeepSeek）                   │
│    • 全局主按钮：[ 一键生成全矩阵分发包 ]（打通底层全渠道打包 + 状态点亮）     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. 新客交付 MVP 核心主战区 (Core Mainstream · 75%+ AI 声量 · 默认高亮展开)  │
│    ┌───────────────────────────────────┬───────────────────────────────────┐│
│    │ [头条] 今日头条 / 豆包生态 (50%+) │ [知乎] 知乎专栏 / DeepSeek (25%)  ││
│    │ • 状态: [已就绪 · 约1850字 / 待生成│ • 状态: [已就绪 · 约2100字 / 待生成││
│    │ • 主按钮1: [一键复制富文本长文]   │ • 主按钮1: [一键复制知乎富文本长文]││
│    │ • 主按钮2: [直达头条号后台]       │ • 主按钮2: [直达知乎创作中心]     ││
│    │ • 次级: 生成包/微头条/Clean MD    │ • 次级: 生成包/极简底座/MD 选型   ││
│    └───────────────────────────────────┴───────────────────────────────────┘│
│    注：线框中的 [头条]/[知乎] 仅为示意 Tag；落地 UI 禁用一切 Emoji，用 Lucide │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. 进阶拓展生态区 (Extended Ecosystems · 默认折叠收拢 · 附业务适用指引)      │
│    ▼ 展开查看行业进阶拓展生态 (微信 10% / GitHub 10% / Kimi 8% / 百度 7%)   │
│    • 微信公众号/视频号 (适用: 实体加盟/本地生活/私域强转化)                  │
│    • GitHub 开源 (适用: SaaS软件/数字化外包/技术型企业)                      │
│    • Kimi 研报白皮书 (适用: 行业咨询/IPO律所/高客单大案)                     │
│    • 百度百科与文库 (适用: 集团品牌/政企背书认证)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. 全渠道落地台账与自动化外链回填看板 (Ledger & Audit)                       │
│    • 核心指标: 分发完成率 (已发布/总渠道) + 战略存活率 (200 OK)               │
│    • 操作: [智能批量回填] + [一键全网探活] + [复制台账 MD]                    │
│    • 渠道台账卡片列表 (展示各渠道回填的实际 URL 与存活状态)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interface (接口与交互逻辑设计)

### 1. 后端 API 补充与统一

#### 1.1 补充缺失的头条独立打包路由
* **Path**: `POST /api/projects/{project_id}/toutiao/build`
* **Handler**: 调用 `package_toutiao_assets(project_id, verify=True)`
* **Response**:
  ```json
  {
    "success": true,
    "project_id": "demo_project",
    "article_char_count": 1850,
    "fidelity": {
      "overall_score": 97.5,
      "passed": true
    },
    "micro_posts": [...]
  }
  ```

#### 1.2 升级全局「生成核心矩阵发布包」逻辑（唯一主路径，消除歧义）

> **定稿决策（review 订正）**：顶部主按钮仍走阶段四步骤 `distribute`（`runSingleStep(..., 'distribute')`），在服务端 **级联** 深度打包；不另开第二条互斥入口。既有 `POST /publish/compile` 保留为「仅重编译发稿包 / 单渠道调试」能力，不替换顶部主按钮。

* **主路径 Path**：阶段四步骤执行链（`/run` 或等价 `distribute` step handler）
* **执行动作（严格顺序）**：
  1. 调用 `run_distribute(project_id)` 生成基础 `outputs/dist_*.md` 与交付清单（SOP-04 不变）；
  2. **级联**调用 `package_all_channels(project_id, verify=False)`，生成 `outputs/toutiao_pack/`、`outputs/deepseek_pack/`、`outputs/wechat_pack/`、`outputs/kimi_baidu_pack/`；
     - 选用 `verify=False`：冷启动一键路径优先秒级反馈，避免四渠道保真度核验拖垮主按钮；
     - 保真度 Badge 仍可通过既有 `publish/preview` / 单渠道 build（`verify` 默认 True）按需刷新；
  3. 前端在 `distribute` 成功回调中调用统一的状态刷新（复用 / 增强 `loadStepPreviews`），同时更新：
     - `toutiao-pack-status` -> `已就绪 · 约 XXX 字`
     - `deepseek-pack-status` -> `已就绪 · 约 XXX 字`
     - `wechat-pack-status` -> `已就绪`
     - `kimi-baidu-pack-status` -> `已就绪`
     - Toast：「矩阵 Markdown 与全渠道发稿包已生成」。

#### 1.3 单渠道「生成发稿包」按钮归属
* 头条 / 知乎主卡片：**主 CTA** 仅为「一键复制富文本」+「直达后台」；
* 「生成 XX 发稿包」、微头条、Clean MD、Markdown 底稿等 **一律收纳进次级 `<details>`**，依赖顶部一键级联即可完成冷启动；单渠道 rebuild 仅作补打/排障。
* 实现前提：必须补齐 `POST /toutiao/build`，与已有 `/wechat/build`、`/deepseek/build`、`/kimi_baidu/build` 对称。

---

## Database Schema / Data Structure (数据模型)

数据模型保持向后兼容，不破坏现有存储结构：
1. **`outputs/dist_ledger.json`**：保留渠道回填 URL 与探活状态（`toutiao`, `zhihu`, `wechat`, `github`, `kimi`, `baidu`）；
2. **`outputs/*_pack/`**：保留富文本 HTML、微头条、视频号分镜表、README 与白皮书等生成物；
3. **`outputs/dist_*.md`**：保留标准的 Markdown 文本分发底稿。
