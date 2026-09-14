# Proposal: 建档后侦察引导阶段0

## Why (为什么做)

- **痛点**：一期已具备「空壳建档 + CLI 侦察回填」，但创建后默认掉进阶段一体检，前端无「Cursor × 反重力豆包」配合引导，运营感觉前后端逻辑对不上。
- **根因**：侦察在 IDE×浏览器，不在 01～05 按钮里；缺**阶段 0 着陆页**。
- **建档摩擦**：官网强制完整 URL、客户常无站；行业常填过糊词，拖累出题。

## What Changes (改动了什么)

### A. 阶段 0（主需求）— 路由已锁定

| 场景 | 落点 |
| :--- | :--- |
| 新建成功 | 一律 `step-0-probe` |
| 「进入流水线」且 `unprobed`（或缺省） | `step-0-probe` |
| 「进入流水线」且 `baseline_ready` / `awaiting_retest` | 直达 `step-1-diag` |
| 侧栏 00 | 常驻可进 |
| 侧栏/CTA 进 01 且仍 `unprobed` | **软确认警告**，不硬卡死 |

引导页：状态徽章、三步可复制 CLI、刷新状态、进人话说明（管理台不问豆包；阶段一≠侦察）。0 Emoji；侧栏 Lucide `radar`（或 `crosshair` / `compass`）。

### B. 建档表单纠偏 — 口径已锁定

1. **官网**：裸域名自动补 `https://`；勾选「暂无，由我方托管」→ **固定**写入 `official_url: https://{client_id}.baicl.cc` 且 `site_pending: true`；前端展示「由我方全托管 / 待客户域名」。
2. **一句话业务**：新建弹窗 **必填**，建议 **15～80 字**；写入 `business_one_liner`，供 `probe-script` 主原料。行业短标签可保留作筛选，不再单独扛出题。
3. **`site_pending` 时剧本**：`probe-script` **跳过**「查客户官网 / URL 是否出现」类无效题，题量倾斜到本地选型、品类痛点、品牌认知（有人物则人物消歧）。

### 明确不做

- 内嵌反重力 / 自动豆包；Web 上传 probe；改阶段一算法；硬锁死禁止进 01。

## Capabilities

| 能力 | 说明 |
| :--- | :--- |
| `step-0-probe` | 侦察引导工作区 |
| 按 `probe_status` 默认路由 | 见上表 |
| 命令复制条 | 预填 `client_id` |
| 官网规范化 + 托管占位 | `{client_id}.baicl.cc` |
| 必填一句话业务 | 15～80 字约束（前端校验） |

## Impact

- 前端：`web/index.html`；后端：创建/profile/`probe-script`；SOP 写明「创建后必经阶段 0」。
- 依赖已归档：`新建客户侦察后回填竞品与意图词`。
- 不推生产、不擅自归档。
