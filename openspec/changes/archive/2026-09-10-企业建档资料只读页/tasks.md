# 企业建档资料只读页 — 任务清单

## 1. 后端轻量补齐

- [x] 在 `tools/geo/server.py` 的 `GET /api/projects/{id}` 补齐只读 `partner_name`（解析自 `partner_id`）
- [x] 在 `GET /api/projects/{id}` 轻量统计并返回 `evidence_count` 与 `facts_count`
- [x] 确保严格只读、鉴权机制不变、内部私有路径剥离

## 2. 企业管理列表抽屉（Drawer）

- [x] 操作列在「进入流水线」左侧/右侧增加规范按钮「查看资料」
- [x] 构建右侧滑出抽屉组件（带半透明背景蒙层、ESC 键及点击蒙层快速关闭）
- [x] 抽屉内调用 `GET /api/projects/{id}` 渲染完整主档资料，带加载中与错误重试状态
- [x] 抽屉底部提供快捷操作：「进入流水线」、「下载 ZIP」

## 3. 主档展示与多版本 YAML 兼容性

- [x] 封装通用主档渲染逻辑（分组展示：基础身份、归属模式、腹地联系、文案资产、核心优势、商业词表与竞对、交付与证据资产）
- [x] 容错兼容：兼顾扁平键（`telephone`, `contact_person`, `area_served`）与嵌套键（`entity.*`），兼顾 `core_values` / `differences` / `core_business`；兼容 simple-yaml 把 `entity` 拍平为顶层 `person`/`phone`/`area`
- [x] 长文本区域（如企业简介）限制高度并支持纵向滚动，避免撑破页面
- [x] 词库以 Chip 标签组呈现，标明词库总条数

## 4. 流水线客户档案（panel-overview）增强

- [x] 将流水线中的 `panel-overview` 由原先 3 格摘要升级为复用主档结构化卡片组
- [x] 仅保留只读展示与流水线步骤导航，绝无写接口和「保存」按钮

## 5. 视觉规范与自测验收

- [x] 严格遵循商业紫白视觉规范，全组件 **0 Emoji** 违规
- [x] 本地 `http://127.0.0.1:8088` 实测验证：对比 `nextgeo`、`demo_corp`、`xuzhou_xuanyuan` 等典型项目主档
- [x] 验证现有列表操作（进入流水线、修改合作商、下载ZIP、删除）无任何回归
- [x] 在 `review-log.md` 中记录自测日志，停步等待验收（严禁擅自推生产或自动归档）
