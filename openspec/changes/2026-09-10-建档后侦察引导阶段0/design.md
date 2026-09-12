# Design: 建档后侦察引导阶段0

## 0. 审查锁定（Antigravity × Cursor）

| 项 | 决议 |
| :--- | :--- |
| 未侦察默认落点 | 创建 / 进入流水线 → `step-0-probe` |
| 已有基线默认落点 | `baseline_ready` / `awaiting_retest` → `step-1-diag` |
| 未侦察进 01 | 软 `confirm`，不硬卡 |
| 托管占位 | **固定** `https://{client_id}.baicl.cc` + `site_pending: true` |
| 一句话业务 | 新建 **必填**，校验 15～80 字 |
| `site_pending` 剧本 | **跳过 URL/官网收录题**，倾斜选型/痛点/品牌 |

## 1. 信息架构

```
新建成功 / unprobed 进入流水线 →【00 step-0-probe】
baseline_* 进入流水线       →【01 step-1-diag】
CLI 回填后刷新               → 徽章变「已有基线」→ 可点进 01
```

阶段 0 = 协作说明 + 状态 + 命令台；**不**跑审计引擎。

## 2. 前端

### 2.1 路由

- `VIEW_META` / `STEP_TO_VIEW[0] = 'step-0-probe'`
- 侧栏：`00 侦察建档`，图标 Lucide `radar`（备选 `crosshair` / `compass`）
- `enterWizard(id)` 无显式 target 时：读 `probe_status` 决定 0 或 1
- 调用方显式传入 `step-1-diag` 且 `unprobed`：弹出确认后再切

### 2.2 `panel-step-0-probe`

1. 标题：阶段零：侦察建档  
2. 状态徽章 + baseline 元数据；`site_pending` 时 Tag「由我方全托管 / 待客户域名」  
3. 人话：管理台不问豆包；Cursor 出题 → 反重力实战 → CLI 回填；阶段一另说  
4. 三步复制命令（`probe-script` / `preview` / `apply`，带 `client_id`）  
5. 刷新状态；主 CTA「进入阶段一体检」+ `unprobed` 确认文案  
6. 0 Emoji

### 2.3 新建弹窗

```
官网 [text]  可填 pidai.baicl.cc
□ 暂无官网，由我方托管创建  → 清空/忽略手工 URL，用占位并 site_pending=true

一句话业务 [textarea required]  min 15 max 80
行业 [optional short]  仅分类展示
```

提交前：

- `normalizeOfficialUrl(raw, { clientId, sitePending })`
- 校验 `business_one_liner` 长度
- 成功 → `enterWizard(id, 'step-0-probe')`
- 弹窗内删除大段 Cursor 教程（改由阶段 0 承载）

## 3. 数据与 profile

```yaml
business_one_liner: "…"   # 必有（新建）
site_pending: true|false
official_url: "https://{client_id}.baicl.cc"  # 当 site_pending
probe_status: unprobed
```

`scalar_keys` 追加：`business_one_liner`；`site_pending` 用 bool upsert（`as_bool=True` 或等价）。

## 4. `probe-script` 行为

1. 品类锚点：`business_one_liner` 优先，否则 `industry`。  
2. 若 `site_pending`：
   - **不生成**「{brand}官网是什么」及依赖真实客户公网站的 URL 题；
   - 用选型 / 价格坑 / 品牌认知 /（可选）人物 / 全国名单 填满 6～10 条。  
3. 非 pending：保留现有 URL 题（观察 `url_present`）。

## 5. 后端

- `POST /api/projects`：规范化 URL、写 `site_pending` / `business_one_liner`；缺一句话返回 400。  
- 纯函数建议抽到 `tools/geo/utils.py` 或 `probe_backfill.py`：`normalize_official_url`，便于单测。

## 6. 验收

1. 新建后首屏阶段 0。  
2. 命令条 `client_id` 正确；复制可用。  
3. `unprobed`→01 有确认；基线项目进流水线直达 01。  
4. 裸域名与托管占位均可创建；占位 URL 形态固定。  
5. 一句话 &lt;15 或空无法创建；剧本用词体现一句话；`site_pending` 无官网题。  
6. 0 Emoji；本地验证；不推生产。
