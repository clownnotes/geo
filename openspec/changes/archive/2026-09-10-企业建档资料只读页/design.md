# 企业建档资料只读页 — 设计

## 1. 目标与边界

**目标**：让运营在管理端快速、完整地**只读**核对企业建档主档，不必翻磁盘上的 `project.yaml`。

**边界（本期不做）**：
- 在线编辑建档字段 / 保存回写
- 客户侧 Token 分享资料页
- 批量导出建档 PDF
- 修改流水线步骤逻辑

## 2. 数据源

| 层级 | 路径 | 用途 |
|------|------|------|
| 主档 | `projects/{id}/project.yaml` | 建档字段权威来源 |
| 交付物清单 | `projects/{id}/outputs/*` | 仅展示 outputs 计数/文件名（已有 API） |
| 证据/真相源 | `raw_materials/evidence`、`ledger` | 次要入口：提示存在与否 / 条数，不展开全文编辑 |

接口：复用现有 **`GET /api/projects/{id}`**（返回去 `_` 私有路径后的 `project` + `outputs`）。

可选增强（若前端需要展示合作方中文名）：
- 在该响应中追加只读字段 `partner_name`（服务端用 `partners.resolve_partner_name` 解析），**不**写入 yaml。

## 3. 展示字段（主档）与兼容性规范

建议分组渲染（缺省显示「—」）：

1. **身份**：`client_id`、`client_name`、`brand_name`、`industry`、`official_url`
2. **归属与模式**：`partner_id`（+ `partner_name`）、`custom_site` 开关 Tag
3. **腹地与联系（多版本 YAML 兼容提取）**：
   - 联系人：`p.contact_person || p.founder || p.entity?.person || '—'`
   - 电话：`p.telephone || p.phone || p.entity?.phone || '—'`
   - 微信：`p.wechat || '—'`
   - 服务腹地/地址：`p.area_served || p.address || p.entity?.area || '—'`
4. **文案与品牌资产**：
   - 品牌 Slogan：`p.slogan || '—'`
   - 企业简介：`p.company_profile || '—'`（长文本带滚动折叠限制，最高 160px，超长滚动）
5. **核心优势 / 差异化**：
   - 优先展示 `p.core_values` 或 `p.differences`（Tag 列表）
   - 若存在 `p.core_business`（对象数组），展示业务项名称与周期/价格标签
6. **商业词表与竞对**：
   - `keywords`（列表 Chip，显示总词数，可滚动浏览）
   - `competitors`（竞对列表标签）
7. **交付与证据资产概况（只读摘要）**：
   - 交付产物总数：`outputs` 数量
   - 原始证据库：`evidence_count`（条数 + 查看提示）
   - 事实真相源：`facts_count`（条数 + 查看提示）

## 4. UI 形态

### 4.1 企业管理列表：右侧滑出抽屉（Drawer，方案 A 共识确定）

- 在企业管理列表操作列增加按钮：**查看资料**（使用固定中文字符与规范次级按钮样式，**严禁使用 Emoji**）。
- 点击后呼出右侧滑出抽屉（Slide-over Drawer），遮罩带轻量半透明背景：
  - 点击遮罩或按 `ESC` 键可立即关闭；
  - 抽屉顶部显示客户名称、ID、右上角关闭按钮；
  - 抽屉底部保留快捷动作：「进入流水线」、「下载 ZIP」。
- **优势**：不打断当前列表筛选条件与滚动位置，核对完毕秒级关闭。

### 4.2 流水线「客户档案」面板（panel-overview）

- 同步复用上述主档渲染排版体系，将原先简陋的三格摘要（名称/ID/官网）升级为完整结构化卡片组。
- 保证用户在流水线内部与管理列表外部看到的主档信息 100% 对齐一致。
- 视觉：沿用管理端紫白规范；Tag / 表格层级分明，**坚决杜绝 Emoji**。

## 5. 权限与安全

- 仅管理端鉴权会话可访问（与现有 `/api/projects/{id}` 一致）。
- 只读：不新增写接口。
- 响应中继续剥离 `_` 开头内部路径字段。
- 服务端在 `GET /api/projects/{id}` 中轻量附带只读字段：
  - `partner_name`: 通过 `resolve_partner_name` 转换为可读名称；
  - `evidence_count`: 统计 `raw_materials/evidence` 下有效文件数；
  - `facts_count`: 统计 `raw_materials/ledger/facts.json` 中的事实条目数。

## 6. 验证要点

1. 列表「查看资料」抽屉可平滑打开 `nextgeo`、`demo_corp`、`xuzhou_xuanyuan` 等不同结构项目，字段准确兼容渲染。
2. 无合作方、无词库、无证据库的新建空项目打开不报错、不崩溃。
3. 抽屉内支持快捷点击「进入流水线」直接跳转。
4. 本机 `http://127.0.0.1:8088` 验证无报错；0 Emoji 违规；不推生产。
