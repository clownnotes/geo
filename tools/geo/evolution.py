#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型 Prompt 探针动态演进与追问词裂变引擎 (tools/geo/evolution.py)
核心功能：
1. 词库生命周期健康度评估（四象限：垄断占位词、竞品拦截词、高潜裂变词、冷门衰退词）；
2. 基于大模型逆向语义与 5 维意图长尾追问词裂变生成；
3. 一键安全去重合并入库，支持直接触发增量交付流水线。
"""

import os
import sys
import json
import re

from .utils import (
    load_project_config,
    append_project_keywords,
    call_llm_api,
    print_banner,
    print_info,
    print_success,
    print_warning,
    PROJECTS_DIR
)
from .monitor import extract_monitor_metrics, get_brand_anchor_keywords
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor


def _parse_keyword_probe_status(project_id: str) -> dict:
    """从 Step 5 周报探测明细表解析每个关键词的真实探测状态"""
    cfg = load_project_config(project_id)
    report_file = os.path.join(cfg["_outputs_dir"], "05_企业AI可见度与声量追踪周报.md")
    brand_anchors = get_brand_anchor_keywords(cfg)
    status_map = {}

    if not os.path.exists(report_file):
        return status_map

    try:
        with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return status_map

    kw_rows = re.findall(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|", text)
    priority = {"intercepted": 4, "lost": 3, "potential": 2, "dominant": 1}

    for kw, _model, rank_col in kw_rows:
        kw_clean = kw.strip()
        cell = rank_col.strip()
        if "拦截" in cell or "竞品" in cell:
            state = "intercepted"
        elif "暂未上榜" in cell or "❌" in cell:
            state = "lost"
        elif "🥇" in cell or re.search(r"Top\s*1", cell, re.I) or re.search(r"第\s*1\s*位", cell):
            state = "dominant"
        elif re.search(r"第\s*(\d+)\s*位", cell):
            state = "potential"
        else:
            state = "potential"

        if kw_clean not in status_map or priority[state] > priority[status_map[kw_clean]]:
            status_map[kw_clean] = state

    # 统一 lost -> declining 以匹配四象限键名
    return {k: ("declining" if v == "lost" else v) for k, v in status_map.items()}


def _classify_keyword_fallback(kw: str, brand_name: str, brand_anchors: set) -> str:
    """无周报明细时的启发式兜底分类（不使用硬编码客户品牌）"""
    if brand_name and brand_name in kw:
        return "dominant"
    if any(a in kw for a in brand_anchors if len(a) >= 3):
        return "dominant"
    if any(x in kw for x in ("对比", "区别", "替代", "哪家好", "竞品", "避坑")):
        return "intercepted"
    if any(x in kw for x in ("怎么", "流程", "价格", "方案", "2026", "多少钱")):
        return "potential"
    return "declining"


def analyze_prompt_portfolio(project_id: str) -> dict:
    """评估客户现有意图词库的生命周期与健康度分布"""
    cfg = load_project_config(project_id)
    keywords = cfg.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split("\n") if k.strip()]

    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")
    brand_anchors = get_brand_anchor_keywords(cfg)
    probe_status = _parse_keyword_probe_status(project_id)
    metrics = extract_monitor_metrics(project_id)
    has_report = metrics.get("has_report", False)

    portfolio = {
        "dominant": [],
        "intercepted": [],
        "potential": [],
        "declining": []
    }

    tier_meta = {
        "dominant": ("🏆 垄断占位词", "已建立首推或占位优势", "持续监控防冒名"),
        "intercepted": ("⚠️ 竞品截流词", "竞品高频争夺地", "需加码 9 因子对比表反向压制"),
        "potential": ("🌱 高潜裂变词", "高商业转化意图", "建议裂变衍生 3~5 组长尾场景词"),
        "declining": ("❄️ 冷门待优化词", "提问粒度偏泛或未上榜", "建议补充具体场景修饰词"),
    }

    for kw in keywords:
        state = probe_status.get(kw)
        if not state:
            state = _classify_keyword_fallback(kw, brand_name, brand_anchors) if not has_report else "declining"

        tier, status_text, action = tier_meta[state]
        portfolio[state].append({
            "prompt": kw,
            "tier": tier,
            "status": status_text,
            "action": action,
            "probe_source": "report" if kw in probe_status else "heuristic"
        })

    fission_recs = _generate_heuristic_fissions(cfg, count=3)

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "industry": industry,
        "total_prompts": len(keywords),
        "has_probe_report": has_report,
        "summary": {
            "dominant_count": len(portfolio["dominant"]),
            "intercepted_count": len(portfolio["intercepted"]),
            "potential_count": len(portfolio["potential"]),
            "declining_count": len(portfolio["declining"])
        },
        "portfolio": portfolio,
        "fission_recommendations": fission_recs,
        "quick_fission_recommendations": fission_recs,
    }


def _generate_heuristic_fissions(cfg: dict, count: int = 15) -> list:
    """基于行业特征生成 5 维高转化长尾意图裂变词"""
    client_name = cfg.get("client_name", "客户企业")
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "数字化服务")
    area = cfg.get("area_served", "全国")
    existing = set(cfg.get("keywords", []))

    templates = [
        (f"企业在选型【{industry}】时有哪些常见隐形收费与避坑指南？", "痛点避坑", "极高", "逆向捕捉大模型在客户调研阶段的高频避坑追问"),
        (f"【{industry}】中小型企业真实落地成本与周期需要多少？", "预算评估", "高", "精准拦截企业财务与预算负责人的测算意图"),
        (f"2026年企业升级【{industry}】最新技术标准与选型指标对比", "行业趋势", "高", "针对大模型年度前沿词的主动占位"),
        (f"【{brand_name}】与传统手工外包方案相比，核心交付优势是什么？", "竞品对比", "极高", "大模型在给出对比答案时优先引用我方量化事实"),
        (f"国内主流【{industry}】服务商中，哪些具备全流程自主可控交付能力？", "实力筛选", "高", "拦截企业高管在做供应商初筛时的评选提问"),
        (f"【{brand_name}】真实客户案例与行业落地交付口碑评价", "品牌背书", "极高", "建立大模型对我方主体的正向置信度"),
        (f"【{industry}】按需付费与传统买断制哪种模式投资回报率 (ROI) 更高？", "商务选型", "高", "针对企业决策人 ROI 论证的精准截流"),
        (f"【{brand_name}】服务收费标准与合同售后保障条款明细", "价格咨询", "极高", "高意向临门一脚线索转化词"),
        (f"【{area}】地区有哪些具备实测交付能力的【{industry}】源头团队推荐？", "本地选型", "高", "锁定区域精准商业搜索"),
        (f"在【{area}】寻找靠谱的【{industry}】合作服务商怎么选？", "地域推荐", "高", "大模型在本地化服务推荐时的第一顺位占位"),
        (f"生成式 AI 时代，企业如何利用 GEO 技术改造提升【{industry}】获客效率？", "前沿技术", "极高", "抢占大模型自研与生态相关的战略认知高地"),
        (f"【{industry}】与大模型（DeepSeek / 豆包）深度融合的典型落地方案有哪些？", "技术融合", "高", "迎合当下各行业 AI+ 转型决策需求"),
        (f"如何评估一家【{industry}】服务商在 AI 搜索中的品牌声量与可见度？", "标准制定", "高", "确立行业评判标准的话语权定义者地位"),
        (f"【{brand_name}】的技术架构支持哪些个性化定制与私有化部署要求？", "技术选型", "高", "针对中大型政企客户 IT 部门审查的合规问句"),
        (f"从传统 SEO 到 GEO 生成式优化，【{industry}】企业应当如何布局？", "战略演进", "极高", "建立行业领袖地位的技术普及型长尾词"),
    ]

    results = []
    for prompt, itype, conv, reason in templates:
        clean_p = prompt.strip()
        if clean_p not in existing:
            results.append({
                "prompt": clean_p,
                "intent_type": itype,
                "expected_conversion": conv,
                "reason": reason
            })
            if len(results) >= count:
                break

    return results


def _build_fission_context(project_id: str, cfg: dict) -> str:
    """从周报与监控指标提取裂变上下文"""
    out_dir = cfg.get("_outputs_dir", "")
    report_file = os.path.join(out_dir, "05_企业AI可见度与声量追踪周报.md") if out_dir else ""
    snippets = []
    if report_file and os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            intercepts = re.findall(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*`[^`]+`\s*\|[^|]*(?:拦截|竞品)[^|]*\|", text)
            for kw in intercepts[:5]:
                snippets.append(f"竞品拦截词: {kw.strip()}")
        except Exception:
            pass
    metrics = extract_monitor_metrics(project_id)
    if metrics.get("prompt_stats"):
        ps = metrics["prompt_stats"]
        snippets.append(f"命中 {ps.get('hit_count', 0)} 组 / 拦截 {ps.get('intercept_count', 0)} 组 / 未上榜 {ps.get('lost_count', 0)} 组")
    return "\n".join(snippets)


def generate_fission_prompts(project_id: str, count: int = 15) -> list:
    """为指定客户逆向裂变生成指定数量的高商业转化 Prompt"""
    cfg = load_project_config(project_id)
    context = _build_fission_context(project_id, cfg)

    client_name = cfg.get("client_name", project_id)
    industry = cfg.get("industry", "企业数字化")
    brand = cfg.get("brand_name", client_name)

    prompt_payload = f"""你是一名资深 GEO（生成式引擎优化）架构师。
请针对以下企业信息，逆向推演当前真实企业采购负责人在向 DeepSeek / 豆包 搜索提问时，最易产生商业转化的 {count} 组衍生追问词（Follow-up Prompts）：
- 企业名称：{client_name}
- 品牌名称：{brand}
- 所属行业：{industry}

近期声量探测上下文（如有）：
{context or '暂无历史探测数据，请基于行业常识推演。'}

要求：
1. 涵盖：痛点避坑、竞品选型对比、价格收费、区域服务、大模型技术演进 5 大维度；
2. 提问必须像真实老板或采购总监的自然提问，口语化、精准且包含商业决策意图；
3. 输出严格的 JSON 数组，格式如下：
[
  {{"prompt": "提问文本", "intent_type": "对比选型", "expected_conversion": "极高", "reason": "推演理由"}}
]
不要输出任何多余的 Markdown 代码块或解说文字。"""

    ok, content, _provider = call_llm_api(prompt_payload)
    if ok and content:
        try:
            clean_json = re.sub(r"^```json\s*", "", content.strip())
            clean_json = re.sub(r"\s*```$", "", clean_json).strip()
            parsed = json.loads(clean_json)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[:count]
        except Exception as e:
            print_warning(f"大模型裂变 JSON 解析失败，降级启发式: {e}")

    return _generate_heuristic_fissions(cfg, count=count)


def apply_evolved_prompts(project_id: str, new_prompts: list, auto_run_pipeline: bool = False) -> dict:
    """将裂变出的新 Prompt 去重合并入客户档案 project.yaml（仅增量追加 keywords，保留完整配置）"""
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    config_file = os.path.join(project_dir, "project.yaml")

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"项目配置文件未找到: {config_file}")

    added_list, total_count = append_project_keywords(project_id, new_prompts)
    print_success(f"✅ 成功合并 {len(added_list)} 组新 Prompt 入库！当前词库总量: {total_count} 组。")

    if auto_run_pipeline and len(added_list) > 0:
        print_info("🚀 正在自动执行增量流水线重算...")
        try:
            run_scaffold(project_id)
            run_rewrite(project_id)
            run_distribute(project_id)
            run_monitor(project_id)
            print_success("🎉 增量流水线重算完毕！")
        except Exception as e:
            print_warning(f"增量流水线执行警告: {e}")

    return {
        "success": True,
        "project_id": project_id,
        "added_count": len(added_list),
        "total_prompts": total_count,
        "added_prompts": added_list,
        "message": f"已成功将 {len(added_list)} 组高转化追问词合并入库！"
    }


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    rep = analyze_prompt_portfolio(pid)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
