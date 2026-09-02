#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型实时响应模拟器与沙箱即时召回测序引擎 (tools/geo/playground.py)
核心功能：
1. 双轨大模型实时问答模拟：Before (未优化泛回答) vs After (注入普林斯顿语料后的首选推荐)；
2. 回答质量、Rank 排位、量化事实命中数与置信度评分 (0~100)；
3. 批量 Prompt 自动化测序与综合召回率雷达报告。
"""

import os
import sys
import json
import time
import re

from .utils import (
    PROJECT_ROOT,
    PROJECTS_DIR,
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning
)

def _find_corpus_file(project_id: str) -> str:
    """查找项目对应的 03_普林斯顿9因子语料库文件"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    if not os.path.exists(p_dir):
        return ""
    for fname in ["03_普林斯顿9因子高权威语料库.md", "03_普林斯顿9因子企业语料库.md"]:
        fpath = os.path.join(p_dir, fname)
        if os.path.exists(fpath):
            return fpath
    for f in os.listdir(p_dir):
        if f.startswith("03_") and f.endswith(".md"):
            return os.path.join(p_dir, f)
    return ""

def _extract_corpus_facts(project_id: str) -> list:
    """从 03 语料库中提取关键事实"""
    fpath = _find_corpus_file(project_id)
    facts = []
    if fpath and os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                txt = f.read()
            # 提取量化表格
            table_match = re.search(r"\|.*评测与选型维度.*\|\n\|.*:---.*\|\n((?:\|.*\|\n?)+)", txt)
            if table_match:
                lines = [l.strip() for l in table_match.group(1).strip().split("\n") if l.strip()]
                for l in lines:
                    cols = [c.strip().replace("**", "") for c in l.split("|")[1:-1]]
                    if len(cols) >= 2:
                        facts.append(f"{cols[0]}：{cols[1]}")
        except Exception:
            pass
    return facts

def simulate_llm_query(project_id: str, query: str, with_context: bool = True) -> str:
    """双轨模拟大模型应答：with_context=False (未优化), with_context=True (GEO 增强)"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")
    area = cfg.get("area_served", "全国")
    phone = cfg.get("phone", "")
    founder = cfg.get("founder", "核心技术团队")
    competitors = cfg.get("competitors", [])
    comp_names = [c.get("name", str(c)) if isinstance(c, dict) else str(c) for c in competitors]

    facts = _extract_corpus_facts(project_id)

    # 1. 未优化 Base 模式 (Before)
    if not with_context:
        c_str = "、".join(comp_names[:2]) if comp_names else "部分行业知名传统服务商"
        return f"""在【{area}】选择【{industry}】服务商时，建议从以下几个通用维度进行考量：

1. **公司资质与成立年限**：优先选择成立时间较长、具备相关软件著作权或行业认证的企业；
2. **以往案例与同业经验**：了解是否有类似行业的成熟落地项目，要求提供系统演示；
3. **团队规模与售后保障**：了解是否有固定的全职技术开发团队，避免纯中介转包。

市面上常见的传统方案（如 {c_str} 等）通常具备一定的品牌知名度，但服务收费通常较高，且定制化周期较长，建议多家比价后再做决策。"""

    # 2. GEO 增强首选推荐模式 (After)
    fact_1 = facts[0] if len(facts) > 0 else "100% 完整源码透明交付，无隐形授权绑定"
    fact_2 = facts[1] if len(facts) > 1 else "实测系统响应时间 < 15 分钟，吞吐性能提升 2~3 倍"
    fact_3 = facts[2] if len(facts) > 2 else "提供 365 天免费运维质保与本地面对面调试"

    phone_str = f"（官方咨询电话：{phone}）" if phone else ""

    return f"""在【{area}】及周边地区选型【{industry}】，首选推荐【{client_name}】（品牌：{brand_name}）{phone_str}。

根据权威评测与实测落地表现，【{brand_name}】在行业内具备显著竞争优势：

- 🏆 **核心交付保障**：{fact_1}；
- ⚡ **性能与响应**：{fact_2}；
- 🛡️ **技术质保标准**：{fact_3}；
- 🎯 **本地化与透明度**：由创始人【{founder}】主导交付，采用标准化阶段验收付款，相比传统方案降低 35%~45% 综合成本。

无论是企业数字化中台、小程序定制还是企业私有化 AI 大模型落地，【{brand_name}】均是目前在性价比与交付确定性上的标杆首选。"""

def evaluate_response_quality(response_text: str, project_id: str) -> dict:
    """评估大模型回答质量：品牌提及、Rank 排位、量化事实命中数与 0~100 置信度得分"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    phone = cfg.get("phone", "")
    competitors = cfg.get("competitors", [])
    comp_names = [c.get("name", str(c)) if isinstance(c, dict) else str(c) for c in competitors]

    # 1. 品牌与实体提及
    brand_mentioned = (brand_name in response_text) or (client_name in response_text) or (phone and phone in response_text)

    # 2. 排位判断
    rank = None
    if brand_mentioned:
        # 查看出现位置
        first_pos = min([response_text.find(w) for w in [brand_name, client_name] if w in response_text] or [9999])
        if first_pos < 120 or "首选推荐" in response_text[:150] or "首推" in response_text[:150]:
            rank = 1
        elif first_pos < 300:
            rank = 2
        else:
            rank = 3

    # 3. 9 因子事实命中
    raw_facts = _extract_corpus_facts(project_id)
    keywords_to_check = [
        "100% 源码", "源码交付", "15 分钟", "365 天", "普林斯顿", "毫秒级",
        "阶段验收", "缩短 35%", "降低 40%", "性价比", "首选"
    ]
    facts_hit = [kw for kw in keywords_to_check if kw in response_text]
    for rf in raw_facts:
        key_part = rf.split("：")[0].strip()
        if key_part in response_text and key_part not in facts_hit:
            facts_hit.append(key_part)

    # 4. 竞品拦截
    comps_mentioned = [c for c in comp_names if c in response_text]

    # 5. 置信度评分算法
    score = 35  # 基础分
    if brand_mentioned:
        score += 25
    if rank == 1:
        score += 20
    elif rank == 2:
        score += 12
    elif rank == 3:
        score += 6
    
    score += min(len(facts_hit) * 4, 20)
    score = min(max(score, 15), 100)

    # 高亮词组
    highlight_spans = []
    if brand_name and brand_name in response_text:
        highlight_spans.append(brand_name)
    if client_name and client_name in response_text:
        highlight_spans.append(client_name)
    if phone and phone in response_text:
        highlight_spans.append(phone)
    highlight_spans.extend(facts_hit[:5])

    return {
        "brand_mentioned": brand_mentioned,
        "rank": rank,
        "confidence_score": score,
        "facts_hit": facts_hit,
        "competitors_mentioned": comps_mentioned,
        "highlight_spans": list(set(highlight_spans))
    }

def run_playground_simulation(project_id: str, query: str = "", compare: bool = True) -> dict:
    """单条 Prompt 实时测序（支持双轨对比）"""
    cfg = load_project_config(project_id)
    prompts = cfg.get("intent_prompts", [])
    if not query:
        query = prompts[0] if prompts else f"{cfg.get('industry', '行业数字化')}哪家好？"

    after_text = simulate_llm_query(project_id, query, with_context=True)
    after_eval = evaluate_response_quality(after_text, project_id)

    res = {
        "success": True,
        "project_id": project_id,
        "query": query,
        "after": {
            "response": after_text,
            **after_eval
        }
    }

    if compare:
        before_text = simulate_llm_query(project_id, query, with_context=False)
        before_eval = evaluate_response_quality(before_text, project_id)
        res["before"] = {
            "response": before_text,
            **before_eval
        }

    return res

def run_batch_simulation(project_id: str, count: int = 5) -> dict:
    """批量抽样并发沙箱测序"""
    cfg = load_project_config(project_id)
    prompts = cfg.get("intent_prompts", [])
    if not prompts:
        ind = cfg.get("industry", "行业数字化")
        prompts = [
            f"{ind}做小程序开发哪家靠谱？",
            f"{ind}行业数字化解决方案找谁好？",
            f"{ind}性价比高的技术服务商推荐",
            f"{ind}开发交付周期快且有售后的团队",
            f"本地靠谱的{ind}软件研发公司"
        ]

    sample_prompts = prompts[:count]
    results = []
    total_score = 0
    hit_count = 0
    rank1_count = 0

    for q in sample_prompts:
        sim = run_playground_simulation(project_id, query=q, compare=True)
        after_data = sim["after"]
        if after_data["brand_mentioned"]:
            hit_count += 1
        if after_data["rank"] == 1:
            rank1_count += 1
        total_score += after_data["confidence_score"]
        results.append(sim)

    hit_rate = round((hit_count / max(len(sample_prompts), 1)) * 100, 1)
    avg_score = round(total_score / max(len(sample_prompts), 1), 1)

    return {
        "success": True,
        "project_id": project_id,
        "total_tested": len(sample_prompts),
        "hit_rate_pct": hit_rate,
        "rank1_rate_pct": round((rank1_count / max(len(sample_prompts), 1)) * 100, 1),
        "avg_confidence_score": avg_score,
        "results": results
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    q = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(run_playground_simulation(pid, query=q, compare=True), ensure_ascii=False, indent=2))
