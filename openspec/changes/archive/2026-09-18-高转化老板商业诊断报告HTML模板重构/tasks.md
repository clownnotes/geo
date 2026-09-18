# 细分开发任务清单：高转化老板商业诊断报告 HTML 模板重构

> 对应变更目录：`openspec/changes/2026-09-18-高转化老板商业诊断报告HTML模板重构`

---

## 1. 规范对齐与模板资产标准化

- [x] 1.1 将参考样板 `/Volumes/a1/Downloads/邻里GEO-AI可见度诊断报告（转化版）.html` 核心样式与 DOM 提纯为干净的自包含模板架构
- [x] 1.2 严格实行 0 Emoji 净化：将样板中残留的 `🔴`、`🟢`、`🟡`、`⚠️` 全部重构为 CSS 状态圆点与专业徽章（`.dr-dot` / `.dr-badge`），杜绝低幼感
- [x] 1.3 提交 cross-IDE review（在 `review-log.md` 记录初始设计共识并保持阶段停步）

## 2. 动态数据提取与纯原生 SVG 渲染引擎

- [x] 2.1 创建 `tools/geo/boss_report_html.py`，实现纯原生 SVG 渲染函数：
  - `render_score_ring_svg(score)`：动态计算圆环进度与等级预警色
  - `render_radar_svg(infra, citation, visibility, accuracy)`：动态计算四维雷达多边形顶点
  - `render_pie_svg(unmentioned_pct, wrong_pct, accurate_pct)`：动态计算三段环形图
- [x] 2.2 实现数据提取适配器 `extract_conversion_report_data(project_id, markdown_text)`：
  - 从 `project.yaml` 提取企业与品牌基础档案
  - 从 `audit_metrics.json` 提取底座达标 6 项与技术真实得分
  - 从 `competitor_probe_*.json` 提取 9 组真实问答证据与实测竞品
  - 从 `01_企业AI可见度商业诊断报告.md` 解析老板心理学一句话定性、3 类流失询盘、四步路线与 30 天愿景
- [x] 2.3 实现 `assemble_boss_conversion_html(data)`：组装 7 大核心区块生成完整自包含 HTML 字符串

## 3. 接口接入与管理端闭环联动

- [x] 3.1 改造 `tools/geo/share.py` 中的 `build_audit_report_html_document`：当 `view == "boss"` 时接入全新的 `assemble_boss_conversion_html`
- [x] 3.2 确保 `python3 -m tools.geo audit <project_id>` 在落盘 Markdown 的同时，自动在 `outputs/` 输出排版精美的 `01_企业AI可见度商业诊断报告.html`
- [x] 3.3 验证管理端 `http://localhost:8088/#project=nextgeo&view=step-1-diag`：
  - 【阶段一：测算诊断】顶层选中【老板商业转化版】
  - 点击【下载老板商业报告 (HTML)】直接触发下载该高质感自包含 HTML
  - 点击【客户报告链接】进入分享门户可完整预览

## 4. 自动化测试回归与验收交付

- [x] 4.1 在 `tests/test_conversion_report.py` 中增加端到端 HTML 生成单测，断言包含关键 SVG 元素与 7 大转化区块
- [x] 4.2 严密执行 0 Emoji 静态扫描断言，确保生成的 HTML 字符中 0 违规 Emoji
- [x] 4.3 运行全量单测套件并通过（100% 绿灯）
- [x] 4.4 本地浏览器（Safari / Chrome）人工验收预览效果并向师弟汇报
- [x] 4.5 严格单步停步铁律：严禁擅自归档，严禁擅自推生产
