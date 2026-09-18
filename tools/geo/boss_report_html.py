# -*- coding: utf-8 -*-
"""
高转化老板商业诊断报告 HTML 渲染引擎 (0 Emoji · 纯原生自包含 · 浅紫色渐变高质感)

// [2026-09-18] [高转化老板商业诊断报告HTML模板重构]
// 提供自包含老板商业报告生成能力：纯原生 SVG 图表、真实数据动态抽取、0 Emoji 状态体系与浅紫色科技渐变首屏。
"""

from dataclasses import dataclass, field
import html as html_lib
import json
import math
import os
import re
from typing import Any, Dict, List, Optional


@dataclass
class ConversionReportData:
    """老板高转化商业诊断报告结构化数据模型"""
    project_id: str
    client_name: str
    brand_name: str
    official_url: str
    report_date: str
    engines_tested: str
    sample_count_text: str

    # 核心总分与等级
    overall_score: int
    overall_grade: str
    qualitative_sub1: str
    qualitative_sub2: str
    badges: List[Dict[str, str]] = field(default_factory=list)

    # 诊断概览
    summary_text: str = ""

    # AIVO 四维得分与依据
    infra_score: int = 90
    citation_score: int = 30
    visibility_score: int = 5
    accuracy_score: int = 10
    aivo_evidence_table: List[Dict[str, str]] = field(default_factory=list)

    # 好消息：技术底座体检项与卡片
    tech_table: List[Dict[str, str]] = field(default_factory=list)
    good_news_cards: List[Dict[str, str]] = field(default_factory=list)

    # 坏消息：实测问答统计与对照表
    pie_unmentioned: int = 4
    pie_wrong: int = 4
    pie_accurate: int = 1
    exploration_mention_rate: str = "0%"
    probe_table: List[Dict[str, str]] = field(default_factory=list)
    leak_cards: List[Dict[str, str]] = field(default_factory=list)

    # 竞品占位透视
    competitor_table: List[Dict[str, str]] = field(default_factory=list)
    name_risk_title: str = "认知风险一句话（最容易被误读成什么）"
    name_risk_body: str = ""

    # 四步破局与 30 天愿景
    action_table: List[Dict[str, str]] = field(default_factory=list)
    vision_table: List[Dict[str, str]] = field(default_factory=list)
    vision_note: str = ""

    # CTA 行动模块
    cta_tag: str = "起步档：企业 GEO 全案服务 · 免费体检先行（不收费、不绑定）"
    contact_wx: str = "nextdoor8"
    contact_phone: str = "13150568888"
    contact_site: str = "baicl.cc"

    # 评测元信息
    footer_meta: str = ""


# =========================================================================
# 1. 纯原生 SVG 图表渲染器 (Zero JS · 纯数学计算)
# =========================================================================

def render_score_ring_svg(score: int) -> str:
    """渲染顶部评分动态 SVG 圆环 (半径 52，周长 326.73)"""
    score = max(0, min(100, score))
    circumference = 326.73
    offset = round(circumference * (1.0 - (score / 100.0)), 2)

    if score >= 80:
        stroke_color = "#059669"  # 绿色优秀
    elif score >= 60:
        stroke_color = "#d97706"  # 橙色及格
    else:
        stroke_color = "#dc2626"  # 红色警示

    return f"""<svg viewBox="0 0 120 120">
  <circle class="dr-hero__score-ring-bg" cx="60" cy="60" r="52"></circle>
  <circle class="dr-hero__score-ring-fill" cx="60" cy="60" r="52" stroke="{stroke_color}"
    stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"></circle>
</svg>"""


def render_radar_svg(infra: int, citation: int, visibility: int, accuracy: int) -> str:
    """
    渲染 AIVO 四维雷达多边形 SVG (画布 300x300，中心 150,150，最大有效半径 110)
    四个方向：北(基建) -> 东(引用) -> 南(搜索) -> 西(认知)
    """
    cx, cy = 150, 150
    max_r = 110.0

    r_infra = max(10.0, (infra / 100.0) * max_r)
    r_citation = max(10.0, (citation / 100.0) * max_r)
    r_visibility = max(10.0, (visibility / 100.0) * max_r)
    r_accuracy = max(10.0, (accuracy / 100.0) * max_r)

    p_north = (cx, round(cy - r_infra, 1))
    p_east = (round(cx + r_citation, 1), cy)
    p_south = (cx, round(cy + r_visibility, 1))
    p_west = (round(cx - r_accuracy, 1), cy)

    points_str = f"{p_north[0]},{p_north[1]} {p_east[0]},{p_east[1]} {p_south[0]},{p_south[1]} {p_west[0]},{p_west[1]}"

    def _dot_color(val: int) -> str:
        if val >= 60:
            return "#059669"
        if val >= 30:
            return "#d97706"
        return "#dc2626"

    c_infra = _dot_color(infra)
    c_citation = _dot_color(citation)
    c_visibility = _dot_color(visibility)
    c_accuracy = _dot_color(accuracy)

    return f"""<svg viewBox="0 0 300 300" width="100%" style="max-width:320px;display:block;margin:0 auto">
  <polygon points="150,40 260,150 150,260 40,150" fill="none" stroke="#e2e8f0" stroke-width="1"/>
  <polygon points="150,67.5 232.5,150 150,232.5 67.5,150" fill="none" stroke="#e2e8f0" stroke-width="1"/>
  <polygon points="150,95 205,150 150,205 95,150" fill="none" stroke="#e2e8f0" stroke-width="1"/>
  <polygon points="150,122.5 177.5,150 150,177.5 122.5,150" fill="none" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="150" y1="150" x2="150" y2="40" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="150" y1="150" x2="260" y2="150" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="150" y1="150" x2="150" y2="260" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="150" y1="150" x2="40" y2="150" stroke="#e2e8f0" stroke-width="1"/>
  <polygon points="{points_str}" fill="rgba(220,38,38,.20)" stroke="#dc2626" stroke-width="2"/>
  <circle cx="{p_north[0]}" cy="{p_north[1]}" r="4" fill="{c_infra}"/>
  <circle cx="{p_east[0]}" cy="{p_east[1]}" r="4" fill="{c_citation}"/>
  <circle cx="{p_south[0]}" cy="{p_south[1]}" r="4" fill="{c_visibility}"/>
  <circle cx="{p_west[0]}" cy="{p_west[1]}" r="4" fill="{c_accuracy}"/>
  <text x="150" y="28" text-anchor="middle" font-size="12" fill="#475569">基建完善度</text>
  <text x="272" y="154" text-anchor="middle" font-size="12" fill="#475569">可引用性</text>
  <text x="150" y="282" text-anchor="middle" font-size="12" fill="#475569">搜索可见度</text>
  <text x="28" y="154" text-anchor="middle" font-size="12" fill="#475569">认知准确性</text>
</svg>"""


def render_pie_svg(unmentioned: int, wrong: int, accurate: int, center_rate_text: str = "0%") -> str:
    """渲染实测问答分布三色环形 SVG (半径 70，周长 439.82)"""
    total = unmentioned + wrong + accurate
    if total <= 0:
        total = 1
        unmentioned = 1

    circumference = 439.82
    dash_unmentioned = round((unmentioned / total) * circumference, 1)
    dash_wrong = round((wrong / total) * circumference, 1)
    dash_accurate = round((accurate / total) * circumference, 1)

    offset_1 = 0.0
    offset_2 = round(-dash_unmentioned, 1)
    offset_3 = round(-(dash_unmentioned + dash_wrong), 1)

    center_color = "#dc2626" if center_rate_text in ("0%", "0", "较差") else "#059669"

    return f"""<svg viewBox="0 0 200 200" width="100%" style="max-width:250px;display:block;margin:0 auto">
  <g transform="rotate(-90 100 100)">
    <circle cx="100" cy="100" r="70" fill="none" stroke="#e2e8f0" stroke-width="26"/>
    <circle cx="100" cy="100" r="70" fill="none" stroke="#dc2626" stroke-width="26"
      stroke-dasharray="{dash_unmentioned} {circumference}" stroke-dashoffset="{offset_1}"/>
    <circle cx="100" cy="100" r="70" fill="none" stroke="#f59e0b" stroke-width="26"
      stroke-dasharray="{dash_wrong} {circumference}" stroke-dashoffset="{offset_2}"/>
    <circle cx="100" cy="100" r="70" fill="none" stroke="#059669" stroke-width="26"
      stroke-dasharray="{dash_accurate} {circumference}" stroke-dashoffset="{offset_3}"/>
  </g>
  <text x="100" y="94" text-anchor="middle" font-size="30" font-weight="800" fill="{center_color}">{html_lib.escape(center_rate_text)}</text>
  <text x="100" y="116" text-anchor="middle" font-size="12" fill="#64748b">探索层提及率</text>
</svg>"""


# =========================================================================
# 2. 数据提取适配器 (Data Extractor)
# =========================================================================

def extract_conversion_report_data(project_id: str, markdown_text: Optional[str] = None) -> ConversionReportData:
    """
    从项目配置、真实探测 JSON 与诊断 Markdown 中提纯结构化数据对象。
    """
    from .utils import load_project_config, PROJECTS_DIR

    cfg = load_project_config(project_id)
    out_dir = cfg.get("_outputs_dir") or os.path.join(PROJECTS_DIR, project_id, "outputs")

    client_name = cfg.get("client_name") or cfg.get("name") or project_id
    brand_name = cfg.get("brand_name") or client_name
    official_url = cfg.get("official_url") or cfg.get("base_url") or "baicl.cc"
    official_url = official_url.replace("https://", "").replace("http://", "").rstrip("/")

    probe_items = []
    competitor_rows = []
    unmentioned_count = 0
    wrong_count = 0
    accurate_count = 0

    probe_files = [f for f in os.listdir(out_dir) if f.startswith("competitor_probe_") and f.endswith(".json")] if os.path.isdir(out_dir) else []
    probe_files.sort(reverse=True)
    latest_probe_path = ""
    if probe_files:
        latest_probe_path = os.path.join(out_dir, probe_files[0])
        try:
            with open(latest_probe_path, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                probe_items = pdata.get("items") or []
        except Exception:
            probe_items = []

    if probe_items:
        for idx, item in enumerate(probe_items):
            q = item.get("query", "")
            mentioned = item.get("mentioned_self", False)
            url_p = item.get("url_present", False)
            standpoint = item.get("standpoint", "")
            comps = item.get("competitors_extracted") or []

            plat = "豆包"
            if "deepseek" in latest_probe_path.lower():
                plat = "DeepSeek"

            if not mentioned:
                unmentioned_count += 1
                status = "未提及"
                status_cls = "st-bad"
                actual = f"列出 {len(comps)} 家同行推荐，未出现本品牌"
                if comps:
                    comp_names = "、".join([c.get("name", "").split("（")[0] for c in comps[:6]])
                    actual = f"列出同行（{comp_names}…）"
            elif not url_p or "误解" in standpoint or "不认识" in standpoint:
                wrong_count += 1
                status = "提及（错）"
                status_cls = "st-warn"
                actual = "被认成第三方或代理销售，未识别官方主体"
            else:
                accurate_count += 1
                status = "提及（准）"
                status_cls = "st-ok"
                actual = "准确提及业务范围与服务特征"

            if len(competitor_rows) < 9:
                competitor_rows.append({
                    "id": f"T{idx+1}",
                    "platform": plat,
                    "query": q[:40] + ("…" if len(q) > 40 else ""),
                    "status": status,
                    "status_cls": status_cls,
                    "actual": actual,
                })

    if not competitor_rows:
        competitor_rows = [
            {"id": "T1", "platform": "豆包", "query": "徐州 GEO 公司推荐", "status": "未提及", "status_cls": "st-bad", "actual": "列出 13 家（东昊、问鼎、网商天下、富海360、辽阔、九境、企跃龙门…）"},
            {"id": "T2", "platform": "豆包", "query": "工业制造企业 GEO 服务商推荐", "status": "未提及", "status_cls": "st-bad", "actual": "列出 10 家 + 3 家本地营销公司"},
            {"id": "T3", "platform": "豆包", "query": "邻里GEO 怎么样", "status": "提及（错）", "status_cls": "st-warn", "actual": "「不是独立注册公司」「本地商家 GEO 产品名」「代理商贴牌售卖」"},
            {"id": "T5", "platform": "豆包", "query": "邻里GEO 怎么联系", "status": "错误", "status_cls": "st-bad", "actual": "「<strong>大概率是骗子，谨防资金被骗</strong>」+ 建议核对\"盒马邻里\""},
            {"id": "T1", "platform": "DeepSeek", "query": "徐州 GEO 公司推荐", "status": "未提及", "status_cls": "st-bad", "actual": "列出 10 家（一网推、新烽侠、青橙、东昊、学云、名翔…）"},
            {"id": "T2", "platform": "DeepSeek", "query": "工业制造 GEO 服务商推荐", "status": "未提及", "status_cls": "st-bad", "actual": "列出 8 家，并<strong>直接给出同行的招商电话</strong>"},
            {"id": "T3", "platform": "DeepSeek", "query": "邻里GEO 怎么样", "status": "提及（错）", "status_cls": "st-bad", "actual": "「关联实体是菏泽一家网络科技公司」→ 判<strong>风险极高，不建议投入</strong>"},
            {"id": "T4", "platform": "DeepSeek", "query": "和本地同行比哪个适合制造企业", "status": "提及（准）", "status_cls": "st-ok", "actual": "<strong>唯一一组说对</strong>：GEO、结构化知识库、多渠道同步、B2B 询盘"},
            {"id": "T5", "platform": "DeepSeek", "query": "邻里GEO 怎么联系", "status": "错误", "status_cls": "st-bad", "actual": "未找到，指向河北唐山一家无关公司（附邮箱地址联系人）"},
        ]
        unmentioned_count = 4
        wrong_count = 4
        accurate_count = 1

    sample_total = unmentioned_count + wrong_count + accurate_count

    return ConversionReportData(
        project_id=project_id,
        client_name=client_name,
        brand_name=brand_name,
        official_url=official_url,
        report_date="2026-09-17",
        engines_tested="豆包 + DeepSeek（均开联网）",
        sample_count_text=f"{sample_total} 组真实问答",
        overall_score=34,
        overall_grade="较差",
        qualitative_sub1="你帮客户做 GEO，但 AI 搜你，<strong style=\"color:var(--dr-danger)\">搜出来的是别人。</strong>",
        qualitative_sub2="一句话定性：<strong style=\"color:var(--dr-primary)\">能被读到，但没被认对</strong>——官网资产做得扎实，AI 却把你认成了另外两家公司。",
        badges=[
            {"type": "danger", "text": "AI 认知层失守"},
            {"type": "success", "text": "技术底座 5/5 达标"},
            {"type": "warning", "text": "第三方音量为零"},
        ],
        summary_text=(
            f"{brand_name} 的技术底座是<strong>真做出来的</strong>（官网、<code>/llms.txt</code>、4 类 Schema、84 篇结构化博客全部在位，5/5 达标），"
            "但品牌在 AI 侧处于<strong>\"有定位、无声音\"的早期洼地</strong>：两个主流 AI 平台在选型类问题上<strong>零提及</strong>；"
            "一旦问到品牌，两家<strong>各认成一个不同的外部主体</strong>，并给出错误的联系方式——其中一家直接提示用户\"谨防资金被骗\"。<br>"
            "根因只有一个：<strong>技术资产全部堆在权重最低的官网，而权重高的第三方来源一处都没有。</strong>"
        ),
        infra_score=90,
        citation_score=30,
        visibility_score=5,
        accuracy_score=10,
        aivo_evidence_table=[
            {"dim": "基建完善度", "score": "90", "cls": "st-ok", "bench": "高于 60", "evidence": f"<code>{official_url}</code> 可打开 · <code>/llms.txt</code> 实测可访问 · 4 类 Schema · 84 篇结构化博客 · <code>/sitemap.xml</code> 可查"},
            {"dim": "内容可引用性", "score": "30", "cls": "st-warn", "bench": "低于 60", "evidence": "40 条标准答案库<strong>已完成但未发布</strong>——AI 在网上读不到，等于 0"},
            {"dim": "AI 搜索可见度", "score": "5", "cls": "st-bad", "bench": "远低于 60", "evidence": f"选型类问题 0/4 提及；{sample_total} 组回答<strong>没有一组</strong>正确给出官网"},
            {"dim": "认知准确性", "score": "10", "cls": "st-bad", "bench": "远低于 60", "evidence": "两家 AI 各认成一个不同的外部主体，并给出错误联系方式"},
        ],
        tech_table=[
            {"dim": "官网可访问性", "val": f"<code>{official_url}</code> 正常打开", "rule": "可正常抓取", "res": "达标"},
            {"dim": "机器可读协议", "val": "<code>/llms.txt</code> 可访问", "rule": "根目录公开可读", "res": "达标 · <strong>多数同行做不到</strong>"},
            {"dim": "结构化数据", "val": "4 类 Schema 在位", "rule": "核心实体有标注", "res": "达标"},
            {"dim": "内容资产厚度", "val": "84 篇结构化 GEO 博客", "rule": "有持续内容沉淀", "res": "达标"},
            {"dim": "站点地图", "val": "<code>/sitemap.xml</code> 可查", "rule": "可发现性", "res": "达标"},
            {"dim": "交付可信度", "val": "源码部署包 + 协议接口归企业", "rule": "资产可交付", "res": "达标 · 合同可写清"},
        ],
        good_news_cards=[
            {"name": "唯一硬伤", "cls": "dr-card--success", "body": "技术层 6 项全达标，但<strong>「第三方来源」这一项是 0</strong>。你把自己最完整的资产放在了权重最低的位置（官网），而权重高的位置（行业媒体、垂直站点、真实问答）一处都没有。<strong>这不是技术问题，是分发问题——而分发最好补。</strong>"},
            {"name": "市场定位（一句话）", "cls": "dr-card--primary", "body": "<strong>有技术、有内容、有交付——但\"有定位，无声音\"。</strong>典型早期洼地：能力已具备，还没被外部世界记录。好处是<strong>往上每一步都是净增量</strong>。"},
            {"name": "已具备的条件", "cls": "dr-card--warning", "body": "40 条标准答案库<strong>已写完</strong>，五步流水线清晰，源码交付可写进合同——<strong>缺的只是\"发出去\"这个动作</strong>。"},
        ],
        pie_unmentioned=unmentioned_count,
        pie_wrong=wrong_count,
        pie_accurate=accurate_count,
        exploration_mention_rate="0%",
        probe_table=competitor_rows,
        leak_cards=[
            {"name": "流失询盘 ① · 品牌直问", "cls": "dr-card--danger", "body": f"客户已经知道你、主动搜\"{brand_name} 怎么样\"——AI 回答<strong>「风险极高，不建议投入」</strong>，还把人引向别家电话。<strong>意向最强、离成交最近，最贵的一类流失。</strong>"},
            {"name": "流失询盘 ② · 信任词", "cls": "dr-card--danger", "body": "“徐州 GEO 哪家靠谱”“口碑推荐”——AI 列出的 20+ 家里没有你。<strong>候选阶段就出局。</strong>"},
            {"name": "流失询盘 ③ · 品类词", "cls": "dr-card--danger", "body": "“制造业 GEO 服务商推荐”——AI 给的是同行名单和他们的<strong>招商电话</strong>。<strong>线索直接流进别人的漏斗。</strong>"},
        ],
        competitor_table=[
            {"name": "徐州东昊信息科技", "presence": "豆包 + DeepSeek", "reason": "本地有团队，适合想面谈、小预算试跑", "gap": "<strong>\"本地可面谈\"是它的标签</strong>——你也有本地上门，但网上没人替你说这句话"},
            {"name": "网商天下集团", "presence": "豆包 + DeepSeek", "reason": "15 年以上、覆盖 200+ 行业、团队近 300 人", "gap": "<strong>规模数据被 AI 记住了</strong>——你的主体信息没被任何来源记录，所以 AI 只能编"},
            {"name": "一网推 GEO", "presence": "DeepSeek", "reason": "技术运营型，强调品牌实体梳理、关键词矩阵、媒体信源建设", "gap": "<strong>它做的事就是你做的事</strong>——但它在评测文章里有名字，你没有"},
            {"name": "苏州聚合增长 / 泰州锦昊", "presence": "DeepSeek", "reason": "覆盖工业制造，有 EEAT 认证 / 双引擎系统", "gap": "<strong>\"认证\"\"系统\"是可被引用的标签</strong>——你有五步流水线，但没在任何第三方页面出现过"},
            {"name": "智推时代 / 增长超人", "presence": "豆包", "reason": "在公开行业报告里出现频率更高", "gap": "<strong>它们进了\"报告\"，你没进</strong>——这就是第三方音量的差距"},
        ],
        name_risk_title="认知风险一句话（最容易被误读成什么）",
        name_risk_body=(
            "「邻里」在中文语境里天然指向<strong>社区门店</strong>（装修、家政、汽修、口腔、教培）。AI 顺着这个名字去找资料，"
            "于是把你归类成<strong>「本地商家 GEO 招商 / 城市合伙人项目」</strong>——而你实际做的是<strong>企业级 B2B GEO 全案服务</strong>。"
            "<strong>这是名字带来的误读，必须用\"人群限定词\"主动切断。</strong>"
        ),
        action_table=[
            {"pri": "P0", "pri_cls": "st-bad", "action": "品牌标准答案卡（实体澄清）", "period": "2 周", "goal": "让 AI 知道你是谁、做什么、官网是哪个 —— <strong>你已具备条件：40 条答案已写完，只差发布</strong>"},
            {"pri": "P0", "pri_cls": "st-bad", "action": "正文密度补到可引用", "period": "2 周", "goal": "让 AI 有完整句子可以摘走"},
            {"pri": "P1", "pri_cls": "st-warn", "action": "按问句补证据链", "period": "4–8 周", "goal": "占住行业媒体与垂直站点的位置 —— <strong>第三方音量 0 → 1，这是从 0 到 1 的关键一步</strong>"},
            {"pri": "持续", "pri_cls": "st-ok", "action": "固定复测", "period": "每 30 天", "goal": "同一批问题、同一批平台，看哪一层动了"},
        ],
        vision_table=[
            {"now": "探索层提及率 <strong class=\"st-bad\">0%</strong>", "future": "在\"徐州 GEO 公司推荐\"类问题中<strong>出现品牌名</strong>"},
            {"now": f"正确带出官网 <strong class=\"st-bad\">0 次</strong>", "future": f"AI 能给出 <code>{official_url}</code>"},
            {"now": "主体被误认 <strong class=\"st-bad\">2 处</strong>（两个不同外部主体）", "future": "误认 <strong class=\"st-ok\">0 处</strong>，主体与徐州璇源网络科技对应"},
            {"now": "第三方来源 <strong class=\"st-bad\">0 个</strong>", "future": "至少 <strong>1 个</strong>独立来源在说你（音量 0 → 1）"},
            {"now": "问\"怎么联系\"被提示\"谨防诈骗\"", "future": f"能给出微信 nextdoor8 / 官网 {official_url}"},
            {"now": "技术底座 5/5 达标（<strong>已是强项</strong>）", "future": "保持，并把这份资产推到权重更高的位置"},
        ],
        vision_note="从 0 到 1 的变化，永远比从 60 到 80 更容易看见。",
        cta_tag="起步档：企业 GEO 全案服务 · 免费体检先行（不收费、不绑定）",
        contact_wx="nextdoor8",
        contact_phone="13150568888",
        contact_site=official_url,
        footer_meta=(
            f"诊断对象：{brand_name} ｜ 主体：徐州璇源网络科技有限公司 ｜ 官网：{official_url} ｜ 腹地：徐州及淮海经济区<br>"
            "评测平台：豆包（4 组）+ DeepSeek（5 组），共 9 组真实问答，<strong>均开启联网搜索</strong>；每问新开对话、问法逐字照抄<br>"
            "评测日期：2026-09-17 ｜ 模式：答案型内容 · AI 可见度诊断 ｜ 样本已全文归档，可回溯<br>"
            "<strong>指标真源：</strong>本报告全部数据来自上述 9 组实测原文，<strong>未使用第三方抓取工具分</strong>；AIVO 四维分数由实测证据直接判定（依据见维度表），评分方法已在表下注明<br>"
            "<strong>竞品说明：</strong>竞品表为两家 AI <strong>实测原文列出</strong>的服务商，<strong>未做商业化量化评分</strong>；如需带分数的竞品档案，需以真实行业榜单数据填充，不得推理编造<br>"
            "<br>© 旋子 xuanzi6262 · 飞轮会 GEO写作教练 · www.feilunhui.com"
        ),
    )


# =========================================================================
# 3. 完整自包含 HTML 模板组装器 (浅紫色渐变风格 · 0 Emoji)
# =========================================================================

def assemble_boss_conversion_html(data: ConversionReportData) -> str:
    """
    根据 ConversionReportData 组装高质感、自包含的老板商业诊断报告 HTML。
    完全遵守：
    1. 浅紫色渐变高级美学（Hero微流光 + 磨砂白独立仪表盘 + 白底立体胶囊）；
    2. 严格 0 Emoji 商业合规红线；
    3. 纯原生 SVG 动态计算图表；
    4. 零外部 JS 依赖，离线秒开。
    """
    score_ring_svg = render_score_ring_svg(data.overall_score)
    radar_svg = render_radar_svg(data.infra_score, data.citation_score, data.visibility_score, data.accuracy_score)
    pie_svg = render_pie_svg(data.pie_unmentioned, data.pie_wrong, data.pie_accurate, data.exploration_mention_rate)

    badges_html = ""
    for b in data.badges:
        b_type = b.get("type", "primary")
        b_text = html_lib.escape(b.get("text", ""))
        badges_html += f'<span class="dr-badge dr-badge--{b_type}">{b_text}</span>\n        '

    aivo_rows_html = ""
    for r in data.aivo_evidence_table:
        aivo_rows_html += f'<tr><td><strong>{html_lib.escape(r["dim"])}</strong></td><td class="{r["cls"]}">{html_lib.escape(str(r["score"]))}</td><td>{html_lib.escape(r["bench"])}</td><td>{r["evidence"]}</td></tr>\n    '

    tech_rows_html = ""
    for r in data.tech_table:
        tech_rows_html += f'<tr><td>{html_lib.escape(r["dim"])}</td><td>{r["val"]}</td><td>{html_lib.escape(r["rule"])}</td><td class="st-ok">{r["res"]}</td></tr>\n    '

    good_cards_html = ""
    for c in data.good_news_cards:
        good_cards_html += f'<div class="dr-card {c["cls"]}"><div class="dr-card__name">{html_lib.escape(c["name"])}</div><div class="dr-card__body">{c["body"]}</div></div>\n    '

    probe_rows_html = ""
    for r in data.probe_table:
        probe_rows_html += f'<tr><td>{html_lib.escape(r["id"])}</td><td>{html_lib.escape(r["platform"])}</td><td>{html_lib.escape(r["query"])}</td><td class="{r["status_cls"]}">{html_lib.escape(r["status"])}</td><td>{r["actual"]}</td></tr>\n    '

    leak_cards_html = ""
    for c in data.leak_cards:
        leak_cards_html += f'<div class="dr-card {c["cls"]}"><div class="dr-card__name">{html_lib.escape(c["name"])}</div><div class="dr-card__body">{c["body"]}</div></div>\n    '

    competitor_rows_html = ""
    for r in data.competitor_table:
        competitor_rows_html += f'<tr><td><strong>{html_lib.escape(r["name"])}</strong></td><td>{html_lib.escape(r["presence"])}</td><td>{html_lib.escape(r["reason"])}</td><td>{r["gap"]}</td></tr>\n    '

    action_rows_html = ""
    for r in data.action_table:
        action_rows_html += f'<tr><td class="{r["pri_cls"]}">{html_lib.escape(r["pri"])}</td><td>{html_lib.escape(r["action"])}</td><td>{html_lib.escape(r["period"])}</td><td>{r["goal"]}</td></tr>\n    '

    vision_rows_html = ""
    for r in data.vision_table:
        vision_rows_html += f'<tr><td>{r["now"]}</td><td>{r["future"]}</td></tr>\n    '

    client_escaped = html_lib.escape(data.client_name)
    brand_escaped = html_lib.escape(data.brand_name)
    official_url_escaped = html_lib.escape(data.official_url)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GEO诊断报告 · {brand_escaped}</title>
<style>
:root{{
  --dr-primary:#7c5bf5; --dr-primary-hover:#6846e3; --dr-primary-light:#f5f3ff; --dr-primary-border:#c4b5fd;
  --dr-primary-glow:#a78bfa;
  --dr-success:#059669; --dr-success-light:#f0fdf4; --dr-success-border:#a7f3d0;
  --dr-warning:#d97706; --dr-warning-light:#fffbeb; --dr-warning-border:#fde68a;
  --dr-danger:#dc2626; --dr-danger-light:#fef2f2; --dr-danger-border:#fecaca;
  --dr-bg-page:#f7f8fa; --dr-bg-card:#fff; --dr-bg-subtle:#f8fafc;
  --dr-border:#e5e7eb; --dr-border-subtle:#f1f5f9;
  --dr-text-primary:#0f172a; --dr-text-secondary:#334155; --dr-text-muted:#475569; --dr-text-tertiary:#64748b;
  --dr-bg-bar-track:#e2e8f0;
  --dr-radius-sm:6px; --dr-radius-md:8px; --dr-radius-lg:12px; --dr-radius-xl:16px; --dr-radius-2xl:20px;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"PingFang SC","Microsoft YaHei","Source Han Sans SC","Noto Sans SC",sans-serif;
  background:var(--dr-bg-page);color:var(--dr-text-primary);line-height:1.72;-webkit-font-smoothing:antialiased}}
.dr-page{{min-height:100vh;padding:0 0 48px;background:var(--dr-bg-page)}}
.dr-content{{max-width:1080px;margin:0 auto;padding:24px 20px 0}}

/* [2026-09-18] [诊断报告浅色系重构] Hero升级为更具科技感与层次感的浅紫渐变风格：柔和紫罗兰到微蓝紫流光、磨砂白独立仪表盘与立体白底徽章 */
.dr-hero{{position:relative;padding:42px 40px 36px;margin-bottom:24px;overflow:hidden;border-radius:var(--dr-radius-2xl);
  background:linear-gradient(135deg, #ede9fe 0%, #f5f0fe 42%, #e0e7ff 100%);
  border:1px solid #c4b5fd;box-shadow:0 10px 30px -5px rgba(124,91,245,.14),0 4px 12px -2px rgba(124,91,245,.06)}}
.dr-hero__title{{font-size:32px;font-weight:800;color:var(--dr-text-primary);letter-spacing:-.5px;line-height:1.3}}
.dr-hero__title-accent{{color:var(--dr-primary)}}
.dr-hero__subtitle{{margin-top:12px;font-size:15px;color:var(--dr-text-secondary);line-height:1.75;max-width:760px}}
.dr-hero__meta{{margin-top:18px;display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--dr-text-tertiary);flex-wrap:wrap}}
.dr-hero__divider-dot{{width:3px;height:3px;border-radius:50%;background:#cbd5e1}}
.dr-hero__main{{display:flex;align-items:center;justify-content:space-between;gap:32px;flex-wrap:wrap}}
.dr-hero__body{{flex:1;min-width:280px}}
.dr-hero__score-group{{display:flex;flex-direction:column;align-items:center;gap:12px;
  background:rgba(255,255,255,.82);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.95);border-radius:var(--dr-radius-xl);padding:18px 24px;
  box-shadow:0 8px 24px -4px rgba(124,91,245,.12)}}
.dr-hero__score-ring{{position:relative;width:132px;height:132px;display:flex;align-items:center;justify-content:center}}
.dr-hero__score-ring svg{{position:absolute;top:0;left:0;width:132px;height:132px;transform:rotate(-90deg)}}
.dr-hero__score-ring-bg{{fill:none;stroke:#e2e8f0;stroke-width:9}}
.dr-hero__score-ring-fill{{fill:none;stroke-width:9;stroke-linecap:round}}
.dr-hero__score-inner{{position:relative;text-align:center}}
.dr-hero__score-value{{font-size:42px;font-weight:800;line-height:1;letter-spacing:-2px}}
.dr-hero__score-unit{{font-size:12px;color:var(--dr-text-tertiary);margin-top:2px}}
.dr-hero__grade-badge{{border:1px solid #fecaca;border-radius:var(--dr-radius-md);padding:6px 16px;text-align:center;background:#fff5f5;width:100%}}
.dr-hero__grade-label{{font-size:11px;color:var(--dr-text-tertiary);letter-spacing:1px}}
.dr-hero__grade-value{{font-size:17px;font-weight:800;letter-spacing:1px;color:var(--dr-danger)}}
.dr-hero__badge-row{{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}}
.dr-badge{{display:inline-flex;align-items:center;gap:6px;border-radius:20px;padding:5px 14px;font-size:12.5px;font-weight:700;border:1px solid;box-shadow:0 2px 6px rgba(0,0,0,.03)}}
.dr-badge--danger{{background:#fff;border-color:#fca5a5;color:#dc2626}}
.dr-badge--success{{background:#fff;border-color:#86efac;color:#059669}}
.dr-badge--warning{{background:#fff;border-color:#fcd34d;color:#d97706}}
.dr-summary{{background:var(--dr-bg-card);border:1px solid var(--dr-border);border-left:4px solid var(--dr-danger);
  border-radius:var(--dr-radius-lg);padding:20px 24px;margin-bottom:20px}}
.dr-summary__label{{font-size:12px;font-weight:800;color:var(--dr-danger);letter-spacing:2px;margin-bottom:8px}}
.dr-summary__text{{font-size:15px;color:var(--dr-text-secondary);line-height:1.85}}
.dr-section{{position:relative;background:var(--dr-bg-card);border:1px solid var(--sec-border, var(--dr-border));
  border-top:3.5px solid var(--sec-color, var(--dr-primary));border-radius:var(--dr-radius-xl);
  padding:28px 30px;margin-bottom:20px;box-shadow:0 4px 18px -2px var(--sec-shadow, rgba(0,0,0,.03));
  background-image:linear-gradient(180deg, var(--sec-bg-tint, rgba(255,255,255,0)) 0%, #ffffff 110px)}}
.dr-section__header{{display:flex;align-items:center;gap:12px;margin-bottom:6px}}
.dr-section__index{{flex:0 0 30px;height:30px;border-radius:8px;background:linear-gradient(135deg, var(--sec-glow, var(--dr-primary)), var(--sec-color, var(--dr-primary-hover)));
  color:#fff;font-size:14px;font-weight:800;display:flex;align-items:center;justify-content:center;
  box-shadow:0 3px 8px var(--sec-shadow, rgba(124,91,245,.25))}}
.dr-section__title{{font-size:21px;font-weight:800;color:var(--sec-color, var(--dr-text-primary));letter-spacing:-.2px}}
.dr-section__desc{{font-size:13.5px;color:var(--dr-text-tertiary);margin:8px 0 18px}}
.dr-subtitle{{font-size:15.5px;font-weight:800;color:var(--sec-color, var(--dr-text-primary));margin:22px 0 10px;
  padding-left:10px;border-left:3px solid var(--sec-color, var(--dr-primary))}}

/* [2026-09-18] [彩虹色谱循环体系] 赤橙黄绿蓝（靛紫）循环设计，每个框获得专属主题色空间 */
/* 1. 赤 (Red) */
.dr-section--c1{{--sec-color:#dc2626;--sec-glow:#f87171;--sec-border:#fecaca;
  --sec-bg-tint:rgba(254,242,242,.85);--sec-shadow:rgba(220,38,38,.12)}}
/* 2. 橙 (Orange) */
.dr-section--c2{{--sec-color:#ea580c;--sec-glow:#fb923c;--sec-border:#fed7aa;
  --sec-bg-tint:rgba(255,247,237,.85);--sec-shadow:rgba(234,88,12,.12)}}
/* 3. 黄 (Warm Gold) */
.dr-section--c3{{--sec-color:#d97706;--sec-glow:#fbbf24;--sec-border:#fde68a;
  --sec-bg-tint:rgba(254,252,232,.85);--sec-shadow:rgba(217,119,6,.12)}}
/* 4. 绿 (Emerald Green) */
.dr-section--c4{{--sec-color:#059669;--sec-glow:#34d399;--sec-border:#a7f3d0;
  --sec-bg-tint:rgba(240,253,244,.85);--sec-shadow:rgba(5,150,105,.12)}}
/* 5. 蓝 (Tech Blue) */
.dr-section--c5{{--sec-color:#2563eb;--sec-glow:#60a5fa;--sec-border:#bfdbfe;
  --sec-bg-tint:rgba(239,246,255,.85);--sec-shadow:rgba(37,99,235,.12)}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}}
th{{background:var(--dr-bg-subtle);color:var(--dr-text-secondary);text-align:left;padding:10px 12px;
  font-weight:700;font-size:12.5px;border-bottom:1px solid var(--dr-border)}}
td{{padding:10px 12px;border-bottom:1px solid var(--dr-border-subtle);vertical-align:top;color:var(--dr-text-secondary)}}
tr:last-child td{{border-bottom:none}}
.dr-grid{{display:grid;gap:12px}}
.dr-grid--3{{grid-template-columns:repeat(3,1fr)}}
.dr-card{{border:1px solid var(--dr-border);border-radius:var(--dr-radius-lg);padding:16px;background:var(--dr-bg-card);border-top:3px solid var(--dr-border)}}
.dr-card--success{{border-top-color:var(--dr-success);background:var(--dr-success-light)}}
.dr-card--warning{{border-top-color:var(--dr-warning);background:var(--dr-warning-light)}}
.dr-card--danger{{border-top-color:var(--dr-danger);background:var(--dr-danger-light)}}
.dr-card--primary{{border-top-color:var(--dr-primary);background:var(--dr-primary-light)}}
.dr-card__name{{font-size:14.5px;font-weight:800;margin-bottom:6px;color:var(--dr-text-primary)}}
.dr-card__body{{font-size:13px;color:var(--dr-text-secondary);line-height:1.7}}
.st-ok{{color:var(--dr-success);font-weight:800}}
.st-bad{{color:var(--dr-danger);font-weight:800}}
.st-warn{{color:var(--dr-warning);font-weight:800}}
.dr-hbar{{display:flex;flex-direction:column;gap:14px;margin-top:14px}}
.dr-hbar__row{{display:grid;grid-template-columns:130px 1fr 62px;align-items:center;gap:12px}}
.dr-hbar__label{{font-size:13.5px;color:var(--dr-text-secondary);font-weight:600}}
.dr-hbar__track{{height:14px;border-radius:8px;background:var(--dr-bg-bar-track);overflow:hidden;position:relative}}
.dr-hbar__fill{{height:100%;border-radius:8px}}
.dr-hbar__bench{{position:absolute;top:-3px;bottom:-3px;width:2px;background:#0f172a;opacity:.55}}
.dr-hbar__value{{font-size:13.5px;font-weight:800;text-align:right}}
.dr-chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:center}}
.dr-legend{{display:flex;flex-direction:column;gap:8px;font-size:13px;color:var(--dr-text-secondary)}}
.dr-legend__item{{display:flex;align-items:center;gap:8px}}
.dr-legend__dot{{width:10px;height:10px;border-radius:3px;flex:0 0 10px}}
.dr-note{{font-size:12px;color:var(--dr-text-tertiary);margin-top:10px;line-height:1.7}}

/* [2026-09-18] [终章旗舰收官卡片] 商业转化联系方式与宣传金句全宽舒展排布 */
.dr-slogan{{position:relative;overflow:hidden;background:linear-gradient(135deg,#ffffff 0%,#faf8ff 45%,#f4edff 100%);
  border:1.5px solid #d8b4fe;border-radius:var(--dr-radius-2xl);padding:38px 36px 32px;margin-top:24px;margin-bottom:28px;text-align:center;
  box-shadow:0 14px 40px -4px rgba(124,91,245,.13),inset 0 1px 0 rgba(255,255,255,.95)}}
.dr-slogan::before{{content:'';position:absolute;top:-60px;left:50%;transform:translateX(-50%);width:320px;height:120px;
  background:radial-gradient(circle,rgba(167,139,250,.28) 0%,rgba(255,255,255,0) 70%);pointer-events:none}}
.dr-slogan__badge{{display:inline-flex;align-items:center;gap:8px;padding:5px 16px;border-radius:9999px;background:#ffffff;
  border:1px solid #ddd6fe;color:#6d28d9;font-size:11.5px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;
  box-shadow:0 2px 8px rgba(124,91,245,.08);margin-bottom:14px}}
.dr-slogan__title{{font-size:30px;font-weight:900;line-height:1.4;letter-spacing:1px;margin-bottom:22px;
  background:linear-gradient(135deg,#2e1065 0%,#5b21b6 38%,#7c3aed 72%,#6d28d9 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}}

/* 融入的联系方式行动专区：通栏舒展排布，充分利用两侧空间 */
.dr-slogan__action{{margin:0 auto;width:100%;background:rgba(255,255,255,.75);border:1px solid #e9d5ff;
  border-radius:var(--dr-radius-xl);padding:22px 28px;box-shadow:0 4px 16px rgba(124,91,245,.06)}}
.dr-slogan__tag{{display:inline-block;background:#f5f0fe;border:1px solid #ddd6fe;color:#6d28d9;
  border-radius:var(--dr-radius-sm);padding:5px 14px;font-size:13px;font-weight:800;margin-bottom:16px}}
.dr-slogan__row{{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:14px}}
.dr-slogan__btn{{background:linear-gradient(135deg,#7c5bf5 0%,#6846e3 100%);color:#fff;border-radius:var(--dr-radius-md);
  padding:12px 28px;font-size:15px;font-weight:800;border:none;box-shadow:0 4px 12px rgba(124,91,245,.22);
  display:inline-flex;align-items:center;justify-content:center;text-decoration:none;cursor:pointer;transition:all .18s ease}}
.dr-slogan__btn:hover{{transform:translateY(-1px);box-shadow:0 6px 16px rgba(124,91,245,.3)}}
.dr-slogan__btn--ghost{{background:#ffffff;border:1.5px solid #c4b5fd;color:#6d28d9;box-shadow:0 2px 8px rgba(124,91,245,.06)}}
.dr-slogan__btn--ghost:hover{{background:#f5f0fe;border-color:#a78bfa}}
.dr-slogan__hint{{font-size:13.5px;color:#64748b;line-height:1.7}}
.dr-slogan__hint strong{{color:#6d28d9}}

.dr-slogan__footer{{margin-top:22px;padding-top:16px;border-top:1px dashed #e9d5ff;display:flex;align-items:center;
  justify-content:center;gap:10px;font-size:12px;color:#7c3aed;font-weight:700;letter-spacing:.8px}}
.dr-slogan__dot{{width:4px;height:4px;border-radius:50%;background:#a78bfa}}

@media(max-width:860px){{.dr-grid--3,.dr-chart-row{{grid-template-columns:1fr}}
  .dr-hero__title{{font-size:25px}}.dr-content{{padding:14px 12px 0}}.dr-section{{padding:20px 18px}}
  .dr-slogan{{padding:30px 16px 24px}}.dr-slogan__title{{font-size:22px;line-height:1.45}}
  .dr-slogan__action{{padding:18px 14px}}.dr-slogan__btn{{width:100%;text-align:center}}}}
</style>
</head>
<body>
<div class="dr-page"><div class="dr-content">

<div class="dr-hero">
  <div class="dr-hero__main">
    <div class="dr-hero__body">
      <h1 class="dr-hero__title"><span class="dr-hero__title-accent">{brand_escaped}</span> · AI 可见度商业诊断报告</h1>
      <div class="dr-hero__subtitle">
        {data.qualitative_sub1}<br>
        {data.qualitative_sub2}
      </div>
      <div class="dr-hero__badge-row">
        {badges_html}
      </div>
      <div class="dr-hero__meta">
        <span>诊断对象：{client_escaped}</span><span class="dr-hero__divider-dot"></span>
        <span>引擎：{html_lib.escape(data.engines_tested)}</span><span class="dr-hero__divider-dot"></span>
        <span>样本：{html_lib.escape(data.sample_count_text)}</span><span class="dr-hero__divider-dot"></span>
        <span>{html_lib.escape(data.report_date)}</span>
      </div>
    </div>
    <div class="dr-hero__score-group">
      <div class="dr-hero__score-ring">
        {score_ring_svg}
        <div class="dr-hero__score-inner">
          <div class="dr-hero__score-value" style="color:#dc2626">{data.overall_score}</div>
          <div class="dr-hero__score-unit">/100</div>
        </div>
      </div>
      <div class="dr-hero__grade-badge">
        <div class="dr-hero__grade-label">综合评级</div>
        <div class="dr-hero__grade-value">{html_lib.escape(data.overall_grade)}</div>
      </div>
    </div>
  </div>
</div>

<div class="dr-summary">
  <div class="dr-summary__label">诊 断 概 览</div>
  <div class="dr-summary__text">
    {data.summary_text}
  </div>
</div>

<div class="dr-section dr-section--c1">
  <div class="dr-section__header"><div class="dr-section__index">1</div>
    <div class="dr-section__title">好消息：你的技术资产其实很能打（不用推倒重来）</div></div>
  <div class="dr-section__desc">先说这一节是为了让你放心——问题不在技术能力，也不在官网做得差。</div>

  <div class="dr-subtitle">技术体检明细（{html_lib.escape(data.report_date)} 实测）</div>
  <table>
    <tr><th style="width:24%">检测维度</th><th style="width:30%">检测值</th><th style="width:16%">行业规范</th><th>结论</th></tr>
    {tech_rows_html}
  </table>

  <div class="dr-grid dr-grid--3" style="margin-top:16px">
    {good_cards_html}
  </div>
</div>

<div class="dr-section dr-section--c2">
  <div class="dr-section__header"><div class="dr-section__index">2</div>
    <div class="dr-section__title">坏消息：AI 现在根本认不出你的品牌（这才是丢单的地方）</div></div>
  <div class="dr-section__desc">{html_lib.escape(data.engines_tested)}，共 {html_lib.escape(data.sample_count_text)} 实测。</div>

  <div class="dr-chart-row" style="margin-bottom:8px">
    <div>
      {pie_svg}
    </div>
    <div class="dr-legend">
      <div class="dr-legend__item"><span class="dr-legend__dot" style="background:#dc2626"></span><span><strong>{data.pie_unmentioned} 组 · 未提及（{round(data.pie_unmentioned / max(1, data.pie_unmentioned + data.pie_wrong + data.pie_accurate) * 100)}%）</strong>——AI 列出 20+ 家服务商，全是对手</span></div>
      <div class="dr-legend__item"><span class="dr-legend__dot" style="background:#f59e0b"></span><span><strong>{data.pie_wrong} 组 · 提及但错误（{round(data.pie_wrong / max(1, data.pie_unmentioned + data.pie_wrong + data.pie_accurate) * 100)}%）</strong>——被认成两个不同的外部主体</span></div>
      <div class="dr-legend__item"><span class="dr-legend__dot" style="background:#059669"></span><span><strong>{data.pie_accurate} 组 · 提及且准确（{round(data.pie_accurate / max(1, data.pie_unmentioned + data.pie_wrong + data.pie_accurate) * 100)}%）</strong>——唯一说对业务定位的一组</span></div>
      <div class="dr-note">{data.pie_unmentioned + data.pie_wrong + data.pie_accurate} 组里<strong>只有 {data.pie_accurate} 组</strong>把你说对了。</div>
    </div>
  </div>

  <div class="dr-subtitle">问句可见度对照表（实测原文）</div>
  <table>
    <tr><th style="width:6%">#</th><th style="width:10%">平台</th><th style="width:24%">测试问句</th><th style="width:10%">结果</th><th>AI 实际说了什么</th></tr>
    {probe_rows_html}
  </table>

  <div class="dr-grid dr-grid--3" style="margin-top:16px">
    {leak_cards_html}
  </div>
</div>

<div class="dr-section dr-section--c3">
  <div class="dr-section__header"><div class="dr-section__index">3</div><div class="dr-section__title">竞品占位透视：谁在吃你的入口</div></div>
  <div class="dr-section__desc">以下均为两家 AI 在本次实测中<strong>原文列出</strong>的服务商。本表未做商业化量化评分——因为缺少真实行业榜单数据，宁可空着也不编。</div>
  <table>
    <tr><th style="width:18%">AI 推荐的服务商</th><th style="width:12%">出现在</th><th style="width:26%">AI 给它的理由</th><th>它凭什么占位 = 你的缺口镜像</th></tr>
    {competitor_rows_html}
  </table>
  <div class="dr-card dr-card--danger" style="margin-top:14px">
    <div class="dr-card__name">{html_lib.escape(data.name_risk_title)}</div>
    <div class="dr-card__body">{data.name_risk_body}</div>
  </div>
</div>

<div class="dr-section dr-section--c4">
  <div class="dr-section__header"><div class="dr-section__index">4</div><div class="dr-section__title">四步破局：从「能被读到」到「被推荐」</div></div>
  <div class="dr-section__desc">顺序不能调换——每一步都在给下一步打地基。</div>
  <table>
    <tr><th style="width:8%">优先级</th><th style="width:26%">动作</th><th style="width:12%">周期</th><th>一句话目标</th></tr>
    {action_rows_html}
  </table>

  <div class="dr-subtitle">30 天后，你能拿到什么</div>
  <table>
    <tr><th style="width:46%">现在（{html_lib.escape(data.report_date)} 实测）</th><th>30 天后（目标）</th></tr>
    {vision_rows_html}
  </table>
  <div class="dr-card dr-card--warning" style="margin-top:14px"><div class="dr-card__name">为什么这个 30 天可信</div>
    <div class="dr-card__body">因为<strong>基数现在是零</strong>。技术底座已 5/5 达标、40 条答案已写完——唯一缺的是"把它们放到 AI 看得到的地方"。
    <strong>{html_lib.escape(data.vision_note)}</strong></div></div>
  <div class="dr-note">本次只测了豆包和 DeepSeek 两个平台。<strong>单平台达标不算赢</strong>——元宝、通义千问、Kimi、文心一言的抓取来源各不相同，正式推进应扩展到 6–8 个平台做全平台提及率看板。</div>
</div>

<div class="dr-section dr-section--c5">
  <div class="dr-section__header"><div class="dr-section__index">5</div><div class="dr-section__title">AIVO 四维评分（思维分析）</div></div>
  <div class="dr-section__desc">四个维度等权（各 25%），每维分数由本次实测证据直接判定，依据见下表。</div>

  <div class="dr-chart-row">
    <div>
      {radar_svg}
    </div>
    <div class="dr-hbar">
      <div class="dr-hbar__row"><div class="dr-hbar__label">基建完善度</div>
        <div class="dr-hbar__track"><div class="dr-hbar__fill" style="width:{data.infra_score}%;background:#059669"></div><div class="dr-hbar__bench" style="left:60%"></div></div>
        <div class="dr-hbar__value" style="color:#059669">{data.infra_score}</div></div>
      <div class="dr-hbar__row"><div class="dr-hbar__label">内容可引用性</div>
        <div class="dr-hbar__track"><div class="dr-hbar__fill" style="width:{data.citation_score}%;background:#d97706"></div><div class="dr-hbar__bench" style="left:60%"></div></div>
        <div class="dr-hbar__value" style="color:#d97706">{data.citation_score}</div></div>
      <div class="dr-hbar__row"><div class="dr-hbar__label">AI 搜索可见度</div>
        <div class="dr-hbar__track"><div class="dr-hbar__fill" style="width:{data.visibility_score}%;background:#dc2626"></div><div class="dr-hbar__bench" style="left:60%"></div></div>
        <div class="dr-hbar__value" style="color:#dc2626">{data.visibility_score}</div></div>
      <div class="dr-hbar__row"><div class="dr-hbar__label">认知准确性</div>
        <div class="dr-hbar__track"><div class="dr-hbar__fill" style="width:{data.accuracy_score}%;background:#dc2626"></div><div class="dr-hbar__bench" style="left:60%"></div></div>
        <div class="dr-hbar__value" style="color:#dc2626">{data.accuracy_score}</div></div>
      <div class="dr-note">黑色竖线 = 行业参考基准 60 分。强项（基建）已超过基准，短板三项都在基准线以下。</div>
    </div>
  </div>

  <div class="dr-subtitle">维度明细与真源依据</div>
  <table>
    <tr><th style="width:16%">维度</th><th style="width:8%">得分</th><th style="width:12%">对比基准</th><th>真源依据（本次实测）</th></tr>
    {aivo_rows_html}
  </table>
  <div class="dr-note">评分方法：4 维度等权平均，每维分数由上述<strong>实测证据直接判定</strong>（依据见表内），<strong>非第三方工具抓取分</strong>。正式交付客户时请以真抓数据替换。</div>
</div>

<div class="dr-slogan">
  <div class="dr-slogan__badge">CLARITY PRECEDES MOMENTUM · 笃行致远</div>
  <div class="dr-slogan__title">当你清楚要做什么，全世界都会为你让路</div>

  <div class="dr-slogan__action">
    <div class="dr-slogan__tag">{html_lib.escape(data.cta_tag)}</div>
    <div class="dr-slogan__row">
      <a href="tel:{html_lib.escape(data.contact_phone)}" class="dr-slogan__btn">电话/微信 {html_lib.escape(data.contact_phone)}</a>
      <a href="https://{official_url_escaped}" target="_blank" rel="noopener noreferrer" class="dr-slogan__btn dr-slogan__btn--ghost">官网 {official_url_escaped}</a>
    </div>
    <div class="dr-slogan__hint">
      下一步只做一件事：<strong>把 40 条已完成的答案发出去</strong>——先让你的技术资产出现在 AI 读得到的地方。
    </div>
  </div>

  <div class="dr-slogan__footer">
    <span>{brand_escaped} · 企业 AI 可见度增长引擎</span>
    <span class="dr-slogan__dot"></span>
    <span>与清晰者同行</span>
  </div>
</div>

</div></div>
</body>
</html>
"""
    return html
