# Design: 发前对照卡 Git 式逐条确认

## Architecture (架构设计与对象关系)

```text
pinned 基线（旧卷子）          当前已确认事实（新卷子）
        \                        /
         \______ facts_diff ____/
                    |
              发前对照卡（唯一拍板台）
                    |
         逐条 ✓ 固定  →  全部确认  →  钉住母盘
                    |
         唯一真相源：只读提醒（有冲突/有差量）
```

**原则（钉死）**

1. **对照卡是拍板台**，真相源不是主 diff UI。
2. **每条差量只有两态语义**：原先（pinned） vs 现在（current）；打勾 = 把「现在」这条结果写入真相源并视为本轮已定。
3. **钉住前必须全部确认**：无未决 `conflict`、无未拍板 blocking 行。
4. **不做三选一下拉**作为主路径（历史确认/候选/当前）。

## 差量类型与打勾语义

| 展示 | 颜色 | ✓ 打勾含义 | （可选）✗ 含义 |
| :--- | :--- | :--- | :--- |
| 新增 | 绿 | 确认保留该事实（confirmed） | 拒绝该事实（rejected） |
| 删除 | 灰 | 确认删除（rejected / 不恢复） | 恢复 pinned 旧值并 confirmed |
| 变更 | 琥珀：旧划线 + 新正文 | 确认采用新值 | 恢复旧值 |

冲突导致「当前不在 confirmed 快照」时，对照卡仍以 **删除或变更行** 呈现（带「须拍板」），打勾走同上表，**不**再跳真相源。

## Interface (接口/API/前端组件设计)

### 已有 / 将收口

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| GET | `/api/projects/{id}/corpus/diff?against=pinned` | 返回 `facts_diff` + `fact_actions`（含 op、from/to、blocking） |
| POST | `/api/projects/{id}/corpus/diff-decide` | `{ fact_key, decision: accept\|reject, op }`；单条拍板 |
| POST | `/api/projects/{id}/corpus/pin` | 仍禁止硬冲突；前端在「全部确认」后才主推调用 |
| POST | `/api/projects/{id}/corpus/diff-confirm-all` | **新增（推荐）**：校验本轮待拍板均为已处理 / 无 hard conflict，写 `diff_confirmed_at` 到 meta 或返回 `ready_to_pin: true` |

### 前端布局

1. 对照卡位于真相源与长预览之间（已部分落地，保持）。
2. 每行：标签（新增/删除/变更）+ 键名 + 原先/现在 + **✓**（主）+ 可选 ✗。
3. 对照卡底部：**全部确认**（主按钮）→ 成功后高亮 **钉住当前母盘**。
4. 真相源标题旁：若 `hard_conflict_count>0` 或 `pending_decisions>0`，显示角标「对照卡有待确认」，点击滚动到对照卡。

### 与实验代码的关系

工作区已有部分 `diff-decide` / 行内 ✓✗ / session ack。本变更要求：

- 语义对齐上表（尤其「删除 + ✓ = 确认删除」）。
- 用服务端「全部确认」闸门替代仅靠 sessionStorage 隐藏行。
- 文案去掉「去真相源仲裁」主引导。

## Database Schema / Data Structure

无新库表。可选在 `03_corpus_meta.json` 或 `outputs/pinned/` 旁增加：

```json
{
  "diff_session": {
    "confirmed_at": "ISO-8601",
    "decided_keys": ["entity.legal_name", "..."]
  }
}
```

v1 也可仅用：全部确认 = 实时校验「无 conflict + fact_actions 为空或全为非 blocking」，不落盘。

## 验收标准

1. 刷新对照后，每条能看懂原先 → 现在；新增绿、删除灰。
2. 打勾即可固定，无需打开「历史候选」下拉。
3. 真相源可保持原列表；仅有提醒，不强迫在真相源内仲裁。
4. 全部确认通过前，钉住按钮禁用或明确拦截提示。
5. 全部确认 + 钉住后，再刷新对照应接近 noop（无待拍板）。
