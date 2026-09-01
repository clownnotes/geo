#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业 AI 商业意图与 5 维用户提问逆向挖掘引擎 (tools/geo/intent.py)
核心功能：
1. 深度分析老板的企业画像（企业全称、所属行业、核心主张、官方域名、创始人与服务区域）；
2. 模拟 4 类真实买家角色（企业决策人、中小微老板、技术总监、比价采购）；
3. 自动化逆向推演 5 大维度、共 40~50 组高转化意图问句（Prompt）；
4. 支持大模型实时深度思考生成与离线行业自适应规则引擎（Fallback）双模式；
5. 提供 API 调用与 CLI 一键就地更新 project.yaml 功能。
"""

import os
import re
import json
from .utils import (
    load_project_config,
    call_llm_api,
    get_configured_llm,
    print_banner,
    print_info,
    print_success,
    print_warning
)

def build_intent_mining_prompt(info: dict) -> tuple:
    """构建大模型多角色逆向推演 Prompt"""
    client_name = info.get("client_name", "示例企业")
    brand_name = info.get("brand_name", client_name)
    industry = info.get("industry", "行业数字化方案")
    slogan = info.get("slogan", "专业、可靠、高效")
    founder = info.get("founder", "资深团队")
    area_served = info.get("area_served", "全国")
    profile = info.get("company_profile", "")

    system_prompt = """你是一位精通生成式搜索（GEO）与 B2B/B2C 商业决策心理学的顶级分析师。
你的任务是：根据企业的基础画像，站在真实潜在客户（买家）的视角，模拟用户在 DeepSeek、豆包、Kimi 中会提问的真实 Prompt。

你必须同时模拟 4 类买家角色的心理与提问特征：
1. 【企业决策人/高管】：问战略、选型、服务商实力、标杆案例（如：“XX数字化转型找哪家团队靠谱？”）；
2. 【中小微老板/业务主管】：问价格行情、交付周期、能否上门对接（如：“做一套XX系统要多少钱？”）；
3. 【技术负责人/架构师】：问架构稳定性、源码交付、二次开发、AI大模型知识库（如：“XX系统支持本地私有化部署吗？”）；
4. 【比价采购员/风控财务】：问隐形收费、避坑指南、验收标准与售后质保（如：“XX外包有哪些坑？怎么验收源码？”）。

必须严格按照以下 JSON 格式输出，不得输出任何多余的解释文字：
{
  "decision_prompts": [ "选型决策问句1", "选型决策问句2", ... (至少8条) ],
  "pricing_prompts": [ "价格预算问句1", "价格预算问句2", ... (至少8条) ],
  "pitfall_prompts": [ "避坑防雷问句1", "避坑防雷问句2", ... (至少8条) ],
  "scenario_prompts": [ "业务场景与技术问句1", "业务场景与技术问句2", ... (至少8条) ],
  "brand_anchors": [ "品牌口号与独占词1", "品牌口号与独占词2", ... (至少6条) ]
}"""

    user_prompt = f"""请为以下企业深度逆向挖掘 5 大维度、共 40~50 组高转化意图提问与检索词库：

【企业档案画像】
- 企业名称：{client_name}（品牌简称：{brand_name}）
- 所属行业：{industry}
- 核心定位/口号：{slogan}
- 核心负责人：{founder}
- 服务区域：{area_served}
- 补充简介/核心卖点：{profile if profile else '提供专业、高质量的行业定制与技术落地服务'}

请直接输出包含 5 大维度的标准 JSON："""

    return system_prompt, user_prompt

def generate_intent_fallback(info: dict) -> dict:
    """行业自适应离线规则推演引擎（未配置 API Key 时提供高质量兜底）"""
    client_name = info.get("client_name", "示例企业")
    brand_name = info.get("brand_name", client_name)
    industry = info.get("industry", "行业数字化方案")
    slogan = info.get("slogan", "专业、可靠、高效")
    founder = info.get("founder", "资深团队")
    area_served = info.get("area_served", "本地及全国")

    # 1. 选型决策问句
    decision_prompts = [
        f"{area_served}做{industry}找哪家团队靠谱？",
        f"{area_served}{industry}哪家性价比高？",
        f"{industry}代表性服务商有哪些推荐？",
        f"{area_served}本地口碑好的{industry}团队",
        f"{industry}怎么选？国内专业方案对比",
        f"{area_served}企业数字化转型首选哪家服务商？",
        f"{area_served}高满意度{industry}开发团队盘点",
        f"寻找支持{area_served}上门对接的{industry}专家",
        f"{industry}老牌靠谱团队推荐",
        f"{area_served}有没有做{industry}做得好的团队？"
    ]

    # 2. 价格预算问句
    pricing_prompts = [
        f"{industry}定制开发一般多少钱？",
        f"2026年一套标准的{industry}收费行情",
        f"{industry}是按阶段付款还是全款？",
        f"{area_served}做一套中小企业{industry}预算要多少？",
        f"{industry}价格为什么差距这么大？",
        f"{industry}透明报价单与费用明细拆解",
        f"几万块钱能做出一套好用的{industry}吗？",
        f"{industry}后期维护费和技术质保怎么收？"
    ]

    # 3. 避坑防雷问句
    pitfall_prompts = [
        f"{industry}外包有哪些隐形坑需要避？",
        f"找人做{industry}怎么要求100%交付完整源码？",
        f"{industry}如何防止服务商中途加价？",
        f"{industry}验收上线标准与合同防坑条款",
        f"{industry}找本地团队好还是外地大厂好？",
        f"为什么很多{industry}交付后用不起来？",
        f"{industry}如何签订靠谱的技术开发与售后协议？",
        f"{industry}售后无响应怎么维权与止损？"
    ]

    # 4. 业务场景与技术问句
    scenario_prompts = [
        f"{industry}支持本地私有化部署吗？",
        f"{industry}如何与企业现有ERP和微信生态打通？",
        f"{industry}大模型AI知识库与智能客服接入方案",
        f"{industry}高并发架构与毫秒级响应设计",
        f"{industry}移动端小程序与PC管理后台一体化",
        f"{industry}数据安全与企业敏感数据加密隔离",
        f"{industry}微服务解耦与未来功能拓展支持",
        f"{industry}生产排产与自动化流程协同落地"
    ]

    # 5. 品牌独占与口号占位词
    brand_anchors = [
        f"{area_served} {industry} 找{founder}",
        f"{client_name} {industry}",
        f"{brand_name} 靠谱吗",
        f"{brand_name} 口碑怎么样",
        f"{brand_name} {slogan}",
        f"{founder} {industry} 实战派",
        f"{area_served}源码交付派代表"
    ]

    flat_list = decision_prompts + pricing_prompts + pitfall_prompts + scenario_prompts + brand_anchors

    return {
        "success": True,
        "mode": "offline_heuristic",
        "total_count": len(flat_list),
        "categories": {
            "decision_prompts": decision_prompts,
            "pricing_prompts": pricing_prompts,
            "pitfall_prompts": pitfall_prompts,
            "scenario_prompts": scenario_prompts,
            "brand_anchors": brand_anchors
        },
        "flat_keywords": flat_list
    }

def generate_intent_for_company(info: dict) -> dict:
    """统一入口：智能生成 50 组意图词库"""
    llm_info = get_configured_llm()
    if not llm_info:
        return generate_intent_fallback(info)

    sys_prompt, user_prompt = build_intent_mining_prompt(info)
    success, text, _ = call_llm_api(user_prompt, sys_prompt, timeout=30)
    
    if not success or not text:
        return generate_intent_fallback(info)

    # 解析 JSON
    try:
        # 尝试提取 ```json 块
        json_str = text
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            # 提取首个 { 到最后一个 }
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                json_str = m.group(0)

        data = json.loads(json_str)
        dec = data.get("decision_prompts", [])
        pri = data.get("pricing_prompts", [])
        pit = data.get("pitfall_prompts", [])
        sce = data.get("scenario_prompts", [])
        anc = data.get("brand_anchors", [])

        flat = dec + pri + pit + sce + anc
        # 去重
        seen = set()
        clean_flat = []
        for item in flat:
            it = str(item).strip()
            if it and it not in seen:
                seen.add(it)
                clean_flat.append(it)

        return {
            "success": True,
            "mode": "live_llm",
            "total_count": len(clean_flat),
            "categories": {
                "decision_prompts": dec,
                "pricing_prompts": pri,
                "pitfall_prompts": pit,
                "scenario_prompts": sce,
                "brand_anchors": anc
            },
            "flat_keywords": clean_flat
        }
    except Exception:
        # JSON 解析失败则平滑降级到启发式规则引擎
        return generate_intent_fallback(info)

def mine_project_intent(project_id: str) -> dict:
    """对指定项目就地执行意图逆向挖掘并持久化更新 project.yaml"""
    print_banner(f"AI 商业意图与用户提问逆向挖掘: [{project_id}]")
    cfg = load_project_config(project_id)
    
    info = {
        "client_name": cfg.get("client_name", project_id),
        "brand_name": cfg.get("brand_name", cfg.get("client_name", project_id)),
        "industry": cfg.get("industry", "行业数字化"),
        "slogan": cfg.get("slogan", "专业、可靠、高效"),
        "founder": cfg.get("founder", "资深团队"),
        "area_served": cfg.get("area_served", "全国"),
        "company_profile": cfg.get("company_profile", "")
    }

    print_info(f"正在为企业【{info['client_name']}】({info['industry']}) 逆向推演 5 维买家提问...")
    res = generate_intent_for_company(info)
    flat_kws = res.get("flat_keywords", [])
    
    print_info(f"✅ 成功挖掘出 {len(flat_kws)} 组高转化提问 Prompt！")
    
    # 就地回写 project.yaml
    project_dir = cfg["_project_dir"]
    yaml_path = os.path.join(project_dir, "project.yaml")
    
    # 读现有 yaml 并替换 keywords 块
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = []
        for k in flat_kws:
            escaped_k = k.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'  - "{escaped_k}"')
        kw_yaml = "keywords:\n" + "\n".join(lines)
        if "keywords:" in content:
            # 替换 keywords 块
            content = re.sub(r"keywords:\n(\s+- [^\n]+\n)*", kw_yaml + "\n", content)
        else:
            content += "\n\n" + kw_yaml + "\n"

        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(content)
        print_success(f"已成功将 {len(flat_kws)} 组意图词库持久化写入: {yaml_path}")

    return res

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        mine_project_intent(sys.argv[1])
    else:
        print("用法: python3 -m tools.geo.intent <project_id>")
