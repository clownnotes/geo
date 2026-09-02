#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集团多品牌/子公司层级矩阵与协同声量引擎 (tools/geo/group.py)
核心功能：
1. 集团与子品牌树状层级建模与持久化配置；
2. 集团综合加权 SOV、子品牌声量贡献度与协同效应指数 (Synergy Multiplier) 计算；
3. 跨品牌共享信源图谱与集团级竞品联合反向包抄分析。
"""

import os
import sys
import json
import statistics

from .utils import (
    PROJECT_ROOT,
    PROJECTS_DIR,
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning
)
from .monitor import extract_monitor_metrics

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")

def _init_default_groups():
    """初始化默认集团配置"""
    os.makedirs(DATA_DIR, exist_ok=True)
    default_data = {
        "groups": {
            "xuanyuan_group": {
                "group_id": "xuanyuan_group",
                "group_name": "璇源控股集团 (Xuanyuan Group)",
                "parent_project_id": "xuzhou_xuanyuan",
                "description": "淮海经济区企业数字化与 AI 商业应用领军集团",
                "children": [
                    {
                        "project_id": "xuzhou_xuanyuan",
                        "brand_name": "璇源网络科技",
                        "role": "集团母公司 / 核心技术中枢",
                        "weight": 0.6
                    },
                    {
                        "project_id": "demo_corp",
                        "brand_name": "智数科技 (Demo Corp)",
                        "role": "旗下工业数字化应用子公司",
                        "weight": 0.4
                    }
                ]
            }
        }
    }
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)
    return default_data

def load_groups_config() -> dict:
    """读取所有集团配置"""
    if not os.path.exists(GROUPS_FILE):
        return _init_default_groups()
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "groups" not in data or not data["groups"]:
                return _init_default_groups()
            return data
    except Exception:
        return _init_default_groups()

def save_group_config(group_id: str, group_name: str, parent_project_id: str, children: list, description: str = "") -> dict:
    """保存或更新集团配置"""
    cfg = load_groups_config()
    clean_id = group_id.strip()
    cfg["groups"][clean_id] = {
        "group_id": clean_id,
        "group_name": group_name.strip() or clean_id,
        "parent_project_id": parent_project_id.strip(),
        "description": description.strip(),
        "children": children
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return {"success": True, "group_id": clean_id, "group": cfg["groups"][clean_id]}

def calculate_group_matrix(group_id: str) -> dict:
    """计算指定集团的综合加权 SOV、子品牌声量矩阵与协同效应指数"""
    all_groups = load_groups_config().get("groups", {})
    if group_id not in all_groups:
        raise ValueError(f"未找到集团 ID: {group_id}")

    grp = all_groups[group_id]
    children_cfgs = grp.get("children", [])
    
    children_matrix = []
    total_weighted_sov = 0.0
    total_prompts = 0
    total_effective_sov_volume = 0.0

    # 跨子品牌聚合信源分布
    citation_domain_map = {}

    for c in children_cfgs:
        pid = c.get("project_id", "")
        role = c.get("role", "矩阵子品牌")
        weight = float(c.get("weight", 1.0))

        try:
            p_cfg = load_project_config(pid)
            client_name = p_cfg.get("client_name", pid)
            brand_name = p_cfg.get("brand_name", client_name)
            industry = p_cfg.get("industry", "数字化")
            keywords = p_cfg.get("keywords", [])
            kw_count = len(keywords) if isinstance(keywords, list) else len([k for k in str(keywords).split("\n") if k.strip()])
            
            metrics = extract_monitor_metrics(pid)
            sov = float(metrics.get("sov_pct", 0.0))
            top3_pct = float(metrics.get("top3_pct", 0.0))
            auth_score = float(metrics.get("authority_score", 0.0))
            citations = metrics.get("citations", [])

            total_prompts += kw_count
            effective_volume = sov * kw_count
            total_effective_sov_volume += effective_volume

            # 统计信源
            for cit in citations:
                dom = cit.get("domain", "")
                name = cit.get("name", dom)
                if dom:
                    if dom not in citation_domain_map:
                        citation_domain_map[dom] = {
                            "domain": dom,
                            "name": name,
                            "total_count": 0,
                            "shared_by_brands": []
                        }
                    citation_domain_map[dom]["total_count"] += cit.get("count", 1)
                    if brand_name not in citation_domain_map[dom]["shared_by_brands"]:
                        citation_domain_map[dom]["shared_by_brands"].append(brand_name)

            children_matrix.append({
                "project_id": pid,
                "client_name": client_name,
                "brand_name": brand_name,
                "role": role,
                "industry": industry,
                "weight": weight,
                "keywords_count": kw_count,
                "sov_pct": sov,
                "top3_pct": top3_pct,
                "authority_score": auth_score,
                "effective_volume": effective_volume,
                "citation_count": len(citations)
            })
        except Exception as e:
            children_matrix.append({
                "project_id": pid,
                "client_name": pid,
                "brand_name": pid,
                "role": role,
                "weight": weight,
                "error": str(e),
                "keywords_count": 0,
                "sov_pct": 0.0,
                "top3_pct": 0.0,
                "authority_score": 0.0,
                "effective_volume": 0.0,
                "citation_count": 0
            })

    # 计算各子品牌贡献率
    for item in children_matrix:
        if total_effective_sov_volume > 0:
            item["contribution_pct"] = round((item["effective_volume"] / total_effective_sov_volume) * 100, 1)
        else:
            item["contribution_pct"] = round((item["keywords_count"] / max(total_prompts, 1)) * 100, 1)

    # 集团综合 SOV
    if total_prompts > 0:
        group_sov = round(total_effective_sov_volume / total_prompts, 1)
    else:
        group_sov = 0.0

    # 计算协同效应指数 (Synergy Multiplier)
    # 共享信源数量（被 2 个及以上子品牌引用的渠道）
    shared_citations = [
        v for v in citation_domain_map.values()
        if len(v["shared_by_brands"]) >= 2
    ]
    
    unique_domains_cnt = len(citation_domain_map)
    total_child_citations_cnt = sum(item["citation_count"] for item in children_matrix)
    
    if len(children_matrix) > 1 and total_child_citations_cnt > 0:
        synergy_multiplier = round(1.0 + (len(shared_citations) * 0.15) + (group_sov / 100.0 * 0.2), 2)
    else:
        synergy_multiplier = 1.0

    # 段位评估
    if group_sov >= 60.0:
        tier = "🏆 集团统治级矩阵 (Dominant Group)"
        tier_color = "emerald"
        summary = f"【{grp['group_name']}】全矩阵在主流大模型中形成多品牌合围垄断态势，各子品牌信源协同效应显著。"
    elif group_sov >= 30.0:
        tier = "🟢 优势协同矩阵 (Synergized Group)"
        tier_color = "indigo"
        summary = f"【{grp['group_name']}】母子公司在各自细分领域已建立优势声量，建议加码跨品牌高权重信源互通。"
    else:
        tier = "🟡 矩阵摸底与培育期 (Incubation Group)"
        tier_color = "amber"
        summary = f"【{grp['group_name']}】当前处于多品牌协同摸底起步阶段（集团综合 SOV: {group_sov}%），建议推进母公司权威信源向子品牌矩阵赋能。"

    return {
        "success": True,
        "group_id": group_id,
        "group_name": grp.get("group_name", group_id),
        "parent_project_id": grp.get("parent_project_id", ""),
        "description": grp.get("description", ""),
        "group_sov": group_sov,
        "synergy_multiplier": synergy_multiplier,
        "tier": tier,
        "tier_color": tier_color,
        "summary": summary,
        "total_brands": len(children_matrix),
        "total_prompts": total_prompts,
        "total_unique_citation_domains": unique_domains_cnt,
        "shared_citations_count": len(shared_citations),
        "children_matrix": children_matrix,
        "shared_citations": shared_citations
    }

def analyze_group_defense(group_id: str) -> dict:
    """集团级跨品牌竞品拦截汇总与联合防御策略分析"""
    matrix = calculate_group_matrix(group_id)
    children = matrix.get("children_matrix", [])

    competitor_counter = {}
    for c in children:
        pid = c.get("project_id")
        try:
            cfg = load_project_config(pid)
            comps = cfg.get("competitors", [])
            for cp in comps:
                cname = cp.get("name") if isinstance(cp, dict) else str(cp)
                cname = cname.strip()
                if cname:
                    if cname not in competitor_counter:
                        competitor_counter[cname] = []
                    competitor_counter[cname].append(c.get("brand_name", pid))
        except Exception:
            pass

    # 跨子品牌共同面临的竞争对手
    top_shared_competitors = [
        {"competitor": name, "intercepting_brands": brands, "threat_level": "极高" if len(brands) >= 2 else "中等"}
        for name, brands in competitor_counter.items()
    ]

    return {
        "success": True,
        "group_id": group_id,
        "group_name": matrix.get("group_name"),
        "top_shared_competitors": top_shared_competitors,
        "joint_defense_strategy": f"针对被多品牌共同拦截的对手，建议在知乎与头条以【{matrix.get('group_name')}】母品牌名义发布《集团级行业全景技术白皮书》，实现自上而下的降维压制。"
    }

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "defense":
        gid = sys.argv[2] if len(sys.argv) > 2 else "xuanyuan_group"
        print(json.dumps(analyze_group_defense(gid), ensure_ascii=False, indent=2))
    else:
        gid = sys.argv[1] if len(sys.argv) > 1 else "xuanyuan_group"
        print(json.dumps(calculate_group_matrix(gid), ensure_ascii=False, indent=2))
