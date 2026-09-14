# Design: 阶段三收口小毛驴配置仅系统设置

## Architecture (架构设计与对象关系)

```text
┌─────────────────────┐         ┌──────────────────────────┐
│ GEO 管理台（本机）   │  HTTP   │ 小毛驴 Nextdoor (:3001)  │
│ · 读 .env 机器密钥   │ ──────► │ · 接入方 geo 专属链       │
│ · status / rewrite   │         │ · 模型梯队 / 计费         │
└─────────────────────┘         └──────────────────────────┘
         │
         ├─ 交付流水线阶段三：只展示 status + 立即检测
         └─ 系统设置：唯一 UI 写 NEXTDOOR_* 到 .env
```

**原则（钉死）**

1. **模型选择不在 GEO**：mode 仅 `flash|think|auto`（计费/回落），梯队在小毛驴。
2. **密钥是机器级资产**：一份 `.env`，不是「每个客户项目一套」。
3. **交付页不写密钥**：避免交付操作与运维配置混在同一视觉层。

## Interface (接口/API/前端组件设计)

### 后端（保持不变）

| 方法 | 路径 | 用途 |
| :--- | :--- | :--- |
| GET | `/api/llm/status?refresh=1` | 连通探测；阶段三「立即检测」继续调用 |
| POST | `/api/llm/config` | 白名单写 `.env`；Ping 失败不落盘；**仅设置页调用** |

### 前端

| 位置 | 变更 |
| :--- | :--- |
| `panel-step-3-princeton` 主卡片 | 删除「配置 Nextdoor」按钮；文案去掉「第一步先配置」 |
| 阶段三折叠使用说明 | 改为：统一小毛驴；密钥在系统设置 |
| 系统设置 / 首页大模型中枢 | **保留**「配置 Nextdoor」+「立即检测」；文案标明「运维入口」 |
| `llm-config-modal` | 保留组件；阶段三不再 `openLlmConfigModal()` 入口 |
| `TERMS_DB.llm_status` / `llm_detect` | 可选增补一句：改 Key 请到系统设置 |

### 交互规则

- Tag 黄/红时：提示「请到系统设置检查密钥或隧道」，**不**在阶段三弹出配置框（可链到 `settings-llm` / `home-settings`）。
- 未登录时 status 行为不变。

## Database Schema / Data Structure (数据模型变更)

无数据库变更。环境变量白名单不变：

- `NEXTDOOR_API_KEY` / `NEXTDOOR_JWT_TOKEN`（兼容）
- `NEXTDOOR_BASE_URL`
- `NEXTDOOR_SOURCE_CLIENT`
- `NEXTDOOR_CHAT_MODE`

## 验收标准

1. 阶段三主卡片看不见「配置 Nextdoor」。
2. 状态 Tag + 立即检测 + 问号仍可用。
3. 系统设置仍能打开配置弹窗并成功保存（Ping 通过才落盘）。
4. SOP-03 不再要求「阶段三右上角配置 Nextdoor」为交付第一步。
