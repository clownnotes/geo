# Review Log — 管理端首页仪表盘与企业管理拆分

## 2026-09-09 | Cursor | propose 阶段

### 产品共识（用户已拍板）

1. **商业洞察独立一级（方案 A）**——单独逻辑不堆首页。
2. **企业管理必须带搜索 + 筛选**。
3. **代理合作归属**：企业可归业务员/合作方名下，可改挂；用于多人拓客分类管理。本期做名册 + 字段 + 筛选，**不做**业务员独立登录隔离（design 预留二期）。

### 一级菜单草案

仪表盘（默认）→ 企业管理 → 商业洞察 → 运维告警 → 系统设置。

### 请对端核对

- [ ] IA 五级是否够用，有无要合并/改名。
- [ ] 合作方名册放「系统设置」是否合适（或放企业管理顶栏）。
- [ ] 列表过滤：项目少时前端滤 vs 接口 `q` 参数，是否接受 design 写法。

**结论**：`[待讨论]`

---

## 2026-09-09 | Cursor | apply 阶段

### 落地摘要

1. 登录后全局壳：`#home-sidebar` + 五页 `home-*`（仪表盘默认，无客户全表）。
2. 企业管理：搜索 + 行业/SOP/合作方筛选；行内改挂；新建可选归属。
3. 商业洞察 / 运维告警：原顶栏能力迁入；沙箱/ROI 需选演示项目。
4. 系统设置：大模型入口 + 合作方名册 CRUD/归档 + 导出说明。
5. 后端：`tools/geo/partners.py`、`config/geo_partners.yaml`；`GET/POST /api/partners`、`POST /api/projects/{id}/meta`；列表带 `partner_id`。

### 本地验证

- `:8088` 已重启；partners / projects / meta 冒烟通过。
- 流水线「返回企业管理」→ `backToEnterprises()`。

### 未做（按 design 二期）

- 业务员独立登录与数据隔离。

**结论**：`[已修正]`（待产品验收，不归档）

---

## 2026-09-09 | QwenWork | review 阶段（跨端复核，回真实代码 + 一手证据）

### 核验方式

不采信 apply 口头结论，逐项回源码 + 冒烟验证：`web/index.html`(11965 行)、`tools/geo/server.py`、`tools/geo/partners.py`、`config/geo_partners.yaml`，并做 `py_compile` 与 Emoji 码位扫描。

### 落地真实性（均为真实接线，非空壳）

- 全局壳与五页：`#home-sidebar` + `home-dashboard/enterprises/insights/ops/settings` 均存在，仪表盘默认。
- 返回落点：`backToDashboard()`(5423) 已转调 `backToEnterprises()`(5427)，语义正确。
- 合作方列/筛选/改挂：表格列(185)、筛选下拉(171-174/5149-5150)、行内改挂 select(5175/5204)、名册面板(252-273)、新建归属(1626-1628) 均实渲染。
- 后端：GET/POST `/api/partners`(3393/456)、POST `/api/partners/{id}`(469)、POST `/api/projects/{id}/meta`(487)、列表回填 `partner_id/partner_name` 并按 `partner_id` 过滤(3408-3457) 真实存在；`partners.py` 冒烟解析/映射/归档清挂逻辑正常。
- 合规：新增 UI 区 Emoji 命中 **0**；`py_compile` 通过。

### propose 遗留讨论项裁决

1. **IA 五级是否够用** → 够用，符合产品拍板方案 A。`[已达成共识]`
2. **合作方名册放系统设置是否合适** → 合理：名册维护属低频配置放设置；高频"改挂"已在企业管理行内提供。`[已达成共识]`
3. **前端滤 vs 接口 `q`** → 项目量级小，前端滤为主 + 接口预留 `partner_id/industry` 过滤，可接受。`[已达成共识]`

### 已订正（文档类）

- 🟡 `design.md` 接口表原写 `PATCH /api/partners/{id}`、`PATCH /api/projects/{id}/meta`，与实现（两端均 **POST**，落在 `do_POST`）不符。已按真实契约订正为 POST 并加注说明。

### 非阻断建议（可择机走 /opsx-fix，不影响本次验收）

- 🟡 `partners.py::_dump_partners_yaml` 用字符串拼接写 YAML，若合作方名称含双引号/换行会破坏回读；建议改用标准 `yaml` 库落盘或对值做转义。
- 🟢 `_slug_id` 对纯中文名回退 `agent_{时间戳}`，同秒并发创建会 ID 冲突报"已存在"；概率极低，可加随机后缀。
- 🟢 本变更无专用自动化测试（partners 端点/改挂回归），建议补一个离线 pytest。

### 状态提示

- 本变更代码目前仍在工作区未提交（`web/index.html`、`tools/geo/server.py`、`web/geo-admin.css` 为 M；`partners.py`、`config/geo_partners.yaml` 为未跟踪）。审查阶段无需提交，归档时再统一 commit。

**结论**：`[通过]`（审查通过，可进入产品验收；上述 🟡/🟢 为非阻断建议，是否处理由产品决定）

> 停步：本轮仅审查与规范订正，未执行编码或归档。等待产品验收或下一步指令。

---

## 2026-09-09 | Cursor | fix 阶段（响应 QwenWork 非阻断建议）

### 已处理

| 项 | 处理 |
|----|------|
| 🟡 `_dump_partners_yaml` 引号/换行 | 增加 `_escape_yaml_str` / `_unescape_yaml_str`，落盘与回读闭环；`set_project_partner_id` 同步转义 |
| 🟢 纯中文 `_slug_id` 同秒冲突 | `agent_{unix}_{token_hex}`，并对已有 ID 再撞时加后缀 |
| 🟢 缺专用测试 | 新增 `tests/test_partners.py`（4 例） |

### 验证

```text
python3 -m unittest tests.test_partners -v
# Ran 4 tests ... OK
```

### 文件

- `tools/geo/partners.py`
- `tests/test_partners.py`
- `design.md`（落盘转义说明）
- `tasks.md`（6.4）

**结论**：`[已修正]`

> 停步：未归档。等待产品验收或复审。

---

## 2026-09-09 | Cursor | archive 阶段

用户确认验收并下达归档提交指令。tasks 已全部完成；审查结论曾为 `[通过]`，fix 建议已落地。

**结论**：`[通过]`
