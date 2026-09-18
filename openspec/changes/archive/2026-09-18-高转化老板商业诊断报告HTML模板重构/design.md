# OpenSpec 技术架构设计：高转化老板商业诊断报告 HTML 模板重构

> 对应变更目录：`openspec/changes/2026-09-18-高转化老板商业诊断报告HTML模板重构`

---

## 1. 整体架构分层与数据流向

```
┌────────────────────────────────────────────────────────┐
│                   数据源点 (真抓与实测)                  │
├──────────────────────────┬─────────────────────────────┤
│ 1. 基础配置              │ project.yaml                │
│ 2. 网络底座指标          │ outputs/audit_metrics.json  │
│ 3. 真实大模型问答探测    │ outputs/competitor_probe_*.json │
│ 4. 老板心理学文字初稿    │ outputs/01_企业AI可见度商业诊断报告.md │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
              ▼                           ▼
┌────────────────────────────────────────────────────────┐
│   数据提取与评分中枢 (tools/geo/boss_report_html.py)    │
│  - 计算 AIVO 四维得分 (基建/引用/搜索/认知)             │
│  - 计算综合得分 (34/100) 与等级标签 (较差/中等/优秀)    │
│  - 统计实测问答分布 (未提及 / 提及错误 / 提及准确)      │
│  - 提取流失询盘卡片、竞品列表与 30 天愿景数据          │
└──────────────────────────┬─────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────┐
│       纯原生 SVG 与高质感自包含 HTML 模板引擎           │
│  - SVG 评分动态圆环 (动态计算 stroke-dashoffset)       │
│  - SVG AIVO 四维雷达网图 (自动计算多边形 points)       │
│  - 行业 60 分基准对比进度条                            │
│  - 纯 CSS 状态徽章体系 (0 Emoji 绝对红线)              │
│  - 沉浸式暗色 Hero + 模块化卡片排版                    │
└──────────────────────────┬─────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────┐
│                   多端产出与交互闭环                    │
├────────────────────────────────────────────────────────┤
│ 1. 静态产出: outputs/01_企业AI可见度商业诊断报告.html   │
│ 2. API 导出: /api/projects/{id}/export-audit-html?view=boss │
│ 3. 客户大屏: /share/{token}?view=boss_report           │
│ 4. 管理端: http://localhost:8088/#project=nextgeo 点击下载 │
└────────────────────────────────────────────────────────┘
```

---

## 2. 数据结构模型 (ConversionReportData)

```python
@dataclass
class ConversionReportData:
    # 基础信息
    client_name: str         # 邻里GEO（徐州璇源网络科技有限公司）
    brand_name: str          # 邻里GEO
    official_url: str        # https://www.baicl.cc
    report_date: str         # 2026-09-18
    engines_tested: str      # 豆包 + DeepSeek（均开联网）
    sample_count: int        # 9 组真实问答

    # 核心评级
    overall_score: int       # 34
    overall_grade: str       # 较差 (较差 / 中等 / 良好 / 优秀)
    qualitative_summary: str # 能被读到，但没被认对——官网资产做得扎实，AI 却把你认成了另外两家公司。
    badges: List[dict]       # [{"type": "danger", "text": "AI 认知层失守"}, ...]

    # AIVO 四维评分卡
    infra_score: int         # 90 (基建完善度)
    citation_score: int      # 30 (内容可引用性)
    visibility_score: int    # 5  (AI 搜索可见度)
    accuracy_score: int      # 10 (认知准确性)
    dimension_evidence: List[dict] # 4 维真源依据

    # 好消息 (技术底座 6 项)
    tech_checklist: List[dict] # [{"dim": "官网可访问性", "val": "baicl.cc 正常打开", "status": "达标"}, ...]

    # 坏消息 (实测问答与流失询盘)
    probe_stats: dict        # {"unmentioned": 4, "wrong": 4, "accurate": 1, "unmentioned_rate": "0%"}
    probe_table: List[dict]  # [{"id": "T1", "platform": "豆包", "query": "...", "status": "未提及", "actual": "..."}]
    leak_cards: List[dict]   # 3 类流失询盘 (品牌直问、信任词、品类词)

    # 竞品占位与误读分析
    competitor_table: List[dict] # AI 推荐的服务商实测清单
    name_risk_summary: str   # 品牌名在中文语境下被误读为社区门店的风险分析

    # 四步破局与 30 天愿景
    action_roadmap: List[dict]   # P0 品牌标准答案卡、P0 密度补足、P1 证据链、持续复测
    vision_comparison: List[dict]# 现在实测值 vs 30 天后目标值

    # 成交转化 CTA
    cta_price_tag: str       # 起步档：企业 GEO 全案服务 · 免费体检先行（不收费、不绑定）
    cta_contact_wx: str      # nextdoor8
    cta_contact_phone: str   # 13150568888
```

---

## 3. 原生 SVG 图表生成算法

### 3.1 评分进度圆环 (`render_score_ring_svg`)
* 半径 $r = 52$，周长 $C = 2 \times \pi \times 52 \approx 326.73$；
* 偏移量 $\text{offset} = C \times (1 - \frac{\text{score}}{100})$；
* 颜色自适应：
  - $\text{score} < 60$：`#dc2626`（红色警示）；
  - $60 \le \text{score} < 80$：`#d97706`（橙黄预警）；
  - $\text{score} \ge 80$：`#059669`（绿色优良）。

### 3.2 AIVO 四维雷达图 (`render_radar_svg`)
* 画布大小：300 × 300，中心点 $(150, 150)$，最大半径 $R = 110$；
* 4 个轴向对应四个维度（北：基建，东：引用，南：搜索，西：认知）；
* 顶点坐标映射：
  - 北 (基建): $(150, 150 - R \times \frac{S_1}{100})$
  - 东 (引用): $(150 + R \times \frac{S_2}{100}, 150)$
  - 南 (搜索): $(150, 150 + R \times \frac{S_3}{100})$
  - 西 (认知): $(150 - R \times \frac{S_4}{100}, 150)$
* 生成 `<polygon points="..." fill="rgba(220,38,38,0.2)" stroke="#dc2626" />` 及各顶点圆形高亮 `<circle />`。

---

## 4. 0 Emoji 严格红线合规映射表

为彻底杜绝 Emoji 带来的低幼感与非严肃商业感，所有状态元素必须严格采用高质感 CSS 规范：

| 原始参考草稿 | 严禁写法 (违规) | 规范 CSS 替换写法 |
| :--- | :--- | :--- |
| 危险状态徽章 | `🔴 AI 认知层失守` | `<span class="dr-badge dr-badge--danger"><span class="dr-dot dr-dot--danger"></span>AI 认知层失守</span>` |
| 达标状态徽章 | `🟢 技术底座达标` | `<span class="dr-badge dr-badge--success"><span class="dr-dot dr-dot--success"></span>技术底座达标</span>` |
| 警告状态徽章 | `🟡 第三方音量为零` | `<span class="dr-badge dr-badge--warning"><span class="dr-dot dr-dot--warning"></span>第三方音量为零</span>` |
| 表格达标标签 | `✅ 达标` / `🟢 达标` | `<span class="st-ok">达标</span>` |
| 表格未提及标签 | `❌ 未提及` / `🔴 错误` | `<span class="st-bad">未提及</span>` / `<span class="st-bad">错误</span>` |
| 提示与说明行 | `⚠️ 评分方法...` | `<div class="dr-note">注：评分方法...</div>` |

---

## 5. 前后端协同与接口改造

1. **`tools/geo/share.py` 改造**：
   - 现有的 `build_audit_report_html_document(project_id, markdown=None, view="boss")` 分流：
     - 当 `view == "boss"` 时，调用 `build_boss_conversion_report_html(project_id, markdown=markdown)`；
     - 当 `view == "tech"` 时，保留原有的纯工程技术审查报告不变。
2. **`web/index.html` 管理端前台**：
   - 【阶段一：测算诊断】顶层选中【老板商业转化版】时：
     - 点击【下载老板商业报告 (HTML)】下载的文件即为该自包含高转化 HTML；
     - 交付物提示保持为 `01_企业AI可见度商业诊断报告.md` 与 `.html` 双产物可查。
3. **单元测试矩阵 (`tests/test_conversion_report.py`)**：
   - 增加对高转化 HTML 渲染的断言测试：
     - 包含 SVG 评分环与雷达图；
     - 包含 7 大核心业务区块；
     - **0 Emoji 严格静态断言校验**（扫描无彩色 Emoji 字符）。
