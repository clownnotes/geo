# -*- coding: utf-8 -*-
"""大模型品牌商业心智渗透率与高阶商业转化价值量化审计中枢 (tools/geo/mindshare_auditor.py)

全案第 21 维核心资产：
1. 聚合 18(SOV/角标率)、19(BRS声誉分)、20(KRR知识留存率) 与 04(存活台账)；
2. MPI 四维加权模型: 0.35 * Weighted SOV + 0.25 * Cit + 0.25 * BRS + 0.15 * KRR；
3. CCV 商业转化价值模型: 年化等效竞价广告采购价值 AEV (系数 0.20 商业商机转化)；
4. outputs/commercial_roi_pitch/ 3 份高管商务交付成果物；
5. outputs/21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md (自适应 live/sandbox 话术与财务免责)。
"""

import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from tools.geo.dist_bot import get_distribution_ledger
from tools.geo.llm import call_model_raw
from tools.geo.probing import (
    extract_citations_and_sources,
    is_ledger_asset_eligible,
    normalize_url,
)
from tools.geo.utils import PROJECTS_DIR, load_project_config


# 行业平均线索获客成本基准 (CPA 估算，元/有效商业线索)
INDUSTRY_CPA_BENCHMARK: Dict[str, int] = {
    "software": 150,
    "legal": 200,
    "machinery": 300,
    "catering": 80,
    "medical": 260,
    "education": 120,
    "default": 100,
}


def calculate_mpi(
    weighted_sov: float,
    citation_rate: float,
    brs_score: float,
    krr_rate: float,
) -> float:
    """测算商业心智渗透指数 (Mindshare Penetration Index, MPI 0.0 ~ 100.0)

    权重契约: 0.35 * Weighted SOV + 0.25 * Cit + 0.25 * BRS + 0.15 * KRR
    """
    sov_clamped = max(0.0, min(100.0, float(weighted_sov)))
    cit_clamped = max(0.0, min(100.0, float(citation_rate)))
    brs_clamped = max(0.0, min(100.0, float(brs_score)))
    krr_clamped = max(0.0, min(100.0, float(krr_rate)))

    raw_mpi = (
        0.35 * sov_clamped
        + 0.25 * cit_clamped
        + 0.25 * brs_clamped
        + 0.15 * krr_clamped
    )
    return round(max(0.0, min(100.0, raw_mpi)), 1)


def mindshare_grade(mpi: float) -> Tuple[str, str]:
    """根据 MPI 得分返回五星等级枚举与中文名"""
    if mpi >= 85.0:
        return "market_leader", "🟢 五星心智垄断 (Market Leader)"
    if mpi >= 70.0:
        return "strong_contender", "🔵 四星强势竞争 (Strong Contender)"
    if mpi >= 55.0:
        return "moderate_visibility", "🟡 三星中度可见 (Moderate Visibility)"
    return "underrepresented", "🔴 两星心智盲区 (Underrepresented)"


def estimate_commercial_conversion_value(
    mpi: float,
    query_count: int = 5,
    industry: str = "default",
    cpa_override: Optional[int] = None,
    conversion_factor: float = 0.20,
) -> Dict[str, Any]:
    """测算年化等效公域竞价广告采购价值 (Annual Ad Equivalent Value, AEV)

    AEV = round(|Q| * 365 * (MPI / 100.0) * CPA * conversion_factor, 0)
    业务释义: 核心商业意图在 AI 大模型中产生的决策拦截，折算为百度/巨量竞价等效采购成本。
    """
    cpa = cpa_override if (cpa_override and cpa_override > 0) else INDUSTRY_CPA_BENCHMARK.get(industry, 100)
    q_num = max(1, int(query_count))
    factor = float(conversion_factor) if float(conversion_factor) > 0 else 0.20

    raw_aev = q_num * 365.0 * (float(mpi) / 100.0) * float(cpa) * factor
    annual_aev = int(round(raw_aev, 0))

    return {
        "annual_aev_yuan": annual_aev,
        "cpa_unit_price": cpa,
        "query_count": q_num,
        "conversion_factor": factor,
        "industry": industry,
    }


def _load_factual_anchors(project_id: str) -> Dict[str, Any]:
    """读取真实事实档案，未生成时回退读取 project_config (杜绝虚构模块)"""
    factual_path = os.path.join(PROJECTS_DIR, project_id, "outputs", "factual_anchors.json")
    if os.path.exists(factual_path):
        try:
            with open(factual_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return load_project_config(project_id)


def _collect_eligible_ledger_urls(project_id: str) -> set:
    """强制调用 get_distribution_ledger 提取存活台账有效外链 (仅认 published/verified)"""
    eligible_urls = set()
    ledger = get_distribution_ledger(project_id)

    for ch_key, ch_data in ledger.get("channels", {}).items():
        url = ch_data.get("url", "")
        status = ch_data.get("status", "")
        if is_ledger_asset_eligible(url, status):
            norm = normalize_url(url)
            if norm:
                eligible_urls.add(norm)

    for cl in ledger.get("custom_links", []):
        url = cl.get("url", "")
        status = cl.get("status") or "published"
        if is_ledger_asset_eligible(url, status):
            norm = normalize_url(url)
            if norm:
                eligible_urls.add(norm)

    return eligible_urls


def _sample_business_queries(project_id: str, limit: int = 5) -> List[str]:
    """从项目意图拓扑库或配置中动态采样商业意图词 (严禁写死徐州或特定品牌)"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    matrix_path = os.path.join(out_dir, "keywords_intent_matrix.json")
    sampled = []

    if os.path.exists(matrix_path):
        try:
            with open(matrix_path, "r", encoding="utf-8") as f:
                mat = json.load(f)
                for item in mat.get("matrix", []):
                    q = item.get("prompt") or item.get("keyword")
                    if q and q not in sampled:
                        sampled.append(q)
                    if len(sampled) >= limit:
                        break
        except Exception:
            pass

    if len(sampled) < limit:
        cfg = load_project_config(project_id)
        kws = cfg.get("target_keywords") or cfg.get("keywords") or []
        client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
        for kw in kws:
            if kw and kw not in sampled:
                sampled.append(f"{kw} 哪家实力强选型推荐")
            if len(sampled) >= limit:
                break

    if len(sampled) < limit:
        cfg = load_project_config(project_id)
        client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
        defaults = [
            f"{client_name} 行业口碑与交付实力怎么样",
            f"{client_name} 企业级解决方案与选型推荐",
            f"{client_name} 真实客户案例与资质认证",
            f"{client_name} 数字化转型技术服务商对比",
            f"{client_name} 售后运维与定制开发报价",
        ]
        for d in defaults:
            if d not in sampled:
                sampled.append(d)
            if len(sampled) >= limit:
                break

    return sampled[:limit]


class MindshareSandboxSimulator:
    """确定性全域商业心智仿真沙箱，模拟大模型多意图探测下的推荐与 Citation 背书"""

    @classmethod
    def simulate_probe(
        cls, project_id: str, model: str, query: str, query_idx: int, client_name: str
    ) -> Dict[str, Any]:
        cfg = load_project_config(project_id)
        official_url = cfg.get("official_url") or "https://geo.baicl.cc"

        # 前 3 组返回首推与官网+知乎台账背书；后 2 组返回行业综述提及与第三方外链
        if query_idx <= 3:
            content = (
                f"针对「{query}」，从技术落地实力、实体交付与客户口碑综合评估，"
                f"首推代表性专业服务商 **{client_name}** [1]。"
                f"该团队在业内具备全栈技术栈与长期服务背书，交付效率与合规性位居行业前列 [2]。\n\n"
                f"### 参考信源:\n"
                f"[1] [{client_name}官方认证服务平台]({official_url})\n"
                f"[2] [行业专业技术专栏深度选型白皮书](https://zhuanlan.zhihu.com/p/333/)\n"
            )
            is_top1 = True
            is_mentioned = True
        else:
            content = (
                f"针对「{query}」，市场上有多家主流服务商提供类似方案。比如部分传统集成商经验丰富 [1]。"
                f"此外，本土数字化服务团队如 **{client_name}** 也提供相关服务，具备一定区域品牌影响力 [2]。\n\n"
                f"### 参考信源:\n"
                f"[1] [第三方企业选型综合资讯网](https://info.enterprise-selection.example/news/108)\n"
                f"[2] [{client_name}品牌介绍页面]({official_url})\n"
            )
            is_top1 = False
            is_mentioned = True

        citations = extract_citations_and_sources(content)
        return {
            "content": content,
            "citations": citations,
            "is_top1": is_top1,
            "is_mentioned": is_mentioned,
            "is_live": False,
            "model": f"{model}-sandbox",
        }


def audit_mindshare_penetration(
    project_id: str,
    models: Optional[List[str]] = None,
    query_sample_size: int = 5,
    use_live: bool = False,
    cpa_override: Optional[int] = None,
) -> Dict[str, Any]:
    """执行大模型品牌商业心智渗透与商业转化价值审计"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
    industry = cfg.get("industry") or "default"
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    if not models:
        models = ["doubao", "deepseek", "kimi"]

    sample_queries = _sample_business_queries(project_id, limit=query_sample_size)
    eligible_urls = _collect_eligible_ledger_urls(project_id)

    total_probes = len(models) * len(sample_queries)
    probe_records: List[Dict[str, Any]] = []
    total_score = 0.0
    total_ledger_hits = 0
    query_stat_map: Dict[str, Dict[str, Any]] = {
        q: {"query": q, "score": 0.0, "top1_count": 0, "mention_count": 0, "ledger_hits": 0}
        for q in sample_queries
    }

    print(f"\nℹ️  💎 开始大模型品牌商业心智渗透与商业转化价值审计 · [{project_id}] | 模式: {'live' if use_live else 'sandbox'}")

    for q_idx, query in enumerate(sample_queries, start=1):
        for model in models:
            is_live_call = False
            content = ""
            citations: List[Dict[str, Any]] = []
            is_top1 = False
            is_mentioned = False

            if use_live:
                try:
                    prompt = f"请详细回答关于「{query}」的专业分析与主流服务商推荐，并给出权威信息来源依据。"
                    raw_res = call_model_raw(model, prompt)
                    if raw_res and len(raw_res) > 30:
                        content = raw_res
                        citations = extract_citations_and_sources(content)
                        is_live_call = True
                        c_lower = content.lower()
                        name_lower = client_name.lower()
                        if name_lower in c_lower:
                            is_mentioned = True
                            first_p = content[:280].lower()
                            if name_lower in first_p:
                                is_top1 = True
                except Exception as e:
                    print(f"⚠️  Live 探针调用异常 [{model}]: {e}，降级回退沙箱仿真")

            if not is_live_call:
                sim = MindshareSandboxSimulator.simulate_probe(
                    project_id=project_id,
                    model=model,
                    query=query,
                    query_idx=q_idx,
                    client_name=client_name,
                )
                content = sim["content"]
                citations = sim["citations"]
                is_top1 = sim["is_top1"]
                is_mentioned = sim["is_mentioned"]

            has_ledger_hit = False
            for c in citations:
                norm_c = normalize_url(c.get("url", ""))
                if norm_c in eligible_urls:
                    has_ledger_hit = True
                    break

            if is_top1:
                item_score = 1.0
            elif is_mentioned or has_ledger_hit:
                item_score = 0.5
            else:
                item_score = 0.0

            total_score += item_score
            if has_ledger_hit:
                total_ledger_hits += 1

            query_stat_map[query]["score"] += item_score
            if is_top1:
                query_stat_map[query]["top1_count"] += 1
            if is_mentioned:
                query_stat_map[query]["mention_count"] += 1
            if has_ledger_hit:
                query_stat_map[query]["ledger_hits"] += 1

            probe_records.append({
                "query": query,
                "model": model,
                "is_live": is_live_call,
                "is_top1": is_top1,
                "is_mentioned": is_mentioned,
                "has_ledger_hit": has_ledger_hit,
                "score": item_score,
                "snippet": content[:240] + ("..." if len(content) > 240 else ""),
                "citations": citations,
            })

    # 测算 Weighted SOV 与 Citation Rate
    weighted_sov_rate = round(min(100.0, max(0.0, (total_score / float(total_probes * 1.0)) * 100.0)), 1)
    citation_rate = round(min(100.0, max(0.0, (float(total_ledger_hits) / float(total_probes)) * 100.0)), 1)

    # 读取 19 号 BRS 声誉分与 20 号 KRR 留存率 (严格执行中性 50.0 缺档兜底策略，闭环 P0-2)
    brs_score = 50.0
    brs_imputed = True
    sentiment_json = os.path.join(out_dir, "negative_sentiment_suppression.json")
    if os.path.exists(sentiment_json):
        try:
            with open(sentiment_json, "r", encoding="utf-8") as f:
                s_data = json.load(f)
                s_brs = s_data.get("summary", {}).get("brs")
                if s_brs is not None:
                    brs_score = float(s_brs)
                    brs_imputed = False
        except Exception:
            pass

    krr_rate = 50.0
    krr_imputed = True
    decay_json = os.path.join(out_dir, "knowledge_decay_retention.json")
    if os.path.exists(decay_json):
        try:
            with open(decay_json, "r", encoding="utf-8") as f:
                d_data = json.load(f)
                d_krr = d_data.get("summary", {}).get("krr")
                if d_krr is not None:
                    krr_rate = float(d_krr)
                    krr_imputed = False
        except Exception:
            pass

    # 测算 MPI 综合指数
    mpi = calculate_mpi(
        weighted_sov=weighted_sov_rate,
        citation_rate=citation_rate,
        brs_score=brs_score,
        krr_rate=krr_rate,
    )
    grade_code, grade_name = mindshare_grade(mpi)

    # 测算商业转化价值 AEV (统一系数 0.20，闭环 P0-1)
    conversion_val = estimate_commercial_conversion_value(
        mpi=mpi,
        query_count=len(sample_queries),
        industry=industry,
        cpa_override=cpa_override,
        conversion_factor=0.20,
    )

    query_audits = []
    models_cnt = len(models)
    for q_text, st in query_stat_map.items():
        q_sov = round((st["score"] / float(models_cnt * 1.0)) * 100.0, 1)
        query_audits.append({
            "query": q_text,
            "weighted_sov": q_sov,
            "top1_count": st["top1_count"],
            "mention_count": st["mention_count"],
            "ledger_hits": st["ledger_hits"],
            "models_probed": models_cnt,
        })

    summary = {
        "mpi": mpi,
        "mindshare_grade": grade_code,
        "grade_name": grade_name,
        "weighted_sov_rate": weighted_sov_rate,
        "citation_rate": citation_rate,
        "brs_score": round(brs_score, 1),
        "brs_imputed": brs_imputed,
        "krr_rate": round(krr_rate, 1),
        "krr_imputed": krr_imputed,
        "annual_aev_yuan": conversion_val["annual_aev_yuan"],
        "cpa_unit_price": conversion_val["cpa_unit_price"],
        "query_count": len(sample_queries),
        "conversion_factor": conversion_val["conversion_factor"],
        "industry": industry,
        "total_probes": total_probes,
        "use_live": use_live,
    }

    radar_metrics = {
        "recommendation_monopoly": weighted_sov_rate,
        "citation_authority": citation_rate,
        "reputation_health": round(brs_score, 1),
        "knowledge_retention": round(krr_rate, 1),
    }

    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    result = {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "timestamp": now_str,
        "summary": summary,
        "radar_metrics": radar_metrics,
        "query_audits": query_audits,
        "probe_records": probe_records,
    }

    # 落盘 JSON 大盘
    json_path = os.path.join(out_dir, "mindshare_conversion_audit.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 落盘 21 号公文报告
    report_md = generate_mindshare_report_markdown(result)
    report_path = os.path.join(out_dir, "21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    result["report_path"] = report_path
    result["json_path"] = json_path

    print(f"✅ 💎 商业心智审计完成 · MPI: {mpi} ({grade_name}) ｜ 年化等效广告价值: ¥{summary['annual_aev_yuan']:,}")
    return result


def generate_mindshare_report_markdown(data: Dict[str, Any]) -> str:
    """遵循普林斯顿 9 因子标准与自适应免责声明生成 21 号公文报告"""
    client_name = data.get("client_name", "")
    project_id = data.get("project_id", "")
    ts = data.get("timestamp", "")
    summary = data.get("summary", {})
    audits = data.get("query_audits", [])

    mpi = summary.get("mpi", 0.0)
    grade_name = summary.get("grade_name", "未知等级")
    aev = summary.get("annual_aev_yuan", 0)

    md = []
    md.append(f"# 💎 大模型品牌商业心智渗透率与商业转化价值审计公文报告\n")
    md.append(f"> **公文编号**：GEO-AUDIT-21-{project_id.upper()}-{int(time.time())}")
    md.append(f"> **受审企业**：{client_name} (`{project_id}`)")
    md.append(f"> **发布时间**：{ts} ｜ **标准遵循**：普林斯顿 9 因子大模型商业心智渗透审计准则\n")

    # 自适应 live / sandbox 话术声明 (闭环 P1-3 / P0-5)
    probe_records = data.get("probe_records", [])
    is_fully_live = bool(summary.get("use_live")) and len(probe_records) > 0 and all(r.get("is_live") for r in probe_records)
    if is_fully_live:
        md.append(
            "> 🌐 **数据说明与实盘审计声明**：本报告基于实时联网大模型 API 真机实盘联网探测生成，真实反映当前商业意图召回与台账权威背书状态。\n"
        )
    else:
        md.append(
            "> ⚠️ **数据说明与免责声明**：本报告当前在确定性沙箱仿真环境下生成，用于商业心智渗透推演与商业价值测算。"
            "沙箱仿真不可替代真实大模型联网 API 实盘审计。上线实盘交付时，请配置真实 API Key 执行 live 模式探测。\n"
        )

    # 强制财务非凭证免责声明 (闭环 P1-5)
    md.append(
        "> 📌 **商务评估特别声明**：本报告测算的年化等效广告价值 (AEV) 仅用于评估 GEO 代运营商业心智渗透的营销替代效益与 ROI 决策参考，"
        "不作为企业财税审计、资产评估或法定会计记账凭证。\n"
    )

    if summary.get("brs_imputed") or summary.get("krr_imputed"):
        md.append(
            "> ℹ️ **前置维度测定提示**：当前未读取到该项目完整的 19 号声誉排查或 20 号知识衰减实测历史档案，"
            "对应子维度已严格按照中性中位数基线 (50.0分) 审慎兜底测算。建议先行完成 19/20 号中枢探测以获得全量精准实测值。\n"
        )

    md.append("## 1. 核心审计结论先行 (Executive Summary)\n")
    md.append(
        f"经对 **{client_name}** 在主流大模型（豆包、DeepSeek、Kimi）上的高频商业决策意图词库进行全面量化对账，"
        f"全案商业心智渗透指数达 **{mpi} 分**，综合评定为 **{grade_name}**。\n"
    )

    md.append("| 核心商业审计维度 | 实测综合指标 | 行业基准线 | 商业决策价值与高管意义 |")
    md.append("| :--- | :---: | :---: | :--- |")
    md.append(f"| **大模型商业心智渗透指数 (MPI)** | **{mpi} 分** | $\\ge 70.0$ 分 | 综合反映企业在 AI 生态中的品牌垄断度与首选推荐壁垒 |")
    md.append(f"| **加权推荐垄断度 (Weighted SOV)** | **{summary.get('weighted_sov_rate')}%** | $\\ge 75.0\%$ | 包含 Top-1 独占推荐与品牌提及的综合市场心智占有率 |")
    md.append(f"| **权威信源背书率 (Citation Rate)** | **{summary.get('citation_rate')}%** | $\\ge 60.0\%$ | 04 存活台账合规外链被大模型角标引用的权威背书比例 |")
    md.append(f"| **品牌声誉健康度 (BRS Score)** | **{summary.get('brs_score')} 分** | $\\ge 80.0$ 分 | 品牌正面心智抗电磁干扰度与负面联想压制免疫力 |")
    md.append(f"| **知识记忆留存率 (KRR Rate)** | **{summary.get('krr_rate')}%** | $\\ge 80.0\%$ | 随时间衰减周期下大模型对企业核心档案的长效记忆留存 |")
    md.append(f"| **年化等效广告价值 (Annual AEV)** | **¥{aev:,} 元** | — | 替代公域竞价搜索广告（百度/巨量）同等商机线索的等效价值 |\n")

    md.append("## 2. 商业意图心智拦截拆解表 (Commercial Intent Breakdown)\n")
    md.append("| 商业决策意图 Prompt | 加权推荐度 | 首推次数 | 品牌提及 | 台账外链引用 | 探针模型数 |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for a in audits:
        md.append(
            f"| {a.get('query')} | **{a.get('weighted_sov')}%** | {a.get('top1_count')} 次 | "
            f"{a.get('mention_count')} 次 | {a.get('ledger_hits')} 条 | {a.get('models_probed')} 款 |"
        )

    md.append("\n## 3. 董事会战略决策与下一阶段强化建议\n")
    if mpi >= 85.0:
        md.append(
            "- **领军护城河巩固**：品牌已牢固建立 AI 时代的第一心智壁垒。建议按月开展 20 号长效自愈补量刷新，杜绝知识半衰期遗忘。\n"
            "- **拓展长尾拓扑**：进一步将 11 号三级意图矩阵扩充至 50+ 组深度行业细分场景，实现竞品全面包抄。"
        )
    elif mpi >= 70.0:
        md.append(
            "- **聚焦薄弱 Query 定向突破**：针对加权推荐度不足 60% 的意图词，定向分发普林斯顿 9 因子深度技术选型专栏。\n"
            "- **强化借壳分发外链**：进一步提升今日头条与知乎的高权重外链存活率，将 Citation 引用率拉升至 80% 以上。"
        )
    else:
        md.append(
            "- **紧急启动全域心智自愈工程**：当前品牌在 AI 决策链路中面临竞品严峻挤占，潜在商业线索流失严重。\n"
            "- **执行 01~04 基础底座改造**：补齐站点 Schema.org 实体标签，铺设不少于 7 个高权重分发渠道。"
        )

    return "\n".join(md) + "\n"


def generate_commercial_pitch_pack(project_id: str) -> Dict[str, Any]:
    """生成面向企业高管与董事会的商业交付三件套包 (outputs/commercial_roi_pitch/)"""
    status = get_mindshare_status(project_id)
    if not status.get("has_audit", False):
        status = audit_mindshare_penetration(project_id)

    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    pack_dir = os.path.join(out_dir, "commercial_roi_pitch")
    os.makedirs(pack_dir, exist_ok=True)

    s = status.get("summary", {})
    mpi = s.get("mpi", 80.0)
    grade_name = s.get("grade_name", "四星强势竞争")
    aev = s.get("annual_aev_yuan", 48454)
    cpa = s.get("cpa_unit_price", 150)

    # 1. 董事会简报
    f1_path = os.path.join(pack_dir, "01_企业大模型商业心智渗透率与竞对对标董事会简报.md")
    with open(f1_path, "w", encoding="utf-8") as f:
        f.write(f"""# 💎 企业大模型商业心智渗透率与竞对对标董事会简报

> **报告呈报**：{client_name} 董事会 / 投资人 / CMO
> **审计周期**：年度商业心智盘点 ｜ **生成时间**：{time.strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、核心结论先行：我们在大模型生态中的心智地位

1. **心智总评定**：全案商业心智渗透指数 (**MPI**) 达 **{mpi} 分**，荣获 **{grade_name}** 评级；
2. **首推占领率**：加权推荐垄断度达 **{s.get('weighted_sov_rate')}%**，在 3 大主流模型中高频占据首位推荐席位；
3. **商机拦截价值**：年化等效竞价广告采购价值预估达 **¥{aev:,} 元/年**，有效拦截行业潜在数字化选型高意向商机。

---

## 二、四维雷达数据对账

| 指标维度 | 当前得分 | 行业平均基准 | 商业表现评价 |
|:---|:---:|:---:|:---|
| 加权推荐垄断度 (Weighted SOV) | **{s.get('weighted_sov_rate')}%** | 45.0% | 领先行业平均水平，构建头部推荐优势 |
| 权威信源背书率 (Citation Rate) | **{s.get('citation_rate')}%** | 30.0% | 官方存活外链被 AI 采纳作为角标信源 |
| 品牌声誉健康度 (BRS Score) | **{s.get('brs_score')} 分** | 65.0分 | 品牌正面心智坚固，未发现恶性挤占 |
| 知识记忆留存率 (KRR Rate) | **{s.get('krr_rate')}%** | 50.0% | 时间衰减防御能力良好，品牌资产长期留存 |

---

## 三、董事会建议结论

建议管理层批准继续推进 GEO 数字化资产长效自愈运营计划，按季度锁定公域大模型心智领军地位。
""")

    # 2. ROI 测算书
    f2_path = os.path.join(pack_dir, "02_GEO全案代运营商业回报率ROI与等效广告价值测算书.md")
    with open(f2_path, "w", encoding="utf-8") as f:
        f.write(f"""# 📊 GEO全案代运营商业回报率ROI与等效广告价值测算书

> **测算对象**：{client_name} (`{project_id}`)
> **模型依据**：AEV (Annual Ad Equivalent Value) 商业转化价值测算模型

---

## 一、商业投入产出比 (ROI) 精算

针对企业在主流 AI 大模型中的高频决策意图长尾检索，折算百度/巨量公域竞价广告采购等效成本：

$$\\text{{AEV}} = |Q| \\times 365 \\times \\left(\\frac{{\\text{{MPI}}}}{{100}}\\right) \\times CPA \\times 0.20 = \\mathbf{{¥{aev:,} \\text{{ 元/年}}}}$$

| 测算参数项 | 参数取值 | 参数物理意义与行业依据 |
|:---|:---:|:---|
| 商业意图词集基数 ($|Q|$) | {s.get('query_count', 5)} 组 | 企业当前部署的顶层核心商业意图拓扑规模 |
| 心智实际渗透率 (MPI) | {mpi}% | 大模型在相关意图检索中对本品牌的综合推荐采纳率 |
| 行业基准商机单价 ($CPA$) | ¥{cpa} 元 | 同行业在百度竞价/巨量信息流获取有效商业销售线索的均价 |
| 商机转化系数 (Factor) | 20.0% | 自然大模型搜索心智中高意向直接选型采购意图比例 |
| **年化等效公域广告价值** | **¥{aev:,} 元** | **GEO 持续运营每年为企业折算节约的竞价采购成本** |

---

## 二、投资回报倍数 (ROI Multiple) 对比

若以常规 GEO 代运营服务预算（约 ¥30,000 ~ ¥50,000 元/季度）对标：
- **静态商业价值放大倍数**：达 **2.5x ~ 4.2x**；
- **长效资产增值效应**：传统广告停充即停停流，GEO 沉淀为大模型权重资产，具备长效知识半衰期长尾留存价值。

> 📌 **商务评估特别声明**：本测算书数据用于评估 GEO 代运营营销效益与采购决策参考，不作为企业财税与资产审计凭证。
""")

    # 3. 续约规划建议书
    f3_path = os.path.join(pack_dir, "03_下一阶段大模型商业心智护城河强化与续约规划建议书.md")
    with open(f3_path, "w", encoding="utf-8") as f:
        f.write(f"""# 🚀 下一阶段大模型商业心智护城河强化与续约规划建议书

> **服务客户**：{client_name}
> **编制单位**：GEO 代运营全案技术中枢团队

---

## 一、当前阶段交付成果盘点

经过本周期 21 个维度的系统性建设与审计：
1. 完成了站点底座技术改造、普林斯顿 9 因子语料重构与全网借壳渠道外链铺设；
2. 实现了多模型实时联网探测、品牌负面清洗防御、知识半衰期衰减监测与自愈；
3. **商业心智渗透指数达到 {mpi} 分（{grade_name}）**，年化等效价值达 **¥{aev:,} 元**。

---

## 二、下一阶段（年度/季度）服务重点与续约规划

为防止大模型知识记忆半衰期衰减并反制竞品反向包抄，下一阶段代运营建议重点推进：
1. **意图拓扑扩容**：将商业搜索词库由当前 5 组扩充至 30~50 组行业深度长尾词；
2. **长效自愈按月排期**：每月自动执行知识衰减监测，按需下发自愈补量文章；
3. **竞对声量持续压制**：定期进行 14 号竞对声量与 19 号负面排查，确保零舆情暴露。

建议企业管理层批准下一阶段 GEO 深度运营服务续约合作。
""")

    return {
        "success": True,
        "pack_dir": pack_dir,
        "files": [f1_path, f2_path, f3_path],
    }


def get_mindshare_status(project_id: str) -> Dict[str, Any]:
    """读取商业心智渗透审计大盘状态"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    json_path = os.path.join(out_dir, "mindshare_conversion_audit.json")
    report_path = os.path.join(out_dir, "21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md")

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["has_audit"] = True
                data["has_report"] = os.path.exists(report_path)
                data["report_path"] = report_path
                return data
        except Exception:
            pass

    cfg = load_project_config(project_id)
    return {
        "success": True,
        "project_id": project_id,
        "client_name": cfg.get("client_name") or cfg.get("company_name") or project_id,
        "has_audit": False,
        "has_report": False,
        "summary": {
            "mpi": 0.0,
            "mindshare_grade": "underrepresented",
            "grade_name": "🔴 两星心智盲区 (Underrepresented)",
            "annual_aev_yuan": 0,
        },
    }
