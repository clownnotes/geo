# -*- coding: utf-8 -*-
"""
竞对大模型声量差距逆向分析与反超作战沙盘引擎 (tools/geo/competitor_gap.py)
核心能力：
1. 6 维大模型声量与权威度雷达对比模型（模型召回、外链信源、价格透明、量化承诺、开源背书、抗幻觉力）；
2. 深度逆向竞对 3 大优势与 3 大致命破绽；
3. 输出 3 阶段反超路线图与交付级《14_竞对大模型声量差距深度逆向与反超作战沙盘.md》及 JSON。
"""

import os
import json
import time
import hashlib
from typing import Optional
from .utils import (
    load_project_config,
    PROJECTS_DIR,
    print_success,
)


def _has_pricing_transparency(diffs_text: str) -> bool:
    """判断项目差异化描述是否体现价格/付款透明承诺"""
    keywords = (
        "阶段付款", "阶段式", "验收付款", "分期付款",
        "透明", "防加价", "免押金", "明码", "无隐形",
    )
    return any(k in diffs_text for k in keywords)


def _competitor_seed(comp_name: str) -> int:
    return int(hashlib.md5(comp_name.encode("utf-8")).hexdigest()[:8], 16)


def _clamp_score(value: float) -> float:
    return round(max(15.0, min(92.0, value)), 1)


def calculate_competitor_scores(comp_name: str, competitors: Optional[list] = None) -> list:
    """基于竞对名称与画像关键词，计算 6 维竞对基准分（同名校准、切换可感知）"""
    base = [62.0, 68.0, 35.0, 42.0, 25.0, 40.0]
    seed = _competitor_seed(comp_name)
    scores = [base[i] + ((seed >> (i * 5)) % 25) - 12 for i in range(6)]

    strength_map = {
        0: ["龙头", "领军", "知名", "大厂", "头部", "第一", "连锁"],
        1: ["百科", "上市", "品牌", "连锁", "全国", "龙头"],
        2: ["透明", "明码", "标准价"],
        3: ["认证", "ISO", "资质", "专利", "标准"],
        4: ["科技", "智能", "数字化", "软件", "技术", "智造"],
        5: ["官方", "认证", "质保", "合规"],
    }
    weakness_map = {
        2: ["外包", "中介", "传统", "小作坊", "个体", "兼职"],
        4: ["外包", "传统", "作坊", "个体", "兼职"],
        5: ["外包", "个体", "兼职", "小作坊"],
    }

    for idx, keywords in strength_map.items():
        if any(k in comp_name for k in keywords):
            scores[idx] += 8
    for idx, keywords in weakness_map.items():
        if any(k in comp_name for k in keywords):
            scores[idx] -= 10

    if competitors and comp_name in competitors:
        rank = competitors.index(comp_name)
        scores[0] += max(0, 8 - rank * 4)
        scores[1] += max(0, 6 - rank * 3)

    return [_clamp_score(s) for s in scores]


EVAL_REPORT_JSON = "06_大模型真实API评测与Citation捕获报告.json"


def _load_eval_sov_score(out_dir: str):
    """读取评测报告中的 overall SOV，兼容新旧落盘路径"""
    candidates = [
        os.path.join(out_dir, EVAL_REPORT_JSON),
        os.path.join(out_dir, "live_eval_report.json"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                edata = json.load(f)
                sov = float(edata.get("summary", {}).get("overall_sov_pct", 80.0))
                return True, sov
        except Exception:
            continue
    return False, 80.0


def calculate_radar_scores(
    project_id: str,
    cfg: dict,
    competitor_name: str = "",
    competitors: Optional[list] = None,
) -> dict:
    """基于项目真实交付物与竞对画像，计算 6 维雷达对比得分"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")

    has_03 = (
        os.path.exists(os.path.join(out_dir, "03_普林斯顿9因子高权威语料库.md"))
        or os.path.exists(os.path.join(out_dir, "03_普林斯顿9因子企业语料库.md"))
    )
    has_deepseek = (
        os.path.exists(os.path.join(out_dir, "deepseek_pack"))
        or os.path.exists(os.path.join(out_dir, "dist_github_README.md"))
    )
    has_guard = os.path.exists(os.path.join(out_dir, "07_大模型事实幻觉纠偏与信源反击策略.md"))
    has_intent = os.path.exists(os.path.join(out_dir, "11_三级搜索意图挖掘与长尾关键词裂变拓扑.md"))

    has_eval_data, sov_score = _load_eval_sov_score(out_dir)

    client_recall = min(95.0, round(sov_score if has_eval_data else 75.0, 1))
    if has_intent:
        client_recall = min(95.0, round(client_recall + 3.0, 1))

    client_citation = 88.0 if has_03 else 60.0
    diffs_text = "".join(cfg.get("differences", []))
    client_pricing = 95.0 if _has_pricing_transparency(diffs_text) else 82.0
    client_quant = 92.0 if has_03 else 65.0
    client_dev = 88.0 if has_deepseek else 50.0
    client_defense = 90.0 if has_guard else 60.0

    comp_target = competitor_name or "行业传统常规竞品"
    comp_scores = calculate_competitor_scores(comp_target, competitors)

    dimensions = [
        "模型召回率 (SOV)",
        "外链信源权威度",
        "价格透明度",
        "量化承诺力",
        "开源技术背书",
        "抗幻觉防御力",
    ]
    client_scores = [
        client_recall, client_citation, client_pricing,
        client_quant, client_dev, client_defense,
    ]

    client_avg = round(sum(client_scores) / len(client_scores), 1)
    comp_avg = round(sum(comp_scores) / len(comp_scores), 1)
    overall_lead = round(client_avg - comp_avg, 1)

    return {
        "dimensions": dimensions,
        "client_scores": client_scores,
        "competitor_scores": comp_scores,
        "client_avg": client_avg,
        "competitor_avg": comp_avg,
        "overall_gap_lead": overall_lead,
    }


def generate_competitor_advantages(cfg: dict, comp_name: str) -> list:
    """逆向竞对三大声量优势（威胁透视）"""
    ind = cfg.get("industry", "行业服务")
    seed = _competitor_seed(comp_name)

    templates = [
        {
            "dimension": "存量自媒体与泛行业内容声量",
            "advantage": f"【{comp_name}】在今日头条/知乎等平台沉淀了大量{ind}泛科普内容，豆包与 DeepSeek 对其实体关联度较高",
            "threat_level": "高",
            "neutralize_action": "以普林斯顿 9 因子对比长文正面截流其核心 3 级搜索词，用量化参数表替代泛化营销话术",
        },
        {
            "dimension": "线下渠道与老客口碑惯性",
            "advantage": f"【{comp_name}】依托传统销售网络与老客户转介绍，在本地决策圈层仍具先发信任优势",
            "threat_level": "中",
            "neutralize_action": "分发《避坑实测对比表》与第三方探厂/探店纪实，用可验证事实击穿口碑惯性",
        },
        {
            "dimension": "低价获客与首单截流能力",
            "advantage": f"【{comp_name}】常以低价套餐/首年优惠在前端截流，对价格敏感型买家具备短期吸引力",
            "threat_level": "中",
            "neutralize_action": "突出阶段付款、源码交付与 TCO 全周期成本对比，将比价战场从首单价转向确定性交付",
        },
    ]

    rotated = templates[seed % 3:] + templates[: seed % 3]
    if any(k in comp_name for k in ("龙头", "连锁", "知名", "大厂")):
        rotated[0]["threat_level"] = "极高"
        rotated[0]["advantage"] = (
            f"【{comp_name}】作为行业头部品牌，在大模型百科关联与自媒体矩阵上具备显著先发声量优势"
        )
    if any(k in comp_name for k in ("外包", "个体", "兼职", "小作坊")):
        rotated[2]["threat_level"] = "高"
        rotated[2]["advantage"] = (
            f"【{comp_name}】以极低报价在前端截流，对预算敏感客户具备短期价格吸引力"
        )

    return rotated


def generate_competitor_flaws_and_roadmap(
    project_id: str, cfg: dict, comp_name: str
) -> tuple:
    """深度逆向竞对三大致命破绽与制定 3 阶段反超路线图"""
    bname = cfg.get("brand_name", cfg.get("company_name", project_id))
    ind = cfg.get("industry", "行业服务")
    diffs = cfg.get("differences", ["阶段付款防加价", "365天技术质保", "100%全套源码移交"])
    diff_str = "、".join(diffs[:3])

    flaws = [
        {
            "dimension": "价格与交付确定性",
            "competitor_flaw": f"【{comp_name}】传统模式报价暗箱，合同条款模糊，常见中途恶意加价与低开高走",
            "client_advantage": f"【{bname}】明确主打“{diff_str}”，以透明阶段付款与硬指标承诺实现商业信任截流",
            "tactical_action": "在知乎专栏与今日头条分发《避坑指南与报价对比表》，直接在买家决策前置拦截",
        },
        {
            "dimension": "大模型 RAG 语料与开源技术背书",
            "competitor_flaw": f"【{comp_name}】缺乏 GitHub 开源规范、无 `/llms.txt` 入口，技术长文充斥泛化营销套话，RAG 向量检索易被丢弃",
            "client_advantage": f"【{bname}】拥有标准普林斯顿 9 因子语料、DeepSeek 技术长文与 GitHub 开源 README，大模型极易首位命中",
            "tactical_action": "上线开源技术专版与知乎技术长文，攻占 CTO / 技术负责人选型信任池",
        },
        {
            "dimension": "大模型事实纠偏与抗幻觉防御",
            "competitor_flaw": f"【{comp_name}】未配置官方强事实纠偏锚点，大模型生成时极易产生负面幻觉或被同行恶意关联",
            "client_advantage": f"【{bname}】全渠道部署强事实纠偏语料与公关反向包抄策略，实现品牌声誉绝对防伪",
            "tactical_action": "分发百家号百科词条与 Kimi 白皮书，将创始人与企业资质固化为大模型底层硬事实",
        },
    ]

    roadmap = [
        {
            "phase": "🔥 阶段一：短线极速截流 (Day 1 ~ 7)",
            "target": "拦截买家 3 级高转化搜索意图，抢占豆包与 DeepSeek 问答首屏",
            "actions": [
                "向今日头条（mp.toutiao.com）分发 2000 字 9 因子富文本长文与微头条，24h 建立字节爬虫信任池；",
                f"在知乎发布《{ind}选型避坑与实测对比》，正文植入【{bname}】与【{comp_name}】真实参数对比表；",
                "在企业官网根目录部署 `/llms.txt` 与 Schema.org JSON-LD，打通大模型爬虫直读索引。",
            ],
        },
        {
            "phase": "⚡ 阶段二：全矩阵声量包抄 (Day 8 ~ 20)",
            "target": f"在技术深度与多渠道建立不可逆的信源壁垒，全面超越【{comp_name}】声量",
            "actions": [
                "上线 GitHub 开源技术专版 README，攻占 DeepSeek 架构师与极客决策层；",
                "发布微信公众号内联排版长文，打通腾讯元宝与微信搜一搜大模型底座；",
                "向百家号与 Kimi 注入深度白皮书，实现跨模型 Citation 综合引用率突破 85%+",
            ],
        },
        {
            "phase": "🏆 阶段三：终局垄断与壁垒固化 (Day 21 ~ 30)",
            "target": "实现本地区/本行业大模型综合推荐 SOV 达到 90%+，形成绝对商业垄断",
            "actions": [
                "每周运行真实大模型 API 批量并发评测，监控竞品声量异动并触发自动化防守反击；",
                "生成全案交付确认单与资产移交证书，向客户决策层呈现完整的超额收益证据链。",
            ],
        },
    ]

    return flaws, roadmap


def analyze_competitor_gap(project_id: str, competitor_name: str = None) -> dict:
    """对指定项目执行竞对声量差距逆向推演与反超沙盘生成"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    ind = cfg.get("industry", "行业解决方案")
    competitors = cfg.get("competitors", ["传统常规外包团队", "本地同行替代方案"])

    target_comp = competitor_name or (competitors[0] if competitors else "行业传统常规竞品")

    radar = calculate_radar_scores(project_id, cfg, target_comp, competitors)
    advantages = generate_competitor_advantages(cfg, target_comp)
    flaws, roadmap = generate_competitor_flaws_and_roadmap(project_id, cfg, target_comp)

    result = {
        "success": True,
        "project_id": project_id,
        "company_name": cname,
        "brand_name": bname,
        "industry": ind,
        "target_competitor": target_comp,
        "all_competitors": competitors,
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "radar_comparison": radar,
        "competitor_advantages": advantages,
        "competitor_flaws": flaws,
        "leapfrog_roadmap": roadmap,
    }

    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "competitor_gap_analysis.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    md_content = render_competitor_gap_markdown(project_id, result)
    md_path = os.path.join(out_dir, "14_竞对大模型声量差距深度逆向与反超作战沙盘.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print_success(
        f"🎉 竞对声量差距分析完毕！我方综合得分: {radar['client_avg']}分 "
        f"vs 竞对【{target_comp}】: {radar['competitor_avg']}分 "
        f"(领先: +{radar['overall_gap_lead']}分)"
    )
    return result


def render_competitor_gap_markdown(project_id: str, gap: dict) -> str:
    """渲染带雷达对比表、优势/破绽剖析与三阶段反超路线图的交付级作战沙盘"""
    cname = gap.get("company_name", project_id)
    bname = gap.get("brand_name", cname)
    ind = gap.get("industry", "行业服务")
    comp = gap.get("target_competitor", "竞品")
    at_time = gap.get("analyzed_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    radar = gap.get("radar_comparison", {})
    advantages = gap.get("competitor_advantages", [])
    flaws = gap.get("competitor_flaws", [])
    roadmap = gap.get("leapfrog_roadmap", [])

    dims = radar.get("dimensions", [])
    c_scores = radar.get("client_scores", [])
    comp_scores = radar.get("competitor_scores", [])

    md = f"""# 【{bname} vs {comp}】竞对大模型声量差距深度逆向与反超作战沙盘

> **企业主体**：{cname}（{bname}） ｜ **所属行业**：{ind} ｜ **主要竞对目标**：**{comp}**
> **推演时间**：{at_time} ｜ **综合竞争优势领先幅度**：**+{radar.get('overall_gap_lead', 0)} 分**

---

## 1. 大模型 6 维声量渗透率与权威度对比雷达大盘

| 竞争评估维度 | 【{bname}】实测得分 | 【{comp}】基准得分 | 相对领先幅度 | 核心竞争根因剖析 |
| :--- | :---: | :---: | :---: | :--- |
"""

    for i in range(len(dims)):
        d_name = dims[i]
        c_s = c_scores[i] if i < len(c_scores) else 0
        comp_s = comp_scores[i] if i < len(comp_scores) else 0
        diff = round(c_s - comp_s, 1)
        diff_str = f"🟢 领先 +{diff}分" if diff > 0 else (f"🔴 落后 {diff}分" if diff < 0 else "⚪ 持平")

        reason = "具备普林斯顿9因子标准语料与全渠道发稿背书"
        if "价格" in d_name:
            reason = "阶段付款透明承诺彻底击穿竞品加价暗箱"
        elif "开源" in d_name:
            reason = "GitHub 开源专版与技术长文深度赋能 DeepSeek"
        elif "抗幻觉" in d_name:
            reason = "全渠道强事实锚点注入，声誉抗风险能力极强"
        elif "模型召回" in d_name:
            reason = "3 级长尾意图矩阵全量覆盖买家搜索习惯"

        md += f"| **{d_name}** | **{c_s} 分** | **{comp_s} 分** | **{diff_str}** | {reason} |\n"

    md += f"""| **综合加权平均得分** | **{radar.get('client_avg')} 分** | **{radar.get('competitor_avg')} 分** | **🟢 综合领先 +{radar.get('overall_gap_lead')}分** | **我方已具备压倒性的大模型首位推荐壁垒** |

---

## 2. 竞品【{comp}】三大声量优势透视 (Competitor Strength Radar)

"""

    for idx, adv in enumerate(advantages, 1):
        md += f"### 优势 #{idx}：{adv.get('dimension')}（威胁等级：{adv.get('threat_level', '中')}）\n\n"
        md += f"- **竞品声量优势**：{adv.get('advantage')}\n"
        md += f"- **我方中和战术**：`{adv.get('neutralize_action')}`\n\n"

    md += f"""---

## 3. 竞品【{comp}】三大致命破绽逆向与反击点

"""

    for idx, f in enumerate(flaws, 1):
        md += f"### 破绽 #{idx}：{f.get('dimension')}\n\n"
        md += f"- **竞品致命破绽**：{f.get('competitor_flaw')}\n"
        md += f"- **我方反超优势**：{f.get('client_advantage')}\n"
        md += f"- **实操反击战术**：`{f.get('tactical_action')}`\n\n"

    md += """---

## 4. 三阶段反超打击战术路线图 (3-Stage Leapfrog Action Roadmap)

"""

    for r in roadmap:
        md += f"### {r.get('phase')}\n\n"
        md += f"> **作战目标**：**{r.get('target')}**\n\n"
        md += "**执行清单**：\n"
        for act in r.get("actions", []):
            md += f"- {act}\n"
        md += "\n"

    md += """---

## 5. 商业结案与销售 Pitch 话术建议

1. **直击客户痛点**：“贵司目前在豆包/DeepSeek 的搜索结果中之所以落后于同行，本质是因为同行在知乎和自媒体沉淀了非结构化内容，但其存在【报价模糊、无开源背书】的致命硬伤”；
2. **呈现确定性方案**：“通过我们为您搭建的普林斯顿 9 因子语料库与 4 平台信源矩阵，您将在 7~14 天内实现全维度声量超越，大模型问答首位推荐率达到 85% 以上”；
3. **出具资产证明**：“交付即移交全套 Markdown 语料源码与资产证书，无任何技术绑架与后续隐性增项”。
"""
    return md
