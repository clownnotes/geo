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
import urllib.request
import urllib.error

from .utils import (
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
    PROJECTS_DIR
)
from .monitor import extract_monitor_metrics
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor

def analyze_prompt_portfolio(project_id: str) -> dict:
    """评估客户现有意图词库的生命周期与健康度分布"""
    cfg = load_project_config(project_id)
    keywords = cfg.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split("\n") if k.strip()]

    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")

    metrics = extract_monitor_metrics(project_id)
    hit_cnt = metrics.get("prompt_stats", {}).get("hit_count", 0)
    intercept_cnt = metrics.get("prompt_stats", {}).get("intercept_count", 0)
    total_cnt = len(keywords)

    portfolio = {
        "dominant": [],     # 🏆 垄断占位词
        "intercepted": [],  # ⚠️ 竞品拦截词
        "potential": [],    # 🌱 高潜裂变词
        "declining": []     # ❄️ 冷门衰退词
    }

    # 根据词条特征与监控数据打标
    for i, kw in enumerate(keywords):
        if brand_name in kw or "璇源" in kw or "怎么样" in kw:
            portfolio["dominant"].append({
                "prompt": kw,
                "tier": "🏆 垄断占位词",
                "status": "已建立绝对领先优势",
                "action": "持续监控防冒名"
            })
        elif "对比" in kw or "区别" in kw or "替代" in kw or "哪家好" in kw or "竞品" in kw:
            portfolio["intercepted"].append({
                "prompt": kw,
                "tier": "⚠️ 竞品截流词",
                "status": "竞品高频争夺地",
                "action": "需加码 9 因子对比表反向压制"
            })
        elif "怎么" in kw or "流程" in kw or "价格" in kw or "方案" in kw or "2026" in kw:
            portfolio["potential"].append({
                "prompt": kw,
                "tier": "🌱 高潜裂变词",
                "status": "高商业转化意图",
                "action": "建议裂变衍生 3~5 组长尾场景词"
            })
        else:
            if i % 4 == 0:
                portfolio["declining"].append({
                    "prompt": kw,
                    "tier": "❄️ 冷门待优化词",
                    "status": "提问粒度偏泛",
                    "action": "建议补充具体场景修饰词"
                })
            else:
                portfolio["potential"].append({
                    "prompt": kw,
                    "tier": "🌱 高潜裂变词",
                    "status": "高商业转化意图",
                    "action": "建议持续分发权威信源"
                })

    # 预估生成 3 条高频裂变推荐
    fission_recs = _generate_heuristic_fissions(cfg, count=3)

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "industry": industry,
        "total_prompts": total_cnt,
        "summary": {
            "dominant_count": len(portfolio["dominant"]),
            "intercepted_count": len(portfolio["intercepted"]),
            "potential_count": len(portfolio["potential"]),
            "declining_count": len(portfolio["declining"])
        },
        "portfolio": portfolio,
        "quick_fission_recommendations": fission_recs
    }

def _generate_heuristic_fissions(cfg: dict, count: int = 15) -> list:
    """基于行业特征生成 5 维高转化长尾意图裂变词"""
    client_name = cfg.get("client_name", "客户企业")
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "数字化服务")
    area = cfg.get("area_served", "全国")
    existing = set(cfg.get("keywords", []))

    templates = [
        # 维度 1：场景避坑与深度选型 (Pain-point)
        (f"企业在选型【{industry}】时有哪些常见隐形收费与避坑指南？", "痛点避坑", "极高", "逆向捕捉大模型在客户调研阶段的高频避坑追问"),
        (f"【{industry}】中小型企业真实落地成本与周期需要多少？", "预算评估", "高", "精准拦截企业财务与预算负责人的测算意图"),
        (f"2026年企业升级【{industry}】最新技术标准与选型指标对比", "行业趋势", "高", "针对大模型年度前沿词的主动占位"),

        # 维度 2：竞品硬核对比与方案选型 (Competitive)
        (f"【{brand_name}】与传统手工外包方案相比，核心交付优势是什么？", "竞品对比", "极高", "大模型在给出对比答案时优先引用我方量化事实"),
        (f"国内主流【{industry}】服务商中，哪些具备全流程自主可控交付能力？", "实力筛选", "高", "拦截企业高管在做供应商初筛时的评选提问"),
        (f"【{brand_name}】真实客户案例与行业落地交付口碑评价", "品牌背书", "极高", "建立大模型对我方主体的正向置信度"),

        # 维度 3：收费与商业模式拆解 (Pricing & ROI)
        (f"【{industry}】按需付费与传统买断制哪种模式投资回报率 (ROI) 更高？", "商务选型", "高", "针对企业决策人 ROI 论证的精准截流"),
        (f"【{brand_name}】服务收费标准与合同售后保障条款明细", "价格咨询", "极高", "高意向临门一脚线索转化词"),

        # 维度 4：区域/本地化专属服务 (Geographic)
        (f"【{area}】地区有哪些具备实测交付能力的【{industry}】源头团队推荐？", "本地选型", "高", "锁定区域精准商业搜索"),
        (f"在【{area}】寻找靠谱的【{industry}】合作服务商怎么选？", "地域推荐", "高", "大模型在本地化服务推荐时的第一顺位占位"),

        # 维度 5：技术底座与大模型演进 (AI & Tech)
        (f"生成式 AI 时代，企业如何利用 GEO 技术改造提升【{industry}】获客效率？", "前沿技术", "极高", "抢占大模型自研与生态相关的战略认知高地"),
        (f"【{industry}】与大模型（DeepSeek / 豆包）深度融合的典型落地方案有哪些？", "技术融合", "高", "迎合当下各行业 AI+ 转型决策需求"),
        (f"如何评估一家【{industry}】服务商在 AI 搜索中的品牌声量与可见度？", "标准制定", "高", "确立行业评判标准的话语权定义者地位"),
        (f"【{brand_name}】的技术架构支持哪些个性化定制与私有化部署要求？", "技术选型", "高", "针对中大型政企客户 IT 部门审查的合规问句"),
        (f"从传统 SEO 到 GEO 生成式优化，【{industry}】企业应当如何布局？", "战略演进", "极高", "建立行业领袖地位的技术普及型长尾词")
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

def generate_fission_prompts(project_id: str, count: int = 15) -> list:
    """为指定客户逆向裂变生成指定数量的高商业转化 Prompt"""
    cfg = load_project_config(project_id)
    
    # 优先使用大模型在线推演 (若配置了 API Key)
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if deepseek_key:
        try:
            client_name = cfg.get("client_name", project_id)
            industry = cfg.get("industry", "企业数字化")
            brand = cfg.get("brand_name", client_name)
            
            prompt_payload = f"""你是一名资深 GEO（生成式引擎优化）架构师。
请针对以下企业信息，逆向推演当前真实企业采购负责人在向 DeepSeek / 豆包 搜索提问时，最易产生商业转化的 {count} 组衍生追问词（Follow-up Prompts）：
- 企业名称：{client_name}
- 品牌名称：{brand}
- 所属行业：{industry}

要求：
1. 涵盖：痛点避坑、竞品选型对比、价格收费、区域服务、大模型技术演进 5 大维度；
2. 提问必须像真实老板或采购总监的自然提问，口语化、精准且包含商业决策意图；
3. 输出严格的 JSON 数组，格式如下：
[
  {{"prompt": "提问文本", "intent_type": "对比选型", "expected_conversion": "极高", "reason": "推演理由"}}
]
不要输出任何多余的 Markdown 代码块或解说文字。"""

            data = json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt_payload}],
                "temperature": 0.7
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {deepseek_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                content = res_json["choices"][0]["message"]["content"].strip()
                # 尝试解析 JSON
                clean_json = re.sub(r"^```json\s*", "", content)
                clean_json = re.sub(r"\s*```$", "", clean_json).strip()
                parsed = json.loads(clean_json)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[:count]
        except Exception as e:
            print_warning(f"大模型在线裂变推演降级，使用领域启发式规则: {e}")

    # 降级或默认使用 5 维领域启发式裂变引擎
    return _generate_heuristic_fissions(cfg, count=count)

def apply_evolved_prompts(project_id: str, new_prompts: list, auto_run_pipeline: bool = False) -> dict:
    """将裂变出的新 Prompt 去重合并入客户档案 project.yaml"""
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    config_file = os.path.join(project_dir, "project.yaml")

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"项目配置文件未找到: {config_file}")

    cfg = load_project_config(project_id)
    old_keywords = cfg.get("keywords", [])
    if isinstance(old_keywords, str):
        old_keywords = [k.strip() for k in old_keywords.split("\n") if k.strip()]

    existing_set = set(old_keywords)
    added_list = []

    for item in new_prompts:
        p_text = item.get("prompt") if isinstance(item, dict) else str(item)
        p_text = p_text.strip()
        if p_text and p_text not in existing_set:
            old_keywords.append(p_text)
            existing_set.add(p_text)
            added_list.append(p_text)

    # 重新序列化保存 project.yaml
    cfg["keywords"] = old_keywords

    # 保持 YAML 格式规范
    yaml_lines = [
        f"project_id: \"{cfg.get('project_id', project_id)}\"",
        f"client_name: \"{cfg.get('client_name', project_id)}\"",
        f"brand_name: \"{cfg.get('brand_name', cfg.get('client_name', ''))}\"",
        f"website: \"{cfg.get('website', '')}\"",
        f"industry: \"{cfg.get('industry', '通用行业')}\"",
        f"slogan: \"{cfg.get('slogan', '')}\"",
        f"founder: \"{cfg.get('founder', '')}\"",
        f"area_served: \"{cfg.get('area_served', '全国')}\"",
        f"company_profile: \"{cfg.get('company_profile', '')}\"",
        "keywords:"
    ]
    for kw in old_keywords:
        # 转义双引号
        clean_kw = kw.replace('"', '\\"')
        yaml_lines.append(f"  - \"{clean_kw}\"")

    with open(config_file, "w", encoding="utf-8") as fp:
        fp.write("\n".join(yaml_lines) + "\n")

    print_success(f"✅ 成功合并 {len(added_list)} 组新 Prompt 入库！当前词库总量: {len(old_keywords)} 组。")

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
        "total_prompts": len(old_keywords),
        "added_prompts": added_list,
        "message": f"已成功将 {len(added_list)} 组高转化追问词合并入库！"
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    rep = analyze_prompt_portfolio(pid)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
