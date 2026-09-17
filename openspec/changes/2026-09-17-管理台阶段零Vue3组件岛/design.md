# Design: 管理台阶段零 Vue3 组件岛

## Architecture (架构)

### 绞杀式（Strangler）原则

```
┌─────────────────────────────────────────────┐
│  web/index.html（现有壳：侧栏、登录、步骤路由） │
│                                             │
│   step-0 视图 ──► <div id="step0-app">      │
│                      ▲                      │
│                      │ Vue3 createApp       │
│               web/step0/（源码）              │
│               web/dist/step0/（构建产物）     │
└─────────────────────────────────────────────┘
```

- **壳子**：继续负责登录态、`currentProject`、场景切换、步骤导航；通过明确的「桥」把 `projectId`、`authToken`、少量全局 toast 能力传给岛屿。
- **岛屿**：阶段零全部 UI 与交互（A/B/C+D、问题清单列表、豆包结果回填、复制提示词、刷新 guide）。
- **禁止**：在岛屿内再复制一套项目切换；禁止岛屿直接操作未声明的全局变量（逐步收敛）。

### 对象边界

| 对象 | 职责 |
| :--- | :--- |
| `Step0App` | 根组件：拉 guide、同步徽章、编排子区 |
| `ScriptFileList` | B 区：问题清单列表 / 选中 / 预览 / 删除 |
| `ScriptPreview` | 题目预览 |
| `ProbeKickoff` | C+D：复制「怎么问」、路径说明、附件提醒 |
| `ResultBackfill` | 豆包答案文件列表 / 预览 / 确认写入 |
| `step0Api` | 封装现有 REST，不发明第二套契约 |
| `plainCopy` | 文案常量（对齐 plain-speak 对照表） |

### 构建与托管

- 工具链：Vite + Vue3（与小毛驴同族，降低心智切换）；**不**上 Vue Router / Pinia，除非后续全站迁。
- 产物目录建议：`web/dist/step0/`（`step0.js` + css）；`index.html` 用 `<script type="module">` 引入。
- 开发：`npm run dev` 可只开发岛屿；联调仍走本机 `8088`（Safari）。
- 服务端：`tools/geo/server.py` 已从 `WEB_DIR` 读静态；需确保能提供 `web/dist/**`（或构建输出拷到 `web/assets/step0/`）。优先少改后端：产物放 `web/assets/step0/` 最省事。

**推荐落地路径（省事优先）**：

1. 源码：`web/step0-src/`（Vite 根）
2. 构建输出：`web/assets/step0/`（已在现有静态路径下）
3. `index.html` 阶段零区块清空为挂载点 + 引入构建后的 `assets/step0/step0.js`

### 与「假丢数据」护栏

- 列表区域初始态不得永久「清单加载中」：超时 / 接口失败 / `scripts=[]` 必须分支到人话空态或错误态。
- 自检（开发或启动时）：挂载后若找不到列表根节点或渲染函数未注册 → console + toast 明示「阶段零组件未加载」，禁止静默空白。

## Interface (接口)

### 复用（不改契约，除非单独立项）

- `GET` 阶段零 guide（现有 probe guide / status）
- `GET/DELETE /api/projects/{id}/output/{filename}`（问题清单与结果文件）
- 现有 probe-preview / probe-apply 相关 API

### 壳 ↔ 岛桥（前端）

```ts
// 壳在切换到步骤 0 / 切换项目时调用
window.__GEO_STEP0__ = {
  mount(el, { projectId, authToken, onToast }),
  unmount(),
  refresh(), // 壳在外部改了 project 后
};
```

具体签名可在 apply 时微调，但必须：**单向数据流入岛；岛通过回调通知壳刷新项目状态**。

## Data Structure (数据)

- **不改**磁盘约定：
  - 问题清单：`probe_script_*.json`
  - 豆包答案：`competitor_probe_*.json` + 项目 `probe_status`
- Vue 侧类型与现有 JSON 字段对齐即可；不新增第二真源。

## 非目标 / 风险

| 风险 | 缓解 |
| :--- | :--- |
| 大搬家一次改坏全站 | 只迁 step0；其余步骤零 diff |
| 双份逻辑（HTML 旧 JS + Vue） | 迁完删除 `index.html` 内阶段零大段脚本，禁止双轨 |
| 构建遗忘导致线上空壳 | tasks 含：未构建则挂载点显示「请先 npm run build」人话 |
| 文案回潮黑盒词 | `plainCopy` 集中；对照 archived plain-speak 表 |

## 验收标准（产品可测）

1. Safari 打开管理台 → 步骤 00：能看到问题清单列表（有文件时），不再永久「加载中」。
2. 选中 / 预览 / 删除单份清单可用。
3. 刷新列表、复制提示词、豆包结果区行为与迁前一致（人话文案不回退）。
4. 切换项目后岛屿数据跟着变，不串项目。
