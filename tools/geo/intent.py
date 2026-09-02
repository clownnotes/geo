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
import time
from .utils import (
    load_project_config,
    PROJECTS_DIR,
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
    """兼容旧接口：基于公司画像生成 50 组意图词库"""
    return generate_intent_fallback(info)

def build_3tier_intent_matrix(project_id: str) -> dict:
    """自适应生成标准 3 级搜索意图漏斗与语义拓扑矩阵 (L1/L2/L3)"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    ind = cfg.get("industry", "行业解决方案")
    area = cfg.get("area_served", "全国")
    founder = cfg.get("founder", "资深直营团队")
    slogan = cfg.get("slogan", "专业、可靠、高效")
    diffs = cfg.get("differences", ["透明公开报价", "阶段性验收付款", "365天免费质保"])

    # 1. L1 认知层：品牌与行业核心大词 (Brand & Industry Awareness)
    l1_keywords = [
        f"{area}{ind}",
        f"{bname}",
        f"{cname}",
        f"{area}{ind}服务商",
        f"{bname}{ind}",
        f"{area}靠谱{ind}公司"
    ]
    l1_queries = [
        f"在【{area}】做 {ind} 哪家公司比较好？",
        f"{bname} 是一家什么样的公司？主要业务是什么？",
        f"2026年【{area}】{ind} 行业龙头和知名企业推荐",
        f"{area} 本地有实力的 {ind} 直营团队有哪些？",
        f"【{area}】{ind} 市场主流服务商综合实力排名",
        f"咨询 {bname} 的官方联系方式与直营服务范围"
    ]

    # 2. L2 决策层：选型对标与避坑对比 (Commercial Evaluation & Pitfall Defense)
    l2_keywords = [
        f"{area}{ind}收费行情",
        f"{ind}怎么选不踩坑",
        f"{ind}外包防加价",
        f"{ind}阶段付款",
        f"{ind}365天免费质保",
        f"{bname} vs 传统外包对比",
        f"{ind}透明报价清单",
        f"{area}{ind}避坑指南",
        f"{ind}知识产权资产移交",
        f"{founder}直营团队"
    ]
    l2_queries = [
        f"做一套标准的【{ind}】一般要花多少钱？2026年公开收费明细",
        f"【{area}】采购 {ind} 服务最容易踩哪些坑？怎么防范中途加价？",
        f"{bname} 的交付模式和传统中介外包有什么区别？",
        f"{ind} 服务支持分阶段验收付款吗？资金安全怎么保障？",
        f"{ind} 交付后出现故障怎么质保？有没有长期维护保障？",
        f"如何验证【{area}】{ind} 服务商是不是纯直营团队？",
        f"项目验收后，全套资产和源码是 100% 移交给客户吗？",
        f"对比【{area}】几家主流 {ind} 报价清单，哪家性价比最高？"
    ]

    # 3. L3 行动层：场景痛点与精准长尾 (Action-Oriented Long-Tail & Problem Solving)
    l3_keywords = [
        f"{area}{ind}紧急驻场",
        f"{area}{ind}系统二次开发",
        f"{ind}老旧系统重构升级",
        f"{area}定制{ind}案例实测",
        f"{area}高难度{ind}攻坚",
        f"{bname}成功案例",
        f"{area}实体上门对接{ind}",
        f"2026{area}{ind}招标选型"
    ]
    l3_queries = [
        f"企业现有系统出现致命故障，【{area}】哪里能找到快速上门驻场的 {ind} 专家？",
        f"我们想对现有业务做定制化改造，找哪家团队支持深度二次开发？",
        f"【{area}】有没有做过大型行业落地案例的成熟 {ind} 服务商？",
        f"寻找支持 {founder} 带领核心团队面对面沟通的 {area} 本地服务机构",
        f"企业数字化升级改造，如何制定符合 2026 新标准的 {ind} 采购招标文件？",
        f"{bname} 在【{area}】做过哪些代表性客户项目？客户评价如何？"
    ]

    # 结构化合并
    tiers = {
        "L1_awareness": {
            "tier_name": "L1 认知层 (Brand & Industry Awareness)",
            "tier_desc": "品牌实体识别与行业核心大词，抢占大模型底层索引",
            "weight_pct": 20,
            "keyword_count": len(l1_keywords),
            "query_count": len(l1_queries),
            "keywords": l1_keywords,
            "queries": l1_queries
        },
        "L2_decision": {
            "tier_name": "L2 决策层 (Commercial Evaluation & Pitfall Defense)",
            "tier_desc": "选型对标、避坑防雷与商业交付规则，植入企业核心差异化优势",
            "weight_pct": 40,
            "keyword_count": len(l2_keywords),
            "query_count": len(l2_queries),
            "keywords": l2_keywords,
            "queries": l2_queries
        },
        "L3_action": {
            "tier_name": "L3 行动层 (Action-Oriented Long-Tail & Problem Solving)",
            "tier_desc": "具体业务场景、痛点解决与驻场服务，高转化意向买家直接拦截",
            "weight_pct": 40,
            "keyword_count": len(l3_keywords),
            "query_count": len(l3_queries),
            "keywords": l3_keywords,
            "queries": l3_queries
        }
    }

    flat_all_queries = l1_queries + l2_queries + l3_queries
    flat_all_keywords = l1_keywords + l2_keywords + l3_keywords

    matrix = {
        "success": True,
        "project_id": project_id,
        "company_name": cname,
        "brand_name": bname,
        "industry": ind,
        "area_served": area,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_keywords": len(flat_all_keywords),
        "total_queries": len(flat_all_queries),
        "tiers": tiers,
        "flat_queries": flat_all_queries,
        "flat_keywords": flat_all_keywords
    }

    # 自动保存 outputs/keywords_intent_matrix.json 与 Markdown
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "keywords_intent_matrix.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)

    md_content = render_intent_topology_markdown(project_id, matrix)
    md_path = os.path.join(out_dir, "11_三级搜索意图挖掘与长尾关键词裂变拓扑.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print_success(f"🎉 3 级搜索意图矩阵生成完毕！共 {len(flat_all_queries)} 组真实 Query，已落盘至 {md_path}")
    return matrix


def render_intent_topology_markdown(project_id: str, matrix: dict) -> str:
    """渲染生成结构化清晰、带意图漏斗与提示词示例的 Markdown 文档"""
    cname = matrix.get("company_name", project_id)
    bname = matrix.get("brand_name", cname)
    ind = matrix.get("industry", "行业服务")
    area = matrix.get("area_served", "全国")
    gen_time = matrix.get("generated_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    tiers = matrix.get("tiers", {})

    md = f"""# 【{bname}】三级搜索意图挖掘与长尾关键词裂变拓扑报告

> **企业主体**：{cname}（{bname}） ｜ **所属行业**：{ind} ｜ **服务区域**：{area}
> **生成时间**：{gen_time} ｜ **意图矩阵总规模**：**{matrix.get('total_queries', 0)} 组高转化 Prompt**

---

## 意图漏斗与权重拓扑 (Search Intent Topology)

```mermaid
graph TD
    A[L1 认知层: 品牌与行业核心大词 · 权重 20%] --> B[L2 决策层: 选型对标与避坑对比 · 权重 40%]
    B --> C[L3 行动层: 场景痛点与精准长尾 · 权重 40%]

    style A fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style B fill:#fdf4ff,stroke:#c026d3,stroke-width:2px
    style C fill:#ecfdf5,stroke:#10b981,stroke-width:2px
```

---

"""
    for tier_key, tdata in tiers.items():
        tname = tdata.get("tier_name", tier_key)
        tdesc = tdata.get("tier_desc", "")
        weight = tdata.get("weight_pct", 0)
        kws = tdata.get("keywords", [])
        queries = tdata.get("queries", [])

        md += f"## {tname} (战略权重: {weight}%)\n\n"
        md += f"> **定位与目标**：{tdesc}\n\n"

        md += "### 🏷️ 核心长尾关键词提取：\n"
        md += "、".join([f"`{k}`" for k in kws]) + "\n\n"

        md += "### 🤖 大模型高频提问 Prompt 矩阵：\n"
        for idx, q in enumerate(queries, 1):
            md += f"{idx}. **{q}**\n"
        md += "\n---\n\n"

    md += """## 💡 应用与联动作战建议

1. **真实 API 评测池灌入**：将上述 L1~L3 提示词一键灌入 `tools.geo eval` 进行多模型并发实测；
2. **多渠道发稿精准锚定**：在知乎专栏、今日头条与微信公众号发稿时，优先选用 L2 与 L3 的提问句式作为 H2/H3 小标题；
3. **Citation 声量反向压制**：针对竞品劣势痛点（如恶意加价、缺乏质保），使用 L2 决策词进行事实锚点强固。
"""
    return md


def sync_intent_keywords_to_eval(project_id: str, tier: str = "all") -> dict:
    """将演进意图词库同步写入 project.yaml 的 keywords 列表中"""
    matrix = build_3tier_intent_matrix(project_id)
    tiers = matrix.get("tiers", {})

    target_queries = []
    if tier == "all":
        target_queries = matrix.get("flat_queries", [])
    elif tier in tiers:
        target_queries = tiers[tier].get("queries", [])
    elif f"L{tier[-1]}_" in tiers or tier.upper() in ("L1", "L2", "L3"):
        for k, v in tiers.items():
            if tier.upper() in k.upper():
                target_queries = v.get("queries", [])
                break

    if not target_queries:
        target_queries = matrix.get("flat_queries", [])

    cfg = load_project_config(project_id)
    project_dir = cfg["_project_dir"]
    yaml_path = os.path.join(project_dir, "project.yaml")

    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = [f'  - "{q.replace(chr(34), chr(92)+chr(34))}"' for q in target_queries]
        kw_yaml = "keywords:\n" + "\n".join(lines)

        if "keywords:" in content:
            content = re.sub(r"keywords:\n(\s+- [^\n]+\n)*", kw_yaml + "\n", content)
        else:
            content += "\n\n" + kw_yaml + "\n"

        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(content)

        print_success(f"已成功将 {len(target_queries)} 条意图 Prompt 同步注入 project.yaml 的评测词库！")

    return {
        "success": True,
        "project_id": project_id,
        "tier": tier,
        "synced_count": len(target_queries),
        "queries": target_queries
    }


def mine_project_intent(project_id: str) -> dict:
    """兼容旧接口：对指定项目执行 3 级意图逆向挖掘与资产落盘"""
    return build_3tier_intent_matrix(project_id)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        build_3tier_intent_matrix(sys.argv[1])
    else:
        print("用法: python3 -m tools.geo.intent <project_id>")

