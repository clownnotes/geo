# Design: 阶段零出题落盘与冒烟护栏

## Architecture

### 问题拆分（必须分开治）

```
A. 流程缝：对话框有题 ≠ 磁盘有 probe_script_*.json
B. 工程缝：改代码后关键路径未冒烟 → 假加载/字段错/404
```

本变更同时治 A+B；验收时分别测，禁止再用「数据丢了」一把梭。

### 对象

| 对象 | 职责 |
| :--- | :--- |
| 出题提示词（`plainCopy.qualityPromptText`） | 强制：先列题；落盘口令；落盘路径；未落盘不得宣称「已进管理台」 |
| B 区列表（`ScriptFileList` / ProbeStep2） | 只反映**磁盘**文件；文案须说明「聊天拟问要落盘后才出现在这里」 |
| `smoke:step0` | 构建 + 静态资源 + 最小断言 |

### A. 落盘契约（产品规则 → 提示词/文案）

1. **列题阶段**：IDE 只在对话列拟问；回复须显式写：**未落盘**。  
2. **落盘阶段**：人说「可以落盘」「直接落盘」「写入 roundN」之一 → IDE **必须**写 UTF-8 JSON 到：  
   - 复测：`projects/{id}/outputs/probe_script_retest_roundN.json`（N=现有最大+1，或人指定）  
   - 首轮：`probe_script_draft.json`（或人指定）  
3. **落盘后回复**：绝对/相对路径 + 题数 +「请管理台点刷新列表」。  
4. **管理台**：B 区标题下固定一句人话（示例）：  
   > 这里只显示电脑里已保存的问题清单。Cursor 聊天里列过但没说「可以落盘」的，不会出现在这里。

不做「自动读 Cursor 聊天记录」——不可靠且跨 IDE；**真源仍是磁盘文件**。

### B. 冒烟护栏

**硬规矩**：凡改动 `web/step0-src/`、`web/assets/step0/`、阶段零相关壳挂载或 `/assets/` 路由，**未跑通 `npm run smoke:step0` 不得宣称完成**。

`npm run smoke:step0`（`scripts/smoke_step0.sh`）步骤：

1. `npm run build:step0`（失败时打印构建日志尾部）  
2. 断言 `web/assets/step0/step0.js` 存在且 size > 50KB  
3. 若本机 `8088` 在听：curl 产物期望 200；缺文件期望 404；未启动则 SKIP 不拦  
4. 本地扫 `projects/nextgeo/outputs/probe_script_*.json` 并打印份数（目录必须存在）

脚本放 `scripts/smoke_step0.sh`；根 `package.json` 挂 `smoke:step0`。

### 非目标

- 不把聊天记录同步进管理台。  
- 不上大型 E2E（Playwright 全站）。  
- 不改 `competitor_probe_*` 豆包答案链路（可另案）。

## Interface

- 无强制新后端 API。  
- 若未来要「待落盘」标记：仅允许写磁盘草稿文件（如 `probe_script_chat_pending.json`），仍不读聊天；本变更 **默认不做自动 pending 文件**，除非 review 拍板「列题同时写 pending」。

### 可选增强（review 三选一，写入共识后再 apply）

| 方案 | 做法 | 利弊 |
| :--- | :--- | :--- |
| S0 文案+提示词+冒烟（推荐默认） | 不自动写 pending | 改动小，靠纪律+可见说明 |
| S1 列题即写 pending | IDE/或粘贴后按钮写 `probe_script_pending.json` | 管理台能看见「待确认」；多一个文件态 |
| S2 取消先聊后盘 | 出题直接落盘 | 最快，失去讨论窗 |

**propose 默认按 S0**；产品在 review-log 改选 S1/S2 后再改 tasks。

## Data

- 仍只认 `probe_script_*.json`。  
- 不新增第二真源目录。

## 验收

1. 复制出题提示词 → IDE 列题且标明未落盘 → 刷新 B 区**不应**出现新文件。  
2. 说「可以落盘」→ 新文件出现在 B 区，预览题数正确。  
3. `npm run smoke:step0` 在干净构建下通过；故意删产物再跑应失败。  
4. 文案无「基线/剧本」黑盒主文案。
