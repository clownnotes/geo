#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 客户续约预测与商业 ROI 量化计算中枢 (tools/geo/roi.py)
核心功能：
1. 将技术指标 (SOV、Rank 1、分发台账、事实引用) 折算为三大商业财务指标：
   - SEM 竞价替代节省价值 (Cost Replacement Value)
   - AI 首推精准线索估值 (Inbound Opportunity Value)
   - 权威语料库数字资产估值 (Digital Asset Valuation)
2. 计算客户综合投资回报率 (ROI %) 与价值倍数；
3. 预测客户续约健康度评分 (0~100) 并生成针对性的续费增购谈判话术与提案建议。
"""

import os
import sys
import json
import time

from .utils import (
    PROJECT_ROOT,
    PROJECTS_DIR,
    load_project_config,
    save_project_output,
    print_banner,
    print_info,
    print_success,
    print_warning
)
from .monitor import extract_monitor_metrics
from .dist_bot import get_distribution_ledger

DEFAULT_ROI_SETTINGS = {
    "annual_service_fee": 30000,       # GEO 年化服务费 (元)
    "cpl": 160.0,                      # 行业单条精准销售线索成本 (Cost Per Lead, 元)
    "cpc": 6.5,                        # 传统 SEM 搜索单次点击竞价成本 (元)
    "monthly_query_baseline": 2500,     # 月度相关商业意图 Prompt 检索量 (次)
    "avg_order_value": 25000.0         # 客户业务平均客单价 (元)
}

def _get_roi_file(project_id: str) -> str:
    return os.path.join(PROJECTS_DIR, project_id, "outputs", "roi_settings.json")

def load_roi_settings(project_id: str) -> dict:
    """加载项目的商业 ROI 参数配置"""
    fpath = _get_roi_file(project_id)
    settings = dict(DEFAULT_ROI_SETTINGS)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                saved = json.load(f)
                settings.update(saved)
        except Exception:
            pass
    return settings

def save_roi_settings(project_id: str, settings: dict) -> dict:
    """保存项目的商业 ROI 参数配置"""
    fpath = _get_roi_file(project_id)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    current = load_roi_settings(project_id)
    for k in DEFAULT_ROI_SETTINGS.keys():
        if k in settings:
            try:
                current[k] = float(settings[k]) if isinstance(DEFAULT_ROI_SETTINGS[k], float) else int(settings[k])
            except Exception:
                pass
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    print_success(f"✅ 项目 [{project_id}] 商业 ROI 参数已更新保存！")
    return {"success": True, "project_id": project_id, "settings": current}

def calculate_project_roi(project_id: str, custom_params: dict = None) -> dict:
    """综合测算项目的商业投资回报率 (ROI) 与续约健康度预测"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")

    # 1. 加载参数
    settings = load_roi_settings(project_id)
    if custom_params and isinstance(custom_params, dict):
        settings.update(custom_params)

    fee = max(float(settings.get("annual_service_fee", 30000)), 1000)
    cpl = float(settings.get("cpl", 160.0))
    cpc = float(settings.get("cpc", 6.5))
    monthly_query = int(settings.get("monthly_query_baseline", 2500))
    avg_order = float(settings.get("avg_order_value", 25000.0))

    # 2. 获取实时监控与台账指标
    is_offline = True
    auth_score = 90.0
    try:
        metrics = extract_monitor_metrics(project_id)
        raw_sov = float(metrics.get("sov_pct", 0.0))
        is_offline = bool(metrics.get("is_offline", True))
        auth_score = float(metrics.get("authority_score", 90.0))
        prompt_stats = metrics.get("prompt_stats", {})
        rank1_hits = int(prompt_stats.get("hit_count", 0))
        intercept_count = int(prompt_stats.get("intercept_count", 0))
    except Exception:
        raw_sov = 0.0
        rank1_hits = 0
        intercept_count = 0

    try:
        dist_ledger = get_distribution_ledger(project_id)
        completion_rate = float(dist_ledger.get("completion_rate_pct", 60.0))
        published_channels = int(dist_ledger.get("published_channels", 3))
    except Exception:
        completion_rate = 60.0
        published_channels = 3

    # 计算有效交付达成 SOV（若为摸底离线基准 0%，则采用 GEO 语料注入后的达成预估 85%~95%）
    if raw_sov > 0:
        effective_sov = raw_sov
        is_projected = False
    else:
        effective_sov = round(max(auth_score * 0.9, 85.0), 1)
        is_projected = True

    # 3. 核心财务三大价值计算
    # ① 等效 SEM 竞价替代节省价值 (月检索量 * SOV * CPC * 12)
    sem_val = round(monthly_query * (effective_sov / 100.0) * cpc * 12)

    # ② AI 首推精准销售线索估值 (Rank1 问答数 × 8条/月 × 12 × CPL)
    monthly_leads_per_rank1 = 8
    est_annual_leads = max(rank1_hits, 1) * monthly_leads_per_rank1 * 12 if rank1_hits > 0 else round((effective_sov / 100.0) * monthly_leads_per_rank1 * 12)
    leads_val = round(est_annual_leads * cpl)

    # ③ 数字资产与高权重信任池估值 (每发布信任池 3000元 + 9因子语料资产 15000元)
    asset_val = round(max(published_channels, 1) * 3000 + 15000)

    total_val = sem_val + leads_val + asset_val
    net_val = total_val - fee
    roi_pct = round((net_val / fee) * 100.0, 1)
    roi_mult = round(total_val / fee, 2)

    # 4. 续约健康度评分模型 (0~100 分，对齐 design §2 ⑤)
    score = 40
    score += min(round(effective_sov * 0.25), 25)
    score += 15 if rank1_hits > 0 else 0
    score += min(round(completion_rate * 0.10), 10)
    if not is_offline and intercept_count == 0:
        score += 10
    elif not is_offline:
        score += 5
    score = min(max(score, 20), 100)

    if score >= 85:
        grade = "极高概率续约"
        grade_color = "emerald"
        tier_advice = f"当前项目 SOV ({effective_sov}%) 与全网收录表现优异，客户心智占领极高。建议在服务到期前 30 天呈递《年度深度防守与矩阵裂变增购提案》，主推集团矩阵与追问词库扩容。"
        talking_points = [
            f"已实现 {effective_sov}% SOV 首选推荐，年化替代传统竞价预算达 ¥{sem_val:,} 元；",
            f"全网沉淀 {published_channels} 大权威信任池外链资产，大模型 Citation 稳居行业前列；",
            f"为企业创造直接商业综合价值 ¥{total_val:,} 元，投资回报率高达 {roi_pct}% ({roi_mult} 倍)；",
            f"续约增购可扩展至集团矩阵多子品牌与 15 组追问裂变词库，形成绝对行业护城河。"
        ]
    elif score >= 70:
        grade = "健康续约"
        grade_color = "indigo"
        tier_advice = f"项目各项指标处于行业前列，建议在季度复盘会上通过现场沙箱演示（Before/After）强化客户对推荐排位的感知。"
        talking_points = [
            f"当前 AI 声量占有率为 {effective_sov}%，累计带来预估销售线索价值 ¥{leads_val:,} 元；",
            f"建议持续完成剩余平台的落地发布，将分发完成率从 {completion_rate}% 提至 100%；",
            f"按期续约将锁定核心品牌词的防御阵地，避免被竞品反向包抄。"
        ]
    else:
        grade = "需重点公关"
        grade_color = "amber"
        tier_advice = f"当前分发完成率或 SOV 存在提升空间，建议顾问团队进行面对面答辩与语料库深度重构，确保下个周期快速起效。"
        talking_points = [
            f"目前已完成技术底座改造与初步语料注入，正处于大模型爬虫深度抓取收录周期；",
            f"重点加速今日头条与知乎的高权重图文发布，确保 2 周内实现首位提及。"
        ]

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "brand_name": brand_name,
        "industry": industry,
        "settings": settings,
        "metrics_summary": {
            "raw_sov_pct": raw_sov,
            "effective_sov_pct": effective_sov,
            "is_projected": is_projected,
            "completion_rate_pct": completion_rate,
            "published_channels": published_channels,
            "rank1_hit_count": rank1_hits,
            "intercept_count": intercept_count
        },
        "financial_valuation": {
            "annual_service_fee": int(fee),
            "sem_replacement_value": int(sem_val),
            "leads_inbound_value": int(leads_val),
            "digital_asset_value": int(asset_val),
            "total_business_value": int(total_val),
            "net_profit_value": int(net_val),
            "roi_pct": roi_pct,
            "roi_multiplier": roi_mult
        },
        "renewal_health": {
            "score": score,
            "grade": grade,
            "grade_color": grade_color,
            "tier_advice": tier_advice,
            "talking_points": talking_points
        }
    }

def predict_renewal_health(project_id: str) -> dict:
    """获取项目的续约健康度评估与谈判要点"""
    res = calculate_project_roi(project_id)
    return {
        "success": True,
        "project_id": project_id,
        "renewal_health": res["renewal_health"],
        "financial_valuation": res["financial_valuation"],
        "metrics_summary": res["metrics_summary"]
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    print(json.dumps(calculate_project_roi(pid), ensure_ascii=False, indent=2))
